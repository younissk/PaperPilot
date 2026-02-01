import {
  useMonitoringPipelines,
  useMonitoringReports,
  useMonitoringCosts,
} from "@/hooks";

// Brutalist coral shadow style
const brutalShadow = { boxShadow: "3px 3px 0 #F3787A" };

function formatDuration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined || !Number.isFinite(seconds)) {
    return "—";
  }
  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const secs = Math.round(seconds - minutes * 60);
  return secs > 0 ? `${minutes}m ${secs}s` : `${minutes}m`;
}

/**
 * Proof strip with trust-building metrics.
 * Brutalist design with black borders and coral shadows.
 * Fetches real data from the monitoring API.
 */
export function ProofStrip() {
  const windowDays = 30;
  const pipelines = useMonitoringPipelines(windowDays);
  const reports = useMonitoringReports(windowDays);
  const costs = useMonitoringCosts(windowDays);

  const medianTime = formatDuration(pipelines.data?.duration_sec.p50);
  const reportsGenerated = reports.data?.reports_generated ?? 0;
  const avgArtifacts = costs.data?.cost_proxies.avg_artifacts_per_pipeline;
  const avgArtifactsStr =
    avgArtifacts !== null && avgArtifacts !== undefined && Number.isFinite(avgArtifacts)
      ? avgArtifacts.toFixed(1)
      : "—";

  const metrics = [
    {
      value: medianTime,
      label: "median generation time",
      sublabel: `last ${windowDays} days`,
    },
    {
      value: String(reportsGenerated),
      label: "reports generated",
      sublabel: `last ${windowDays} days`,
    },
    {
      value: avgArtifactsStr,
      label: "avg artifacts per report",
      sublabel: "data exports",
    },
  ];

  const isLoading = pipelines.isLoading || reports.isLoading || costs.isLoading;

  return (
    <section className="py-8 border-y border-black">
      <div className="max-w-4xl mx-auto px-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {metrics.map((metric) => (
            <div
              key={metric.label}
              className="bg-white border-2 border-black p-6 text-center"
              style={brutalShadow}
            >
              <div className="text-4xl font-bold text-shadow-brutal mb-2">
                {isLoading ? (
                  <span className="inline-block w-16 h-10 bg-gray-100 animate-pulse" />
                ) : (
                  metric.value
                )}
              </div>
              <div className="text-sm font-medium text-gray-900 lowercase">
                {metric.label}
              </div>
              <div className="text-xs text-gray-500 mt-1 lowercase">
                {metric.sublabel}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
