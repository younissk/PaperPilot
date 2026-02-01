import { useState, useEffect, useCallback } from "react";

// Brutalist coral shadow styles
const brutalShadow = { boxShadow: "3px 3px 0 #F3787A" };

// Document colors for the memory pairs - high contrast, distinct colors
const DOC_COLORS = [
  "#E11D48", // rose/red
  "#2563EB", // blue
  "#16A34A", // green
  "#9333EA", // purple
  "#EA580C", // orange
  "#0891B2", // cyan
];

interface Card {
  id: number;
  colorIndex: number;
  isFlipped: boolean;
  isMatched: boolean;
}

/**
 * Flat document SVG component - shows colored lines when revealed
 */
function ColoredDoc({ color, size = 48 }: { color: string; size?: number }) {
  const scale = size / 360;
  const strokeWidth = 20 * Math.max(scale, 0.5);
  return (
    <svg
      width={size}
      height={size * (460 / 360)}
      viewBox="0 0 360 460"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Document body with color fill */}
      <path
        d="M350 450H10V10H230L350 130V450Z"
        fill={color}
        fillOpacity={0.15}
      />
      {/* Document outline */}
      <path
        d="M350 450H10V10H230L350 130V450Z"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeMiterlimit="10"
        strokeLinecap="round"
      />
      {/* Folded corner */}
      <path
        d="M340 130H230V20"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeMiterlimit="10"
        strokeLinecap="round"
      />
      {/* Text lines with color */}
      <path d="M280 200H80V220H280V200Z" fill={color} />
      <path d="M280 320H80V340H280V320Z" fill={color} />
      <path d="M240 260H80V280H240V260Z" fill={color} />
    </svg>
  );
}

/**
 * Black document SVG for hidden cards - completely filled black
 */
function BlackDoc({ size = 48 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size * (460 / 360)}
      viewBox="0 0 360 460"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Document body - solid black fill */}
      <path
        d="M350 450H10V10H230L350 130V450Z"
        fill="black"
      />
      {/* Folded corner triangle */}
      <path
        d="M230 10L350 130H230V10Z"
        fill="#333"
      />
    </svg>
  );
}

/**
 * Single memory card component
 */
function MemoryCard({
  card,
  onClick,
  disabled,
}: {
  card: Card;
  onClick: () => void;
  disabled: boolean;
}) {
  const isRevealed = card.isFlipped || card.isMatched;
  const docSize = 56;

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled || card.isMatched}
      className={`
        p-1 bg-transparent
        transition-all duration-200 transform
        ${card.isMatched ? "opacity-50" : ""}
        ${!disabled && !card.isMatched ? "hover:scale-110 active:scale-95" : ""}
      `}
    >
      {isRevealed ? (
        <ColoredDoc color={DOC_COLORS[card.colorIndex]} size={docSize} />
      ) : (
        <BlackDoc size={docSize} />
      )}
    </button>
  );
}

interface MemoryGameProps {
  onClose: () => void;
  onBack?: () => void;
}

const NUM_PAIRS = 6; // Always 12 cards

/**
 * Memory matching game component
 */
