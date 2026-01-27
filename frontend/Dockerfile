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

# Lambda Web Adapter
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.8.4 /lambda-adapter /opt/extensions/lambda-adapter

WORKDIR /app

# Copy built application
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

# Set environment variables for Lambda Web Adapter
ENV PORT=4321
ENV AWS_LWA_INVOKE_MODE=response_stream
ENV AWS_LWA_READINESS_CHECK_PATH=/api/health

# Expose port
EXPOSE 4321

# Start the Astro server
CMD ["node", "./dist/server/entry.mjs"]
