import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router";
import { useMutation } from "@tanstack/react-query";
import { startPipeline, slugifyQuery } from "@/lib/api";
import { DEFAULT_PIPELINE_PARAMS } from "@/lib/config";
import type { PipelineRequest } from "@/lib/types";

// Brutalist shadow styles
const brutalShadow = { boxShadow: "3px 3px 0 #F3787A" };

/**
 * Search form component with advanced options - brutalist design.
 */
export function SearchForm() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [pipelineEnabled, setPipelineEnabled] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form state for advanced options
  const [numResults, setNumResults] = useState<number>(DEFAULT_PIPELINE_PARAMS.num_results);
  const [maxIterations, setMaxIterations] = useState<number>(DEFAULT_PIPELINE_PARAMS.max_iterations);
  const [maxAccepted, setMaxAccepted] = useState<number>(DEFAULT_PIPELINE_PARAMS.max_accepted);
  const [topN, setTopN] = useState<number>(DEFAULT_PIPELINE_PARAMS.top_n);
  const [kFactor, setKFactor] = useState<number>(DEFAULT_PIPELINE_PARAMS.k_factor);
  const [pairing, setPairing] = useState<"swiss" | "random">(DEFAULT_PIPELINE_PARAMS.pairing);
  const [earlyStop, setEarlyStop] = useState<boolean>(DEFAULT_PIPELINE_PARAMS.early_stop);
  const [eloConcurrency, setEloConcurrency] = useState<number>(DEFAULT_PIPELINE_PARAMS.elo_concurrency);
  const [reportTopK, setReportTopK] = useState<number>(DEFAULT_PIPELINE_PARAMS.report_top_k);

  // Notification settings
  const [notificationEmail, setNotificationEmail] = useState<string>("");

  const mutation = useMutation({
    mutationFn: (request: PipelineRequest) => startPipeline(request),
    onSuccess: (response) => {
      const slug = slugifyQuery(query);
      navigate(`/report/${slug}?job=${response.job_id}`);
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : "Failed to start pipeline");
    },
  });

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setError(null);
    mutation.mutate({
      query: query.trim(),
      num_results: numResults,
      max_iterations: maxIterations,
      max_accepted: maxAccepted,
      top_n: topN,
      k_factor: kFactor,
      pairing,
      early_stop: earlyStop,
      elo_concurrency: eloConcurrency,
      report_top_k: reportTopK,
      notification_email: notificationEmail.trim() || undefined,
    });
  };

  return (
    <div className="stack stack-lg text-center">
      <h1 className="text-5xl font-bold text-black leading-tight md:text-4xl text-shadow-brutal lowercase">
        discover research papers
      </h1>
      <p className="text-lg text-gray-600 max-w-xl mx-auto lowercase">
        use our intelligent snowball search to find and explore relevant academic
        papers. enter your research query to get started.
      </p>

      <form onSubmit={handleSubmit} className="w-full mt-8">
        <div className="flex gap-4 md:flex-col">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="form-input form-input-lg flex-1 border-2 border-black"
            style={brutalShadow}
            placeholder="e.g., llm based recommendation systems"
            required
          />
          <button
            type="submit"
            disabled={mutation.isPending}
            className="btn btn-brutal btn-lg whitespace-nowrap lowercase"
            style={brutalShadow}
          >
            {mutation.isPending ? "starting..." : "search"}
          </button>
        </div>

        <div className="flex justify-between items-center mt-4 md:flex-col md:items-start md:gap-2">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={pipelineEnabled}
              onChange={(e) => setPipelineEnabled(e.target.checked)}
              className="w-4 h-4 accent-black"
            />
            <span className="text-sm text-gray-600 lowercase">
              full pipeline (search + rank + report)
            </span>
          </label>
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="bg-transparent border-none text-black cursor-pointer text-sm hover:underline lowercase"
          >
            {showAdvanced ? "hide advanced options" : "show advanced options"}
          </button>
        </div>

        {showAdvanced && (
          <div className="mt-6">
            <div className="bg-white border-2 border-black p-6 text-left" style={brutalShadow}>
              <h4 className="text-sm font-bold text-black mb-4 lowercase">
                query configuration
              </h4>
              <div className="grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-4">
                <div className="form-group">
                  <label className="form-label">Results per Query</label>
                  <input
                    type="number"
                    value={numResults}
                    onChange={(e) => setNumResults(Number(e.target.value))}
                    min={1}
                    max={100}
                    className="form-input"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Max Iterations</label>
                  <input
                    type="number"
                    value={maxIterations}
                    onChange={(e) => setMaxIterations(Number(e.target.value))}
                    min={1}
                    max={20}
                    className="form-input"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Max Accepted Papers</label>
                  <input
                    type="number"
                    value={maxAccepted}
                    onChange={(e) => setMaxAccepted(Number(e.target.value))}
                    min={10}
                    className="form-input"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Top N Candidates</label>
                  <input
                    type="number"
                    value={topN}
                    onChange={(e) => setTopN(Number(e.target.value))}
                    min={5}
                    className="form-input"
                  />
                </div>
              </div>

              {pipelineEnabled && (
                <>
                  <h4 className="text-sm font-bold text-black mb-4 mt-6 lowercase">
                    elo ranking configuration
                  </h4>
                  <div className="grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-4">
                    <div className="form-group">
                      <label className="form-label">K-Factor</label>
                      <input
                        type="number"
                        value={kFactor}
                        onChange={(e) => setKFactor(Number(e.target.value))}
                        min={1}
                        max={100}
                        className="form-input"
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Pairing Strategy</label>
                      <select
                        value={pairing}
                        onChange={(e) =>
                          setPairing(e.target.value as "swiss" | "random")
                        }
                        className="form-input"
                      >
                        <option value="swiss">Swiss (Recommended)</option>
                        <option value="random">Random</option>
                      </select>
                    </div>
                    <div className="form-group">
                      <label className="form-label">ELO Concurrency</label>
                      <input
                        type="number"
                        value={eloConcurrency}
                        onChange={(e) => setEloConcurrency(Number(e.target.value))}
                        min={1}
                        max={20}
                        className="form-input"
                      />
                    </div>
                    <div className="form-group">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={earlyStop}
                          onChange={(e) => setEarlyStop(e.target.checked)}
                        />
                        Early Stop (when rankings stabilize)
                      </label>
                    </div>
                  </div>

                  <h4 className="text-sm font-bold text-black mb-4 mt-6 lowercase">
                    report generation
                  </h4>
                  <div className="grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-4">
                    <div className="form-group">
                      <label className="form-label">Top K Papers for Report</label>
                      <input
                        type="number"
                        value={reportTopK}
                        onChange={(e) => setReportTopK(Number(e.target.value))}
                        min={1}
                        className="form-input"
                      />
                    </div>
                  </div>
                </>
              )}

              <h4 className="text-sm font-bold text-black mb-4 mt-6 lowercase">
                notifications
              </h4>
              <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-4">
                <div className="form-group">
                  <label className="form-label">Email Notification (optional)</label>
                  <input
                    type="email"
                    value={notificationEmail}
                    onChange={(e) => setNotificationEmail(e.target.value)}
                    className="form-input"
                    placeholder="your@email.com"
                  />
                  <p className="text-xs text-gray-400 mt-1">
                    Get notified when your report is ready
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </form>

      {error && (
        <div className="mt-6">
          <div className="p-4 border-2 border-black border-l-4 border-l-red-500 bg-white text-left">
            <strong className="lowercase">error:</strong> {error}
          </div>
          <button
            type="button"
            onClick={() => setError(null)}
            className="btn border-2 border-black bg-white text-black hover:bg-gray-50 mt-2 lowercase"
          >
            try again
          </button>
        </div>
      )}
    </div>
  );
}
