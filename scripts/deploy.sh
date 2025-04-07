#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${GREEN}==>${NC} $1"
}

print_error() {
    echo -e "${RED}Error:${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}Warning:${NC} $1"
}

# Parse arguments
WITH_DB=false
while [[ $# -gt 0 ]]; do
  case $1 in
    --with-db)
      WITH_DB=true
      shift
      ;;
    *)
      print_error "Unknown option: $1"
      echo "Usage: $0 [--with-db]"
      exit 1
      ;;
  esac
done

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker not found. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker compose &> /dev/null; then
    print_warning "Docker Compose v2 not found. Checking for legacy docker-compose..."
    if ! command -v docker-compose &> /dev/null; then
        print_error "Neither Docker Compose v2 nor legacy docker-compose found. Please install Docker Compose."
        exit 1
    else
        DOCKER_COMPOSE="docker-compose"
    fi
else
    DOCKER_COMPOSE="docker compose"
fi

# Check if .env.production exists
if [ ! -f .env.production ]; then
    print_step "Creating .env.production file from template..."
    if [ -f .env.production.example ]; then
        cp .env.production.example .env.production
        print_warning "Created .env.production from example. Please edit it with your actual configuration values."
        print_warning "Run this script again after updating the configuration."
        exit 0
    else
        print_error ".env.production.example not found. Please create a .env.production file manually."
        exit 1
    fi
fi

# Create required directories
print_step "Creating required directories..."
mkdir -p logs uploads data

# Set up the compose command
COMPOSE_CMD="$DOCKER_COMPOSE up -d --build"
if [ "$WITH_DB" = true ]; then
    print_step "Setting up with PostgreSQL database (for development)..."
    COMPOSE_CMD="$DOCKER_COMPOSE --profile dev up -d --build"
else
    print_step "Setting up API only (recommended for production)..."
fi

# Build and start the containers
print_step "Building and starting containers..."
$COMPOSE_CMD

# Wait for the API to start
print_step "Waiting for the API to start..."
sleep 10

# Check if the API is running
print_step "Checking API health..."
if curl -s http://localhost:8000/health > /dev/null; then
    print_step "API is running successfully!"
    echo -e "${GREEN}Deployment completed successfully!${NC}"
    echo "API is available at: http://localhost:8000"
    echo "API documentation is available at: http://localhost:8000/docs"
else
    print_error "API failed to start properly. Check the logs with: docker logs fama-api"
    echo "You can troubleshoot by running: $DOCKER_COMPOSE logs api"
fi

# Print deployment info
echo ""
echo "=== Deployment Information ==="
echo "API container: fama-api"
if [ "$WITH_DB" = true ]; then
    echo "Database container: fama-postgres (development only)"
    echo "PostgreSQL connection: postgresql://fama_user:postgres@localhost:5432/fama"
    echo "Note: This database is NOT automatically used by the API."
    echo "      API callers must provide their own database connection in requests."
fi
echo "Logs directory: ./logs"
echo "Uploads directory: ./uploads"
echo "Data directory: ./data"
echo ""
echo "To stop the services: $DOCKER_COMPOSE down"
echo "To view logs: $DOCKER_COMPOSE logs -f"
echo "To restart: $DOCKER_COMPOSE restart"
echo ""
echo "Remember: All configuration is provided by API callers in their requests."
echo "For more information, see the deployment documentation: documentation/deployment.md" 