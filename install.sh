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
sudo apt-get install -y python3 python3-pip python3-venv python3-pil \
    fonts-dejavu fonts-dejavu-core fonts-dejavu-extra \
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

# Install Waveshare e-Paper library if not already installed
echo "[7/8] Installing Waveshare e-Paper library..."
if [ ! -d "waveshare_epd" ]; then
    echo "Downloading Waveshare e-Paper library..."
    git clone https://github.com/waveshare/e-Paper.git waveshare_epd_repo
    cp -r waveshare_epd_repo/RaspberryPi_JetsonNano/python/lib/waveshare_epd ./
    rm -rf waveshare_epd_repo
    echo "Waveshare library installed"
else
    echo "Waveshare library already installed"
fi

# Create configuration file if it doesn't exist
echo "[8/8] Setting up configuration..."
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

echo ""
echo "================================================"
echo "Installation Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Edit config/config.yaml with your Home Assistant details:"
echo "   nano config/config.yaml"
echo ""
echo "2. Generate a long-lived access token in Home Assistant:"
echo "   Profile -> Long-Lived Access Tokens -> Create Token"
echo ""
echo "3. Test the display (mock mode):"
echo "   python3 src/main.py"
echo "   This will create calendar_display.png"
echo ""
echo "4. To test with actual hardware, edit config/config.yaml:"
echo "   Set mock_mode: false under display settings"
echo ""
echo "5. Set up cron job for hourly updates:"
echo "   crontab -e"
echo "   Add: 0 * * * * cd $(pwd) && $(pwd)/venv/bin/python3 src/main.py >> logs/cron.log 2>&1"
echo ""
echo "6. To set up required Home Assistant entities:"
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
