import { useState, type FormEvent } from "react";
import { useNavigate, Link } from "react-router";
import { useMutation } from "@tanstack/react-query";
import { startPipeline, slugifyQuery } from "@/lib/api";
import { DEFAULT_PIPELINE_PARAMS } from "@/lib/config";
import type { PipelineRequest } from "@/lib/types";

const EXAMPLE_QUERIES = [
  "RAG evaluation for medical QA",
  "synthetic data for recommender systems",
  "prompting for structured extraction",
];

/**
 * Hero section with search input, example chips, and CTAs.
 */
export function HeroSection() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);

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
      num_results: DEFAULT_PIPELINE_PARAMS.num_results,
      max_iterations: DEFAULT_PIPELINE_PARAMS.max_iterations,
      max_accepted: DEFAULT_PIPELINE_PARAMS.max_accepted,
      top_n: DEFAULT_PIPELINE_PARAMS.top_n,
      k_factor: DEFAULT_PIPELINE_PARAMS.k_factor,
      pairing: DEFAULT_PIPELINE_PARAMS.pairing,
      early_stop: DEFAULT_PIPELINE_PARAMS.early_stop,
      elo_concurrency: DEFAULT_PIPELINE_PARAMS.elo_concurrency,
      report_top_k: DEFAULT_PIPELINE_PARAMS.report_top_k,
    });
  };

  const handleChipClick = (exampleQuery: string) => {
    setQuery(exampleQuery);
  };

  return (
    <section className="py-16 md:py-24 px-4">
      <div className="max-w-3xl mx-auto text-center">
        {/* Headline */}
        <h1 className="text-4xl md:text-5xl font-bold text-gray-900 leading-tight mb-4">
          From query to survey, with citations
        </h1>

        {/* Subtext */}
        <p className="text-lg md:text-xl text-gray-600 mb-10 max-w-2xl mx-auto">
          Get top papers, research angles, and open problems, with traceable
          sources for every section.
        </p>

        {/* Search Form */}
        <form onSubmit={handleSubmit} className="w-full">
          <div className="flex gap-3 md:flex-col">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="form-input form-input-lg flex-1 shadow-md"
              placeholder="Try: diffusion models for audio generation benchmarks"
              required
            />
            <button
              type="submit"
              disabled={mutation.isPending}
              className="btn btn-primary btn-lg whitespace-nowrap shadow-md"
            >
              {mutation.isPending ? "Starting..." : "Generate report"}
            </button>
          </div>

          {/* Example Chips */}
          <div className="flex flex-wrap justify-center gap-2 mt-4">
            {EXAMPLE_QUERIES.map((example) => (
              <button
                key={example}
                type="button"
                onClick={() => handleChipClick(example)}
                className="chip"
              >
                {example}
              </button>
            ))}
          </div>

          {/* Secondary CTA */}
          <div className="mt-6">
            <Link
              to="/queries"
              className="btn btn-secondary"
            >
              View demo report
            </Link>
          </div>
        </form>

        {/* Error Alert */}
        {error && (
          <div className="mt-6">
            <div className="alert alert-error">
              <strong>Error:</strong> {error}
            </div>
            <button
              type="button"
              onClick={() => setError(null)}
              className="btn btn-secondary mt-2"
            >
              Try Again
            </button>
          </div>
        )}
      </div>
    </section>
  );
}
