/**
 * Component for displaying timeline visualization.
 */

import { TimelineVisualization } from './TimelineVisualization';

interface TimelineViewProps {
  query: string;
  timelineData: Record<string, unknown> | null;
  isLoading?: boolean;
}

export function TimelineView({ query, timelineData, isLoading }: TimelineViewProps) {
  if (isLoading || !timelineData) {
    return (
      <div className="visualization-view">
        <div className="visualization-loading">
          <div className="loading-spinner"></div>
          <p>Creating timeline...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="visualization-view">
      <TimelineVisualization data={timelineData as any} />
    </div>
  );
}
