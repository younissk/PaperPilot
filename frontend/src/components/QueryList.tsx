/**
 * Component for displaying and managing previous search queries.
 */

import { useEffect, useState } from 'react';
import { listQueries, getQueryMetadata, getSnowballResults, type QueryListResponse, type QueryMetadataResponse, type Paper } from '../services/api';

interface QueryListProps {
  onSelectQuery?: (query: string, papers: Paper[]) => void;
}

export function QueryList({ onSelectQuery }: QueryListProps) {
  const [queries, setQueries] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedQuery, setSelectedQuery] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<Record<string, unknown> | null>(null);
  const [loadingMetadata, setLoadingMetadata] = useState(false);

  useEffect(() => {
    loadQueries();
  }, []);

  const loadQueries = async () => {
    try {
      setLoading(true);
      setError(null);
      const response: QueryListResponse = await listQueries();
      setQueries(response.queries);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load queries';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleQueryClick = async (query: string) => {
    try {
      setLoadingMetadata(true);
      setSelectedQuery(query);
      setError(null);

      // Load metadata
      const metadataResponse: QueryMetadataResponse = await getQueryMetadata(query);
      setMetadata(metadataResponse.metadata);

      // Load papers and notify parent
      if (onSelectQuery) {
        const snowballData = await getSnowballResults(query);
        onSelectQuery(query, snowballData.papers);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load query data';
      setError(errorMessage);
    } finally {
      setLoadingMetadata(false);
    }
  };

  if (loading) {
    return (
      <div className="query-list">
        <h2>Previous Queries</h2>
        <div className="loading-state">Loading queries...</div>
      </div>
    );
  }

  if (error && queries.length === 0) {
    return (
      <div className="query-list">
        <h2>Previous Queries</h2>
        <div className="error-message">{error}</div>
        <button onClick={loadQueries}>Retry</button>
      </div>
    );
  }

  return (
    <div className="query-list">
      <div className="query-list-header">
        <h2>Previous Queries</h2>
        <button onClick={loadQueries} className="refresh-btn" title="Refresh queries">
          ↻
        </button>
      </div>

      {error && (
        <div className="error-message">{error}</div>
      )}

      {queries.length === 0 ? (
        <div className="empty-state">
          <p>No previous queries found.</p>
        </div>
      ) : (
        <div className="queries-container">
          {queries.map((query) => (
            <div
              key={query}
              className={`query-item ${selectedQuery === query ? 'selected' : ''}`}
              onClick={() => handleQueryClick(query)}
            >
              <div className="query-text">{query}</div>
              {loadingMetadata && selectedQuery === query && (
                <div className="query-loading">Loading...</div>
              )}
              {metadata && selectedQuery === query && (
                <div className="query-metadata">
                  {Object.entries(metadata).map(([key, value]) => (
                    <div key={key} className="metadata-item">
                      <span className="metadata-key">{key}:</span>
                      <span className="metadata-value">
                        {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
