#!/usr/bin/env python3
"""Simple webhook server to trigger calendar display updates."""

import json
import os
import signal
import subprocess
import shutil
import re
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from utils.logger import get_logger
from utils.state_manager import load_state
import yaml

logger = get_logger()

# main.py runs as a persistent daemon (ha-calendar.service) that refreshes
# itself hourly. Spawning a second main.py process here would compete with
# the daemon for the display/GPIO lock, so an on-demand refresh instead
# signals the daemon to wake up and run a cycle immediately.
CALENDAR_SERVICE_NAME = os.environ.get('CALENDAR_SERVICE_NAME', 'ha-calendar.service')
REFRESH_SIGNAL_TIMEOUT = 60  # seconds to wait for the daemon to finish a signaled refresh


def _get_daemon_pid():
    """Look up the PID of the running ha-calendar.service via systemd."""
    result = subprocess.run(
        ['systemctl', 'show', CALENDAR_SERVICE_NAME, '--property=MainPID', '--value'],
        capture_output=True, text=True, timeout=10
    )
    pid = int(result.stdout.strip())
    return pid if pid > 0 else None


def trigger_refresh_and_wait(timeout=REFRESH_SIGNAL_TIMEOUT):
    """
    Signal the running calendar daemon to refresh immediately and wait for
    it to complete.

    Returns:
        tuple: (success: bool, message: str)
    """
    pid = _get_daemon_pid()
    if not pid:
        return False, 'Calendar daemon (ha-calendar.service) is not running'

    before = load_state() or {}
    before_updated = before.get('state_updated')

    try:
        os.kill(pid, signal.SIGUSR1)
    except ProcessLookupError:
        return False, f'Calendar daemon process {pid} not found'

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        state = load_state() or {}
        if state.get('state_updated') and state.get('state_updated') != before_updated:
            return True, 'Calendar refresh triggered successfully'
        time.sleep(1)

    return False, 'Timed out waiting for calendar daemon to finish refreshing'

# Get deployment directory
DEPLOYMENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(DEPLOYMENT_DIR, 'config', 'config.yaml')
DISPLAY_PATH = os.path.join(DEPLOYMENT_DIR, 'calendar_display.png')
IMG_DIR = os.path.join(DEPLOYMENT_DIR, 'img')


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


def parse_multipart_form(data, boundary):
    """
    Parse multipart/form-data without using the deprecated cgi module.
    
    Args:
        data: Raw bytes of the form data
        boundary: Boundary string from Content-Type header
    
    Returns:
        dict: Parsed form fields and files
    """
    parts = data.split(('--' + boundary).encode())
    files = {}
    
    for part in parts:
        if not part or part == b'--\r\n' or part == b'--':
            continue
            
        # Split headers from content
        if b'\r\n\r\n' in part:
            header_section, content = part.split(b'\r\n\r\n', 1)
        else:
            continue
        
        # Remove trailing \r\n from content
        content = content.rstrip(b'\r\n')
        
        # Parse Content-Disposition header
        header_section_str = header_section.decode('utf-8', errors='ignore')
        
        # Extract filename if present
        filename_match = re.search(r'filename="([^"]+)"', header_section_str)
        name_match = re.search(r'name="([^"]+)"', header_section_str)
        
        if filename_match and name_match:
            field_name = name_match.group(1)
            filename = filename_match.group(1)
            files[field_name] = {
                'filename': filename,
                'content': content
            }
    
    return files


class WebhookHandler(BaseHTTPRequestHandler):
    """Handle webhook requests to trigger calendar updates."""

    def do_POST(self):
        """Handle POST requests to trigger a calendar update."""
        if self.path == '/refresh':
            logger.info("Webhook received: Triggering calendar refresh")

            try:
                success, message = trigger_refresh_and_wait()

                if success:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(message.encode())
                    logger.info("Calendar refresh completed successfully")
                else:
                    self.send_response(500)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(f'Error: {message}'.encode())
                    logger.error(f"Calendar refresh failed: {message}")

            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(f'Error: {str(e)}'.encode())
                logger.error(f"Calendar refresh error: {e}", exc_info=True)
                
        elif self.path == '/pics':
            logger.info("Easter egg triggered: Displaying random picture")

            try:
                # Signal the daemon to show a picture itself (it owns the
                # display/GPIO) rather than spawning a competing process.
                pid = _get_daemon_pid()
                if not pid:
                    raise RuntimeError(f'Calendar daemon ({CALENDAR_SERVICE_NAME}) is not running')

                os.kill(pid, signal.SIGUSR2)

                self.send_response(202)  # 202 Accepted
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Picture display started! Will show for 15 seconds then restore calendar.')
                logger.info("Picture display signal sent to daemon")

            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(f'Error: {str(e)}'.encode())
                logger.error(f"Picture display error: {e}", exc_info=True)
                
        elif self.path == '/upload':
            logger.info("File upload request received")
            
            try:
                # Parse the multipart form data
                content_type = self.headers.get('Content-Type')
                
                if not content_type or not content_type.startswith('multipart/form-data'):
                    self.send_response(400)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'Error: Content-Type must be multipart/form-data')
                    logger.error("Upload failed: wrong content type")
                    return
                
                # Extract boundary from Content-Type
                boundary_match = re.search(r'boundary=([^;]+)', content_type)
                if not boundary_match:
                    self.send_response(400)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'Error: No boundary in Content-Type')
                    logger.error("Upload failed: no boundary")
                    return
                
                boundary = boundary_match.group(1).strip('"')
                
                # Read the request body
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                
                # Parse the form data
                files = parse_multipart_form(body, boundary)
                
                # Get the uploaded file
                if 'file' not in files:
                    self.send_response(400)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'Error: No file field in upload')
                    logger.error("Upload failed: no file field")
                    return
                
                file_data = files['file']
                filename = file_data['filename']
                file_content = file_data['content']
                
                if not filename:
                    self.send_response(400)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'Error: No file selected')
                    logger.error("Upload failed: no file selected")
                    return
                
                # Validate file extension
                filename = os.path.basename(filename)
                allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif']
                file_ext = os.path.splitext(filename)[1].lower()
                
                if file_ext not in allowed_extensions:
                    self.send_response(400)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(f'Error: File type {file_ext} not allowed. Use: {", ".join(allowed_extensions)}'.encode())
                    logger.error(f"Upload failed: invalid file type {file_ext}")
                    return
                
                # Ensure img directory exists
                os.makedirs(IMG_DIR, exist_ok=True)
                
                # Save the file
                filepath = os.path.join(IMG_DIR, filename)
                
                # Check if file already exists
                if os.path.exists(filepath):
                    # Add timestamp to make unique
                    name, ext = os.path.splitext(filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{name}_{timestamp}{ext}"
                    filepath = os.path.join(IMG_DIR, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(file_content)
                
                logger.info(f"File uploaded successfully: {filename}")
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    'status': 'success',
                    'message': f'File uploaded successfully: {filename}',
                    'filename': filename,
                    'path': filepath
                }
                self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(f'Error: {str(e)}'.encode())
                logger.error(f"File upload error: {e}", exc_info=True)
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
