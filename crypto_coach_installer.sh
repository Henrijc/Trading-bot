#!/bin/bash

# =============================================================================
# AI Crypto Trading Coach - VPS CI/CD Installation Script
# Ubuntu 22.04 + Virtualizor Compatible
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Global variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/crypto-coach-install.log"
BACKUP_DIR="/tmp/crypto-coach-backup-$(date +%Y%m%d_%H%M%S)"
INSTALL_DIR="/opt/crypto-coach"
SERVICE_USER="crypto-coach"
VPS_IP="156.155.253.224"
DOMAIN="zikhethele.properties"
SUBDOMAIN="crypto-coach.zikhethele.properties"

# Download URLs (will be downloaded first)
DOCKER_COMPOSE_URL="https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-linux-x86_64"
NODEJS_SETUP_URL="https://deb.nodesource.com/setup_18.x"

# =============================================================================
# Utility Functions
# =============================================================================

log() {
    echo -e "${1}" | tee -a "$LOG_FILE"
}

log_info() {
    log "${BLUE}[INFO]${NC} ${1}"
}

log_success() {
    log "${GREEN}[SUCCESS]${NC} ${1}"
}

log_warning() {
    log "${YELLOW}[WARNING]${NC} ${1}"
}

log_error() {
    log "${RED}[ERROR]${NC} ${1}"
}

log_header() {
    echo ""
    log "${PURPLE}========================================${NC}"
    log "${PURPLE} ${1}${NC}"
    log "${PURPLE}========================================${NC}"
}

# =============================================================================
# Pre-flight Checks
# =============================================================================

check_root_sudo() {
    log_header "Checking User Privileges"
    
    # Check if running with root privileges
    if [[ $EUID -ne 0 ]]; then
        log_error "This script requires root privileges. Please run with sudo:"
        log_error "sudo $0"
        exit 1
    fi
    
    # Check if NOT running as direct root user
    if [[ -z "${SUDO_USER:-}" ]]; then
        log_error "Do not run this script as the root user directly."
        log_error "Please create a sudo user and run the script with sudo."
        log_error ""
        log_error "To create a sudo user (if needed):"
        log_error "  adduser cryptoadmin"
        log_error "  usermod -aG sudo cryptoadmin"
        log_error "  su - cryptoadmin"
        log_error "  sudo $0"
        exit 1
    fi
    
    log_success "Running with proper sudo privileges as user: $SUDO_USER"
}

check_ubuntu_version() {
    log_header "Checking Ubuntu Version"
    
    if [[ ! -f /etc/os-release ]]; then
        log_error "Cannot determine OS version"
        exit 1
    fi
    
    source /etc/os-release
    
    if [[ "$ID" != "ubuntu" ]]; then
        log_error "This script is designed for Ubuntu. Detected: $ID"
        exit 1
    fi
    
    # Check for Ubuntu 20.04+ (should work with 22.04)
    version_major=$(echo "$VERSION_ID" | cut -d. -f1)
    version_minor=$(echo "$VERSION_ID" | cut -d. -f2)
    
    if [[ $version_major -lt 20 ]] || [[ $version_major -eq 20 && $version_minor -lt 4 ]]; then
        log_error "Ubuntu 20.04+ required. Detected: $VERSION_ID"
        exit 1
    fi
    
    log_success "Ubuntu $VERSION_ID detected - Compatible"
}

