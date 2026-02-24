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

    def render(self, events_by_day, weather_info, footer_sensor_text=None):
        """
        Render two-week view.

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
        # Layout: 2 rows (weeks) x 7 columns (days)
        footer_height = 40  # Footer with last updated time
        available_height = self.height - footer_height
        row_height = available_height // 2
        col_width = self.width // 7

        # Get today's date for reference
        today = date.today()

        # Draw week 1 (current week)
        week1_start = today - timedelta(days=today.weekday())  # Monday of current week
        self._draw_week_row(draw, week1_start, y, row_height, col_width, events_by_day, weather_info)

        # Draw week 2 (next week)
        week2_start = week1_start + timedelta(days=7)
        self._draw_week_row(draw, week2_start, y + row_height, row_height, col_width, events_by_day, weather_info)

        # Draw footer with last updated time
        self.draw_footer(draw, y + available_height, footer_height, footer_sensor_text)

        # Legend removed - calendar colors are self-explanatory

        self.logger.info("Rendered two-week grid view")
        return image

    def _draw_week_row(self, draw, week_start, y, row_height, col_width, events_by_day, weather_info=None):
        """
        Draw a single week row.

        Args:
            draw: ImageDraw object
            week_start: Date of Monday for this week
            y: Y coordinate for this row
            row_height: Height of the row
            col_width: Width of each column
            events_by_day: Dictionary mapping date to DayEvents
            weather_info: WeatherInfo object (for current week only)
        """
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        today = date.today()

        row_dates = [week_start + timedelta(days=i) for i in range(7)]
        lanes, overflow, span_keys = self._get_all_day_span_lanes(row_dates, events_by_day, max_lanes=3)
        lane_height = 18
        all_day_height = lane_height * len(lanes)

        all_day_top = y + 30
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
                weather_info if is_today else None
            )

    def _draw_day_cell(self, draw, x, y, width, height, date_obj, day_name, day_events, is_today, all_day_height, span_keys, weather_info=None):
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
            all_day_height: Height of all-day event spans
            span_keys: Set of span event keys
            weather_info: WeatherInfo object (today only)
        """
        # Draw cell border
        border_width = 1
        self.draw_box(draw, x, y, width, height, outline=self.black, outline_width=border_width)

        # Draw blue header background bar (height 30)
        header_height = 30
        self.draw_box(draw, x + 1, y + 1, width - 2, header_height - 2, fill=self.blue)

        # Draw day name and date in white on blue background
        date_str = f"{day_name} {date_obj.day}"
        padding = 5
        text_x = x + padding
        text_y = y + 5

        self.draw_text(draw, date_str, text_x, text_y, self.fonts['medium'], self.white)

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
            
            # Fallback to current temperature if no forecast available
            if not temp_str and weather_info and weather_info.temperature:
                temp_str = f"{int(weather_info.temperature)}°"
            
            if icon or temp_str:
                weather_icon_font = self.fonts.get('weather_small', self.fonts['small'])
                
                # Prepare text string: icon (if available) + temperature
                weather_display = ""
                if icon:
                    weather_display = icon + " "
                if temp_str:
                    weather_display += temp_str
                
                # Measure width
                display_bbox = draw.textbbox((0, 0), weather_display, font=weather_icon_font)
                display_width = display_bbox[2] - display_bbox[0]
                
                # Position from right edge of cell
                weather_x = x + width - 5 - display_width
                weather_y = y + 6
                
                # Draw weather info
                self.draw_text(draw, weather_display, weather_x, weather_y, weather_icon_font, self.white)

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

        filtered_events = [event for event in day_events.events if self._event_key(event) not in span_keys]
        events_to_show = filtered_events[:max_events]
        num_events = len(events_to_show)
        
        # Dynamic sizing based on number of events
        # Fewer events = larger, more readable text
        if num_events <= 2:
            line_height = 18
            min_bar_height = 36
            font_key = 'medium'
        elif num_events <= 3:
            line_height = 16
            min_bar_height = 28
            font_key = 'normal'
        else:
            line_height = 14
            min_bar_height = 22
            font_key = 'small'
        
        current_y = y

        for event in events_to_show:
            # Format event text
            if show_time and not event.all_day:
                time_str = event.start.strftime("%I:%M %p")
                event_text = f"{time_str} {event.title}"
            else:
                event_text = event.title

            # Wrap text based on remaining space in the cell
            remaining_height = (y + height) - current_y
            max_text_lines = max(1, min(6, (remaining_height - 4) // line_height))
            text_lines = self.wrap_text(
                event_text,
                width - 6,
                self.fonts[font_key],
                draw,
                max_lines=max_text_lines
            )

            # Calculate bar height based on number of lines
            bar_height = max(min_bar_height, len(text_lines) * line_height + 4)

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
        overflow_count = max(0, len(filtered_events) - max_events)
        if overflow_count > 0:
            if current_y + 15 <= y + height:
                more_text = f"+{overflow_count} more"
                self.draw_text(
                    draw,
                    more_text,
                    x,
                    current_y,
                    self.fonts['small'],
                    self.black
                )
