import { useState } from "react";
import { MemoryGame } from "./MemoryGame";
import { FlappyDocGame } from "./FlappyDocGame";

// Brutalist coral shadow styles
const brutalShadow = { boxShadow: "3px 3px 0 #F3787A" };

type ActiveGame = "menu" | "memory" | "flappy";

interface GameCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  onClick: () => void;
}

/**
 * Game selection card
 */
function GameCard({ title, description, icon, onClick }: GameCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex flex-col items-center p-4 border-2 border-black bg-white hover:bg-gray-50 transition-all hover:translate-x-[-2px] hover:translate-y-[-2px] active:translate-x-0 active:translate-y-0"
      style={brutalShadow}
    >
      <div className="mb-3">{icon}</div>
      <h4 className="text-sm font-bold lowercase">{title}</h4>
      <p className="text-xs text-gray-500 lowercase mt-1">{description}</p>
    </button>
  );
}

/**
 * Memory game icon - grid of documents
 */
function MemoryIcon() {
  return (
    <div className="grid grid-cols-2 gap-1">
      {[0, 1, 2, 3].map((i) => (
        <svg
          key={i}
          width="20"
          height="26"
          viewBox="0 0 360 460"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M350 450H10V10H230L350 130V450Z"
            fill={i % 2 === 0 ? "black" : "white"}
            stroke="black"
            strokeWidth="30"
          />
        </svg>
      ))}
    </div>
  );
}

/**
 * FlappyDoc icon - flying document
 */
function FlappyIcon() {
  return (
    <div className="relative">
      <svg
        width="40"
        height="52"
        viewBox="0 0 360 460"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{ transform: "rotate(-15deg)" }}
      >
        <path
          d="M350 450H10V10H230L350 130V450Z"
          fill="white"
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
      {/* Motion lines */}
      <div className="absolute -left-3 top-1/2 -translate-y-1/2 space-y-1">
        <div className="w-3 h-0.5 bg-black" />
        <div className="w-2 h-0.5 bg-black ml-1" />
        <div className="w-3 h-0.5 bg-black" />
      </div>
    </div>
  );
}

interface GameLauncherProps {
  onClose: () => void;
}

/**
 * Game launcher with menu to select between games
 */
export function GameLauncher({ onClose }: GameLauncherProps) {
  const [activeGame, setActiveGame] = useState<ActiveGame>("menu");

  const handleBack = () => {
    setActiveGame("menu");
  };

  // Render active game
  if (activeGame === "memory") {
    return <MemoryGame onClose={onClose} onBack={handleBack} />;
  }

  if (activeGame === "flappy") {
    return <FlappyDocGame onClose={onClose} onBack={handleBack} />;
  }

  // Render menu
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ backgroundColor: "rgba(0, 0, 0, 0.5)" }}
    >
      <div
        className="bg-white border-2 border-black max-w-sm w-full"
        style={brutalShadow}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b-2 border-black">
          <h3 className="text-lg font-bold lowercase">choose a game</h3>
          <button
            type="button"
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center border-2 border-black bg-white hover:bg-gray-100 font-bold"
          >
            ×
          </button>
        </div>

        {/* Game grid */}
        <div className="p-4">
          <div className="grid grid-cols-2 gap-4">
            <GameCard
              title="memory"
              description="match the papers"
              icon={<MemoryIcon />}
              onClick={() => setActiveGame("memory")}
            />
            <GameCard
              title="flappydoc"
              description="dodge the pipes"
              icon={<FlappyIcon />}
              onClick={() => setActiveGame("flappy")}
            />
          </div>
        </div>

        {/* Footer */}
        <div className="p-3 border-t-2 border-black text-center">
          <p className="text-[10px] text-gray-400 lowercase">
            kill time while your report generates
          </p>
        </div>
      </div>
    </div>
  );
}
