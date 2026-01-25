/**
 * Main application component for PaperPilot frontend.
 */

import { useState, useEffect } from 'react';
import { SearchForm } from './components/SearchForm';
import { PaperList } from './components/PaperList';
import { QueryList } from './components/QueryList';
import { healthCheck, type Paper } from './services/api';
import './App.css';

type Tab = 'search' | 'results' | 'queries';

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('search');
  const [papers, setPapers] = useState<Paper[]>([]);
  const [apiStatus, setApiStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [currentQuery, setCurrentQuery] = useState<string | null>(null);

  useEffect(() => {
    checkApiHealth();
  }, []);

  const checkApiHealth = async () => {
    try {
      setApiStatus('checking');
      await healthCheck();
      setApiStatus('online');
    } catch {
      setApiStatus('offline');
    }
  };

  const handleSearchComplete = (_jobId: string, searchPapers: unknown[]) => {
    setPapers(searchPapers as Paper[]);
    setActiveTab('results');
  };

  const handleQuerySelect = (query: string, queryPapers: Paper[]) => {
    setCurrentQuery(query);
    setPapers(queryPapers);
    setActiveTab('results');
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>PaperPilot</h1>
        <div className="api-status">
          <span className={`status-indicator status-${apiStatus}`}></span>
          <span className="status-text">
            {apiStatus === 'checking' && 'Checking API...'}
            {apiStatus === 'online' && 'API Online'}
            {apiStatus === 'offline' && 'API Offline'}
          </span>
          {apiStatus === 'offline' && (
            <button onClick={checkApiHealth} className="retry-btn">
              Retry
            </button>
          )}
        </div>
      </header>

      <nav className="app-nav">
        <button
          className={`nav-tab ${activeTab === 'search' ? 'active' : ''}`}
          onClick={() => setActiveTab('search')}
        >
          Search
        </button>
        <button
          className={`nav-tab ${activeTab === 'results' ? 'active' : ''}`}
          onClick={() => setActiveTab('results')}
          disabled={papers.length === 0}
        >
          Results {papers.length > 0 && `(${papers.length})`}
        </button>
        <button
          className={`nav-tab ${activeTab === 'queries' ? 'active' : ''}`}
          onClick={() => setActiveTab('queries')}
        >
          Previous Queries
        </button>
      </nav>

      <main className="app-main">
        {apiStatus === 'offline' && (
          <div className="api-warning">
            <p>
              <strong>Warning:</strong> Cannot connect to the API server.
              Make sure the backend is running on <code>http://localhost:8000</code>
            </p>
          </div>
        )}

        {activeTab === 'search' && (
          <div className="tab-content">
            <SearchForm onSearchComplete={handleSearchComplete} />
          </div>
        )}

        {activeTab === 'results' && (
          <div className="tab-content">
            {papers.length === 0 ? (
              <div className="empty-state">
                <p>No results to display. Start a search to see papers here.</p>
              </div>
            ) : (
              <PaperList
                papers={papers}
                title={currentQuery ? `Results for: ${currentQuery}` : 'Search Results'}
              />
            )}
          </div>
        )}

        {activeTab === 'queries' && (
          <div className="tab-content">
            <QueryList onSelectQuery={handleQuerySelect} />
          </div>
        )}
      </main>

      <footer className="app-footer">
        <p>PaperPilot - AI-powered academic literature discovery</p>
      </footer>
    </div>
  );
}

export default App;
