import { useMutation, useQuery } from '@tanstack/react-query';
import { startReport, getReportStatus, type ReportRequest, type ReportResponse } from '../../services/api';

export function useReportMutation() {
  return useMutation<ReportResponse, Error, ReportRequest>({
    mutationFn: startReport,
  });
}

export function useReportStatus(jobId: string | null, enabled: boolean = true) {
  return useQuery<ReportResponse, Error>({
    queryKey: ['report', jobId],
    queryFn: () => getReportStatus(jobId!),
    enabled: enabled && jobId !== null,
    refetchInterval: (data) => {
      if (data?.status === 'queued' || data?.status === 'running') {
        return 2000;
      }
      return false;
    },
    retry: false,
  });
}
