# Vite React Frontend Docker image for Lambda Web Adapter

FROM public.ecr.aws/docker/library/node:22-slim AS builder

WORKDIR /app

# Copy package files
COPY package.json ./

# Install dependencies fresh (don't use lock file in Docker due to platform-specific native binaries)
RUN npm install

# Copy source code
COPY . .

# Build the Vite app
RUN npm run build

# Production image - serve static files with a simple Node server
FROM public.ecr.aws/docker/library/node:22-slim AS runtime

# Install curl for downloading lambda adapter and serve for static file serving
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g serve

# Download Lambda Web Adapter directly (workaround for BuildKit cross-arch COPY --from bug)
RUN curl -Lo /opt/extensions/lambda-adapter \
    https://github.com/awslabs/aws-lambda-web-adapter/releases/download/v0.8.4/lambda-adapter-x86_64 \
    && chmod +x /opt/extensions/lambda-adapter

WORKDIR /app

# Copy built static files
COPY --from=builder /app/dist ./dist

# Set environment variables for Lambda Web Adapter
ENV PORT=4321
ENV AWS_LWA_INVOKE_MODE=buffered
ENV AWS_LWA_READINESS_CHECK_PATH=/

# Expose port
EXPOSE 4321

# Serve static files with SPA fallback
CMD ["serve", "-s", "dist", "-l", "4321"]
