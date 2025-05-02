#!/bin/bash
clear

COMPOSE_FILE="docker-compose.yml"
DEFAULT_PORT=11434
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$PROJECT_DIR"

# Stop and remove all containers
docker-compose down

# Remove old images for this project (images named mcp-*)
docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}' | grep mcp- | awk '{print $2}' | xargs -r docker rmi -f

# Find the current host port mapped to 11434 in the compose file
CURRENT_PORT=$(grep -oE '[0-9]+:11434' "$COMPOSE_FILE" | head -n1 | cut -d: -f1)
if [[ -z "$CURRENT_PORT" ]]; then
    CURRENT_PORT=$DEFAULT_PORT
fi

# Find a free port starting from CURRENT_PORT
PORT=$CURRENT_PORT
while lsof -i ":$PORT" >/dev/null 2>&1; do
    PORT=$((PORT+1))
done

# Update the port in docker-compose.yml (replace any <number>:11434 mapping)
sed -i "s/[0-9]\\+:11434/$PORT:11434/g" "$COMPOSE_FILE"
echo "Changed port mapping to $PORT:11434 in $COMPOSE_FILE"

# Bring up the stack
docker-compose up --build