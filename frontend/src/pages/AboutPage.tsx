import { SEO } from "@/components";

const FEATURES = [
  {
    title: "Semantic Search with Snowball Sampling",
    description:
      "Discover relevant papers by iteratively expanding your search based on citations and references.",
  },
  {
    title: "ELO-based Paper Ranking",
    description:
      "AI-powered pairwise comparisons to rank papers by relevance to your research question.",
  },
  {
    title: "Citation Graph Visualization",
    description:
      "Explore relationships between papers through interactive citation network graphs.",
  },
  {
    title: "Timeline Analysis",
    description: "Visualize the evolution of research topics over time.",
  },
  {
    title: "Paper Clustering",
    description:
      "Automatically group papers by topic using advanced embedding techniques.",
  },
  {
    title: "Automated Research Reports",
    description:
      "Generate comprehensive literature review reports with citations and insights.",
  },
];

const STEPS = [
  {
    number: 1,
    title: "Enter Your Query",
    description: "Describe your research topic or question.",
  },
  {
    number: 2,
    title: "Snowball Search",
    description: "We find relevant papers and expand via citations/references.",
  },
  {
    number: 3,
    title: "AI Ranking",
    description: "Papers are compared pairwise and ranked by relevance.",
  },
  {
    number: 4,
    title: "Report Generation",
    description: "A comprehensive report summarizes key findings and themes.",
  },
];

/**
 * About page with feature list and how it works.
 */
export default function AboutPage() {
  return (
    <>
      <SEO
        title="About"
        description="Learn about Paper Navigator - AI-powered academic literature discovery and analysis."
      />

      <div className="container container-lg">
        <div className="stack stack-xl">
          <h1>About Paper Navigator</h1>

          <div className="card">
            <div className="stack stack-md">
              <p className="text-lg font-bold">
                AI-powered academic literature discovery
              </p>
              <p>
                Paper Navigator helps researchers discover and analyze academic papers
                through intelligent search, ranking, visualization, and automated
                report generation.
              </p>

              <h3>Features</h3>
              <ul className="list-none p-0">
                {FEATURES.map((feature) => (
                  <li
                    key={feature.title}
                    className="py-4 border-b border-gray-100 last:border-b-0"
                  >
                    <strong>{feature.title}</strong>
                    <p className="text-gray-500 text-sm">{feature.description}</p>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="card">
            <h3>How It Works</h3>
            <div className="stack stack-md">
              {STEPS.map((step) => (
                <div key={step.number} className="flex items-start gap-4">
                  <span className="flex items-center justify-center w-8 h-8 bg-primary-600 text-white rounded-full font-semibold shrink-0">
                    {step.number}
                  </span>
                  <div>
                    <strong>{step.title}</strong>
                    <p className="text-gray-500 text-sm">{step.description}</p>
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
