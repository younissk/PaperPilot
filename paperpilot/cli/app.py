"""Typer CLI application for PaperPilot.

This module provides the command-line interface for running literature
discovery searches and viewing results.
"""

import asyncio
import json
from pathlib import Path

import typer

from paperpilot.cli.console import (
    console,
    print_header,
    print_error,
    display_papers_table,
    print_step,
    print_success,
    print_warning,
    display_query_profile,
    display_augmented_queries,
    display_filtering_results,
    display_resolve_result,
    display_export_success,
    create_spinner_progress,
    display_clusters_table,
    display_cluster_export_success,
)
from paperpilot.cli.handlers import RichEventHandler
from paperpilot.core.models import AcceptedPaper, EdgeType
from paperpilot.core.augment import augment_search
from paperpilot.core.profiler import generate_query_profile
from paperpilot.core.search import search_all_queries
from paperpilot.core.filter import filter_results
from paperpilot.core.openalex import (
    resolve_arxiv_to_openalex,
    get_work_details,
    resolve_by_title,
    extract_openalex_id,
    extract_arxiv_id,
)
from paperpilot.core.models import ReducedArxivEntry, SnowballCandidate
from paperpilot.core.logging import configure_logging, get_logger
from paperpilot.core.results import ResultsManager
import aiohttp

# Configure logging for CLI mode
configure_logging(cli_mode=True)
logger = get_logger(__name__)

app = typer.Typer(
    name="paperpilot",
    help="AI-powered academic literature discovery using snowball sampling.",
    add_completion=False,
    rich_markup_mode="rich",
    no_args_is_help=False,  # Allow running without commands
)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """PaperPilot - Interactive academic literature discovery.
    
    If no command is provided, launches the interactive menu.
    """
    if ctx.invoked_subcommand is None:
        # No command provided, launch interactive menu
        from paperpilot.cli.interactive import run_interactive
        run_interactive()


async def run_search_with_display(
    query: str,
    num_results: int = 5,
    output_file: str = "",
    max_iterations: int = 5,
    max_accepted: int = 200,
    top_n: int = 50,
) -> None:
    """Run search with Rich console output."""
    # Initialize results manager
    results_manager = ResultsManager()
    
    # Create shared aiohttp session for all HTTP requests
    async with aiohttp.ClientSession() as session:
        # Step 1: Generate query profile
        print_step(1, "Generating query profile...")
        
        with create_spinner_progress() as progress:
            progress.add_task("Analyzing research domain...", total=None)
            profile = await generate_query_profile(query)
        
        display_query_profile(profile)
        console.print()
        
        # Step 2: Augment the search query
        print_step(2, "Augmenting search queries...")
        
        with create_spinner_progress() as progress:
            task = progress.add_task("Generating query variants...", total=None)
            augmented_queries, time_taken = await augment_search(query)
        
        display_augmented_queries(augmented_queries, time_taken)
        console.print()
        
        # Step 3: Search arXiv for all query variants CONCURRENTLY
        print_step(3, "Searching arXiv...")
        
        console.print(f"[dim]Searching {len(augmented_queries)} queries concurrently...[/dim]")
        
        # Search all queries concurrently
        feeds = await search_all_queries(session, augmented_queries, num_results)
        
        # Collect all results
        all_results: list[ReducedArxivEntry] = []
        
        for search_query, feed in zip(augmented_queries, feeds):
            for entry in feed.entries:
                html_link = next(
                    (link.href for link in entry.links if link.type == "text/html"), None
                )
                pdf_link = next(
                    (link.href for link in entry.links if link.type == "application/pdf"), None
                )
                
                all_results.append(ReducedArxivEntry(
                    title=entry.title,
                    updated=entry.updated,
                    summary=entry.summary,
                    link=html_link or pdf_link,
                    source_query=search_query,
                ))
        
        print_success(f"Found {len(all_results)} total results from arXiv")
        console.print()
        
        # Step 4: Filter results for relevance (CONCURRENT LLM calls)
        print_step(4, "Filtering results for relevance...")
        
        console.print("[dim]Running LLM relevance filter concurrently...[/dim]")
        filtered_results, discarded_results, total_time_taken = await filter_results(
            profile, all_results
        )
        
        display_filtering_results(filtered_results, discarded_results, total_time_taken)
        
        if filtered_results:
            console.print()
            display_papers_table(
                filtered_results,
                title="Relevant Papers",
                show_link=True,
                max_rows=10,
            )
        
        if not filtered_results:
            print_warning("No relevant papers found in initial search. Cannot start snowballing.")
            return
        
        console.print()
        
        # Step 5: Resolve arXiv papers to OpenAlex IDs (CONCURRENT)
        print_step(5, "Resolving papers to OpenAlex...")
        print_header("OpenAlex Resolution", "bold cyan")
        
        console.print("[dim]Resolving papers concurrently...[/dim]")
        
        # Resolve all papers concurrently
        seeds = await _resolve_papers_to_openalex_with_display(session, filtered_results)
        
        print_success(f"Resolved {len(seeds)} of {len(filtered_results)} papers")
        
        if not seeds:
            print_warning("No papers could be resolved to OpenAlex. Cannot start snowballing.")
            return
        
        console.print()
        
        # Step 6: Run the Snowball Engine
        print_step(6, "Running snowball discovery...")
        
        from paperpilot.core.snowball import SnowballEngine
        
        engine = SnowballEngine(
            profile=profile,
            max_iterations=max_iterations,
            top_n_per_iteration=top_n,
            min_new_papers_threshold=3,
            max_total_accepted=max_accepted,
        )
        
        accepted_papers = await engine.run(session, seeds)
        
        # Step 7: Export results
        print_step(7, "Exporting results...")
        from paperpilot.core.service import export_results
        
        # Use ResultsManager if output_file not specified
        if not output_file:
            saved_path = results_manager.save_snowball(query, {
                "query": query,
                "total_accepted": len(accepted_papers),
                "papers": [
                    {
                        "paper_id": p.paper_id,
                        "title": p.title,
                        "year": p.year,
                        "citation_count": p.citation_count,
                        "discovered_from": p.discovered_from,
                        "edge_type": p.edge_type.value,
                        "depth": p.depth,
                        "judge_reason": p.judge_reason,
                        "judge_confidence": p.judge_confidence,
                        "abstract": p.abstract[:500] if p.abstract else None,
                    }
                    for p in accepted_papers
                ],
            })
            output_file = str(saved_path)
        else:
            export_results(accepted_papers, query, output_file)
        
        display_export_success(output_file, len(accepted_papers), query)


