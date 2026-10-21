#!/bin/bash
# Double-click in Finder to start the FUTURES bots (Interactive Brokers paper: MES, MNQ, MGC) and open their city.
# IB Gateway must be running and logged in to your PAPER account first (docs/futures-city.md).
# Keeps the Mac awake while they run. Keep this window open. Close it, or press Control-C, to stop them;
# they close any open trade first.
cd "$(dirname "$0")" || exit 1
if [ ! -d .venv ]; then
  echo "Setup isn't finished: this folder needs .venv (see README section 3)."
  read -r -p "Press Return to close." _; exit 1
fi
if lsof -nP -iTCP:8767 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "The futures bots are already running: http://127.0.0.1:8767"
  open "http://127.0.0.1:8767"; exit 0
fi
source .venv/bin/activate
python -c "import ib_async" 2>/dev/null || pip install -q -r requirements-futures.txt
[ -f .env ] && { set -a; source .env; set +a; }
echo "Starting the futures bots. The city opens in your browser in a few seconds: http://127.0.0.1:8767"
(sleep 8; open "http://127.0.0.1:8767") &
caffeinate -i python -m scalpcity --config config.futures.yaml paper
read -r -p "The bots stopped. Press Return to close this window." _