check_virtualizor_environment() {
    log_header "Checking Virtualizor Environment"
    
    # Check for common Virtualizor indicators
    if [[ -f /proc/vz/version ]] || [[ -d /vz ]] || grep -q "vz" /proc/cmdline 2>/dev/null; then
        log_info "OpenVZ/Virtualizor container detected"
        export CONTAINER_ENV="openvz"
    elif [[ -f /.dockerenv ]] || grep -q docker /proc/1/cgroup 2>/dev/null; then
        log_warning "Docker container detected - may cause issues"
        export CONTAINER_ENV="docker"
    else
        log_info "Standard VPS/VM environment detected"
        export CONTAINER_ENV="standard"
    fi
    
    # Check available resources
    mem_total=$(free -m | awk 'NR==2{printf "%.0f", $2}')
    disk_avail=$(df / | awk 'NR==2{printf "%.0f", $4/1024/1024}')
    
    if [[ $mem_total -lt 3900 ]]; then
        log_warning "Low memory detected: ${mem_total}MB (4GB+ recommended)"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    if [[ $disk_avail -lt 45 ]]; then
        log_warning "Low disk space: ${disk_avail}GB (50GB+ recommended)"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    log_success "System resources: ${mem_total}MB RAM, ${disk_avail}GB disk"
}

