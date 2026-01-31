/**
 * Animated diagram showing query augmentation flow.
 * User query splits into profile (for filtering) and augmented variants (for search).
 */
export function QueryFlowDiagram() {
  return (
    <div
      className="my-8 p-4 border-2 border-black bg-white"
      style={{ boxShadow: "4px 4px 0 #F3787A" }}
      role="img"
      aria-label="Diagram showing how a user query is augmented into multiple search queries"
    >
      <svg
        viewBox="0 0 400 220"
        className="w-full h-auto"
        style={{ maxHeight: "220px" }}
      >
        {/* Connection lines - drawn with animation */}
        <g className="stroke-black" strokeWidth="2" fill="none">
          {/* Query to Profile */}
          <path
            d="M 80 50 Q 120 30, 160 40"
            strokeDasharray="100"
            className="animate-stroke-draw"
            style={{ animationDelay: "0.2s" }}
          />
          {/* Query to Augment */}
          <path
            d="M 80 50 Q 120 70, 160 80"
            strokeDasharray="100"
            className="animate-stroke-draw"
            style={{ animationDelay: "0.4s" }}
          />
          {/* Augment to variants */}
          <path
            d="M 240 80 L 280 120"
            strokeDasharray="100"
            className="animate-stroke-draw"
            style={{ animationDelay: "0.8s" }}
          />
          <path
            d="M 240 80 L 320 120"
            strokeDasharray="100"
            className="animate-stroke-draw"
            style={{ animationDelay: "1s" }}
          />
          <path
            d="M 240 80 L 360 120"
            strokeDasharray="100"
            className="animate-stroke-draw"
            style={{ animationDelay: "1.2s" }}
          />
        </g>

        {/* Traveling pulse dots */}
        <g>
          {/* Dot traveling to Profile */}
          <circle r="4" fill="#F3787A" className="animate-pulse-dot">
            <animateMotion
              dur="4s"
              repeatCount="indefinite"
              path="M 80 50 Q 120 30, 160 40"
              begin="0s"
            />
          </circle>
          {/* Dot traveling to Augment */}
          <circle r="4" fill="#F3787A" className="animate-pulse-dot">
            <animateMotion
              dur="4s"
              repeatCount="indefinite"
              path="M 80 50 Q 120 70, 160 80"
              begin="0.3s"
            />
          </circle>
          {/* Dots traveling to variants */}
          <circle r="3" fill="#F3787A" className="animate-pulse-dot">
            <animateMotion
              dur="4s"
              repeatCount="indefinite"
              path="M 240 80 L 280 140"
              begin="1.5s"
            />
          </circle>
          <circle r="3" fill="#F3787A" className="animate-pulse-dot">
            <animateMotion
              dur="4s"
              repeatCount="indefinite"
              path="M 240 80 L 320 140"
              begin="1.7s"
            />
          </circle>
          <circle r="3" fill="#F3787A" className="animate-pulse-dot">
            <animateMotion
              dur="4s"
              repeatCount="indefinite"
              path="M 240 80 L 360 140"
              begin="1.9s"
            />
          </circle>
        </g>

        {/* User Query Node */}
        <g className="animate-fade-in" style={{ animationDelay: "0s" }}>
          <rect
            x="10"
            y="30"
            width="70"
            height="40"
            fill="white"
            stroke="black"
            strokeWidth="2"
          />
          <rect
            x="12"
            y="32"
            width="70"
            height="40"
            fill="none"
            stroke="#F3787A"
            strokeWidth="1"
            opacity="0.3"
          />
          <text
            x="45"
            y="48"
            textAnchor="middle"
            className="text-[8px] font-bold fill-black"
          >
            query
          </text>
          <text
            x="45"
            y="60"
            textAnchor="middle"
            className="text-[6px] fill-gray-500"
          >
            "LLMs in medicine"
          </text>
        </g>

        {/* Profile Node */}
        <g className="animate-fade-in" style={{ animationDelay: "0.3s" }}>
          <rect
            x="160"
            y="20"
            width="80"
            height="35"
            fill="white"
            stroke="black"
            strokeWidth="2"
          />
          <text
            x="200"
            y="35"
            textAnchor="middle"
            className="text-[8px] font-bold fill-black"
          >
            profile
          </text>
          <text
            x="200"
            y="47"
            textAnchor="middle"
            className="text-[6px] fill-gray-500"
          >
            (for filtering)
          </text>
        </g>

        {/* Augment Node */}
        <g className="animate-fade-in" style={{ animationDelay: "0.5s" }}>
          <rect
            x="160"
            y="60"
            width="80"
            height="35"
            fill="black"
            stroke="black"
            strokeWidth="2"
          />
          <text
            x="200"
            y="75"
            textAnchor="middle"
            className="text-[8px] font-bold fill-white"
          >
            augment
          </text>
          <text
            x="200"
            y="87"
            textAnchor="middle"
            className="text-[6px] fill-gray-300"
          >
            LLM expansion
          </text>
        </g>

        {/* Search Variant Nodes */}
        <g className="animate-fade-in" style={{ animationDelay: "0.9s" }}>
          {/* Survey */}
          <rect
            x="255"
            y="130"
            width="50"
            height="30"
            fill="white"
            stroke="black"
            strokeWidth="2"
          />
          <text
            x="280"
            y="148"
            textAnchor="middle"
            className="text-[7px] fill-black"
          >
            surveys
          </text>
        </g>

        <g className="animate-fade-in" style={{ animationDelay: "1.1s" }}>
          {/* Methods */}
          <rect
            x="310"
            y="130"
            width="50"
            height="30"
            fill="white"
            stroke="black"
            strokeWidth="2"
          />
          <text
            x="335"
            y="148"
            textAnchor="middle"
            className="text-[7px] fill-black"
          >
            methods
          </text>
        </g>

        <g className="animate-fade-in" style={{ animationDelay: "1.3s" }}>
          {/* Datasets */}
          <rect
            x="365"
            y="130"
            width="50"
            height="30"
            fill="white"
            stroke="black"
            strokeWidth="2"
          />
          <text
            x="390"
            y="148"
            textAnchor="middle"
            className="text-[7px] fill-black"
          >
            datasets
          </text>
        </g>

        {/* More variants indicator */}
        <text
          x="335"
          y="180"
          textAnchor="middle"
          className="text-[8px] fill-gray-400 animate-fade-in"
          style={{ animationDelay: "1.5s" }}
        >
          + 3 more variants
        </text>

        {/* Arrows */}
        <defs>
          <marker
            id="arrowhead"
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

      <p className="text-xs text-gray-500 text-center mt-2 lowercase">
        query augmentation: one question becomes many searches
      </p>
    </div>
  );
}
