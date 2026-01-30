import { SEO } from "@/components";
import {
  useHealthCheck,
  useMonitoringCosts,
  useMonitoringPipelines,
  useMonitoringReports,
  useReadinessCheck,
} from "@/hooks";

function formatSeconds(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "—";
  }
  if (value < 60) {
    return `${value.toFixed(1)}s`;
  }
  const minutes = Math.floor(value / 60);
  const seconds = value - minutes * 60;
  return `${minutes}m ${seconds.toFixed(0)}s`;
}

function formatBytes(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "—";
  }
  const units = ["B", "KB", "MB", "GB", "TB"] as const;
  let n = value;
  let u = 0;
  while (n >= 1024 && u < units.length - 1) {
    n /= 1024;
    u += 1;
  }
  const decimals = u === 0 ? 0 : 1;
  return `${n.toFixed(decimals)} ${units[u]}`;
}

type MonitorState = "ok" | "degraded" | "down";

function Heartbeat({ state, bpm }: { state: MonitorState; bpm: number }) {
  const color =
    state === "ok"
      ? "stroke-teal-500"
      : state === "degraded"
        ? "stroke-orange-500"
        : "stroke-red-500";

  const pulseClass =
    state === "ok"
      ? "animate-pulse"
      : state === "degraded"
        ? "animate-pulse"
        : "";

  const showFlatline = state === "down";

  return (
    <div className="card">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="stack stack-sm">
          <h2 className="text-lg">Health & Readiness</h2>
          <p className="text-sm text-gray-500">
            State:{" "}
            <span className="font-semibold">
              {state === "ok"
                ? "OK"
                : state === "degraded"
                  ? "Degraded"
                  : "Down"}
            </span>
            {" · "}
            BPM: <span className="font-semibold">{bpm}</span>
          </p>
        </div>

        <span
          className={`inline-flex items-center gap-2 rounded-md px-3 py-1 text-sm border ${
            state === "ok"
              ? "bg-teal-50 border-teal-200 text-teal-800"
              : state === "degraded"
                ? "bg-orange-50 border-orange-200 text-orange-800"
                : "bg-red-50 border-red-200 text-red-800"
          }`}
        >
          <span
            className={`w-2.5 h-2.5 rounded-full ${
              state === "ok"
                ? "bg-teal-500"
                : state === "degraded"
                  ? "bg-orange-500"
                  : "bg-red-500"
            } ${pulseClass}`}
          />
          {state === "ok"
            ? "Ready"
            : state === "degraded"
              ? "Not ready"
              : "Offline"}
        </span>
      </div>

      <div className="mt-4 bg-gray-50 border border-gray-200 rounded-md p-4 overflow-hidden">
        <svg
          viewBox="0 0 240 60"
          className="w-full h-14"
          role="img"
          aria-label="Heartbeat monitor"
        >
          <path
            d={
              showFlatline
                ? "M0 30 H240"
                : "M0 30 H30 L38 30 L44 12 L50 48 L56 30 H90 L96 30 L102 15 L108 45 L114 30 H240"
            }
            className={`fill-none stroke-[3] ${color} ${
              showFlatline ? "" : "ecg-line"
            }`}
            strokeLinejoin="round"
            strokeLinecap="round"
          />
          <path
            d="M0 30 H240"
            className="fill-none stroke-[2] stroke-gray-200"
            strokeLinejoin="round"
            strokeLinecap="round"
          />
        </svg>
      </div>
    </div>
  );
}

/**
 * Monitoring page placeholder for API and system status.
 */
