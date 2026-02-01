import { useEffect, useState } from "react";

/**
 * Animated Elo leaderboard table showing papers with W/L/Elo.
 * Flat design, no card wrapper.
 */
export function EloTableDiagram() {
  const [tick, setTick] = useState(0);

  // Cycle through states to animate Elo changes
  useEffect(() => {
    const interval = setInterval(() => {
      setTick((prev) => (prev + 1) % 3);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  // Elo values change based on tick
  const eloValues = [
    { elo: 1540, w: 5, l: 2 },
    { elo: 1510, w: 4, l: 3 },
    { elo: 1470, w: 2, l: 4 },
  ];

  const eloChanges = [
    [1540, 1552, 1548],
    [1510, 1498, 1510],
    [1470, 1470, 1462],
  ];

  return (
    <div
      className="my-4 py-2"
      role="img"
      aria-label="Elo leaderboard table showing paper rankings"
    >
      <svg
        viewBox="0 0 380 130"
        className="w-full h-auto"
        style={{ maxHeight: "130px" }}
      >
        {/* Table header */}
        <g>
          <rect
            x="20"
            y="10"
            width="340"
            height="25"
            fill="black"
            stroke="black"
            strokeWidth="2"
          />
          <text
            x="30"
            y="27"
            textAnchor="start"
            className="text-[9px] font-bold fill-white"
          >
            Paper
          </text>
          <text
            x="280"
            y="27"
            textAnchor="middle"
            className="text-[9px] font-bold fill-white"
          >
            W
          </text>
          <text
            x="310"
            y="27"
            textAnchor="middle"
            className="text-[9px] font-bold fill-white"
          >
            L
          </text>
          <text
            x="345"
            y="27"
            textAnchor="middle"
            className="text-[9px] font-bold fill-white"
          >
            Elo
          </text>
        </g>

        {/* Row 1 - Paper A (winner) */}
        <g>
          <rect
            x="20"
            y="35"
            width="340"
            height="28"
            fill={tick === 1 ? "#F3787A20" : "white"}
            stroke="black"
            strokeWidth="1.5"
            style={{ transition: "fill 0.3s ease" }}
          />
          <text
            x="30"
            y="53"
            textAnchor="start"
            className="text-[8px] fill-gray-700"
          >
            Attention Is All You Need
          </text>
          <text
            x="280"
            y="53"
            textAnchor="middle"
            className="text-[8px] fill-gray-700"
          >
            {eloValues[0].w + (tick >= 1 ? 1 : 0)}
          </text>
          <text
            x="310"
            y="53"
            textAnchor="middle"
            className="text-[8px] fill-gray-700"
          >
            {eloValues[0].l}
          </text>
          <text
            x="345"
            y="53"
            textAnchor="middle"
            className="text-[10px] font-mono font-bold"
            fill="#F3787A"
          >
            {eloChanges[0][tick]}
          </text>
        </g>

        {/* Row 2 - Paper B */}
        <g>
          <rect
            x="20"
            y="63"
            width="340"
            height="28"
            fill={tick === 1 ? "#ff000010" : "white"}
            stroke="black"
            strokeWidth="1.5"
            style={{ transition: "fill 0.3s ease" }}
          />
          <text
            x="30"
            y="81"
            textAnchor="start"
            className="text-[8px] fill-gray-700"
          >
            BERT: Pre-training of Deep Bidirectional...
          </text>
          <text
            x="280"
            y="81"
            textAnchor="middle"
            className="text-[8px] fill-gray-700"
          >
            {eloValues[1].w}
          </text>
          <text
            x="310"
            y="81"
            textAnchor="middle"
            className="text-[8px] fill-gray-700"
          >
            {eloValues[1].l + (tick >= 1 ? 1 : 0)}
          </text>
          <text
            x="345"
            y="81"
            textAnchor="middle"
            className="text-[10px] font-mono font-bold"
            fill="#F3787A"
          >
            {eloChanges[1][tick]}
          </text>
        </g>

        {/* Row 3 - Paper C */}
        <g>
          <rect
            x="20"
            y="91"
            width="340"
            height="28"
            fill={tick === 2 ? "#ff000010" : "white"}
            stroke="black"
            strokeWidth="1.5"
            style={{ transition: "fill 0.3s ease" }}
          />
          <text
            x="30"
            y="109"
            textAnchor="start"
            className="text-[8px] fill-gray-700"
          >
            GPT-4 Technical Report
          </text>
          <text
            x="280"
            y="109"
            textAnchor="middle"
            className="text-[8px] fill-gray-700"
          >
            {eloValues[2].w}
          </text>
          <text
            x="310"
            y="109"
            textAnchor="middle"
            className="text-[8px] fill-gray-700"
          >
            {eloValues[2].l + (tick >= 2 ? 1 : 0)}
          </text>
          <text
            x="345"
            y="109"
            textAnchor="middle"
            className="text-[10px] font-mono font-bold"
            fill="#F3787A"
          >
            {eloChanges[2][tick]}
          </text>
        </g>

        {/* Update indicator */}
        {tick > 0 && (
          <g className="animate-fade-in">
            <text
              x="345"
              y="125"
              textAnchor="middle"
              className="text-[6px] fill-gray-400"
            >
              updating...
            </text>
          </g>
        )}
      </svg>
    </div>
  );
}
