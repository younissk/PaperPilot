import { useState, useEffect, useCallback, useRef } from "react";

// Brutalist coral shadow styles
const brutalShadow = { boxShadow: "3px 3px 0 #F3787A" };

// Game constants
const GRID_SIZE = 9;
const GAME_DURATION = 60; // seconds
const INITIAL_SPAWN_INTERVAL = 1200; // ms
const MIN_SPAWN_INTERVAL = 600; // ms
const DOC_VISIBLE_MIN = 1500; // ms
const DOC_VISIBLE_MAX = 2500; // ms
const IMPORTANT_CHANCE = 0.7;

type DocType = "important" | "spam" | null;
type GameState = "ready" | "playing" | "gameOver";

interface Slot {
  type: DocType;
  expiresAt: number;
  animating: boolean;
}

/**
 * Important document SVG - green tint with checkmark
 */
function ImportantDoc({ size = 60 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size * (460 / 360)}
      viewBox="0 0 360 460"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M350 450H10V10H230L350 130V450Z"
        fill="#16A34A"
        fillOpacity={0.15}
      />
      <path
        d="M350 450H10V10H230L350 130V450Z"
        stroke="#16A34A"
        strokeWidth="16"
        strokeMiterlimit="10"
        strokeLinecap="round"
      />
      <path
        d="M340 130H230V20"
        stroke="#16A34A"
        strokeWidth="16"
        strokeMiterlimit="10"
        strokeLinecap="round"
      />
      {/* Checkmark */}
      <path
        d="M120 280L170 330L260 200"
        stroke="#16A34A"
        strokeWidth="28"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/**
 * Spam document SVG - red tint with X
 */
function SpamDoc({ size = 60 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size * (460 / 360)}
      viewBox="0 0 360 460"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M350 450H10V10H230L350 130V450Z"
        fill="#DC2626"
        fillOpacity={0.15}
      />
      <path
        d="M350 450H10V10H230L350 130V450Z"
        stroke="#DC2626"
        strokeWidth="16"
        strokeMiterlimit="10"
        strokeLinecap="round"
      />
      <path
        d="M340 130H230V20"
        stroke="#DC2626"
        strokeWidth="16"
        strokeMiterlimit="10"
        strokeLinecap="round"
      />
      {/* X mark */}
      <path
        d="M130 200L250 330M250 200L130 330"
        stroke="#DC2626"
        strokeWidth="28"
        strokeLinecap="round"
      />
    </svg>
  );
}

interface WhackADocGameProps {
  onClose: () => void;
  onBack?: () => void;
}

/**
 * Whack-a-Doc game - tap important docs, avoid spam
 */
