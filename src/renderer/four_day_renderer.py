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
        header_height = 50
        y = self.draw_header(draw, weather_info, header_height)

        # Calculate column dimensions
        # Layout: 4 columns (4 days)
        footer_height = 0  # No footer needed
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
        Draw events within a column with time-based vertical positioning.
        Event heights are proportional to their duration.

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
        line_height = 14  # Height per line of text

        # Time range for positioning: 6 AM (hour 6) to 10 PM (hour 22) = 16 hours
        start_hour = 6
        end_hour = 22
        time_range_hours = end_hour - start_hour
        pixels_per_hour = height / time_range_hours

        # Minimum bar height for readability
        min_bar_height = 22

        # Track occupied vertical space to detect overlaps
        occupied_slots = []

        for event in events_to_show:
            # Format event text
            if show_time and not event.all_day:
                time_str = event.start.strftime("%I:%M %p")
                event_text = f"{time_str} {event.title}"
            else:
                event_text = event.title

            # Calculate vertical position based on event time
            if event.all_day:
                # All-day events go at the top with fixed small height
                event_y = y
                bar_height = min_bar_height
            else:
                # Convert start time to hours (with decimal for minutes)
                event_hour = event.start.hour + event.start.minute / 60.0

                # Clamp to our display range
                if event_hour < start_hour:
                    event_hour = start_hour
                elif event_hour > end_hour:
                    event_hour = end_hour

                # Calculate position
                hours_from_start = event_hour - start_hour
                event_y = y + int(hours_from_start * pixels_per_hour)

                # Calculate bar height based on event duration
                duration_hours = (event.end - event.start).total_seconds() / 3600.0
                bar_height = max(int(duration_hours * pixels_per_hour), min_bar_height)

            # Wrap text to fit in the bar
            # More lines allowed for longer events
            max_text_lines = max(2, min(5, bar_height // line_height - 1))
            text_lines = self.wrap_text(event_text, width - 6, self.fonts['small'], draw, max_lines=max_text_lines)

            # Check if this overlaps with previous events at the same time
            # If so, nudge it down slightly
            for occupied_start, occupied_end in occupied_slots:
                if event_y < occupied_end and event_y + bar_height > occupied_start:
                    # Overlap detected - nudge down
                    event_y = occupied_end + 2

            # Ensure it doesn't go off the bottom
            if event_y + bar_height > y + height:
                # Try to shrink the bar to fit
                bar_height = max((y + height) - event_y, min_bar_height)
                if event_y + bar_height > y + height:
                    # Still doesn't fit - skip this event
                    continue

            # Record this slot as occupied
            occupied_slots.append((event_y, event_y + bar_height))

            # Draw colored bar as background for event
            self.draw_box(draw, x, event_y, width, bar_height, fill=event.color)

            # Draw text lines centered vertically in the bar
            total_text_height = len(text_lines) * line_height
            text_start_y = event_y + max(2, (bar_height - total_text_height) // 2)

            for line in text_lines:
                # Make sure text doesn't overflow the bar
                if text_start_y + line_height <= event_y + bar_height - 2:
                    self.draw_text(
                        draw,
                        line,
                        x + 3,
                        text_start_y,
                        self.fonts['small'],
                        self.white
                    )
                    text_start_y += line_height