async def _resolve_papers_to_openalex_with_display(
    session: aiohttp.ClientSession,
    filtered_results: list[ReducedArxivEntry]
) -> list[SnowballCandidate]:
    """Resolve arXiv papers to OpenAlex IDs concurrently with display."""
    
    async def resolve_single_paper(result: ReducedArxivEntry) -> tuple[ReducedArxivEntry, SnowballCandidate | None]:
        """Resolve a single paper, returning (result, candidate or None)."""
        # Try to resolve via arXiv DOI first
        openalex_id = await resolve_arxiv_to_openalex(session, result.link) if result.link else None
        
        # Fallback: search by title
        if not openalex_id:
            paper_data = await resolve_by_title(session, result.title)
            if paper_data:
                openalex_id = extract_openalex_id(paper_data)
        
        if openalex_id:
            details = await get_work_details(session, openalex_id)
            arxiv_id = extract_arxiv_id(result.link) if result.link else None
            
            seed = SnowballCandidate(
                paper_id=openalex_id,
                title=result.title,
                abstract=result.summary,
                year=details.get("publication_year") if details else None,
                citation_count=details.get("cited_by_count", 0) if details else 0,
                influential_citation_count=0,
                discovered_from=result.source_query,
                edge_type=EdgeType.SEED,
                depth=0,
                arxiv_id=arxiv_id,
            )
            return result, seed
        
        return result, None
    
    # Resolve all papers concurrently
    tasks = [resolve_single_paper(result) for result in filtered_results]
    results = await asyncio.gather(*tasks)
    
    # Collect seeds and display results
    seeds: list[SnowballCandidate] = []
    
    for result, seed in results:
        if seed:
            seeds.append(seed)
            display_resolve_result(
                result.title,
                success=True,
                openalex_id=seed.paper_id,
                citations=seed.citation_count,
                year=seed.year,
            )
        else:
            display_resolve_result(result.title, success=False)
    
    return seeds


@app.command()
def search(
    query: str = typer.Argument(
        ...,
        help="Research topic to search for (e.g., 'LLM Based Recommendation Systems')",
    ),
    num_results: int = typer.Option(
        5,
        "-n", "--num-results",
        help="Number of results per query variant",
        min=1,
        max=100,
    ),
    output: str = typer.Option(
        "snowball_results.json",
        "-o", "--output",
        help="Output file for results",
    ),
    max_iterations: int = typer.Option(
        5,
        "--max-iterations",
        help="Maximum snowball iterations",
        min=1,
        max=20,
    ),
    max_accepted: int = typer.Option(
        200,
        "--max-accepted",
        help="Maximum total papers to accept",
        min=10,
    ),
    top_n: int = typer.Option(
        50,
        "--top-n",
        help="Top N candidates to judge per iteration",
        min=5,
    ),
) -> None:
    """Search for papers and run snowball discovery.
    
    This command performs the full PaperPilot workflow:
    
    1. Generate a query profile using LLM
    2. Augment the search with query variants
    3. Search arXiv for initial papers
    4. Filter results for relevance
    5. Resolve papers to OpenAlex IDs
    6. Run iterative snowball sampling
    7. Export results to JSON
    """
    print_header("PaperPilot", "bold blue")
    console.print(f"[bold]Query:[/bold] {query}")
    console.print(f"[bold]Results per query:[/bold] {num_results}")
    console.print(f"[bold]Output:[/bold] {output}")
    console.print("[dim]Using async concurrency for faster execution[/dim]")
    console.print()
    
    try:
        # Run the async search workflow with display
        asyncio.run(
            run_search_with_display(
                query=query,
                num_results=num_results,
                output_file=output,
                max_iterations=max_iterations,
                max_accepted=max_accepted,
                top_n=top_n,
            )
        )
    except KeyboardInterrupt:
        console.print()
        print_error("Search interrupted by user")
        raise typer.Exit(code=1)
    except Exception as e:
        print_error(f"Search failed: {e}")
        raise typer.Exit(code=1)


