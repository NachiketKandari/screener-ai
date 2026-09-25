#!/bin/bash
set -e

PROJECT_DIR="/home/nachiket/projects/screener-ai"
cd "$PROJECT_DIR"

# Load environment (API keys, model, DB path)
set -a
. ./.env
set +a

# Kill any existing process on port 8001
existing_pids=$(pgrep -f "uvicorn backend.main:app" 2>/dev/null || true)
if [ -n "$existing_pids" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') | Killing existing strattest PIDs: $(echo $existing_pids | tr '\n' ' ')"
    kill $existing_pids 2>/dev/null || true
    sleep 2
    kill -9 $existing_pids 2>/dev/null || true
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') | Starting strattest..."
nohup /home/nachiket/.local/bin/uvicorn backend.main:app \
    --host 127.0.0.1 --port 8001 \
    --proxy-headers --forwarded-allow-ips='*' \
    >> uvicorn.log 2>&1 &

echo "$(date '+%Y-%m-%d %H:%M:%S') | Started strattest PID $!"
