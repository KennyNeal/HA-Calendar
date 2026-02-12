"""Week calendar renderer."""

from datetime import datetime, date, timedelta
from renderer.base_renderer import BaseRenderer


class WeekRenderer(BaseRenderer):
    """Renders a single week calendar view with larger cells."""

    def __init__(self, config, color_manager):
        """
        Initialize week renderer.

        Args:
            config: Configuration dictionary
            color_manager: ColorManager instance
        """
        super().__init__(config, color_manager)
        self.view_config = config['views']['week']

    def render(self, events_by_day, weather_info):
        """
        Render single week view.

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

        # Calculate grid dimensions
        # Layout: 1 row (week) x 7 columns (days) with larger cells
        footer_height = 40
        available_height = self.height - header_height - footer_height
        row_height = available_height
        col_width = self.width // 7

        # Get current week (Monday to Sunday)
        today = date.today()
        week_start = today - timedelta(days=today.weekday())  # Monday of current week

        # Draw week row
        self._draw_week_row(draw, week_start, y, row_height, col_width, events_by_day)

        # Legend removed - calendar colors are self-explanatory

        self.logger.info("Rendered week calendar view")
        return image

    def _draw_week_row(self, draw, week_start, y, row_height, col_width, events_by_day):
        """
        Draw the week row.

        Args:
            draw: ImageDraw object
            week_start: Date of Monday for this week
            y: Y coordinate for this row
            row_height: Height of the row
            col_width: Width of each column
            events_by_day: Dictionary mapping date to DayEvents
        """
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
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
        Draw a single day cell for week view.

        Args:
            draw: ImageDraw object
            x: X coordinate
            y: Y coordinate
            width: Cell width
            height: Cell height
            date_obj: Date object for this cell
            day_name: Full day name (e.g., 'Monday')
            day_events: DayEvents object or None
            is_today: Boolean indicating if this is today
        """
        # Draw cell border (thicker if today)
        border_width = 3 if is_today else 1
        self.draw_box(draw, x, y, width, height, outline=self.black, outline_width=border_width)

        # Draw day name and date
        padding = 8
        date_header = f"{day_name[:3]} {date_obj.day}"
        self.draw_text(draw, date_header, x + padding, y + padding, self.fonts['large'], self.black)

        # Draw events if any
        if day_events and day_events.events:
            self._draw_events_in_cell(
                draw,
                x + padding,
                y + 40,  # Start below the date header
                width - (2 * padding),
                height - 45,
                day_events
            )

    def _draw_events_in_cell(self, draw, x, y, width, height, day_events):
        """
        Draw events within a cell (more space than two-week view).

        Args:
            draw: ImageDraw object
            x: X coordinate for event area
            y: Y coordinate for event area
            width: Available width
            height: Available height
            day_events: DayEvents object
        """
        max_events = self.view_config.get('max_events_per_day', 5)
        show_time = self.view_config.get('show_time', True)

        events_to_show = day_events.events[:max_events]
        event_height = 22  # Slightly more height per event
        current_y = y

        for event in events_to_show:
            if current_y + event_height > y + height:
                break  # No more space

            # Draw colored indicator bar
            bar_width = 4
            bar_height = 16
            self.draw_box(draw, x, current_y + 2, bar_width, bar_height, fill=event.color)

            # Format event text with more detail
            text_x = x + bar_width + 6

            if show_time and not event.all_day:
                time_str = event.start.strftime("%H:%M")
                event_text = f"{time_str} - {event.title}"
            else:
                event_text = event.title

            # Draw event text
            self.draw_text(
                draw,
                event_text,
                text_x,
                current_y,
                self.fonts['normal'],
                self.black,
                max_width=width - bar_width - 8
            )

            current_y += event_height

        # Show "+X more" if there are overflow events
        if hasattr(day_events, 'overflow_count') and day_events.overflow_count > 0:
            if current_y + event_height <= y + height:
                more_text = f"+{day_events.overflow_count} more"
                self.draw_text(
                    draw,
                    more_text,
                    x,
                    current_y,
                    self.fonts['small'],
                    self.black
                )
