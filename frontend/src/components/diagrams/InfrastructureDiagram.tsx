/**
 * Infrastructure diagram showing Azure cloud architecture.
 * Brutalist SVG design matching existing diagrams.
 */
export function InfrastructureDiagram() {
  return (
    <div
      className="my-6 py-4"
      role="img"
      aria-label="Diagram showing PaperPilot's Azure cloud infrastructure"
    >
      <svg
        viewBox="0 0 700 320"
        className="w-full h-auto"
        style={{ maxHeight: "320px" }}
      >
        {/* Definitions */}
        <defs>
          <marker
            id="arrow-infra"
            markerWidth="8"
            markerHeight="8"
            refX="7"
            refY="4"
            orient="auto"
          >
            <path d="M 0 0 L 8 4 L 0 8 Z" fill="black" />
          </marker>
          <marker
            id="arrow-infra-gray"
            markerWidth="8"
            markerHeight="8"
            refX="7"
            refY="4"
            orient="auto"
          >
            <path d="M 0 0 L 8 4 L 0 8 Z" fill="#9CA3AF" />
          </marker>
        </defs>

        {/* Background regions */}
        {/* User region */}
        <rect
          x="10"
          y="10"
          width="100"
          height="300"
          fill="#F9FAFB"
          stroke="#E5E7EB"
          strokeWidth="1"
          strokeDasharray="4"
        />
        <text x="60" y="30" textAnchor="middle" className="text-[8px] fill-gray-400 uppercase">
          user
        </text>

        {/* Azure region */}
        <rect
          x="130"
          y="10"
          width="560"
          height="300"
          fill="#EFF6FF"
          stroke="#BFDBFE"
          strokeWidth="1"
          strokeDasharray="4"
        />
        <text x="410" y="30" textAnchor="middle" className="text-[8px] fill-blue-400 uppercase">
          azure cloud
        </text>

        {/* User/Browser */}
        <g>
          <rect
            x="30"
            y="120"
            width="60"
            height="60"
            fill="white"
            stroke="black"
            strokeWidth="2"
          />
          <text x="60" y="145" textAnchor="middle" className="text-[9px] font-bold fill-black">
            browser
          </text>
          <text x="60" y="160" textAnchor="middle" className="text-[7px] fill-gray-500">
            user
          </text>
          {/* Browser icon */}
          <circle cx="60" cy="195" r="12" fill="none" stroke="black" strokeWidth="1.5" />
          <circle cx="60" cy="195" r="4" fill="black" />
        </g>

        {/* Static Web App (Frontend) */}
        <g>
          <rect
            x="150"
            y="100"
            width="100"
            height="70"
            fill="white"
            stroke="black"
            strokeWidth="2"
          />
          <rect x="150" y="100" width="100" height="20" fill="black" />
          <text x="200" y="114" textAnchor="middle" className="text-[8px] font-bold fill-white">
            static web app
          </text>
          <text x="200" y="138" textAnchor="middle" className="text-[9px] font-bold fill-black">
            frontend
          </text>
          <text x="200" y="155" textAnchor="middle" className="text-[7px] fill-gray-500">
            react + vite
          </text>
        </g>

        {/* Arrow: Browser → Frontend */}
        <path
          d="M 95 150 L 145 150"
          stroke="black"
          strokeWidth="2"
          fill="none"
          markerEnd="url(#arrow-infra)"
        />
        <text x="120" y="143" textAnchor="middle" className="text-[6px] fill-gray-500">
          HTTPS
        </text>

        {/* Function App (API) */}
        <g>
          <rect
            x="300"
            y="100"
            width="100"
            height="70"
            fill="white"
            stroke="black"
            strokeWidth="2"
          />
          <rect x="300" y="100" width="100" height="20" fill="black" />
          <text x="350" y="114" textAnchor="middle" className="text-[8px] font-bold fill-white">
            function app
          </text>
          <text x="350" y="138" textAnchor="middle" className="text-[9px] font-bold fill-black">
            api
          </text>
          <text x="350" y="155" textAnchor="middle" className="text-[7px] fill-gray-500">
            python (serverless)
          </text>
        </g>

        {/* Arrow: Frontend → API */}
        <path
          d="M 255 135 L 295 135"
          stroke="black"
          strokeWidth="2"
          fill="none"
          markerEnd="url(#arrow-infra)"
        />
        <text x="275" y="128" textAnchor="middle" className="text-[6px] fill-gray-500">
          REST
        </text>

        {/* Service Bus */}
        <g>
          <rect
            x="450"
            y="100"
            width="100"
            height="70"
            fill="white"
            stroke="black"
            strokeWidth="2"
          />
          <rect x="450" y="100" width="100" height="20" fill="#F3787A" />
          <text x="500" y="114" textAnchor="middle" className="text-[8px] font-bold fill-white">
            service bus
          </text>
          <text x="500" y="138" textAnchor="middle" className="text-[9px] font-bold fill-black">
            queue
          </text>
          <text x="500" y="155" textAnchor="middle" className="text-[7px] fill-gray-500">
            async jobs
          </text>
        </g>

        {/* Arrow: API → Service Bus */}
        <path
          d="M 405 135 L 445 135"
          stroke="black"
          strokeWidth="2"
          fill="none"
          markerEnd="url(#arrow-infra)"
        />
        <text x="425" y="128" textAnchor="middle" className="text-[6px] fill-gray-500">
          enqueue
        </text>

        {/* Worker (consuming from queue) */}
        <g>
          <rect
            x="580"
            y="100"
            width="90"
            height="70"
            fill="white"
            stroke="black"
            strokeWidth="2"
          />
          <rect x="580" y="100" width="90" height="20" fill="black" />
          <text x="625" y="114" textAnchor="middle" className="text-[8px] font-bold fill-white">
            function app
          </text>
          <text x="625" y="138" textAnchor="middle" className="text-[9px] font-bold fill-black">
            worker
          </text>
          <text x="625" y="155" textAnchor="middle" className="text-[7px] fill-gray-500">
            pipeline jobs
          </text>
        </g>

        {/* Arrow: Service Bus → Worker */}
        <path
          d="M 555 135 L 575 135"
          stroke="black"
          strokeWidth="2"
          fill="none"
          markerEnd="url(#arrow-infra)"
        />

        {/* Cosmos DB */}
        <g>
          <rect
            x="450"
            y="220"
            width="100"
            height="70"
            fill="white"
            stroke="black"
            strokeWidth="2"
          />
          <rect x="450" y="220" width="100" height="20" fill="black" />
          <text x="500" y="234" textAnchor="middle" className="text-[8px] font-bold fill-white">
            cosmos db
          </text>
          <text x="500" y="258" textAnchor="middle" className="text-[9px] font-bold fill-black">
            database
          </text>
          <text x="500" y="275" textAnchor="middle" className="text-[7px] fill-gray-500">
            serverless nosql
          </text>
        </g>

        {/* Arrow: API → Cosmos DB */}
        <path
          d="M 370 175 L 370 210 L 445 210 L 445 235"
          stroke="black"
          strokeWidth="2"
          fill="none"
          markerEnd="url(#arrow-infra)"
        />
        <text x="407" y="205" textAnchor="middle" className="text-[6px] fill-gray-500">
          read/write
        </text>

        {/* Arrow: Worker → Cosmos DB */}
        <path
          d="M 625 175 L 625 210 L 555 210 L 555 235"
          stroke="black"
          strokeWidth="2"
          fill="none"
          markerEnd="url(#arrow-infra)"
        />

        {/* Storage Account */}
        <g>
          <rect
            x="300"
            y="220"
            width="100"
            height="70"
            fill="white"
            stroke="black"
            strokeWidth="2"
          />
          <rect x="300" y="220" width="100" height="20" fill="black" />
          <text x="350" y="234" textAnchor="middle" className="text-[8px] font-bold fill-white">
            storage
          </text>
          <text x="350" y="258" textAnchor="middle" className="text-[9px] font-bold fill-black">
            blobs
          </text>
          <text x="350" y="275" textAnchor="middle" className="text-[7px] fill-gray-500">
            reports, assets
          </text>
        </g>

        {/* Arrow: Worker → Storage */}
        <path
          d="M 600 175 L 600 255 L 405 255"
          stroke="#9CA3AF"
          strokeWidth="1.5"
          fill="none"
          strokeDasharray="4"
          markerEnd="url(#arrow-infra-gray)"
        />

        {/* Key Vault */}
        <g>
          <rect
            x="150"
            y="220"
            width="100"
            height="70"
            fill="white"
            stroke="black"
            strokeWidth="2"
          />
          <rect x="150" y="220" width="100" height="20" fill="#F3787A" />
          <text x="200" y="234" textAnchor="middle" className="text-[8px] font-bold fill-white">
            key vault
          </text>
          <text x="200" y="258" textAnchor="middle" className="text-[9px] font-bold fill-black">
            secrets
          </text>
          <text x="200" y="275" textAnchor="middle" className="text-[7px] fill-gray-500">
            api keys, creds
          </text>
          {/* Lock icon */}
          <rect x="188" y="240" width="24" height="4" fill="none" />
        </g>

        {/* Dashed arrows: Key Vault → API and Worker */}
        <path
          d="M 255 250 L 295 185"
          stroke="#9CA3AF"
          strokeWidth="1.5"
          fill="none"
          strokeDasharray="4"
          markerEnd="url(#arrow-infra-gray)"
        />
        <path
          d="M 255 240 L 575 140"
          stroke="#9CA3AF"
          strokeWidth="1.5"
          fill="none"
          strokeDasharray="4"
          markerEnd="url(#arrow-infra-gray)"
        />
        <text x="230" y="195" textAnchor="middle" className="text-[6px] fill-gray-400">
          secrets ref
        </text>

        {/* GitHub Actions badge */}
        <g>
          <rect
            x="150"
            y="45"
            width="80"
            height="35"
            fill="white"
            stroke="black"
            strokeWidth="1.5"
          />
          <text x="190" y="60" textAnchor="middle" className="text-[7px] font-bold fill-black">
            github actions
          </text>
          <text x="190" y="72" textAnchor="middle" className="text-[6px] fill-gray-500">
            CI/CD deploy
          </text>
        </g>

        {/* Bicep/IaC badge */}
        <g>
          <rect
            x="250"
            y="45"
            width="60"
            height="35"
            fill="white"
            stroke="black"
            strokeWidth="1.5"
          />
          <text x="280" y="60" textAnchor="middle" className="text-[7px] font-bold fill-black">
            bicep
          </text>
          <text x="280" y="72" textAnchor="middle" className="text-[6px] fill-gray-500">
            IaC
          </text>
        </g>
      </svg>
    </div>
  );
}
