/**
 * Component for displaying a list of papers.
 */

import { useState } from 'react';
import { type Paper } from '../services/api';

interface PaperListProps {
  papers: Paper[];
  title?: string;
}

export function PaperList({ papers, title = 'Papers' }: PaperListProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [sortBy, setSortBy] = useState<'year' | 'citations' | 'confidence' | 'depth'>('citations');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const toggleExpand = (paperId: string) => {
    const newExpanded = new Set(expandedIds);
    if (newExpanded.has(paperId)) {
      newExpanded.delete(paperId);
    } else {
      newExpanded.add(paperId);
    }
    setExpandedIds(newExpanded);
  };

  const sortedPapers = [...papers].sort((a, b) => {
    let aVal: number;
    let bVal: number;

    switch (sortBy) {
      case 'year':
        aVal = a.year ?? 0;
        bVal = b.year ?? 0;
        break;
      case 'citations':
        aVal = a.citation_count;
        bVal = b.citation_count;
        break;
      case 'confidence':
        aVal = a.judge_confidence;
        bVal = b.judge_confidence;
        break;
      case 'depth':
        aVal = a.depth;
        bVal = b.depth;
        break;
      default:
        return 0;
    }

    if (sortOrder === 'asc') {
      return aVal - bVal;
    } else {
      return bVal - aVal;
    }
  });

  if (papers.length === 0) {
    return (
      <div className="paper-list">
        <h2>{title}</h2>
        <div className="empty-state">
          <p>No papers to display.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="paper-list">
      <div className="paper-list-header">
        <h2>{title} ({papers.length})</h2>
        <div className="sort-controls">
          <label>
            Sort by:
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
            >
              <option value="citations">Citations</option>
              <option value="year">Year</option>
              <option value="confidence">Confidence</option>
              <option value="depth">Depth</option>
            </select>
          </label>
          <button
            onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            className="sort-order-btn"
            title={`Sort ${sortOrder === 'asc' ? 'descending' : 'ascending'}`}
          >
            {sortOrder === 'asc' ? '↑' : '↓'}
          </button>
        </div>
      </div>

      <div className="papers-container">
        {sortedPapers.map((paper) => {
          const isExpanded = expandedIds.has(paper.paper_id);
          const abstract = paper.abstract || 'No abstract available';
          const shouldTruncate = abstract.length > 300;

          return (
            <div key={paper.paper_id} className="paper-card">
              <div className="paper-header">
                <h3 className="paper-title">{paper.title}</h3>
                <div className="paper-meta">
                  {paper.year && <span className="meta-badge year">{paper.year}</span>}
                  <span className="meta-badge citations">
                    {paper.citation_count} citations
                  </span>
                  <span className="meta-badge depth">Depth: {paper.depth}</span>
                  <span className="meta-badge confidence">
                    {(paper.judge_confidence * 100).toFixed(1)}% confidence
                  </span>
                </div>
              </div>

              {shouldTruncate ? (
                <div className="paper-abstract">
                  {isExpanded ? abstract : `${abstract.substring(0, 300)}...`}
                  <button
                    className="expand-btn"
                    onClick={() => toggleExpand(paper.paper_id)}
                  >
                    {isExpanded ? 'Show less' : 'Show more'}
                  </button>
                </div>
              ) : (
                <div className="paper-abstract">{abstract}</div>
              )}

              <div className="paper-footer">
                <div className="paper-discovery">
                  <span className="discovery-label">Edge type:</span>
                  <span className="discovery-value">{paper.edge_type}</span>
                  {paper.discovered_from && (
                    <>
                      <span className="discovery-label">From:</span>
                      <span className="discovery-value">{paper.discovered_from}</span>
                    </>
                  )}
                </div>
                <div className="paper-reason">
                  <strong>Reason:</strong> {paper.judge_reason}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
