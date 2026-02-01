// Brutalist shadow styles
const brutalShadow = { boxShadow: "3px 3px 0 #F3787A" };

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

/**
 * About section for the home page - brutalist design.
 * Displays features and description of Paper Navigator.
 */
export function AboutSection() {
  return (
    <section className="py-16 px-4">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-3xl md:text-4xl font-bold text-gray-900 text-center mb-2 text-shadow-brutal lowercase">
          about paper navigator
        </h2>
        <p className="text-gray-600 text-center mb-8 lowercase">
          ai-powered academic literature discovery and analysis
        </p>

        <div
          className="bg-white border-2 border-black p-6"
          style={brutalShadow}
        >
          <div className="space-y-4">
            <p className="text-gray-600 lowercase">
              paper navigator helps researchers discover and analyze academic
              papers through intelligent search, ranking, visualization, and
              automated report generation.
            </p>

            <h3 className="text-xl font-bold text-black lowercase mt-6">
              features
            </h3>
            <ul className="list-none p-0 m-0">
              {FEATURES.map((feature) => (
                <li
                  key={feature.title}
                  className="py-4 border-b border-black last:border-b-0"
                >
                  <strong className="text-black">{feature.title}</strong>
                  <p className="text-gray-600 text-sm mt-1">
                    {feature.description}
                  </p>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
