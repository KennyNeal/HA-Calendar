#!/bin/bash
# Installation script for HA-Calendar on Raspberry Pi

set -e  # Exit on error

echo "================================================"
echo "HA-Calendar Installation Script"
echo "================================================"
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    echo "WARNING: This doesn't appear to be a Raspberry Pi"
    echo "Installation will continue but hardware features may not work"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
echo "[1/8] Updating system packages..."
sudo apt-get update

# Install system dependencies
echo "[2/8] Installing system dependencies..."
sudo apt-get install -y git python3 python3-pip python3-venv python3-pil \
    fonts-dejavu fonts-dejavu-core fonts-dejavu-extra \
    fonts-liberation fonts-roboto-unhinted fonts-ubuntu fonts-noto \
    libopenjp2-7

# Enable SPI (required for e-paper display)
echo "[3/8] Enabling SPI interface..."
if ! grep -q "^dtparam=spi=on" /boot/config.txt; then
    echo "dtparam=spi=on" | sudo tee -a /boot/config.txt
    echo "SPI enabled (requires reboot to take effect)"
    NEEDS_REBOOT=1
else
    echo "SPI already enabled"
fi

# Create virtual environment
echo "[4/8] Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv --system-site-packages venv
    echo "Virtual environment created (with system packages access)"
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "[5/8] Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "[6/8] Installing Python dependencies..."
pip install -r requirements.txt

# Waveshare e-Paper library is included in the repository
echo "[7/9] Checking Waveshare e-Paper library..."
if [ -d "waveshare_epd" ]; then
    echo "Waveshare library found in repository"
else
    echo "ERROR: waveshare_epd folder not found!"
    echo "This should be included in the repository."
    echo "If missing, run: git pull"
    exit 1
fi

# Install Weather Icons font
echo "[8/9] Installing Weather Icons font..."
FONT_DIR="/usr/share/fonts/truetype/weather-icons"
if [ ! -f "$FONT_DIR/weathericons-regular-webfont.ttf" ]; then
    sudo mkdir -p "$FONT_DIR"
    echo "Downloading Weather Icons font..."
    sudo wget -q -O "$FONT_DIR/weathericons-regular-webfont.ttf" \
        "https://github.com/erikflowers/weather-icons/raw/master/font/weathericons-regular-webfont.ttf"
    if [ $? -eq 0 ]; then
        echo "Updating font cache..."
        sudo fc-cache -f -v > /dev/null 2>&1
        echo "Weather Icons font installed successfully"
    else
        echo "Warning: Failed to download Weather Icons font (continuing without it)"
    fi
else
    echo "Weather Icons font already installed"
fi

# Create configuration file if it doesn't exist
echo "[9/9] Setting up configuration..."
if [ ! -f "config/config.yaml" ]; then
    cp config/config.example.yaml config/config.yaml
    echo "Created config/config.yaml from example"
    echo ""
    echo "IMPORTANT: Edit config/config.yaml with your settings:"
    echo "  - Home Assistant URL"
    echo "  - Long-lived access token"
    echo "  - Calendar entity IDs"
else
    echo "config/config.yaml already exists"
fi

# Create logs directory
mkdir -p logs

# Generate systemd service file with deployment-specific paths
echo "[10/10] Generating systemd service file..."
DEPLOYMENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="$DEPLOYMENT_DIR/src/main.py"
SERVICE_FILE="ha-calendar-webhook.service"

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=HA Calendar Webhook Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$DEPLOYMENT_DIR
Environment="CALENDAR_SCRIPT_PATH=$SCRIPT_PATH"
ExecStart=$DEPLOYMENT_DIR/venv/bin/python3 $DEPLOYMENT_DIR/src/webhook_server.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "Service file generated: $SERVICE_FILE"
echo "Run './setup-webhook.sh' to install the webhook server"

echo ""
echo "================================================"
echo "Installation Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Set up Git (if not already done):"
echo "   git config --global user.name \"Your Name\""
echo "   git config --global user.email \"your.email@example.com\""
echo ""
echo "2. Link with GitHub repository (recommended for easy updates):"
echo "   This directory is already a Git repository."
echo "   To switch branches and get updates:"
echo "     git fetch origin"
echo "     git checkout main           # Switch to main branch"
echo "     git checkout Dynamic-size   # Switch to feature branches"
echo "     git pull                    # Get latest updates"
echo ""
echo "3. Edit config/config.yaml with your Home Assistant details:"
echo "   nano config/config.yaml"
echo ""
echo "4. Generate a long-lived access token in Home Assistant:"
echo "   Profile -> Long-Lived Access Tokens -> Create Token"
echo ""
echo "5. Test the display (mock mode):"
echo "   python3 src/main.py"
echo "   This will create calendar_display.png"
echo ""
echo "6. To test with actual hardware, edit config/config.yaml:"
echo "   Set mock_mode: false under display settings"
echo ""
echo "7. Set up webhook server for remote calendar updates:"
echo "   sudo ./setup-webhook.sh"
echo ""
echo "8. Set up cron job for hourly updates:"
echo "   crontab -e"
echo "   Add: 0 * * * * cd $(pwd) && $(pwd)/venv/bin/python3 src/main.py >> logs/cron.log 2>&1"
echo ""
echo "9. To set up required Home Assistant entities:"
echo "   - Create input_select.calendar_view with options:"
echo "     two_week, month, week, agenda"
echo "   - Ensure calendar.family and calendar.prairieville_high_school_football exist"
echo "   - Ensure weather.forecast_home entity exists"
echo ""

if [ ! -z "$NEEDS_REBOOT" ]; then
    echo "================================================"
    echo "REBOOT REQUIRED"
    echo "================================================"
    echo "SPI interface was enabled. Please reboot your Raspberry Pi:"
    echo "  sudo reboot"
    echo ""
fi

echo "For troubleshooting, check: logs/calendar.log"
echo ""
