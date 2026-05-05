#!/bin/bash

# VPS Initial Setup Script for SmartNyumba
# Run this script on your Hetzner VPS as root user

set -e

echo "======================================"
echo "SmartNyumba VPS Initial Setup"
echo "======================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (use: sudo bash vps-setup.sh)${NC}"
    exit 1
fi

echo -e "${YELLOW}Updating system packages...${NC}"
apt update && apt upgrade -y

echo -e "${YELLOW}Installing essential packages...${NC}"
apt install -y curl git wget nano ufw htop

echo -e "${YELLOW}Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl start docker
    systemctl enable docker
    echo -e "${GREEN}Docker installed successfully${NC}"
else
    echo -e "${GREEN}Docker is already installed${NC}"
fi

echo -e "${YELLOW}Installing Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}Docker Compose installed successfully${NC}"
else
    echo -e "${GREEN}Docker Compose is already installed${NC}"
fi

echo -e "${YELLOW}Creating deployment directory...${NC}"
mkdir -p /opt/smartnyumba
chmod 755 /opt/smartnyumba

echo -e "${YELLOW}Configuring firewall...${NC}"
# Allow SSH (important - don't lock yourself out!)
ufw allow 22/tcp

# Allow application port
ufw allow 8080/tcp

# Enable firewall (with confirmation)
echo -e "${YELLOW}About to enable firewall. Make sure SSH (port 22) is allowed!${NC}"
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "y" | ufw enable
    echo -e "${GREEN}Firewall configured${NC}"
else
    echo -e "${YELLOW}Firewall configuration skipped${NC}"
fi

echo -e "${YELLOW}Setting up swap (if not exists)...${NC}"
if ! swapon --show | grep -q '/swapfile'; then
    # Create 2GB swap
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo -e "${GREEN}Swap created and enabled${NC}"
else
    echo -e "${GREEN}Swap already exists${NC}"
fi

echo -e "${YELLOW}Configuring Docker log rotation...${NC}"
cat > /etc/docker/daemon.json <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF
systemctl reload docker

echo -e "${YELLOW}Creating daily cleanup cron job...${NC}"
cat > /etc/cron.daily/docker-cleanup <<'EOF'
#!/bin/bash
# Clean up old Docker resources
docker system prune -f --filter "until=72h"
EOF
chmod +x /etc/cron.daily/docker-cleanup

echo -e "${GREEN}======================================"
echo "VPS Setup Complete!"
echo "======================================${NC}"
echo ""
echo "Installed versions:"
docker --version
docker-compose --version
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Add your SSH public key to ~/.ssh/authorized_keys"
echo "2. Configure GitHub Secrets for automated deployment"
echo "3. Push to GitHub main branch to trigger deployment"
echo ""
echo -e "${YELLOW}Or deploy manually:${NC}"
echo "cd /opt/smartnyumba"
echo "git clone <your-repo-url> ."
echo "cp .env.example .env"
echo "nano .env  # Configure your environment variables"
echo "./deploy.sh"
echo ""
echo -e "${GREEN}VPS is ready for SmartNyumba deployment!${NC}"
