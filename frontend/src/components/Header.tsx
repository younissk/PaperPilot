import { Link, useLocation } from "react-router";
import { useHealthCheck } from "@/hooks";

/**
 * Header component with navigation and API health indicator.
 */
export function Header() {
  const location = useLocation();
  const { data: health, isLoading, error } = useHealthCheck();

  const getHealthStatus = () => {
    if (isLoading) {
      return { status: "checking", text: "Checking...", color: "bg-yellow-300" };
    }
    if (error || !health) {
      return { status: "offline", text: "API Offline", color: "bg-red-400" };
    }
    return { status: "online", text: "API Online", color: "bg-teal-300" };
  };

  const healthStatus = getHealthStatus();

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="bg-primary-600 h-14 flex items-center">
      <div className="w-full flex items-center px-4">
        <Link
          to="/"
          className="font-bold text-xl text-white no-underline hover:no-underline mr-6"
        >
          Paper Navigator
        </Link>

        <Link
          to="/monitoring"
          className="flex items-center gap-1.5 no-underline hover:opacity-80 transition-opacity"
        >
          <span
            className={`w-2 h-2 rounded-full ${healthStatus.color} ${
              healthStatus.status === "checking" ? "animate-pulse" : ""
            }`}
          />
          <span className="text-xs text-white opacity-90">
            {healthStatus.text}
          </span>
        </Link>

        <nav className="flex h-14 ml-auto">
          <Link
            to="/queries"
            className={`flex items-center px-6 font-medium no-underline transition-colors duration-200 ${
              isActive("/queries")
                ? "bg-primary-50 text-primary-600"
                : "bg-white text-primary-600 hover:bg-gray-100"
            }`}
          >
            Searches
          </Link>
          <Link
            to="/about"
            className={`flex items-center px-6 font-medium no-underline transition-colors duration-200 ${
              isActive("/about")
                ? "bg-primary-50 text-primary-600"
                : "bg-white text-primary-600 hover:bg-gray-100"
            }`}
          >
            About
          </Link>
        </nav>
      </div>
    </header>
  );
}
