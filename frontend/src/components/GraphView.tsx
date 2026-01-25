/**
 * Component for displaying citation graph visualization.
 */

import { GraphVisualization } from './GraphVisualization';

interface GraphViewProps {
  query: string;
  graphData: Record<string, unknown> | null;
  isLoading?: boolean;
}

export function GraphView({ query, graphData, isLoading }: GraphViewProps) {
  if (isLoading || !graphData) {
    return (
      <div className="visualization-view">
        <div className="visualization-loading">
          <div className="loading-spinner"></div>
          <p>Building citation graph...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="visualization-view">
      <GraphVisualization data={graphData as any} />
    </div>
  );
}
