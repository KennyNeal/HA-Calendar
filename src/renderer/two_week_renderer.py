"""Two-week grid calendar renderer."""

from datetime import datetime, date, timedelta
from renderer.base_renderer import BaseRenderer


class TwoWeekRenderer(BaseRenderer):
    """Renders a 2-week grid calendar view."""

    def __init__(self, config, color_manager):
        """
        Initialize two-week renderer.

        Args:
            config: Configuration dictionary
            color_manager: ColorManager instance
        """
        super().__init__(config, color_manager)
        self.view_config = config['views']['two_week']

    def render(self, events_by_day, weather_info):
        """
        Render two-week grid view.

        Args:
            events_by_day: Dictionary mapping date to DayEvents
            weather_info: WeatherInfo object

        Returns:
            PIL.Image: Rendered calendar image
        """
        image, draw = self.create_canvas()

        # Draw header with weather
        header_height = 50
        y = self.draw_header(draw, weather_info, header_height)

        # Calculate grid dimensions
        # Layout: 2 rows (weeks) x 7 columns (days)
        footer_height = 0  # No footer needed
        available_height = self.height - header_height - footer_height
        row_height = available_height // 2
        col_width = self.width // 7

        # Get today's date for reference
        today = date.today()

        # Draw week 1 (current week)
        week1_start = today - timedelta(days=today.weekday())  # Monday of current week
        self._draw_week_row(draw, week1_start, y, row_height, col_width, events_by_day)

        # Draw week 2 (next week)
        week2_start = week1_start + timedelta(days=7)
        self._draw_week_row(draw, week2_start, y + row_height, row_height, col_width, events_by_day)

        # Legend removed - calendar colors are self-explanatory

        self.logger.info("Rendered two-week grid view")
        return image

    def _draw_week_row(self, draw, week_start, y, row_height, col_width, events_by_day):
        """
        Draw a single week row.

        Args:
            draw: ImageDraw object
            week_start: Date of Monday for this week
            y: Y coordinate for this row
            row_height: Height of the row
            col_width: Width of each column
            events_by_day: Dictionary mapping date to DayEvents
        """
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        today = date.today()

        for i in range(7):
            current_date = week_start + timedelta(days=i)
            x = i * col_width
            is_today = (current_date == today)

            # Draw cell
            self._draw_day_cell(
                draw,
                x,
                y,
                col_width,
                row_height,
                current_date,
                day_names[i],
                events_by_day.get(current_date),
                is_today
            )

    def _draw_day_cell(self, draw, x, y, width, height, date_obj, day_name, day_events, is_today):
        """
        Draw a single day cell.

        Args:
            draw: ImageDraw object
            x: X coordinate
            y: Y coordinate
            width: Cell width
            height: Cell height
            date_obj: Date object for this cell
            day_name: Day name (e.g., 'Mon')
            day_events: DayEvents object or None
            is_today: Boolean indicating if this is today
        """
        # Draw cell border
        border_width = 1
        self.draw_box(draw, x, y, width, height, outline=self.black, outline_width=border_width)

        # Highlight today with a thick green left border
        if is_today:
            # Draw thick green left border
            for i in range(8):
                draw.line([(x + i, y), (x + i, y + height)], fill=self.green, width=1)

        # Draw day name and date number
        date_str = f"{day_name} {date_obj.day}"
        padding = 5
        text_x = x + padding + (8 if is_today else 0)  # Add padding if today (for green border)
        self.draw_text(draw, date_str, text_x, y + padding, self.fonts['medium'], self.black)

        # Draw events if any
        if day_events and day_events.events:
            self._draw_events_in_cell(
                draw,
                text_x,
                y + 30,  # Start below the date
                width - padding - (8 if is_today else 0) - padding,
                height - 35,
                day_events
            )

    def _draw_events_in_cell(self, draw, x, y, width, height, day_events):
        """
        Draw events within a cell.

        Args:
            draw: ImageDraw object
            x: X coordinate for event area
            y: Y coordinate for event area
            width: Available width
            height: Available height
            day_events: DayEvents object
        """
        max_events = self.view_config.get('max_events_per_day', 3)
        show_time = self.view_config.get('show_time', True)

        events_to_show = day_events.events[:max_events]
        num_events = len(events_to_show)
        
        # Dynamic sizing based on number of events
        # Fewer events = larger, more readable text
        if num_events <= 2:
            line_height = 18
            font_key = 'medium'
            max_lines_per_event = 3
        elif num_events <= 3:
            line_height = 16
            font_key = 'normal'
            max_lines_per_event = 2
        else:
            line_height = 14
            font_key = 'small'
            max_lines_per_event = 2
        
        current_y = y

        for event in events_to_show:
            # Format event text
            if show_time and not event.all_day:
                time_str = event.start.strftime("%I:%M %p")
                event_text = f"{time_str} {event.title}"
            else:
                event_text = event.title

            # Wrap text
            text_lines = self.wrap_text(event_text, width - 6, self.fonts[font_key], draw, max_lines=max_lines_per_event)

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
                    self.fonts[font_key],
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
