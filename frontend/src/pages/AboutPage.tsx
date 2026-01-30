import { SEO } from "@/components";

// Brutalist shadow styles
const brutalShadow = { boxShadow: "3px 3px 0 #F3787A" };
const brutalShadowSmall = { boxShadow: "1px 1px 0 #F3787A" };

const FEATURES = [
  {
    title: "semantic search with snowball sampling",
    description:
      "discover relevant papers by iteratively expanding your search based on citations and references.",
  },
  {
    title: "elo-based paper ranking",
    description:
      "ai-powered pairwise comparisons to rank papers by relevance to your research question.",
  },
  {
    title: "citation graph visualization",
    description:
      "explore relationships between papers through interactive citation network graphs.",
  },
  {
    title: "timeline analysis",
    description: "visualize the evolution of research topics over time.",
  },
  {
    title: "paper clustering",
    description:
      "automatically group papers by topic using advanced embedding techniques.",
  },
  {
    title: "automated research reports",
    description:
      "generate comprehensive literature review reports with citations and insights.",
  },
];

const STEPS = [
  {
    number: "01",
    title: "enter your query",
    description: "describe your research topic or question.",
  },
  {
    number: "02",
    title: "snowball search",
    description: "we find relevant papers and expand via citations/references.",
  },
  {
    number: "03",
    title: "ai ranking",
    description: "papers are compared pairwise and ranked by relevance.",
  },
  {
    number: "04",
    title: "report generation",
    description: "a comprehensive report summarizes key findings and themes.",
  },
];

/**
 * About page with feature list and how it works - brutalist design.
 */
export default function AboutPage() {
  return (
    <>
      <SEO
        title="About"
        description="Learn about Paper Navigator - AI-powered academic literature discovery and analysis."
      />

      <div className="container container-lg py-12 px-4">
        <div className="stack stack-xl">
          <h1 className="text-3xl md:text-4xl font-bold text-black text-shadow-brutal lowercase">
            about paper navigator
          </h1>

          <div className="bg-white border-2 border-black p-6" style={brutalShadow}>
            <div className="stack stack-md">
              <p className="text-lg font-bold lowercase">
                ai-powered academic literature discovery
              </p>
              <p className="text-gray-600 lowercase">
                paper navigator helps researchers discover and analyze academic papers
                through intelligent search, ranking, visualization, and automated
                report generation.
              </p>

              <h3 className="text-xl font-bold text-black lowercase mt-4">features</h3>
              <ul className="list-none p-0">
                {FEATURES.map((feature) => (
                  <li
                    key={feature.title}
                    className="py-4 border-b border-black last:border-b-0"
                  >
                    <strong className="text-black">{feature.title}</strong>
                    <p className="text-gray-600 text-sm mt-1">{feature.description}</p>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="bg-white border-2 border-black p-6" style={brutalShadow}>
            <h3 className="text-xl font-bold text-black lowercase mb-6">how it works</h3>
            <div className="stack stack-md">
              {STEPS.map((step) => (
                <div key={step.number} className="flex items-start gap-4">
                  <span
                    className="flex items-center justify-center w-10 h-10 bg-black text-white font-bold shrink-0 text-sm"
                    style={brutalShadowSmall}
                  >
                    {step.number}
                  </span>
                  <div>
                    <strong className="text-black">{step.title}</strong>
                    <p className="text-gray-600 text-sm mt-1">{step.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
