"""E-paper display driver for Waveshare 7.3" HAT (E)."""

import os
from utils.logger import get_logger

# Try to import Waveshare library (may not be available on dev machine)
try:
    import sys
    # Add waveshare lib path (adjust as needed based on installation)
    lib_path = os.path.join(os.path.dirname(__file__), '../../waveshare_epd')
    if os.path.exists(lib_path):
        sys.path.append(lib_path)

    from waveshare_epd import epd7in3e
    WAVESHARE_AVAILABLE = True
except ImportError:
    WAVESHARE_AVAILABLE = False


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

        # Color mapping for quantization
        self.color_map = {
            (0, 0, 0): self.EPD_BLACK,
            (255, 255, 255): self.EPD_WHITE,
            (255, 0, 0): self.EPD_RED,
            (255, 255, 0): self.EPD_YELLOW,
            (0, 255, 0): self.EPD_GREEN,
            (0, 0, 255): self.EPD_BLUE
        }

        if not self.mock_mode and not WAVESHARE_AVAILABLE:
            self.logger.warning(
                "Waveshare library not available. Falling back to mock mode. "
                "Install waveshare_epd library for hardware support."
            )
            self.mock_mode = True

    def init_display(self):
        """Initialize the e-paper display hardware."""
        if self.mock_mode:
            self.logger.info("Running in mock mode - no hardware initialization")
            return

        try:
            self.logger.info("Initializing Waveshare 7.3\" e-Paper display...")
            self.epd = epd7in3e.EPD()
            self.epd.init()
            self.logger.info("Display initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize display: {e}")
            self.logger.warning("Falling back to mock mode")
            self.mock_mode = True

    def quantize_image(self, image):
        """
        Convert PIL Image to e-paper 6-color palette.

        Args:
            image: PIL Image object

        Returns:
            PIL.Image: Quantized image
        """
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Get image data
        pixels = image.load()
        width, height = image.size

        # Quantize each pixel to nearest e-paper color
        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                nearest_color = self._find_nearest_color((r, g, b))
                pixels[x, y] = nearest_color

        return image

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

        # The 7.3" HAT (E) uses a specific color encoding
        # Each pixel is mapped to a color code
        buf = [0x00] * (self.display_config['width'] * self.display_config['height'])

        pixels = image.load()
        width, height = image.size

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

                buf[y * width + x] = color_code

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

        try:
            if self.epd:
                self.logger.info("Putting display to sleep...")
                self.epd.sleep()
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
