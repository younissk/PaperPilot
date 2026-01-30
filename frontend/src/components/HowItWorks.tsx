import { useState } from "react";

interface Step {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  details: string[];
}

const STEPS: Step[] = [
  {
    id: "search",
    title: "Search",
    description: "Find relevant papers through semantic search and citation expansion",
    icon: (
      <svg
        className="w-8 h-8"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
        />
      </svg>
    ),
    details: [
      "Query OpenAlex for initial seed papers using semantic matching",
      "Snowball sampling: expand via citations and references",
      "Iteratively grow the candidate pool until saturation",
      "Filter by relevance threshold and publication date",
    ],
  },
  {
    id: "rank",
    title: "Rank",
    description: "AI-powered pairwise comparisons to surface the best papers",
    icon: (
      <svg
        className="w-8 h-8"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
        />
      </svg>
    ),
    details: [
      "ELO tournament: papers compete head-to-head via LLM judgment",
      "Swiss pairing for efficient comparison scheduling",
      "Early stopping when rankings stabilize",
      "Concurrent comparisons for faster processing",
    ],
  },
  {
    id: "report",
    title: "Report",
    description: "Generate a structured survey with inline citations",
    icon: (
      <svg
        className="w-8 h-8"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
      </svg>
    ),
    details: [
      "LLM synthesizes findings from top-ranked papers",
      "Sections: Introduction, Current Research, Open Problems, Conclusion",
      "Every claim includes inline citations to source papers",
      "JSON export available for programmatic access",
    ],
  },
];

/**
 * How it works section with 3 steps and expandable details.
 */
export function HowItWorks() {
  const [expandedStep, setExpandedStep] = useState<string | null>(null);

  const toggleStep = (stepId: string) => {
    setExpandedStep(expandedStep === stepId ? null : stepId);
  };

  return (
    <section id="how-it-works" className="py-16 px-4 bg-gray-50">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold text-gray-900 text-center mb-2">
          How it works
        </h2>
        <p className="text-gray-600 text-center mb-12">
          Three steps from query to comprehensive literature review
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {STEPS.map((step, index) => (
            <div key={step.id} className="relative">
              {/* Connector line (hidden on mobile, shown between cards on desktop) */}
              {index < STEPS.length - 1 && (
                <div className="hidden md:block absolute top-12 left-full w-6 h-0.5 bg-gray-300 -translate-y-1/2 z-0" />
              )}

              <div className="bg-white rounded-lg border border-gray-200 p-6 h-full flex flex-col">
                {/* Icon */}
                <div className="w-16 h-16 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center mb-4 mx-auto">
                  {step.icon}
                </div>

                {/* Title & Description */}
                <h3 className="text-lg font-semibold text-gray-900 text-center mb-2">
                  {step.title}
                </h3>
                <p className="text-sm text-gray-600 text-center mb-4 flex-1">
                  {step.description}
                </p>

                {/* Accordion Toggle */}
                <button
                  type="button"
                  onClick={() => toggleStep(step.id)}
                  className="accordion-toggle"
                  aria-expanded={expandedStep === step.id}
                >
                  {expandedStep === step.id ? "Hide details" : "See details"}
                  <svg
                    className={`w-4 h-4 transition-transform ${
                      expandedStep === step.id ? "rotate-180" : ""
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </button>

                {/* Accordion Content */}
                {expandedStep === step.id && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <ul className="space-y-2">
                      {step.details.map((detail) => (
                        <li
                          key={detail}
                          className="text-sm text-gray-600 flex items-start gap-2"
                        >
                          <span className="text-primary-500 mt-0.5">•</span>
                          {detail}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
