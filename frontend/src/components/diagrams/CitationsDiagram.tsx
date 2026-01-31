/**
 * Diagram showing paper with references (left) and citations (right).
 * Flat design, no card wrapper.
 */
export function CitationsDiagram() {
  return (
    <div
      className="my-4 py-2"
      role="img"
      aria-label="Diagram showing paper with references on left and citations on right"
    >
      <svg
        viewBox="0 0 400 120"
        className="w-full h-auto"
        style={{ maxHeight: "120px" }}
      >
        {/* References (left) */}
        <g>
          <rect
            x="20"
            y="10"
            width="80"
            height="22"
            fill="white"
            stroke="black"
            strokeWidth="1.5"
          />
          <text
            x="60"
            y="25"
            textAnchor="middle"
            className="text-[7px] fill-gray-600"
          >
            ref paper 1
          </text>
        </g>
        <g>
          <rect
            x="20"
            y="38"
            width="80"
            height="22"
            fill="white"
            stroke="black"
            strokeWidth="1.5"
          />
          <text
            x="60"
            y="53"
            textAnchor="middle"
            className="text-[7px] fill-gray-600"
          >
            ref paper 2
          </text>
        </g>
        <g>
          <rect
            x="20"
            y="66"
            width="80"
            height="22"
            fill="white"
            stroke="black"
            strokeWidth="1.5"
          />
          <text
            x="60"
            y="81"
            textAnchor="middle"
            className="text-[7px] fill-gray-600"
          >
            ref paper 3
          </text>
        </g>
        <text
          x="60"
          y="105"
          textAnchor="middle"
          className="text-[7px] fill-gray-400"
        >
          ← backward
        </text>

        {/* Arrows from refs to paper */}
        <g className="stroke-black" strokeWidth="1.5" fill="none">
          <path d="M 100 21 L 145 50" markerEnd="url(#arrow-cite)" />
          <path d="M 100 49 L 145 55" markerEnd="url(#arrow-cite)" />
          <path d="M 100 77 L 145 60" markerEnd="url(#arrow-cite)" />
        </g>

        {/* Animated dots - refs to paper */}
        <g>
          <circle r="3" fill="#F3787A">
            <animateMotion
              dur="4s"
              repeatCount="indefinite"
              path="M 100 21 L 145 50"
              begin="0s"
            />
          </circle>
          <circle r="3" fill="#F3787A">
            <animateMotion
              dur="4s"
              repeatCount="indefinite"
              path="M 100 49 L 145 55"
              begin="0.4s"
            />
          </circle>
          <circle r="3" fill="#F3787A">
            <animateMotion
              dur="4s"
              repeatCount="indefinite"
              path="M 100 77 L 145 60"
              begin="0.8s"
            />
          </circle>
        </g>

        {/* Center paper */}
        <g>
          <rect
            x="150"
            y="30"
            width="100"
            height="55"
            fill="black"
            stroke="black"
            strokeWidth="2"
          />
          <text
            x="200"
            y="55"
            textAnchor="middle"
            className="text-[9px] font-bold fill-white"
          >
            Seed Paper
          </text>
          <text
            x="200"
            y="70"
            textAnchor="middle"
            className="text-[7px] fill-gray-300"
          >
            current focus
          </text>
        </g>

        {/* Arrows from paper to cites */}
        <g className="stroke-black" strokeWidth="1.5" fill="none">
          <path d="M 250 50 L 295 21" markerEnd="url(#arrow-cite)" />
          <path d="M 250 55 L 295 49" markerEnd="url(#arrow-cite)" />
          <path d="M 250 60 L 295 77" markerEnd="url(#arrow-cite)" />
        </g>

        {/* Animated dots - paper to cites */}
        <g>
          <circle r="3" fill="#F3787A">
            <animateMotion
              dur="4s"
              repeatCount="indefinite"
              path="M 250 50 L 295 21"
              begin="2s"
            />
          </circle>
          <circle r="3" fill="#F3787A">
            <animateMotion
              dur="4s"
              repeatCount="indefinite"
              path="M 250 55 L 295 49"
              begin="2.4s"
            />
          </circle>
          <circle r="3" fill="#F3787A">
            <animateMotion
              dur="4s"
              repeatCount="indefinite"
              path="M 250 60 L 295 77"
              begin="2.8s"
            />
          </circle>
        </g>

        {/* Citations (right) */}
        <g>
          <rect
            x="300"
            y="10"
            width="80"
            height="22"
            fill="white"
            stroke="black"
            strokeWidth="1.5"
          />
          <text
            x="340"
            y="25"
            textAnchor="middle"
            className="text-[7px] fill-gray-600"
          >
            citing paper 1
          </text>
        </g>
        <g>
          <rect
            x="300"
            y="38"
            width="80"
            height="22"
            fill="white"
            stroke="black"
            strokeWidth="1.5"
          />
          <text
            x="340"
            y="53"
            textAnchor="middle"
            className="text-[7px] fill-gray-600"
          >
            citing paper 2
          </text>
        </g>
        <g>
          <rect
            x="300"
            y="66"
            width="80"
            height="22"
            fill="white"
            stroke="black"
            strokeWidth="1.5"
          />
          <text
            x="340"
            y="81"
            textAnchor="middle"
            className="text-[7px] fill-gray-600"
          >
            citing paper 3
          </text>
        </g>
        <text
          x="340"
          y="105"
          textAnchor="middle"
          className="text-[7px] fill-gray-400"
        >
          forward →
        </text>

        {/* Arrow marker */}
        <defs>
          <marker
            id="arrow-cite"
            markerWidth="5"
            markerHeight="5"
            refX="4"
            refY="2.5"
            orient="auto"
          >
            <path d="M 0 0 L 5 2.5 L 0 5 Z" fill="black" />
          </marker>
        </defs>
      </svg>
    </div>
  );
}
