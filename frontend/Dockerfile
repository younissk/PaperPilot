# Astro SSR Frontend Docker image for Lambda Web Adapter

FROM public.ecr.aws/docker/library/node:22-slim AS builder

WORKDIR /app

# Copy package files
COPY package.json ./

# Install dependencies fresh (don't use lock file in Docker due to platform-specific native binaries)
RUN npm install

# Copy source code
COPY . .

# Build the Astro app
RUN npm run build

# Production image
FROM public.ecr.aws/docker/library/node:22-slim AS runtime

# Install curl for downloading lambda adapter
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Download Lambda Web Adapter directly (workaround for BuildKit cross-arch COPY --from bug)
RUN curl -Lo /opt/extensions/lambda-adapter \
    https://github.com/awslabs/aws-lambda-web-adapter/releases/download/v0.8.4/lambda-adapter-x86_64 \
    && chmod +x /opt/extensions/lambda-adapter

WORKDIR /app

# Copy built application
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

# Set environment variables for Lambda Web Adapter
ENV PORT=4321
ENV AWS_LWA_INVOKE_MODE=buffered
ENV AWS_LWA_READINESS_CHECK_PATH=/

# Expose port
EXPOSE 4321

# Start the Astro server
CMD ["node", "./dist/server/entry.mjs"]
