/**
 * Proof strip with trust-building metrics.
 */
export function ProofStrip() {
  const metrics = [
    {
      value: "38s",
      label: "Median generation time",
      sublabel: "Last 20 reports",
    },
    {
      value: "240",
      label: "Median papers screened",
      sublabel: "Per report",
    },
    {
      value: "6.1",
      label: "Avg citations per section",
      sublabel: "Traceable sources",
    },
  ];

  return (
    <section className="bg-gray-100 py-8 border-y border-gray-200">
      <div className="max-w-4xl mx-auto px-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {metrics.map((metric) => (
            <div key={metric.label} className="metric-card">
              <div className="text-3xl font-bold text-primary-600 mb-1">
                {metric.value}
              </div>
              <div className="text-sm font-medium text-gray-700">
                {metric.label}
              </div>
              <div className="text-xs text-gray-500 mt-0.5">
                {metric.sublabel}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
