import { useState, FormEvent } from 'react';
import { TextInput, NumberInput, Button, Stack, Alert, Badge, Group, Paper } from '@mantine/core';
import { useSearchMutation, useSearchStatus } from '../hooks/queries/useSearch';
import { DEFAULT_SEARCH_PARAMS } from '../config';
import { showError, showSuccess } from '../utils/notifications';
import type { Paper as PaperType } from '../services/api';

interface SearchFormProps {
  onSearchComplete?: (jobId: string, papers: PaperType[]) => void;
}

export function SearchForm({ onSearchComplete }: SearchFormProps) {
  const [query, setQuery] = useState('');
  const [numResults, setNumResults] = useState(DEFAULT_SEARCH_PARAMS.num_results);
  const [maxIterations, setMaxIterations] = useState(DEFAULT_SEARCH_PARAMS.max_iterations);
  const [maxAccepted, setMaxAccepted] = useState(DEFAULT_SEARCH_PARAMS.max_accepted);
  const [topN, setTopN] = useState(DEFAULT_SEARCH_PARAMS.top_n);
  const [jobId, setJobId] = useState<string | null>(null);

  const searchMutation = useSearchMutation();
  const { data: searchData, error: pollingError } = useSearchStatus(jobId, jobId !== null);

  // Handle search completion
  if (searchData?.status === 'completed' && searchData.papers && onSearchComplete) {
    onSearchComplete(searchData.job_id, searchData.papers);
    showSuccess(`Search completed! Found ${searchData.papers.length} papers.`);
    setJobId(null);
  }

  // Handle search errors
  if (searchData?.status === 'failed') {
    showError('Search failed. Please try again.');
    setJobId(null);
  }

  if (pollingError) {
    showError(pollingError.message);
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!query.trim()) {
      showError('Please enter a search query');
      return;
    }

    try {
      const response = await searchMutation.mutateAsync({
        query: query.trim(),
        num_results: numResults,
        max_iterations: maxIterations,
        max_accepted: maxAccepted,
        top_n: topN,
      });
      setJobId(response.job_id);
      showSuccess('Search started successfully!');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start search';
      showError(errorMessage);
    }
  };

  const handleReset = () => {
    setQuery('');
    setNumResults(DEFAULT_SEARCH_PARAMS.num_results);
    setMaxIterations(DEFAULT_SEARCH_PARAMS.max_iterations);
    setMaxAccepted(DEFAULT_SEARCH_PARAMS.max_accepted);
    setTopN(DEFAULT_SEARCH_PARAMS.top_n);
    setJobId(null);
  };

  const currentStatus = searchData?.status || (searchMutation.isPending ? 'queued' : null);
  const totalAccepted = searchData?.total_accepted ?? 0;
  const isProcessing = currentStatus === 'running' || currentStatus === 'queued' || searchMutation.isPending;

  return (
    <Paper p="md" withBorder>
      <form onSubmit={handleSubmit}>
        <Stack gap="md">
          <TextInput
            label="Research Query"
            placeholder="e.g., LLM Based Recommendation Systems"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={isProcessing}
            required
            size="md"
          />

          <Group grow>
            <NumberInput
              label="Results per Query"
              value={numResults}
              onChange={(value) => setNumResults(typeof value === 'number' ? value : DEFAULT_SEARCH_PARAMS.num_results)}
              min={1}
              max={100}
              disabled={isProcessing}
            />
            <NumberInput
              label="Max Iterations"
              value={maxIterations}
              onChange={(value) => setMaxIterations(typeof value === 'number' ? value : DEFAULT_SEARCH_PARAMS.max_iterations)}
              min={1}
              max={20}
              disabled={isProcessing}
            />
          </Group>

          <Group grow>
            <NumberInput
              label="Max Accepted Papers"
              value={maxAccepted}
              onChange={(value) => setMaxAccepted(typeof value === 'number' ? value : DEFAULT_SEARCH_PARAMS.max_accepted)}
              min={10}
              disabled={isProcessing}
            />
            <NumberInput
              label="Top N Candidates"
              value={topN}
              onChange={(value) => setTopN(typeof value === 'number' ? value : DEFAULT_SEARCH_PARAMS.top_n)}
              min={5}
              disabled={isProcessing}
            />
          </Group>

          {currentStatus && (
            <Alert
              color={currentStatus === 'completed' ? 'primary' : currentStatus === 'failed' ? 'error' : 'accent'}
              title={currentStatus.toUpperCase()}
            >
              {currentStatus === 'running' && totalAccepted > 0 && (
                <div>Papers found: {totalAccepted}</div>
              )}
              {currentStatus === 'completed' && (
                <div>Search completed! Found {totalAccepted} papers.</div>
              )}
              {currentStatus === 'failed' && (
                <div>Search failed. Please try again.</div>
              )}
            </Alert>
          )}

          <Group>
            <Button
              type="submit"
              disabled={isProcessing}
              loading={isProcessing}
            >
              {isProcessing ? 'Searching...' : 'Start Search'}
            </Button>
            {(currentStatus === 'completed' || currentStatus === 'failed') && (
              <Button variant="outline" onClick={handleReset}>
                New Search
              </Button>
            )}
          </Group>
        </Stack>
      </form>
    </Paper>
  );
}
