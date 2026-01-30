"""Cheap ranking for snowball candidates before LLM judgment.

This module provides priority scoring to filter and rank candidates
before expensive LLM calls, reducing cost and noise.
"""

import math
import re

from papernavigator.models import QueryProfile, SnowballCandidate


def passes_keyword_gate(
    candidate: SnowballCandidate,
    profile: QueryProfile,
    relaxed: bool = False
) -> bool:
    """Check if a candidate passes the keyword gate filter.
    
    In strict mode (default): AND across groups - must match at least one term from EACH group.
    In relaxed mode: OR across groups - must match at least one term from ANY group.
    
    Relaxed mode is useful for foundational papers discovered through citation traversal,
    which may only match one concept domain (e.g., BERT matches "language model" but not "recommender").
    
    Args:
        candidate: The paper candidate to check
        profile: The query profile with concept groups and keyword patterns
        relaxed: If True, use OR across groups (for foundational papers).
                 If False, use AND across groups (strict mode).
        
    Returns:
        True if the candidate passes the gate, False otherwise
    """
    # Combine title and abstract for matching
    text = candidate.title or ""
    if candidate.abstract:
        text += " " + candidate.abstract

    if not text.strip():
        return False  # No text to match against

    text_lower = text.lower()

    # Use required_concept_groups if available (preferred)
    if profile.required_concept_groups:
        if relaxed:
            # RELAXED: OR across groups - at least ONE group must match
            # This allows foundational papers (e.g., BERT, BPR) to pass
            for group in profile.required_concept_groups:
                group_matched = any(term.lower() in text_lower for term in group)
                if group_matched:
                    return True
            return False  # No group matched at all
        else:
            # STRICT: AND across groups - must match at least one term from EACH group
            for group in profile.required_concept_groups:
                group_matched = any(term.lower() in text_lower for term in group)
                if not group_matched:
                    return False
            return True

    # Fallback: use keyword_patterns if groups not available
    if not profile.keyword_patterns:
        return True  # No patterns = everything passes

    # All patterns must match (AND logic) for the paper to pass
    for pattern_str in profile.keyword_patterns:
        try:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            if not pattern.search(text):
                return False
        except re.error:
            # Skip invalid patterns
            continue

    return True


def compute_title_overlap(title: str, profile: QueryProfile) -> float:
    """Score based on title overlap with query concepts.
    
    Args:
        title: Paper title
        profile: Query profile with required/optional concepts
        
    Returns:
        Score from 0-30 based on keyword overlap
    """
    if not title:
        return 0.0

    title_lower = title.lower()
    score = 0.0

    # Required concepts: +5 points each (max ~20 from these)
    for concept in profile.required_concepts:
        if concept.lower() in title_lower:
            score += 5.0

    # Optional concepts: +3 points each
    for concept in profile.optional_concepts:
        if concept.lower() in title_lower:
            score += 3.0

    # Penalize exclusion concepts: -10 points each
    for concept in profile.exclusion_concepts:
        if concept.lower() in title_lower:
            score -= 10.0

    # Clamp to 0-30 range
    return max(0.0, min(30.0, score))


def compute_priority_score(
    candidate: SnowballCandidate,
    profile: QueryProfile,
    current_year: int = 2026,
    relaxed: bool = False
) -> float:
    """Compute a priority score for ranking candidates before LLM judging.
    
    Scoring components:
    1. Keyword gate: must pass or return -1 (filtered out)
    2. Recency boost: 0-20 points (newer papers score higher)
    3. Citation count boost: 0-30 points (log scale for influence)
    4. Influential citation boost: 0-20 points
    5. Title overlap: 0-30 points (keyword matches)
    
    Total possible: ~100 points
    
    Args:
        candidate: The snowball candidate to score
        profile: Query profile for relevance signals
        current_year: Current year for recency calculation
        relaxed: If True, use relaxed keyword gate (OR across concept groups)
        
    Returns:
        Priority score (higher = more promising), or -1.0 if filtered out
    """
    # 1. Keyword gate (must pass)
    if not passes_keyword_gate(candidate, profile, relaxed=relaxed):
        return -1.0  # Filtered out

    score = 0.0

    # 2. Recency boost (0-20 points)
    # Papers from current year get 20 points, decreases by 2 per year
    if candidate.year:
        age = current_year - candidate.year
        recency_score = max(0, 20 - age * 2)
        score += recency_score

    # 3. Citation count boost (0-30 points, log scale)
    # Using log1p to handle 0 citations gracefully
    citation_score = min(30, math.log1p(candidate.citation_count) * 5)
    score += citation_score

    # 4. Influential citation boost (0-20 points)
    # Influential citations are weighted more heavily
    influential_score = min(20, candidate.influential_citation_count * 2)
    score += influential_score

    # 5. Title overlap with query keywords (0-30 points)
    title_score = compute_title_overlap(candidate.title, profile)
    score += title_score

    return score


def rank_candidates(
    candidates: list[SnowballCandidate],
    profile: QueryProfile,
    top_n: int = 50,
    current_year: int = 2026,
    relaxed: bool = False
) -> tuple[list[SnowballCandidate], int, int]:
    """Rank and filter candidates, returning top N for LLM judgment.
    
    Args:
        candidates: List of candidates to rank
        profile: Query profile for scoring
        top_n: Maximum number of candidates to return
        current_year: Current year for recency calculation
        relaxed: If True, use relaxed keyword gate (OR across concept groups).
                 Use for candidates discovered via citation traversal.
        
    Returns:
        Tuple of (ranked_candidates, passed_gate_count, total_count)
    """
    scored_candidates = []
    passed_gate_count = 0

    for candidate in candidates:
        score = compute_priority_score(candidate, profile, current_year, relaxed=relaxed)

        if score >= 0:  # Passed keyword gate
            passed_gate_count += 1
            candidate.priority_score = score
            scored_candidates.append(candidate)

    # Sort by priority score descending
    scored_candidates.sort(key=lambda c: c.priority_score, reverse=True)

    # Return top N
    return scored_candidates[:top_n], passed_gate_count, len(candidates)


