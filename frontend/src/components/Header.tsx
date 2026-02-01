import { useState, useEffect } from "react";
import { Link, useLocation } from "react-router";

/**
 * Header component with minimal brutalist navigation.
 * Transparent background, full-screen mobile menu with animation.
 */
export function Header() {
  const location = useLocation();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const isActive = (path: string) => location.pathname === path;

  // Close menu on route change
  useEffect(() => {
    setIsMenuOpen(false);
  }, [location.pathname]);

  // Prevent body scroll when menu is open
  useEffect(() => {
    if (isMenuOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isMenuOpen]);

  return (
    <>
      <header className="bg-gray-50 h-12 flex items-center sticky top-0 z-50">
        <div className="w-full max-w-7xl mx-auto flex items-center px-4">
          {/* Logo */}
          <Link
            to="/"
            className="flex items-center gap-1 font-medium text-base text-gray-900 no-underline hover:no-underline lowercase z-50"
          >
            <svg
              width="16"
              height="20"
              viewBox="0 0 360 460"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              className="shrink-0"
            >
              <path
                d="M350 450H10V10H230L350 130V450Z"
                fill="#F3787A"
                stroke="black"
                strokeWidth="20"
                strokeMiterlimit="10"
                strokeLinecap="round"
              />
              <path
                d="M340 130H230V20"
                stroke="black"
                strokeWidth="20"
                strokeMiterlimit="10"
                strokeLinecap="round"
              />
              <path d="M280 200H80V220H280V200Z" fill="black" />
              <path d="M280 320H80V340H280V320Z" fill="black" />
              <path d="M240 260H80V280H240V260Z" fill="black" />
            </svg>
            <span>-navigator</span>
            <span className="relative group ml-1.5">
              <span
                className="px-1 py-px text-[8px] font-semibold bg-black text-white border border-black cursor-default"
                style={{ boxShadow: "rgb(243, 120, 122) 1.5px 1.5px 0px" }}
              >
                v0.1
              </span>
              <span className="absolute left-1/2 -translate-x-1/2 top-full mt-2 px-2 py-1 text-[10px] text-white bg-gray-900 rounded whitespace-nowrap opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-opacity duration-200 pointer-events-none z-50">
                Early preview — expect bugs!
                <span className="absolute left-1/2 -translate-x-1/2 -top-1 w-2 h-2 bg-gray-900 rotate-45" />
              </span>
            </span>
          </Link>

          {/* Menu Button */}
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="ml-auto z-50 p-2 -mr-2"
            aria-label={isMenuOpen ? "Close menu" : "Open menu"}
          >
            <div className="w-6 h-5 relative flex flex-col justify-between">
              <span
                className={`w-full h-0.5 bg-black transition-all duration-300 origin-center ${
                  isMenuOpen ? "rotate-45 translate-y-2" : ""
                }`}
              />
              <span
                className={`w-full h-0.5 bg-black transition-all duration-300 ${
                  isMenuOpen ? "opacity-0 scale-0" : ""
                }`}
              />
              <span
                className={`w-full h-0.5 bg-black transition-all duration-300 origin-center ${
                  isMenuOpen ? "-rotate-45 -translate-y-2" : ""
                }`}
              />
            </div>
          </button>
        </div>
      </header>

      {/* Menu Overlay */}
      <div
        className={`fixed inset-0 bg-white z-40 flex flex-col items-center justify-center transition-all duration-300 ${
          isMenuOpen
            ? "opacity-100 visible"
            : "opacity-0 invisible pointer-events-none"
        }`}
      >
        <nav className="flex flex-col items-center gap-8">
          <Link
            to="/queries"
            onClick={() => setIsMenuOpen(false)}
            className={`text-5xl font-bold no-underline transition-all duration-300 lowercase ${
              isActive("/queries") ? "text-gray-900" : "text-gray-400 hover:text-gray-900"
            } ${isMenuOpen ? "translate-y-0 opacity-100" : "translate-y-8 opacity-0"}`}
            style={{ transitionDelay: isMenuOpen ? "100ms" : "0ms" }}
          >
            reports
          </Link>
          <Link
            to="/monitoring"
            onClick={() => setIsMenuOpen(false)}
            className={`text-5xl font-bold no-underline transition-all duration-300 lowercase ${
              isActive("/monitoring") ? "text-gray-900" : "text-gray-400 hover:text-gray-900"
            } ${isMenuOpen ? "translate-y-0 opacity-100" : "translate-y-8 opacity-0"}`}
            style={{ transitionDelay: isMenuOpen ? "200ms" : "0ms" }}
          >
            monitoring
          </Link>
          <a
            href="/#how-it-works"
            onClick={() => setIsMenuOpen(false)}
            className={`text-5xl font-bold no-underline transition-all duration-300 lowercase text-gray-400 hover:text-gray-900 ${
              isMenuOpen ? "translate-y-0 opacity-100" : "translate-y-8 opacity-0"
            }`}
            style={{ transitionDelay: isMenuOpen ? "300ms" : "0ms" }}
          >
            how it works
          </a>
          <a
            href="/#infrastructure"
            onClick={() => setIsMenuOpen(false)}
            className={`text-5xl font-bold no-underline transition-all duration-300 lowercase text-gray-400 hover:text-gray-900 ${
              isMenuOpen ? "translate-y-0 opacity-100" : "translate-y-8 opacity-0"
            }`}
            style={{ transitionDelay: isMenuOpen ? "400ms" : "0ms" }}
          >
            infrastructure
          </a>
          <a
            href="https://forms.gle/Nu4sUUeWMSJmCYR28"
            target="_blank"
            rel="noopener noreferrer"
            onClick={() => setIsMenuOpen(false)}
            className={`text-5xl font-bold no-underline transition-all duration-300 lowercase text-gray-400 hover:text-gray-900 ${
              isMenuOpen ? "translate-y-0 opacity-100" : "translate-y-8 opacity-0"
            }`}
            style={{ transitionDelay: isMenuOpen ? "500ms" : "0ms" }}
          >
            feedback / complaints
          </a>
        </nav>

        {/* Attribution Footer */}
        <div
          className={`absolute bottom-8 text-sm text-gray-500 transition-all duration-300 ${
            isMenuOpen ? "translate-y-0 opacity-100" : "translate-y-4 opacity-0"
          }`}
          style={{ transitionDelay: isMenuOpen ? "600ms" : "0ms" }}
        >
          made with 💻 by{" "}
          <a
            href="https://younissk.github.io"
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-900 hover:text-[#F3787A] no-underline font-medium transition-colors"
          >
            younissk
          </a>
        </div>
      </div>
    </>
  );
}
