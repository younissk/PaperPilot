"""Snowball Engine for iterative citation graph exploration (Async version).

This module implements the core snowballing algorithm that:
1. Starts with seed papers
2. Expands via references (backward) and citations (forward)
3. Ranks candidates cheaply before LLM judging
4. Runs in iterations until convergence or budget cap
5. Tracks full provenance for explainability

Uses async/await for concurrent API calls to improve performance.
"""

import asyncio
from collections.abc import Callable

import aiohttp

from papernavigator.judge import judge_candidate
from papernavigator.models import (
    AcceptedPaper,
    EdgeType,
    JudgmentResult,
    QueryProfile,
    SnowballCandidate,
)
from papernavigator.openalex import (
    extract_openalex_id,
    get_citations,
    get_references_with_fallback,
    search_related_works,
)
from papernavigator.ranker import rank_candidates

# Configuration defaults
DEFAULT_MAX_ITERATIONS = 5
DEFAULT_TOP_N_PER_ITERATION = 50
DEFAULT_MIN_NEW_PAPERS_THRESHOLD = 3
DEFAULT_MAX_TOTAL_ACCEPTED = 200
DEFAULT_MAX_REFS_PER_PAPER = 100
DEFAULT_MAX_CITATIONS_PER_PAPER = 100


class SnowballEngine:
    """Orchestrates iterative snowballing for literature discovery (Async version)."""

    def __init__(
        self,
        profile: QueryProfile,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
        top_n_per_iteration: int = DEFAULT_TOP_N_PER_ITERATION,
        min_new_papers_threshold: int = DEFAULT_MIN_NEW_PAPERS_THRESHOLD,
        max_total_accepted: int = DEFAULT_MAX_TOTAL_ACCEPTED,
        max_refs_per_paper: int = DEFAULT_MAX_REFS_PER_PAPER,
        max_citations_per_paper: int = DEFAULT_MAX_CITATIONS_PER_PAPER,
    ):
        """Initialize the snowball engine.
        
        Args:
            profile: Query profile for relevance filtering
            max_iterations: Maximum number of expansion iterations
            top_n_per_iteration: Max candidates to LLM-judge per iteration
            min_new_papers_threshold: Stop if fewer new papers accepted
            max_total_accepted: Budget cap on total accepted papers
            max_refs_per_paper: Max references to fetch per paper
            max_citations_per_paper: Max citations to fetch per paper
        """
        self.profile = profile
        self.max_iterations = max_iterations
        self.top_n_per_iteration = top_n_per_iteration
        self.min_new_papers_threshold = min_new_papers_threshold
        self.max_total_accepted = max_total_accepted
        self.max_refs_per_paper = max_refs_per_paper
        self.max_citations_per_paper = max_citations_per_paper

        # State
        self.visited: set[str] = set()  # paper_ids we've seen
        self.accepted: list[AcceptedPaper] = []  # papers that passed judgment
        self.paper_titles: dict[str, str] = {}  # paper_id -> title for logging

    async def run(
        self,
        session: aiohttp.ClientSession,
        seeds: list[SnowballCandidate],
        progress_callback: Callable[[int, str, int, int, str, int, int], None] | None = None,
        total_iterations: int = 0,
    ) -> list[AcceptedPaper]:
        """Run the iterative snowballing algorithm.
        
        Args:
            session: aiohttp ClientSession for HTTP requests
            seeds: Initial seed papers to start snowballing from
            progress_callback: Optional callback function(step, step_name, current, total, message, current_iteration, total_iterations)
            total_iterations: Maximum iterations configured (for progress tracking)
            
        Returns:
            List of accepted papers with full provenance
        """
        # Iteration 0: Accept all seeds (they already passed initial filtering)
        if progress_callback:
            progress_callback(5, "Running Snowball Search", 0, len(seeds), f"Processing {len(seeds)} seed papers...", 0, total_iterations)

        current_frontier: list[SnowballCandidate] = []

        for idx, seed in enumerate(seeds, 1):
            if seed.paper_id in self.visited:
                continue

            self.visited.add(seed.paper_id)
            self.paper_titles[seed.paper_id] = seed.title

            # Seeds are pre-accepted (they came from initial search + filtering)
            accepted = AcceptedPaper(
                paper_id=seed.paper_id,
                title=seed.title,
                abstract=seed.abstract,
                year=seed.year,
                citation_count=seed.citation_count,
                discovered_from=seed.discovered_from,
                edge_type=EdgeType.SEED,
                depth=0,
                judge_reason=seed.seed_reason or "Seed paper from initial search",
                judge_confidence=seed.seed_confidence if seed.seed_confidence is not None else 1.0,
            )
            self.accepted.append(accepted)
            current_frontier.append(seed)

            if progress_callback:
                progress_callback(5, "Running Snowball Search", idx, len(seeds), f"Accepted {idx} of {len(seeds)} seed papers", 0, total_iterations)

        # Iterations 1..N: Expand, rank, judge
        for iteration in range(1, self.max_iterations + 1):
            if not current_frontier:
                break

            if len(self.accepted) >= self.max_total_accepted:
                break

            if progress_callback:
                progress_callback(5, "Running Snowball Search", 0, 0, f"Iteration {iteration}: Expanding frontier...", iteration, total_iterations)

            # Phase 1: Expand - get refs and citations (CONCURRENT)
            all_candidates = await self._expand_frontier(session, current_frontier, depth=iteration, progress_callback=progress_callback, iteration=iteration, total_iterations=total_iterations)

            if not all_candidates:
                # Fallback: Try to find established related papers if iteration 1 failed
                if iteration == 1:
                    if progress_callback:
                        progress_callback(5, "Running Snowball Search", 0, 0, "Iteration 1: No candidates found, trying fallback search...", iteration, total_iterations)
                    fallback_candidates = await self._search_established_papers(session)

                    if fallback_candidates:
                        all_candidates = fallback_candidates
                        if progress_callback:
                            progress_callback(5, "Running Snowball Search", len(all_candidates), len(all_candidates), f"Iteration 1: Found {len(all_candidates)} fallback candidates", iteration, total_iterations)
                    else:
                        break
                else:
                    break

            if progress_callback:
                progress_callback(5, "Running Snowball Search", 0, len(all_candidates), f"Iteration {iteration}: Ranking {len(all_candidates)} candidates...", iteration, total_iterations)

            # Phase 2: Rank - cheap scoring before LLM (sync, CPU-bound)
            ranked, passed_gate, total = rank_candidates(
                all_candidates,
                self.profile,
                top_n=self.top_n_per_iteration,
                relaxed=True  # Allow papers matching ANY concept group
            )

            if progress_callback:
                progress_callback(5, "Running Snowball Search", len(ranked), len(all_candidates), f"Iteration {iteration}: Ranked {len(ranked)} top candidates for judging", iteration, total_iterations)

            if not ranked:
                break

            if progress_callback:
                progress_callback(5, "Running Snowball Search", 0, len(ranked), f"Iteration {iteration}: Judging {len(ranked)} candidates...", iteration, total_iterations)

            # Phase 3: Judge - LLM evaluation of top N (CONCURRENT)
            new_accepted = await self._judge_candidates(ranked, progress_callback=progress_callback, iteration=iteration, total_iterations=total_iterations)

            if progress_callback:
                progress_callback(5, "Running Snowball Search", len(new_accepted), len(ranked), f"Iteration {iteration}: Accepted {len(new_accepted)} papers (total: {len(self.accepted)})", iteration, total_iterations)

            # Update frontier for next iteration
            current_frontier = [
                SnowballCandidate(
                    paper_id=p.paper_id,
                    title=p.title,
                    abstract=p.abstract,
                    year=p.year,
                    citation_count=p.citation_count,
                    influential_citation_count=0,
                    discovered_from=p.discovered_from,
                    edge_type=p.edge_type,
                    depth=p.depth,
                )
                for p in new_accepted
            ]

            # Check convergence
            if len(new_accepted) < self.min_new_papers_threshold:
                if progress_callback:
                    progress_callback(5, "Running Snowball Search", len(self.accepted), len(self.accepted), f"Converged: Only {len(new_accepted)} new papers (threshold: {self.min_new_papers_threshold})", iteration, total_iterations)
                break

        return self.accepted

    async def _expand_frontier(
        self,
        session: aiohttp.ClientSession,
        frontier: list[SnowballCandidate],
        depth: int,
        progress_callback: Callable[[int, str, int, int, str, int, int], None] | None = None,
        iteration: int = 0,
        total_iterations: int = 0,
    ) -> list[SnowballCandidate]:
        """Expand all papers in the frontier by fetching refs and citations concurrently.
        
        Args:
            session: aiohttp ClientSession
            frontier: Papers to expand
            depth: Current iteration depth
            
        Returns:
            List of new candidate papers (not yet visited)
        """
        async def expand_single_paper(
            paper: SnowballCandidate
        ) -> tuple[list[SnowballCandidate], list[SnowballCandidate]]:
            """Expand a single paper, returning (ref_candidates, cite_candidates)."""
            paper_id = paper.paper_id

            # Get references and citations concurrently for this paper
            refs_task = get_references_with_fallback(
                session,
                paper_id,
                arxiv_id=paper.arxiv_id,
                limit=self.max_refs_per_paper,
                verbose=False
            )
            cites_task = get_citations(
                session,
                paper_id,
                limit=self.max_citations_per_paper,
                verbose=False
            )

            refs, cites = await asyncio.gather(refs_task, cites_task)

            ref_candidates = self._process_linked_papers(refs, paper_id, EdgeType.REFERENCE, depth)
            cite_candidates = self._process_linked_papers(cites, paper_id, EdgeType.CITATION, depth)

            return ref_candidates, cite_candidates

        # Expand all frontier papers concurrently
        tasks = [expand_single_paper(paper) for paper in frontier]
        results = await asyncio.gather(*tasks)

        # Collect all candidates
        all_candidates: list[SnowballCandidate] = []
        paper_results: dict[str, tuple[int, int]] = {}  # paper_id -> (ref_count, cite_count)

        for idx, (paper, (ref_candidates, cite_candidates)) in enumerate(zip(frontier, results), 1):
            all_candidates.extend(ref_candidates)
            all_candidates.extend(cite_candidates)
            paper_results[paper.paper_id] = (len(ref_candidates), len(cite_candidates))

            if progress_callback and idx % 5 == 0:  # Update every 5 papers
                progress_callback(5, "Running Snowball Search", idx, len(frontier), f"Iteration {iteration}: Expanded {idx} of {len(frontier)} papers, found {len(all_candidates)} candidates", iteration, total_iterations)

        # Deduplicate candidates by paper_id (keep first occurrence)
        seen: set[str] = set()
        unique_candidates: list[SnowballCandidate] = []
        for c in all_candidates:
            if c.paper_id not in seen:
                seen.add(c.paper_id)
                unique_candidates.append(c)

        return unique_candidates

    async def _search_established_papers(
        self,
        session: aiohttp.ClientSession
    ) -> list[SnowballCandidate]:
        """Search for established related papers as fallback when seeds have no refs.
        
        Uses multiple domain-specific queries to find well-cited papers concurrently.
        
        Args:
            session: aiohttp ClientSession
            
        Returns:
            List of SnowballCandidate objects from established papers
        """
        # Build multiple fallback queries for comprehensive coverage
        fallback_queries = self._build_fallback_queries()

        async def search_single_query(query_info: dict) -> list[SnowballCandidate]:
            """Search for a single query and return candidates."""
            query = query_info["query"]
            min_cites = query_info.get("min_citations", 20)
            query_type = query_info.get("type", "general")

            related_works = await search_related_works(
                session,
                query=query,
                limit=15,
                min_citations=min_cites,
                verbose=False
            )

            candidates = []
            for work in related_works:
                paper_id = extract_openalex_id(work)
                if not paper_id or paper_id in self.visited:
                    continue

                # Check if this paper has indexed references
                ref_count = work.get("referenced_works_count")
                if ref_count is None:
                    referenced = work.get("referenced_works")
                    if isinstance(referenced, list):
                        ref_count = len(referenced)
                    else:
                        ref_count = 0
                cite_count = work.get("cited_by_count", 0)

                if ref_count == 0:
                    continue  # Skip papers without indexed references

                self.visited.add(paper_id)
                title = work.get("title") or work.get("display_name") or "(No title)"
                self.paper_titles[paper_id] = title

                candidate = SnowballCandidate(
                    paper_id=paper_id,
                    title=title,
                    abstract=work.get("abstract"),
                    year=work.get("publication_year"),
                    citation_count=cite_count,
                    influential_citation_count=0,
                    discovered_from=f"fallback_{query_type}",
                    edge_type=EdgeType.REFERENCE,
                    depth=1,
                )
                candidates.append(candidate)

            return candidates

        # Run all searches concurrently
        tasks = [search_single_query(q) for q in fallback_queries]
        results = await asyncio.gather(*tasks)

        # Combine and deduplicate
        seen_ids: set[str] = set()
        all_candidates: list[SnowballCandidate] = []

        for candidates in results:
            for c in candidates:
                if c.paper_id not in seen_ids:
                    seen_ids.add(c.paper_id)
                    all_candidates.append(c)

        return all_candidates

    def _build_fallback_queries(self) -> list[dict]:
        """Build a list of fallback queries for comprehensive paper discovery.
        
        Strategy:
        1. Use LLM-generated fallback queries from profile (if available)
        2. Core query with all concepts (intersection papers)
        3. Each concept group separately (foundational papers)
        4. Survey/review queries for the domain
        5. Key methodological terms
        
        Returns:
            List of dicts with 'query', 'min_citations', and 'type' keys
        """
        queries = []

        # 1. Core query - papers at intersection of all concepts
        queries.append({
            "query": self.profile.core_query,
            "min_citations": 0,
            "type": "core"
        })

        # 2. Add survey/review queries
        queries.append({
            "query": f"{self.profile.core_query} survey",
            "min_citations": 0,
            "type": "survey"
        })

        # 3. Use LLM-generated fallback queries from profile (most important)
        if self.profile.fallback_queries:
            for i, query in enumerate(self.profile.fallback_queries):
                queries.append({
                    "query": query,
                    "min_citations": 0,
                    "type": f"llm_fallback_{i}"
                })

        # 4. Search each concept group separately for foundational papers
        for i, group in enumerate(self.profile.required_concept_groups):
            if group:
                # Use top 2 terms from each group
                group_terms = " ".join(group[:2])
                queries.append({
                    "query": f"{group_terms} survey review",
                    "min_citations": 0,
                    "type": f"foundation_group_{i}"
                })

        # 5. Add domain-specific methodological queries based on concepts
        method_queries = self._generate_method_queries()
        queries.extend(method_queries)

        return queries

    def _generate_method_queries(self) -> list[dict]:
        """Generate methodological queries based on the domain.
        
        Returns common methodological papers that might be foundational
        for the research domain.
        """
        queries = []

        # Check for common patterns in required concepts
        all_concepts = " ".join(self.profile.required_concepts).lower()

        # If about language models / LLMs
        if any(term in all_concepts for term in ["llm", "language model", "transformer", "gpt", "bert"]):
            queries.append({
                "query": "transformer attention mechanism deep learning",
                "min_citations": 0,
                "type": "foundation_nlp"
            })
            queries.append({
                "query": "BERT pre-training language representation",
                "min_citations": 0,
                "type": "foundation_nlp"
            })

        # If about recommender systems
        if any(term in all_concepts for term in ["recommend", "personalized", "collaborative", "user-item"]):
            queries.append({
                "query": "collaborative filtering matrix factorization recommender",
                "min_citations": 0,
                "type": "foundation_recsys"
            })
            queries.append({
                "query": "sequential recommendation neural network",
                "min_citations": 0,
                "type": "foundation_recsys"
            })
            queries.append({
                "query": "personalized ranking implicit feedback",
                "min_citations": 0,
                "type": "foundation_recsys"
            })

        # If about neural networks / deep learning
        if any(term in all_concepts for term in ["neural", "deep learning", "embedding"]):
            queries.append({
                "query": "neural network embedding representation learning",
                "min_citations": 0,
                "type": "foundation_ml"
            })

        return queries

    def _process_linked_papers(
        self,
        papers: list[dict],
        parent_id: str,
        edge_type: EdgeType,
        depth: int
    ) -> list[SnowballCandidate]:
        """Convert OpenAlex API response to SnowballCandidate objects.
        
        Args:
            papers: List of paper dicts from OpenAlex API
            parent_id: ID of the paper these came from
            edge_type: Whether these are references or citations
            depth: Current depth in the graph
            
        Returns:
            List of SnowballCandidate objects for papers not yet visited
        """
        candidates = []

        for p in papers:
            # Extract OpenAlex ID (format: W1234567890)
            paper_id = extract_openalex_id(p)
            if not paper_id:
                continue

            # Skip if already visited
            if paper_id in self.visited:
                continue

            # Mark as visited to avoid duplicates
            self.visited.add(paper_id)

            # OpenAlex uses different field names
            title = p.get("title") or p.get("display_name") or "(No title)"
            self.paper_titles[paper_id] = title

            candidate = SnowballCandidate(
                paper_id=paper_id,
                title=title,
                abstract=p.get("abstract"),  # Already decoded by openalex module
                year=p.get("publication_year"),
                citation_count=p.get("cited_by_count", 0) or 0,
                influential_citation_count=0,  # OpenAlex doesn't have this field
                discovered_from=parent_id,
                edge_type=edge_type,
                depth=depth,
            )
            candidates.append(candidate)

        return candidates

    async def _judge_candidates(
        self,
        candidates: list[SnowballCandidate],
        progress_callback: Callable[[int, str, int, int, str, int, int], None] | None = None,
        iteration: int = 0,
        total_iterations: int = 0,
    ) -> list[AcceptedPaper]:
        """Send candidates to LLM judge concurrently and collect accepted papers.
        
        Args:
            candidates: Ranked candidates to judge
            
        Returns:
            List of accepted papers
        """
        # Build contexts for all candidates
        candidates_with_context: list[tuple[SnowballCandidate, str]] = []

        for candidate in candidates:
            # Check budget before adding
            if len(self.accepted) + len(candidates_with_context) >= self.max_total_accepted:
                break

            parent_title = self.paper_titles.get(candidate.discovered_from, "Unknown")
            context = (f"Found as {candidate.edge_type.value} of '{parent_title[:50]}' "
                      f"at depth {candidate.depth}")
            candidates_with_context.append((candidate, context))

        # Judge all candidates concurrently
        tasks = [
            judge_candidate(self.profile, candidate, context)
            for candidate, context in candidates_with_context
        ]

        results: list[JudgmentResult] = await asyncio.gather(*tasks)

        # Process results
        new_accepted: list[AcceptedPaper] = []

        for idx, ((candidate, _), result) in enumerate(zip(candidates_with_context, results), 1):
            if result.relevant:
                # Check budget
                if len(self.accepted) >= self.max_total_accepted:
                    break

                accepted = AcceptedPaper(
                    paper_id=candidate.paper_id,
                    title=candidate.title,
                    abstract=candidate.abstract,
                    year=candidate.year,
                    citation_count=candidate.citation_count,
                    discovered_from=candidate.discovered_from,
                    edge_type=candidate.edge_type,
                    depth=candidate.depth,
                    judge_reason=result.reason,
                    judge_confidence=result.confidence,
                )
                self.accepted.append(accepted)
                new_accepted.append(accepted)

            if progress_callback and idx % 5 == 0:  # Update every 5 judgments
                progress_callback(5, "Running Snowball Search", idx, len(candidates_with_context), f"Iteration {iteration}: Judged {idx} of {len(candidates_with_context)} candidates, accepted {len(new_accepted)}", iteration, total_iterations)

        return new_accepted
