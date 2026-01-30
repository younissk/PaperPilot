import { useState, useEffect, useCallback } from "react";
import { Outlet, useLocation } from "react-router";
import { Header } from "./Header";
import { Footer } from "./Footer";
import { CustomCursor } from "./CustomCursor";
import { SplashScreen } from "./SplashScreen";

const SPLASH_STORAGE_KEY = "paperpilot_splash_shown";

/**
 * Main layout component wrapping all pages.
 * Brutalist minimal design with transparent header, minimal footer, and custom cursor.
 * Shows splash screen on first visit to home page.
 */
export default function Layout() {
  const location = useLocation();
  const isHomePage = location.pathname === "/";

  const [showSplash, setShowSplash] = useState(() => {
    // Only show splash on home page and if not already shown this session
    if (!isHomePage) return false;
    return sessionStorage.getItem(SPLASH_STORAGE_KEY) !== "true";
  });

  const handleSplashComplete = useCallback(() => {
    sessionStorage.setItem(SPLASH_STORAGE_KEY, "true");
    setShowSplash(false);
  }, []);

  // Reset splash state if navigating away and back (edge case)
  useEffect(() => {
    if (!isHomePage) {
      setShowSplash(false);
    }
  }, [isHomePage]);

  return (
    <>
      {showSplash && <SplashScreen onComplete={handleSplashComplete} />}
      <CustomCursor />
      <Header />
      <main>
        <Outlet />
      </main>
      <Footer />
    </>
  );
}
