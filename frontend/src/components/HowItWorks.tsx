import { useState, useEffect } from "react";

interface Step {
  id: string;
  number: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  details: string[];
}

const STEPS: Step[] = [
  {
    id: "search",
    number: "01",
    title: "search",
    description: "find relevant papers through semantic search and citation expansion",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6">
        <circle cx="11" cy="11" r="8" />
        <path d="m21 21-4.35-4.35" />
      </svg>
    ),
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
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6">
        <path d="M12 20V10" />
        <path d="M18 20V4" />
        <path d="M6 20v-4" />
      </svg>
    ),
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
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14,2 14,8 20,8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
        <line x1="10" y1="9" x2="8" y2="9" />
      </svg>
    ),
    details: [
      "LLM synthesizes findings from top-ranked papers",
      "sections: introduction, current research, open problems, conclusion",
      "every claim includes inline citations to source papers",
      "JSON export available for programmatic access",
    ],
  },
];

/**
 * How it works section with vertical timeline and animated steps.
 * Brutalist design with staggered entrance animations.
 */
export function HowItWorks() {
  const [expandedStep, setExpandedStep] = useState<string | null>(null);
  const [visibleSteps, setVisibleSteps] = useState<Set<string>>(new Set());

  useEffect(() => {
    // Staggered animation on mount
    STEPS.forEach((step, index) => {
      setTimeout(() => {
        setVisibleSteps((prev) => new Set([...prev, step.id]));
      }, 200 + index * 150);
    });
  }, []);

  const toggleStep = (stepId: string) => {
    setExpandedStep(expandedStep === stepId ? null : stepId);
  };

  return (
    <section id="how-it-works" className="py-20 px-4 overflow-hidden">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-bold text-gray-900 mb-3 text-shadow-brutal lowercase">
            how it works
          </h2>
          <p className="text-gray-600 lowercase text-lg">
            three steps from query to comprehensive literature review
          </p>
        </div>

        {/* Vertical Timeline */}
        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-8 md:left-12 top-0 bottom-0 w-0.5 bg-black" />

          {/* Steps */}
          <div className="space-y-8">
            {STEPS.map((step, index) => (
              <div
                key={step.id}
                className={`relative pl-20 md:pl-28 transition-all duration-700 ease-out ${
                  visibleSteps.has(step.id)
                    ? "opacity-100 translate-x-0"
                    : "opacity-0 -translate-x-8"
                }`}
              >
                {/* Timeline node */}
                <div className="absolute left-4 md:left-8 top-6 flex items-center justify-center">
                  <div
                    className={`w-8 h-8 md:w-9 md:h-9 bg-white border-2 border-black flex items-center justify-center z-10 transition-all duration-500 ${
                      visibleSteps.has(step.id) ? "scale-100" : "scale-0"
                    }`}
                    style={{
                      boxShadow: "2px 2px 0 #F3787A",
                      transitionDelay: `${index * 150 + 100}ms`,
                    }}
                  >
                    <span className="text-xs font-bold">{step.number}</span>
                  </div>
                  {/* Pulse ring animation */}
                  <div
                    className={`absolute w-8 h-8 md:w-9 md:h-9 border-2 border-black animate-ping-slow opacity-30 ${
                      visibleSteps.has(step.id) ? "block" : "hidden"
                    }`}
                    style={{ animationDelay: `${index * 200}ms` }}
                  />
                </div>

                {/* Step Card */}
                <div
                  className="bg-white border-2 border-black transition-all duration-300 hover:-translate-y-1"
                  style={{ boxShadow: "4px 4px 0 #F3787A" }}
                >
                  {/* Card Header */}
                  <div className="p-6 pb-4">
                    <div className="flex items-start gap-4">
                      {/* Icon */}
                      <div
                        className="w-12 h-12 bg-black text-white flex items-center justify-center shrink-0"
                        style={{ boxShadow: "2px 2px 0 #F3787A" }}
                      >
                        {step.icon}
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <h3 className="text-xl md:text-2xl font-bold text-gray-900 lowercase mb-1">
                          {step.title}
                        </h3>
                        <p className="text-gray-600 lowercase leading-relaxed">
                          {step.description}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Expandable Details */}
                  <div className="border-t-2 border-black">
                    <button
                      type="button"
                      onClick={() => toggleStep(step.id)}
                      className="flex items-center justify-between w-full px-6 py-3 text-sm font-medium bg-gray-50 hover:bg-gray-100 transition-colors lowercase group"
                      aria-expanded={expandedStep === step.id}
                    >
                      <span className="flex items-center gap-2">
                        <span className="w-1.5 h-1.5 bg-black rounded-full group-hover:scale-125 transition-transform" />
                        {expandedStep === step.id ? "hide details" : "see details"}
                      </span>
                      <svg
                        className={`w-4 h-4 transition-transform duration-300 ${
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

                    {/* Details Panel */}
                    <div
                      className={`overflow-hidden transition-all duration-300 ease-out ${
                        expandedStep === step.id ? "max-h-96" : "max-h-0"
                      }`}
                    >
                      <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
                        <ul className="space-y-3">
                          {step.details.map((detail, detailIndex) => (
                            <li
                              key={detail}
                              className="flex items-start gap-3 text-sm text-gray-600 lowercase"
                              style={{
                                animationDelay: `${detailIndex * 50}ms`,
                              }}
                            >
                              <span className="w-5 h-5 bg-black text-white text-xs flex items-center justify-center shrink-0 mt-0.5">
                                {detailIndex + 1}
                              </span>
                              <span className="leading-relaxed">{detail}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* End marker */}
          <div className="absolute left-4 md:left-8 -bottom-4 flex items-center justify-center">
            <div
              className="w-8 h-8 md:w-9 md:h-9 bg-black border-2 border-black flex items-center justify-center z-10"
              style={{ boxShadow: "2px 2px 0 #F3787A" }}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" className="w-4 h-4">
                <polyline points="20,6 9,17 4,12" />
              </svg>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