check_network_connectivity() {
    log_header "Checking Network Connectivity"
    
    # Test internet connectivity
    if ! ping -c 1 8.8.8.8 &> /dev/null; then
        log_error "No internet connectivity detected"
        exit 1
    fi
    
    # Test DNS resolution
    if ! nslookup github.com &> /dev/null; then
        log_error "DNS resolution failed"
        exit 1
    fi
    
    # Check if ports are available
    local ports_to_check=(80 443 3000 8001 8082 27017)
    local busy_ports=()
    
    for port in "${ports_to_check[@]}"; do
        if netstat -tuln | grep -q ":$port "; then
            busy_ports+=("$port")
        fi
    done
    
    if [[ ${#busy_ports[@]} -gt 0 ]]; then
        log_warning "Ports in use: ${busy_ports[*]}"
        log_warning "These ports will need to be available for the application"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    log_success "Network connectivity verified"
}

# =============================================================================
# Interactive Configuration
# =============================================================================

collect_configuration() {
    log_header "Configuration Setup"
    
    echo "Please provide the following configuration details:"
    echo ""
    
    # API Keys
    log_info "=== Trading API Keys ==="
    while [[ -z "${LUNO_API_KEY:-}" ]]; do
        read -p "Enter your Luno API Key: " LUNO_API_KEY
    done
    
    while [[ -z "${LUNO_SECRET:-}" ]]; do
        read -s -p "Enter your Luno Secret Key: " LUNO_SECRET
        echo
    done
    
    while [[ -z "${GEMINI_API_KEY:-}" ]]; do
        read -p "Enter your Google Gemini API Key: " GEMINI_API_KEY
    done
    
    echo ""
    log_info "=== Admin Account ==="
    while [[ -z "${ADMIN_USERNAME:-}" ]]; do
        read -p "Enter admin username [default: admin]: " ADMIN_USERNAME
        ADMIN_USERNAME=${ADMIN_USERNAME:-admin}
    done
    
    while [[ -z "${ADMIN_PASSWORD:-}" ]]; do
        read -s -p "Enter admin password: " ADMIN_PASSWORD
        echo
        if [[ ${#ADMIN_PASSWORD} -lt 8 ]]; then
            log_warning "Password should be at least 8 characters"
            ADMIN_PASSWORD=""
        fi
    done
    
    echo ""
    log_info "=== Security Configuration ==="
    log_info "Auto-generating JWT secret key..."
    JWT_SECRET_KEY=$(openssl rand -hex 32)
    
    log_info "Auto-generating encryption key..."
    ENCRYPTION_KEY=$(openssl rand -hex 16)
    
    echo ""
    log_info "=== Network Configuration ==="
    log_info "Detected server IP: $VPS_IP"
    log_info "Domain: $DOMAIN"
    log_info "Subdomain: $SUBDOMAIN"
    
    read -p "Enter your home/office IP address for access restriction: " USER_IP
    while [[ ! $USER_IP =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; do
        log_error "Invalid IP address format"
        read -p "Enter your home/office IP address: " USER_IP
    done
    
    echo ""
    log_info "=== GitHub Configuration ==="
    read -p "Enter your GitHub username: " GITHUB_USERNAME
    while [[ -z "$GITHUB_USERNAME" ]]; do
        read -p "GitHub username is required: " GITHUB_USERNAME
    done
    
    echo ""
    log_success "Configuration collected successfully"
}

# =============================================================================
# Pre-download Dependencies
# =============================================================================

download_dependencies() {
    log_header "Pre-downloading Dependencies"
    
    local download_dir="/tmp/crypto-coach-downloads"
    mkdir -p "$download_dir"
    
    log_info "Downloading Docker Compose..."
    if ! curl -fsSL "$DOCKER_COMPOSE_URL" -o "$download_dir/docker-compose"; then
        log_error "Failed to download Docker Compose"
        return 1
    fi
    
    log_info "Downloading Node.js setup script..."
    if ! curl -fsSL "$NODEJS_SETUP_URL" -o "$download_dir/nodejs-setup.sh"; then
        log_error "Failed to download Node.js setup"
        return 1
    fi
    
    log_info "Downloading Docker installation script..."
    if ! curl -fsSL https://get.docker.com -o "$download_dir/get-docker.sh"; then
        log_error "Failed to download Docker setup"
        return 1
    fi
    
    export DOWNLOAD_DIR="$download_dir"
    log_success "All dependencies downloaded successfully"
}

# =============================================================================
# Rollback Functionality
# =============================================================================

create_backup() {
    log_info "Creating system backup..."
    mkdir -p "$BACKUP_DIR"
    
    # Backup existing configurations
    [[ -f /etc/nginx/sites-available/default ]] && cp /etc/nginx/sites-available/default "$BACKUP_DIR/"
    [[ -d "$INSTALL_DIR" ]] && cp -r "$INSTALL_DIR" "$BACKUP_DIR/"
    
    # Save installed packages list
    dpkg --get-selections > "$BACKUP_DIR/installed-packages.txt"
    
    log_success "Backup created at: $BACKUP_DIR"
}

rollback_changes() {
    log_error "Installation failed. Rolling back changes..."
    
    # Stop services
    systemctl stop nginx 2>/dev/null || true
    systemctl stop docker 2>/dev/null || true
    
    # Remove created directories
    [[ -d "$INSTALL_DIR" ]] && rm -rf "$INSTALL_DIR"
    
    # Remove service user
    if id "$SERVICE_USER" &>/dev/null; then
        userdel -r "$SERVICE_USER" 2>/dev/null || true
    fi
    
    # Restore nginx config
    if [[ -f "$BACKUP_DIR/default" ]]; then
        cp "$BACKUP_DIR/default" /etc/nginx/sites-available/default
        systemctl restart nginx 2>/dev/null || true
    fi
    
    log_info "Rollback completed. Check logs at: $LOG_FILE"
}

# =============================================================================
# Installation Functions
# =============================================================================

update_system() {
    log_header "Updating System Packages"
    
    export DEBIAN_FRONTEND=noninteractive
    
    if ! apt update && apt upgrade -y; then
        log_error "System update failed"
        return 1
    fi
    
    # Install essential packages
    if ! apt install -y curl wget gnupg2 software-properties-common apt-transport-https ca-certificates lsb-release; then
        log_error "Failed to install essential packages"
        return 1
    fi
    
    log_success "System updated successfully"
}

install_docker() {
    log_header "Installing Docker"
    
    # Remove old Docker versions
    apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    
    # Install Docker using pre-downloaded script
    if [[ -f "$DOWNLOAD_DIR/get-docker.sh" ]]; then
        bash "$DOWNLOAD_DIR/get-docker.sh"
    else
        log_error "Docker installation script not found"
        return 1
    fi
    
    # Install Docker Compose using pre-downloaded binary
    if [[ -f "$DOWNLOAD_DIR/docker-compose" ]]; then
        install -m 755 "$DOWNLOAD_DIR/docker-compose" /usr/local/bin/docker-compose
    else
        # Fallback to apt installation
        apt install -y docker-compose-plugin
        ln -sf /usr/libexec/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose 2>/dev/null || true
    fi
    
    # Start and enable Docker
    systemctl enable docker
    systemctl start docker
    
    # Add service user to docker group
    usermod -aG docker "$SERVICE_USER" 2>/dev/null || true
    usermod -aG docker "$SUDO_USER" 2>/dev/null || true
    
    # Test Docker installation
    if ! docker --version && docker-compose --version; then
        log_error "Docker installation verification failed"
        return 1
    fi
    
    log_success "Docker installed successfully"
}

install_nginx() {
    log_header "Installing Nginx"
    
    if ! apt install -y nginx; then
        log_error "Nginx installation failed"
        return 1
    fi
    
    systemctl enable nginx
    systemctl start nginx
    
    # Test Nginx
    if ! systemctl is-active --quiet nginx; then
        log_error "Nginx failed to start"
        return 1
    fi
    
    log_success "Nginx installed successfully"
}

install_certbot() {
    log_header "Installing Certbot"
    
    if ! apt install -y certbot python3-certbot-nginx; then
        log_error "Certbot installation failed"
        return 1
    fi
    
    log_success "Certbot installed successfully"
}

install_nodejs() {
    log_header "Installing Node.js"
    
    # Install Node.js using pre-downloaded script
    if [[ -f "$DOWNLOAD_DIR/nodejs-setup.sh" ]]; then
        bash "$DOWNLOAD_DIR/nodejs-setup.sh"
        apt-get install -y nodejs
    else
        log_error "Node.js setup script not found"
        return 1
    fi
    
    # Install additional tools
    if ! apt install -y build-essential; then
        log_warning "Build tools installation failed (may affect some npm packages)"
    fi
    
    # Test Node.js installation
    if ! node --version && npm --version; then
        log_error "Node.js installation verification failed"
        return 1
    fi
    
    log_success "Node.js installed successfully"
}

install_git() {
    log_header "Installing Git"
    
    if ! apt install -y git; then
        log_error "Git installation failed"
        return 1
    fi
    
    log_success "Git installed successfully"
}

create_service_user() {
    log_header "Creating Service User"
    
    # Create service user if it doesn't exist
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd -r -s /bin/false -d "$INSTALL_DIR" "$SERVICE_USER"
        log_success "Created service user: $SERVICE_USER"
    else
        log_info "Service user already exists: $SERVICE_USER"
    fi
    
    # Add to docker group
    usermod -aG docker "$SERVICE_USER"
}

setup_application_directory() {
    log_header "Setting Up Application Directory"
    
    # Create directory structure
    mkdir -p "$INSTALL_DIR"/{app,docker,scripts,logs,backups}
    
    # Set ownership
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    
    # Set permissions
    chmod 755 "$INSTALL_DIR"
    chmod 750 "$INSTALL_DIR"/{logs,backups}
    
    log_success "Application directory created: $INSTALL_DIR"
}

configure_nginx() {
    log_header "Configuring Nginx"
    
    # Create Nginx configuration
    cat > /etc/nginx/sites-available/crypto-coach << EOF
server {
    listen 80;
    server_name $SUBDOMAIN;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $SUBDOMAIN;
    
    # SSL Configuration (will be added by certbot)
    
    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    
    # IP Restriction - PRIVATE ACCESS ONLY
    allow $USER_IP;
    deny all;
    
    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
    
    # Frontend (React App)
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Backend API
    location /api {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }
}
EOF
    
    # Enable site
    if [[ -f /etc/nginx/sites-enabled/default ]]; then
        rm /etc/nginx/sites-enabled/default
    fi
    
    ln -sf /etc/nginx/sites-available/crypto-coach /etc/nginx/sites-enabled/
    
    # Test Nginx configuration
    if ! nginx -t; then
        log_error "Nginx configuration test failed"
        return 1
    fi
    
    systemctl reload nginx
    
    log_success "Nginx configured successfully"
}

create_environment_file() {
    log_header "Creating Environment Configuration"
    
    cat > "$INSTALL_DIR/.env" << EOF
# AI Crypto Trading Coach - Production Environment
# Generated on $(date)

# Database Configuration
MONGO_ROOT_USER=cryptoadmin
MONGO_ROOT_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
MONGO_DB_NAME=crypto_trader_coach

# Trading API Keys
LUNO_API_KEY=$LUNO_API_KEY
LUNO_SECRET=$LUNO_SECRET

# AI Service API Keys
GEMINI_API_KEY=$GEMINI_API_KEY

# Security Configuration
JWT_SECRET_KEY=$JWT_SECRET_KEY
ADMIN_USERNAME=$ADMIN_USERNAME
ADMIN_PASSWORD=$ADMIN_PASSWORD
ENCRYPTION_KEY=$ENCRYPTION_KEY

# GitHub Configuration
GITHUB_REPOSITORY=$GITHUB_USERNAME/ai-crypto-trading-coach-vps

# Network Configuration
VPS_IP=$VPS_IP
DOMAIN=$DOMAIN
SUBDOMAIN=$SUBDOMAIN
USER_IP=$USER_IP

# Trading Configuration
MONTHLY_TARGET=8000
WEEKLY_TARGET=2000

# Security Limits
MAX_TRADE_AMOUNT=50000
MAX_DAILY_TRADING_VOLUME=200000
MAX_PORTFOLIO_PERCENTAGE_PER_TRADE=20

# Production Settings
ENVIRONMENT=production
DEBUG=false
EOF
    
    # Set secure permissions
    chmod 600 "$INSTALL_DIR/.env"
    chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/.env"
    
    log_success "Environment file created"
}

# =============================================================================
# SSL Certificate Setup
# =============================================================================

setup_ssl_certificate() {
    log_header "Setting Up SSL Certificate"
    
    log_info "Please ensure your DNS record is configured:"
    log_info "Type: A"
    log_info "Name: crypto-coach"
    log_info "Value: $VPS_IP"
    log_info "Domain: $DOMAIN"
    echo ""
    
    read -p "Have you configured the DNS record? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_warning "SSL certificate setup skipped"
        log_warning "You can run this later: certbot --nginx -d $SUBDOMAIN"
        return 0
    fi
    
    # Test DNS resolution
    log_info "Testing DNS resolution..."
    local dns_test_count=0
    while [[ $dns_test_count -lt 30 ]]; do
        if nslookup "$SUBDOMAIN" | grep -q "$VPS_IP"; then
            log_success "DNS resolution verified"
            break
        fi
        log_info "Waiting for DNS propagation... ($((dns_test_count + 1))/30)"
        sleep 10
        ((dns_test_count++))
    done
    
    if [[ $dns_test_count -eq 30 ]]; then
        log_warning "DNS propagation taking longer than expected"
        read -p "Continue with SSL setup anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return 0
        fi
    fi
    
    # Obtain SSL certificate
    if certbot --nginx -d "$SUBDOMAIN" --non-interactive --agree-tos --email "admin@$DOMAIN"; then
        log_success "SSL certificate obtained successfully"
    else
        log_warning "SSL certificate setup failed - you can retry later"
        return 0
    fi
}

# =============================================================================
# Final Setup
# =============================================================================

create_management_scripts() {
    log_header "Creating Management Scripts"
    
    # Health check script
    cat > "$INSTALL_DIR/scripts/health-check.sh" << 'EOF'
#!/bin/bash
set -e

echo "🔍 Health Check - AI Crypto Trading Coach"
echo "========================================"

DOMAIN="crypto-coach.zikhethele.properties"
FAILED_CHECKS=0

# Function to check HTTP endpoint
check_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "Checking $name... "
    
    if response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 --max-time 30 "$url" 2>/dev/null); then
        if [ "$response" -eq "$expected_status" ]; then
            echo "✅ OK (HTTP $response)"
        else
            echo "❌ FAILED (HTTP $response, expected $expected_status)"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        fi
    else
        echo "❌ FAILED (Connection error)"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
}

# Check endpoints
check_endpoint "Frontend" "https://$DOMAIN/"
check_endpoint "Backend API" "https://$DOMAIN/api/"

echo ""
if [ $FAILED_CHECKS -eq 0 ]; then
    echo "🎉 All checks passed!"
    exit 0
else
    echo "❌ $FAILED_CHECKS checks failed!"
    exit 1
fi
EOF
    
    # Backup script
    cat > "$INSTALL_DIR/scripts/backup.sh" << 'EOF'
#!/bin/bash
set -e

BACKUP_DIR="/opt/crypto-coach/backups/backup-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Creating backup at: $BACKUP_DIR"

# Backup environment file
cp /opt/crypto-coach/.env "$BACKUP_DIR/"

# Backup database
docker exec crypto-coach-mongo-prod mongodump --out "$BACKUP_DIR/mongodb" 2>/dev/null || true

# Backup logs
cp -r /opt/crypto-coach/logs "$BACKUP_DIR/" 2>/dev/null || true

echo "Backup completed: $BACKUP_DIR"
EOF
    
    chmod +x "$INSTALL_DIR/scripts/"*.sh
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/scripts"
    
    log_success "Management scripts created"
}

display_completion_info() {
    log_header "Installation Complete!"
    
    echo ""
    log_success "🎉 AI Crypto Trading Coach installed successfully!"
    echo ""
    log_info "=== ACCESS INFORMATION ==="
    log_info "URL: https://$SUBDOMAIN"
    log_info "Admin Username: $ADMIN_USERNAME"
    log_info "Admin Password: [as configured]"
    log_info "Allowed IP: $USER_IP"
    echo ""
    log_info "=== NEXT STEPS ==="
    log_info "1. Set up your GitHub repository for CI/CD"
    log_info "2. Configure GitHub secrets for automatic deployment"
    log_info "3. Access your application at: https://$SUBDOMAIN"
    echo ""
    log_info "=== MANAGEMENT ==="
    log_info "Health Check: $INSTALL_DIR/scripts/health-check.sh"
    log_info "Backup: $INSTALL_DIR/scripts/backup.sh"
    log_info "Logs: $LOG_FILE"
    echo ""
    log_info "=== FILES CREATED ==="
    log_info "Installation Directory: $INSTALL_DIR"
    log_info "Environment File: $INSTALL_DIR/.env"
    log_info "Nginx Config: /etc/nginx/sites-available/crypto-coach"
    log_info "Backup Location: $BACKUP_DIR"
    echo ""
}

# =============================================================================
# Main Installation Flow
# =============================================================================

main() {
    log_header "AI Crypto Trading Coach - VPS Installation"
    log_info "Starting installation on Ubuntu 22.04 + Virtualizor"
    log_info "Log file: $LOG_FILE"
    
    # Pre-flight checks
    check_root_sudo
    check_ubuntu_version
    check_virtualizor_environment
    check_network_connectivity
    
    # Interactive configuration
    collect_configuration
    
    # Create backup before making changes
    create_backup
    
    # Set up error handling with rollback
    trap 'rollback_changes' ERR
    
    # Pre-download dependencies
    download_dependencies
    
    # System setup
    update_system
    install_docker
    install_nginx
    install_certbot
    install_nodejs
    install_git
    
    # Application setup
    create_service_user
    setup_application_directory
    configure_nginx
    create_environment_file
    
    # SSL setup
    setup_ssl_certificate
    
    # Final setup
    create_management_scripts
    
    # Disable error trap (installation successful)
    trap - ERR
    
    # Display completion information
    display_completion_info
    
    log_success "Installation completed successfully!"
}

# =============================================================================
# Script Entry Point
# =============================================================================

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi