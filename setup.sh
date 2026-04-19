#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"
REQUIREMENTS="$PROJECT_ROOT/requirements.txt"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at $VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi

echo "Activating virtual environment"
source "$VENV_DIR/bin/activate"

echo "Installing/upgrading dependencies from requirements.txt"
pip install --upgrade pip --quiet
pip install -r "$REQUIREMENTS"

echo "Ensuring logs directory exists"
mkdir -p "$PROJECT_ROOT/logs"

echo ""
echo "Running lint check..."
ruff check src/ tests/ examples/ --fix
echo "Running format check..."
ruff format src/ tests/ examples/

echo ""
echo "Setup complete. Activate the environment with: source .venv/bin/activate"
echo "Start the server with: uvicorn src.api:app --reload"
