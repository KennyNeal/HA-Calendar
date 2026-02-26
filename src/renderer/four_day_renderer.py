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

    def render(self, events_by_day, weather_info, footer_sensor_text=None):
        """
        Render 4-day view.

        Args:
            events_by_day: Dictionary mapping date to DayEvents
            weather_info: WeatherInfo object
            footer_sensor_text: Optional sensor text for footer

        Returns:
            PIL.Image: Rendered calendar image
        """
        image, draw = self.create_canvas()

        # No header - grid extends to top
        y = 0

        # Calculate column dimensions
        # Layout: 4 columns (4 days)
        footer_height = 40  # Footer with last updated time
        available_height = self.height - footer_height
        col_width = self.width // 4

        # Get today's date
        today = date.today()

        # Draw 4 days starting from today
        row_dates = [today + timedelta(days=i) for i in range(4)]
        lanes, overflow, span_keys = self._get_all_day_span_lanes(row_dates, events_by_day, max_lanes=3)
        lane_height = 18
        all_day_height = lane_height * len(lanes)

        all_day_top = y + 60
        self._draw_all_day_spans(draw, all_day_top, col_width, lanes, lane_height)

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
                is_today,
                all_day_height,
                span_keys,
                weather_info
            )

        # Draw footer with last updated time and calendar legend
        footer_y = y + available_height
        self.draw_footer(draw, footer_y, footer_height, footer_sensor_text)
        calendar_legend = self._collect_calendar_legend(events_by_day)
        self.draw_calendar_legend(draw, footer_y, footer_height, calendar_legend)

        self.logger.info("Rendered 4-day view")
        return image

    def _draw_day_column(self, draw, x, y, width, height, date_obj, day_events, is_today, all_day_height, span_keys, weather_info=None):
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
            all_day_height: Height of all-day event lanes
            span_keys: Set of span event keys
            weather_info: WeatherInfo object for today's weather (for first column only)
        """
        # Draw column border
        border_width = 1
        self.draw_box(draw, x, y, width, height, outline=self.black, outline_width=border_width)

        # Draw blue header background bar (height 50)
        header_height = 50
        self.draw_box(draw, x + 1, y + 1, width - 2, header_height - 2, fill=self.blue)

        # Draw day name and date in white on blue background
        day_name = date_obj.strftime("%A")
        date_str = date_obj.strftime("%b %d")

        padding = 5
        text_x = x + padding
        text_y = y + 5

        # Day name (larger, white)
        self.draw_text(draw, day_name, text_x, text_y, self.fonts['large'], self.white)

        # Date (smaller, below day name, white)
        self.draw_text(draw, date_str, text_x, text_y + 22, self.fonts['medium'], self.white)

        # Draw weather icon and temperature right-aligned in header
        if weather_info:
            icon, condition = self.get_weather_icon_for_date(weather_info, date_obj)
            
            # Get temperature for this date from forecast dict
            temp_str = None
            if weather_info and weather_info.forecast:
                date_key = date_obj.isoformat()
                forecast = weather_info.forecast.get(date_key)
                if forecast and forecast.temperature:
                    temp_str = f"{int(forecast.temperature)}°"

            if icon or temp_str:
                weather_icon_font = self.fonts.get('weather_medium', self.fonts['medium'])
                temp_font = self.fonts['medium']
                
                # Measure widths separately
                icon_width = 0
                if icon:
                    icon_bbox = draw.textbbox((0, 0), icon, font=weather_icon_font)
                    icon_width = icon_bbox[2] - icon_bbox[0]
                
                temp_width = 0
                if temp_str:
                    temp_bbox = draw.textbbox((0, 0), temp_str, font=temp_font)
                    temp_width = temp_bbox[2] - temp_bbox[0]
                
                # Position from right edge of column (icon + space + temp)
                total_width = icon_width + (8 if icon and temp_str else 0) + temp_width
                weather_x = x + width - 5 - total_width
                weather_y = y + 8
                
                # Draw icon first
                if icon:
                    self.draw_text(draw, icon, weather_x, weather_y, weather_icon_font, self.white)
                    weather_x += icon_width + 8
                
                # Draw temperature
                if temp_str:
                    self.draw_text(draw, temp_str, weather_x, weather_y + 2, temp_font, self.white)

        # Draw events if any
        if day_events and day_events.events:
            self._draw_events_in_column(
                draw,
                text_x,
                y + header_height + all_day_height,  # Start below the header and all-day spans
                width - (2 * padding),
                height - header_height - all_day_height - 2,
                day_events,
                span_keys
            )

    def _draw_events_in_column(self, draw, x, y, width, height, day_events, span_keys):
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

        filtered_events = [event for event in day_events.events if self._event_key(event) not in span_keys]
        events_to_show = filtered_events[:max_events]
        num_events = len(events_to_show)
        
        # Dynamic sizing based on number of events
        # Fewer events = larger, more readable text
        if num_events <= 3:
            line_height = 18
            min_bar_height = 36
            font_key = 'medium'
        elif num_events <= 6:
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
                # All-day events go at the top with extra room for wrapping
                event_y = y
                all_day_max_height = min(height // 3, min_bar_height * 3)
                bar_height = all_day_max_height
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
            max_text_lines = max(1, min(6, (bar_height - 4) // line_height))
            text_lines = self.wrap_text(event_text, width - 6, self.fonts[font_key], draw, max_lines=max_text_lines)

            if event.all_day:
                bar_height = max(min_bar_height, len(text_lines) * line_height + 4)
                if bar_height > all_day_max_height:
                    bar_height = all_day_max_height

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
