// Brutalist coral shadow style
const brutalShadowSmall = { boxShadow: "1px 1px 0 #F3787A" };

const PRIVACY_ITEMS = [
  {
    title: "no accounts required",
    description: "start generating reports immediately, no sign-up needed",
  },
  {
    title: "query processed server-side",
    description: "your search query is sent to our API for processing with OpenAlex and LLM services",
  },
  {
    title: "reports are shareable",
    description: "generated reports are stored as JSON and can be shared via URL",
  },
];

/**
 * Privacy and transparency section.
 * Brutalist design with simplified list and black checkmarks.
 */
export function PrivacySection() {
  return (
    <section id="privacy" className="py-16 px-4 border-t border-black">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-3xl md:text-4xl font-bold text-gray-900 text-center mb-2 text-shadow-brutal lowercase">
          privacy & transparency
        </h2>
        <p className="text-gray-600 text-center mb-12 lowercase">
          simple and transparent. no tracking, no accounts.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {PRIVACY_ITEMS.map((item) => (
            <div key={item.title} className="flex flex-col items-center text-center">
              {/* Checkmark */}
              <span
                className="flex items-center justify-center w-8 h-8 bg-black text-white mb-4"
                style={brutalShadowSmall}
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={3}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </span>
              <div className="font-medium text-gray-900 mb-1 lowercase">
                {item.title}
              </div>
              <div className="text-sm text-gray-500 lowercase">
                {item.description}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
