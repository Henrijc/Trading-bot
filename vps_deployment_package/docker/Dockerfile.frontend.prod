# ---- Stage 1: Build Application ----
FROM node:20-alpine AS builder

# Set the working directory
WORKDIR /app

# Enable Corepack, the modern way to manage Yarn
RUN corepack enable

# Copy only dependency manifests to leverage Docker's build cache
COPY frontend/package.json frontend/yarn.lock ./

# Install all dependencies, including devDependencies needed for the build (like craco)
RUN yarn install --frozen-lockfile

# Copy the rest of the application source code
COPY frontend/. ./

# Create the production build
RUN yarn build


# ---- Stage 2: Production Server ----
FROM nginx:1.27-alpine

# Copy the built static assets from the 'builder' stage to the Nginx server directory
COPY --from=builder /app/build /usr/share/nginx/html

# Copy a basic Nginx configuration to serve the React application
# This ensures that routing is handled correctly by the single-page app
RUN echo 'server { \
    listen 3000; \
    server_name localhost; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

# Create a non-root user and group for security
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Set correct ownership for Nginx assets and directories
RUN chown -R appuser:appgroup /usr/share/nginx/html && \
    chown -R appuser:appgroup /var/cache/nginx && \
    chown -R appuser:appgroup /var/log/nginx && \
    chown -R appuser:appgroup /etc/nginx/conf.d

# Switch to the non-root user
USER appuser

# Expose the port the container will listen on
EXPOSE 3000

# Start Nginx in the foreground when the container launches
CMD ["nginx", "-g", "daemon off;"]