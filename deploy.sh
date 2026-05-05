#!/bin/bash

set -e

echo "======================================"
echo "Starting SmartNyumba Deployment"
echo "======================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl start docker
    systemctl enable docker
    echo -e "${GREEN}Docker installed successfully${NC}"
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Installing Docker Compose...${NC}"
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}Docker Compose installed successfully${NC}"
fi

# Navigate to project directory
cd /opt/smartnyumba

echo -e "${YELLOW}Stopping existing containers...${NC}"
docker-compose down --remove-orphans || true

echo -e "${YELLOW}Pulling latest image from Docker Hub...${NC}"
docker-compose pull

echo -e "${YELLOW}Starting containers...${NC}"
docker-compose up -d

echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
sleep 10

# Check if containers are running
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}Containers are running${NC}"
else
    echo -e "${RED}Failed to start containers${NC}"
    docker-compose logs
    exit 1
fi

echo -e "${YELLOW}Running database migrations...${NC}"
docker-compose exec -T web python manage.py migrate --noinput

echo -e "${YELLOW}Collecting static files...${NC}"
docker-compose exec -T web python manage.py collectstatic --noinput || true

echo -e "${YELLOW}Checking container health...${NC}"
docker-compose ps

echo -e "${YELLOW}Cleaning up old images...${NC}"
docker image prune -f

echo -e "${GREEN}======================================"
echo "Deployment completed successfully!"
echo "======================================${NC}"
echo -e "Application is running on: ${GREEN}http://178.105.35.41:8080${NC}"
echo -e "To view logs: ${YELLOW}docker-compose -f /opt/smartnyumba/docker-compose.yml logs -f${NC}"
echo -e "To restart: ${YELLOW}docker-compose -f /opt/smartnyumba/docker-compose.yml restart${NC}"
echo -e "To stop: ${YELLOW}docker-compose -f /opt/smartnyumba/docker-compose.yml down${NC}"
