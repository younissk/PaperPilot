import { useState } from "react";

// Brutalist coral shadow style
const brutalShadow = { boxShadow: "3px 3px 0 #F3787A" };

interface Step {
  id: string;
  number: string;
  title: string;
  description: string;
  details: string[];
}

const STEPS: Step[] = [
  {
    id: "search",
    number: "01",
    title: "search",
    description: "find relevant papers through semantic search and citation expansion",
    details: [
      "query OpenAlex for initial seed papers using semantic matching",
      "snowball sampling: expand via citations and references",
      "iteratively grow the candidate pool until saturation",
      "filter by relevance threshold and publication date",
    ],
  },
  {
    id: "rank",
    number: "02",
    title: "rank",
    description: "AI-powered pairwise comparisons to surface the best papers",
    details: [
      "ELO tournament: papers compete head-to-head via LLM judgment",
      "swiss pairing for efficient comparison scheduling",
      "early stopping when rankings stabilize",
      "concurrent comparisons for faster processing",
    ],
  },
  {
    id: "report",
    number: "03",
    title: "report",
    description: "generate a structured survey with inline citations",
    details: [
      "LLM synthesizes findings from top-ranked papers",
      "sections: introduction, current research, open problems, conclusion",
      "every claim includes inline citations to source papers",
      "JSON export available for programmatic access",
    ],
  },
];

/**
 * How it works section with 3 steps and expandable details.
 * Brutalist design with numbered steps and black accents.
 */
export function HowItWorks() {
  const [expandedStep, setExpandedStep] = useState<string | null>(null);

  const toggleStep = (stepId: string) => {
    setExpandedStep(expandedStep === stepId ? null : stepId);
  };

  return (
    <section id="how-it-works" className="py-16 px-4">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-3xl md:text-4xl font-bold text-gray-900 text-center mb-2 text-shadow-brutal lowercase">
          how it works
        </h2>
        <p className="text-gray-600 text-center mb-12 lowercase">
          three steps from query to comprehensive literature review
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {STEPS.map((step, index) => (
            <div key={step.id} className="relative">
              {/* Connector line (hidden on mobile, shown between cards on desktop) */}
              {index < STEPS.length - 1 && (
                <div className="hidden md:block absolute top-10 left-full w-6 h-0.5 bg-black z-0" />
              )}

              <div
                className="bg-white border-2 border-black p-6 h-full flex flex-col"
                style={brutalShadow}
              >
                {/* Step Number */}
                <div className="text-5xl font-bold text-shadow-brutal mb-4 text-center">
                  {step.number}
                </div>

                {/* Title & Description */}
                <h3 className="text-lg font-semibold text-gray-900 text-center mb-2 lowercase">
                  {step.title}
                </h3>
                <p className="text-sm text-gray-600 text-center mb-4 flex-1 lowercase">
                  {step.description}
                </p>

                {/* Accordion Toggle */}
                <button
                  type="button"
                  onClick={() => toggleStep(step.id)}
                  className="flex items-center justify-center gap-2 w-full px-3 py-2 text-sm font-medium bg-black text-white border-2 border-black hover:bg-gray-900 transition-colors lowercase"
                  aria-expanded={expandedStep === step.id}
                >
                  {expandedStep === step.id ? "hide details" : "see details"}
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
                  <div className="mt-4 pt-4 border-t border-black">
                    <ul className="space-y-2">
                      {step.details.map((detail) => (
                        <li
                          key={detail}
                          className="text-sm text-gray-600 flex items-start gap-2 lowercase"
                        >
                          <span className="w-1.5 h-1.5 bg-black rounded-full mt-1.5 shrink-0" />
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
