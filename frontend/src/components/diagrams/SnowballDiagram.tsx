/**
 * Animated diagram showing snowball/citation expansion.
 * Seed papers expand outward via references and citations in waves.
 */
export function SnowballDiagram() {
  return (
    <div
      className="my-8 p-4 border-2 border-black bg-white"
      style={{ boxShadow: "4px 4px 0 #F3787A" }}
      role="img"
      aria-label="Diagram showing how papers expand through citation snowballing"
    >
      <svg
        viewBox="0 0 400 200"
        className="w-full h-auto"
        style={{ maxHeight: "200px" }}
      >
        {/* Iteration labels */}
        <text x="50" y="20" className="text-[9px] font-bold fill-gray-400">
          seed
        </text>
        <text x="150" y="20" className="text-[9px] font-bold fill-gray-400">
          iteration 1
        </text>
        <text x="280" y="20" className="text-[9px] font-bold fill-gray-400">
          iteration 2
        </text>

        {/* Connection lines */}
        <g className="stroke-black" strokeWidth="1.5" fill="none">
          {/* Seed to refs/cites */}
          <path d="M 70 70 L 130 50" strokeDasharray="4,2" />
          <path d="M 70 70 L 130 90" strokeDasharray="4,2" />
          
          {/* Refs to more */}
          <path d="M 190 50 L 250 40" strokeDasharray="4,2" />
          <path d="M 190 50 L 250 60" strokeDasharray="4,2" />
          
          {/* Cites to more */}
          <path d="M 190 90 L 250 100" strokeDasharray="4,2" />
          
          {/* To filter */}
          <path d="M 250 100 L 320 130" strokeDasharray="4,2" />
          <path d="M 250 60 L 320 130" strokeDasharray="4,2" />
        </g>

        {/* Animated pulse waves */}
        <g>
          {/* Wave 1: Seed to expansion */}
          <circle r="3" fill="#F3787A" opacity="0.8">
            <animateMotion
              dur="5s"
              repeatCount="indefinite"
              path="M 70 70 L 130 50"
              begin="0s"
            />
          </circle>
          <circle r="3" fill="#F3787A" opacity="0.8">
            <animateMotion
              dur="5s"
              repeatCount="indefinite"
              path="M 70 70 L 130 90"
              begin="0.2s"
            />
          </circle>
          
          {/* Wave 2: Further expansion */}
          <circle r="2.5" fill="#F3787A" opacity="0.7">
            <animateMotion
              dur="5s"
              repeatCount="indefinite"
              path="M 190 50 L 250 40"
              begin="1.5s"
            />
          </circle>
          <circle r="2.5" fill="#F3787A" opacity="0.7">
            <animateMotion
              dur="5s"
              repeatCount="indefinite"
              path="M 190 90 L 250 100"
              begin="1.7s"
            />
          </circle>
          
          {/* Wave 3: To filter */}
          <circle r="2" fill="#F3787A" opacity="0.6">
            <animateMotion
              dur="5s"
              repeatCount="indefinite"
              path="M 250 100 L 320 130"
              begin="3s"
            />
          </circle>
        </g>

        {/* Seed Papers - center node with glow */}
        <g>
          <rect
            x="30"
            y="50"
            width="60"
            height="40"
            fill="black"
            stroke="black"
            strokeWidth="2"
          >
            <animate
              attributeName="opacity"
              values="1;0.7;1"
              dur="3s"
              repeatCount="indefinite"
            />
          </rect>
          <text
            x="60"
            y="68"
            textAnchor="middle"
            className="text-[8px] font-bold fill-white"
          >
            seed
          </text>
          <text
            x="60"
            y="80"
            textAnchor="middle"
            className="text-[7px] fill-gray-300"
          >
            papers
          </text>
        </g>

        {/* References node */}
        <g>
          <rect
            x="120"
            y="35"
            width="70"
            height="30"
            fill="white"
            stroke="black"
            strokeWidth="2"
          />
          <text
            x="155"
            y="50"
            textAnchor="middle"
            className="text-[7px] fill-black"
          >
            references
          </text>
          <text
            x="155"
            y="60"
            textAnchor="middle"
            className="text-[6px] fill-gray-500"
          >
            ← backward
          </text>
        </g>

        {/* Citations node */}
        <g>
          <rect
            x="120"
            y="75"
            width="70"
            height="30"
            fill="white"
            stroke="black"
            strokeWidth="2"
          />
          <text
            x="155"
            y="90"
            textAnchor="middle"
            className="text-[7px] fill-black"
          >
            citations
          </text>
          <text
            x="155"
            y="100"
            textAnchor="middle"
            className="text-[6px] fill-gray-500"
          >
            forward →
          </text>
        </g>

        {/* Iteration 2 expanded papers */}
        <g>
          <rect
            x="230"
            y="30"
            width="50"
            height="25"
            fill="white"
            stroke="black"
            strokeWidth="1.5"
            opacity="0.9"
          />
          <text
            x="255"
            y="46"
            textAnchor="middle"
            className="text-[6px] fill-gray-600"
          >
            +refs
          </text>
        </g>
        <g>
          <rect
            x="230"
            y="60"
            width="50"
            height="25"
            fill="white"
            stroke="black"
            strokeWidth="1.5"
            opacity="0.9"
          />
          <text
            x="255"
            y="76"
            textAnchor="middle"
            className="text-[6px] fill-gray-600"
          >
            +cites
          </text>
        </g>
        <g>
          <rect
            x="230"
            y="90"
            width="50"
            height="25"
            fill="white"
            stroke="black"
            strokeWidth="1.5"
            opacity="0.9"
          />
          <text
            x="255"
            y="106"
            textAnchor="middle"
            className="text-[6px] fill-gray-600"
          >
            +more
          </text>
        </g>

        {/* LLM Filter node */}
        <g>
          <rect
            x="300"
            y="120"
            width="70"
            height="35"
            fill="black"
            stroke="black"
            strokeWidth="2"
          >
            <animate
              attributeName="opacity"
              values="1;0.8;1"
              dur="2s"
              repeatCount="indefinite"
              begin="3.5s"
            />
          </rect>
          <text
            x="335"
            y="137"
            textAnchor="middle"
            className="text-[8px] font-bold fill-white"
          >
            LLM filter
          </text>
          <text
            x="335"
            y="149"
            textAnchor="middle"
            className="text-[6px] fill-gray-300"
          >
            relevance check
          </text>
        </g>

        {/* Accepted papers indicator */}
        <g>
          <text
            x="335"
            y="175"
            textAnchor="middle"
            className="text-[7px] fill-gray-500"
          >
            ↓ accepted
          </text>
          <rect
            x="310"
            y="180"
            width="50"
            height="15"
            fill="#F3787A"
            stroke="black"
            strokeWidth="1"
            rx="2"
          >
            <animate
              attributeName="opacity"
              values="0.5;1;0.5"
              dur="2s"
              repeatCount="indefinite"
              begin="4s"
            />
          </rect>
        </g>
      </svg>

      <p className="text-xs text-gray-500 text-center mt-2 lowercase">
        snowballing: follow citations to discover more relevant papers
      </p>
    </div>
  );
}
