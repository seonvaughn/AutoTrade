#!/bin/bash
# Start the options bots automatically at 6:50am Eastern, Monday to Friday, so the 07:00 morning study runs.
#   bash scripts/morning_autostart.sh install     turn it on (and check it registered)
#   bash scripts/morning_autostart.sh status      is it on? are the bots running? when did it last start them?
#   bash scripts/morning_autostart.sh remove      turn it off
# The Mac must be awake at 6:50 (plugged in, lid open). If it's asleep, macOS runs it when the Mac wakes.
# To wake the Mac by itself at 6:45 on weekdays (asks for your Mac password once):
#   sudo pmset repeat wakeorpoweron MTWRF 06:45:00
# Paper trading only: this runs "Start Options City.command", which uses your Alpaca paper keys.
LABEL=com.scalpcity.options-morning
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$REPO/data/autostart.log"
DOMAIN="gui/$(id -u)"
registered() { launchctl print "$DOMAIN/$LABEL" >/dev/null 2>&1; }
case "$1" in
  install)
    # 6:50am Eastern in this Mac's own time zone (launchd uses local time)
    PY="$REPO/.venv/bin/python"; [ -x "$PY" ] || PY=python3
    read -r HOUR MINUTE < <("$PY" -c 'from datetime import datetime; from zoneinfo import ZoneInfo
t = datetime.now(ZoneInfo("America/New_York")).replace(hour=6, minute=50).astimezone()
print(t.hour, t.minute)')
    mkdir -p "$HOME/Library/LaunchAgents" "$REPO/data"
    {
      echo '<?xml version="1.0" encoding="UTF-8"?>'
      echo '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">'
      echo '<plist version="1.0"><dict>'
      echo "  <key>Label</key><string>$LABEL</string>"
      echo '  <key>ProgramArguments</key><array>'
      echo '    <string>/bin/bash</string><string>-c</string>'
      echo "    <string>echo \"\$(date): starting the options city\" &gt;&gt; '$LOG'; /usr/bin/open -a Terminal '$REPO/Start Options City.command'</string>"
      echo '  </array>'
      echo "  <key>StandardErrorPath</key><string>$LOG</string>"
      echo '  <key>StartCalendarInterval</key><array>'
      for day in 1 2 3 4 5; do
        echo "    <dict><key>Weekday</key><integer>$day</integer><key>Hour</key><integer>$HOUR</integer><key>Minute</key><integer>$MINUTE</integer></dict>"
      done
      echo '  </array>'
      echo '</dict></plist>'
    } > "$PLIST"
    launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || launchctl unload "$PLIST" 2>/dev/null
    launchctl bootstrap "$DOMAIN" "$PLIST" 2>/dev/null || launchctl load "$PLIST" 2>/dev/null
    if registered; then
      printf 'ON: the options city will start Monday-Friday at %d:%02d your time (6:50am Eastern).\n' "$HOUR" "$MINUTE"
      echo "Keep the Mac plugged in with the lid open overnight. Check any time: bash scripts/morning_autostart.sh status"
    else
      echo "PROBLEM: macOS did not register the autostart. Paste this whole message to Claude."
      launchctl bootstrap "$DOMAIN" "$PLIST"
      exit 1
    fi
    ;;
  status)
    if registered; then echo "Autostart: ON"; else echo "Autostart: OFF (run: bash scripts/morning_autostart.sh install)"; fi
    if lsof -nP -iTCP:8765 -sTCP:LISTEN >/dev/null 2>&1; then
      echo "Bots: RUNNING (city at http://127.0.0.1:8765)"
    else
      echo "Bots: NOT RUNNING"
    fi
    if [ -f "$LOG" ]; then echo "Last automatic starts:"; tail -3 "$LOG"; else echo "Last automatic starts: none yet"; fi
    pmset -g sched 2>/dev/null | grep -i wake | head -2 | sed 's/^/Wake schedule: /'
    ;;
  remove)
    launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || launchctl unload "$PLIST" 2>/dev/null
    rm -f "$PLIST"
    echo "Off: the options city will no longer start by itself."
    ;;
  *)
    echo "usage: bash scripts/morning_autostart.sh install|status|remove"; exit 1
    ;;
esac
