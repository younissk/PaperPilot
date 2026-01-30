import { useState } from "react";

/**
 * Static preview card showing what a report looks like.
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
    "Retrieval quality metrics",
    "Generation faithfulness",
    "End-to-end evaluation frameworks",
  ];

  const painPoints = [
    "Lack of standardized benchmarks for domain-specific RAG",
    "Difficulty measuring hallucination rates accurately",
  ];

  const getMedalClass = (rank: number) => {
    switch (rank) {
      case 1:
        return "bg-amber-100 text-amber-700 medal-gold";
      case 2:
        return "bg-gray-100 text-gray-600 medal-silver";
      case 3:
        return "bg-orange-100 text-orange-700 medal-bronze";
      default:
        return "bg-gray-100 text-gray-600";
    }
  };

  return (
    <section className="py-16 px-4">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold text-gray-900 text-center mb-2">
          What you'll get
        </h2>
        <p className="text-gray-600 text-center mb-8">
          A structured research report with ranked papers and cited insights
        </p>

        <div className="preview-card">
          {/* Header */}
          <div className="bg-primary-600 text-white p-4 rounded-t-lg -m-6 mb-6">
            <div className="text-sm opacity-80">Sample Report</div>
            <div className="font-semibold">RAG evaluation for medical QA</div>
          </div>

          {/* Top Papers */}
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Top Papers
            </h3>
            <div className="space-y-3">
              {topPapers.map((paper) => (
                <div
                  key={paper.id}
                  className="flex items-start gap-3 p-3 bg-gray-50 rounded-md relative group"
                >
                  <span
                    className={`flex items-center justify-center w-6 h-6 text-xs font-bold rounded-full shrink-0 ${getMedalClass(paper.rank)}`}
                  >
                    {paper.rank}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-gray-900 truncate">
                      {paper.title}
                    </div>
                    <button
                      type="button"
                      className="text-xs text-primary-600 hover:text-primary-700 mt-1 cursor-help"
                      onMouseEnter={() => setActiveTooltip(paper.id)}
                      onMouseLeave={() => setActiveTooltip(null)}
                    >
                      Why included?
                    </button>
                    {activeTooltip === paper.id && (
                      <div className="absolute left-0 right-0 top-full mt-1 z-10 p-3 bg-gray-900 text-white text-xs rounded-md shadow-lg">
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
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Research Angles
            </h3>
            <div className="flex flex-wrap gap-2">
              {researchAngles.map((angle) => (
                <span key={angle} className="badge">
                  {angle}
                </span>
              ))}
            </div>
          </div>

          {/* Pain Points */}
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Open Problems
            </h3>
            <ul className="space-y-2">
              {painPoints.map((point) => (
                <li
                  key={point}
                  className="text-sm text-gray-700 flex items-start gap-2"
                >
                  <span className="text-warning mt-0.5">●</span>
                  {point}
                </li>
              ))}
            </ul>
          </div>

          {/* References */}
          <div>
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
              References
            </h3>
            <div className="flex flex-wrap gap-1">
              {["W2963403868", "W3045442180", "W4388726703"].map((ref) => (
                <a
                  key={ref}
                  href={`https://openalex.org/${ref}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="citation"
                >
                  [{ref}]
                </a>
              ))}
              <span className="text-xs text-gray-400 self-center ml-1">
                +24 more
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
