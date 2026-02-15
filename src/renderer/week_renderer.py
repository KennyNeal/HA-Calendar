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

    def render(self, events_by_day, weather_info, footer_sensor_text=None):
        """
        Render single week view.

        Args:
            events_by_day: Dictionary mapping date to DayEvents
            weather_info: WeatherInfo object
            footer_sensor_text: Optional sensor text for footer

        Returns:
            PIL.Image: Rendered calendar image
        """
        image, draw = self.create_canvas()

        # Draw header with weather
        header_height = 50
        y = self.draw_header(draw, weather_info, header_height)

        # Calculate grid dimensions
        # Layout: 1 row (week) x 7 columns (days) with larger cells
        footer_height = 40  # Footer with last updated time
        available_height = self.height - header_height - footer_height
        row_height = available_height
        col_width = self.width // 7

        # Get current week (Monday to Sunday)
        today = date.today()
        week_start = today - timedelta(days=today.weekday())  # Monday of current week

        # Draw week row
        self._draw_week_row(draw, week_start, y, row_height, col_width, events_by_day)

        # Draw footer with last updated time
        self.draw_footer(draw, y + row_height, footer_height, footer_sensor_text)

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
        Draw events within a cell with time-based vertical positioning.
        Event heights are proportional to their duration.

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
        num_events = len(events_to_show)
        
        # Dynamic sizing based on number of events
        # Fewer events = larger, more readable text
        if num_events <= 2:
            line_height = 18
            min_bar_height = 36
            font_key = 'medium'
        elif num_events <= 4:
            line_height = 16
            min_bar_height = 28
            font_key = 'normal'
        else:
            line_height = 14
            min_bar_height = 22
            font_key = 'small'

        # Time range for positioning: 6 AM (hour 6) to 10 PM (hour 22) = 16 hours
        start_hour = 6
        end_hour = 22
        time_range_hours = end_hour - start_hour
        pixels_per_hour = height / time_range_hours

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
            max_text_lines = max(1, min(5, bar_height // line_height - 1))
            text_lines = self.wrap_text(event_text, width - 6, self.fonts[font_key], draw, max_lines=max_text_lines)

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
                        self.fonts[font_key],
                        self.white
                    )
                    text_start_y += line_height