export default function MonitoringPage() {
  const windowDays = 30;

  const health = useHealthCheck();
  const readiness = useReadinessCheck();
  const reports = useMonitoringReports(windowDays);
  const pipelines = useMonitoringPipelines(windowDays);
  const costs = useMonitoringCosts(windowDays);

  const monitorState: MonitorState = (() => {
    if (health.isLoading) {
      return "degraded";
    }
    if (health.error || !health.data) {
      return "down";
    }
    if (readiness.data?.ready) {
      return "ok";
    }
    return "degraded";
  })();

  const bpm = monitorState === "ok" ? 78 : monitorState === "degraded" ? 52 : 0;

  const daily = reports.data?.daily ?? [];
  const maxDaily = Math.max(1, ...daily.map((d) => d.count));

  return (
    <>
      <SEO
        title="Monitoring"
        description="API and system monitoring dashboard"
      />
      <div className="container container-lg">
        <div className="stack stack-xl">
          <h1>Monitoring</h1>

          <Heartbeat state={monitorState} bpm={bpm} />

          <div className="grid gap-6 md:grid-cols-3">
            <div className="card">
              <div className="stack stack-sm">
                <h2 className="text-base">Reports (last {windowDays} days)</h2>
                {reports.isLoading ? (
                  <div className="inline inline-sm text-gray-500">
                    <div className="spinner" />
                    <span>Loading…</span>
                  </div>
                ) : reports.error ? (
                  <div className="text-sm text-red-700">
                    {reports.error instanceof Error
                      ? reports.error.message
                      : "Failed to load report metrics"}
                  </div>
                ) : (
                  <>
                    <div className="text-3xl font-semibold text-gray-900">
                      {reports.data?.reports_generated ?? 0}
                    </div>
                    <div className="mt-3">
                      <div className="flex items-end gap-0.5 h-10">
                        {daily.slice(-windowDays).map((d) => (
                          <div
                            key={d.date}
                            className="w-1 rounded-sm bg-primary-200"
                            style={{
                              height: `${Math.max(
                                8,
                                Math.round((d.count / maxDaily) * 100),
                              )}%`,
                            }}
                            title={`${d.date}: ${d.count}`}
                          />
                        ))}
                      </div>
                      <p className="text-xs text-gray-500 mt-2">
                        Daily counts (sparkline)
                      </p>
                    </div>
                  </>
                )}
              </div>
            </div>

            <div className="card">
              <div className="stack stack-sm">
                <h2 className="text-base">Pipeline time (last {windowDays} days)</h2>
                {pipelines.isLoading ? (
                  <div className="inline inline-sm text-gray-500">
                    <div className="spinner" />
                    <span>Loading…</span>
                  </div>
                ) : pipelines.error ? (
                  <div className="text-sm text-red-700">
                    {pipelines.error instanceof Error
                      ? pipelines.error.message
                      : "Failed to load pipeline metrics"}
                  </div>
                ) : (
                  <>
                    <div className="text-sm text-gray-600">
                      Avg:{" "}
                      <span className="font-semibold text-gray-900">
                        {formatSeconds(pipelines.data?.duration_sec.avg)}
                      </span>
                      {" · "}p95:{" "}
                      <span className="font-semibold text-gray-900">
                        {formatSeconds(pipelines.data?.duration_sec.p95)}
                      </span>
                    </div>

                    <div className="mt-3">
                      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                        Avg per phase
                      </h3>
                      <div className="stack stack-sm">
                        {Object.entries(
                          pipelines.data?.per_phase_avg_duration_sec ?? {},
                        ).map(([phase, sec]) => (
                          <div key={phase} className="flex justify-between text-sm">
                            <span className="text-gray-600">{phase}</span>
                            <span className="font-medium text-gray-900">
                              {formatSeconds(sec)}
                            </span>
                          </div>
                        ))}
                        {Object.keys(
                          pipelines.data?.per_phase_avg_duration_sec ?? {},
                        ).length === 0 && (
                          <p className="text-sm text-gray-500">
                            No phase timing data yet.
                          </p>
                        )}
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>

            <div className="card">
              <div className="stack stack-sm">
                <h2 className="text-base">Cost signals (excluding OpenAI)</h2>
                {costs.isLoading ? (
                  <div className="inline inline-sm text-gray-500">
                    <div className="spinner" />
                    <span>Loading…</span>
                  </div>
                ) : costs.error ? (
                  <div className="text-sm text-red-700">
                    {costs.error instanceof Error
                      ? costs.error.message
                      : "Failed to load cost signals"}
                  </div>
                ) : (
                  <>
                    <div className="stack stack-sm">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Bytes uploaded (total)</span>
                        <span className="font-medium text-gray-900">
                          {formatBytes(costs.data?.cost_proxies.bytes_uploaded_total)}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Avg bytes / pipeline</span>
                        <span className="font-medium text-gray-900">
                          {formatBytes(
                            costs.data?.cost_proxies.avg_bytes_uploaded_per_pipeline,
                          )}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Artifacts (total)</span>
                        <span className="font-medium text-gray-900">
                          {costs.data?.cost_proxies.artifact_count_total ?? 0}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Avg artifacts / pipeline</span>
                        <span className="font-medium text-gray-900">
                          {costs.data?.cost_proxies.avg_artifacts_per_pipeline ??
                            "—"}
                        </span>
                      </div>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">
                      OpenAI/LLM costs intentionally excluded for now.
                    </p>
                  </>
                )}
              </div>
            </div>
          </div>

          {(readiness.error || readiness.data) && (
            <div className="card">
              <h2 className="text-base mb-3">Readiness checks</h2>
              {readiness.error ? (
                <p className="text-sm text-red-700">
                  {readiness.error instanceof Error
                    ? readiness.error.message
                    : "Failed to load readiness"}
                </p>
              ) : (
                <div className="grid gap-2">
                  {Object.entries(readiness.data?.checks ?? {}).map(
                    ([name, status]) => (
                      <div
                        key={name}
                        className="flex justify-between text-sm border-b border-gray-100 pb-2 last:border-b-0 last:pb-0"
                      >
                        <span className="text-gray-600">{name}</span>
                        <span
                          className={
                            status === "connected"
                              ? "text-teal-700 font-medium"
                              : "text-red-700 font-medium"
                          }
                        >
                          {status}
                        </span>
                      </div>
                    ),
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
