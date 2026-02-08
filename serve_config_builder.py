#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple HTTP server to serve the web configuration builder
Opens browser automatically to the configuration interface
"""

import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

PORT = 8000
HOST = 'localhost'

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler to serve the config builder"""

    def __init__(self, *args, **kwargs):
        # Set the directory to serve files from
        super().__init__(*args, directory=str(Path(__file__).parent), **kwargs)

    def do_GET(self):
        """Handle GET requests"""
        # Redirect root to the config builder
        if self.path == '/':
            self.path = '/web_config_builder.html'
        return super().do_GET()

    def log_message(self, format, *args):
        """Custom log format"""
        print(f"[SERVER] {args[0]}")


def main():
    """Start the web server"""

    # Check if the HTML file exists
    html_file = Path(__file__).parent / 'web_config_builder.html'
    if not html_file.exists():
        print(f"ERROR: web_config_builder.html not found!")
        print(f"   Expected at: {html_file}")
        return 1

    try:
        # Create server
        with socketserver.TCPServer((HOST, PORT), CustomHTTPRequestHandler) as httpd:
            url = f"http://{HOST}:{PORT}"

            print("=" * 70)
            print("  Slideshow Configuration Builder - Web Server")
            print("=" * 70)
            print(f"\nServer started successfully!")
            print(f"URL: {url}")
            print(f"Opening browser automatically...\n")
            print("Instructions:")
            print("   1. Fill in the required fields (marked with *)")
            print("   2. Customize optional settings as desired")
            print("   3. Click 'Generate Configuration' to validate")
            print("   4. Download the YAML file")
            print("   5. Run: python create_slideshow_enhanced.py --config your_config.yaml")
            print(f"\nPress Ctrl+C to stop the server")
            print("=" * 70 + "\n")

            # Open browser
            try:
                webbrowser.open(url)
            except Exception as e:
                print(f"Could not open browser automatically: {e}")
                print(f"   Please open manually: {url}")

            # Start serving
            print("[SERVER] Waiting for requests...")
            httpd.serve_forever()

    except OSError as e:
        if e.errno == 98 or e.errno == 48:  # Address already in use
            print(f"ERROR: Port {PORT} is already in use")
            print(f"   Try closing other applications or use a different port")
            print(f"   You can also manually open: file://{html_file}")
            return 1
        else:
            raise
    except KeyboardInterrupt:
        print("\n\n[SERVER] Shutting down...")
        print("Thank you for using the Slideshow Configuration Builder!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
