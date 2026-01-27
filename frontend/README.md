# PaperPilot Frontend

Astro SSR frontend for PaperPilot - AI-powered academic literature discovery.

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
```

## Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Backend API URL
API_BASE_URL=http://localhost:8000
```

## Pages

- `/` - Search form to start a new research query
- `/report/{query_id}` - View generated research report (SSR for SEO)
- `/queries` - List of previous queries
- `/about` - About page

## SEO Features

- Server-side rendering for all report pages
- Dynamic sitemap.xml at `/sitemap.xml`
- robots.txt at `/robots.txt`
- JSON-LD structured data on report pages
- Canonical URLs to avoid duplicate content
- `noindex` on in-progress/generating pages

## Deployment

The frontend is deployed as a Lambda function using Lambda Web Adapter.
See `infra/template.yaml` for the SAM configuration.

### Local Docker Build

```bash
# Build the Docker image
docker build -t paperpilot-frontend .

# Run locally
docker run -p 4321:4321 -e API_BASE_URL=http://host.docker.internal:8000 paperpilot-frontend
```

## Architecture

```
src/
├── components/      # Astro components
│   └── Header.astro
├── layouts/         # Page layouts
│   └── Layout.astro
├── lib/            # Shared utilities
│   ├── api.ts      # API client
│   ├── config.ts   # Configuration
│   └── types.ts    # TypeScript types
├── pages/          # Route pages
│   ├── index.astro
│   ├── about.astro
│   ├── queries.astro
│   ├── report/
│   │   └── [query_id].astro
│   ├── robots.txt.ts
│   └── sitemap.xml.ts
└── styles/
    └── global.css
```
