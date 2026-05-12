#!/bin/bash
# Generates the launchd plist with correct paths for this machine
# and installs it so the newsletter sends automatically on the 1st of every month.
#
# Usage:
#   chmod +x install_scheduler.sh
#   ./install_scheduler.sh

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$REPO_DIR/venv/bin/python"
SCRIPT="$REPO_DIR/pressfriends/send_newsletter.py"
LOG="$REPO_DIR/pressfriends/logs/launchd.log"
PLIST_DEST="$HOME/Library/LaunchAgents/com.pressfriends.newsletter.plist"

if [ ! -f "$PYTHON" ]; then
  echo "ERROR: venv not found at $PYTHON"
  echo "Run: python3 -m venv venv && pip install -r requirements.txt"
  exit 1
fi

mkdir -p "$REPO_DIR/pressfriends/logs"

cat > "$PLIST_DEST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.pressfriends.newsletter</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PYTHON</string>
    <string>$SCRIPT</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Day</key>
    <integer>1</integer>
    <key>Hour</key>
    <integer>9</integer>
    <key>Minute</key>
    <integer>0</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>$LOG</string>
  <key>StandardErrorPath</key>
  <string>$LOG</string>
  <key>RunAtLoad</key>
  <false/>
</dict>
</plist>
EOF

launchctl unload "$PLIST_DEST" 2>/dev/null || true
launchctl load "$PLIST_DEST"

echo "Scheduler installed. Newsletter will send on the 1st of every month at 9:00am."
echo "To uninstall: launchctl unload $PLIST_DEST && rm $PLIST_DEST"
