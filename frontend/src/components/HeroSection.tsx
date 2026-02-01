import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router";
import { useMutation } from "@tanstack/react-query";
import { startPipeline, slugifyQuery } from "@/lib/api";
import { DEFAULT_PIPELINE_PARAMS } from "@/lib/config";
import type { PipelineRequest } from "@/lib/types";
import { DocumentRain } from "./DocumentRain";

const EXAMPLE_QUERIES = [
  "effect of chatgpt on students",
  "RAG evaluation for medical QA",
  "synthetic data for recommender systems",
  "prompting for structured extraction",
];

// Brutalist coral shadow styles
const brutalShadow = { boxShadow: "3px 3px 0 #F3787A" };
const brutalShadowSmall = { boxShadow: "1px 1px 0 #F3787A" };

/**
 * Hero section with brutalist design.
 * Full viewport height, large shadow text, marquee examples.
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

  const handleExampleClick = (exampleQuery: string) => {
    setQuery(exampleQuery);
  };

  const scrollToNextSection = () => {
    const nextSection = document.getElementById("how-it-works");
    if (nextSection) {
      nextSection.scrollIntoView({ behavior: "smooth" });
    }
  };

  // Double the items for seamless marquee loop
  const marqueeItems = [...EXAMPLE_QUERIES, ...EXAMPLE_QUERIES];

  return (
    <section className="relative h-[calc(100vh-3rem)] flex flex-col px-4 pb-6 overflow-hidden">
      {/* Physics-based document rain background */}
      <DocumentRain maxDocuments={15} spawnInterval={400} scale={1.8} />

      {/* Main content area */}
      <div className="relative z-10 flex-1 flex flex-col justify-center max-w-4xl mx-auto w-full text-center">
        {/* Headline with brutalist shadow */}
        <h1 className="text-3xl sm:text-5xl md:text-7xl lg:text-8xl font-bold text-gray-900 leading-tight mb-4 md:mb-6 text-shadow-brutal lowercase">
          from query to full survey in minutes
        </h1>

        {/* Subtext */}
        <p className="text-sm sm:text-base md:text-lg text-gray-600 mb-8 md:mb-12 lowercase px-2">
          get top papers, research angles and open problems, with traceable sources
        </p>

        {/* Search Form - full width to match marquee */}
        <form onSubmit={handleSubmit} className="w-full">
          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="form-input form-input-lg flex-1 border-2 border-black"
              style={brutalShadow}
              placeholder="try: effect of chatgpt on students (works best on tech papers)"
              required
            />
            <button
              type="submit"
              disabled={mutation.isPending}
              className="btn btn-brutal btn-lg whitespace-nowrap w-full sm:w-auto"
              style={brutalShadow}
            >
              {mutation.isPending ? "..." : "generate"}
            </button>
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

        {/* Marquee Section - right under form */}
        <div className="marquee-container mt-4">
          <div
            className="marquee-track cursor-pointer"
            onClick={(e) => {
              const target = e.target as HTMLElement;
              if (target.classList.contains("marquee-item")) {
                handleExampleClick(target.textContent || "");
              }
            }}
          >
            {marqueeItems.map((item, i) => (
              <span key={`${item}-${i}`} className="flex items-center gap-6">
                <span className="marquee-item hover:text-gray-600 transition-colors lowercase">
                  {item}
                </span>
                <span
                  className="w-3 h-3 rounded-full bg-black shrink-0"
                  style={brutalShadowSmall}
                />
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Scroll Down Triangle - at bottom of viewport */}
      <button
        onClick={scrollToNextSection}
        className="relative z-10 mx-auto hover:translate-y-1 transition-transform"
        aria-label="Scroll to next section"
      >
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="black"
          className="w-6 h-6"
        >
          <polygon points="12,20 2,8 22,8" />
        </svg>
      </button>
    </section>
  );
}
