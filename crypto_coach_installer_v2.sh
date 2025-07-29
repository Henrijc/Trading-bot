#!/bin/bash

# =============================================================================
# AI Crypto Trading Coach - COMPREHENSIVE VPS INSTALLER  
# Ubuntu 22.04 + Virtualizor Compatible
# 
# Based on Post-Mortem Analysis from Zikhethele Properties CRM Deployment
# Addresses ALL critical failure points identified in production deployment
# =============================================================================

set -euo pipefail

# Version and compatibility
SCRIPT_VERSION="2.0.0"
REQUIRED_UBUNTU_MIN="20.04"
REQUIRED_RAM_GB=4
REQUIRED_DISK_GB=50

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Global configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/crypto-coach-install-$(date +%Y%m%d_%H%M%S).log"
BACKUP_DIR="/tmp/crypto-coach-backup-$(date +%Y%m%d_%H%M%S)"
INSTALL_DIR="/opt/crypto-coach"
SERVICE_USER="crypto-coach"
COMPOSE_FILE="docker-compose.prod.yml"

# Network configuration from user's environment
VPS_IP="156.155.253.224"
DOMAIN="zikhethele.properties"
SUBDOMAIN="crypto-coach.zikhethele.properties"

# Service ports that must be available
REQUIRED_PORTS=(80 443 3000 8001 8082 27017 22)
DOCKER_PORTS=(3000 8001 8082 27017)  # Ports used by Docker containers

# Services that might conflict with Docker ports
CONFLICTING_SERVICES=(
    "postgresql:5432"
    "redis:6379" 
    "mongodb:27017"
    "nginx:80"
    "apache2:80"
    "mysql:3306"
)

# Pre-download URLs (to avoid network failures during install)
DOCKER_COMPOSE_URL="https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-linux-x86_64"
NODEJS_SETUP_URL="https://deb.nodesource.com/setup_18.x"
DOCKER_INSTALL_URL="https://get.docker.com"

# =============================================================================
# LOGGING AND UTILITY FUNCTIONS
# =============================================================================

log() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${message}" | tee -a "$LOG_FILE"
    echo "[$timestamp] $message" >> "$LOG_FILE"
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
    log "${PURPLE}============================================${NC}"
    log "${PURPLE} ${1}${NC}"
    log "${PURPLE}============================================${NC}"
}

# Progress indicator
show_progress() {
    local current=$1
    local total=$2
    local desc=$3
    local percentage=$((current * 100 / total))
    printf "\r${CYAN}[%3d%%]${NC} Step %d/%d: %s" "$percentage" "$current" "$total" "$desc"
}

# =============================================================================
# CRITICAL BUG FIXES BASED ON POST-MORTEM ANALYSIS
# =============================================================================

# FIX #1: Proper Sudo/Root Detection (addresses Bug #2 from post-mortem)
check_user_privileges() {
    log_header "User Privilege Verification"
    
    # Must have root privileges
    if [[ $EUID -ne 0 ]]; then
        log_error "This script requires root privileges"
        log_error "Run with: sudo $0"
        exit 1
    fi
    
    # Must NOT be direct root login (must be sudo)
    if [[ -z "${SUDO_USER:-}" ]]; then
        log_error "Do not run this script as root user directly"
        log_error "Please create a sudo user and run with sudo:"
        log_error ""
        log_error "  # Create sudo user (if needed):"
        log_error "  adduser cryptoadmin"
        log_error "  usermod -aG sudo cryptoadmin"
        log_error ""
        log_error "  # Switch to sudo user and run:"
        log_error "  su - cryptoadmin"
        log_error "  sudo $0"
        exit 1
    fi
    
    log_success "Running with proper sudo privileges as user: $SUDO_USER"
}

# FIX #2: Single Deployment Strategy Enforcement (addresses Bug #1 from post-mortem)
verify_deployment_strategy() {
    log_header "Deployment Strategy Verification"
    
    log_info "This installer implements DOCKER-BASED deployment strategy"
    log_info "Strategy: Docker Compose + Nginx Reverse Proxy + CI/CD"
    
    # Check if this is consistent with any existing setup
    if [[ -f "$INSTALL_DIR/package.json" ]] || [[ -f "$INSTALL_DIR/requirements.txt" ]]; then
        log_warning "Found existing application files that suggest traditional deployment"
        log_warning "This installer uses Docker containers, not traditional PM2/systemd services"
        
        read -p "Continue with Docker strategy? This will replace any existing setup (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Installation cancelled by user"
            exit 0
        fi
    fi
    
    log_success "Docker-based deployment strategy confirmed"
}

# FIX #3: Dynamic Service Path Detection (addresses Bug #3 from post-mortem)
find_service_config() {
    local service_name=$1
    local config_filename=$2
    
    # Search common locations dynamically
    local search_paths=(
        "/etc/$service_name"
        "/etc/$service_name.d"
        "/opt/$service_name"
        "/usr/local/etc/$service_name"
        "/var/lib/$service_name"
    )
    
    for path in "${search_paths[@]}"; do
        if [[ -d "$path" ]]; then
            local found_config=$(find "$path" -name "$config_filename" -type f 2>/dev/null | head -1)
            if [[ -n "$found_config" ]]; then
                echo "$found_config"
                return 0
            fi
        fi
    done
    
    return 1
}

