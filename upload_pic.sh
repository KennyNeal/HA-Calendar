#!/bin/bash
# Simple wrapper script to upload images to HA-Calendar

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if arguments provided
if [ $# -lt 2 ]; then
    echo "Usage: ./upload_pic.sh <server_url> <image_path>"
    echo ""
    echo "Example:"
    echo "  ./upload_pic.sh http://192.168.1.100:8765 photo.jpg"
    echo "  ./upload_pic.sh http://raspberrypi.local:8765 /path/to/image.png"
    exit 1
fi

SERVER_URL="$1"
IMAGE_PATH="$2"

# Check if virtual environment exists
if [ -f "$SCRIPT_DIR/venv/bin/python3" ]; then
    PYTHON="$SCRIPT_DIR/venv/bin/python3"
else
    PYTHON="python3"
fi

# Run the upload script
"$PYTHON" "$SCRIPT_DIR/upload_pic.py" "$SERVER_URL" "$IMAGE_PATH"
