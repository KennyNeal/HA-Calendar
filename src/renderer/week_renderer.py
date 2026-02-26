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

        # No header - grid extends to top
        y = 0

        # Calculate grid dimensions
        # Layout: 1 row (week) x 7 columns (days) with larger cells
        footer_height = 40  # Footer with last updated time
        available_height = self.height - footer_height
        row_height = available_height
        col_width = self.width // 7

        # Get current week (Monday to Sunday)
        today = date.today()
        week_start = today - timedelta(days=today.weekday())  # Monday of current week

        # Draw week row
        self._draw_week_row(draw, week_start, y, row_height, col_width, events_by_day, weather_info)

        # Draw footer with last updated time and calendar legend
        footer_y = y + row_height
        self.draw_footer(draw, footer_y, footer_height, footer_sensor_text)
        calendar_legend = self._collect_calendar_legend(events_by_day)
        self.draw_calendar_legend(draw, footer_y, footer_height, calendar_legend)

        self.logger.info("Rendered week calendar view")
        return image

    def _draw_week_row(self, draw, week_start, y, row_height, col_width, events_by_day, weather_info=None):
        """
        Draw the week row.

        Args:
            draw: ImageDraw object
            week_start: Date of Monday for this week
            y: Y coordinate for this row
            row_height: Height of the row
            col_width: Width of each column
            events_by_day: Dictionary mapping date to DayEvents
            weather_info: WeatherInfo object (for current week only)
        """
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        today = date.today()

        row_dates = [week_start + timedelta(days=i) for i in range(7)]
        lanes, overflow, span_keys = self._get_all_day_span_lanes(row_dates, events_by_day, max_lanes=3)
        lane_height = 18
        all_day_height = lane_height * len(lanes)

        all_day_top = y + 40
        self._draw_all_day_spans(draw, all_day_top, col_width, lanes, lane_height)

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
                is_today,
                all_day_height,
                span_keys,
                weather_info
            )

    def _draw_day_cell(self, draw, x, y, width, height, date_obj, day_name, day_events, is_today, all_day_height, span_keys, weather_info=None):
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
            all_day_height: Height of all-day event spans
            span_keys: Set of span event keys
            weather_info: WeatherInfo object (today only)
        """
        # Draw cell border
        border_width = 1
        self.draw_box(draw, x, y, width, height, outline=self.black, outline_width=border_width)

        # Draw blue header background bar (height 40)
        header_height = 40
        self.draw_box(draw, x + 1, y + 1, width - 2, header_height - 2, fill=self.blue)

        # Draw day name and date in white on blue background (inline, slightly larger)
        padding = 5
        day_name_short = day_name[:3]
        date_str = f"{date_obj.day}"
        header_text = f"{day_name_short} {date_str}"
        text_x = x + padding
        text_y = y + 5
        
        # Draw day name and date inline
        self.draw_text(draw, header_text, text_x, text_y, self.fonts['normal'], self.white)

        # Draw weather icon and temperature centered below day/date
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
                weather_icon_font = self.fonts.get('weather_tiny', self.fonts['small'])
                temp_font = self.fonts['small']
                
                # Measure widths separately
                icon_width = 0
                if icon:
                    icon_bbox = draw.textbbox((0, 0), icon, font=weather_icon_font)
                    icon_width = icon_bbox[2] - icon_bbox[0]
                
                temp_width = 0
                if temp_str:
                    temp_bbox = draw.textbbox((0, 0), temp_str, font=temp_font)
                    temp_width = temp_bbox[2] - temp_bbox[0]
                
                # Center weather display horizontally in the column
                total_width = icon_width + (3 if icon and temp_str else 0) + temp_width
                weather_x = x + (width - total_width) // 2
                weather_y = y + 19
                
                # Draw icon first
                if icon:
                    self.draw_text(draw, icon, weather_x, weather_y, weather_icon_font, self.white)
                    weather_x += icon_width + 3
                
                # Draw temperature
                if temp_str:
                    self.draw_text(draw, temp_str, weather_x, weather_y + 1, temp_font, self.white)

        # Draw events if any
        if day_events and day_events.events:
            self._draw_events_in_cell(
                draw,
                text_x,
                y + header_height + all_day_height,  # Start below the header and all-day spans
                width - (2 * padding),
                height - header_height - all_day_height - 2,
                day_events,
                span_keys
            )

    def _draw_events_in_cell(self, draw, x, y, width, height, day_events, span_keys):
        """
        Draw events with time-based vertical positioning and bars that grow to fit wrapped text.
        Events falling earlier in the day appear higher; a tall bar pushes subsequent events down.

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

        filtered_events = [event for event in day_events.events if self._event_key(event) not in span_keys]
        # Sort by start time so time-positioning is meaningful
        filtered_events.sort(key=lambda e: e.start)
        events_to_show = filtered_events[:max_events]
        num_events = len(events_to_show)

        # Dynamic sizing based on number of events
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

        # Time range: 6 AM to 10 PM
        start_hour = 6
        end_hour = 22
        pixels_per_hour = height / (end_hour - start_hour)

        current_y = y  # minimum y for next bar (prevents overlapping previous bar)

        for event in events_to_show:
            # Format event text
            if show_time and not event.all_day:
                time_str = event.start.strftime("%I:%M %p")
                event_text = f"{time_str} {event.title}"
            else:
                event_text = event.title

            # Calculate time-based y; all-day events start at top
            if event.all_day:
                time_y = y
            else:
                event_hour = max(start_hour, min(end_hour, event.start.hour + event.start.minute / 60.0))
                time_y = y + int((event_hour - start_hour) * pixels_per_hour)

            # Honour time position but never overlap the previous bar
            event_y = max(time_y, current_y)

            # Wrap text based on remaining space below event_y
            remaining_height = (y + height) - event_y
            max_text_lines = max(1, min(6, (remaining_height - 4) // line_height))
            text_lines = self.wrap_text(
                event_text,
                width - 6,
                self.fonts[font_key],
                draw,
                max_lines=max_text_lines
            )

            bar_height = max(min_bar_height, len(text_lines) * line_height + 4)

            if event_y + bar_height > y + height:
                break

            # Draw colored bar
            self.draw_box(draw, x, event_y, width, bar_height, fill=event.color)

            text_y = event_y + 2
            for line in text_lines:
                self.draw_text(draw, line, x + 3, text_y, self.fonts[font_key], self.white)
                text_y += line_height

            current_y = event_y + bar_height + 2

        # Show "+X more" if there are overflow events
        overflow_count = max(0, len(filtered_events) - max_events)
        if overflow_count > 0 and current_y + 15 <= y + height:
            self.draw_text(draw, f"+{overflow_count} more", x, current_y, self.fonts['small'], self.black)
