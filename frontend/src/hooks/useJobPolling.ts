/**
 * Custom hook for polling job status from the API.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { JOB_POLLING_INTERVAL } from '../config';

export type JobStatus = 'queued' | 'running' | 'completed' | 'failed';

export interface UseJobPollingOptions<T> {
  pollFn: (jobId: string) => Promise<T>;
  jobId: string | null;
  enabled?: boolean;
  interval?: number;
  onComplete?: (data: T) => void;
  onError?: (error: Error) => void;
}

export interface UseJobPollingResult<T> {
  data: T | null;
  status: JobStatus | null;
  error: Error | null;
  isLoading: boolean;
  stopPolling: () => void;
}

/**
 * Polls a job endpoint until the job is completed or failed.
 */
export function useJobPolling<T extends { status: JobStatus }>({
  pollFn,
  jobId,
  enabled = true,
  interval = JOB_POLLING_INTERVAL,
  onComplete,
  onError,
}: UseJobPollingOptions<T>): UseJobPollingResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  const intervalRef = useRef<number | null>(null);
  const isPollingRef = useRef(false);

  const stopPolling = useCallback(() => {
    if (intervalRef.current !== null) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    isPollingRef.current = false;
  }, []);

  const poll = useCallback(async () => {
    if (!jobId || !enabled || isPollingRef.current) {
      return;
    }

    try {
      setIsLoading(true);
      isPollingRef.current = true;
      const result = await pollFn(jobId);
      
      setData(result);
      setStatus(result.status);
      setError(null);

      // Stop polling if job is completed or failed
      if (result.status === 'completed' || result.status === 'failed') {
        stopPolling();
        setIsLoading(false);
        isPollingRef.current = false;
        
        if (result.status === 'completed' && onComplete) {
          onComplete(result);
        } else if (result.status === 'failed' && onError) {
          onError(new Error('Job failed'));
        }
      } else {
        isPollingRef.current = false;
        setIsLoading(false);
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error');
      setError(error);
      setIsLoading(false);
      isPollingRef.current = false;
      stopPolling();
      
      if (onError) {
        onError(error);
      }
    }
  }, [jobId, enabled, pollFn, onComplete, onError, stopPolling]);

  useEffect(() => {
    if (!jobId || !enabled) {
      stopPolling();
      return;
    }

    // Initial poll
    poll();

    // Set up interval polling
    intervalRef.current = window.setInterval(() => {
      poll();
    }, interval);

    return () => {
      stopPolling();
    };
  }, [jobId, enabled, interval, poll, stopPolling]);

  return {
    data,
    status,
    error,
    isLoading,
    stopPolling,
  };
}
