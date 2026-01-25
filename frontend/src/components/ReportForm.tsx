/**
 * Report form component for starting report generation jobs.
 */

import { useState, FormEvent } from 'react';
import { startReport, getReportStatus, type ReportRequest } from '../services/api';
import { useJobPolling } from '../hooks/useJobPolling';

interface ReportFormProps {
  query: string;
  onReportStart?: (jobId: string) => void;
  onReportComplete?: (jobId: string, reportPath: string | null) => void;
  onCancel?: () => void;
}

export function ReportForm({ query, onReportStart, onReportComplete, onCancel }: ReportFormProps) {
  const [topK, setTopK] = useState(30);
  const [filePath, setFilePath] = useState<string>('');
  const [eloFilePath, setEloFilePath] = useState<string>('');
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { status, data, error: pollingError } = useJobPolling({
    pollFn: getReportStatus,
    jobId,
    enabled: jobId !== null,
    onComplete: (result) => {
      if (onReportComplete) {
        onReportComplete(result.job_id, result.report_path || null);
      }
    },
  });

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setJobId(null);

    try {
      const request: ReportRequest = {
        query: query.trim(),
        top_k: topK,
        file_path: filePath.trim() || null,
        elo_file_path: eloFilePath.trim() || null,
      };

      const response = await startReport(request);
      setJobId(response.job_id);
      if (onReportStart) {
        onReportStart(response.job_id);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start report generation';
      setError(errorMessage);
    }
  };

  const handleReset = () => {
    setTopK(30);
    setFilePath('');
    setEloFilePath('');
    setJobId(null);
    setError(null);
  };

  const displayError = error || (pollingError ? pollingError.message : null);
  const currentStatus = status || (data?.status ?? null);

  return (
    <div className="report-form">
      <div className="report-form-header">
        <h2>Generate Research Report</h2>
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
          <label htmlFor="top_k">Top K Papers</label>
          <input
            id="top_k"
            type="number"
            min="1"
            max="100"
            value={topK}
            onChange={(e) => setTopK(parseInt(e.target.value) || 30)}
            disabled={currentStatus === 'running' || currentStatus === 'queued'}
          />
          <small>Number of top papers to include in report (default: 30)</small>
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

        <div className="form-group">
          <label htmlFor="elo_file_path">ELO Ranking File (optional)</label>
          <input
            id="elo_file_path"
            type="text"
            value={eloFilePath}
            onChange={(e) => setEloFilePath(e.target.value)}
            placeholder="Leave empty to auto-detect"
            disabled={currentStatus === 'running' || currentStatus === 'queued'}
          />
          <small>Path to ELO ranking file (auto-detected if not provided)</small>
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
                Report generation completed!
              </div>
            )}
            {currentStatus === 'failed' && (
              <div className="status-info error">
                Report generation failed. Please try again.
              </div>
            )}
          </div>
        )}

        <div className="form-actions">
          <button
            type="submit"
            disabled={currentStatus === 'running' || currentStatus === 'queued'}
          >
            {currentStatus === 'running' || currentStatus === 'queued' ? 'Generating Report...' : 'Start Report Generation'}
          </button>
          {(currentStatus === 'completed' || currentStatus === 'failed') && (
            <button type="button" onClick={handleReset}>
              New Report
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
