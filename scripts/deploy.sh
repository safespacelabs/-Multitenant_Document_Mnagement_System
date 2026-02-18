#!/bin/bash

# Deployment Script — Dev & Staging environments
# Usage: ./scripts/deploy.sh [dev|staging]

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ $# -eq 0 ]; then
    echo -e "${RED}Error: environment required${NC}"
    echo "Usage: ./scripts/deploy.sh [dev|staging]"
    exit 1
fi

ENV=$1

case $ENV in
    dev)
        COMPOSE_FILE="docker-compose.dev.yml"
        ENV_FILE=".env.dev"
        BACKEND_PORT=8001
        BACKEND_CONTAINER="backend-dev"
        FRONTEND_CONTAINER="frontend-dev"
        ;;
    staging)
        COMPOSE_FILE="docker-compose.staging.yml"
        ENV_FILE=".env.staging"
        BACKEND_PORT=8002
        BACKEND_CONTAINER="backend-staging"
        FRONTEND_CONTAINER="frontend-staging"
        ;;
    *)
        echo -e "${RED}Error: invalid environment '$ENV'. Use: dev | staging${NC}"
        exit 1
        ;;
esac

echo -e "${GREEN}Deploying to [$ENV] environment...${NC}"

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: $ENV_FILE not found. Create it from ${ENV_FILE}.example${NC}"
    exit 1
fi

# Load env vars
export $(cat "$ENV_FILE" | grep -v '^#' | xargs)

# Pull latest code
if [ -d ".git" ]; then
    echo -e "${GREEN}Pulling latest changes...${NC}"
    git pull || echo -e "${YELLOW}Warning: git pull failed${NC}"
fi

# Stop existing containers
echo -e "${GREEN}Stopping existing containers...${NC}"
docker-compose -f "$COMPOSE_FILE" down

# Clean up old images
docker image prune -f

# Build and start
echo -e "${GREEN}Building and starting containers...${NC}"
docker-compose -f "$COMPOSE_FILE" up -d --build

echo "Waiting for services to start..."
sleep 15

docker-compose -f "$COMPOSE_FILE" ps

# Health check
echo -e "${GREEN}Running health check...${NC}"
max_attempts=10
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -sf "http://localhost:${BACKEND_PORT}/health" > /dev/null; then
        echo -e "${GREEN}Backend is healthy!${NC}"
        break
    fi
    attempt=$((attempt + 1))
    echo "Attempt $attempt/$max_attempts — retrying in 3s..."
    sleep 3
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}Health check failed. Showing logs:${NC}"
    docker-compose -f "$COMPOSE_FILE" logs "$BACKEND_CONTAINER"
    exit 1
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Deployed to [$ENV] successfully!${NC}"
echo -e "${GREEN}========================================${NC}"

case $ENV in
    dev)
        echo "  Frontend : https://devapp.safespacelabs.cloud"
        echo "  Backend  : https://devapi.safespacelabs.cloud"
        ;;
    staging)
        echo "  Frontend : https://qaapp.safespacelabs.cloud"
        echo "  Backend  : https://qaapi.safespacelabs.cloud"
        ;;
esac

echo ""
echo "Useful commands:"
echo "  Logs    : docker-compose -f $COMPOSE_FILE logs -f"
echo "  Stop    : docker-compose -f $COMPOSE_FILE down"
echo "  Restart : docker-compose -f $COMPOSE_FILE restart"
