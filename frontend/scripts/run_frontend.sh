#!/usr/bin/env bash
# Frontend Startup Script
# Starts the Vite development server with port cleanup and strict binding

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$(dirname "$SCRIPT_DIR")"
FRONTEND_PORT="${FRONTEND_PORT:-5176}"
FRONTEND_HOST="${FRONTEND_HOST:-0.0.0.0}"

echo "=========================================="
echo "AI Researcher Frontend Startup"
echo "=========================================="

# Set frontend configuration
export VITE_USE_MOCK="${VITE_USE_MOCK:-false}"
export VITE_API_BASE_URL="${VITE_API_BASE_URL:-http://127.0.0.1:8005}"
export CHOKIDAR_USEPOLLING="${CHOKIDAR_USEPOLLING:-1}"
export CHOKIDAR_INTERVAL="${CHOKIDAR_INTERVAL:-150}"

echo ""
echo "Configuration:"
echo "  Use Mock API: $VITE_USE_MOCK"
echo "  Backend URL: $VITE_API_BASE_URL"
echo "  Frontend URL: http://$FRONTEND_HOST:$FRONTEND_PORT"
echo ""

kill_project_listener_on_port() {
    local port="$1"
    local pids

    pids="$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
    [ -z "$pids" ] && return 0

    for pid in $pids; do
        local cwd cmd
        cwd="$(readlink -f "/proc/$pid/cwd" 2>/dev/null || true)"
        cmd="$(ps -p "$pid" -o args= 2>/dev/null || true)"

        if echo "$cwd $cmd" | grep -q "$FRONTEND_DIR"; then
            echo "Stopping stale frontend process PID=$pid on :$port"
            kill "$pid" 2>/dev/null || true
        fi
    done
}

cleanup_ports() {
    # Clean likely stale project Vite ports.
    for p in 5173 5174 5175 5176; do
        kill_project_listener_on_port "$p"
    done
}

VITE_PID=""

on_exit() {
    if [ -n "${VITE_PID:-}" ] && kill -0 "$VITE_PID" 2>/dev/null; then
        kill "$VITE_PID" 2>/dev/null || true
        wait "$VITE_PID" 2>/dev/null || true
    fi
    cleanup_ports
}

trap on_exit EXIT INT TERM

# Change to frontend directory
cd "$FRONTEND_DIR"

# Clean stale project ports from previous sessions
cleanup_ports

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Start dev server
echo ""
echo "Starting frontend dev server..."
echo "Press Ctrl+C to stop"
echo ""

npx vite --host "$FRONTEND_HOST" --port "$FRONTEND_PORT" --strictPort &
VITE_PID=$!
wait "$VITE_PID"
