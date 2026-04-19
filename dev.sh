#!/usr/bin/env bash
# Development server with automatic port fallback

set -e

DEFAULT_PORT=8000
PORT=$DEFAULT_PORT

# Find next available port starting from DEFAULT_PORT
find_available_port() {
    local port=$1
    while netstat -tuln 2>/dev/null | grep -q ":$port " || \
          ss -tuln 2>/dev/null | grep -q ":$port "; do
        echo "Port $port is in use, trying next port..."
        port=$((port + 1))
    done
    echo "$port"
}

# Find available port
AVAILABLE_PORT=$(find_available_port $DEFAULT_PORT)

if [ "$AVAILABLE_PORT" != "$DEFAULT_PORT" ]; then
    echo "Port $DEFAULT_PORT is in use, starting server on port $AVAILABLE_PORT"
    PORT=$AVAILABLE_PORT
else
    echo "Starting server on default port $DEFAULT_PORT"
fi

# Check if venv is active
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

echo "Starting OCR API server on http://127.0.0.1:$PORT"
echo "Press Ctrl+C to stop"

python -m uvicorn src.api:app --host 127.0.0.1 --port $PORT