@app.command()
def results(
    file: str = typer.Argument(
        "snowball_results.json",
        help="Results file to display",
    ),
    top: int = typer.Option(
        20,
        "-t", "--top",
        help="Number of top papers to show",
        min=1,
    ),
    sort_by: str = typer.Option(
        "citations",
        "-s", "--sort",
        help="Sort by: citations, year, depth",
    ),
    show_abstracts: bool = typer.Option(
        False,
        "-a", "--abstracts",
        help="Show paper abstracts",
    ),
) -> None:
    """Display results from a previous search.
    
    View and analyze papers from a snowball_results.json file.
    """
    file_path = Path(file)
    
    if not file_path.exists():
        print_error(f"Results file not found: {file}")
        raise typer.Exit(code=1)
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON in results file: {e}")
        raise typer.Exit(code=1)
    
    print_header(f"Results: {data.get('query', 'Unknown')}", "bold blue")
    
    papers = data.get("papers", [])
    total = data.get("total_accepted", len(papers))
    
    console.print(f"[bold]Total papers:[/bold] {total}")
    console.print(f"[bold]Query:[/bold] {data.get('query', 'N/A')}")
    console.print()
    
    if not papers:
        print_error("No papers in results file")
        raise typer.Exit(code=1)
    
    # Convert to objects for easier handling
    paper_objects = []
    for p in papers:
        paper_objects.append(
            AcceptedPaper(
                paper_id=p.get("paper_id", ""),
                title=p.get("title", "Unknown"),
                abstract=p.get("abstract"),
                year=p.get("year"),
                citation_count=p.get("citation_count", 0),
                discovered_from=p.get("discovered_from"),
                edge_type=EdgeType(p.get("edge_type", "seed")),
                depth=p.get("depth", 0),
                judge_reason=p.get("judge_reason", ""),
                judge_confidence=p.get("judge_confidence", 0.0),
            )
        )
    
    # Sort papers
    if sort_by == "citations":
        paper_objects.sort(key=lambda p: p.citation_count, reverse=True)
    elif sort_by == "year":
        paper_objects.sort(key=lambda p: p.year or 0, reverse=True)
    elif sort_by == "depth":
        paper_objects.sort(key=lambda p: p.depth)
    
    # Display table
    display_papers_table(
        paper_objects[:top],
        title=f"Top {min(top, len(paper_objects))} Papers (sorted by {sort_by})",
        show_depth=True,
        show_judge=True,
    )
    
    if show_abstracts:
        console.print()
        print_header("Abstracts", "bold cyan")
        for i, p in enumerate(paper_objects[:top], 1):
            if p.abstract:
                console.print(f"[bold cyan]{i}. {p.title}[/bold cyan]")
                console.print(f"[dim]{p.abstract}[/dim]")
                console.print()
    
    # Show summary stats
    console.print()
    seeds = sum(1 for p in paper_objects if p.edge_type == EdgeType.SEED)
    refs = sum(1 for p in paper_objects if p.edge_type == EdgeType.REFERENCE)
    cites = sum(1 for p in paper_objects if p.edge_type == EdgeType.CITATION)
    
    console.print("[bold]Breakdown:[/bold]")
    console.print(f"  Seeds: {seeds} | References: {refs} | Citations: {cites}")


@app.command()
def rank(
    file: str = typer.Argument(
        "snowball_results.json",
        help="Results file to rank with Elo",
    ),
    n_matches: int = typer.Option(
        None,
        "-m", "--matches",
        help="Number of matches to run (default: papers * 3)",
    ),
    k_factor: float = typer.Option(
        32.0,
        "-k", "--k-factor",
        help="K-factor for Elo updates (higher = more volatile)",
        min=1.0,
        max=100.0,
    ),
    pairing: str = typer.Option(
        "swiss",
        "-p", "--pairing",
        help="Pairing strategy: random or swiss (default: swiss)",
    ),
    early_stop: bool = typer.Option(
        True,
        "--early-stop/--no-early-stop",
        help="Stop when top-30 rankings stabilize (default: enabled)",
    ),
    concurrency: int = typer.Option(
        5,
        "-c", "--concurrency",
        help="Max concurrent API calls (default: 5)",
        min=1,
        max=20,
    ),
    tournament: bool = typer.Option(
        False,
        "--tournament/--no-tournament",
        help="Use tournament rounds instead of stability-based stopping",
    ),
    output: str = typer.Option(
        None,
        "-o", "--output",
        help="Output file for ranked results (default: elo_ranked_<input>)",
    ),
    quiet: bool = typer.Option(
        False,
        "-q", "--quiet",
        help="Disable interactive display",
    ),
) -> None:
    """Rank papers using Elo rating system with interactive display.
    
    This command runs an Elo ranking tournament where papers "battle" each other
    using LLM judgment. The result is a relevance-based ranking that considers
    pairwise comparisons rather than independent scoring.
    
    Features:
    - Swiss-style pairing for informative matches (after calibration)
    - Relevance-first prompts (quality as tiebreaker only)
    - Early stopping when rankings stabilize
    - Concurrent match execution for speed
    
    Live interactive display shows:
    - Real-time Elo standings
    - Current match being judged
    - Match history and statistics
    
    Example:
        paperpilot rank snowball_results.json -m 100 -k 32 --pairing swiss --concurrency 5
    """
    file_path = Path(file)
    
    if not file_path.exists():
        print_error(f"Results file not found: {file}")
        raise typer.Exit(code=1)
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON in results file: {e}")
        raise typer.Exit(code=1)
    
    papers = data.get("papers", [])
    query = data.get("query", "Unknown")
    
    if not papers:
        print_error("No papers in results file")
        raise typer.Exit(code=1)
    
    if len(papers) < 2:
        print_error("Need at least 2 papers for Elo ranking")
        raise typer.Exit(code=1)
    
    if pairing not in ["random", "swiss"]:
        print_error(f"Invalid pairing strategy: {pairing}. Must be 'random' or 'swiss'")
        raise typer.Exit(code=1)
    
    print_header("Elo Ranking", "bold cyan")
    console.print(f"[bold]Query:[/bold] {query}")
    console.print(f"[bold]Papers:[/bold] {len(papers)}")
    console.print(f"[bold]Matches:[/bold] {n_matches or len(papers) * 3}")
    console.print(f"[bold]K-factor:[/bold] {k_factor}")
    console.print(f"[bold]Pairing:[/bold] {pairing}")
    console.print(f"[bold]Early stop:[/bold] {early_stop}")
    console.print(f"[bold]Concurrency:[/bold] {concurrency}")
    if tournament:
        console.print("[bold]Tournament mode:[/bold] enabled")
    console.print()
    
    try:
        asyncio.run(
            run_elo_ranking(
                papers=papers,
                query=query,
                n_matches=n_matches,
                k_factor=k_factor,
                pairing=pairing,
                early_stop=early_stop,
                concurrency=concurrency,
                tournament=tournament,
                output_file=output or f"elo_ranked_{file_path.name}",
                interactive=not quiet,
            )
        )
    except KeyboardInterrupt:
        console.print()
        print_error("Ranking interrupted by user")
        raise typer.Exit(code=1)
    except Exception as e:
        print_error(f"Ranking failed: {e}")
        raise typer.Exit(code=1)


