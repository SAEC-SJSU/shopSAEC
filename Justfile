# SAEC Shop - Build & Deploy

NETWORK := "website-internal"

# Default: list available recipes
default:
    @just --list

# Ensure the shared network exists
_ensure-network:
    -docker network create {{NETWORK}} 2>/dev/null

# --- Frontend ---

# Build the frontend Docker image (empty VITE_API_URL = same-origin for production)
frontend-build VITE_API_URL="":
    docker build --build-arg VITE_API_URL="{{VITE_API_URL}}" -t saec-frontend .

# Run the frontend container
frontend-run PORT="3000": _ensure-network
    docker run -d --name saec-frontend --network {{NETWORK}} -p 127.0.0.1:{{PORT}}:3000 saec-frontend

# Rebuild and restart the frontend
frontend-rebuild VITE_API_URL="" PORT="3000":
    -docker stop saec-frontend
    -docker rm saec-frontend
    just frontend-build "{{VITE_API_URL}}"
    just frontend-run {{PORT}}

# --- Backend ---

# Build the backend Docker image
backend-build:
    docker build -t saec-backend ./backend

# Run the backend container
backend-run PORT="7676" ENV_FILE=".env.local": _ensure-network
    docker run -d --name saec-backend --network {{NETWORK}} -p 127.0.0.1:{{PORT}}:7676 -e ENV=prod --env-file {{ENV_FILE}} saec-backend

# Rebuild and restart the backend
backend-rebuild PORT="7676" ENV_FILE=".env.local":
    -docker stop saec-backend
    -docker rm saec-backend
    just backend-build
    just backend-run {{PORT}} {{ENV_FILE}}

# --- MongoDB ---

# Start MongoDB
mongo-up: _ensure-network
    docker compose -f config/mongodb/docker-compose.yml up -d

# Stop MongoDB
mongo-down:
    docker compose -f config/mongodb/docker-compose.yml down

# Restart MongoDB
mongo-restart:
    just mongo-down
    just mongo-up

# --- All Services ---

# Build all Docker images
build-all VITE_API_URL="":
    just frontend-build "{{VITE_API_URL}}"
    just backend-build

# Start everything (mongo + backend + frontend)
up VITE_API_URL="" BACKEND_PORT="7676" FRONTEND_PORT="3000" ENV_FILE=".env.local":
    just mongo-up
    just backend-rebuild {{BACKEND_PORT}} {{ENV_FILE}}
    just frontend-rebuild "{{VITE_API_URL}}" {{FRONTEND_PORT}}

# Stop everything
down:
    -docker stop saec-frontend saec-backend
    -docker rm saec-frontend saec-backend
    just mongo-down

# Rebuild and restart everything
rebuild VITE_API_URL="" BACKEND_PORT="7676" FRONTEND_PORT="3000" ENV_FILE=".env.local":
    just build-all "{{VITE_API_URL}}"
    just up "{{VITE_API_URL}}" {{BACKEND_PORT}} {{FRONTEND_PORT}} {{ENV_FILE}}

# --- Dev ---

# Run frontend dev server (no Docker)
dev:
    bun dev

# Run backend dev server (no Docker)
dev-backend:
    cd backend && uvicorn main:app --reload --port 7676

# --- Logs ---

# Tail frontend logs
logs-frontend:
    docker logs -f saec-frontend

# Tail backend logs
logs-backend:
    docker logs -f saec-backend

# Tail MongoDB logs
logs-mongo:
    docker logs -f saec-mongo

# Show status of all containers
status:
    @docker ps --filter "name=saec-" --format "table {{{{.Names}}}}\t{{{{.Status}}}}\t{{{{.Ports}}}}"
