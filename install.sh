#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# InfraMind Installation Script
echo -e "${BLUE}"
cat << "EOF"
  ___        __           __  __ _           _
 |_ _|_ __  / _|_ __ __ _|  \/  (_)_ __   __| |
  | || '_ \| |_| '__/ _` | |\/| | | '_ \ / _` |
  | || | | |  _| | | (_| | |  | | | | | | (_| |
 |___|_| |_|_| |_|  \__,_|_|  |_|_|_| |_|\__,_|

 Intelligent CI/CD Optimization Engine

EOF
echo -e "${NC}"

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed.${NC}"
    echo "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed.${NC}"
    echo "Please install Docker Compose from https://docs.docker.com/compose/install/"
    exit 1
fi

# Use 'docker compose' (v2) or 'docker-compose' (v1)
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

echo -e "${GREEN}✓ Docker found${NC}"
echo -e "${GREEN}✓ Docker Compose found${NC}"

# Check if running from cloned repo or need to clone
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${YELLOW}Cloning InfraMind repository...${NC}"

    INSTALL_DIR="${INSTALL_DIR:-$HOME/inframind}"

    if [ -d "$INSTALL_DIR" ]; then
        echo -e "${YELLOW}Directory $INSTALL_DIR already exists.${NC}"
        read -p "Remove and re-clone? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$INSTALL_DIR"
        else
            echo -e "${RED}Installation cancelled.${NC}"
            exit 1
        fi
    fi

    git clone https://github.com/yourorg/inframind.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
else
    echo -e "${GREEN}✓ Running from InfraMind repository${NC}"
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env configuration file...${NC}"
    cp .env.example .env

    # Generate random API key
    API_KEY=$(openssl rand -hex 32 2>/dev/null || cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)

    # Update .env with generated values
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/your-secret-api-key-here/$API_KEY/" .env
    else
        # Linux
        sed -i "s/your-secret-api-key-here/$API_KEY/" .env
    fi

    echo -e "${GREEN}✓ Created .env file with generated API key${NC}"
else
    echo -e "${GREEN}✓ Found existing .env file${NC}"
fi

# Pull latest images
echo -e "${YELLOW}Pulling Docker images...${NC}"
$DOCKER_COMPOSE pull

# Start services
echo -e "${YELLOW}Starting InfraMind services...${NC}"
$DOCKER_COMPOSE up -d

# Wait for services to be healthy
echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 10

# Check service health
echo -e "${YELLOW}Checking service health...${NC}"

check_service() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ $service is healthy${NC}"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done

    echo -e "${RED}✗ $service failed to start${NC}"
    return 1
}

check_service "API" "http://localhost:8081/health"
check_service "Grafana" "http://localhost:3001/api/health"
check_service "Prometheus" "http://localhost:9092/-/healthy"

# Generate demo data (optional)
echo ""
read -p "Generate demo data for testing? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo -e "${YELLOW}Generating demo data...${NC}"
    $DOCKER_COMPOSE exec -T api python app/scripts/generate_demo_data.py
    echo -e "${GREEN}✓ Demo data generated${NC}"
fi

# Display access information
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}InfraMind is now running!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Access the services:${NC}"
echo ""
echo -e "  📊 API Documentation:  ${YELLOW}http://localhost:8081/docs${NC}"
echo -e "  📈 Grafana Dashboards: ${YELLOW}http://localhost:3001${NC} (admin/admin)"
echo -e "  🔍 Prometheus:         ${YELLOW}http://localhost:9092${NC}"
echo ""
echo -e "${BLUE}Quick test:${NC}"
echo ""
echo -e "  curl -X POST http://localhost:8081/optimize \\"
echo -e "    -H 'Content-Type: application/json' \\"
echo -e "    -d '{\"repo\":\"test/repo\",\"branch\":\"main\"}'"
echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo ""
echo -e "  View logs:    ${YELLOW}$DOCKER_COMPOSE logs -f${NC}"
echo -e "  Stop:         ${YELLOW}$DOCKER_COMPOSE stop${NC}"
echo -e "  Restart:      ${YELLOW}$DOCKER_COMPOSE restart${NC}"
echo -e "  Shutdown:     ${YELLOW}$DOCKER_COMPOSE down${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo ""
echo -e "  1. View the API docs at http://localhost:8081/docs"
echo -e "  2. Check out Grafana dashboards at http://localhost:3001"
echo -e "  3. Integrate with your CI/CD pipeline (see docs/integration/)"
echo ""
echo -e "${GREEN}Happy building! 🚀${NC}"
echo ""

# Save API key to a file for reference
API_KEY=$(grep INFRAMIND_API_KEY .env | cut -d '=' -f2)
cat > .inframind-credentials << EOF
InfraMind Credentials
=====================

API URL: http://localhost:8081
API Key: $API_KEY

Grafana URL: http://localhost:3001
Grafana User: admin
Grafana Password: admin

Keep this file secure and do not commit it to version control!
EOF

echo -e "${YELLOW}Credentials saved to .inframind-credentials${NC}"
