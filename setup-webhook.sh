#!/bin/bash
# Setup script for HA Calendar webhook server

set -e

echo "Setting up HA Calendar webhook server..."

# Copy systemd service file
echo "Installing systemd service..."
sudo cp ha-calendar-webhook.service /etc/systemd/system/
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
