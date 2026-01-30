import { Link, useLocation } from "react-router";
import { useHealthCheck } from "@/hooks";

/**
 * Header component with navigation and API health indicator.
 * Thin, calm design with white background.
 */
export function Header() {
  const location = useLocation();
  const { data: health, isLoading, error } = useHealthCheck();

  const getHealthStatus = () => {
    if (isLoading) {
      return { status: "checking", text: "Checking...", color: "bg-yellow-400" };
    }
    if (error || !health) {
      return { status: "offline", text: "Offline", color: "bg-red-400" };
    }
    return { status: "online", text: "Online", color: "bg-green-400" };
  };

  const healthStatus = getHealthStatus();

  const isActive = (path: string) => location.pathname === path;
  const isHome = location.pathname === "/";

  return (
    <header className="bg-white border-b border-gray-200 h-12 flex items-center sticky top-0 z-50">
      <div className="w-full max-w-7xl mx-auto flex items-center px-4">
        {/* Logo */}
        <Link
          to="/"
          className="font-semibold text-lg text-gray-900 no-underline hover:no-underline hover:text-primary-600 transition-colors"
        >
          PaperNavigator
        </Link>

        {/* Monitoring indicator */}
        <Link
          to="/monitoring"
          className="flex items-center gap-1.5 ml-4 no-underline hover:opacity-80 transition-opacity"
          title="System status"
        >
          <span
            className={`w-2 h-2 rounded-full ${healthStatus.color} ${
              healthStatus.status === "checking" ? "animate-pulse" : ""
            }`}
          />
          <span className="text-xs text-gray-500">
            {healthStatus.text}
          </span>
        </Link>

        {/* Navigation */}
        <nav className="flex items-center gap-1 ml-auto">
          <Link
            to="/queries"
            className={`px-3 py-1.5 text-sm font-medium no-underline rounded-md transition-colors duration-200 ${
              isActive("/queries")
                ? "bg-primary-50 text-primary-700"
                : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
            }`}
          >
            Public reports
          </Link>
          {isHome ? (
            <a
              href="#how-it-works"
              className="px-3 py-1.5 text-sm font-medium no-underline rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors duration-200"
            >
              How it works
            </a>
          ) : (
            <Link
              to="/#how-it-works"
              className="px-3 py-1.5 text-sm font-medium no-underline rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors duration-200"
            >
              How it works
            </Link>
          )}
          <a
            href="https://github.com/younisskandah/PaperPilot"
            target="_blank"
            rel="noopener noreferrer"
            className="px-3 py-1.5 text-sm font-medium no-underline rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors duration-200"
          >
            GitHub
          </a>
          {isHome ? (
            <a
              href="#privacy"
              className="px-3 py-1.5 text-sm font-medium no-underline rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors duration-200"
            >
              Privacy
            </a>
          ) : (
            <Link
              to="/#privacy"
              className="px-3 py-1.5 text-sm font-medium no-underline rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors duration-200"
            >
              Privacy
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}
