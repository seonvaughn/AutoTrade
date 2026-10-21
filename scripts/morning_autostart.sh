#!/bin/bash
# Start the options bots automatically at 6:50am ET, Monday to Friday, so the 07:00 morning study runs.
#   bash scripts/morning_autostart.sh install     turn it on
#   bash scripts/morning_autostart.sh remove      turn it off
# The Mac must be awake (lid open, not asleep) at 6:50 for it to start. If it's asleep, it starts when
# you wake it. Paper trading only: this runs "Start Options City.command", which uses your Alpaca paper keys.
set -e
LABEL=com.scalpcity.options-morning
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
case "$1" in
  install)
    # 6:50am Eastern in this Mac's own time zone (launchd uses local time)
    PY="$REPO/.venv/bin/python"; [ -x "$PY" ] || PY=python3
    read -r HOUR MINUTE < <("$PY" -c 'from datetime import datetime; from zoneinfo import ZoneInfo
t = datetime.now(ZoneInfo("America/New_York")).replace(hour=6, minute=50).astimezone()
print(t.hour, t.minute)')
    mkdir -p "$HOME/Library/LaunchAgents"
    {
      echo '<?xml version="1.0" encoding="UTF-8"?>'
      echo '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">'
      echo '<plist version="1.0"><dict>'
      echo "  <key>Label</key><string>$LABEL</string>"
      echo '  <key>ProgramArguments</key><array>'
      echo '    <string>/usr/bin/open</string><string>-a</string><string>Terminal</string>'
      echo "    <string>$REPO/Start Options City.command</string>"
      echo '  </array>'
      echo '  <key>StartCalendarInterval</key><array>'
      for day in 1 2 3 4 5; do
        echo "    <dict><key>Weekday</key><integer>$day</integer><key>Hour</key><integer>$HOUR</integer><key>Minute</key><integer>$MINUTE</integer></dict>"
      done
      echo '  </array>'
      echo '</dict></plist>'
    } > "$PLIST"
    launchctl unload "$PLIST" 2>/dev/null || true
    launchctl load "$PLIST"
    printf 'On: the options city will start Monday-Friday at %d:%02d your time (6:50am Eastern).\n' "$HOUR" "$MINUTE"
    echo "Keep the Mac awake and plugged in overnight. To turn it off: bash scripts/morning_autostart.sh remove"
    ;;
  remove)
    launchctl unload "$PLIST" 2>/dev/null || true
    rm -f "$PLIST"
    echo "Off: the options city will no longer start by itself."
    ;;
  *)
    echo "usage: bash scripts/morning_autostart.sh install|remove"; exit 1
    ;;
esac
