/**
 * Simple diagram showing query → profile transformation.
 * Flat design, no card wrapper.
 */
export function QueryProfileDiagram() {
  return (
    <div
      className="my-4 py-2"
      role="img"
      aria-label="Diagram showing how a user query becomes a query profile"
    >
      <svg
        viewBox="0 0 380 100"
        className="w-full h-auto"
        style={{ maxHeight: "100px" }}
      >
        {/* Query box */}
        <g>
          <rect
            x="10"
            y="25"
            width="100"
            height="50"
            fill="white"
            stroke="black"
            strokeWidth="2"
          />
          <text
            x="60"
            y="45"
            textAnchor="middle"
            className="text-[9px] font-bold fill-black"
          >
            query
          </text>
          <text
            x="60"
            y="60"
            textAnchor="middle"
            className="text-[7px] fill-gray-500"
          >
            "LLMs in medicine"
          </text>
        </g>

        {/* Arrow with LLM label */}
        <g>
          <path
            d="M 115 50 L 175 50"
            stroke="black"
            strokeWidth="2"
            fill="none"
            markerEnd="url(#arrow-profile)"
          />
          <rect
            x="125"
            y="35"
            width="40"
            height="18"
            fill="black"
            rx="2"
          />
          <text
            x="145"
            y="47"
            textAnchor="middle"
            className="text-[7px] font-bold fill-white"
          >
            LLM
          </text>
        </g>

        {/* Profile box */}
        <g>
          <rect
            x="180"
            y="10"
            width="190"
            height="80"
            fill="white"
            stroke="black"
            strokeWidth="2"
          />
          <text
            x="275"
            y="28"
            textAnchor="middle"
            className="text-[9px] font-bold fill-black"
          >
            query profile
          </text>
          <line x1="190" y1="35" x2="360" y2="35" stroke="black" strokeWidth="1" />
          
          {/* Profile details */}
          <text x="195" y="50" className="text-[7px] fill-gray-600">
            required: LLM, healthcare, clinical
          </text>
          <text x="195" y="62" className="text-[7px] fill-gray-600">
            optional: diagnosis, treatment
          </text>
          <text x="195" y="74" className="text-[7px] fill-gray-600">
            exclude: gaming, entertainment
          </text>
        </g>

        {/* Arrow marker */}
        <defs>
          <marker
            id="arrow-profile"
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
