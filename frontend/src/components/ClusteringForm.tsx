/**
 * Clustering form component for starting clustering jobs.
 */

import { useState, FormEvent } from 'react';
import { startClustering, getClusteringStatus, type ClusteringRequest } from '../services/api';
import { useJobPolling } from '../hooks/useJobPolling';

interface ClusteringFormProps {
  query: string;
  onClusteringStart?: (jobId: string) => void;
  onClusteringComplete?: (jobId: string, htmlPath: string | null) => void;
  onCancel?: () => void;
}

export function ClusteringForm({ query, onClusteringStart, onClusteringComplete, onCancel }: ClusteringFormProps) {
  const [method, setMethod] = useState<'hdbscan' | 'dbscan' | 'kmeans'>('hdbscan');
  const [dimMethod, setDimMethod] = useState<'umap' | 'tsne' | 'pca'>('umap');
  const [nClusters, setNClusters] = useState<string>('');
  const [eps, setEps] = useState<string>('');
  const [minSamples, setMinSamples] = useState<string>('');
  const [filePath, setFilePath] = useState<string>('');
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { status, data, error: pollingError } = useJobPolling({
    pollFn: getClusteringStatus,
    jobId,
    enabled: jobId !== null,
    onComplete: (result) => {
      if (onClusteringComplete) {
        onClusteringComplete(result.job_id, result.html_content || null);
      }
    },
  });

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setJobId(null);

    // Validate kmeans requires n_clusters
    if (method === 'kmeans' && !nClusters.trim()) {
      setError('Number of clusters is required for kmeans method');
      return;
    }

    try {
      const request: ClusteringRequest = {
        query: query.trim(),
        method: method,
        dim_method: dimMethod,
        n_clusters: nClusters.trim() ? parseInt(nClusters.trim()) : null,
        eps: eps.trim() ? parseFloat(eps.trim()) : null,
        min_samples: minSamples.trim() ? parseInt(minSamples.trim()) : null,
        file_path: filePath.trim() || null,
      };

      const response = await startClustering(request);
      setJobId(response.job_id);
      if (onClusteringStart) {
        onClusteringStart(response.job_id);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start clustering';
      setError(errorMessage);
    }
  };

  const handleReset = () => {
    setMethod('hdbscan');
    setDimMethod('umap');
    setNClusters('');
    setEps('');
    setMinSamples('');
    setFilePath('');
    setJobId(null);
    setError(null);
  };

  const displayError = error || (pollingError ? pollingError.message : null);
  const currentStatus = status || (data?.status ?? null);
  const isKmeans = method === 'kmeans';
  const isDensityBased = method === 'dbscan' || method === 'hdbscan';

  return (
    <div className="clustering-form">
      <div className="clustering-form-header">
        <h2>Cluster Papers</h2>
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
            <label htmlFor="method">Clustering Method</label>
            <select
              id="method"
              value={method}
              onChange={(e) => setMethod(e.target.value as typeof method)}
              disabled={currentStatus === 'running' || currentStatus === 'queued'}
            >
              <option value="hdbscan">HDBSCAN (recommended)</option>
              <option value="dbscan">DBSCAN</option>
              <option value="kmeans">K-Means</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="dim_method">Dimension Reduction</label>
            <select
              id="dim_method"
              value={dimMethod}
              onChange={(e) => setDimMethod(e.target.value as typeof dimMethod)}
              disabled={currentStatus === 'running' || currentStatus === 'queued'}
            >
              <option value="umap">UMAP (recommended)</option>
              <option value="tsne">t-SNE</option>
              <option value="pca">PCA</option>
            </select>
          </div>
        </div>

        {isKmeans && (
          <div className="form-group">
            <label htmlFor="n_clusters">Number of Clusters *</label>
            <input
              id="n_clusters"
              type="number"
              min="2"
              value={nClusters}
              onChange={(e) => setNClusters(e.target.value)}
              placeholder="Required for kmeans"
              disabled={currentStatus === 'running' || currentStatus === 'queued'}
              required
            />
            <small>Required for kmeans method</small>
          </div>
        )}

        {isDensityBased && (
          <>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="eps">Eps (optional)</label>
                <input
                  id="eps"
                  type="number"
                  min="0"
                  step="0.1"
                  value={eps}
                  onChange={(e) => setEps(e.target.value)}
                  placeholder="Auto"
                  disabled={currentStatus === 'running' || currentStatus === 'queued'}
                />
                <small>Distance threshold for DBSCAN/HDBSCAN</small>
              </div>

              <div className="form-group">
                <label htmlFor="min_samples">Min Samples (optional)</label>
                <input
                  id="min_samples"
                  type="number"
                  min="1"
                  value={minSamples}
                  onChange={(e) => setMinSamples(e.target.value)}
                  placeholder="Auto"
                  disabled={currentStatus === 'running' || currentStatus === 'queued'}
                />
                <small>Minimum samples for DBSCAN/HDBSCAN</small>
              </div>
            </div>
          </>
        )}

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
                Clustering completed!
              </div>
            )}
            {currentStatus === 'failed' && (
              <div className="status-info error">
                Clustering failed. Please try again.
              </div>
            )}
          </div>
        )}

        <div className="form-actions">
          <button
            type="submit"
            disabled={currentStatus === 'running' || currentStatus === 'queued'}
          >
            {currentStatus === 'running' || currentStatus === 'queued' ? 'Clustering...' : 'Start Clustering'}
          </button>
          {(currentStatus === 'completed' || currentStatus === 'failed') && (
            <button type="button" onClick={handleReset}>
              New Clustering
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
