/**
 * Privacy and transparency section.
 */
export function PrivacySection() {
  return (
    <section id="privacy" className="py-16 px-4">
      <div className="max-w-2xl mx-auto text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          Privacy & Transparency
        </h2>
        <p className="text-gray-600 mb-6">
          PaperNavigator is designed to be simple and transparent. We don't track
          you, and we don't require an account.
        </p>

        <div className="bg-white rounded-lg border border-gray-200 p-6 text-left">
          <ul className="space-y-4">
            <li className="flex items-start gap-3">
              <span className="flex items-center justify-center w-6 h-6 bg-green-100 text-green-600 rounded-full shrink-0 mt-0.5">
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </span>
              <div>
                <div className="font-medium text-gray-900">No accounts required</div>
                <div className="text-sm text-gray-500">
                  Start generating reports immediately, no sign-up needed
                </div>
              </div>
            </li>
            <li className="flex items-start gap-3">
              <span className="flex items-center justify-center w-6 h-6 bg-green-100 text-green-600 rounded-full shrink-0 mt-0.5">
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </span>
              <div>
                <div className="font-medium text-gray-900">Query processed server-side</div>
                <div className="text-sm text-gray-500">
                  Your search query is sent to our API for processing with OpenAlex and LLM services
                </div>
              </div>
            </li>
            <li className="flex items-start gap-3">
              <span className="flex items-center justify-center w-6 h-6 bg-green-100 text-green-600 rounded-full shrink-0 mt-0.5">
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </span>
              <div>
                <div className="font-medium text-gray-900">Reports are shareable</div>
                <div className="text-sm text-gray-500">
                  Generated reports are stored as JSON and can be shared via URL
                </div>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </section>
  );
}
