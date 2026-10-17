#!/bin/bash
# Double-click in Finder to start the options bots (Alpaca paper) and open the city.
# Keeps the Mac awake while they run (closing the lid still sleeps it). Keep this window open. Close it, or press Control-C, to stop them;
# they close any open trade first.
cd "$(dirname "$0")" || exit 1
if [ ! -d .venv ] || [ ! -f .env ]; then
  echo "Setup isn't finished: this folder needs .venv and .env (see README section 3)."
  read -r -p "Press Return to close." _; exit 1
fi
source .venv/bin/activate
set -a; source .env; set +a
echo "Starting the options bots. The city opens in your browser in a few seconds: http://127.0.0.1:8765"
(sleep 8; open "http://127.0.0.1:8765") &
caffeinate -i python -m scalpcity  paper
read -r -p "The bots stopped. Press Return to close this window." _
