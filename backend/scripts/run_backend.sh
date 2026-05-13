#!/usr/bin/env bash
# Backend Startup Script
# Starts the FastAPI backend server with required environment variables

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "AI Researcher Backend Startup"
echo "=========================================="

# Check required environment variables
# if [ -z "${LLM_API_KEY:-}" ]; then
#     echo "ERROR: LLM_API_KEY environment variable is required"
#     echo "Please set it before starting the backend:"
#     echo "  export LLM_API_KEY=sk-..."
#     exit 1
# fi

# Set defaults for optional variables
export LLM_PROVIDER=${LLM_PROVIDER:-moonshot}
export LLM_MODEL=${LLM_MODEL:-moonshot-v1-8k}
export LLM_BASE_URL=${LLM_BASE_URL:-https://api.moonshot.cn/v1}
export LLM_TIMEOUT_S=${LLM_TIMEOUT_S:-60}

# Backend server configuration
export BACKEND_HOST=${BACKEND_HOST:-127.0.0.1}
export BACKEND_PORT=${BACKEND_PORT:-8005}

kill_project_listener_on_port() {
    local port="$1"
    local pids

    pids="$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
    [ -z "$pids" ] && return 0

    for pid in $pids; do
        local cwd cmd
        cwd="$(readlink -f "/proc/$pid/cwd" 2>/dev/null || true)"
        cmd="$(ps -p "$pid" -o args= 2>/dev/null || true)"

        if echo "$cwd $cmd" | grep -q "$BACKEND_DIR"; then
            echo "Stopping stale backend process PID=$pid on :$port"
            kill "$pid" 2>/dev/null || true
        fi
    done
}

cleanup_ports() {
    # Clean likely stale backend ports used by this project.
    for p in 8005 8006; do
        kill_project_listener_on_port "$p"
    done
}

on_exit() {
    cleanup_ports
}

trap on_exit EXIT INT TERM

echo ""
echo "Configuration:"
echo "  LLM Provider: $LLM_PROVIDER"
echo "  LLM Model: $LLM_MODEL"
echo "  LLM Base URL: $LLM_BASE_URL"
echo "  Backend: http://$BACKEND_HOST:$BACKEND_PORT"
echo ""

# Activate conda environment if needed
if [ -n "$CONDA_DEFAULT_ENV" ]; then
    echo "Using conda environment: $CONDA_DEFAULT_ENV"
else
    echo "WARNING: No conda environment active"
    echo "Activate with: conda activate autollm"
fi

# Change to backend directory
cd "$BACKEND_DIR"

# Clean stale project backend ports from previous sessions
cleanup_ports

# Start server
echo ""
echo "Starting backend server..."
echo "Press Ctrl+C to stop"
echo ""

uvicorn app.main:app \
    --host "$BACKEND_HOST" \
    --port "$BACKEND_PORT" \
    --reload
