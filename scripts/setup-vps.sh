#!/bin/bash

# VPS Initial Setup Script
# This script sets up a fresh VPS for hosting the multitenant document management system

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}VPS Initial Setup Script${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root or with sudo${NC}"
    exit 1
fi

# Update system packages
echo -e "${GREEN}Updating system packages...${NC}"
apt-get update
apt-get upgrade -y

# Install required packages
echo -e "${GREEN}Installing required packages...${NC}"
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    software-properties-common \
    git \
    ufw \
    fail2ban \
    htop \
    certbot \
    python3-certbot-nginx

# Install Docker
echo -e "${GREEN}Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    
    # Start and enable Docker
    systemctl start docker
    systemctl enable docker
    
    echo -e "${GREEN}Docker installed successfully${NC}"
else
    echo -e "${YELLOW}Docker is already installed${NC}"
fi

# Install Docker Compose
echo -e "${GREEN}Installing Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_VERSION="2.24.5"
    curl -L "https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    echo -e "${GREEN}Docker Compose installed successfully${NC}"
else
    echo -e "${YELLOW}Docker Compose is already installed${NC}"
fi

# Create application directory
echo -e "${GREEN}Creating application directory...${NC}"
mkdir -p ~/multitenant-app
cd ~/multitenant-app

# Create logs directory
mkdir -p logs

# Configure firewall
echo -e "${GREEN}Configuring firewall...${NC}"
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw status

# Configure fail2ban for SSH protection
echo -e "${GREEN}Configuring fail2ban...${NC}"
systemctl start fail2ban
systemctl enable fail2ban

# Install and configure Nginx
echo -e "${GREEN}Installing Nginx...${NC}"
if ! command -v nginx &> /dev/null; then
    apt-get install -y nginx
    systemctl start nginx
    systemctl enable nginx
    echo -e "${GREEN}Nginx installed successfully${NC}"
else
    echo -e "${YELLOW}Nginx is already installed${NC}"
fi

# Create nginx sites directory if it doesn't exist
mkdir -p /etc/nginx/sites-available
mkdir -p /etc/nginx/sites-enabled

# Set up log rotation
echo -e "${GREEN}Setting up log rotation...${NC}"
cat > /etc/logrotate.d/multitenant-app << 'EOF'
/var/log/nginx/*-access.log /var/log/nginx/*-error.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        if [ -f /var/run/nginx.pid ]; then
            kill -USR1 `cat /var/run/nginx.pid`
        fi
    endscript
}

~/multitenant-app/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 root root
}
EOF

# Display versions
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Installation Summary${NC}"
echo -e "${GREEN}========================================${NC}"
echo "Docker version:"
docker --version
echo ""
echo "Docker Compose version:"
docker-compose --version
echo ""
echo "Nginx version:"
nginx -v
echo ""

# Next steps
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}VPS Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Configure DNS records for your domain"
echo "   - dev-app.yourdomain.com"
echo "   - dev-api.yourdomain.com"
echo "   - staging-app.yourdomain.com"
echo "   - staging-api.yourdomain.com"
echo "   - app.yourdomain.com"
echo "   - api.yourdomain.com"
echo ""
echo "2. Clone your repository to ~/multitenant-app"
echo "   cd ~/multitenant-app"
echo "   git clone <your-repo-url> ."
echo ""
echo "3. Copy nginx configuration"
echo "   sudo cp nginx/nginx-vps.conf /etc/nginx/sites-available/multitenant-app"
echo "   sudo ln -s /etc/nginx/sites-available/multitenant-app /etc/nginx/sites-enabled/"
echo "   sudo nginx -t"
echo "   sudo systemctl reload nginx"
echo ""
echo "4. Obtain SSL certificates (after DNS is configured)"
echo "   sudo certbot --nginx -d dev-app.yourdomain.com"
echo "   sudo certbot --nginx -d dev-api.yourdomain.com"
echo "   sudo certbot --nginx -d staging-app.yourdomain.com"
echo "   sudo certbot --nginx -d staging-api.yourdomain.com"
echo "   sudo certbot --nginx -d app.yourdomain.com"
echo "   sudo certbot --nginx -d api.yourdomain.com"
echo ""
echo "5. Create environment files from templates"
echo "   cp .env.dev.example .env.dev"
echo "   cp .env.staging.example .env.staging"
echo "   cp .env.prod.example .env.prod"
echo "   # Edit each file with your actual values"
echo ""
echo "6. Set up GitHub Actions secrets in your repository"
echo ""
echo "7. Test deployment with: ./scripts/deploy.sh dev"
