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
          <span className="text-sm text-gray-600 lowercase">
            paper-navigator
          </span>
          <span className="text-sm text-gray-400">
            {currentYear}
          </span>
        </div>

        {/* Links */}
        <nav className="flex items-center gap-6 text-sm">
          <a
            href="https://github.com/younisskandah/PaperPilot"
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
            to="/about"
            className="text-gray-600 hover:text-black no-underline lowercase transition-colors"
          >
            about
          </Link>
        </nav>
      </div>
    </footer>
  );
}
