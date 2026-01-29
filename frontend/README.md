# PaperPilot Frontend

Vite + React SPA frontend for PaperPilot - AI-powered academic literature discovery.

## Tech Stack

- **React 19** - UI framework
- **Vite** - Build tool and dev server
- **React Router v7** - Client-side routing
- **TanStack Query** - Data fetching and caching
- **Tailwind CSS** - Styling
- **react-helmet-async** - SEO meta tags

## Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Backend API URL (VITE_ prefix required for Vite)
VITE_API_BASE_URL=http://localhost:8000
```

## Pages

- `/` - Search form to start a new research query
- `/report/:queryId` - View generated research report
- `/queries` - List of previous queries
- `/about` - About page

## SEO Features

- Client-side meta tags with react-helmet-async
- JSON-LD structured data on report pages
- Static robots.txt in public folder
- `noindex` on in-progress/generating pages

## Deployment

The frontend is deployed as a Lambda function using Lambda Web Adapter.
See `infra/template.yaml` for the SAM configuration.

### Local Docker Build

```bash
# Build the Docker image
docker build -t paperpilot-frontend .

# Run locally
docker run -p 4321:4321 -e VITE_API_BASE_URL=http://host.docker.internal:8000 paperpilot-frontend
```

## Architecture

```
src/
├── components/          # React components
│   ├── Header.tsx       # Navigation with health indicator
│   ├── Layout.tsx       # Main layout wrapper
│   ├── PaperCard.tsx    # Paper display card
│   ├── ProgressIndicator.tsx  # Pipeline progress UI
│   ├── SearchForm.tsx   # Query input form
│   └── SEO.tsx          # Meta tags component
├── hooks/               # TanStack Query hooks
│   ├── useAllResults.ts # Fetch report results
│   ├── useHealthCheck.ts # API health check
│   ├── usePipelineStatus.ts # Job polling
│   └── useQueries.ts    # List queries
├── lib/                 # Shared utilities
│   ├── api.ts           # API client
│   ├── config.ts        # Configuration
│   └── types.ts         # TypeScript types
├── pages/               # Route pages
│   ├── AboutPage.tsx
│   ├── HomePage.tsx
│   ├── QueriesPage.tsx
│   └── ReportPage.tsx
├── App.tsx              # Router setup
├── main.tsx             # React entry point
└── index.css            # Tailwind styles
```
