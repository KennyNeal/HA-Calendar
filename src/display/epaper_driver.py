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
            lib_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '../../waveshare_epd'))
            if os.path.exists(lib_path):
                # Append the parent directory so `import waveshare_epd` will find
                # the package directory named `waveshare_epd` within it.
                sys.path.append(os.path.dirname(lib_path))

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
        Convert PIL Image to e-paper 7-color palette.
        Uses the official Waveshare palette order.

        Args:
            image: PIL Image object

        Returns:
            PIL.Image: Quantized palette image
        """
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Create palette image matching official Waveshare driver
        # Palette order: Black, White, Yellow, Red, Black(duplicate), Blue, Green
        pal_image = Image.new("P", (1, 1))
        pal_image.putpalette(
            (0, 0, 0,           # 0: Black
             255, 255, 255,     # 1: White
             255, 255, 0,       # 2: Yellow
             255, 0, 0,         # 3: Red
             0, 0, 0,           # 4: Black (duplicate)
             0, 0, 255,         # 5: Blue
             0, 255, 0)         # 6: Green
            + (0, 0, 0) * 249   # Fill remaining palette slots
        )

        # Quantize to the 7-color palette (no dithering for solid colors)
        quantized = image.convert("RGB").quantize(palette=pal_image, dither=Image.Dither.NONE)

        return quantized

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
            # Convert to RGB for saving as PNG
            output_path = 'calendar_display.png'
            quantized_image.convert('RGB').save(output_path)
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
                # Save as backup (convert to RGB for debugging)
                quantized_image.convert('RGB').save('calendar_display_error.png')
                self.logger.info("Saved error backup to calendar_display_error.png")

    def _image_to_buffer(self, image):
        """
        Convert PIL palette Image to Waveshare buffer format.
        Matches the official Waveshare implementation.

        Args:
            image: PIL palette Image (already quantized)

        Returns:
            bytearray: Buffer for Waveshare display
        """
        # The 7.3" HAT (E) uses 4 bits per pixel (2 pixels per byte)
        # Get the palette indices directly
        buf_indices = bytearray(image.tobytes('raw'))

        # Pack 2 pixels (4-bit color indices) into each byte
        width, height = image.size
        buf = [0x00] * (width * height // 2)

        idx = 0
        for i in range(0, len(buf_indices), 2):
            # Pack high nibble (first pixel) and low nibble (second pixel)
            buf[idx] = (buf_indices[i] << 4) + buf_indices[i + 1]
            idx += 1

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