export function MemoryGame({ onClose, onBack }: MemoryGameProps) {
  const [cards, setCards] = useState<Card[]>([]);
  const [flippedIndices, setFlippedIndices] = useState<number[]>([]);
  const [moves, setMoves] = useState(0);
  const [matches, setMatches] = useState(0);
  const [isChecking, setIsChecking] = useState(false);
  const [gameComplete, setGameComplete] = useState(false);

  const initializeGame = useCallback(() => {
    const colorIndices = Array.from({ length: NUM_PAIRS }, (_, i) => i % DOC_COLORS.length);
    
    // Create pairs
    const cardPairs: Card[] = [];
    colorIndices.forEach((colorIndex, pairIndex) => {
      cardPairs.push(
        { id: pairIndex * 2, colorIndex, isFlipped: false, isMatched: false },
        { id: pairIndex * 2 + 1, colorIndex, isFlipped: false, isMatched: false }
      );
    });

    // Shuffle cards
    for (let i = cardPairs.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [cardPairs[i], cardPairs[j]] = [cardPairs[j], cardPairs[i]];
    }

    setCards(cardPairs);
    setFlippedIndices([]);
    setMoves(0);
    setMatches(0);
    setIsChecking(false);
    setGameComplete(false);
  }, []);

  useEffect(() => {
    initializeGame();
  }, [initializeGame]);

  const handleCardClick = (index: number) => {
    if (isChecking || flippedIndices.includes(index) || cards[index].isMatched) {
      return;
    }

    const newFlipped = [...flippedIndices, index];
    setFlippedIndices(newFlipped);

    // Update card state
    setCards((prev) =>
      prev.map((card, i) => (i === index ? { ...card, isFlipped: true } : card))
    );

    if (newFlipped.length === 2) {
      setMoves((m) => m + 1);
      setIsChecking(true);

      const [first, second] = newFlipped;
      const isMatch = cards[first].colorIndex === cards[second].colorIndex;

      setTimeout(() => {
        if (isMatch) {
          setCards((prev) =>
            prev.map((card, i) =>
              i === first || i === second ? { ...card, isMatched: true } : card
            )
          );
          setMatches((m) => {
            const newMatches = m + 1;
            if (newMatches === NUM_PAIRS) {
              setGameComplete(true);
            }
            return newMatches;
          });
        } else {
          setCards((prev) =>
            prev.map((card, i) =>
              i === first || i === second ? { ...card, isFlipped: false } : card
            )
          );
        }
        setFlippedIndices([]);
        setIsChecking(false);
      }, 800);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ backgroundColor: "rgba(0, 0, 0, 0.5)" }}
    >
      <div
        className="bg-white border-2 border-black max-w-md w-full max-h-[90vh] overflow-auto"
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
            <h3 className="text-lg font-bold lowercase">memory game</h3>
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
        <div className="flex justify-center gap-4 p-3 text-xs lowercase border-b-2 border-black">
          <div className="flex items-center gap-1 px-2 py-1 border border-black">
            <span className="font-bold">{moves}</span>
            <span className="text-gray-600">moves</span>
          </div>
          <div className="flex items-center gap-1 px-2 py-1 border border-black">
            <span className="font-bold">{matches}</span>
            <span className="text-gray-600">/ {NUM_PAIRS} matched</span>
          </div>
        </div>

        {/* Game board */}
        <div className="p-4">
          {gameComplete ? (
            <div className="text-center py-8">
              <div className="text-2xl font-bold mb-2">🎉</div>
              <h4 className="text-lg font-bold lowercase mb-2">complete!</h4>
              <p className="text-sm text-gray-600 lowercase mb-4">
                you matched all pairs in {moves} moves
              </p>
              <button
                type="button"
                onClick={initializeGame}
                className="px-4 py-2 bg-black text-white font-bold text-sm lowercase border-2 border-black hover:bg-gray-900"
                style={brutalShadow}
              >
                play again
              </button>
            </div>
          ) : (
            <div
              className="grid gap-1 justify-items-center"
              style={{
                gridTemplateColumns: "repeat(4, auto)",
                justifyContent: "center",
              }}
            >
              {cards.map((card, index) => (
                <MemoryCard
                  key={card.id}
                  card={card}
                  onClick={() => handleCardClick(index)}
                  disabled={isChecking}
                />
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t-2 border-black text-center">
          <button
            type="button"
            onClick={initializeGame}
            className="text-xs text-gray-600 hover:text-black lowercase underline"
          >
            restart game
          </button>
          <p className="text-[10px] text-gray-400 mt-2 lowercase">
            colorblind? lol good luck
          </p>
        </div>
      </div>
    </div>
  );
}
