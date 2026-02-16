#!/usr/bin/env python3
"""Upload an image to the HA-Calendar img folder via webhook."""

import argparse
import requests
import os
import sys


def upload_image(server_url, image_path):
    """
    Upload an image to the calendar server.
    
    Args:
        server_url: Base URL of the webhook server (e.g., http://192.168.1.100:8765)
        image_path: Local path to the image file
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Validate file exists
    if not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}")
        return False
    
    # Validate it's a file
    if not os.path.isfile(image_path):
        print(f"Error: Not a file: {image_path}")
        return False
    
    # Get filename
    filename = os.path.basename(image_path)
    
    print(f"Uploading {filename} to {server_url}...")
    
    try:
        # Open file and upload
        with open(image_path, 'rb') as f:
            files = {'file': (filename, f, 'image/jpeg')}
            
            # Make the POST request
            response = requests.post(
                f"{server_url}/upload",
                files=files,
                timeout=30
            )
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Success! {result['message']}")
            return True
        else:
            print(f"✗ Upload failed: {response.status_code}")
            print(f"  {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Network error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Upload an image to the HA-Calendar display',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python upload_pic.py http://192.168.1.100:8765 photo.jpg
  python upload_pic.py http://raspberrypi.local:8765 /path/to/image.png
        """
    )
    
    parser.add_argument(
        'server',
        help='Webhook server URL (e.g., http://192.168.1.100:8765)'
    )
    
    parser.add_argument(
        'image',
        help='Path to image file to upload'
    )
    
    args = parser.parse_args()
    
    # Upload the image
    success = upload_image(args.server, args.image)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
