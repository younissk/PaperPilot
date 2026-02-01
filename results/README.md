# Results Directory

This directory contains example pipeline outputs for demonstration and testing purposes.

## Policy: Historical Examples Only

The results in this directory are **committed historical examples** that showcase the pipeline's output format. 

**New generated outputs should NOT be committed to git.**

In production, pipeline results are stored in Azure Blob Storage, not in this repository.

## Committed Examples

The following queries have example results:

| Query | Files |
|-------|-------|
| `ai_in_heath_care` | snowball, elo, report |
| `ai_in_law` | snowball, elo, report |
| `borderline_personality_disorder` | snowball (partial) |
| `how_chatgpt_effects_students` | snowball, elo, report, clusters |
| `llm_based_recommender_systems` | snowball, elo, report, clusters, graph, timeline |
| `llm_in_healthcare` | report (partial) |
| `multi_modal_llms` | snowball (partial) |

## File Types

- `metadata.json` - Query metadata and file paths
- `snowball.json` - Raw search results from snowball sampling
- `elo_ranked_*.json` - Papers ranked by ELO algorithm
- `report_top_k*.json` - Generated research report
- `clusters_*.json/html` - Paper clustering visualizations
- `graph_*.json/html` - Citation graph visualizations
- `timeline.json/html` - Publication timeline

## For Development

If you need to generate new results locally:

1. Results will be saved to this directory by default
2. Do NOT commit them (they are gitignored)
3. For production, results go to Azure Blob Storage via the serverless pipeline

To use these examples in tests, consider copying specific files to `tests/fixtures/`.
