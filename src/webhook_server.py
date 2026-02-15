#!/usr/bin/env python3
"""Simple webhook server to trigger calendar display updates."""

import json
import os
import subprocess
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from utils.logger import get_logger
from utils.state_manager import load_state
import yaml

logger = get_logger()

# Get the calendar script path from environment variable
CALENDAR_SCRIPT_PATH = os.environ.get(
    'CALENDAR_SCRIPT_PATH',
    os.path.join(os.path.dirname(__file__), 'main.py')
)

# Get deployment directory
DEPLOYMENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(DEPLOYMENT_DIR, 'config', 'config.yaml')
DISPLAY_PATH = os.path.join(DEPLOYMENT_DIR, 'calendar_display.png')

# Get venv python path
VENV_PYTHON = os.path.join(DEPLOYMENT_DIR, 'venv', 'bin', 'python3')


def get_config():
    """Load the current configuration."""
    try:
        if not os.path.exists(CONFIG_PATH):
            logger.warning(f"Config file not found at: {CONFIG_PATH}")
            return None
        with open(CONFIG_PATH, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to read config: {e}")
        return None

class WebhookHandler(BaseHTTPRequestHandler):
    """Handle webhook requests to trigger calendar updates."""

    def do_POST(self):
        """Handle POST requests to trigger a calendar update."""
        if self.path == '/refresh':
            logger.info("Webhook received: Triggering calendar refresh")

            try:
                # Use venv Python if available, otherwise system Python
                python_cmd = VENV_PYTHON if os.path.exists(VENV_PYTHON) else sys.executable
                
                # Run the calendar update script (no sudo needed)
                result = subprocess.run(
                    [python_cmd, CALENDAR_SCRIPT_PATH],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    cwd=DEPLOYMENT_DIR
                )

                if result.returncode == 0:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'Calendar refresh triggered successfully')
                    logger.info("Calendar refresh completed successfully")
                    if result.stdout:
                        logger.debug(f"Output: {result.stdout}")
                else:
                    self.send_response(500)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    error_msg = result.stderr or result.stdout or 'Unknown error'
                    self.wfile.write(f'Error: {error_msg}'.encode())
                    logger.error(f"Calendar refresh failed (code {result.returncode}): {error_msg}")

            except subprocess.TimeoutExpired:
                self.send_response(500)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Error: Calendar update timed out')
                logger.error("Calendar refresh timed out")
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(f'Error: {str(e)}'.encode())
                logger.error(f"Calendar refresh error: {e}", exc_info=True)
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        """Handle GET requests for health checks."""
        if self.path == '/health':
            # Load state from file
            state = load_state()
            
            if state:
                health_data = {
                    'status': 'ok',
                    'last_updated': state.get('last_updated'),
                    'current_view': state.get('current_view'),
                    'state_updated': state.get('state_updated')
                }
            else:
                # No state file yet (first run)
                health_data = {
                    'status': 'no_state',
                    'message': 'Display has not been updated yet',
                    'last_updated': None,
                    'current_view': None
                }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(health_data).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Override to use our logger instead of printing."""
        logger.info("%s - - [%s] %s" % (self.address_string(), self.log_date_time_string(), format % args))


def run_server(port=8765):
    """Run the webhook server."""
    server_address = ('', port)
    httpd = HTTPServer(server_address, WebhookHandler)
    logger.info(f"Starting webhook server on port {port}")
    print(f"Webhook server running on port {port}")
    print(f"Endpoint: http://<raspberry-pi-ip>:{port}/refresh")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down webhook server")
        httpd.shutdown()


if __name__ == '__main__':
    run_server()
