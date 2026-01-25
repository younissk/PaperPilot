/**
 * Timeline form component for starting timeline creation jobs.
 */

import { useState, FormEvent } from 'react';
import { startTimeline, getTimelineStatus, type TimelineRequest } from '../services/api';
import { useJobPolling } from '../hooks/useJobPolling';

interface TimelineFormProps {
  query: string;
  onTimelineStart?: (jobId: string) => void;
  onTimelineComplete?: (jobId: string, htmlPath: string | null) => void;
  onCancel?: () => void;
}

export function TimelineForm({ query, onTimelineStart, onTimelineComplete, onCancel }: TimelineFormProps) {
  const [filePath, setFilePath] = useState<string>('');
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { status, data, error: pollingError } = useJobPolling({
    pollFn: getTimelineStatus,
    jobId,
    enabled: jobId !== null,
    onComplete: (result) => {
      if (onTimelineComplete) {
        onTimelineComplete(result.job_id, result.html_content || null);
      }
    },
  });

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setJobId(null);

    try {
      const request: TimelineRequest = {
        query: query.trim(),
        file_path: filePath.trim() || null,
      };

      const response = await startTimeline(request);
      setJobId(response.job_id);
      if (onTimelineStart) {
        onTimelineStart(response.job_id);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start timeline creation';
      setError(errorMessage);
    }
  };

  const handleReset = () => {
    setFilePath('');
    setJobId(null);
    setError(null);
  };

  const displayError = error || (pollingError ? pollingError.message : null);
  const currentStatus = status || (data?.status ?? null);

  return (
    <div className="timeline-form">
      <div className="timeline-form-header">
        <h2>Create Timeline</h2>
        {onCancel && (
          <button type="button" onClick={onCancel} className="cancel-btn">
            Cancel
          </button>
        )}
      </div>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="query">Research Query</label>
          <input
            id="query"
            type="text"
            value={query}
            disabled
            className="disabled-input"
          />
        </div>

        <div className="form-group">
          <label htmlFor="file_path">Custom Results File (optional)</label>
          <input
            id="file_path"
            type="text"
            value={filePath}
            onChange={(e) => setFilePath(e.target.value)}
            placeholder="Leave empty to use latest results for query"
            disabled={currentStatus === 'running' || currentStatus === 'queued'}
          />
        </div>

        {displayError && (
          <div className="error-message">
            {displayError}
          </div>
        )}

        {currentStatus && (
          <div className="job-status">
            <div className={`status-badge status-${currentStatus}`}>
              {currentStatus.toUpperCase()}
            </div>
            {currentStatus === 'completed' && (
              <div className="status-info success">
                Timeline creation completed!
              </div>
            )}
            {currentStatus === 'failed' && (
              <div className="status-info error">
                Timeline creation failed. Please try again.
              </div>
            )}
          </div>
        )}

        <div className="form-actions">
          <button
            type="submit"
            disabled={currentStatus === 'running' || currentStatus === 'queued'}
          >
            {currentStatus === 'running' || currentStatus === 'queued' ? 'Creating Timeline...' : 'Create Timeline'}
          </button>
          {(currentStatus === 'completed' || currentStatus === 'failed') && (
            <button type="button" onClick={handleReset}>
              New Timeline
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