async def run_elo_ranking(
    papers: list,
    query: str,
    n_matches: int | None,
    k_factor: float,
    pairing: str,
    early_stop: bool,
    concurrency: int,
    tournament: bool,
    output_file: str,
    interactive: bool,
) -> None:
    """Run Elo ranking on papers."""
    from paperpilot.core.elo_ranker import EloRanker, RankerConfig
    from paperpilot.core.profiler import generate_query_profile
    
    # Generate query profile for relevance judgment
    console.print("[dim]Generating query profile for relevance judgment...[/dim]")
    profile = await generate_query_profile(query)
    console.print()
    
    # Convert papers to SnowballCandidate objects
    candidates = []
    for p in papers:
        candidate = SnowballCandidate(
            paper_id=p.get("paper_id", ""),
            title=p.get("title", "Unknown"),
            abstract=p.get("abstract"),
            year=p.get("year"),
            citation_count=p.get("citation_count", 0),
            influential_citation_count=0,
            discovered_from=p.get("discovered_from"),
            edge_type=EdgeType(p.get("edge_type", "seed")),
            depth=p.get("depth", 0),
        )
        candidates.append(candidate)
    
    # Create configuration
    config = RankerConfig(
        k_factor=k_factor,
        max_matches=n_matches,
        pairing_strategy=pairing,
        early_stop_enabled=early_stop,
        concurrency=concurrency,
        tournament_mode=tournament,
        interactive=interactive,
    )
    
    # Create event handler for Rich display
    event_handler = RichEventHandler(console=console) if interactive else None
    
    # Create and run Elo ranker
    ranker = EloRanker(
        profile=profile,
        candidates=candidates,
        config=config,
        event_handler=event_handler,
    )
    
    ranked = await ranker.rank_candidates()
    
    # Export ranked results
    ranked_papers = []
    for i, ce in enumerate(ranked, 1):
        ranked_papers.append({
            "rank": i,
            "elo": round(ce.elo, 1),
            "elo_change": round(ce.elo - 1500, 1),
            "wins": ce.wins,
            "losses": ce.losses,
            "draws": ce.draws,
            "paper_id": ce.candidate.paper_id,
            "title": ce.candidate.title,
            "year": ce.candidate.year,
            "citation_count": ce.candidate.citation_count,
            "abstract": ce.candidate.abstract[:500] if ce.candidate.abstract else None,
        })
    
    results = {
        "query": query,
        "ranking_method": "elo",
        "k_factor": k_factor,
        "total_matches": len(ranker.match_history),
        "total_papers": len(ranked),
        "papers": ranked_papers,
    }
    
    # Use ResultsManager if output_file not specified
    results_manager = ResultsManager()
    if not output_file:
        saved_path = results_manager.save_elo_ranking(
            query, 
            results,
            pairing=pairing,
            k_factor=k_factor,
        )
        output_file = str(saved_path)
    else:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    
    console.print()
    print_success(f"Ranked results exported to: {output_file}")


@app.command()
def cluster(
    file: str = typer.Argument(
        "snowball_results.json",
        help="Input results file to cluster",
    ),
    method: str = typer.Option(
        "hdbscan",
        "-m", "--method",
        help="Clustering method: hdbscan, dbscan (auto k), or kmeans (manual k)",
    ),
    n_clusters: int = typer.Option(
        None,
        "-k", "--n-clusters",
        help="Number of clusters (kmeans only, default: 5)",
    ),
    dim_method: str = typer.Option(
        "umap",
        "-d", "--dim-method",
        help="Dimension reduction: umap, tsne, or pca",
    ),
    eps: float = typer.Option(
        None,
        "--eps",
        help="Eps parameter for DBSCAN (auto-selected if not provided)",
    ),
    min_samples: int = typer.Option(
        None,
        "--min-samples",
        help="Min samples for DBSCAN/HDBSCAN (default: 2)",
    ),
    output: str = typer.Option(
        "clusters.json",
        "-o", "--output",
        help="Output JSON file for cluster assignments",
    ),
    html: str = typer.Option(
        "clusters.html",
        "--html",
        help="Output HTML file for interactive visualization",
    ),
) -> None:
    """Cluster papers by semantic similarity.
    
    This command performs semantic clustering of papers:
    
    1. Embed paper title + abstract using OpenAI embeddings
    2. Reduce dimensions with UMAP, t-SNE, or PCA
    3. Cluster using HDBSCAN, DBSCAN, or KMeans
    4. Display clusters in the terminal
    5. Export to JSON and interactive HTML
    
    Note: UMAP and HDBSCAN require Python < 3.13 and the cluster-full
    optional dependencies. On Python 3.13+, PCA and DBSCAN are used
    as fallbacks automatically.
    
    Example:
        paperpilot cluster snowball_results.json -m hdbscan -d umap
        paperpilot cluster snowball_results.json -m kmeans -k 5 -d tsne
        paperpilot cluster snowball_results.json -d pca -m kmeans -k 8
    """
    file_path = Path(file)
    
    if not file_path.exists():
        print_error(f"Results file not found: {file}")
        raise typer.Exit(code=1)
    
    # Validate options
    if method not in ["hdbscan", "dbscan", "kmeans"]:
        print_error(f"Invalid clustering method: {method}. Use 'hdbscan', 'dbscan', or 'kmeans'")
        raise typer.Exit(code=1)
    
    if dim_method not in ["umap", "tsne", "pca"]:
        print_error(f"Invalid dimension reduction method: {dim_method}. Use 'umap', 'tsne', or 'pca'")
        raise typer.Exit(code=1)
    
    if method == "kmeans" and n_clusters is None:
        n_clusters = 5  # Default for kmeans
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON in results file: {e}")
        raise typer.Exit(code=1)
    
    papers = data.get("papers", [])
    query = data.get("query", "Unknown")
    
    if not papers:
        print_error("No papers in results file")
        raise typer.Exit(code=1)
    
    if len(papers) < 3:
        print_error("Need at least 3 papers for clustering")
        raise typer.Exit(code=1)
    
    print_header("Paper Clustering", "bold magenta")
    console.print(f"[bold]Query:[/bold] {query}")
    console.print(f"[bold]Papers:[/bold] {len(papers)}")
    console.print(f"[bold]Method:[/bold] {method.upper()}")
    console.print(f"[bold]Dim reduction:[/bold] {dim_method.upper()}")
    if method == "kmeans":
        console.print(f"[bold]K:[/bold] {n_clusters}")
    if method in ["dbscan", "hdbscan"]:
        if eps is not None:
            console.print(f"[bold]Eps:[/bold] {eps}")
        if min_samples is not None:
            console.print(f"[bold]Min samples:[/bold] {min_samples}")
    console.print()
    
    try:
        run_clustering(
            papers=papers,
            query=query,
            cluster_method=method,
            dim_method=dim_method,
            n_clusters=n_clusters,
            eps=eps,
            min_samples=min_samples,
            output_file=output,
            html_file=html,
        )
    except KeyboardInterrupt:
        console.print()
        print_error("Clustering interrupted by user")
        raise typer.Exit(code=1)
    except Exception as e:
        print_error(f"Clustering failed: {e}")
        raise typer.Exit(code=1)


