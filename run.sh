#!/usr/bin/env bash
# Runs one check. Called by cron every hour on the server.
set -euo pipefail
cd "$(dirname "$0")"
set -a; . ./.env; set +a
mkdir -p "$STATE_DIR"
echo "== $(date '+%F %T')" >> "$STATE_DIR/cron.log"
python3 check_shows.py >> "$STATE_DIR/cron.log" 2>&1