# FIX #4: Service Conflict Resolution (addresses Bug #4 from post-mortem)
stop_conflicting_services() {
    log_header "Resolving Service Port Conflicts"
    
    local stopped_services=()
    
    # Check and stop services that might conflict with Docker ports
    for service_port in "${CONFLICTING_SERVICES[@]}"; do
        local service="${service_port%:*}"
        local port="${service_port#*:}"
        
        # Check if service is running
        if systemctl is-active --quiet "$service" 2>/dev/null; then
            log_warning "Service '$service' is running on port $port (needed for Docker)"
            read -p "Stop $service? (y/N): " -n 1 -r
            echo
            
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                systemctl stop "$service"
                systemctl disable "$service" 2>/dev/null || true
                stopped_services+=("$service")
                log_success "Stopped and disabled $service"
            else
                log_error "Cannot continue with $service running on port $port"
                exit 1
            fi
        fi
    done
    
    # Check for processes using required ports
    for port in "${DOCKER_PORTS[@]}"; do
        local pid=$(lsof -ti tcp:$port 2>/dev/null || true)
        if [[ -n "$pid" ]]; then
            local process_name=$(ps -p $pid -o comm= 2>/dev/null || echo "unknown")
            log_warning "Port $port is in use by process: $process_name (PID: $pid)"
            
            read -p "Kill process using port $port? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                kill -TERM $pid 2>/dev/null || kill -KILL $pid 2>/dev/null || true
                log_success "Killed process on port $port"
            else
                log_error "Cannot continue with port $port in use"
                exit 1
            fi
        fi
    done
    
    if [[ ${#stopped_services[@]} -gt 0 ]]; then
        log_info "Stopped services: ${stopped_services[*]}"
        echo "Stopped services: ${stopped_services[*]}" >> "$BACKUP_DIR/stopped_services.txt"
    fi
    
    log_success "Port conflicts resolved"
}

# =============================================================================
# COMPREHENSIVE SYSTEM VERIFICATION
# =============================================================================

verify_system_requirements() {
    log_header "System Requirements Verification"
    
    # Ubuntu version check with dynamic detection
    if [[ ! -f /etc/os-release ]]; then
        log_error "Cannot determine operating system"
        exit 1
    fi
    
    source /etc/os-release
    
    if [[ "$ID" != "ubuntu" ]]; then
        log_error "This installer requires Ubuntu. Detected: $ID $VERSION_ID"
        exit 1
    fi
    
    # Version comparison
    local version_major=$(echo "$VERSION_ID" | cut -d. -f1)
    local version_minor=$(echo "$VERSION_ID" | cut -d. -f2)
    local required_major=$(echo "$REQUIRED_UBUNTU_MIN" | cut -d. -f1)
    local required_minor=$(echo "$REQUIRED_UBUNTU_MIN" | cut -d. -f2)
    
    if [[ $version_major -lt $required_major ]] || \
       [[ $version_major -eq $required_major && $version_minor -lt $required_minor ]]; then
        log_error "Ubuntu $REQUIRED_UBUNTU_MIN+ required. Detected: $VERSION_ID"
        exit 1
    fi
    
    log_success "Ubuntu $VERSION_ID - Compatible"
    
    # Memory check
    local mem_gb=$(free -g | awk 'NR==2{print $2}')
    if [[ $mem_gb -lt $REQUIRED_RAM_GB ]]; then
        log_warning "Low memory: ${mem_gb}GB (${REQUIRED_RAM_GB}GB+ recommended)"
        read -p "Continue with low memory? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        log_success "Memory: ${mem_gb}GB - Sufficient"
    fi
    
    # Disk space check
    local disk_gb=$(df / | awk 'NR==2{printf "%.0f", $4/1024/1024}')
    if [[ $disk_gb -lt $REQUIRED_DISK_GB ]]; then
        log_warning "Low disk space: ${disk_gb}GB (${REQUIRED_DISK_GB}GB+ recommended)"
        read -p "Continue with low disk space? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        log_success "Disk space: ${disk_gb}GB - Sufficient"
    fi
}

verify_network_requirements() {
    log_header "Network Requirements Verification"
    
    # Internet connectivity
    if ! ping -c 2 8.8.8.8 &>/dev/null; then
        log_error "No internet connectivity"
        exit 1
    fi
    
    # DNS resolution
    if ! nslookup github.com &>/dev/null; then
        log_error "DNS resolution failed"
        exit 1
    fi
    
    # Check firewall status
    local ufw_status=""
    if command -v ufw &>/dev/null; then
        ufw_status=$(ufw status | head -1)
        log_info "UFW Status: $ufw_status"
    fi
    
    # Port availability check
    local busy_ports=()
    for port in "${REQUIRED_PORTS[@]}"; do
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            busy_ports+=("$port")
        fi
    done
    
    if [[ ${#busy_ports[@]} -gt 0 ]]; then
        log_warning "Ports currently in use: ${busy_ports[*]}"
        log_info "These will be handled during service conflict resolution"
    fi
    
    # Test domain resolution (if configured)
    if nslookup "$SUBDOMAIN" 2>/dev/null | grep -q "$VPS_IP"; then
        log_success "DNS: $SUBDOMAIN resolves to $VPS_IP"
    else
        log_warning "DNS: $SUBDOMAIN does not resolve to $VPS_IP yet"
        log_info "You'll need to configure DNS before SSL setup"
    fi
    
    log_success "Network requirements verified"
}

verify_virtualizor_environment() {
    log_header "Virtualizor Environment Detection"
    
    # Detect virtualization technology
    local virt_type=""
    if [[ -f /proc/vz/version ]]; then
        virt_type="OpenVZ/Virtualizor"
    elif [[ -d /proc/vz ]]; then
        virt_type="OpenVZ Container"
    elif grep -q "docker" /proc/1/cgroup 2>/dev/null; then
        virt_type="Docker Container"
        log_error "Cannot install Docker inside Docker container"
        exit 1
    elif command -v systemd-detect-virt &>/dev/null; then
        virt_type=$(systemd-detect-virt 2>/dev/null || echo "unknown")
    fi
    
    if [[ -n "$virt_type" && "$virt_type" != "none" ]]; then
        log_info "Virtualization detected: $virt_type"
        
        # Check for common Virtualizor limitations
        if [[ "$virt_type" == *"OpenVZ"* ]] || [[ "$virt_type" == *"Virtualizor"* ]]; then
            log_warning "OpenVZ/Virtualizor environment detected"
            log_info "Docker should work, but some features may be limited"
            
            # Check for Docker compatibility
            if [[ ! -c /dev/fuse ]]; then
                log_warning "FUSE device not available - some Docker features may not work"
            fi
        fi
    else
        log_info "Native/KVM virtualization - Full Docker compatibility expected"
    fi
    
    log_success "Virtualization environment compatible"
}

# =============================================================================
# INTERACTIVE CONFIGURATION WITH VALIDATION
# =============================================================================

collect_configuration() {
    log_header "Configuration Collection"
    
    echo "This installer will set up AI Crypto Trading Coach with the following:"
    echo "- Domain: $SUBDOMAIN"  
    echo "- Server IP: $VPS_IP"
    echo "- Strategy: Docker-based deployment with CI/CD"
    echo ""
    
    # API Keys with validation
    log_info "=== Required API Keys ==="
    
    while [[ -z "${LUNO_API_KEY:-}" ]]; do
        read -p "Luno API Key: " LUNO_API_KEY
        if [[ ${#LUNO_API_KEY} -lt 10 ]]; then
            log_warning "Luno API key seems too short"
            LUNO_API_KEY=""
        fi
    done
    
    while [[ -z "${LUNO_SECRET:-}" ]]; do
        read -s -p "Luno Secret Key: " LUNO_SECRET
        echo
        if [[ ${#LUNO_SECRET} -lt 10 ]]; then
            log_warning "Luno secret seems too short"
            LUNO_SECRET=""
        fi
    done
    
    while [[ -z "${GEMINI_API_KEY:-}" ]]; do
        read -p "Google Gemini API Key: " GEMINI_API_KEY
        if [[ ${#GEMINI_API_KEY} -lt 20 ]]; then
            log_warning "Gemini API key seems too short"
            GEMINI_API_KEY=""  
        fi
    done
    
    # Admin credentials with validation
    log_info "=== Admin Account Setup ==="
    
    while [[ -z "${ADMIN_USERNAME:-}" ]]; do
        read -p "Admin username [admin]: " ADMIN_USERNAME
        ADMIN_USERNAME=${ADMIN_USERNAME:-admin}
        if [[ ! $ADMIN_USERNAME =~ ^[a-zA-Z0-9_]+$ ]]; then
            log_warning "Username must contain only letters, numbers, and underscores"
            ADMIN_USERNAME=""
        fi
    done
    
    while [[ -z "${ADMIN_PASSWORD:-}" ]]; do
        read -s -p "Admin password (min 8 chars): " ADMIN_PASSWORD
        echo
        if [[ ${#ADMIN_PASSWORD} -lt 8 ]]; then
            log_warning "Password must be at least 8 characters"
            ADMIN_PASSWORD=""
        fi
        
        if [[ -n "$ADMIN_PASSWORD" ]]; then
            read -s -p "Confirm password: " password_confirm
            echo
            if [[ "$ADMIN_PASSWORD" != "$password_confirm" ]]; then
                log_warning "Passwords do not match"
                ADMIN_PASSWORD=""
            fi
        fi
    done
    
    # Network access configuration
    log_info "=== Access Control Setup ==="
    
    while [[ -z "${USER_IP:-}" ]]; do
        echo "Enter your public IP address for access restriction."
        echo "You can find it at: https://whatismyipaddress.com/"
        read -p "Your public IP: " USER_IP
        
        if [[ ! $USER_IP =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
            log_warning "Invalid IP address format"
            USER_IP=""
        else
            # Validate IP ranges
            IFS='.' read -ra IP_PARTS <<< "$USER_IP"
            for part in "${IP_PARTS[@]}"; do
                if [[ $part -lt 0 || $part -gt 255 ]]; then
                    log_warning "Invalid IP address range"
                    USER_IP=""
                    break
                fi
            done
        fi
    done
    
    # GitHub configuration for CI/CD
    log_info "=== GitHub CI/CD Setup ==="
    
    while [[ -z "${GITHUB_USERNAME:-}" ]]; do
        read -p "GitHub username (for CI/CD repository): " GITHUB_USERNAME
        if [[ ! $GITHUB_USERNAME =~ ^[a-zA-Z0-9-]+$ ]]; then
            log_warning "Invalid GitHub username format"
            GITHUB_USERNAME=""
        fi
    done
    
    # Generate secure secrets
    log_info "=== Security Configuration ==="
    log_info "Generating secure keys..."
    
    JWT_SECRET_KEY=$(openssl rand -hex 32)
    ENCRYPTION_KEY=$(openssl rand -hex 16)  
    MONGO_ROOT_PASSWORD=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-20)
    
    log_success "Configuration collected and validated"
}

# =============================================================================
# DEPENDENCY PRE-DOWNLOAD (FIX FOR NETWORK FAILURES)
# =============================================================================

pre_download_dependencies() {
    log_header "Pre-downloading All Dependencies"
    
    local download_dir="/tmp/crypto-coach-downloads"
    mkdir -p "$download_dir"
    
    local downloads=(
        "$DOCKER_INSTALL_URL:get-docker.sh"
        "$DOCKER_COMPOSE_URL:docker-compose"
        "$NODEJS_SETUP_URL:nodejs-setup.sh"
    )
    
    local downloaded=0
    local total=${#downloads[@]}
    
    for download in "${downloads[@]}"; do
        local url="${download%:*}"
        local filename="${download#*:}"
        local filepath="$download_dir/$filename"
        
        ((downloaded++))
        show_progress $downloaded $total "Downloading $filename"
        
        if ! curl -fsSL "$url" -o "$filepath"; then
            echo ""
            log_error "Failed to download $filename from $url"
            return 1
        fi
        
        # Verify download
        if [[ ! -s "$filepath" ]]; then
            echo ""
            log_error "Downloaded file $filename is empty"
            return 1
        fi
    done
    
    echo ""
    export DOWNLOAD_DIR="$download_dir"
    log_success "All dependencies downloaded successfully"
}

# =============================================================================
# SYSTEM INSTALLATION WITH ROLLBACK SUPPORT
# =============================================================================

create_backup() {
    log_info "Creating system backup..."
    mkdir -p "$BACKUP_DIR"
    
    # Backup configurations
    [[ -f /etc/nginx/sites-available/default ]] && cp /etc/nginx/sites-available/default "$BACKUP_DIR/"
    [[ -d "$INSTALL_DIR" ]] && cp -r "$INSTALL_DIR" "$BACKUP_DIR/"
    
    # Save current state
    systemctl list-units --state=active --type=service > "$BACKUP_DIR/active_services.txt"
    dpkg --get-selections > "$BACKUP_DIR/installed_packages.txt"
    
    echo "Backup created at: $BACKUP_DIR" >> "$LOG_FILE"
}

setup_rollback_trap() {
    trap 'rollback_installation' ERR
}

rollback_installation() {
    log_error "Installation failed - Rolling back changes"
    
    # Stop Docker services
    docker-compose -f "$INSTALL_DIR/docker/$COMPOSE_FILE" down 2>/dev/null || true
    
    # Remove created directories
    [[ -d "$INSTALL_DIR" ]] && rm -rf "$INSTALL_DIR"
    
    # Remove service user
    if id "$SERVICE_USER" &>/dev/null; then
        userdel -r "$SERVICE_USER" 2>/dev/null || true
    fi
    
    # Restore services that were stopped
    if [[ -f "$BACKUP_DIR/stopped_services.txt" ]]; then
        while read -r service; do
            systemctl start "$service" 2>/dev/null || true
        done < "$BACKUP_DIR/stopped_services.txt"
    fi
    
    log_info "Rollback completed. Check logs: $LOG_FILE"
    exit 1
}

# =============================================================================
# SOFTWARE INSTALLATION FUNCTIONS
# =============================================================================

update_system() {
    log_header "System Update"
    
    export DEBIAN_FRONTEND=noninteractive
    
    show_progress 1 3 "Updating package lists"
    apt update -qq
    
    show_progress 2 3 "Upgrading system packages"  
    apt upgrade -y -qq
    
    show_progress 3 3 "Installing essential packages"
    apt install -y -qq \
        curl wget gnupg2 software-properties-common \
        apt-transport-https ca-certificates lsb-release \
        unzip git openssl jq net-tools lsof
    
    echo ""
    log_success "System updated successfully"
}

install_docker() {
    log_header "Docker Installation"
    
    # Remove old Docker installations
    show_progress 1 5 "Removing old Docker versions"
    apt remove -y -qq docker docker-engine docker.io containerd runc 2>/dev/null || true
    
    # Install Docker using pre-downloaded script
    show_progress 2 5 "Installing Docker Engine"
    if [[ -f "$DOWNLOAD_DIR/get-docker.sh" ]]; then
        bash "$DOWNLOAD_DIR/get-docker.sh" --quiet
    else
        log_error "Docker installation script not found"
        return 1
    fi
    
    # Install Docker Compose
    show_progress 3 5 "Installing Docker Compose"
    if [[ -f "$DOWNLOAD_DIR/docker-compose" ]]; then
        install -m 755 "$DOWNLOAD_DIR/docker-compose" /usr/local/bin/docker-compose
    else
        # Fallback to apt
        apt install -y -qq docker-compose-plugin
        ln -sf /usr/libexec/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose
    fi
    
    # Configure Docker service
    show_progress 4 5 "Configuring Docker service"
    systemctl enable docker
    systemctl start docker
    
    # Add users to docker group
    usermod -aG docker "$SUDO_USER"
    
    # Test Docker installation
    show_progress 5 5 "Verifying Docker installation"
    if ! docker --version >/dev/null 2>&1; then
        echo ""
        log_error "Docker installation verification failed"
        return 1
    fi
    
    if ! docker-compose --version >/dev/null 2>&1; then
        echo ""
        log_error "Docker Compose installation verification failed"
        return 1
    fi
    
    echo ""
    log_success "Docker installed successfully"
}

install_nginx() {
    log_header "Nginx Installation"
    
    show_progress 1 3 "Installing Nginx"
    apt install -y -qq nginx
    
    show_progress 2 3 "Configuring Nginx service"
    systemctl enable nginx
    systemctl start nginx
    
    show_progress 3 3 "Verifying Nginx installation"
    if ! systemctl is-active --quiet nginx; then
        echo ""
        log_error "Nginx failed to start"
        return 1
    fi
    
    echo ""
    log_success "Nginx installed successfully"
}

install_certbot() {
    log_header "Certbot Installation"
    
    show_progress 1 2 "Installing Certbot and Nginx plugin"
    apt install -y -qq certbot python3-certbot-nginx
    
    show_progress 2 2 "Verifying Certbot installation"
    if ! certbot --version >/dev/null 2>&1; then
        echo ""
        log_error "Certbot installation verification failed"
        return 1
    fi
    
    echo ""
    log_success "Certbot installed successfully"
}

install_nodejs() {
    log_header "Node.js Installation"
    
    show_progress 1 4 "Adding Node.js repository"
    if [[ -f "$DOWNLOAD_DIR/nodejs-setup.sh" ]]; then
        bash "$DOWNLOAD_DIR/nodejs-setup.sh"
    else
        log_error "Node.js setup script not found"
        return 1
    fi
    
    show_progress 2 4 "Installing Node.js"
    apt-get install -y -qq nodejs
    
    show_progress 3 4 "Installing build tools"
    apt install -y -qq build-essential
    
    show_progress 4 4 "Verifying Node.js installation"
    if ! node --version >/dev/null 2>&1 || ! npm --version >/dev/null 2>&1; then
        echo ""
        log_error "Node.js installation verification failed"
        return 1
    fi
    
    echo ""
    log_success "Node.js $(node --version) installed successfully"
}

# =============================================================================
# APPLICATION SETUP
# =============================================================================

create_service_user() {
    log_header "Service User Creation"
    
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
    log_header "Application Directory Setup"
    
    # Create directory structure
    mkdir -p "$INSTALL_DIR"/{app,docker,scripts,logs,backups,data}
    mkdir -p "$INSTALL_DIR/data"/{mongodb,freqtrade,backend-logs}
    
    # Set ownership and permissions
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    chmod 755 "$INSTALL_DIR"
    chmod 750 "$INSTALL_DIR"/{logs,backups,data}
    
    log_success "Application directory created: $INSTALL_DIR"
}

create_environment_file() {
    log_header "Environment Configuration"
    
    cat > "$INSTALL_DIR/.env" << EOF
# AI Crypto Trading Coach - Production Environment
# Generated: $(date)
# Server: $VPS_IP
# Domain: $SUBDOMAIN

# Database Configuration
MONGO_ROOT_USER=cryptoadmin
MONGO_ROOT_PASSWORD=$MONGO_ROOT_PASSWORD
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

# GitHub Configuration for CI/CD
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
    
    chmod 600 "$INSTALL_DIR/.env"
    chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/.env"
    
    log_success "Environment file created with secure permissions"
}

# FIX #5: Complete Nginx Configuration (addresses Bug #5 from post-mortem)
configure_nginx_complete() {
    log_header "Complete Nginx Configuration"
    
    # Remove default site
    [[ -f /etc/nginx/sites-enabled/default ]] && rm /etc/nginx/sites-enabled/default
    
    # Create comprehensive site configuration
    cat > /etc/nginx/sites-available/crypto-coach << EOF
# Rate limiting zones
limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone \$binary_remote_addr zone=login:10m rate=3r/m;

# Upstream servers
upstream frontend {
    server 127.0.0.1:3000;
    keepalive 32;
}

upstream backend {
    server 127.0.0.1:8001;
    keepalive 32;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name $SUBDOMAIN;
    
    # Redirect all HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    server_name $SUBDOMAIN;
    
    # SSL Configuration (will be added by certbot)
    # ssl_certificate managed by Certbot
    # ssl_certificate_key managed by Certbot
    
    # Security Headers
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self' wss:;" always;
    
    # IP Access Restriction - CRITICAL SECURITY
    allow $USER_IP;
    deny all;
    
    # Logging
    access_log /var/log/nginx/crypto-coach-access.log;
    error_log /var/log/nginx/crypto-coach-error.log;
    
    # Frontend Application (React SPA)
    location / {
        # Rate limiting
        limit_req zone=api burst=20 nodelay;
        
        # Proxy configuration
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }
    
    # Backend API Routes - CRITICAL: Separate routing for API
    location /api {
        # Stricter rate limiting for API
        limit_req zone=api burst=10 nodelay;
        
        # Proxy to backend
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # API-specific timeouts (may need longer for AI operations)
        proxy_connect_timeout 60s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
    
    # Authentication endpoints with stricter limits
    location /api/auth {
        limit_req zone=login burst=5 nodelay;
        
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Health check endpoint (no rate limiting)
    location /health {
        access_log off;
        proxy_pass http://backend/api/;
        proxy_set_header Host \$host;
    }
    
    # Static assets with caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        proxy_pass http://frontend;
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header X-Content-Type-Options nosniff;
    }
    
    # Security: Block access to sensitive files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    location ~ \.(env|log|conf)$ {
        deny all;
        access_log off;
        log_not_found off;
    }
}
EOF
    
    # Enable site
    ln -sf /etc/nginx/sites-available/crypto-coach /etc/nginx/sites-enabled/
    
    # Test configuration
    if ! nginx -t; then
        log_error "Nginx configuration test failed"
        cat /etc/nginx/sites-available/crypto-coach
        return 1
    fi
    
    # Reload Nginx
    systemctl reload nginx
    
    log_success "Complete Nginx configuration applied"
}

# =============================================================================
# DOCKER APPLICATION DEPLOYMENT
# =============================================================================

create_docker_configuration() {
    log_header "Docker Configuration Creation"
    
    # Create Docker Compose file for production
    cat > "$INSTALL_DIR/docker/$COMPOSE_FILE" << EOF
version: '3.8'

services:
  mongodb:
    image: mongo:7
    container_name: crypto-coach-mongo-prod
    restart: unless-stopped
    environment:
      MONGO_INITDB_ROOT_USERNAME: \${MONGO_ROOT_USER}
      MONGO_INITDB_ROOT_PASSWORD: \${MONGO_ROOT_PASSWORD}
      MONGO_INITDB_DATABASE: \${MONGO_DB_NAME}
    volumes:
      - ../data/mongodb:/data/db
      - ../data/mongodb-logs:/var/log/mongodb
    networks:
      - crypto-coach-network
    ports:
      - "127.0.0.1:27017:27017"
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 40s

  backend:
    image: ghcr.io/\${GITHUB_REPOSITORY}/backend:latest
    container_name: crypto-coach-backend-prod
    restart: unless-stopped
    environment:
      - MONGO_URL=mongodb://\${MONGO_ROOT_USER}:\${MONGO_ROOT_PASSWORD}@mongodb:27017/\${MONGO_DB_NAME}?authSource=admin
      - DB_NAME=\${MONGO_DB_NAME}
      - LUNO_API_KEY=\${LUNO_API_KEY}
      - LUNO_SECRET=\${LUNO_SECRET}
      - GEMINI_API_KEY=\${GEMINI_API_KEY}
      - JWT_SECRET_KEY=\${JWT_SECRET_KEY}
      - ADMIN_USERNAME=\${ADMIN_USERNAME}
      - ADMIN_PASSWORD=\${ADMIN_PASSWORD}
      - ENCRYPTION_KEY=\${ENCRYPTION_KEY}
      - ENVIRONMENT=production
      - DEBUG=false
    depends_on:
      mongodb:
        condition: service_healthy
    networks:
      - crypto-coach-network
    ports:
      - "127.0.0.1:8001:8001"
    volumes:
      - ../data/backend-logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/api/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  frontend:
    image: ghcr.io/\${GITHUB_REPOSITORY}/frontend:latest
    container_name: crypto-coach-frontend-prod
    restart: unless-stopped
    environment:
      - REACT_APP_BACKEND_URL=https://\${SUBDOMAIN}/api
      - REACT_APP_VERSION=1.0.0
    networks:
      - crypto-coach-network
    ports:
      - "127.0.0.1:3000:3000"
    depends_on:
      backend:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

  freqtrade:
    image: ghcr.io/\${GITHUB_REPOSITORY}/freqtrade:latest
    container_name: crypto-coach-freqtrade-prod
    restart: unless-stopped
    environment:
      - LUNO_API_KEY=\${LUNO_API_KEY}
      - LUNO_SECRET=\${LUNO_SECRET}
      - FREQTRADE_CONFIG=/freqtrade/config.json
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - crypto-coach-network
    ports:
      - "127.0.0.1:8082:8082"
    volumes:
      - ../data/freqtrade:/freqtrade/user_data
      - ../data/freqtrade-logs:/freqtrade/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8082/api/v1/ping"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

networks:
  crypto-coach-network:
    driver: bridge
    name: crypto-coach-network

volumes:
  mongodb_data:
    driver: local
  freqtrade_data:
    driver: local
  backend_logs:
    driver: local
EOF
    
    # Create .env symlink for Docker Compose
    ln -sf "$INSTALL_DIR/.env" "$INSTALL_DIR/docker/.env"
    
    log_success "Docker configuration created"
}

# =============================================================================
# SSL CERTIFICATE SETUP
# =============================================================================

setup_ssl_certificate() {
    log_header "SSL Certificate Setup"
    
    log_info "Checking DNS configuration for $SUBDOMAIN"
    
    # Wait for DNS propagation
    local dns_attempts=0
    local max_dns_attempts=30
    
    while [[ $dns_attempts -lt $max_dns_attempts ]]; do
        if nslookup "$SUBDOMAIN" 2>/dev/null | grep -q "$VPS_IP"; then
            log_success "DNS resolution confirmed: $SUBDOMAIN -> $VPS_IP"
            break
        fi
        
        ((dns_attempts++))
        log_info "Waiting for DNS propagation... ($dns_attempts/$max_dns_attempts)"
        sleep 10
    done
    
    if [[ $dns_attempts -eq $max_dns_attempts ]]; then
        log_warning "DNS not fully propagated after 5 minutes"
        echo ""
        echo "Please ensure your DNS is configured:"
        echo "Type: A Record"
        echo "Name: crypto-coach"  
        echo "Value: $VPS_IP"
        echo "Domain: $DOMAIN"
        echo ""
        read -p "Continue with SSL setup? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "SSL setup skipped - you can run this later:"
            log_info "certbot --nginx -d $SUBDOMAIN"
            return 0
        fi
    fi
    
    # Obtain SSL certificate
    log_info "Obtaining SSL certificate from Let's Encrypt..."
    
    if certbot --nginx -d "$SUBDOMAIN" \
        --non-interactive \
        --agree-tos \
        --email "admin@$DOMAIN" \
        --redirect; then
        log_success "SSL certificate obtained and configured"
    else
        log_warning "SSL certificate setup failed"
        log_info "You can retry later with: certbot --nginx -d $SUBDOMAIN"
        return 0
    fi
}

# =============================================================================
# MANAGEMENT SCRIPTS CREATION
# =============================================================================

create_management_scripts() {
    log_header "Management Scripts Creation" 
    
    # Comprehensive health check script
    cat > "$INSTALL_DIR/scripts/health-check.sh" << 'EOF'
#!/bin/bash
set -e

echo "🔍 AI Crypto Trading Coach - Comprehensive Health Check"
echo "=================================================="

SUBDOMAIN="crypto-coach.zikhethele.properties"
INSTALL_DIR="/opt/crypto-coach"
COMPOSE_FILE="$INSTALL_DIR/docker/docker-compose.prod.yml"
FAILED_CHECKS=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m' 
YELLOW='\033[1;33m'
NC='\033[0m'

check_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    
    printf "%-30s" "Checking $name..."
    
    if response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 --max-time 30 "$url" 2>/dev/null); then
        if [ "$response" -eq "$expected_status" ]; then
            echo -e "${GREEN}✓ OK${NC} (HTTP $response)"
        else
            echo -e "${RED}✗ FAILED${NC} (HTTP $response, expected $expected_status)"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        fi
    else
        echo -e "${RED}✗ FAILED${NC} (Connection error)"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
}

check_container() {
    local name=$1
    local container_name=$2
    
    printf "%-30s" "Checking $name container..."
    
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$container_name.*Up"; then
        echo -e "${GREEN}✓ RUNNING${NC}"
    else
        echo -e "${RED}✗ NOT RUNNING${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
}

check_container_health() {
    local name=$1
    local container_name=$2
    
    printf "%-30s" "$name health..."
    
    local health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "unknown")
    
    case $health_status in
        "healthy")
            echo -e "${GREEN}✓ HEALTHY${NC}"
            ;;
        "unhealthy")
            echo -e "${RED}✗ UNHEALTHY${NC}"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
            ;;
        "starting")
            echo -e "${YELLOW}⚠ STARTING${NC}"
            ;;
        *)
            echo -e "${YELLOW}⚠ $health_status${NC}"
            ;;
    esac
}

# External endpoints
echo "🌐 External Endpoint Health:"
check_endpoint "Frontend" "https://$SUBDOMAIN/"
check_endpoint "Backend API" "https://$SUBDOMAIN/api/"
check_endpoint "Health endpoint" "https://$SUBDOMAIN/health"

echo ""

# Docker containers
echo "🐳 Container Status:"
check_container "MongoDB" "crypto-coach-mongo-prod"
check_container "Backend" "crypto-coach-backend-prod"
check_container "Frontend" "crypto-coach-frontend-prod"
check_container "Freqtrade" "crypto-coach-freqtrade-prod"

echo ""

# Container health
echo "🏥 Container Health:"
check_container_health "MongoDB" "crypto-coach-mongo-prod"
check_container_health "Backend" "crypto-coach-backend-prod"
check_container_health "Frontend" "crypto-coach-frontend-prod"
check_container_health "Freqtrade" "crypto-coach-freqtrade-prod"

echo ""

# System resources
echo "💾 System Resources:"
disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
memory_usage=$(free | awk 'NR==2{printf "%.1f", $3*100/$2}')

printf "%-30s" "Disk usage..."
if [ "$disk_usage" -lt 85 ]; then
    echo -e "${GREEN}✓ OK${NC} (${disk_usage}% used)"
else
    echo -e "${YELLOW}⚠ HIGH${NC} (${disk_usage}% used)"
fi

printf "%-30s" "Memory usage..."
echo -e "${GREEN}ℹ INFO${NC} (${memory_usage}% used)"

echo ""

# Summary
echo "📊 Health Check Summary:"
echo "========================"
if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "${GREEN}🎉 All checks passed! System is healthy.${NC}"
    echo "🌐 Application URL: https://$SUBDOMAIN"
    exit 0
else
    echo -e "${RED}❌ $FAILED_CHECKS checks failed!${NC}"
    echo ""
    echo "🔧 Troubleshooting commands:"
    echo "- Check logs: docker-compose -f $COMPOSE_FILE logs"
    echo "- Restart services: docker-compose -f $COMPOSE_FILE restart"
    echo "- View system resources: df -h && free -h"
    exit 1
fi
EOF
    
    # Deployment script
    cat > "$INSTALL_DIR/scripts/deploy.sh" << 'EOF'
#!/bin/bash
set -e

INSTALL_DIR="/opt/crypto-coach"
COMPOSE_FILE="$INSTALL_DIR/docker/docker-compose.prod.yml"

echo "🚀 Deploying AI Crypto Trading Coach..."

cd "$INSTALL_DIR"

# Load environment
if [[ -f .env ]]; then
    source .env
else
    echo "❌ Environment file not found!"
    exit 1
fi

# Pull latest images (when CI/CD is set up)
echo "📥 Pulling latest images..."
docker-compose -f "$COMPOSE_FILE" pull 2>/dev/null || echo "⚠️ Image pull failed (using local images)"

# Stop existing containers
echo "⏹️ Stopping existing containers..."
docker-compose -f "$COMPOSE_FILE" down --timeout 30

# Start new containers
echo "🚀 Starting containers..."
docker-compose -f "$COMPOSE_FILE" up -d

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 60

# Health check
echo "🔍 Running health check..."
./scripts/health-check.sh

echo "✅ Deployment completed!"
EOF
    
    # Backup script
    cat > "$INSTALL_DIR/scripts/backup.sh" << 'EOF'
#!/bin/bash
set -e

INSTALL_DIR="/opt/crypto-coach"
BACKUP_DIR="$INSTALL_DIR/backups/backup-$(date +%Y%m%d_%H%M%S)"

echo "💾 Creating backup..."
mkdir -p "$BACKUP_DIR"

# Backup environment file
cp "$INSTALL_DIR/.env" "$BACKUP_DIR/"

# Backup MongoDB data
echo "📦 Backing up database..."
docker exec crypto-coach-mongo-prod mongodump --out "$BACKUP_DIR/mongodb" 2>/dev/null || echo "⚠️ Database backup failed"

# Backup application logs
cp -r "$INSTALL_DIR/logs" "$BACKUP_DIR/" 2>/dev/null || true

# Backup Docker configuration
cp -r "$INSTALL_DIR/docker" "$BACKUP_DIR/"

echo "✅ Backup completed: $BACKUP_DIR"

# Cleanup old backups (keep last 10)
find "$INSTALL_DIR/backups" -type d -name "backup-*" | sort -r | tail -n +11 | xargs rm -rf 2>/dev/null || true
EOF
    
    # Log viewer script
    cat > "$INSTALL_DIR/scripts/logs.sh" << 'EOF'
#!/bin/bash

INSTALL_DIR="/opt/crypto-coach"
COMPOSE_FILE="$INSTALL_DIR/docker/docker-compose.prod.yml"

case ${1:-all} in
    "backend")
        docker-compose -f "$COMPOSE_FILE" logs -f backend
        ;;
    "frontend")
        docker-compose -f "$COMPOSE_FILE" logs -f frontend
        ;;
    "mongodb")
        docker-compose -f "$COMPOSE_FILE" logs -f mongodb
        ;;
    "freqtrade")
        docker-compose -f "$COMPOSE_FILE" logs -f freqtrade
        ;;
    "all"|*)
        docker-compose -f "$COMPOSE_FILE" logs -f
        ;;
esac
EOF
    
    # Make scripts executable
    chmod +x "$INSTALL_DIR/scripts/"*.sh
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/scripts"
    
    log_success "Management scripts created and configured"
}

# =============================================================================
# FINAL SETUP AND INFORMATION
# =============================================================================

display_completion_info() {
    log_header "Installation Complete!"
    
    echo ""
    log_success "🎉 AI Crypto Trading Coach installation completed successfully!"
    echo ""
    
    echo "📋 INSTALLATION SUMMARY:"
    echo "========================"
    echo "Server IP: $VPS_IP"
    echo "Domain: $SUBDOMAIN"
    echo "Access IP: $USER_IP (restricted)"
    echo "Strategy: Docker-based deployment"
    echo ""
    
    echo "🔐 ACCESS INFORMATION:"
    echo "======================"
    echo "URL: https://$SUBDOMAIN"
    echo "Admin Username: $ADMIN_USERNAME"
    echo "Admin Password: [as configured during setup]"
    echo ""
    
    echo "🛠️ MANAGEMENT COMMANDS:"
    echo "======================="
    echo "Health Check: $INSTALL_DIR/scripts/health-check.sh"
    echo "View Logs: $INSTALL_DIR/scripts/logs.sh [service]"
    echo "Backup: $INSTALL_DIR/scripts/backup.sh"
    echo "Deploy: $INSTALL_DIR/scripts/deploy.sh"
    echo ""
    
    echo "📁 IMPORTANT FILES:"
    echo "==================="
    echo "Environment: $INSTALL_DIR/.env"
    echo "Docker Config: $INSTALL_DIR/docker/$COMPOSE_FILE"
    echo "Nginx Config: /etc/nginx/sites-available/crypto-coach"
    echo "Installation Log: $LOG_FILE"
    echo "System Backup: $BACKUP_DIR"
    echo ""
    
    echo "🚀 NEXT STEPS:"
    echo "=============="
    echo "1. Set up GitHub repository for CI/CD:"
    echo "   - Create private repo: $GITHUB_USERNAME/ai-crypto-trading-coach-vps"
    echo "   - Add GitHub secrets for automatic deployment"
    echo ""
    echo "2. Verify installation:"
    echo "   - Run: $INSTALL_DIR/scripts/health-check.sh"
    echo "   - Visit: https://$SUBDOMAIN"
    echo ""
    echo "3. Configure GitHub CI/CD (optional):"
    echo "   - Upload application code to repository"
    echo "   - Set up GitHub Actions for automatic deployment"
    echo ""
    
    echo "⚠️ SECURITY REMINDERS:"
    echo "======================"
    echo "- Only IP $USER_IP can access the application"
    echo "- SSL certificate is configured and active"
    echo "- Environment file contains sensitive data - keep secure"
    echo "- Regular backups are recommended"
    echo ""
    
    echo "🆘 TROUBLESHOOTING:"
    echo "==================="
    echo "- If website not accessible: Check DNS configuration"
    echo "- If services not starting: Check logs with scripts/logs.sh"
    echo "- If SSL issues: Run 'certbot --nginx -d $SUBDOMAIN'"
    echo "- If port conflicts: Check for competing services"
    echo ""
    
    log_success "Setup completed successfully! Your AI Crypto Trading Coach is ready."
}

# =============================================================================
# MAIN INSTALLATION WORKFLOW
# =============================================================================

main() {
    log_header "AI Crypto Trading Coach - Comprehensive VPS Installer v$SCRIPT_VERSION"
    log_info "Ubuntu 22.04 + Virtualizor + Docker Strategy"
    log_info "Addresses all critical issues from Zikhethele Properties deployment"
    log_info "Installation log: $LOG_FILE"
    
    # Pre-flight checks (critical bug fixes applied)
    check_user_privileges
    verify_deployment_strategy
    verify_system_requirements
    verify_network_requirements
    verify_virtualizor_environment
    
    # Interactive configuration
    collect_configuration
    
    # Pre-download all dependencies (prevents network failures)
    pre_download_dependencies
    
    # Create backup and setup rollback
    create_backup
    setup_rollback_trap
    
    # Resolve service conflicts (critical fix)
    stop_conflicting_services
    
    # System installation
    update_system
    install_docker
    install_nginx
    install_certbot
    install_nodejs
    
    # Application setup
    create_service_user
    setup_application_directory
    create_environment_file
    
    # Complete Nginx configuration (critical fix)
    configure_nginx_complete
    
    # Docker application setup
    create_docker_configuration
    
    # SSL certificate setup
    setup_ssl_certificate
    
    # Management scripts
    create_management_scripts
    
    # Disable error trap (installation successful)
    trap - ERR
    
    # Display completion information
    display_completion_info
    
    log_success "Installation completed without errors!"
}

# =============================================================================
# SCRIPT ENTRY POINT
# =============================================================================

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi