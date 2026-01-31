import { Link } from "react-router";

/**
 * Minimal brutalist footer with essential links.
 * Sitewide component rendered in Layout.
 */
export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t border-black py-8 px-4">
      <div className="max-w-4xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-4">
        {/* Brand */}
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1 text-sm text-gray-600 lowercase">
            <svg
              width="14"
              height="18"
              viewBox="0 0 360 460"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              className="shrink-0"
            >
              <path
                d="M340 130H230V20"
                stroke="currentColor"
                strokeWidth="24"
                strokeMiterlimit="10"
                strokeLinecap="round"
              />
              <path
                d="M350 450H10V10H230L350 130V450Z"
                stroke="currentColor"
                strokeWidth="24"
                strokeMiterlimit="10"
                strokeLinecap="round"
              />
              <path d="M280 200H80V220H280V200Z" fill="currentColor" />
              <path d="M280 320H80V340H280V320Z" fill="currentColor" />
              <path d="M240 260H80V280H240V260Z" fill="currentColor" />
            </svg>
            <span>-navigator</span>
          </span>
          <span className="text-sm text-gray-400">
            {currentYear}
          </span>
        </div>

        {/* Links */}
        <nav className="flex items-center gap-6 text-sm">
          <a
            href="https://github.com/younissk/PaperNavigator"
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-600 hover:text-black no-underline lowercase transition-colors"
          >
            github
          </a>
          <Link
            to="/queries"
            className="text-gray-600 hover:text-black no-underline lowercase transition-colors"
          >
            reports
          </Link>
          <Link
            to="/monitoring"
            className="text-gray-600 hover:text-black no-underline lowercase transition-colors"
          >
            monitoring
          </Link>
          <a
            href="https://younissk.github.io"
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-600 hover:text-black no-underline lowercase transition-colors"
          >
            portfolio
          </a>
        </nav>
      </div>
    </footer>
  );
}
