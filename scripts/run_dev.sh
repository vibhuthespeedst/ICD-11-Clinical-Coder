#!/bin/sh
# Runs the coder on the dev notes with keys from .env (never printed), then scores it.
set -e
cd "$(dirname "$0")/.."
if [ -f .env ]; then
  set -a
  eval "$(tr -d '\r' < .env | grep -E '^[A-Z_]+=')"
  set +a
fi
PY="${PY:-.venv/Scripts/python}"
export CODER_CACHE_DIR="${CODER_CACHE_DIR:-work/cache}"
"$PY" -m coder "${1:-data/dev_notes.jsonl}" out/dev.jsonl
python score.py --gold "${1:-data/dev_notes.jsonl}" --pred out/dev.jsonl --mms data/mms-2026-01.json --per-note out/dev.per-note.jsonl