def run_clustering(
    papers: list,
    query: str,
    cluster_method: str,
    dim_method: str,
    n_clusters: int | None,
    eps: float | None,
    min_samples: int | None,
    output_file: str,
    html_file: str,
) -> None:
    """Run the clustering pipeline with display."""
    from paperpilot.core.cluster import ClusteringEngine
    from paperpilot.core.visualize import save_cluster_visualization
    
    engine = ClusteringEngine()
    
    # Check feature availability and warn about fallbacks
    features = engine.get_available_features()
    if dim_method == "umap" and not features["umap"]:
        print_warning("umap-learn not installed - using PCA for dimension reduction")
        dim_method = "pca"
    if cluster_method == "hdbscan" and not features["hdbscan"]:
        print_warning("hdbscan not installed - using DBSCAN for clustering")
        cluster_method = "dbscan"
    console.print()
    
    # Step 1: Embed papers
    print_step(1, "Embedding papers with OpenAI...")
    with create_spinner_progress() as progress:
        progress.add_task("Generating embeddings...", total=None)
        embeddings = engine.embed_papers(papers)
    print_success(f"Generated {embeddings.shape[0]} embeddings ({embeddings.shape[1]} dims)")
    console.print()
    
    # Step 2: Reduce dimensions
    print_step(2, f"Reducing dimensions with {dim_method.upper()}...")
    with create_spinner_progress() as progress:
        progress.add_task("Fitting dimension reduction...", total=None)
        coords_2d = engine.reduce_dimensions(embeddings, method=dim_method)
    print_success("Reduced to 2D coordinates")
    console.print()
    
    # Step 3: Cluster
    print_step(3, f"Clustering with {cluster_method.upper()}...")
    with create_spinner_progress() as progress:
        progress.add_task("Finding clusters...", total=None)
        labels = engine.cluster(
            embeddings,
            method=cluster_method,
            n_clusters=n_clusters,
            eps=eps,
            min_samples=min_samples,
        )
    
    # Show auto-selected eps if DBSCAN was used
    if cluster_method == "dbscan" and eps is None and hasattr(engine, '_last_eps') and engine._last_eps is not None:
        console.print(f"[dim]Auto-selected eps: {engine._last_eps:.4f}[/dim]")
    
    # Get summaries
    summaries = engine.get_cluster_summaries(papers, labels)
    actual_clusters = len([s for s in summaries if s.cluster_id != -1])
    print_success(f"Found {actual_clusters} clusters")
    
    # Warn if too few clusters found (heuristic: < 3 clusters for > 20 papers)
    if actual_clusters < 3 and len(papers) > 20:
        print_warning(
            f"Only {actual_clusters} cluster(s) found for {len(papers)} papers. "
            f"This may indicate clustering parameters need tuning. "
            f"Try adjusting --eps or --min-samples, or use -m kmeans -k <n> for manual clustering."
        )
    console.print()
    
    # Step 4: Display results
    print_step(4, "Displaying cluster analysis...")
    console.print()
    display_clusters_table(summaries, len(papers), cluster_method, dim_method)
    
    # Step 5: Export
    print_step(5, "Exporting results...")
    
    # Build clustering result for export
    from paperpilot.core.cluster import ClusteringResult
    result = ClusteringResult(
        method=cluster_method,
        dim_reduction=dim_method,
        n_clusters=actual_clusters,
        labels=labels,
        coords_2d=coords_2d,
        cluster_summaries=summaries,
        papers=papers,
    )
    
    # Export JSON
    json_data = engine.to_json(result)
    json_data["query"] = query
    
    # Use ResultsManager if output files not specified
    results_manager = ResultsManager()
    if not output_file or not html_file:
        # Generate HTML content to string by saving to temp file first
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
            tmp_html = tmp.name
        
        from paperpilot.core.visualize import save_cluster_visualization
        save_cluster_visualization(result, tmp_html, title=f"Paper Clusters: {query}")
        
        # Read HTML content
        with open(tmp_html, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        import os
        os.unlink(tmp_html)
        
        json_path, html_path = results_manager.save_clusters(
            query,
            json_data,
            html_content,
            method=cluster_method,
            dim_reduction=dim_method,
            n_clusters=n_clusters if cluster_method == "kmeans" else None,
        )
        output_file = str(json_path)
        html_file = str(html_path) if html_path else html_file
    else:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        from paperpilot.core.visualize import save_cluster_visualization
        save_cluster_visualization(result, html_file, title=f"Paper Clusters: {query}")
    
    console.print()
    display_cluster_export_success(output_file, html_file, len(papers), actual_clusters)


@app.command()
def timeline(
    file: str = typer.Argument(
        "snowball_results.json",
        help="Input results file to create timeline from",
    ),
    output: str = typer.Option(
        None,
        "-o", "--output",
        help="Output JSON file (default: timeline.json)",
    ),
    html: str = typer.Option(
        None,
        "--html",
        help="Output HTML file (default: timeline.html)",
    ),
) -> None:
    """Create a chronological timeline of papers.
    
    This command creates a timeline visualization showing when papers
    were published, grouped by year.
    
    Example:
        paperpilot timeline snowball_results.json
    """
    file_path = Path(file)
    
    if not file_path.exists():
        print_error(f"Results file not found: {file}")
        raise typer.Exit(code=1)
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON in results file: {e}")
        raise typer.Exit(code=1)
    
    papers = data.get("papers", [])
    query = data.get("query", "Unknown")
    
    if not papers:
        print_error("No papers in results file")
        raise typer.Exit(code=1)
    
    print_header("Timeline Creator", "bold yellow")
    console.print(f"[bold]Query:[/bold] {query}")
    console.print(f"[bold]Papers:[/bold] {len(papers)}")
    console.print()
    
    try:
        from paperpilot.core.timeline import create_timeline
        from paperpilot.core.visualize import save_timeline_visualization
        
        # Create timeline data
        print_step(1, "Creating timeline...")
        timeline_data = create_timeline(papers, query)
        
        year_range = timeline_data.get("year_range", {})
        if year_range.get("min") and year_range.get("max"):
            console.print(f"[dim]Year range: {year_range['min']} - {year_range['max']}[/dim]")
        
        print_success(f"Timeline created with {len(timeline_data.get('timeline', []))} years")
        console.print()
        
        # Generate visualization
        print_step(2, "Generating visualization...")
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
            tmp_html = tmp.name
        
        save_timeline_visualization(timeline_data, tmp_html, title=f"Paper Timeline: {query}")
        
        # Read HTML content
        with open(tmp_html, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        import os
        os.unlink(tmp_html)
        
        # Save using ResultsManager
        results_manager = ResultsManager()
        if not output or not html:
            json_path, html_path = results_manager.save_timeline(
                query,
                timeline_data,
                html_content,
            )
            output = str(json_path)
            html = str(html_path) if html_path else html
        else:
            with open(output, "w", encoding="utf-8") as f:
                json.dump(timeline_data, f, indent=2, ensure_ascii=False)
            save_timeline_visualization(timeline_data, html, title=f"Paper Timeline: {query}")
        
        console.print()
        print_success(f"Timeline exported to: {output}")
        if html:
            print_success(f"Visualization exported to: {html}")
        
    except KeyboardInterrupt:
        console.print()
        print_error("Timeline creation interrupted by user")
        raise typer.Exit(code=1)
    except Exception as e:
        print_error(f"Timeline creation failed: {e}")
        raise typer.Exit(code=1)


@app.command()
def graph(
    file: str = typer.Argument(
        "snowball_results.json",
        help="Input results file to create graph from",
    ),
    direction: str = typer.Option(
        "both",
        "-d", "--direction",
        help="Graph direction: both, citations, or references",
    ),
    limit: int = typer.Option(
        100,
        "-l", "--limit",
        help="Maximum refs/cites to fetch per paper",
        min=1,
        max=500,
    ),
    output: str = typer.Option(
        None,
        "-o", "--output",
        help="Output JSON file (default: graph_<direction>_l<limit>.json)",
    ),
    html: str = typer.Option(
        None,
        "--html",
        help="Output HTML file (default: graph_<direction>_l<limit>.html)",
    ),
) -> None:
    """Create a citation/reference graph of papers.
    
    This command builds a graph showing how papers in the snowball
    are connected through citations and references.
    
    Example:
        paperpilot graph snowball_results.json
        paperpilot graph snowball_results.json -d citations -l 50
    """
    file_path = Path(file)
    
    if not file_path.exists():
        print_error(f"Results file not found: {file}")
        raise typer.Exit(code=1)
    
    if direction not in ["both", "citations", "references"]:
        print_error(f"Invalid direction: {direction}. Use 'both', 'citations', or 'references'")
        raise typer.Exit(code=1)
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON in results file: {e}")
        raise typer.Exit(code=1)
    
    papers = data.get("papers", [])
    query = data.get("query", "Unknown")
    
    if not papers:
        print_error("No papers in results file")
        raise typer.Exit(code=1)
    
    print_header("Source Graph Builder", "bold green")
    console.print(f"[bold]Query:[/bold] {query}")
    console.print(f"[bold]Papers:[/bold] {len(papers)}")
    console.print(f"[bold]Direction:[/bold] {direction}")
    console.print(f"[bold]Limit per paper:[/bold] {limit}")
    console.print()
    
    try:
        from paperpilot.core.graph import build_citation_graph
        from paperpilot.core.visualize import save_graph_visualization
        
        # Build graph
        print_step(1, "Fetching citation/reference data from OpenAlex...")
        async def run_graph_building():
            async with aiohttp.ClientSession() as session:
                graph_data = await build_citation_graph(
                    session,
                    papers,
                    query=query,
                    direction=direction,
                    limit=limit,
                )
                return graph_data
        
        graph_data = asyncio.run(run_graph_building())
        
        print_success(f"Graph built: {graph_data.get('total_papers', 0)} nodes, {graph_data.get('total_edges', 0)} edges")
        console.print()
        
        # Generate visualization
        print_step(2, "Generating visualization...")
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
            tmp_html = tmp.name
        
        save_graph_visualization(graph_data, tmp_html, title=f"Citation Graph: {query}")
        
        # Read HTML content
        with open(tmp_html, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        import os
        os.unlink(tmp_html)
        
        # Save using ResultsManager
        results_manager = ResultsManager()
        if not output or not html:
            json_path, html_path = results_manager.save_graph(
                query,
                graph_data,
                html_content,
                direction=direction,
                limit=limit,
            )
            output = str(json_path)
            html = str(html_path) if html_path else html
        else:
            with open(output, "w", encoding="utf-8") as f:
                json.dump(graph_data, f, indent=2, ensure_ascii=False)
            save_graph_visualization(graph_data, html, title=f"Citation Graph: {query}")
        
        console.print()
        print_success(f"Graph exported to: {output}")
        if html:
            print_success(f"Visualization exported to: {html}")
        
    except KeyboardInterrupt:
        console.print()
        print_error("Graph building interrupted by user")
        raise typer.Exit(code=1)
    except Exception as e:
        print_error(f"Graph building failed: {e}")
        raise typer.Exit(code=1)


@app.command()
def everything(
    file: str = typer.Argument(
        "snowball_results.json",
        help="Input results file to process",
    ),
) -> None:
    """Run all analysis features with default parameters.
    
    This command runs all features sequentially:
    1. Elo ranking (swiss pairing, k_factor=32)
    2. Clustering (hdbscan, umap)
    3. Timeline
    4. Source graph (both directions, limit=100)
    
    Example:
        paperpilot everything snowball_results.json
    """
    file_path = Path(file)
    
    if not file_path.exists():
        print_error(f"Results file not found: {file}")
        raise typer.Exit(code=1)
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON in results file: {e}")
        raise typer.Exit(code=1)
    
    papers = data.get("papers", [])
    query = data.get("query", "Unknown")
    
    if not papers:
        print_error("No papers in results file")
        raise typer.Exit(code=1)
    
    print_header("Everything Mode", "bold cyan")
    console.print(f"[bold]Query:[/bold] {query}")
    console.print(f"[bold]Papers:[/bold] {len(papers)}")
    console.print()
    
    results_manager = ResultsManager()
    generated_files = []
    
    try:
        # 1. Elo Ranking
        console.print("[bold cyan]1. Running Elo Ranking...[/bold cyan]")
        console.print()
        try:
            asyncio.run(run_elo_ranking(
                papers=papers,
                query=query,
                n_matches=None,  # Auto
                k_factor=32.0,
                pairing="swiss",
                early_stop=True,
                concurrency=5,
                tournament=False,
                output_file="",  # Use ResultsManager
                interactive=False,
            ))
            # Get the generated file from metadata
            metadata = results_manager.get_metadata(query)
            if metadata and metadata.get("elo_file"):
                generated_files.append(metadata["elo_file"])
        except Exception as e:
            print_warning(f"Elo ranking failed: {e}")
        
        console.print()
        console.print()
        
        # 2. Clustering
        console.print("[bold magenta]2. Running Clustering...[/bold magenta]")
        console.print()
        try:
            run_clustering(
                papers=papers,
                query=query,
                cluster_method="hdbscan",
                dim_method="umap",
                n_clusters=None,
                eps=None,
                min_samples=None,
                output_file="",  # Use ResultsManager
                html_file="",  # Use ResultsManager
            )
            # Get the generated files from metadata
            metadata = results_manager.get_metadata(query)
            if metadata:
                if metadata.get("clusters_json"):
                    generated_files.append(metadata["clusters_json"])
                if metadata.get("clusters_html"):
                    generated_files.append(metadata["clusters_html"])
        except Exception as e:
            print_warning(f"Clustering failed: {e}")
        
        console.print()
        console.print()
        
        # 3. Timeline
        console.print("[bold yellow]3. Creating Timeline...[/bold yellow]")
        console.print()
        try:
            from paperpilot.core.timeline import create_timeline
            from paperpilot.core.visualize import save_timeline_visualization
            
            timeline_data = create_timeline(papers, query)
            
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
                tmp_html = tmp.name
            
            save_timeline_visualization(timeline_data, tmp_html, title=f"Paper Timeline: {query}")
            
            with open(tmp_html, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            import os
            os.unlink(tmp_html)
            
            json_path, html_path = results_manager.save_timeline(
                query,
                timeline_data,
                html_content,
            )
            generated_files.append(json_path.name)
            if html_path:
                generated_files.append(html_path.name)
            
            print_success(f"Timeline created: {json_path.name}")
        except Exception as e:
            print_warning(f"Timeline creation failed: {e}")
        
        console.print()
        console.print()
        
        # 4. Source Graph
        console.print("[bold green]4. Building Source Graph...[/bold green]")
        console.print()
        try:
            from paperpilot.core.graph import build_citation_graph
            from paperpilot.core.visualize import save_graph_visualization
            
            async def run_graph():
                async with aiohttp.ClientSession() as session:
                    graph_data = await build_citation_graph(
                        session,
                        papers,
                        query=query,
                        direction="both",
                        limit=100,
                    )
                    return graph_data
            
            graph_data = asyncio.run(run_graph())
            
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
                tmp_html = tmp.name
            
            save_graph_visualization(graph_data, tmp_html, title=f"Citation Graph: {query}")
            
            with open(tmp_html, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            import os
            os.unlink(tmp_html)
            
            json_path, html_path = results_manager.save_graph(
                query,
                graph_data,
                html_content,
                direction="both",
                limit=100,
            )
            generated_files.append(json_path.name)
            if html_path:
                generated_files.append(html_path.name)
            
            print_success(f"Graph built: {json_path.name}")
        except Exception as e:
            print_warning(f"Graph building failed: {e}")
        
        console.print()
        console.print()
        print_header("Summary", "bold green")
        console.print(f"[bold]Generated {len(generated_files)} files:[/bold]")
        for fname in generated_files:
            console.print(f"  • {fname}")
        console.print()
        query_dir = results_manager.get_query_dir(query)
        print_success(f"All results saved to: {query_dir}")
        
    except KeyboardInterrupt:
        console.print()
        print_error("Everything mode interrupted by user")
        raise typer.Exit(code=1)
    except Exception as e:
        print_error(f"Everything mode failed: {e}")
        raise typer.Exit(code=1)


@app.command()
def report(
    file: str = typer.Argument(
        "snowball.json",
        help="Snowball results file to generate report from",
    ),
    top_k: int = typer.Option(
        30,
        "-k", "--top-k",
        help="Number of top papers to use (default: 30)",
    ),
    elo_file: str = typer.Option(
        None,
        "-e", "--elo",
        help="Elo ranking file (auto-detected if not specified)",
    ),
    output: str = typer.Option(
        None,
        "-o", "--output",
        help="Output file path (default: report.json in query folder)",
    ),
) -> None:
    """Generate a structured research report from papers.
    
    This command creates a citation-safe research report by:
    
    1. Selecting top-k papers from elo ranking or snowball results
    2. Building structured paper cards with claims and metadata
    3. Generating a thematic outline based on research paradigms
    4. Writing sections with enforced citations
    5. Auditing citations for accuracy
    
    The report includes:
    - Introduction to the research topic
    - Current research themes with citations
    - Open problems identified from limitations
    - Conclusion with future directions
    
    Example:
        paperpilot report snowball.json -k 30
        paperpilot report snowball.json --elo elo_ranked.json -k 20
        paperpilot report results/my_query/snowball.json -o my_report.json
    """
    from paperpilot.core.report.generator import generate_report, report_to_dict
    
    file_path = Path(file)
    
    if not file_path.exists():
        print_error(f"Results file not found: {file}")
        raise typer.Exit(code=1)
    
    # Initialize results manager
    results_manager = ResultsManager()
    
    # Determine elo file path
    elo_path = None
    if elo_file:
        elo_path = Path(elo_file)
        if not elo_path.exists():
            print_warning(f"Elo file not found: {elo_file}, will use snowball results")
            elo_path = None
    else:
        # Try to auto-detect elo file in the same directory
        parent_dir = file_path.parent
        elo_candidates = list(parent_dir.glob("elo_ranked*.json"))
        if elo_candidates:
            # Use the most recent one
            elo_path = max(elo_candidates, key=lambda p: p.stat().st_mtime)
            console.print(f"[dim]Auto-detected elo file: {elo_path.name}[/dim]")
    
    # Load data to get query
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON in results file: {e}")
        raise typer.Exit(code=1)
    
    query = data.get("query", "Unknown query")
    total_papers = len(data.get("papers", []))
    
    if total_papers == 0:
        print_error("No papers in results file")
        raise typer.Exit(code=1)
    
    print_header("Report Generation", "bold cyan")
    console.print(f"[bold]Query:[/bold] {query}")
    console.print(f"[bold]Available papers:[/bold] {total_papers}")
    console.print(f"[bold]Using top-k:[/bold] {min(top_k, total_papers)}")
    if elo_path:
        console.print(f"[bold]Source:[/bold] Elo-ranked papers from {elo_path.name}")
    else:
        console.print("[bold]Source:[/bold] Snowball results (by citation count)")
    console.print()
    
    async def run_report_generation():
        try:
            print_step(1, "Selecting top papers...")
            console.print()
            
            print_step(2, "Generating paper cards...")
            with create_spinner_progress() as progress:
                task = progress.add_task("Processing papers...", total=None)
                report_obj = await generate_report(
                    snowball_file=file_path,
                    elo_file=elo_path,
                    top_k=top_k,
                )
            
            print_success(f"Generated report with {len(report_obj.current_research)} sections")
            console.print()
            
            # Convert to dict for saving
            report_data = report_to_dict(report_obj)
            
            # Save the report
            if output:
                output_path = Path(output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(report_data, f, indent=2, ensure_ascii=False)
                print_success(f"Report saved to: {output_path}")
            else:
                # Use ResultsManager to save in organized location
                output_path = results_manager.save_report(
                    query=query,
                    report_data=report_data,
                    top_k=top_k,
                )
                print_success(f"Report saved to: {output_path}")
            
            # Display summary
            console.print()
            print_header("Report Summary", "bold green")
            console.print(f"[bold]Papers used:[/bold] {report_obj.total_papers_used}")
            console.print(f"[bold]Sections:[/bold] {len(report_obj.current_research)}")
            console.print(f"[bold]Open problems:[/bold] {len(report_obj.open_problems)}")
            console.print()
            
            # Show section titles
            console.print("[bold]Sections:[/bold]")
            for i, section in enumerate(report_obj.current_research, 1):
                citations = len(section.paper_ids)
                console.print(f"  {i}. {section.title} ({citations} citations)")
            
            console.print()
            
        except Exception as e:
            logger.exception("Report generation failed")
            print_error(f"Report generation failed: {e}")
            raise typer.Exit(code=1)
    
    try:
        asyncio.run(run_report_generation())
    except KeyboardInterrupt:
        console.print()
        print_error("Report generation interrupted by user")
        raise typer.Exit(code=1)


@app.command()
def interactive() -> None:
    """Launch interactive menu-driven interface.
    
    This command is also the default when running paperpilot without arguments.
    """
    from paperpilot.cli.interactive import run_interactive
    run_interactive()


@app.command()
def version() -> None:
    """Show PaperPilot version."""
    console.print("[bold]PaperPilot[/bold] v0.1.0")
    console.print("[dim]AI-powered academic literature discovery[/dim]")


if __name__ == "__main__":
    app()
