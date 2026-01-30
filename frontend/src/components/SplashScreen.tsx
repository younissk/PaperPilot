import { useState, useEffect } from "react";

type AnimationPhase = "idle" | "pump1" | "pump2" | "pump3" | "done";

const COLORS = {
  black: "#000000",
  teal: "#2c7a7b",
  coral: "#F3787A",
} as const;

/**
 * Full-page splash screen with animated document icon.
 * 3 dramatic pumps with color changes, culminating in an explosive pop.
 */
export function SplashScreen({ onComplete }: { onComplete: () => void }) {
  const [phase, setPhase] = useState<AnimationPhase>("idle");
  const [showRipple, setShowRipple] = useState(false);

  useEffect(() => {
    // Small delay before starting for anticipation
    const startDelay = setTimeout(() => setPhase("pump1"), 200);

    return () => clearTimeout(startDelay);
  }, []);

  useEffect(() => {
    if (phase === "idle" || phase === "done") return;

    let timer: NodeJS.Timeout;

    if (phase === "pump1") {
      timer = setTimeout(() => setPhase("pump2"), 500);
    } else if (phase === "pump2") {
      timer = setTimeout(() => setPhase("pump3"), 500);
    } else if (phase === "pump3") {
      setShowRipple(true);
      timer = setTimeout(() => {
        setPhase("done");
        onComplete();
      }, 600);
    }

    return () => clearTimeout(timer);
  }, [phase, onComplete]);

  if (phase === "done") return null;

  // Color based on phase
  const getColor = () => {
    switch (phase) {
      case "idle":
      case "pump1":
        return COLORS.black;
      case "pump2":
        return COLORS.teal;
      case "pump3":
        return COLORS.coral;
      default:
        return COLORS.black;
    }
  };

  // Shadow color matches icon color
  const getShadowColor = () => {
    switch (phase) {
      case "pump2":
        return "rgba(44, 122, 123, 0.4)";
      case "pump3":
        return "rgba(243, 120, 122, 0.5)";
      default:
        return "rgba(0, 0, 0, 0.2)";
    }
  };

  const isPumping = phase === "pump1" || phase === "pump2";
  const isPopping = phase === "pump3";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-gray-50 overflow-hidden"
      aria-hidden="true"
    >
      {/* Expanding ripple on pop */}
      {showRipple && (
        <div
          className="absolute rounded-full animate-ripple-burst"
          style={{
            width: 160,
            height: 160,
            border: `3px solid ${COLORS.coral}`,
          }}
        />
      )}

      {/* Icon container with animations */}
      <div
        key={phase} // Force re-mount to restart animation
        className={`
          relative transition-all duration-200
          ${isPumping ? "animate-pump" : ""}
          ${isPopping ? "animate-pop" : ""}
        `}
        style={{
          color: getColor(),
          filter: `drop-shadow(0 0 20px ${getShadowColor()})`,
        }}
      >
        {/* Glow pulse behind icon */}
        <div
          className={`
            absolute inset-0 rounded-full blur-2xl transition-opacity duration-300
            ${isPumping ? "animate-glow-pulse" : ""}
            ${isPopping ? "opacity-0" : "opacity-60"}
          `}
          style={{
            background: getShadowColor(),
            transform: "scale(2)",
          }}
        />

        {/* The document SVG */}
        <svg
          width="140"
          height="180"
          viewBox="0 0 360 460"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="relative z-10"
        >
          <path
            d="M340 130H230V20"
            stroke="currentColor"
            strokeWidth="20"
            strokeMiterlimit="10"
            strokeLinecap="round"
          />
          <path
            d="M350 450H10V10H230L350 130V450Z"
            stroke="currentColor"
            strokeWidth="20"
            strokeMiterlimit="10"
            strokeLinecap="round"
          />
          <path d="M280 200H80V220H280V200Z" fill="currentColor" />
          <path d="M280 320H80V340H280V320Z" fill="currentColor" />
          <path d="M240 260H80V280H240V260Z" fill="currentColor" />
        </svg>
      </div>
    </div>
  );
}
