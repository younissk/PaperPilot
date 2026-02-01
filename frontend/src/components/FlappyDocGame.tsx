import { useState, useEffect, useRef, useCallback } from "react";

// Brutalist coral shadow styles
const brutalShadow = { boxShadow: "3px 3px 0 #F3787A" };

// Game constants
const GRAVITY = 0.4;
const JUMP_VELOCITY = -7;
const PIPE_WIDTH = 50;
const PIPE_GAP = 120;
const PIPE_SPEED = 2.5;
const DOC_WIDTH = 36;
const DOC_HEIGHT = 46;

interface Pipe {
  x: number;
  gapY: number;
  passed: boolean;
}

type GameState = "ready" | "playing" | "gameOver";

/**
 * Doc SVG component for the player
 */
function DocPlayer({ rotation }: { rotation: number }) {
  return (
    <svg
      width={DOC_WIDTH}
      height={DOC_HEIGHT}
      viewBox="0 0 360 460"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      style={{
        transform: `rotate(${rotation}deg)`,
        transition: "transform 0.1s ease-out",
      }}
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
  );
}

interface FlappyDocGameProps {
  onClose: () => void;
  onBack?: () => void;
}

/**
 * FlappyDoc game - a Flappy Bird clone with the doc SVG
 */
export function FlappyDocGame({ onClose, onBack }: FlappyDocGameProps) {
  const gameAreaRef = useRef<HTMLDivElement>(null);
  const animationRef = useRef<number>(0);
  
  const [gameState, setGameState] = useState<GameState>("ready");
  const [score, setScore] = useState(0);
  const [highScore, setHighScore] = useState(() => {
    const saved = localStorage.getItem("flappydoc-highscore");
    return saved ? parseInt(saved, 10) : 0;
  });
  
  // Game physics state
  const [docY, setDocY] = useState(150);
  const [velocity, setVelocity] = useState(0);
  const [pipes, setPipes] = useState<Pipe[]>([]);
  
  // Game area dimensions
  const GAME_WIDTH = 320;
  const GAME_HEIGHT = 400;
  const DOC_X = 60;

  const resetGame = useCallback(() => {
    setDocY(150);
    setVelocity(0);
    setPipes([]);
    setScore(0);
    setGameState("ready");
  }, []);

  const jump = useCallback(() => {
    if (gameState === "ready") {
      setGameState("playing");
      setVelocity(JUMP_VELOCITY);
      setPipes([{ x: GAME_WIDTH + 50, gapY: 150 + Math.random() * 100, passed: false }]);
    } else if (gameState === "playing") {
      setVelocity(JUMP_VELOCITY);
    } else if (gameState === "gameOver") {
      resetGame();
    }
  }, [gameState, resetGame]);

  // Handle keyboard input
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === "Space" || e.key === " ") {
        e.preventDefault();
        jump();
      }
    };
    
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [jump]);

  // Game loop
  useEffect(() => {
    if (gameState !== "playing") return;

    const gameLoop = () => {
      setVelocity((v) => v + GRAVITY);
      setDocY((y) => {
        const newY = y + velocity;
        
        // Check floor/ceiling collision
        if (newY < 0 || newY + DOC_HEIGHT > GAME_HEIGHT) {
          setGameState("gameOver");
          return Math.max(0, Math.min(newY, GAME_HEIGHT - DOC_HEIGHT));
        }
        
        return newY;
      });

      setPipes((currentPipes) => {
        // Move pipes
        let newPipes = currentPipes.map((pipe) => ({
          ...pipe,
          x: pipe.x - PIPE_SPEED,
        }));

        // Check for score
        newPipes = newPipes.map((pipe) => {
          if (!pipe.passed && pipe.x + PIPE_WIDTH < DOC_X) {
            setScore((s) => {
              const newScore = s + 1;
              if (newScore > highScore) {
                setHighScore(newScore);
                localStorage.setItem("flappydoc-highscore", newScore.toString());
              }
              return newScore;
            });
            return { ...pipe, passed: true };
          }
          return pipe;
        });

        // Remove off-screen pipes
        newPipes = newPipes.filter((pipe) => pipe.x + PIPE_WIDTH > -50);

        // Add new pipes
        const lastPipe = newPipes[newPipes.length - 1];
        if (!lastPipe || lastPipe.x < GAME_WIDTH - 180) {
          const minGapY = 60;
          const maxGapY = GAME_HEIGHT - PIPE_GAP - 60;
          newPipes.push({
            x: GAME_WIDTH,
            gapY: minGapY + Math.random() * (maxGapY - minGapY),
            passed: false,
          });
        }

        // Check collision with pipes
        const docRect = {
          left: DOC_X + 5,
          right: DOC_X + DOC_WIDTH - 5,
          top: docY + 5,
          bottom: docY + DOC_HEIGHT - 5,
        };

        for (const pipe of newPipes) {
          const pipeLeft = pipe.x;
          const pipeRight = pipe.x + PIPE_WIDTH;
          
          // Check if doc is in pipe's x range
          if (docRect.right > pipeLeft && docRect.left < pipeRight) {
            // Check if doc hits top or bottom pipe
            if (docRect.top < pipe.gapY || docRect.bottom > pipe.gapY + PIPE_GAP) {
              setGameState("gameOver");
              break;
            }
          }
        }

        return newPipes;
      });

      animationRef.current = requestAnimationFrame(gameLoop);
    };

    animationRef.current = requestAnimationFrame(gameLoop);
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [gameState, velocity, docY, highScore]);

  // Calculate doc rotation based on velocity
  const rotation = Math.min(Math.max(velocity * 3, -30), 90);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ backgroundColor: "rgba(0, 0, 0, 0.5)" }}
    >
      <div
        className="bg-white border-2 border-black max-w-md w-full"
        style={brutalShadow}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b-2 border-black">
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
            <h3 className="text-lg font-bold lowercase">flappydoc</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center border-2 border-black bg-white hover:bg-gray-100 font-bold"
          >
            ×
          </button>
        </div>

        {/* Score display */}
        <div className="flex justify-center gap-4 p-3 text-xs lowercase border-b-2 border-black">
          <div className="flex items-center gap-1 px-2 py-1 border border-black">
            <span className="font-bold">{score}</span>
            <span className="text-gray-600">score</span>
          </div>
          <div className="flex items-center gap-1 px-2 py-1 border border-black">
            <span className="font-bold">{highScore}</span>
            <span className="text-gray-600">best</span>
          </div>
        </div>

        {/* Game area */}
        <div className="p-4 flex justify-center">
          <div
            ref={gameAreaRef}
            onClick={jump}
            className="relative overflow-hidden border-2 border-black cursor-pointer select-none"
            style={{
              width: GAME_WIDTH,
              height: GAME_HEIGHT,
              backgroundColor: "#fafafa",
            }}
          >
            {/* Sky gradient background */}
            <div
              className="absolute inset-0"
              style={{
                background: "linear-gradient(180deg, #e8f4fc 0%, #ffffff 100%)",
              }}
            />

            {/* Ground */}
            <div
              className="absolute bottom-0 left-0 right-0 h-1 bg-black"
            />

            {/* Pipes */}
            {pipes.map((pipe, index) => (
              <div key={index}>
                {/* Top pipe */}
                <div
                  className="absolute"
                  style={{
                    left: pipe.x,
                    top: 0,
                    width: PIPE_WIDTH,
                    height: pipe.gapY,
                    backgroundColor: "black",
                    borderRight: "3px solid #F3787A",
                    borderBottom: "3px solid #F3787A",
                  }}
                />
                {/* Bottom pipe */}
                <div
                  className="absolute"
                  style={{
                    left: pipe.x,
                    top: pipe.gapY + PIPE_GAP,
                    width: PIPE_WIDTH,
                    height: GAME_HEIGHT - pipe.gapY - PIPE_GAP,
                    backgroundColor: "black",
                    borderRight: "3px solid #F3787A",
                    borderTop: "3px solid #F3787A",
                  }}
                />
              </div>
            ))}

            {/* Doc player */}
            <div
              className="absolute"
              style={{
                left: DOC_X,
                top: docY,
                zIndex: 10,
              }}
            >
              <DocPlayer rotation={rotation} />
            </div>

            {/* Ready state overlay */}
            {gameState === "ready" && (
              <div className="absolute inset-0 flex flex-col items-center justify-center bg-white/80">
                <div className="mb-4">
                  <DocPlayer rotation={0} />
                </div>
                <p className="text-sm font-bold lowercase">tap or press space</p>
                <p className="text-xs text-gray-500 lowercase mt-1">to start</p>
              </div>
            )}

            {/* Game over overlay */}
            {gameState === "gameOver" && (
              <div className="absolute inset-0 flex flex-col items-center justify-center bg-white/90">
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
                  onClick={(e) => {
                    e.stopPropagation();
                    resetGame();
                  }}
                  className="mt-2 px-4 py-2 bg-black text-white font-bold text-sm lowercase border-2 border-black hover:bg-gray-900"
                  style={brutalShadow}
                >
                  play again
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-3 border-t-2 border-black text-center">
          <p className="text-[10px] text-gray-400 lowercase">
            dodge the pipes, collect points
          </p>
        </div>
      </div>
    </div>
  );
}
