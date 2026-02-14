#!/bin/bash
# Setup script for HA Calendar webhook server

set -e

echo "Setting up HA Calendar webhook server..."

# Get the actual user (not root if running with sudo)
ACTUAL_USER=${SUDO_USER:-$USER}

# Generate systemd service file with deployment-specific paths
DEPLOYMENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="$DEPLOYMENT_DIR/src/main.py"
SERVICE_FILE="$DEPLOYMENT_DIR/ha-calendar-webhook.service"

echo "Generating service file for deployment at: $DEPLOYMENT_DIR"
echo "Service will run as user: $ACTUAL_USER"
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=HA Calendar Webhook Server
After=network.target

[Service]
Type=simple
User=$ACTUAL_USER
WorkingDirectory=$DEPLOYMENT_DIR
Environment="CALENDAR_SCRIPT_PATH=$SCRIPT_PATH"
ExecStart=$DEPLOYMENT_DIR/venv/bin/python3 $DEPLOYMENT_DIR/src/webhook_server.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Copy systemd service file
echo "Installing systemd service..."
sudo cp "$SERVICE_FILE" /etc/systemd/system/
sudo systemctl daemon-reload

# Enable and start the service
echo "Enabling webhook service..."
sudo systemctl enable ha-calendar-webhook.service
sudo systemctl start ha-calendar-webhook.service

# Check status
echo ""
echo "Webhook server status:"
sudo systemctl status ha-calendar-webhook.service --no-pager

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. The webhook server is now running on port 8765"
echo "2. Add the automation to your Home Assistant configuration (see docs/ha-automation.yaml)"
echo "3. Update the IP address in the automation to match your Pi's IP"
echo "4. Restart Home Assistant to load the new automation"
echo ""
echo "Test the webhook with:"
echo "  curl -X POST http://192.168.50.95:8765/refresh"
echo ""
echo "View logs with:"
echo "  sudo journalctl -u ha-calendar-webhook -f"
