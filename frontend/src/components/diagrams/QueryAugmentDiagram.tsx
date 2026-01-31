/**
 * Diagram showing query augmentation and search in OpenAlex/arXiv.
 * Flat design, no card wrapper.
 */
export function QueryAugmentDiagram() {
  return (
    <div
      className="my-4 py-2"
      role="img"
      aria-label="Diagram showing how a query is augmented into multiple search queries"
    >
      <svg
        viewBox="0 0 400 140"
        className="w-full h-auto"
        style={{ maxHeight: "140px" }}
      >
        {/* Query box */}
        <g>
          <rect
            x="10"
            y="50"
            width="70"
            height="40"
            fill="black"
            stroke="black"
            strokeWidth="2"
          />
          <text
            x="45"
            y="73"
            textAnchor="middle"
            className="text-[8px] font-bold fill-white"
          >
            query
          </text>
        </g>

        {/* Branching lines */}
        <g className="stroke-black" strokeWidth="1.5" fill="none">
          <path d="M 80 70 L 110 30" />
          <path d="M 80 70 L 110 70" />
          <path d="M 80 70 L 110 110" />
        </g>

        {/* Animated dots on branches */}
        <g>
          <circle r="3" fill="#F3787A">
            <animateMotion
              dur="3s"
              repeatCount="indefinite"
              path="M 80 70 L 110 30"
              begin="0s"
            />
          </circle>
          <circle r="3" fill="#F3787A">
            <animateMotion
              dur="3s"
              repeatCount="indefinite"
              path="M 80 70 L 110 70"
              begin="0.3s"
            />
          </circle>
          <circle r="3" fill="#F3787A">
            <animateMotion
              dur="3s"
              repeatCount="indefinite"
              path="M 80 70 L 110 110"
              begin="0.6s"
            />
          </circle>
        </g>

        {/* Augmented query variants */}
        <g>
          <rect
            x="115"
            y="15"
            width="70"
            height="30"
            fill="white"
            stroke="black"
            strokeWidth="1.5"
          />
          <text
            x="150"
            y="34"
            textAnchor="middle"
            className="text-[7px] fill-black"
          >
            surveys
          </text>
        </g>
        <g>
          <rect
            x="115"
            y="55"
            width="70"
            height="30"
            fill="white"
            stroke="black"
            strokeWidth="1.5"
          />
          <text
            x="150"
            y="74"
            textAnchor="middle"
            className="text-[7px] fill-black"
          >
            methods
          </text>
        </g>
        <g>
          <rect
            x="115"
            y="95"
            width="70"
            height="30"
            fill="white"
            stroke="black"
            strokeWidth="1.5"
          />
          <text
            x="150"
            y="114"
            textAnchor="middle"
            className="text-[7px] fill-black"
          >
            datasets
          </text>
        </g>

        {/* More indicator */}
        <text
          x="150"
          y="138"
          textAnchor="middle"
          className="text-[6px] fill-gray-400"
        >
          +3 more
        </text>

        {/* Lines to search APIs */}
        <g className="stroke-black" strokeWidth="1.5" fill="none">
          <path d="M 185 30 L 250 55" />
          <path d="M 185 70 L 250 70" />
          <path d="M 185 110 L 250 85" />
        </g>

        {/* Animated dots to APIs */}
        <g>
          <circle r="2.5" fill="#F3787A">
            <animateMotion
              dur="3s"
              repeatCount="indefinite"
              path="M 185 30 L 250 55"
              begin="1.2s"
            />
          </circle>
          <circle r="2.5" fill="#F3787A">
            <animateMotion
              dur="3s"
              repeatCount="indefinite"
              path="M 185 70 L 250 70"
              begin="1.4s"
            />
          </circle>
          <circle r="2.5" fill="#F3787A">
            <animateMotion
              dur="3s"
              repeatCount="indefinite"
              path="M 185 110 L 250 85"
              begin="1.6s"
            />
          </circle>
        </g>

        {/* Search APIs */}
        <g>
          <rect
            x="255"
            y="35"
            width="70"
            height="30"
            fill="white"
            stroke="black"
            strokeWidth="2"
          />
          <text
            x="290"
            y="54"
            textAnchor="middle"
            className="text-[8px] font-bold fill-black"
          >
            OpenAlex
          </text>
        </g>
        <g>
          <rect
            x="255"
            y="75"
            width="70"
            height="30"
            fill="white"
            stroke="black"
            strokeWidth="2"
          />
          <text
            x="290"
            y="94"
            textAnchor="middle"
            className="text-[8px] font-bold fill-black"
          >
            arXiv
          </text>
        </g>

        {/* Arrow to results */}
        <g>
          <path
            d="M 330 70 L 370 70"
            stroke="black"
            strokeWidth="2"
            fill="none"
            markerEnd="url(#arrow-augment)"
          />
        </g>

        {/* Results */}
        <g>
          <rect
            x="375"
            y="50"
            width="20"
            height="40"
            fill="#F3787A"
            stroke="black"
            strokeWidth="1"
          >
            <animate
              attributeName="opacity"
              values="0.6;1;0.6"
              dur="2s"
              repeatCount="indefinite"
            />
          </rect>
          <text
            x="385"
            y="75"
            textAnchor="middle"
            className="text-[6px] fill-white font-bold"
          >
            ↓
          </text>
        </g>

        {/* Arrow marker */}
        <defs>
          <marker
            id="arrow-augment"
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
