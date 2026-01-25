/**
 * Component for displaying ranked papers with ELO ratings.
 */

import { useState, useEffect } from 'react';
import { type Paper } from '../services/api';

interface RankingListProps {
  papers: Paper[];
  title?: string;
  isLive?: boolean;
}

export function RankingList({ papers, title = 'Ranked Papers', isLive = false }: RankingListProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [sortBy, setSortBy] = useState<'rank' | 'elo' | 'elo_change' | 'wins' | 'citations'>('rank');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [previousRanks, setPreviousRanks] = useState<Map<string, number>>(new Map());

  // Track rank changes for animation
  useEffect(() => {
    const currentRanks = new Map(papers.map(p => [p.paper_id, p.rank || 0]));
    setPreviousRanks(currentRanks);
  }, [papers]);

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
      case 'rank':
        aVal = a.rank ?? 999;
        bVal = b.rank ?? 999;
        break;
      case 'elo':
        aVal = a.elo ?? 0;
        bVal = b.elo ?? 0;
        break;
      case 'elo_change':
        aVal = a.elo_change ?? 0;
        bVal = b.elo_change ?? 0;
        break;
      case 'wins':
        aVal = a.wins ?? 0;
        bVal = b.wins ?? 0;
        break;
      case 'citations':
        aVal = a.citation_count;
        bVal = b.citation_count;
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

  const getRankBadgeClass = (rank?: number): string => {
    if (!rank) return 'rank-badge';
    if (rank === 1) return 'rank-badge rank-gold';
    if (rank === 2) return 'rank-badge rank-silver';
    if (rank === 3) return 'rank-badge rank-bronze';
    return 'rank-badge';
  };

  const getEloColor = (elo?: number): string => {
    if (!elo) return '';
    if (elo >= 1600) return 'elo-high';
    if (elo >= 1500) return 'elo-medium';
    return 'elo-low';
  };

  const getRankChange = (paperId: string, currentRank?: number): number | null => {
    if (!currentRank) return null;
    const prevRank = previousRanks.get(paperId);
    if (prevRank === undefined || prevRank === currentRank) return null;
    return prevRank - currentRank; // Positive = moved up, negative = moved down
  };

  if (papers.length === 0) {
    return (
      <div className="ranking-list">
        <h2>{title}</h2>
        <div className="empty-state">
          <p>No ranked papers to display.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="ranking-list">
      <div className="ranking-list-header">
        <div className="header-title">
          <h2>{title} ({papers.length})</h2>
          {isLive && (
            <span className="live-indicator">
              <span className="live-dot"></span>
              Live Ranking
            </span>
          )}
        </div>
        <div className="sort-controls">
          <label>
            Sort by:
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
            >
              <option value="rank">Rank</option>
              <option value="elo">ELO Rating</option>
              <option value="elo_change">ELO Change</option>
              <option value="wins">Wins</option>
              <option value="citations">Citations</option>
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
          const rankChange = getRankChange(paper.paper_id, paper.rank);

          return (
            <div
              key={paper.paper_id}
              className={`paper-card ranking-card ${isLive ? 'live-update' : ''}`}
            >
              <div className="paper-header">
                <div className="rank-section">
                  <div className={getRankBadgeClass(paper.rank)}>
                    #{paper.rank ?? '?'}
                  </div>
                  {rankChange !== null && rankChange !== 0 && (
                    <span className={`rank-change ${rankChange > 0 ? 'rank-up' : 'rank-down'}`}>
                      {rankChange > 0 ? '↑' : '↓'} {Math.abs(rankChange)}
                    </span>
                  )}
                </div>
                <h3 className="paper-title">{paper.title}</h3>
              </div>

              <div className="elo-section">
                <div className={`elo-rating ${getEloColor(paper.elo)}`}>
                  <span className="elo-label">ELO:</span>
                  <span className="elo-value">{paper.elo?.toFixed(1) ?? 'N/A'}</span>
                  {paper.elo_change !== undefined && (
                    <span className={`elo-change ${paper.elo_change >= 0 ? 'positive' : 'negative'}`}>
                      {paper.elo_change >= 0 ? '+' : ''}{paper.elo_change.toFixed(1)}
                    </span>
                  )}
                </div>
                <div className="match-record">
                  <span className="match-stat wins">W: {paper.wins ?? 0}</span>
                  <span className="match-stat losses">L: {paper.losses ?? 0}</span>
                  <span className="match-stat draws">D: {paper.draws ?? 0}</span>
                </div>
              </div>

              <div className="paper-meta">
                {paper.year && <span className="meta-badge year">{paper.year}</span>}
                <span className="meta-badge citations">
                  {paper.citation_count} citations
                </span>
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
            </div>
          );
        })}
      </div>
    </div>
  );
}
