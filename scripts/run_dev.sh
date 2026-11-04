#!/bin/sh
# Runs the coder on dev notes with settings from .env (never printed; variables already set win), then scores it.
set -e
cd "$(dirname "$0")/.."
if [ -f .env ]; then
  for line in $(tr -d '\r' < .env | grep -E '^[A-Z_]+=.'); do
    name="${line%%=*}"
    eval "set_already=\${$name+yes}"
    [ "$set_already" = yes ] || export "$line"
  done
fi
PY="${PY:-.venv/Scripts/python}"
export CODER_CACHE_DIR="${CODER_CACHE_DIR:-work/cache}"
"$PY" -m coder "${1:-data/dev_notes.jsonl}" out/dev.jsonl
python score.py --gold "${1:-data/dev_notes.jsonl}" --pred out/dev.jsonl --mms data/mms-2026-01.json --per-note out/dev.per-note.jsonl
