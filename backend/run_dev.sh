#!/usr/bin/env bash
# Backend Dev Startup Script
# Finds a free port, writes it to .dev/ports.json, starts uvicorn.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR"
PROJECT_ROOT="$(dirname "$BACKEND_DIR")"
DEV_DIR="$PROJECT_ROOT/.dev"
PORTS_FILE="$DEV_DIR/ports.json"

DEFAULT_PORT="${BACKEND_PORT:-8005}"
HOST="${BACKEND_HOST:-127.0.0.1}"

echo "=========================================="
echo "AI Researcher Backend — Dev Startup"
echo "=========================================="

# --- Find a free port starting from DEFAULT_PORT ---
find_free_port() {
    /home/guiyao/miniconda3/bin/python - "$1" <<'PY'
import socket, sys
start = int(sys.argv[1])
for p in range(start, start + 20):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", p))
        print(p)
        break
    except OSError:
        pass
    finally:
        s.close()
PY
}

# Kill stale project listeners on a port
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
            echo "  Stopping stale backend PID=$pid on :$port"
            kill "$pid" 2>/dev/null || true
            sleep 1
        fi
    done
}

cleanup() {
    for p in 8005 8006 8007 8008 8009 8010; do
        kill_project_listener_on_port "$p"
    done
}

UVICORN_PID=""
on_exit() {
    if [ -n "${UVICORN_PID:-}" ] && kill -0 "$UVICORN_PID" 2>/dev/null; then
        kill "$UVICORN_PID" 2>/dev/null || true
        wait "$UVICORN_PID" 2>/dev/null || true
    fi
    cleanup
    # Remove ports file on exit
    rm -f "$PORTS_FILE" 2>/dev/null || true
}
trap on_exit EXIT INT TERM

# --- Clean stale project ports ---
echo ""
echo "Cleaning stale backend ports..."
cleanup

# --- Find free port ---
FREE_PORT="$(find_free_port "$DEFAULT_PORT")"
if [ -z "$FREE_PORT" ]; then
    echo "ERROR: Could not find free port in range $DEFAULT_PORT-$((DEFAULT_PORT+19))"
    exit 1
fi

# --- Write .dev/ports.json ---
mkdir -p "$DEV_DIR"
cat > "$PORTS_FILE" <<EOF
{
  "backend": {
    "host": "$HOST",
    "port": $FREE_PORT,
    "url": "http://$HOST:$FREE_PORT"
  },
  "updated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

echo ""
echo "Configuration:"
echo "  Port: $FREE_PORT (default was $DEFAULT_PORT)"
echo "  Host: $HOST"
echo "  URL:  http://$HOST:$FREE_PORT"
echo "  Ports file: $PORTS_FILE"
echo ""

# --- Start uvicorn ---
cd "$BACKEND_DIR"

echo "Starting backend server..."
echo "Press Ctrl+C to stop"
echo ""

/home/guiyao/miniconda3/bin/python -m uvicorn app.main:app \
    --host "$HOST" \
    --port "$FREE_PORT" \
    --reload \
    --reload-exclude 'data/*' \
    --reload-exclude 'backend/data/*' &
UVICORN_PID=$!
wait "$UVICORN_PID"
