"""Four-day calendar renderer showing today plus next 3 days."""

from datetime import datetime, date, timedelta
from renderer.base_renderer import BaseRenderer


class FourDayRenderer(BaseRenderer):
    """Renders a 4-day view with detailed event listings."""

    def __init__(self, config, color_manager):
        """
        Initialize four-day renderer.

        Args:
            config: Configuration dictionary
            color_manager: ColorManager instance
        """
        super().__init__(config, color_manager)
        self.view_config = config['views']['four_day']

    def render(self, events_by_day, weather_info):
        """
        Render 4-day view.

        Args:
            events_by_day: Dictionary mapping date to DayEvents
            weather_info: WeatherInfo object

        Returns:
            PIL.Image: Rendered calendar image
        """
        image, draw = self.create_canvas()

        # Draw header with weather
        header_height = 80
        y = self.draw_header(draw, weather_info, header_height)

        # Calculate column dimensions
        # Layout: 4 columns (4 days)
        footer_height = 20
        available_height = self.height - header_height - footer_height
        col_width = self.width // 4

        # Get today's date
        today = date.today()

        # Draw 4 days starting from today
        for i in range(4):
            current_date = today + timedelta(days=i)
            x = i * col_width
            is_today = (i == 0)

            self._draw_day_column(
                draw,
                x,
                y,
                col_width,
                available_height,
                current_date,
                events_by_day.get(current_date),
                is_today
            )

        self.logger.info("Rendered 4-day view")
        return image

    def _draw_day_column(self, draw, x, y, width, height, date_obj, day_events, is_today):
        """
        Draw a single day column.

        Args:
            draw: ImageDraw object
            x: X coordinate
            y: Y coordinate
            width: Column width
            height: Column height
            date_obj: Date object for this column
            day_events: DayEvents object or None
            is_today: Boolean indicating if this is today
        """
        # Draw column border
        border_width = 1
        self.draw_box(draw, x, y, width, height, outline=self.black, outline_width=border_width)

        # Note: No highlight for today since it's always the first column

        # Draw day name and date
        day_name = date_obj.strftime("%A")
        date_str = date_obj.strftime("%b %d")

        padding = 5
        text_x = x + padding

        # Day name (larger)
        self.draw_text(draw, day_name, text_x, y + padding, self.fonts['large'], self.black)

        # Date (smaller, below day name)
        self.draw_text(draw, date_str, text_x, y + padding + 25, self.fonts['medium'], self.black)

        # Draw events if any
        if day_events and day_events.events:
            self._draw_events_in_column(
                draw,
                text_x,
                y + 60,  # Start below the date
                width - (2 * padding),
                height - 65,
                day_events
            )

    def _draw_events_in_column(self, draw, x, y, width, height, day_events):
        """
        Draw events within a column.

        Args:
            draw: ImageDraw object
            x: X coordinate for event area
            y: Y coordinate for event area
            width: Available width
            height: Available height
            day_events: DayEvents object
        """
        max_events = self.view_config.get('max_events_per_day', 10)
        show_time = self.view_config.get('show_time', True)

        events_to_show = day_events.events[:max_events]
        current_y = y
        line_height = 14  # Height per line of text

        for event in events_to_show:
            # Format event text
            if show_time and not event.all_day:
                time_str = event.start.strftime("%I:%M %p")
                event_text = f"{time_str} {event.title}"
            else:
                event_text = event.title

            # Wrap text to up to 3 lines (more space in 4-day view)
            text_lines = self.wrap_text(event_text, width - 6, self.fonts['small'], draw, max_lines=3)

            # Calculate bar height based on number of lines
            bar_height = len(text_lines) * line_height + 4

            # Check if we have space
            if current_y + bar_height > y + height:
                break

            # Draw colored bar as background for event
            self.draw_box(draw, x, current_y, width, bar_height, fill=event.color)

            # Draw each line of text in white on colored background
            text_y = current_y + 2
            for line in text_lines:
                self.draw_text(
                    draw,
                    line,
                    x + 3,
                    text_y,
                    self.fonts['small'],
                    self.white
                )
                text_y += line_height

            current_y += bar_height + 2  # Add small gap between events

        # Show "+X more" if there are overflow events
        if hasattr(day_events, 'overflow_count') and day_events.overflow_count > 0:
            if current_y + 15 <= y + height:
                more_text = f"+{day_events.overflow_count} more"
                self.draw_text(
                    draw,
                    more_text,
                    x,
                    current_y,
                    self.fonts['small'],
                    self.black
                )
