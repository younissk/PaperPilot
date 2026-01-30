// Brutalist coral shadow style
const brutalShadow = { boxShadow: "3px 3px 0 #F3787A" };

/**
 * Proof strip with trust-building metrics.
 * Brutalist design with black borders and coral shadows.
 */
export function ProofStrip() {
  const metrics = [
    {
      value: "38s",
      label: "median generation time",
      sublabel: "last 20 reports",
    },
    {
      value: "240",
      label: "median papers screened",
      sublabel: "per report",
    },
    {
      value: "6.1",
      label: "avg citations per section",
      sublabel: "traceable sources",
    },
  ];

  return (
    <section className="py-8 border-y border-black">
      <div className="max-w-4xl mx-auto px-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {metrics.map((metric) => (
            <div
              key={metric.label}
              className="bg-white border-2 border-black p-6 text-center"
              style={brutalShadow}
            >
              <div className="text-4xl font-bold text-shadow-brutal mb-2">
                {metric.value}
              </div>
              <div className="text-sm font-medium text-gray-900 lowercase">
                {metric.label}
              </div>
              <div className="text-xs text-gray-500 mt-1 lowercase">
                {metric.sublabel}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
