#!/usr/bin/env python3
"""Display a random picture from the img folder for 15 seconds."""

import os
import sys
import random
import time
from pathlib import Path
from PIL import Image
import yaml

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import setup_logger, get_logger
from display.epaper_driver import EPaperDisplay


def load_config():
    """Load configuration from YAML file."""
    config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
    
    if not config_path.exists():
        print(f"ERROR: Configuration file not found: {config_path}")
        sys.exit(1)
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"ERROR: Failed to load configuration: {e}")
        sys.exit(1)


def get_random_image():
    """Get a random image from the img folder."""
    img_dir = Path(__file__).parent.parent / 'img'
    
    if not img_dir.exists():
        return None
    
    # Get all image files
    image_files = list(img_dir.glob('*.jpg')) + list(img_dir.glob('*.jpeg')) + \
                  list(img_dir.glob('*.png')) + list(img_dir.glob('*.gif'))
    
    if not image_files:
        return None
    
    return random.choice(image_files)


def display_picture():
    """Display a random picture for 15 seconds."""
    # Load configuration
    config = load_config()
    
    # Setup logging
    logger = setup_logger(config)
    logger.info("="* 60)
    logger.info("HA-Calendar Easter Egg: Random Picture Display")
    logger.info("="* 60)
    
    try:
        # Get a random image
        image_path = get_random_image()
        
        if not image_path:
            logger.error("No images found in img/ folder")
            return
        
        logger.info(f"Selected image: {image_path.name}")
        
        # Load and resize image to display dimensions
        display_config = config['display']
        width = display_config['width']
        height = display_config['height']
        
        logger.info(f"Loading image and resizing to {width}x{height}...")
        image = Image.open(image_path)
        
        # Resize maintaining aspect ratio, then crop to fit
        img_ratio = image.width / image.height
        display_ratio = width / height
        
        if img_ratio > display_ratio:
            # Image is wider - fit to height and crop width
            new_height = height
            new_width = int(height * img_ratio)
        else:
            # Image is taller - fit to width and crop height
            new_width = width
            new_height = int(width / img_ratio)
        
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Crop to center
        left = (new_width - width) // 2
        top = (new_height - height) // 2
        image = image.crop((left, top, left + width, top + height))
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Initialize display
        display = EPaperDisplay(config)
        logger.info("Initializing display...")
        display.init_display()
        
        # Display the image
        logger.info("Displaying image...")
        display.display_image(image)
        
        # Wait 15 seconds
        logger.info("Displaying for 15 seconds...")
        time.sleep(15)
        
        # Don't put display to sleep - it will be refreshed by the next calendar update
        logger.info("Picture display complete")
        logger.info("="* 60)
        
    except Exception as e:
        logger.error(f"Error displaying picture: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    display_picture()
