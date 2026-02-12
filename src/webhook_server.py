#!/usr/bin/env python3
"""Simple webhook server to trigger calendar display updates."""

import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from utils.logger import get_logger

logger = get_logger()

class WebhookHandler(BaseHTTPRequestHandler):
    """Handle webhook requests to trigger calendar updates."""

    def do_POST(self):
        """Handle POST requests to trigger a calendar update."""
        if self.path == '/refresh':
            logger.info("Webhook received: Triggering calendar refresh")

            try:
                # Run the calendar update script
                result = subprocess.run(
                    ['sudo', sys.executable, '/home/kenny/HA-Calendar/src/main.py'],
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                if result.returncode == 0:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'Calendar refresh triggered successfully')
                    logger.info("Calendar refresh completed successfully")
                else:
                    self.send_response(500)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(f'Error: {result.stderr}'.encode())
                    logger.error(f"Calendar refresh failed: {result.stderr}")

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
                logger.error(f"Calendar refresh error: {e}")
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        """Handle GET requests for health checks."""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
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
