#!/usr/bin/env bash
# Run the real open-source Hindsight server locally (embedded PostgreSQL via pg0) backed by Ollama.
# No Docker, no Cloud, no API key.   Usage: scripts/hindsight-local.sh start|stop|status
set -euo pipefail
cd "$(dirname "$0")/.."
VENV="${HINDSIGHT_VENV:-.hindsight-venv}"
LOG="${HINDSIGHT_LOG:-hindsight-local.log}"
PIDF=".hindsight.pid"
OLLAMA="${OLLAMA_URL:-http://127.0.0.1:11434}"

export HINDSIGHT_API_HOST=127.0.0.1 HINDSIGHT_API_PORT=8888
export HINDSIGHT_API_LLM_PROVIDER=ollama
export HINDSIGHT_API_LLM_BASE_URL="$OLLAMA/v1"
export HINDSIGHT_API_LLM_MODEL="${ERRATA_LLM:-qwen3.5:9b}"
export HINDSIGHT_API_LLM_MAX_CONCURRENT=1        # one local generation at a time
export HINDSIGHT_API_LLM_REASONING_EFFORT=none   # qwen3.5 thinks by default; off = far fewer tokens
export HINDSIGHT_API_LLM_TIMEOUT="${HINDSIGHT_API_LLM_TIMEOUT:-300}"
export HINDSIGHT_API_ENABLE_OBSERVATIONS=false   # Errata does not use observations/mental models

case "${1:-start}" in
  start)
    curl -sf -m 3 "$OLLAMA/api/version" >/dev/null || { echo "Ollama is not running (open the Ollama app or run 'ollama serve')"; exit 1; }
    ollama show "$HINDSIGHT_API_LLM_MODEL" >/dev/null 2>&1 ||{ echo "Model missing: ollama pull ${HINDSIGHT_API_LLM_MODEL}"; exit 1; }
    [ -x "$VENV/bin/hindsight-api" ] || { uv venv --python 3.12 "$VENV" && uv pip install --python "$VENV/bin/python" "hindsight-all==1.2.0"; }
    if curl -sf -m 3 http://127.0.0.1:8888/health >/dev/null; then echo "Hindsight already running"; exit 0; fi
    nohup "$VENV/bin/hindsight-api" --host 127.0.0.1 --port 8888 >"$LOG" 2>&1 & echo $! >"$PIDF"
    echo -n "starting Hindsight (first run downloads embedding/reranker models)"
    for _ in $(seq 1 180); do
      curl -sf -m 2 http://127.0.0.1:8888/health >/dev/null && { echo " ready: http://127.0.0.1:8888"; exit 0; }
      kill -0 "$(cat "$PIDF")" 2>/dev/null || { echo " server exited, see $LOG"; rm -f "$PIDF"; exit 1; }
      sleep 2; echo -n .
    done
    echo " not ready after 6 min, see $LOG"; exit 1 ;;
  stop)
    PID=$(cat "$PIDF" 2>/dev/null || true)
    if [ -n "$PID" ] && ps -p "$PID" -o command= | grep -q hindsight-api; then
      kill "$PID"; while kill -0 "$PID" 2>/dev/null; do sleep 1; done; echo stopped
    else echo "no hindsight-api process from this script is running"; fi
    rm -f "$PIDF" ;;
  status)
    curl -s -m 3 http://127.0.0.1:8888/health || echo "Hindsight: down"; echo ;;
  *) echo "usage: $0 start|stop|status"; exit 2 ;;
esac
