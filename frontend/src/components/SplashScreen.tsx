import { useState, useEffect } from "react";

type AnimationPhase = "pump1" | "pump2" | "pump3" | "done";

/**
 * Clean full-page splash screen with animated document icon.
 * 3 subtle pumps with color changes, then fades out to reveal the page.
 */
export function SplashScreen({ onComplete }: { onComplete: () => void }) {
  const [phase, setPhase] = useState<AnimationPhase>("pump1");

  useEffect(() => {
    const timings = {
      pump1: 400,
      pump2: 800,
      pump3: 1200,
      done: 1600,
    };

    const t1 = setTimeout(() => setPhase("pump2"), timings.pump1);
    const t2 = setTimeout(() => setPhase("pump3"), timings.pump2);
    const t3 = setTimeout(() => {
      setPhase("done");
      onComplete();
    }, timings.done);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
    };
  }, [onComplete]);

  if (phase === "done") return null;

  const colors = {
    pump1: "#1a1a1a",
    pump2: "#2c7a7b",
    pump3: "#F3787A",
  };

  const isPopping = phase === "pump3";

  return (
    <div
      className={`
        fixed inset-0 z-50 flex items-center justify-center bg-gray-50
        transition-opacity duration-300
        ${isPopping ? "opacity-0" : "opacity-100"}
      `}
      aria-hidden="true"
    >
      <div
        key={phase}
        className={isPopping ? "animate-splash-pop" : "animate-splash-pump"}
        style={{ color: colors[phase] }}
      >
        <svg
          width="100"
          height="128"
          viewBox="0 0 360 460"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="transition-colors duration-150"
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
