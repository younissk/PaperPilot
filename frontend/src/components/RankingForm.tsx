/**
 * Ranking form component for starting ELO ranking jobs.
 */

import { useState, FormEvent } from 'react';
import { startRanking, getRankingStatus, type RankingRequest } from '../services/api';
import { useJobPolling } from '../hooks/useJobPolling';

interface RankingFormProps {
  query: string;
  onRankingStart?: (jobId: string) => void;
  onRankingComplete?: (jobId: string, papers: unknown[]) => void;
  onCancel?: () => void;
}

export function RankingForm({ query, onRankingStart, onRankingComplete, onCancel }: RankingFormProps) {
  const [kFactor, setKFactor] = useState(32.0);
  const [pairing, setPairing] = useState<'swiss' | 'random'>('swiss');
  const [earlyStop, setEarlyStop] = useState(true);
  const [concurrency, setConcurrency] = useState(5);
  const [tournament, setTournament] = useState(false);
  const [filePath, setFilePath] = useState<string>('');
  const [nMatches, setNMatches] = useState<string>('');
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { status, data, error: pollingError } = useJobPolling({
    pollFn: getRankingStatus,
    jobId,
    enabled: jobId !== null,
    onComplete: (result) => {
      if (onRankingComplete && result.papers) {
        onRankingComplete(result.job_id, result.papers);
      }
    },
  });

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setJobId(null);

    try {
      const request: RankingRequest = {
        query: query.trim(),
        k_factor: kFactor,
        pairing: pairing,
        early_stop: earlyStop,
        concurrency: concurrency,
        tournament: tournament,
        file_path: filePath.trim() || null,
        n_matches: nMatches.trim() ? parseInt(nMatches.trim()) : null,
      };

      const response = await startRanking(request);
      setJobId(response.job_id);
      if (onRankingStart) {
        onRankingStart(response.job_id);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start ranking';
      setError(errorMessage);
    }
  };

  const handleReset = () => {
    setKFactor(32.0);
    setPairing('swiss');
    setEarlyStop(true);
    setConcurrency(5);
    setTournament(false);
    setFilePath('');
    setNMatches('');
    setJobId(null);
    setError(null);
  };

  const displayError = error || (pollingError ? pollingError.message : null);
  const currentStatus = status || (data?.status ?? null);
  const matchesPlayed = data?.matches_played ?? 0;
  const totalMatches = data?.total_matches ?? 0;

  return (
    <div className="ranking-form">
      <div className="ranking-form-header">
        <h2>Rank Papers with ELO</h2>
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
            <label htmlFor="k_factor">K-Factor</label>
            <input
              id="k_factor"
              type="number"
              min="1"
              max="100"
              step="0.1"
              value={kFactor}
              onChange={(e) => setKFactor(parseFloat(e.target.value) || 32.0)}
              disabled={currentStatus === 'running' || currentStatus === 'queued'}
            />
            <small>Higher = more volatile ratings (default: 32.0)</small>
          </div>

          <div className="form-group">
            <label htmlFor="pairing">Pairing Strategy</label>
            <select
              id="pairing"
              value={pairing}
              onChange={(e) => setPairing(e.target.value as 'swiss' | 'random')}
              disabled={currentStatus === 'running' || currentStatus === 'queued'}
            >
              <option value="swiss">Swiss (recommended)</option>
              <option value="random">Random</option>
            </select>
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="concurrency">Concurrency</label>
            <input
              id="concurrency"
              type="number"
              min="1"
              max="20"
              value={concurrency}
              onChange={(e) => setConcurrency(parseInt(e.target.value) || 5)}
              disabled={currentStatus === 'running' || currentStatus === 'queued'}
            />
            <small>Max concurrent API calls (default: 5)</small>
          </div>

          <div className="form-group">
            <label htmlFor="n_matches">Number of Matches (optional)</label>
            <input
              id="n_matches"
              type="number"
              min="1"
              value={nMatches}
              onChange={(e) => setNMatches(e.target.value)}
              placeholder="Auto (papers × 3)"
              disabled={currentStatus === 'running' || currentStatus === 'queued'}
            />
            <small>Leave empty for automatic calculation</small>
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

        <div className="form-row">
          <div className="form-group checkbox-group">
            <label>
              <input
                type="checkbox"
                checked={earlyStop}
                onChange={(e) => setEarlyStop(e.target.checked)}
                disabled={currentStatus === 'running' || currentStatus === 'queued'}
              />
              Early Stop (stop when top-30 rankings stabilize)
            </label>
          </div>

          <div className="form-group checkbox-group">
            <label>
              <input
                type="checkbox"
                checked={tournament}
                onChange={(e) => setTournament(e.target.checked)}
                disabled={currentStatus === 'running' || currentStatus === 'queued'}
              />
              Tournament Mode
            </label>
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
            {currentStatus === 'running' && totalMatches > 0 && (
              <div className="status-info">
                Match {matchesPlayed} of {totalMatches}
                {totalMatches > 0 && (
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{ width: `${(matchesPlayed / totalMatches) * 100}%` }}
                    />
                  </div>
                )}
              </div>
            )}
            {currentStatus === 'completed' && (
              <div className="status-info success">
                Ranking completed! {data?.papers?.length ?? 0} papers ranked.
              </div>
            )}
            {currentStatus === 'failed' && (
              <div className="status-info error">
                Ranking failed. Please try again.
              </div>
            )}
          </div>
        )}

        <div className="form-actions">
          <button
            type="submit"
            disabled={currentStatus === 'running' || currentStatus === 'queued'}
          >
            {currentStatus === 'running' || currentStatus === 'queued' ? 'Ranking...' : 'Start Ranking'}
          </button>
          {(currentStatus === 'completed' || currentStatus === 'failed') && (
            <button type="button" onClick={handleReset}>
              New Ranking
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
