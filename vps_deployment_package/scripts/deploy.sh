#!/bin/bash
set -euo pipefail

# --- Configuration ---
readonly GIT_URL="git@github.com:Henrijc/Trading-bot.git"
readonly DEPLOY_BRANCH="for-deployment"
readonly APP_DIR="/opt/crypto-coach"
readonly COMPOSE_DIR="${APP_DIR}/vps_deployment_package/docker"
readonly COMPOSE_FILE="${COMPOSE_DIR}/docker-compose.prod.yml"
readonly ENV_FILE="${APP_DIR}/.env"
readonly SUBDOMAIN="crypto-coach.zikhethele.properties"
readonly NGINX_CONF="/etc/nginx/sites-available/${SUBDOMAIN}"

# --- Logging Functions ---
log_info() { echo "[INFO] $1"; }
log_success() { echo "[SUCCESS] $1"; }
log_error() { echo "[ERROR] $1"; exit 1; }

# --- Main Logic ---
main() {
    log_info "Starting deployment from '${DEPLOY_BRANCH}' branch..."

    # Create .env file if it doesn't exist
    if [ ! -f "${ENV_FILE}" ]; then
        log_error ".env file not found at ${ENV_FILE}. Please create it before running."
    fi

    # Install dependencies
    log_info "Installing dependencies..."
    sudo apt-get update -qq && sudo apt-get install -y git docker.io docker-compose nginx certbot python3-certbot-nginx -qq
    sudo usermod -aG docker "${USER}"

    # Clone or update repository
    log_info "Updating repository..."
    if [ -d "${APP_DIR}" ]; then
        sudo rm -rf "${APP_DIR}"
    fi
    git clone --branch "${DEPLOY_BRANCH}" "${GIT_URL}" "${APP_DIR}"
    
    # Configure Nginx
    log_info "Configuring Nginx..."
    sudo tee "${NGINX_CONF}" > /dev/null <<'EOF'
server {
    listen 80;
    server_name crypto-coach.zikhethele.properties;
    return 301 https://$host$request_uri;
}
server {
    listen 443 ssl http2;
    server_name crypto-coach.zikhethele.properties;
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
    }
    location /api {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
    }
}
EOF
    sudo ln -sf "${NGINX_CONF}" "/etc/nginx/sites-enabled/${SUBDOMAIN}"
    sudo nginx -t && sudo systemctl reload nginx

    # Obtain SSL
    log_info "Configuring SSL..."
    if ! sudo certbot certificates | grep -q "${SUBDOMAIN}"; then
        sudo certbot --nginx -d "${SUBDOMAIN}" --non-interactive --agree-tos --email "admin@${SUBDOMAIN}" --redirect
    fi
    
    # Deploy with Docker Compose
    log_info "Starting Docker containers..."
    cd "${COMPOSE_DIR}"
    sudo docker-compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" up -d --build --remove-orphans

    log_success "Deployment complete! Application should be available at https://${SUBDOMAIN}"
    log_info "Run 'sudo docker ps' to see container status."
}

# Run main function, but only if user has docker group access
if groups "$USER" | grep -q docker; then
    main "$@"
else
    # Re-run script with docker group permissions
    exec sg docker "$0 $*"
fi