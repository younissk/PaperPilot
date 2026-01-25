"""LLM-based match judging with relevance-first prompts."""

import json
import os
import asyncio
from typing import List, Tuple, Optional

from openai import AsyncOpenAI

from paperpilot.core.models import SnowballCandidate, QueryProfile
from paperpilot.core.elo_ranker.models import MatchResult

# Async OpenAI client
async_client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)


async def judge_match(
    candidate1: SnowballCandidate,
    candidate2: SnowballCandidate,
    profile: QueryProfile
) -> Tuple[Optional[int], str]:
    """Judge a single match between two candidates.
    
    Uses a relevance-first prompt that prioritizes citation usefulness
    over general quality/significance.
    
    Args:
        candidate1: First candidate paper
        candidate2: Second candidate paper
        profile: Query profile for relevance judgment
        
    Returns:
        Tuple of (winner, reason) where winner is 1, 2, or None for draw
    """
    # Build relevance-first prompt
    required_concepts_str = ", ".join(profile.required_concepts) if profile.required_concepts else "None specified"
    optional_concepts_str = ", ".join(profile.optional_concepts) if profile.optional_concepts else "None specified"
    
    abstract1 = candidate1.abstract or "(No abstract available)"
    abstract2 = candidate2.abstract or "(No abstract available)"
    
    prompt = f"""You are judging which paper is MORE USEFUL TO CITE for a survey on:
"{profile.core_query}"

Domain: {profile.domain_description}

Required concepts: {required_concepts_str}
Optional concepts: {optional_concepts_str}

DECISION CRITERIA (in order of priority):
1. PRIMARY - Relevance to core query: Which paper directly addresses the research question?
2. SECONDARY (tiebreaker only): If equally relevant, prefer clearer methodology/evaluation.

IMPORTANT: Do NOT prefer papers just because they are:
- Highly cited (citation count is not a relevance signal)
- Foundational/classic (unless directly on-topic)
- Broader in scope (focused papers may be more citable)

Paper A:
Title: {candidate1.title}
Abstract: {abstract1[:500]}

Paper B:
Title: {candidate2.title}
Abstract: {abstract2[:500]}

Output ONLY valid JSON with keys:
- winner: integer (1 for Paper A, 2 for Paper B, 0 for draw)
- reason: short string (max 20 words) explaining the choice
"""

    try:
        response = await async_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=150,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content.strip()
        data = json.loads(content)
        
        winner = data.get("winner")
        reason = data.get("reason", "")
        
        if winner == 1:
            return 1, reason
        elif winner == 2:
            return 2, reason
        elif winner == 0:
            return None, reason  # Draw
        else:
            # Invalid response, treat as draw
            return None, "Invalid response"
            
    except (json.JSONDecodeError, KeyError, AttributeError):
        # On error, treat as draw to avoid skewing ratings
        return None, "Parse error"
    except Exception:
        # On any other error, treat as draw
        return None, "API error"


async def judge_match_batch(
    pairs: List[Tuple[SnowballCandidate, SnowballCandidate]],
    profile: QueryProfile,
    concurrency: int = 5
) -> List[MatchResult]:
    """Judge multiple matches concurrently.
    
    Args:
        pairs: List of (candidate1, candidate2) tuples
        profile: Query profile for relevance judgment
        concurrency: Maximum number of concurrent API calls
        
    Returns:
        List of MatchResult objects
    """
    semaphore = asyncio.Semaphore(concurrency)
    
    async def judge_one(pair: Tuple[SnowballCandidate, SnowballCandidate]) -> MatchResult:
        async with semaphore:
            candidate1, candidate2 = pair
            winner, reason = await judge_match(candidate1, candidate2, profile)
            return MatchResult(
                paper1_title=candidate1.title,
                paper2_title=candidate2.title,
                winner=winner,
                reason=reason
            )
    
    results = await asyncio.gather(*[judge_one(pair) for pair in pairs])
    return list(results)
