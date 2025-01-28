#!/bin/bash

set -e

LOG_FILE="/var/log/install_telegram.log"
exec > >(tee -i $LOG_FILE)
exec 2>&1

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
SHARED_VENV="$SCRIPT_DIR/venv"
PROGRESS_FILE="$SCRIPT_DIR/install_telegram.json"

function update_progress() {
    local progress="$1"
    local message="$2"
    echo "{\"progress\": $progress, \"message\": \"$message\", \"installing\": true}" > "$PROGRESS_FILE"
}

if [ ! -d "$SHARED_VENV" ]; then
    update_progress 0 "Shared virtual env not found."
    echo "[Error]: Shared virtual env not found at $SHARED_VENV."
    exit 1
fi

update_progress 20 "Activating virtual env"
source "$SHARED_VENV/bin/activate"

update_progress 40 "Installing Requirement."
pip install --upgrade pip
pip install python-dotenv python-telegram-bot aiohttp matplotlib qrcode "python-telegram-bot[job-queue]" pyyaml flask-session
sudo apt-get install -y fonts-dejavu

update_progress 60 "Setting up Telegram bot service."
cd "$SCRIPT_DIR/telegram"

SERVICE_FILE=/etc/systemd/system/telegram-bot-fa.service
sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=Telegram Bot Service
After=network.target

[Service]
Type=simple
WorkingDirectory=$SCRIPT_DIR/telegram
ExecStart=$SHARED_VENV/bin/python $SCRIPT_DIR/telegram/robot-fa.py
Restart=always
User=$(whoami)

[Install]
WantedBy=multi-user.target
EOF

update_progress 80 "Reloading systemd and enabling service."
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot-fa.service

update_progress 100 "Starting Telegram bot service."
sudo systemctl start telegram-bot-fa.service

update_progress 100 "Telegram bot service installed and started successfully."
