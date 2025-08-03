FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./
COPY frontend/yarn.lock ./

# Install dependencies
RUN yarn install --frozen-lockfile

# Copy source code
COPY frontend/ .

# Build the application
RUN yarn build

# Install serve to run the built app
RUN yarn global add serve

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# Start the application
CMD ["serve", "-s", "build", "-l", "3000"]