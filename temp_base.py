"""Base renderer class with shared rendering utilities."""

from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime
from utils.logger import get_logger


class BaseRenderer:
    """Base class for calendar renderers with common utilities."""

    def __init__(self, config, color_manager):
        """
        Initialize base renderer.

        Args:
            config: Configuration dictionary
            color_manager: ColorManager instance
        """
        self.config = config
        self.color_manager = color_manager
        self.logger = get_logger()

        # Display dimensions
        display_config = config['display']
        self.width = display_config['width']
        self.height = display_config['height']

        # Colors
        self.black = self.color_manager.get_rgb('black')
        self.white = self.color_manager.get_rgb('white')

        # Load fonts
        self.fonts = self._load_fonts()

    def _load_fonts(self):
        """
        Load fonts for rendering.

        Returns:
            dict: Dictionary of font objects by name
        """
        # Try to use system fonts, fall back to defaults
        font_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            'C:/Windows/Fonts/arial.ttf',  # Windows fallback
            'C:/Windows/Fonts/arialbd.ttf'
        ]

        fonts = {}

        try:
            # Try DejaVu fonts (Linux)
            if os.path.exists(font_paths[0]):
                fonts['small'] = ImageFont.truetype(font_paths[0], 10)
                fonts['normal'] = ImageFont.truetype(font_paths[0], 12)
                fonts['medium'] = ImageFont.truetype(font_paths[0], 14)
                fonts['large'] = ImageFont.truetype(font_paths[1], 18)
                fonts['xlarge'] = ImageFont.truetype(font_paths[1], 24)
            # Try Arial fonts (Windows)
            elif os.path.exists(font_paths[2]):
                fonts['small'] = ImageFont.truetype(font_paths[2], 10)
                fonts['normal'] = ImageFont.truetype(font_paths[2], 12)
                fonts['medium'] = ImageFont.truetype(font_paths[2], 14)
                fonts['large'] = ImageFont.truetype(font_paths[3], 18)
                fonts['xlarge'] = ImageFont.truetype(font_paths[3], 24)
            else:
                # Use default fonts
                self.logger.warning("System fonts not found, using default fonts")
                fonts['small'] = ImageFont.load_default()
                fonts['normal'] = ImageFont.load_default()
                fonts['medium'] = ImageFont.load_default()
                fonts['large'] = ImageFont.load_default()
                fonts['xlarge'] = ImageFont.load_default()
        except Exception as e:
            self.logger.error(f"Error loading fonts: {e}. Using defaults.")
            fonts['small'] = ImageFont.load_default()
            fonts['normal'] = ImageFont.load_default()
            fonts['medium'] = ImageFont.load_default()
            fonts['large'] = ImageFont.load_default()
            fonts['xlarge'] = ImageFont.load_default()

        return fonts

    def create_canvas(self):
        """
        Create a blank canvas with white background.

        Returns:
            tuple: (Image, ImageDraw) objects
        """
        image = Image.new('RGB', (self.width, self.height), self.white)
        draw = ImageDraw.Draw(image)
        return image, draw

    def draw_text(self, draw, text, x, y, font, color, max_width=None, align='left'):
        """
        Draw text with optional truncation.

        Args:
            draw: ImageDraw object
            text: Text to draw
            x: X coordinate
            y: Y coordinate
            font: Font object
            color: RGB color tuple
            max_width: Maximum width (will truncate if exceeded)
            align: Text alignment ('left', 'center', 'right')

        Returns:
            tuple: (width, height) of drawn text
        """
        if max_width:
            text = self.truncate_text(text, max_width, font, draw)

        # Calculate text bbox for alignment
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Adjust x position based on alignment
        if align == 'center':
            x = x - text_width // 2
        elif align == 'right':
            x = x - text_width

        draw.text((x, y), text, font=font, fill=color)

        return text_width, text_height

    def truncate_text(self, text, max_width, font, draw):
        """
        Truncate text to fit within max_width with ellipsis.

        Args:
            text: Text to truncate
            max_width: Maximum width in pixels
            font: Font object
            draw: ImageDraw object

        Returns:
            str: Truncated text with ellipsis if needed
        """
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]

        if text_width <= max_width:
            return text

        # Truncate with ellipsis
        ellipsis = '...'
        while text and text_width > max_width:
            text = text[:-1]
            bbox = draw.textbbox((0, 0), text + ellipsis, font=font)
            text_width = bbox[2] - bbox[0]

        return text + ellipsis if text else ellipsis

    def draw_box(self, draw, x, y, width, height, fill=None, outline=None, outline_width=1):
        """
        Draw a rectangle box.

        Args:
            draw: ImageDraw object
            x: X coordinate
            y: Y coordinate
            width: Box width
            height: Box height
            fill: Fill color (RGB tuple)
            outline: Outline color (RGB tuple)
            outline_width: Width of outline
        """
        coords = [(x, y), (x + width, y + height)]
        draw.rectangle(coords, fill=fill, outline=outline, width=outline_width)

    def draw_header(self, draw, weather_info, height=80):
        """
        Draw header with date and weather.

        Args:
            draw: ImageDraw object
            weather_info: WeatherInfo object or None
            height: Header height in pixels

        Returns:
            int: Y coordinate where header ends
        """
        # Draw header background (white)
        self.draw_box(draw, 0, 0, self.width, height, fill=self.white)

        # Draw current date
        today = datetime.now()
        date_str = today.strftime("%A, %B %d, %Y")
        self.draw_text(draw, date_str, 20, 15, self.fonts['xlarge'], self.black)

        # Draw weather if available
        if weather_info:
            from weather_data import WeatherDataProcessor
            weather_processor = WeatherDataProcessor()
            weather_text = weather_processor.format_weather_text(weather_info)
            self.draw_text(draw, weather_text, 20, 45, self.fonts['medium'], self.black)

        # Draw separator line
        draw.line([(0, height), (self.width, height)], fill=self.black, width=2)

        return height

    def draw_legend(self, draw, y_start, calendars):
        """
        Draw calendar legend.

        Args:
            draw: ImageDraw object
            y_start: Y coordinate to start legend
            calendars: List of calendar info dicts from color_manager

        Returns:
            int: Y coordinate where legend ends
        """
        legend_height = 30
        x = 20
        spacing = 150

        for i, cal_info in enumerate(calendars):
            # Draw color box
            box_size = 15
            box_x = x + (i * spacing)
            box_y = y_start + 8
            self.draw_box(draw, box_x, box_y, box_size, box_size, fill=cal_info['color'], outline=self.black)

            # Draw calendar name
            text_x = box_x + box_size + 8
            text_y = y_start + 8
            self.draw_text(draw, cal_info['name'], text_x, text_y, self.fonts['normal'], self.black)

        return y_start + legend_height

    def render(self, events_by_day, weather_info):
        """
        Render the calendar view (to be implemented by subclasses).

        Args:
            events_by_day: Dictionary mapping date to DayEvents
            weather_info: WeatherInfo object

        Returns:
            PIL.Image: Rendered image
        """
        raise NotImplementedError("Subclasses must implement render method")
