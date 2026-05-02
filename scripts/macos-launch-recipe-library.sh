#!/bin/bash

set -euo pipefail

PROJECT_DIR="/Users/fredericfadda/ffadev/cuisine-recipes-library"
LOG_DIR="$PROJECT_DIR/logs"
LAUNCH_LOG="$LOG_DIR/macos-launch.log"

mkdir -p "$LOG_DIR"

{
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Recipe Library launch script"
  cd "$PROJECT_DIR"
  /bin/bash ./start-docker.sh
} >> "$LAUNCH_LOG" 2>&1

# Made with Bob
