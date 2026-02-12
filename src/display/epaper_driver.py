"""E-paper display driver for Waveshare 7.3" HAT (E)."""

import os
from PIL import Image
from utils.logger import get_logger


class EPaperDisplay:
    """Driver for Waveshare 7.3" e-Paper HAT (E) with 6-color support."""

    # E-paper color constants (Waveshare-specific)
    EPD_BLACK = 0x000000
    EPD_WHITE = 0xFFFFFF
    EPD_RED = 0xFF0000
    EPD_YELLOW = 0xFFFF00
    EPD_GREEN = 0x00FF00
    EPD_BLUE = 0x0000FF

    def __init__(self, config):
        """
        Initialize e-paper display.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = get_logger()
        self.display_config = config['display']
        self.mock_mode = self.display_config.get('mock_mode', False)
        self.epd = None
        self.is_sleeping = False  # Track sleep state

        # Color mapping for quantization
        self.color_map = {
            (0, 0, 0): self.EPD_BLACK,
            (255, 255, 255): self.EPD_WHITE,
            (255, 0, 0): self.EPD_RED,
            (255, 255, 0): self.EPD_YELLOW,
            (0, 255, 0): self.EPD_GREEN,
            (0, 0, 255): self.EPD_BLUE
        }

    def init_display(self):
        """Initialize the e-paper display hardware."""
        if self.mock_mode:
            self.logger.info("Running in mock mode - no hardware initialization")
            return

        # Import Waveshare library only when needed (not in mock mode)
        try:
            import sys
            # Add waveshare lib path (adjust as needed based on installation)
            lib_path = os.path.join(os.path.dirname(__file__), '../../waveshare_epd')
            if os.path.exists(lib_path):
                sys.path.append(lib_path)

            from waveshare_epd import epd7in3e

            self.logger.info("Initializing Waveshare 7.3\" e-Paper display...")
            self.epd = epd7in3e.EPD()
            self.epd.init()
            self.logger.info("Display initialized successfully")
        except ImportError as e:
            self.logger.error(f"Failed to import Waveshare library: {e}")
            self.logger.warning("Falling back to mock mode")
            self.mock_mode = True
        except Exception as e:
            self.logger.error(f"Failed to initialize display: {e}")
            self.logger.warning("Falling back to mock mode")
            self.mock_mode = True

    def quantize_image(self, image):
        """
        Convert PIL Image to e-paper 6-color palette with dithering.

        Args:
            image: PIL Image object

        Returns:
            PIL.Image: Quantized image with dithering
        """
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Create a palette image with our 6 e-paper colors
        # Palette needs to be 768 bytes (256 colors * 3 RGB values)
        palette_img = Image.new('P', (1, 1))

        # Build palette: first 6 colors are ours, rest are black
        palette = []
        epaper_colors = [
            (0, 0, 0),      # Black
            (255, 255, 255), # White
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (255, 0, 0),    # Red
            (255, 255, 0),  # Yellow
        ]

        for color in epaper_colors:
            palette.extend(color)

        # Fill remaining palette slots with black
        for _ in range(256 - len(epaper_colors)):
            palette.extend([0, 0, 0])

        palette_img.putpalette(palette)

        # Apply Floyd-Steinberg dithering while quantizing
        # This creates the illusion of more colors
        quantized = image.quantize(palette=palette_img, dither=Image.Dither.FLOYDSTEINBERG)

        # Convert back to RGB for compatibility with buffer conversion
        return quantized.convert('RGB')

    def _find_nearest_color(self, rgb):
        """
        Find the nearest e-paper color for an RGB value.

        Args:
            rgb: RGB tuple (r, g, b)

        Returns:
            tuple: Nearest e-paper color RGB tuple
        """
        r, g, b = rgb
        min_distance = float('inf')
        nearest = (0, 0, 0)

        for epaper_rgb in self.color_map.keys():
            er, eg, eb = epaper_rgb
            # Euclidean distance in RGB space
            distance = ((r - er) ** 2 + (g - eg) ** 2 + (b - eb) ** 2) ** 0.5

            if distance < min_distance:
                min_distance = distance
                nearest = epaper_rgb

        return nearest

    def display_image(self, image):
        """
        Display an image on the e-paper screen.

        Args:
            image: PIL Image object
        """
        # Ensure image is correct size
        if image.size != (self.display_config['width'], self.display_config['height']):
            self.logger.warning(
                f"Image size {image.size} doesn't match display size "
                f"({self.display_config['width']}, {self.display_config['height']}). Resizing..."
            )
            image = image.resize((self.display_config['width'], self.display_config['height']))

        # Quantize to e-paper colors
        quantized_image = self.quantize_image(image)

        if self.mock_mode:
            # Save to file instead of displaying on hardware
            output_path = 'calendar_display.png'
            quantized_image.save(output_path)
            self.logger.info(f"Mock mode: Saved image to {output_path}")
        else:
            try:
                self.logger.info("Sending image to e-paper display...")

                # Convert PIL image to format expected by Waveshare library
                # The Waveshare library expects a buffer in specific format
                buffer = self._image_to_buffer(quantized_image)

                # Display on e-paper
                self.epd.display(buffer)
                self.logger.info("Image displayed successfully")

            except Exception as e:
                self.logger.error(f"Failed to display image: {e}")
                # Save as backup
                quantized_image.save('calendar_display_error.png')
                self.logger.info("Saved error backup to calendar_display_error.png")

    def _image_to_buffer(self, image):
        """
        Convert PIL Image to Waveshare buffer format.

        Args:
            image: PIL Image (already quantized)

        Returns:
            bytearray: Buffer for Waveshare display
        """
        # This method converts the RGB image to the specific format
        # required by the Waveshare 7.3" HAT (E)

        # The 7.3" HAT (E) uses 4 bits per pixel (2 pixels per byte)
        # Buffer size is width * height / 2
        width, height = image.size
        buf = [0x00] * (width * height // 2)

        pixels = image.load()

        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]

                # Map RGB to Waveshare color code
                # These codes are specific to the 7.3" HAT (E)
                if (r, g, b) == (0, 0, 0):
                    color_code = 0x00  # Black
                elif (r, g, b) == (255, 255, 255):
                    color_code = 0x01  # White
                elif (r, g, b) == (0, 255, 0):
                    color_code = 0x02  # Green
                elif (r, g, b) == (0, 0, 255):
                    color_code = 0x03  # Blue
                elif (r, g, b) == (255, 0, 0):
                    color_code = 0x04  # Red
                elif (r, g, b) == (255, 255, 0):
                    color_code = 0x05  # Yellow
                else:
                    color_code = 0x00  # Default to black

                # Pack 2 pixels per byte (4 bits each)
                pixel_index = y * width + x
                byte_index = pixel_index // 2

                if pixel_index % 2 == 0:
                    # First pixel in byte (high nibble)
                    buf[byte_index] = (color_code << 4) & 0xF0
                else:
                    # Second pixel in byte (low nibble)
                    buf[byte_index] |= color_code & 0x0F

        return bytes(buf)

    def clear(self):
        """Clear the display (set to white)."""
        if self.mock_mode:
            self.logger.info("Mock mode: Display clear requested")
            return

        try:
            if self.epd:
                self.logger.info("Clearing display...")
                self.epd.Clear()
                self.logger.info("Display cleared")
        except Exception as e:
            self.logger.error(f"Failed to clear display: {e}")

    def sleep(self):
        """Put the display into sleep mode to save power."""
        if self.mock_mode:
            self.logger.info("Mock mode: Display sleep requested")
            return

        if self.is_sleeping:
            return  # Already sleeping, don't try again

        try:
            if self.epd:
                self.logger.info("Putting display to sleep...")
                self.epd.sleep()
                self.is_sleeping = True
                self.logger.info("Display is now in sleep mode")
        except Exception as e:
            self.logger.error(f"Failed to sleep display: {e}")

    def __del__(self):
        """Cleanup when object is destroyed."""
        if not self.mock_mode and self.epd:
            try:
                self.sleep()
            except:
                pass
