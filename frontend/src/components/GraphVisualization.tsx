/**
 * Component for visualizing citation graph as a network.
 */

import { useState, useRef, useEffect } from 'react';

interface GraphNode {
  id: string;
  title: string;
  year?: number;
  citation_count: number;
  abstract?: string;
}

interface GraphEdge {
  source: string;
  target: string;
  type: string;
  direction?: string;
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  query: string;
  total_papers?: number;
  total_edges?: number;
}

interface GraphVisualizationProps {
  data: GraphData | null;
}

export function GraphVisualization({ data }: GraphVisualizationProps) {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const [dimensions, setDimensions] = useState({ width: 1200, height: 800 });

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

  if (!data || !data.nodes || data.nodes.length === 0) {
    return (
      <div className="visualization-empty">
        <p>No graph data available.</p>
      </div>
    );
  }

  // Simple circular layout for nodes
  const nodes = data.nodes.map((node, i) => {
    const angle = (i / data.nodes.length) * 2 * Math.PI;
    const radius = Math.min(dimensions.width, dimensions.height) * 0.35;
    return {
      ...node,
      x: dimensions.width / 2 + radius * Math.cos(angle),
      y: dimensions.height / 2 + radius * Math.sin(angle),
    };
  });

  const nodeMap = new Map(nodes.map(n => [n.id, n]));

  return (
    <div className="graph-visualization">
      <div className="graph-header">
        <h3>Citation Graph: {data.query}</h3>
        <div className="graph-stats">
          <span>{data.nodes.length} papers</span>
          <span>{data.edges?.length || 0} connections</span>
        </div>
      </div>
      <div className="graph-container">
        <svg
          ref={svgRef}
          width={dimensions.width}
          height={dimensions.height}
          className="graph-svg"
        >
          {/* Edges */}
          <g className="edges">
            {data.edges?.map((edge, i) => {
              const source = nodeMap.get(edge.source);
              const target = nodeMap.get(edge.target);
              if (!source || !target) return null;
              return (
                <line
                  key={i}
                  x1={source.x}
                  y1={source.y}
                  x2={target.x}
                  y2={target.y}
                  className={`edge edge-${edge.type}`}
                  strokeWidth={1.5}
                  opacity={0.3}
                />
              );
            })}
          </g>

          {/* Nodes */}
          <g className="nodes">
            {nodes.map((node) => {
              const isSelected = selectedNode?.id === node.id;
              const isHovered = hoveredNode === node.id;
              const radius = 8 + Math.min(node.citation_count / 10, 5);
              
              return (
                <g
                  key={node.id}
                  className={`node ${isSelected ? 'selected' : ''} ${isHovered ? 'hovered' : ''}`}
                  transform={`translate(${node.x}, ${node.y})`}
                  onClick={() => setSelectedNode(isSelected ? null : node)}
                  onMouseEnter={() => setHoveredNode(node.id)}
                  onMouseLeave={() => setHoveredNode(null)}
                >
                  <circle
                    r={radius}
                    className="node-circle"
                    fill={isSelected ? '#646cff' : isHovered ? '#535bf2' : '#4caf50'}
                  />
                  {isHovered && (
                    <text
                      y={-radius - 5}
                      textAnchor="middle"
                      className="node-label"
                      fontSize="12"
                      fill="#fff"
                    >
                      {node.title.substring(0, 30)}...
                    </text>
                  )}
                </g>
              );
            })}
          </g>
        </svg>
      </div>

      {selectedNode && (
        <div className="node-details">
          <button
            className="close-details-btn"
            onClick={() => setSelectedNode(null)}
          >
            ×
          </button>
          <h4>{selectedNode.title}</h4>
          <div className="node-meta">
            {selectedNode.year && <span>Year: {selectedNode.year}</span>}
            <span>Citations: {selectedNode.citation_count}</span>
          </div>
          {selectedNode.abstract && (
            <p className="node-abstract">{selectedNode.abstract}</p>
          )}
        </div>
      )}

      <div className="graph-legend">
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#4caf50' }}></span>
          <span>Paper (node size = citations)</span>
        </div>
        <div className="legend-item">
          <span className="legend-line"></span>
          <span>Citation connection</span>
        </div>
      </div>
    </div>
  );
}
