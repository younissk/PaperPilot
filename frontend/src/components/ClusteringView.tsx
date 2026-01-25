/**
 * Component for displaying clustering visualization.
 */

import { ClusteringVisualization } from './ClusteringVisualization';

interface ClusteringViewProps {
  query: string;
  clustersData: Record<string, unknown> | null;
  isLoading?: boolean;
}

export function ClusteringView({ query, clustersData, isLoading }: ClusteringViewProps) {
  if (isLoading || !clustersData) {
    return (
      <div className="visualization-view">
        <div className="visualization-loading">
          <div className="loading-spinner"></div>
          <p>Clustering papers...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="visualization-view">
      <ClusteringVisualization data={clustersData as any} />
    </div>
  );
}
