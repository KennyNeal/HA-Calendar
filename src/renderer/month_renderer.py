"""Month calendar renderer."""

from datetime import datetime, date, timedelta
from calendar import monthrange
from renderer.base_renderer import BaseRenderer


class MonthRenderer(BaseRenderer):
    """Renders a traditional month calendar view."""

    def __init__(self, config, color_manager):
        """
        Initialize month renderer.

        Args:
            config: Configuration dictionary
            color_manager: ColorManager instance
        """
        super().__init__(config, color_manager)
        self.view_config = config['views']['month']

    def render(self, events_by_day, weather_info, footer_sensor_text=None):
        """
        Render month calendar view.

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
        # Layout: Up to 6 rows (weeks) x 7 columns (days)
        footer_height = 40  # Footer with last updated time
        available_height = self.height - footer_height
        row_height = available_height // 6
        col_width = self.width // 7

        # Get current month info
        today = date.today()
        year, month = today.year, today.month
        _, last_day = monthrange(year, month)

        # Draw month name
        month_name = today.strftime("%B %Y")
        self.draw_text(draw, month_name, self.width // 2, y + 10, self.fonts['large'], self.black, align='center')

        # Draw day headers (Sun, Mon, Tue, etc.)
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        header_y = y + 45
        for i, day_name in enumerate(day_names):
            x = i * col_width + col_width // 2
            self.draw_text(draw, day_name, x, header_y, self.fonts['medium'], self.black, align='center')

        # Calculate calendar start (Monday before or on first of month)
        first_day = date(year, month, 1)
        days_to_monday = first_day.weekday()  # 0=Monday
        calendar_start = first_day - timedelta(days=days_to_monday)

        # Draw calendar grid
        grid_start_y = y + 70
        current_date = calendar_start

        for week in range(6):  # Up to 6 weeks in a month view
            for day_col in range(7):
                x = day_col * col_width
                y = grid_start_y + (week * row_height)

                # Check if this date is in current month
                in_current_month = (current_date.month == month)
                is_today = (current_date == today)

                # Draw cell
                self._draw_day_cell(
                    draw,
                    x,
                    y,
                    col_width,
                    row_height,
                    current_date,
                    events_by_day.get(current_date),
                    is_today,
                    in_current_month,
                    weather_info if is_today else None
                )

                current_date += timedelta(days=1)

        # Draw footer with last updated time
        self.draw_footer(draw, available_height, footer_height, footer_sensor_text)

        # Legend removed - calendar colors are self-explanatory

        self.logger.info("Rendered month calendar view")
        return image

    def _draw_day_cell(self, draw, x, y, width, height, date_obj, day_events, is_today, in_current_month, weather_info=None):
        """
        Draw a single day cell for month view.

        Args:
            draw: ImageDraw object
            x: X coordinate
            y: Y coordinate
            width: Cell width
            height: Cell height
            date_obj: Date object for this cell
            day_events: DayEvents object or None
            is_today: Boolean indicating if this is today
            in_current_month: Boolean indicating if date is in current month
            weather_info: WeatherInfo object (today only)
        """
        # Draw cell border
        border_width = 1
        self.draw_box(draw, x, y, width, height, outline=self.black, outline_width=border_width)

        # Draw blue header background bar for today's date
        if is_today and in_current_month:
            header_height = 25
            self.draw_box(draw, x + 1, y + 1, width - 2, header_height - 2, fill=self.blue)
            
            # Draw date in white on blue background
            date_str = str(date_obj.day)
            self.draw_text(draw, date_str, x + 5, y + 5, self.fonts['medium'], self.white)
            
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
                    weather_y = y + 4
                    
                    # Draw weather info
                    self.draw_text(draw, weather_display, weather_x, weather_y, weather_icon_font, self.white)
            
            # Draw event indicators below the header
            if day_events and day_events.events:
                self._draw_event_indicators(
                    draw,
                    x + 5,
                    y + header_height + 3,
                    width - 10,
                    height - header_height - 5,
                    day_events
                )
        else:
            # Draw date number
            padding = 5
            date_str = str(date_obj.day)
            text_color = self.black if in_current_month else self.black
            
            self.draw_text(draw, date_str, x + padding, y + padding, self.fonts['medium'], text_color)

            # Draw weather icon and temperature for non-today dates
            if weather_info and in_current_month:
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
                    weather_y = y + 5
                    
                    # Draw weather info
                    self.draw_text(draw, weather_display, weather_x, weather_y, weather_icon_font, self.black)

            # Draw event indicators if any
            if day_events and day_events.events and in_current_month:
                self._draw_event_indicators(
                    draw,
                    x + padding,
                    y + 25,  # Start below the date
                    width - (2 * padding),
                    height - 30,
                    day_events
                )

    def _draw_event_indicators(self, draw, x, y, width, height, day_events):
        """
        Draw event indicators (colored dots/bars) in cell.

        Args:
            draw: ImageDraw object
            x: X coordinate for event area
            y: Y coordinate for event area
            width: Available width
            height: Available height
            day_events: DayEvents object
        """
        max_events = self.view_config.get('max_events_per_day', 3)
        events_to_show = day_events.events[:max_events]
        num_events = len(events_to_show)
        
        # Dynamic sizing: fewer events = bigger dots
        if num_events <= 1:
            dot_size = 12
            dot_spacing = 14
        elif num_events <= 2:
            dot_size = 10
            dot_spacing = 12
        else:
            dot_size = 8
            dot_spacing = 10
        current_x = x
        current_y = y

        for i, event in enumerate(events_to_show):
            if current_x + dot_size > x + width:
                # Move to next line
                current_x = x
                current_y += dot_spacing
                if current_y + dot_size > y + height:
                    break  # No more space

            # Draw colored indicator
            self.draw_box(draw, current_x, current_y, dot_size, dot_size, fill=event.color)
            current_x += dot_size + 3

        # Show count if more events
        if hasattr(day_events, 'overflow_count') and day_events.overflow_count > 0:
            count_text = f"+{day_events.overflow_count}"
            self.draw_text(draw, count_text, x, y + 15, self.fonts['small'], self.black)
