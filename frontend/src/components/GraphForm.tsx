/**
 * Graph form component for starting citation graph building jobs.
 */

import { useState, FormEvent } from 'react';
import { startGraph, getGraphStatus, type GraphRequest } from '../services/api';
import { useJobPolling } from '../hooks/useJobPolling';

interface GraphFormProps {
  query: string;
  onGraphStart?: (jobId: string) => void;
  onGraphComplete?: (jobId: string, htmlPath: string | null) => void;
  onCancel?: () => void;
}

export function GraphForm({ query, onGraphStart, onGraphComplete, onCancel }: GraphFormProps) {
  const [direction, setDirection] = useState<'both' | 'citations' | 'references'>('both');
  const [limit, setLimit] = useState(100);
  const [filePath, setFilePath] = useState<string>('');
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { status, data, error: pollingError } = useJobPolling({
    pollFn: getGraphStatus,
    jobId,
    enabled: jobId !== null,
    onComplete: (result) => {
      if (onGraphComplete) {
        onGraphComplete(result.job_id, result.html_content || null);
      }
    },
  });

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setJobId(null);

    try {
      const request: GraphRequest = {
        query: query.trim(),
        direction: direction,
        limit: limit,
        file_path: filePath.trim() || null,
      };

      const response = await startGraph(request);
      setJobId(response.job_id);
      if (onGraphStart) {
        onGraphStart(response.job_id);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start graph building';
      setError(errorMessage);
    }
  };

  const handleReset = () => {
    setDirection('both');
    setLimit(100);
    setFilePath('');
    setJobId(null);
    setError(null);
  };

  const displayError = error || (pollingError ? pollingError.message : null);
  const currentStatus = status || (data?.status ?? null);

  return (
    <div className="graph-form">
      <div className="graph-form-header">
        <h2>Build Citation Graph</h2>
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

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="direction">Direction</label>
            <select
              id="direction"
              value={direction}
              onChange={(e) => setDirection(e.target.value as typeof direction)}
              disabled={currentStatus === 'running' || currentStatus === 'queued'}
            >
              <option value="both">Both (Citations & References)</option>
              <option value="citations">Citations Only</option>
              <option value="references">References Only</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="limit">Limit per Paper</label>
            <input
              id="limit"
              type="number"
              min="1"
              max="500"
              value={limit}
              onChange={(e) => setLimit(parseInt(e.target.value) || 100)}
              disabled={currentStatus === 'running' || currentStatus === 'queued'}
            />
            <small>Max refs/cites to fetch per paper (default: 100)</small>
          </div>
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
                Graph building completed!
              </div>
            )}
            {currentStatus === 'failed' && (
              <div className="status-info error">
                Graph building failed. Please try again.
              </div>
            )}
          </div>
        )}

        <div className="form-actions">
          <button
            type="submit"
            disabled={currentStatus === 'running' || currentStatus === 'queued'}
          >
            {currentStatus === 'running' || currentStatus === 'queued' ? 'Building Graph...' : 'Start Building Graph'}
          </button>
          {(currentStatus === 'completed' || currentStatus === 'failed') && (
            <button type="button" onClick={handleReset}>
              New Graph
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
