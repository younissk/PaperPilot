/**
 * Search form component for starting paper searches.
 */

import { useState, FormEvent } from 'react';
import { startSearch, getSearchStatus, type SearchRequest } from '../services/api';
import { useJobPolling } from '../hooks/useJobPolling';
import { DEFAULT_SEARCH_PARAMS } from '../config';

interface SearchFormProps {
  onSearchComplete?: (jobId: string, papers: unknown[]) => void;
}

export function SearchForm({ onSearchComplete }: SearchFormProps) {
  const [query, setQuery] = useState('');
  const [numResults, setNumResults] = useState(DEFAULT_SEARCH_PARAMS.num_results);
  const [maxIterations, setMaxIterations] = useState(DEFAULT_SEARCH_PARAMS.max_iterations);
  const [maxAccepted, setMaxAccepted] = useState(DEFAULT_SEARCH_PARAMS.max_accepted);
  const [topN, setTopN] = useState(DEFAULT_SEARCH_PARAMS.top_n);
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { status, data, error: pollingError } = useJobPolling({
    pollFn: getSearchStatus,
    jobId,
    enabled: jobId !== null,
    onComplete: (result) => {
      if (onSearchComplete && result.papers) {
        onSearchComplete(result.job_id, result.papers);
      }
    },
  });

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setJobId(null);

    if (!query.trim()) {
      setError('Please enter a search query');
      return;
    }

    try {
      const request: SearchRequest = {
        query: query.trim(),
        num_results: numResults,
        max_iterations: maxIterations,
        max_accepted: maxAccepted,
        top_n: topN,
      };

      const response = await startSearch(request);
      setJobId(response.job_id);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start search';
      setError(errorMessage);
    }
  };

  const handleReset = () => {
    setQuery('');
    setNumResults(DEFAULT_SEARCH_PARAMS.num_results);
    setMaxIterations(DEFAULT_SEARCH_PARAMS.max_iterations);
    setMaxAccepted(DEFAULT_SEARCH_PARAMS.max_accepted);
    setTopN(DEFAULT_SEARCH_PARAMS.top_n);
    setJobId(null);
    setError(null);
  };

  const displayError = error || (pollingError ? pollingError.message : null);
  const currentStatus = status || (data?.status ?? null);
  const totalAccepted = data?.total_accepted ?? 0;

  return (
    <div className="search-form">
      <h2>Start New Search</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="query">Research Query *</label>
          <input
            id="query"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., LLM Based Recommendation Systems"
            disabled={currentStatus === 'running' || currentStatus === 'queued'}
            required
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="num_results">Results per Query</label>
            <input
              id="num_results"
              type="number"
              min="1"
              max="100"
              value={numResults}
              onChange={(e) => setNumResults(parseInt(e.target.value) || DEFAULT_SEARCH_PARAMS.num_results)}
              disabled={currentStatus === 'running' || currentStatus === 'queued'}
            />
          </div>

          <div className="form-group">
            <label htmlFor="max_iterations">Max Iterations</label>
            <input
              id="max_iterations"
              type="number"
              min="1"
              max="20"
              value={maxIterations}
              onChange={(e) => setMaxIterations(parseInt(e.target.value) || DEFAULT_SEARCH_PARAMS.max_iterations)}
              disabled={currentStatus === 'running' || currentStatus === 'queued'}
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="max_accepted">Max Accepted Papers</label>
            <input
              id="max_accepted"
              type="number"
              min="10"
              value={maxAccepted}
              onChange={(e) => setMaxAccepted(parseInt(e.target.value) || DEFAULT_SEARCH_PARAMS.max_accepted)}
              disabled={currentStatus === 'running' || currentStatus === 'queued'}
            />
          </div>

          <div className="form-group">
            <label htmlFor="top_n">Top N Candidates</label>
            <input
              id="top_n"
              type="number"
              min="5"
              value={topN}
              onChange={(e) => setTopN(parseInt(e.target.value) || DEFAULT_SEARCH_PARAMS.top_n)}
              disabled={currentStatus === 'running' || currentStatus === 'queued'}
            />
          </div>
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
            {currentStatus === 'running' && totalAccepted > 0 && (
              <div className="status-info">
                Papers found: {totalAccepted}
              </div>
            )}
            {currentStatus === 'completed' && (
              <div className="status-info success">
                Search completed! Found {totalAccepted} papers.
              </div>
            )}
            {currentStatus === 'failed' && (
              <div className="status-info error">
                Search failed. Please try again.
              </div>
            )}
          </div>
        )}

        <div className="form-actions">
          <button
            type="submit"
            disabled={currentStatus === 'running' || currentStatus === 'queued'}
          >
            {currentStatus === 'running' || currentStatus === 'queued' ? 'Searching...' : 'Start Search'}
          </button>
          {(currentStatus === 'completed' || currentStatus === 'failed') && (
            <button type="button" onClick={handleReset}>
              New Search
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
