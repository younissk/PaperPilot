/**
 * Component for visualizing paper timeline.
 */

import { useState } from 'react';

interface TimelineYear {
  year: number;
  count: number;
  papers: Array<{
    title: string;
    year?: number;
    citation_count: number;
    paper_id?: string;
  }>;
}

interface TimelineData {
  query: string;
  total_papers: number;
  years: Record<string, Array<unknown>>;
  timeline: TimelineYear[];
  year_range: {
    min?: number;
    max?: number;
  };
}

interface TimelineVisualizationProps {
  data: TimelineData | null;
}

export function TimelineVisualization({ data }: TimelineVisualizationProps) {
  const [expandedYear, setExpandedYear] = useState<number | null>(null);

  if (!data || !data.timeline || data.timeline.length === 0) {
    return (
      <div className="visualization-empty">
        <p>No timeline data available.</p>
      </div>
    );
  }

  const minYear = data.year_range?.min || data.timeline[0]?.year || 2000;
  const maxYear = data.year_range?.max || data.timeline[data.timeline.length - 1]?.year || new Date().getFullYear();
  const yearRange = maxYear - minYear || 1;

  return (
    <div className="timeline-visualization">
      <div className="timeline-header">
        <h3>Timeline: {data.query}</h3>
        <div className="timeline-stats">
          <span>{data.total_papers} papers</span>
          <span> | </span>
          <span>{minYear} - {maxYear}</span>
        </div>
      </div>

      <div className="timeline-container">
        <div className="timeline-track">
          {data.timeline.map((yearData) => {
            const isExpanded = expandedYear === yearData.year;
            const position = ((yearData.year - minYear) / yearRange) * 100;
            const maxCount = Math.max(...data.timeline.map(y => y.count), 1);
            const heightPercent = (yearData.count / maxCount) * 100;

            return (
              <div
                key={yearData.year}
                className={`timeline-year ${isExpanded ? 'expanded' : ''}`}
                style={{ left: `${position}%` }}
                onClick={() => setExpandedYear(isExpanded ? null : yearData.year)}
              >
                <div className="year-marker">
                  <div className="year-bar" style={{ height: `${Math.max(heightPercent, 10)}%` }} />
                  <div className="year-label">{yearData.year}</div>
                  <div className="year-count">{yearData.count}</div>
                </div>

                {isExpanded && (
                  <div className="year-papers">
                    <h4>Papers from {yearData.year} ({yearData.count})</h4>
                    <div className="papers-list">
                      {yearData.papers.map((paper, idx) => (
                        <div key={idx} className="timeline-paper">
                          <div className="paper-title">{paper.title}</div>
                          <div className="paper-meta">
                            {paper.citation_count > 0 && (
                              <span className="meta-badge">{paper.citation_count} citations</span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <div className="timeline-legend">
        <p>Click on a year to see papers from that year</p>
      </div>
    </div>
  );
}
