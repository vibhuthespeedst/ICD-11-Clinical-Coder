#!/bin/sh
# Runs a command with settings from .env (never printed); variables already set win.
cd "$(dirname "$0")/.."
if [ -f .env ]; then
  for line in $(tr -d '\r' < .env | grep -E '^[A-Z_]+=.'); do
    name="${line%%=*}"
    eval "set_already=\${$name+yes}"
    [ "$set_already" = yes ] || export "$line"
  done
fi
exec "$@"
