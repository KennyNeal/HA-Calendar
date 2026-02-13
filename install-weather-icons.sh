#!/bin/bash

# Weather Icons Font Installation Script
# Installs the Weather Icons font for use in HA-Calendar display

set -e

echo "================================"
echo "Weather Icons Font Installer"
echo "================================"
echo ""

# Check if running on Linux
if [[ ! "$OSTYPE" =~ ^linux ]]; then
    echo "Error: This script is for Linux systems (Raspberry Pi)."
    echo "For Windows, please see: docs/WEATHER_ICONS_SETUP.md"
    exit 1
fi

# Determine font directory
FONT_DIR="/usr/share/fonts/truetype/weather-icons"

echo "Creating font directory: $FONT_DIR"
sudo mkdir -p "$FONT_DIR"

echo "Downloading Weather Icons font..."
sudo wget -q -O "$FONT_DIR/weathericons-regular-webfont.ttf" \
    "https://github.com/erikflowers/weather-icons/raw/master/font/weathericons-regular-webfont.ttf"

if [ $? -ne 0 ]; then
    echo "Error: Failed to download font. Please check your internet connection."
    exit 1
fi

echo "Verifying font file..."
if [ ! -f "$FONT_DIR/weathericons-regular-webfont.ttf" ]; then
    echo "Error: Font file not found after download."
    exit 1
fi

FONT_SIZE=$(stat -f%z "$FONT_DIR/weathericons-regular-webfont.ttf" 2>/dev/null || stat -c%s "$FONT_DIR/weathericons-regular-webfont.ttf" 2>/dev/null)
if [ "$FONT_SIZE" -lt 50000 ]; then
    echo "Warning: Font file seems unusually small ($FONT_SIZE bytes). Download may have failed."
    exit 1
fi

echo "Updating font cache..."
sudo fc-cache -f -v > /dev/null 2>&1

echo "Verifying installation..."
if fc-list | grep -qi "weather"; then
    echo ""
    echo "✓ Weather Icons font installed successfully!"
    echo ""
    echo "Font location: $FONT_DIR/weathericons-regular-webfont.ttf"
    echo "Restart your HA-Calendar service to use the new icons:"
    echo "  systemctl restart ha-calendar-webhook"
    echo ""
else
    echo ""
    echo "⚠ Warning: Font installation complete, but verification failed."
    echo "Try restarting your system or running: sudo fc-cache -f -v"
    echo ""
fi

echo "Setup complete!"
exit 0
