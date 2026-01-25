/**
 * Component for visualizing paper clusters as a scatter plot.
 */

import { useState, useRef, useEffect } from 'react';

interface ClusterData {
  id: number;
  label: string;
  count: number;
  top_papers: Array<{
    title: string;
    year?: number;
    citations?: number;
  }>;
  papers: Array<{
    paper_id: string;
    title: string;
    year?: number;
    citation_count: number;
    x: number;
    y: number;
  }>;
}

interface ClusteringData {
  query: string;
  method: string;
  dim_reduction: string;
  n_clusters?: number;
  total_papers: number;
  clusters: ClusterData[];
}

interface ClusteringVisualizationProps {
  data: ClusteringData | null;
}

const CLUSTER_COLORS = [
  '#646cff', '#4caf50', '#ffa500', '#f44336', '#2196f3',
  '#9c27b0', '#00bcd4', '#ffeb3b', '#795548', '#607d8b',
];

export function ClusteringVisualization({ data }: ClusteringVisualizationProps) {
  const [selectedCluster, setSelectedCluster] = useState<number | null>(null);
  const [hoveredPoint, setHoveredPoint] = useState<string | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const [dimensions, setDimensions] = useState({ width: 1000, height: 700 });
  const [bounds, setBounds] = useState({ minX: 0, maxX: 1, minY: 0, maxY: 1 });

  useEffect(() => {
    const updateDimensions = () => {
      if (svgRef.current?.parentElement) {
        setDimensions({
          width: svgRef.current.parentElement.clientWidth,
          height: Math.max(600, window.innerHeight - 300),
        });
      }
    };
    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  // Extract all papers with coordinates from clusters
  const allPapers = data?.clusters?.flatMap(cluster => cluster.papers) || [];

  useEffect(() => {
    if (allPapers.length > 0) {
      const xs = allPapers.map(p => p.x);
      const ys = allPapers.map(p => p.y);
      setBounds({
        minX: Math.min(...xs),
        maxX: Math.max(...xs),
        minY: Math.min(...ys),
        maxY: Math.max(...ys),
      });
    }
  }, [allPapers.length]);

  if (!data || !data.clusters || data.clusters.length === 0 || allPapers.length === 0) {
    return (
      <div className="visualization-empty">
        <p>No clustering data available.</p>
      </div>
    );
  }

  const scaleX = (x: number) => {
    const range = bounds.maxX - bounds.minX || 1;
    return ((x - bounds.minX) / range) * (dimensions.width - 80) + 40;
  };

  const scaleY = (y: number) => {
    const range = bounds.maxY - bounds.minY || 1;
    return dimensions.height - 40 - ((y - bounds.minY) / range) * (dimensions.height - 80);
  };

  const uniqueClusters = data.clusters
    .map(c => c.id)
    .filter(id => id >= 0)
    .sort((a, b) => a - b);

  return (
    <div className="clustering-visualization">
      <div className="clustering-header">
        <h3>Paper Clusters: {data.query || 'Unknown Query'}</h3>
        <div className="clustering-stats">
          <span>{data.total_papers || allPapers.length} papers</span>
          <span>{uniqueClusters.length} clusters</span>
          <span>Method: {data.method} ({data.dim_reduction})</span>
        </div>
      </div>

      <div className="clustering-container">
        <svg
          ref={svgRef}
          width={dimensions.width}
          height={dimensions.height}
          className="clustering-svg"
        >
          {/* Grid lines */}
          <g className="grid">
            {[0, 0.25, 0.5, 0.75, 1].map(t => {
              const x = scaleX(bounds.minX + t * (bounds.maxX - bounds.minX));
              const y = scaleY(bounds.minY + t * (bounds.maxY - bounds.minY));
              return (
                <g key={t}>
                  <line x1={x} y1={40} x2={x} y2={dimensions.height - 40} className="grid-line" />
                  <line x1={40} y1={y} x2={dimensions.width - 40} y2={y} className="grid-line" />
                </g>
              );
            })}
          </g>

          {/* Points */}
          <g className="points">
            {allPapers.map((paper) => {
              // Find which cluster this paper belongs to
              const cluster = data.clusters.find(c => 
                c.papers.some(p => p.paper_id === paper.paper_id)
              );
              const label = cluster?.id ?? -1;
              const isNoise = label === -1;
              const isSelected = selectedCluster === label;
              const isHovered = hoveredPoint === paper.paper_id;
              const color = isNoise ? '#666' : CLUSTER_COLORS[label % CLUSTER_COLORS.length];
              
              return (
                <g
                  key={paper.paper_id}
                  className={`point ${isSelected ? 'selected' : ''} ${isHovered ? 'hovered' : ''}`}
                  transform={`translate(${scaleX(paper.x)}, ${scaleY(paper.y)})`}
                  onClick={() => setSelectedCluster(isSelected ? null : label)}
                  onMouseEnter={() => setHoveredPoint(paper.paper_id)}
                  onMouseLeave={() => setHoveredPoint(null)}
                >
                  <circle
                    r={isHovered ? 6 : 4}
                    fill={color}
                    stroke={isHovered || isSelected ? '#fff' : 'none'}
                    strokeWidth={2}
                    opacity={isSelected || isHovered ? 1 : selectedCluster === null ? 0.7 : selectedCluster === label ? 1 : 0.2}
                  />
                  {isHovered && (
                    <text
                      y={-10}
                      textAnchor="middle"
                      className="point-label"
                      fontSize="11"
                      fill="#fff"
                    >
                      {paper.title.substring(0, 40)}...
                    </text>
                  )}
                </g>
              );
            })}
          </g>
        </svg>
      </div>

      {data.clusters && data.clusters.length > 0 && (
        <div className="cluster-summaries">
          <h4>Cluster Summaries</h4>
          <div className="summaries-list">
            {data.clusters
              .filter(c => c.id >= 0)
              .map((cluster) => {
                const isSelected = selectedCluster === cluster.id;
                return (
                  <div
                    key={cluster.id}
                    className={`cluster-summary ${isSelected ? 'selected' : ''}`}
                    onClick={() => setSelectedCluster(isSelected ? null : cluster.id)}
                  >
                    <div className="summary-header">
                      <span
                        className="cluster-color"
                        style={{ backgroundColor: CLUSTER_COLORS[cluster.id % CLUSTER_COLORS.length] }}
                      />
                      <strong>{cluster.label}</strong>
                      <span className="cluster-size">({cluster.count} papers)</span>
                    </div>
                    {cluster.top_papers && cluster.top_papers.length > 0 && (
                      <div className="top-papers">
                        <strong>Top papers:</strong>
                        <ul>
                          {cluster.top_papers.slice(0, 3).map((paper, idx) => (
                            <li key={idx}>{paper.title}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                );
              })}
          </div>
        </div>
      )}

      <div className="clustering-legend">
        <div className="legend-item">
          <span className="legend-note">Click on a cluster summary to highlight it, or click a point to filter by cluster</span>
        </div>
      </div>
    </div>
  );
}
