"""Base renderer class with shared rendering utilities."""

from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime, timedelta
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
        self.red = self.color_manager.get_rgb('red')
        self.yellow = self.color_manager.get_rgb('yellow')
        self.green = self.color_manager.get_rgb('green')
        self.blue = self.color_manager.get_rgb('blue')

        # Load fonts
        self.fonts = self._load_fonts()

    def _load_fonts(self):
        """
        Load fonts for rendering.
        
        Prioritizes fonts that render cleanly on e-paper displays:
        - Liberation Sans (excellent hinting, very clean)
        - Roboto (Google's font, designed for screens)
        - Ubuntu (clean and modern)
        - Noto Sans (very readable)
        - DejaVu Sans (fallback)

        Returns:
            dict: Dictionary of font objects by name
        """
        # Font paths in order of preference (best for e-paper first)
        font_paths = {
            'regular': [
                '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',  # Best for e-paper
                '/usr/share/fonts/truetype/roboto/Roboto-Regular.ttf',
                '/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf',
                '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                'C:/Windows/Fonts/arial.ttf',  # Windows fallback
            ],
            'bold': [
                '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
                '/usr/share/fonts/truetype/roboto/Roboto-Bold.ttf',
                '/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf',
                '/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                'C:/Windows/Fonts/arialbd.ttf',
            ],
            'weather': [
                'C:/Users/kneal/AppData/Local/Microsoft/Windows/Fonts/weathericons-regular-webfont.ttf',
                '/usr/share/fonts/truetype/weather-icons/weathericons-regular-webfont.ttf',
                'C:/Windows/Fonts/weathericons-regular-webfont.ttf'
            ]
        }

        fonts = {}

        # Find best available regular font
        regular_font = None
        for path in font_paths['regular']:
            if os.path.exists(path):
                regular_font = path
                self.logger.info(f"Using font: {os.path.basename(path)}")
                break

        # Find best available bold font
        bold_font = None
        for path in font_paths['bold']:
            if os.path.exists(path):
                bold_font = path
                break

        try:
            if regular_font and bold_font:
                # Load regular weight fonts with optimized sizes for e-paper
                fonts['small'] = ImageFont.truetype(regular_font, 13)   # Slightly larger
                fonts['normal'] = ImageFont.truetype(regular_font, 15)  # Slightly larger
                fonts['medium'] = ImageFont.truetype(regular_font, 17)  # Slightly larger
                fonts['large'] = ImageFont.truetype(bold_font, 21)      # Slightly larger
                fonts['xlarge'] = ImageFont.truetype(bold_font, 27)     # Slightly larger
                
                # Try to load weather icons font
                weather_font_loaded = False
                self.logger.info(f"Looking for weather icons font in:")
                for path in font_paths['weather']:
                    self.logger.info(f"  Checking: {path} (exists: {os.path.exists(path)})")
                    if os.path.exists(path):
                        fonts['weather_tiny'] = ImageFont.truetype(path, 14)
                        fonts['weather_small'] = ImageFont.truetype(path, 22)
                        fonts['weather_medium'] = ImageFont.truetype(path, 30)
                        fonts['weather_large'] = ImageFont.truetype(path, 38)
                        weather_font_loaded = True
                        self.logger.info(f"  [+] Found weather icons font at: {path}")
                        break
                
                if not weather_font_loaded:
                    self.logger.warning("Weather Icons font not found, weather icons may not render correctly")
                    # Check if font might be in a different location
                    self.logger.info("If you have the weather icons font installed, provide the full path:")
                    self.logger.info("  Option 1: Add path to font_paths['weather'] in base_renderer.py")
                    self.logger.info("  Option 2: Copy font to: C:/Windows/Fonts/weathericons-regular-webfont.ttf")
                    fonts['weather_tiny'] = fonts['small']
                    fonts['weather_small'] = fonts['normal']
                    fonts['weather_medium'] = fonts['medium']
                    fonts['weather_large'] = fonts['large']
            else:
                # Use default fonts
                self.logger.warning("Preferred fonts not found, using default fonts (may look pixelated)")
                fonts['small'] = ImageFont.load_default()
                fonts['normal'] = ImageFont.load_default()
                fonts['medium'] = ImageFont.load_default()
                fonts['large'] = ImageFont.load_default()
                fonts['xlarge'] = ImageFont.load_default()
                fonts['weather_small'] = ImageFont.load_default()
                fonts['weather_medium'] = ImageFont.load_default()
                fonts['weather_large'] = ImageFont.load_default()
        except Exception as e:
            self.logger.error(f"Error loading fonts: {e}. Using defaults.")
            fonts['small'] = ImageFont.load_default()
            fonts['normal'] = ImageFont.load_default()
            fonts['medium'] = ImageFont.load_default()
            fonts['large'] = ImageFont.load_default()
            fonts['xlarge'] = ImageFont.load_default()
            fonts['weather_small'] = ImageFont.load_default()
            fonts['weather_medium'] = ImageFont.load_default()
            fonts['weather_large'] = ImageFont.load_default()

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

    def get_weather_icon_for_date(self, weather_info, date_obj):
        """
        Get weather icon for a specific date if forecast is available.

        Args:
            weather_info: WeatherInfo object or None
            date_obj: date object

        Returns:
            tuple: (icon_str, condition_str) or (None, None) if no forecast available
        """
        if not weather_info or not weather_info.forecast:
            return None, None
        
        date_key = date_obj.isoformat()  # YYYY-MM-DD format
        forecast = weather_info.forecast.get(date_key)
        
        if not forecast:
            return None, None
        
        from weather_data import WeatherDataProcessor
        weather_processor = WeatherDataProcessor()
        icon = weather_processor.get_weather_icon(forecast.condition.lower())
        
        return icon, forecast.condition

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

    def wrap_text(self, text, max_width, font, draw, max_lines=2):
        """
        Wrap text to fit within max_width, up to max_lines.

        Args:
            text: Text to wrap
            max_width: Maximum width in pixels per line
            font: Font object
            draw: ImageDraw object
            max_lines: Maximum number of lines (default 2)

        Returns:
            list: List of text lines
        """
        words = text.split(' ')
        lines = []
        current_line = ''
        words_used = 0

        for i, word in enumerate(words):
            test_line = current_line + (' ' if current_line else '') + word
            bbox = draw.textbbox((0, 0), test_line, font=font)
            test_width = bbox[2] - bbox[0]

            if test_width <= max_width:
                current_line = test_line
                words_used = i + 1
            else:
                if current_line:
                    lines.append(current_line)
                    if len(lines) >= max_lines:
                        break
                    current_line = word
                    words_used = i + 1
                else:
                    # Single word is too long, truncate it
                    current_line = self.truncate_text(word, max_width, font, draw)
                    lines.append(current_line)
                    words_used = i + 1
                    if len(lines) >= max_lines:
                        break
                    current_line = ''

        # Add remaining text if we haven't hit max lines
        if current_line and len(lines) < max_lines:
            lines.append(current_line)
            words_used = len(words)

        # If we have more words and hit max lines, add ellipsis to last line
        if lines and words_used < len(words):
            # There are remaining words - add ellipsis
            last_line = lines[-1]
            ellipsis = '...'
            # Make room for ellipsis
            bbox = draw.textbbox((0, 0), ellipsis, font=font)
            ellipsis_width = bbox[2] - bbox[0]
            lines[-1] = self.truncate_text(last_line, max_width - ellipsis_width, font, draw) + ellipsis

        return lines

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

    def draw_header(self, draw, weather_info, height=50):
        """
        Draw compact header with date and weather on same line.

        Args:
            draw: ImageDraw object
            weather_info: WeatherInfo object or None
            height: Header height in pixels (default 50)

        Returns:
            int: Y coordinate where header ends
        """
        # Draw header background with blue color
        self.draw_box(draw, 0, 0, self.width, height, fill=self.blue)

        # Calculate vertical centering
        text_y = (height - 26) // 2  # Center the xlarge font (26px) vertically

        # Draw current date in white (left side)
        today = datetime.now()
        date_str = today.strftime("%A, %B %d, %Y")
        self.draw_text(draw, date_str, 20, text_y, self.fonts['xlarge'], self.white)

        # Draw weather on right side if available (same vertical position)
        if weather_info:
            from weather_data import WeatherDataProcessor
            weather_processor = WeatherDataProcessor()
            
            # Get icon and temperature separately
            icon = weather_processor.get_weather_icon(weather_info.condition.lower())
            temp_str = f"{weather_info.temperature:.0f}{weather_info.temperature_unit}"
            
            # Use weather icon font for icon, regular font for temperature
            weather_icon_font = self.fonts.get('weather_medium', self.fonts['medium'])
            temp_font = self.fonts['medium']
            
            # Calculate position from right edge (measure temperature first for positioning)
            temp_bbox = draw.textbbox((0, 0), temp_str, font=temp_font)
            temp_width = temp_bbox[2] - temp_bbox[0]
            
            # Measure icon width
            icon_bbox = draw.textbbox((0, 0), icon, font=weather_icon_font)
            icon_width = icon_bbox[2] - icon_bbox[0]
            
            # Position from right edge (icon + space + temp)
            total_width = icon_width + 8 + temp_width  # 8 pixels for space
            weather_x = self.width - 20 - total_width
            
            # Draw icon first
            self.draw_text(draw, icon, weather_x, text_y, weather_icon_font, self.white)
            
            # Draw temperature to the right of icon
            temp_x = weather_x + icon_width + 8  # 8 pixel gap
            self.draw_text(draw, temp_str, temp_x, text_y + 4, temp_font, self.white)

        # Draw separator line
        draw.line([(0, height), (self.width, height)], fill=self.black, width=2)

        return height

    def draw_footer(self, draw, y_start, height=40, footer_sensor_text=None):
        """
        Draw footer with last updated date and time, and optional sensor value.

        Args:
            draw: ImageDraw object
            y_start: Y coordinate where footer starts
            height: Footer height in pixels (default 40)
            footer_sensor_text: Optional text to display on right side (e.g., "Outdoor Scene: LSU")

        Returns:
            int: Y coordinate where footer ends
        """
        footer_y = y_start
        
        # Draw separator line above footer
        draw.line([(0, footer_y), (self.width, footer_y)], fill=self.black, width=2)

        # Draw footer background (light gray or white)
        self.draw_box(draw, 0, footer_y, self.width, height, fill=self.white, outline=self.black, outline_width=1)

        # Calculate vertical centering
        text_y = footer_y + (height - 14) // 2  # Center normal font (14px) vertically

        # Draw "Last Updated:" label and timestamp on the left
        last_updated = datetime.now().strftime("%m/%d %I:%M %p")
        updated_text = f"Last Updated: {last_updated}"
        
        self.draw_text(draw, updated_text, 20, text_y, self.fonts['normal'], self.black)

        # Draw optional sensor text on the right
        if footer_sensor_text:
            bbox = draw.textbbox((0, 0), footer_sensor_text, font=self.fonts['normal'])
            text_width = bbox[2] - bbox[0]
            right_x = self.width - text_width - 20
            self.draw_text(draw, footer_sensor_text, right_x, text_y, self.fonts['normal'], self.black)

        return footer_y + height

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

    def _event_key(self, event):
        return (
            event.calendar_id,
            event.title,
            event.start.isoformat(),
            event.end.isoformat()
        )

    def _get_all_day_span_lanes(self, dates, events_by_day, max_lanes=3):
        row_start = dates[0]
        row_end = dates[-1]
        span_events = {}

        for day in dates:
            day_events = events_by_day.get(day)
            if not day_events:
                continue

            for event in day_events.events:
                if not event.all_day:
                    continue

                end_inclusive = event.end.date() - timedelta(days=1)
                if end_inclusive <= event.start.date():
                    continue

                if end_inclusive < row_start or event.start.date() > row_end:
                    continue

                span_events[self._event_key(event)] = event

        spans = []
        for event in span_events.values():
            start_date = event.start.date()
            end_inclusive = event.end.date() - timedelta(days=1)
            span_start = max(start_date, row_start)
            span_end = min(end_inclusive, row_end)
            start_idx = dates.index(span_start)
            end_idx = dates.index(span_end)
            spans.append((start_idx, end_idx, event))

        spans.sort(key=lambda s: (s[0], (s[1] - s[0]), s[2].title))

        lanes = []
        overflow = 0

        for span in spans:
            placed = False
            for lane in lanes:
                if all(span[1] < existing[0] or span[0] > existing[1] for existing in lane):
                    lane.append(span)
                    placed = True
                    break

            if not placed:
                if len(lanes) < max_lanes:
                    lanes.append([span])
                else:
                    overflow += 1

        return lanes, overflow, set(span_events.keys())

    def _draw_all_day_spans(self, draw, y, col_width, lanes, lane_height):
        if not lanes:
            return

        line_height = 14
        font = self.fonts['small']

        for lane_idx, lane in enumerate(lanes):
            lane_y = y + lane_idx * lane_height
            for start_idx, end_idx, event in lane:
                span_x = start_idx * col_width + 2
                span_width = (end_idx - start_idx + 1) * col_width - 4

                self.draw_box(draw, span_x, lane_y, span_width, lane_height - 2, fill=event.color)

                text_lines = self.wrap_text(
                    event.title,
                    span_width - 6,
                    font,
                    draw,
                    max_lines=2
                )

                total_text_height = len(text_lines) * line_height
                text_y = lane_y + max(2, (lane_height - total_text_height) // 2)
                text_center_x = span_x + (span_width // 2)

                for line in text_lines:
                    self.draw_text(draw, line, text_center_x, text_y, font, self.white, align='center')
                    text_y += line_height
