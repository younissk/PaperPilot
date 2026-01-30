import { useState } from "react";

// Brutalist coral shadow style
const brutalShadow = { boxShadow: "3px 3px 0 #F3787A" };
const brutalShadowSmall = { boxShadow: "1px 1px 0 #F3787A" };

/**
 * Static preview card showing what a report looks like.
 * Brutalist design with black borders and coral shadows.
 */
export function OutputPreview() {
  const [activeTooltip, setActiveTooltip] = useState<string | null>(null);

  const topPapers = [
    {
      id: "1",
      title: "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
      rank: 1,
      reason: "Foundational RAG paper with 2,400+ citations. Introduces the core architecture.",
      sources: 12,
    },
    {
      id: "2",
      title: "Self-RAG: Learning to Retrieve, Generate, and Critique",
      rank: 2,
      reason: "State-of-the-art self-reflective RAG approach. High relevance to evaluation.",
      sources: 8,
    },
    {
      id: "3",
      title: "RAGAS: Automated Evaluation of Retrieval Augmented Generation",
      rank: 3,
      reason: "Directly addresses RAG evaluation metrics. Core to the query topic.",
      sources: 6,
    },
  ];

  const researchAngles = [
    "retrieval quality metrics",
    "generation faithfulness",
    "end-to-end evaluation frameworks",
  ];

  const painPoints = [
    "lack of standardized benchmarks for domain-specific RAG",
    "difficulty measuring hallucination rates accurately",
  ];

  return (
    <section className="py-16 px-4">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-3xl md:text-4xl font-bold text-gray-900 text-center mb-2 text-shadow-brutal lowercase">
          what you'll get
        </h2>
        <p className="text-gray-600 text-center mb-8 lowercase">
          a structured research report with ranked papers and cited insights
        </p>

        <div
          className="bg-white border-2 border-black p-6"
          style={brutalShadow}
        >
          {/* Header */}
          <div className="bg-black text-white p-4 -m-6 mb-6">
            <div className="text-sm opacity-70 lowercase">sample report</div>
            <div className="font-semibold">RAG evaluation for medical QA</div>
          </div>

          {/* Top Papers */}
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-3">
              top papers
            </h3>
            <div className="space-y-3">
              {topPapers.map((paper) => (
                <div
                  key={paper.id}
                  className="flex items-start gap-3 p-3 border border-black relative group"
                >
                  <span
                    className="flex items-center justify-center w-6 h-6 text-xs font-bold bg-white border-2 border-black shrink-0"
                    style={brutalShadowSmall}
                  >
                    {paper.rank}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-gray-900 truncate">
                      {paper.title}
                    </div>
                    <button
                      type="button"
                      className="text-xs text-gray-500 hover:text-black mt-1 cursor-help lowercase"
                      onMouseEnter={() => setActiveTooltip(paper.id)}
                      onMouseLeave={() => setActiveTooltip(null)}
                    >
                      why included?
                    </button>
                    {activeTooltip === paper.id && (
                      <div className="absolute left-0 right-0 top-full mt-1 z-10 p-3 bg-black text-white text-xs border-2 border-black">
                        <div className="mb-1">{paper.reason}</div>
                        <div className="text-gray-400">
                          Referenced in {paper.sources} sources
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Research Angles */}
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-3">
              research angles
            </h3>
            <div className="flex flex-wrap gap-2">
              {researchAngles.map((angle) => (
                <span
                  key={angle}
                  className="px-3 py-1 text-sm border border-black bg-white lowercase"
                >
                  {angle}
                </span>
              ))}
            </div>
          </div>

          {/* Pain Points */}
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-3">
              open problems
            </h3>
            <ul className="space-y-2">
              {painPoints.map((point) => (
                <li
                  key={point}
                  className="text-sm text-gray-700 flex items-start gap-2 lowercase"
                >
                  <span
                    className="w-2 h-2 bg-black rounded-full mt-1.5 shrink-0"
                    style={brutalShadowSmall}
                  />
                  {point}
                </li>
              ))}
            </ul>
          </div>

          {/* References */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-3">
              references
            </h3>
            <div className="flex flex-wrap gap-2">
              {["W2963403868", "W3045442180", "W4388726703"].map((ref) => (
                <a
                  key={ref}
                  href={`https://openalex.org/${ref}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs px-2 py-1 border border-black bg-white hover:bg-gray-100 no-underline text-black"
                >
                  [{ref}]
                </a>
              ))}
              <span className="text-xs text-gray-500 self-center ml-1 lowercase">
                +24 more
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
