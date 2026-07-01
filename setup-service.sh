#!/bin/bash
# Install ha-calendar as a systemd service (replaces the cron job).
# The service retries indefinitely on network failure and auto-restarts
# if the process crashes, so a reboot is no longer needed to recover.

set -e

DEPLOYMENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="ha-calendar"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
PYTHON_PATH="$DEPLOYMENT_DIR/venv/bin/python3"
CURRENT_USER="$(whoami)"

if [ ! -f "$PYTHON_PATH" ]; then
    echo "ERROR: Virtual environment not found at $PYTHON_PATH"
    echo "Please run ./install.sh first"
    exit 1
fi

if [ ! -d "$DEPLOYMENT_DIR/logs" ]; then
    mkdir -p "$DEPLOYMENT_DIR/logs"
fi

echo "Installing systemd service..."

sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=HA-Calendar e-ink display updater
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${CURRENT_USER}
WorkingDirectory=${DEPLOYMENT_DIR}
ExecStart=${PYTHON_PATH} ${DEPLOYMENT_DIR}/src/main.py
Restart=always
RestartSec=30
StandardOutput=append:${DEPLOYMENT_DIR}/logs/calendar.log
StandardError=append:${DEPLOYMENT_DIR}/logs/calendar.log

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now "$SERVICE_NAME"

echo ""
echo "✓ Service installed and started!"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status $SERVICE_NAME    # check status"
echo "  sudo systemctl restart $SERVICE_NAME   # force a refresh now"
echo "  sudo journalctl -u $SERVICE_NAME -f    # follow service logs"
echo "  tail -f $DEPLOYMENT_DIR/logs/calendar.log"
echo ""

# Warn about cron conflict
if crontab -l 2>/dev/null | grep -q "$DEPLOYMENT_DIR/src/main.py"; then
    echo "⚠️  WARNING: A cron job for main.py is still installed and will conflict"
    echo "   with the service. Remove it by running:"
    echo ""
    echo "     crontab -e"
    echo ""
    echo "   Then delete the line containing:"
    echo "     $DEPLOYMENT_DIR/src/main.py"
    echo ""
fi
