import { useEffect, useState } from "react";

/**
 * Animated diagram showing ELO tournament ranking.
 * Papers compete head-to-head, LLM judges, Elo scores update.
 */
export function EloBracketDiagram() {
  const [phase, setPhase] = useState(0);
  
  // Cycle through animation phases: 0=idle, 1=judging, 2=result
  useEffect(() => {
    const interval = setInterval(() => {
      setPhase((prev) => (prev + 1) % 4);
    }, 1500);
    return () => clearInterval(interval);
  }, []);

  // Elo values change based on phase
  const eloA = phase >= 3 ? "1520" : "1500";
  const eloB = phase >= 3 ? "1480" : "1500";
  const winnerA = phase >= 3;

  return (
    <div
      className="my-4 py-2"
      role="img"
      aria-label="Diagram showing ELO ranking tournament between papers"
    >
      <svg
        viewBox="0 0 400 180"
        className="w-full h-auto"
        style={{ maxHeight: "180px" }}
      >
        {/* Paper A */}
        <g
          style={{
            filter: phase === 1 || winnerA ? "drop-shadow(0 0 6px rgba(243,120,122,0.8))" : "none",
            transition: "filter 0.3s ease",
          }}
        >
          <rect
            x="30"
            y="30"
            width="100"
            height="50"
            fill={winnerA ? "#F3787A" : "white"}
            stroke="black"
            strokeWidth="2"
            style={{ transition: "fill 0.3s ease" }}
          />
          <text
            x="80"
            y="52"
            textAnchor="middle"
            className="text-[9px] font-bold"
            fill={winnerA ? "white" : "black"}
          >
            Paper A
          </text>
          <text
            x="80"
            y="68"
            textAnchor="middle"
            className="text-[10px] font-mono font-bold"
            fill={winnerA ? "white" : "#F3787A"}
          >
            {eloA}
          </text>
        </g>

        {/* Paper B */}
        <g
          style={{
            filter: phase === 1 ? "drop-shadow(0 0 6px rgba(243,120,122,0.8))" : "none",
            transition: "filter 0.3s ease",
          }}
        >
          <rect
            x="30"
            y="100"
            width="100"
            height="50"
            fill="white"
            stroke="black"
            strokeWidth="2"
          />
          <text
            x="80"
            y="122"
            textAnchor="middle"
            className="text-[9px] font-bold fill-black"
          >
            Paper B
          </text>
          <text
            x="80"
            y="138"
            textAnchor="middle"
            className="text-[10px] font-mono font-bold"
            fill="#F3787A"
          >
            {eloB}
          </text>
        </g>

        {/* Connection lines to judge */}
        <g className="stroke-black" strokeWidth="1.5" fill="none">
          <path d="M 130 55 L 170 90" />
          <path d="M 130 125 L 170 90" />
        </g>

        {/* Animated dots traveling to judge */}
        {phase === 1 && (
          <>
            <circle r="4" fill="#F3787A">
              <animateMotion
                dur="0.8s"
                repeatCount="1"
                path="M 130 55 L 170 90"
              />
            </circle>
            <circle r="4" fill="#F3787A">
              <animateMotion
                dur="0.8s"
                repeatCount="1"
                path="M 130 125 L 170 90"
              />
            </circle>
          </>
        )}

        {/* LLM Judge */}
        <g
          style={{
            filter: phase === 2 ? "drop-shadow(0 0 8px rgba(0,0,0,0.5))" : "none",
            transition: "filter 0.3s ease",
          }}
        >
          <rect
            x="170"
            y="65"
            width="70"
            height="50"
            fill="black"
            stroke="black"
            strokeWidth="2"
          />
          <text
            x="205"
            y="85"
            textAnchor="middle"
            className="text-[9px] font-bold fill-white"
          >
            LLM
          </text>
          <text
            x="205"
            y="100"
            textAnchor="middle"
            className="text-[8px] fill-gray-300"
          >
            judge
          </text>
          {/* Thinking indicator */}
          {phase === 2 && (
            <g>
              <circle cx="190" cy="108" r="2" fill="#F3787A">
                <animate
                  attributeName="opacity"
                  values="0;1;0"
                  dur="0.6s"
                  repeatCount="indefinite"
                />
              </circle>
              <circle cx="205" cy="108" r="2" fill="#F3787A">
                <animate
                  attributeName="opacity"
                  values="0;1;0"
                  dur="0.6s"
                  repeatCount="indefinite"
                  begin="0.2s"
                />
              </circle>
              <circle cx="220" cy="108" r="2" fill="#F3787A">
                <animate
                  attributeName="opacity"
                  values="0;1;0"
                  dur="0.6s"
                  repeatCount="indefinite"
                  begin="0.4s"
                />
              </circle>
            </g>
          )}
        </g>

        {/* Result arrow */}
        {phase >= 3 && (
          <g className="animate-fade-in">
            <path
              d="M 240 90 L 280 90"
              stroke="black"
              strokeWidth="2"
              fill="none"
              markerEnd="url(#arrowhead-elo)"
            />
          </g>
        )}

        {/* Winner indicator */}
        {phase >= 3 && (
          <g className="animate-fade-in">
            <text
              x="310"
              y="85"
              textAnchor="start"
              className="text-[10px] font-bold fill-black"
            >
              winner:
            </text>
            <text
              x="310"
              y="100"
              textAnchor="start"
              className="text-[9px] fill-gray-600"
            >
              Paper A +20
            </text>
          </g>
        )}

        {/* Process labels */}
        <text
          x="80"
          y="170"
          textAnchor="middle"
          className="text-[8px] fill-gray-400"
        >
          head-to-head
        </text>
        <text
          x="205"
          y="170"
          textAnchor="middle"
          className="text-[8px] fill-gray-400"
        >
          comparison
        </text>
        <text
          x="330"
          y="170"
          textAnchor="middle"
          className="text-[8px] fill-gray-400"
        >
          elo update
        </text>

        {/* Swiss pairing indicator */}
        <g>
          <rect
            x="280"
            y="30"
            width="90"
            height="35"
            fill="white"
            stroke="black"
            strokeWidth="1"
            strokeDasharray="4,2"
          />
          <text
            x="325"
            y="45"
            textAnchor="middle"
            className="text-[7px] fill-gray-600"
          >
            swiss pairing
          </text>
          <text
            x="325"
            y="57"
            textAnchor="middle"
            className="text-[6px] fill-gray-400"
          >
            similar elo = better match
          </text>
        </g>

        {/* Arrow marker definition */}
        <defs>
          <marker
            id="arrowhead-elo"
            markerWidth="6"
            markerHeight="6"
            refX="5"
            refY="3"
            orient="auto"
          >
            <path d="M 0 0 L 6 3 L 0 6 Z" fill="black" />
          </marker>
        </defs>
      </svg>
    </div>
  );
}
