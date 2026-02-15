#!/bin/bash
# Setup script to install the cron job for HA-Calendar

set -e

DEPLOYMENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH="$DEPLOYMENT_DIR/venv/bin/python3"
LOG_FILE="$DEPLOYMENT_DIR/logs/cron.log"

# Check if virtual environment exists
if [ ! -f "$PYTHON_PATH" ]; then
    echo "ERROR: Virtual environment not found at $PYTHON_PATH"
    echo "Please run ./install.sh first"
    exit 1
fi

# Check if logs directory exists
if [ ! -d "$DEPLOYMENT_DIR/logs" ]; then
    mkdir -p "$DEPLOYMENT_DIR/logs"
fi

# Create the cron job command with absolute paths
CRON_COMMAND="0 * * * * cd $DEPLOYMENT_DIR && $PYTHON_PATH src/main.py >> $LOG_FILE 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$DEPLOYMENT_DIR/src/main.py"; then
    echo "Cron job already exists. Updating..."
    # Remove the old cron job
    crontab -l | grep -v "$DEPLOYMENT_DIR/src/main.py" | crontab -
fi

# Add the new cron job
(crontab -l 2>/dev/null || echo "") | {
    cat
    echo "$CRON_COMMAND"
} | crontab -

echo "✓ Cron job installed successfully!"
echo ""
echo "Cron job configured:"
echo "  $CRON_COMMAND"
echo ""
echo "Cron logs will be written to: $LOG_FILE"
echo ""
echo "To verify the cron job was installed:"
echo "  crontab -l"
echo ""
echo "To remove the cron job:"
echo "  crontab -e"
echo "  (find and delete the line with $DEPLOYMENT_DIR/src/main.py)"
echo ""
