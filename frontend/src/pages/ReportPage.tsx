import { useEffect } from "react";
import { useParams, useSearchParams, useNavigate, Link } from "react-router";
import { SEO, PaperCard, ProgressIndicator } from "@/components";
import { useAllResults, usePipelineStatus } from "@/hooks";

// Brutalist shadow styles
const brutalShadow = { boxShadow: "3px 3px 0 #F3787A" };

/**
 * Helper function to format citations in text.
 * Converts [W123456789] to clickable OpenAlex links.
 */
function formatCitations(text: string): string {
  return text.replace(/\[([A-Za-z0-9_:-]+)\]/g, (_match, paperId) => {
    const isOpenAlex = paperId.startsWith("W");
    const url = isOpenAlex
      ? `https://openalex.org/${paperId}`
      : `https://openalex.org/search?q=${encodeURIComponent(paperId)}`;
    return `<a href="${url}" target="_blank" rel="noopener" class="citation" title="View paper">[${paperId}]</a>`;
  });
}

/**
 * Report page component - brutalist design.
 */
export default function ReportPage() {
  const { queryId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const jobId = searchParams.get("job");

  const { results, metadata, isLoading, error, notFound } = useAllResults(queryId);
  const reportData = results?.report ?? null;
  const papers = results?.snowball?.papers ?? [];

  // Poll pipeline status if job is provided
  const { data: pipelineStatus } = usePipelineStatus(jobId);

  // Redirect when pipeline completes
  useEffect(() => {
    if (pipelineStatus?.status === "completed" && jobId) {
      // Remove job parameter and reload
      navigate(`/report/${queryId}`, { replace: true });
    }
  }, [pipelineStatus?.status, jobId, queryId, navigate]);

  // Display title
  const queryTitle = reportData?.query || queryId?.replace(/_/g, " ") || "Research Report";
  const pageTitle = `Research Report: ${queryTitle}`;

  // Meta description
  const introText = reportData?.introduction || "";
  const metaDescription =
    introText.length > 160
      ? introText.substring(0, 157) + "..."
      : introText || `Research report on ${queryTitle}`;

  // Canonical URL
  const canonicalUrl = `${window.location.origin}/report/${queryId}`;

  // JSON-LD structured data
  const jsonLd = reportData
    ? {
        "@context": "https://schema.org",
        "@type": "ScholarlyArticle",
        headline: pageTitle,
        description: metaDescription,
        author: {
          "@type": "Organization",
          name: "Paper Navigator",
        },
        datePublished: metadata?.report_generated_at || reportData.generated_at,
        dateModified: metadata?.last_updated || reportData.generated_at,
        mainEntityOfPage: {
          "@type": "WebPage",
          "@id": canonicalUrl,
        },
        about: {
          "@type": "Thing",
          name: queryTitle,
        },
        numberOfPages: reportData.total_papers_used,
      }
    : undefined;

  // 404 state
  if (notFound && !jobId) {
    return (
      <>
        <SEO title="Report Not Found" noindex />
        <div className="text-center py-12 px-4">
          <h1 className="text-3xl font-bold text-black text-shadow-brutal lowercase">
            report not found
          </h1>
          <p className="text-gray-600 mt-2 lowercase">
            the report for "{queryId?.replace(/_/g, " ")}" does not exist.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 mt-6 justify-center">
            <Link
              to="/"
              className="btn btn-brutal lowercase"
              style={brutalShadow}
            >
              create new report
            </Link>
            <Link
              to="/queries"
              className="btn border-2 border-black bg-white text-black hover:bg-gray-50 lowercase"
            >
              view existing reports
            </Link>
          </div>
        </div>
      </>
    );
  }

  // Error state
  if (error) {
    return (
      <>
        <SEO title="Error" noindex />
        <div className="container container-lg py-12 px-4">
          <div className="p-4 border-2 border-black border-l-4 border-l-red-500 bg-white">
            <strong className="lowercase">error loading report:</strong> {error.message}
          </div>
        </div>
      </>
    );
  }

  // Loading state (no job, just fetching)
  if (isLoading && !jobId) {
    return (
      <>
        <SEO title="Loading..." noindex />
        <div className="flex justify-center items-center min-h-[400px]">
          <div className="text-center">
            <div className="spinner mx-auto mb-4" />
            <p className="text-gray-600 lowercase">loading report...</p>
          </div>
        </div>
      </>
    );
  }

  // Generating state (has job, polling)
  if (!reportData && jobId && pipelineStatus) {
    // Check for pipeline failure
    if (pipelineStatus.status === "failed") {
      return (
        <>
          <SEO title="Generation Failed" noindex />
          <div className="container container-lg py-12 px-4">
            <div className="p-4 border-2 border-black border-l-4 border-l-red-500 bg-white">
              <strong className="lowercase">report generation failed:</strong>{" "}
              {pipelineStatus.error || "unknown error"}
            </div>
            {pipelineStatus.alerts && pipelineStatus.alerts.length > 0 && (
              <div className="stack stack-sm mt-4">
                {pipelineStatus.alerts.slice(-3).map((alert, idx) => (
                  <div
                    key={`${alert.ts ?? "alert"}-${idx}`}
                    className={`p-3 border-2 border-black bg-white ${
                      alert.level === "error" ? "border-l-4 border-l-red-500" : ""
                    }`}
                  >
                    <strong className="lowercase">{alert.level || "warning"}:</strong>{" "}
                    {alert.message}
                  </div>
                ))}
              </div>
            )}
            <Link
              to="/"
              className="btn border-2 border-black bg-white text-black hover:bg-gray-50 mt-4 lowercase inline-block"
            >
              try again
            </Link>
          </div>
        </>
      );
    }

    return (
      <>
        <SEO title="Generating Report..." noindex />
        <ProgressIndicator
          status={pipelineStatus}
          queryTitle={queryId?.replace(/_/g, " ")}
        />
      </>
    );
  }

  // Report display
  if (!reportData) {
    return null;
  }

  return (
    <>
      <SEO
        title={pageTitle}
        description={metaDescription}
        canonical={canonicalUrl}
        jsonLd={jsonLd}
      />

      <div className="container container-lg py-12 px-4">
        <article className="max-w-4xl mx-auto">
          {/* Header */}
          <header
            className="bg-black text-white p-8 mb-8 border-2 border-black"
            style={brutalShadow}
          >
            <h1 className="text-white text-2xl md:text-3xl mb-4 lowercase">
              research report: <span>{reportData.query}</span>
            </h1>
            <div className="flex gap-2 flex-wrap">
              <span
                className="inline-flex items-center px-3 py-1 text-sm border border-white text-white lowercase"
              >
                {new Date(reportData.generated_at).toLocaleDateString()}
              </span>
              <span
                className="inline-flex items-center px-3 py-1 text-sm border border-white text-white lowercase"
              >
                {reportData.total_papers_used} papers used
              </span>
            </div>
          </header>

          {/* Table of Contents */}
          <nav
            className="bg-white p-6 border-2 border-black mb-8"
            style={brutalShadow}
          >
            <h3 className="text-base font-bold text-black mb-4 lowercase">table of contents</h3>
            <ul className="list-none p-0 m-0">
              <li className="mb-2">
                <a href="#introduction" className="text-gray-700 hover:text-black no-underline hover:underline lowercase">
                  introduction
                </a>
              </li>
              <li className="mb-2">
                <a href="#current-research" className="text-gray-700 hover:text-black no-underline hover:underline lowercase">
                  current research
                </a>
                {reportData.current_research.length > 0 && (
                  <ul className="list-none p-0 ml-6 mt-1">
                    {reportData.current_research.map((item, idx) => (
                      <li key={idx} className="text-sm mb-1">
                        <a href={`#research-${idx}`} className="text-gray-600 hover:text-black no-underline hover:underline">
                          {item.title}
                        </a>
                      </li>
                    ))}
                  </ul>
                )}
              </li>
              {reportData.open_problems.length > 0 && (
                <li className="mb-2">
                  <a href="#open-problems" className="text-gray-700 hover:text-black no-underline hover:underline lowercase">
                    open problems
                  </a>
                </li>
              )}
              <li className="mb-2">
                <a href="#conclusion" className="text-gray-700 hover:text-black no-underline hover:underline lowercase">
                  conclusion
                </a>
              </li>
              <li>
                <a href="#sources" className="text-gray-700 hover:text-black no-underline hover:underline lowercase">
                  sources
                </a>
              </li>
            </ul>
          </nav>

          {/* Introduction */}
          <ReportSection id="introduction" title="introduction">
            <p
              className="leading-relaxed"
              dangerouslySetInnerHTML={{ __html: formatCitations(reportData.introduction) }}
            />
          </ReportSection>

          {/* Current Research */}
          <ReportSection id="current-research" title="current research">
            {reportData.current_research.map((item, idx) => (
              <div
                key={idx}
                id={`research-${idx}`}
                className="mb-8 pb-6 border-b border-black last:mb-0 last:pb-0 last:border-b-0"
              >
                <h3 className="text-black font-bold mb-4">{item.title}</h3>
                <p
                  className="leading-relaxed"
                  dangerouslySetInnerHTML={{ __html: formatCitations(item.summary) }}
                />
                {item.paper_ids.length > 0 && (
                  <div className="mt-4 p-4 border border-black bg-white text-sm">
                    <strong className="lowercase">referenced papers:</strong>
                    <ul className="list-none p-0 mt-2">
                      {item.paper_ids.map((paperId) => {
                        const card = reportData.paper_cards.find((c) => c.id === paperId);
                        const isOpenAlex = paperId.startsWith("W");
                        const url = isOpenAlex
                          ? `https://openalex.org/${paperId}`
                          : `https://openalex.org/search?q=${encodeURIComponent(paperId)}`;
                        return (
                          <li key={paperId} className="mb-1 flex items-baseline gap-2">
                            <a
                              href={url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="citation"
                            >
                              [{paperId}]
                            </a>
                            {card && <span className="text-gray-600">{card.title}</span>}
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </ReportSection>

          {/* Open Problems */}
          {reportData.open_problems.length > 0 && (
            <ReportSection id="open-problems" title="open problems">
              {reportData.open_problems.map((problem, idx) => (
                <div
                  key={idx}
                  className="mb-6 p-6 bg-white border-2 border-black border-l-4"
                  style={{ borderLeftColor: "#F3787A" }}
                >
                  <h3 className="text-black font-bold mb-4">{problem.title}</h3>
                  <p
                    className="leading-relaxed"
                    dangerouslySetInnerHTML={{ __html: formatCitations(problem.text) }}
                  />
                  {problem.paper_ids.length > 0 && (
                    <div className="mt-4 flex gap-1 flex-wrap items-center">
                      <strong className="lowercase">sources:</strong>
                      {problem.paper_ids.map((paperId) => {
                        const isOpenAlex = paperId.startsWith("W");
                        const url = isOpenAlex
                          ? `https://openalex.org/${paperId}`
                          : `https://openalex.org/search?q=${encodeURIComponent(paperId)}`;
                        return (
                          <a
                            key={paperId}
                            href={url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="citation"
                          >
                            [{paperId}]
                          </a>
                        );
                      })}
                    </div>
                  )}
                </div>
              ))}
            </ReportSection>
          )}

          {/* Conclusion */}
          <ReportSection id="conclusion" title="conclusion">
            <p
              className="leading-relaxed"
              dangerouslySetInnerHTML={{ __html: formatCitations(reportData.conclusion) }}
            />
          </ReportSection>

          {/* Sources */}
          <ReportSection id="sources" title="sources">
            <p className="text-gray-600 text-sm mb-6 lowercase">
              {papers.length} papers were analyzed for this report. click on any paper
              to view it on openalex.
            </p>

            {reportData.paper_cards.length > 0 && (
              <div className="grid gap-4">
                {reportData.paper_cards.map((card) => (
                  <PaperCard key={card.id} card={card} />
                ))}
              </div>
            )}
          </ReportSection>
        </article>
      </div>
    </>
  );
}

/**
 * Report section wrapper component - brutalist design.
 */
function ReportSection({
  id,
  title,
  children,
}: {
  id: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section
      id={id}
      className="bg-white p-8 mb-6 border-2 border-black"
      style={brutalShadow}
    >
      <h2 className="text-black font-bold text-xl mb-6 pb-2 border-b-2 border-black lowercase">
        {title}
      </h2>
      {children}
    </section>
  );
}