export function WhackADocGame({ onClose, onBack }: WhackADocGameProps) {
  const [gameState, setGameState] = useState<GameState>("ready");
  const [score, setScore] = useState(0);
  const [highScore, setHighScore] = useState(() => {
    const saved = localStorage.getItem("whackadoc-highscore");
    return saved ? parseInt(saved, 10) : 0;
  });
  const [lives, setLives] = useState(3);
  const [timeLeft, setTimeLeft] = useState(GAME_DURATION);
  const [slots, setSlots] = useState<Slot[]>(
    Array(GRID_SIZE).fill(null).map(() => ({ type: null, expiresAt: 0, animating: false }))
  );

  const spawnIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const gameTickRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const currentSpawnRate = useRef(INITIAL_SPAWN_INTERVAL);

  const resetGame = useCallback(() => {
    setScore(0);
    setLives(3);
    setTimeLeft(GAME_DURATION);
    setSlots(Array(GRID_SIZE).fill(null).map(() => ({ type: null, expiresAt: 0, animating: false })));
    setGameState("ready");
    currentSpawnRate.current = INITIAL_SPAWN_INTERVAL;
  }, []);

  const endGame = useCallback(() => {
    setGameState("gameOver");
    if (spawnIntervalRef.current) {
      clearInterval(spawnIntervalRef.current);
      spawnIntervalRef.current = null;
    }
    if (gameTickRef.current) {
      clearInterval(gameTickRef.current);
      gameTickRef.current = null;
    }
  }, []);

  const spawnDoc = useCallback(() => {
    setSlots((currentSlots) => {
      const emptyIndices = currentSlots
        .map((slot, index) => (slot.type === null ? index : -1))
        .filter((index) => index !== -1);

      if (emptyIndices.length === 0) return currentSlots;

      const randomIndex = emptyIndices[Math.floor(Math.random() * emptyIndices.length)];
      const docType: DocType = Math.random() < IMPORTANT_CHANCE ? "important" : "spam";
      const visibleDuration = DOC_VISIBLE_MIN + Math.random() * (DOC_VISIBLE_MAX - DOC_VISIBLE_MIN);

      const newSlots = [...currentSlots];
      newSlots[randomIndex] = {
        type: docType,
        expiresAt: Date.now() + visibleDuration,
        animating: true,
      };

      // Remove animating flag after animation
      setTimeout(() => {
        setSlots((s) => {
          const updated = [...s];
          if (updated[randomIndex]?.type === docType) {
            updated[randomIndex] = { ...updated[randomIndex], animating: false };
          }
          return updated;
        });
      }, 100);

      return newSlots;
    });
  }, []);

  const handleSlotClick = useCallback((index: number) => {
    if (gameState !== "playing") return;

    setSlots((currentSlots) => {
      const slot = currentSlots[index];
      if (!slot.type) return currentSlots;

      if (slot.type === "important") {
        setScore((s) => {
          const newScore = s + 10;
          if (newScore > highScore) {
            setHighScore(newScore);
            localStorage.setItem("whackadoc-highscore", newScore.toString());
          }
          return newScore;
        });
      } else {
        // Spam clicked - lose a life
        setLives((l) => {
          const newLives = l - 1;
          if (newLives <= 0) {
            endGame();
          }
          return newLives;
        });
      }

      const newSlots = [...currentSlots];
      newSlots[index] = { type: null, expiresAt: 0, animating: false };
      return newSlots;
    });
  }, [gameState, highScore, endGame]);

  const startGame = useCallback(() => {
    setGameState("playing");
    setScore(0);
    setLives(3);
    setTimeLeft(GAME_DURATION);
    setSlots(Array(GRID_SIZE).fill(null).map(() => ({ type: null, expiresAt: 0, animating: false })));
    currentSpawnRate.current = INITIAL_SPAWN_INTERVAL;
  }, []);

  // Game tick - check expired docs and update timer
  useEffect(() => {
    if (gameState !== "playing") return;

    gameTickRef.current = setInterval(() => {
      const now = Date.now();

      // Check for expired docs
      setSlots((currentSlots) => {
        let livesLost = 0;
        const newSlots = currentSlots.map((slot) => {
          if (slot.type && now >= slot.expiresAt) {
            if (slot.type === "important") {
              livesLost++;
            }
            return { type: null as DocType, expiresAt: 0, animating: false };
          }
          return slot;
        });

        if (livesLost > 0) {
          setLives((l) => {
            const newLives = l - livesLost;
            if (newLives <= 0) {
              endGame();
            }
            return Math.max(0, newLives);
          });
        }

        return newSlots;
      });

      // Update timer
      setTimeLeft((t) => {
        const newTime = t - 0.1;
        if (newTime <= 0) {
          endGame();
          return 0;
        }
        return newTime;
      });
    }, 100);

    return () => {
      if (gameTickRef.current) {
        clearInterval(gameTickRef.current);
      }
    };
  }, [gameState, endGame]);

  // Spawn loop with increasing difficulty
  useEffect(() => {
    if (gameState !== "playing") return;

    const scheduleNextSpawn = () => {
      spawnIntervalRef.current = setTimeout(() => {
        spawnDoc();
        // Increase difficulty
        currentSpawnRate.current = Math.max(
          MIN_SPAWN_INTERVAL,
          currentSpawnRate.current - 10
        );
        scheduleNextSpawn();
      }, currentSpawnRate.current);
    };

    // Initial spawn
    spawnDoc();
    scheduleNextSpawn();

    return () => {
      if (spawnIntervalRef.current) {
        clearTimeout(spawnIntervalRef.current);
      }
    };
  }, [gameState, spawnDoc]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ backgroundColor: "rgba(0, 0, 0, 0.5)" }}
    >
      <div
        className="bg-white border-2 border-black w-full max-w-sm"
        style={brutalShadow}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-3 border-b-2 border-black">
          <div className="flex items-center gap-2">
            {onBack && (
              <button
                type="button"
                onClick={onBack}
                className="w-8 h-8 flex items-center justify-center border-2 border-black bg-white hover:bg-gray-100 font-bold text-sm"
              >
                ←
              </button>
            )}
            <h3 className="text-lg font-bold lowercase">whack-a-doc</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center border-2 border-black bg-white hover:bg-gray-100 font-bold"
          >
            ×
          </button>
        </div>

        {/* Stats */}
        <div className="flex justify-center gap-2 p-2 text-xs lowercase border-b-2 border-black flex-wrap">
          <div className="flex items-center gap-1 px-2 py-1 border border-black">
            <span className="font-bold">{score}</span>
            <span className="text-gray-600">score</span>
          </div>
          <div className="flex items-center gap-1 px-2 py-1 border border-black">
            <span className="font-bold">{highScore}</span>
            <span className="text-gray-600">best</span>
          </div>
          <div className="flex items-center gap-1 px-2 py-1 border border-black">
            <span className="font-bold text-red-600">{"♥".repeat(lives)}</span>
            <span className="text-gray-400">{"♥".repeat(3 - lives)}</span>
          </div>
        </div>

        {/* Game area */}
        <div className="p-4">
          {gameState === "ready" && (
            <div className="text-center py-8">
              <div className="flex justify-center gap-4 mb-4">
                <ImportantDoc size={40} />
                <SpamDoc size={40} />
              </div>
              <h4 className="text-lg font-bold lowercase mb-2">how to play</h4>
              <p className="text-sm text-gray-600 lowercase mb-1">
                tap <span className="text-green-600 font-bold">green docs</span> = +10 points
              </p>
              <p className="text-sm text-gray-600 lowercase mb-4">
                avoid <span className="text-red-600 font-bold">red docs</span> = -1 life
              </p>
              <button
                type="button"
                onClick={startGame}
                className="px-6 py-3 bg-black text-white font-bold text-sm lowercase border-2 border-black hover:bg-gray-900 active:scale-95 transition-transform"
                style={brutalShadow}
              >
                start game
              </button>
            </div>
          )}

          {gameState === "playing" && (
            <>
              {/* Timer */}
              <div className="text-center mb-3">
                <span className="text-sm font-mono font-bold lowercase">
                  {Math.ceil(timeLeft)}s remaining
                </span>
              </div>

              {/* Grid */}
              <div
                className="grid grid-cols-3 gap-2 mx-auto"
                style={{ maxWidth: "280px" }}
              >
                {slots.map((slot, index) => (
                  <button
                    key={index}
                    type="button"
                    onClick={() => handleSlotClick(index)}
                    className={`
                      aspect-[3/4] border-2 border-dashed border-gray-300 
                      flex items-center justify-center
                      transition-transform duration-100
                      active:scale-90
                      ${slot.type ? "border-solid border-black bg-gray-50" : "bg-white"}
                    `}
                    style={{
                      minHeight: "80px",
                      touchAction: "manipulation",
                    }}
                  >
                    {slot.type === "important" && (
                      <div
                        className={`transition-transform duration-100 ${
                          slot.animating ? "scale-0" : "scale-100"
                        }`}
                        style={{ willChange: "transform" }}
                      >
                        <ImportantDoc size={50} />
                      </div>
                    )}
                    {slot.type === "spam" && (
                      <div
                        className={`transition-transform duration-100 ${
                          slot.animating ? "scale-0" : "scale-100"
                        }`}
                        style={{ willChange: "transform" }}
                      >
                        <SpamDoc size={50} />
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </>
          )}

          {gameState === "gameOver" && (
            <div className="text-center py-8">
              <h4 className="text-xl font-bold lowercase mb-2">game over</h4>
              <p className="text-sm text-gray-600 lowercase mb-1">
                score: <span className="font-bold text-black">{score}</span>
              </p>
              {score === highScore && score > 0 && (
                <p className="text-xs text-[#F3787A] font-bold lowercase mb-2">
                  new high score!
                </p>
              )}
              <button
                type="button"
                onClick={resetGame}
                className="mt-4 px-6 py-3 bg-black text-white font-bold text-sm lowercase border-2 border-black hover:bg-gray-900 active:scale-95 transition-transform"
                style={brutalShadow}
              >
                play again
              </button>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t-2 border-black text-center">
          <p className="text-[10px] text-gray-400 lowercase">
            tap important docs, avoid spam
          </p>
        </div>
      </div>
    </div>
  );
}
