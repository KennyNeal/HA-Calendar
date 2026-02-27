"""Agenda/list calendar renderer."""

from datetime import datetime, date, timedelta
from renderer.base_renderer import BaseRenderer


class AgendaRenderer(BaseRenderer):
    """Renders a chronological list view of events."""

    def __init__(self, config, color_manager):
        """
        Initialize agenda renderer.

        Args:
            config: Configuration dictionary
            color_manager: ColorManager instance
        """
        super().__init__(config, color_manager)
        self.view_config = config['views']['agenda']

    def render(self, events_by_day, weather_info, footer_sensor_text=None):
        """
        Render agenda list view.

        Args:
            events_by_day: Dictionary mapping date to DayEvents
            weather_info: WeatherInfo object
            footer_sensor_text: Optional sensor text for footer

        Returns:
            PIL.Image: Rendered calendar image
        """
        image, draw = self.create_canvas()

        y = 0

        # Header and footer layout
        header_height = 50
        footer_height = 40  # Footer with last updated time
        content_top = header_height + 10
        content_bottom = self.height - footer_height

        # Split main content area (left: agenda, right: weather)
        left_width = int(self.width * 0.65)
        right_x = left_width
        right_width = self.width - right_x
        content_y = content_top

        # Draw blue header bar with title
        self.draw_box(draw, 0, y, self.width, header_height, fill=self.blue)
        self.draw_text(
            draw,
            "Upcoming Events",
            self.width // 2,
            y + 12,
            self.fonts['large'],
            self.white,
            align='center'
        )

        # Draw divider between agenda and weather panel
        draw.line([(right_x, header_height), (right_x, content_bottom)], fill=self.black, width=2)

        # Get sorted dates
        sorted_dates = sorted(events_by_day.keys())

        # Collect unique calendars for legend {name: color}
        calendar_legend = {}

        # Draw events chronologically
        line_height = 24
        padding = 20
        max_width = left_width - (2 * padding)

        for event_date in sorted_dates:
            day_events = events_by_day[event_date]

            if not day_events.events:
                continue  # Skip days with no events

            # Filter past events for today
            events_to_show = []
            for event in day_events.events:
                # If today, skip events that have already passed
                if day_events.is_today and not event.all_day:
                    # Handle both timezone-aware and timezone-naive datetimes
                    current_time = datetime.now(event.start.tzinfo) if event.start.tzinfo else datetime.now()
                    if event.start < current_time:
                        continue
                events_to_show.append(event)

            if not events_to_show:
                continue  # Skip if no events to show

            # Check if this is today or tomorrow
            is_tomorrow = event_date == date.today() + timedelta(days=1)
            
            # For days other than today/tomorrow, check if we can show all events
            if not day_events.is_today and not is_tomorrow:
                # Calculate space needed for this day
                text_x = padding + 10 + 10 + 10  # padding + indicator position + indicator size + gap
                space_needed = line_height + 5  # date header with underline
                
                for event in events_to_show:
                    if event.all_day:
                        event_text = f"{event.title} (All Day)"
                    else:
                        time_str = event.start.strftime("%I:%M %p")
                        event_text = f"{time_str} - {event.title}"
                    
                    text_lines = self.wrap_text(
                        event_text,
                        max_width - (text_x - padding),
                        self.fonts['medium'],
                        draw,
                        max_lines=2
                    )
                    space_needed += line_height * len(text_lines)
                
                space_needed += 6  # spacing between days
                
                # Skip this day if we can't show all events
                if content_y + space_needed > content_bottom:
                    continue

            # Draw date header
            if day_events.is_today:
                date_str = f"TODAY - {event_date.strftime('%A, %B %d')}"
            elif event_date == date.today() + timedelta(days=1):
                date_str = f"TOMORROW - {event_date.strftime('%A, %B %d')}"
            else:
                date_str = event_date.strftime("%A, %B %d")

            self.draw_text(
                draw,
                date_str,
                padding,
                content_y,
                self.fonts['large'],
                self.black
            )

            # Draw underline for date
            date_bbox = draw.textbbox((padding, content_y), date_str, font=self.fonts['large'])
            date_width = date_bbox[2] - date_bbox[0]
            draw.line(
                [(padding, content_y + 24), (padding + date_width, content_y + 24)],
                fill=self.black,
                width=1
            )

            content_y += line_height + 5

            # Draw events for this day
            for event in events_to_show:
                if content_y + line_height > content_bottom:
                    break  # No more space

                # Draw colored indicator
                indicator_size = 10
                indicator_x = padding + 10
                indicator_y = content_y + 4
                self.draw_box(
                    draw,
                    indicator_x,
                    indicator_y,
                    indicator_size,
                    indicator_size,
                    fill=event.color
                )

                # Format event text
                text_x = indicator_x + indicator_size + 10

                # Track calendar for legend
                if event.calendar_name and event.calendar_name not in calendar_legend:
                    calendar_legend[event.calendar_name] = event.color

                if event.all_day:
                    event_text = f"{event.title} (All Day)"
                else:
                    time_str = event.start.strftime("%I:%M %p")
                    event_text = f"{time_str} - {event.title}"

                # Draw wrapped event text
                text_lines = self.wrap_text(
                    event_text,
                    max_width - (text_x - padding),
                    self.fonts['medium'],
                    draw,
                    max_lines=2
                )

                required_height = line_height * len(text_lines)
                if content_y + required_height > content_bottom:
                    self.draw_text(
                        draw,
                        "... (more events not shown)",
                        padding,
                        content_y,
                        self.fonts['medium'],
                        self.black
                    )
                    content_y = content_bottom
                    break

                for line in text_lines:
                    self.draw_text(
                        draw,
                        line,
                        text_x,
                        content_y,
                        self.fonts['medium'],
                        self.black
                    )
                    content_y += line_height

            # Add spacing between days
            content_y += 6

            if content_y >= content_bottom:
                break

        # Draw weather station panel on the right
        weather_top = content_top + 5
        weather_x_center = right_x + (right_width // 2)
        weather_y = weather_top

        if weather_info:
            from weather_data import WeatherDataProcessor
            weather_processor = WeatherDataProcessor()

            icon, icon_color = weather_processor.get_weather_icon_with_color(weather_info.condition.lower())
            temp_str = f"{weather_info.temperature:.0f}{weather_info.temperature_unit}"

            icon_font = self.fonts.get('weather_large', self.fonts['xlarge'])
            temp_font = self.fonts['xlarge']

            icon_bbox = draw.textbbox((0, 0), icon, font=icon_font) if icon else (0, 0, 0, 0)
            icon_width = icon_bbox[2] - icon_bbox[0]
            icon_height = icon_bbox[3] - icon_bbox[1]
            temp_bbox = draw.textbbox((0, 0), temp_str, font=temp_font)
            temp_width = temp_bbox[2] - temp_bbox[0]

            gap = 10 if icon else 0
            total_width = icon_width + gap + temp_width
            start_x = weather_x_center - (total_width // 2)

            if icon:
                icon_rgb = self.color_manager.get_rgb(icon_color)
                # Use outlined text for gold icons to make them more visible
                if icon_color == 'gold':
                    self.draw_text_with_outline(draw, icon, start_x, weather_y, icon_font, icon_rgb)
                else:
                    self.draw_text(draw, icon, start_x, weather_y, icon_font, icon_rgb)
            self.draw_text(draw, temp_str, start_x + icon_width + gap, weather_y + 6, temp_font, self.black)

            # Draw formatted condition 5 pixels below the icon
            formatted_condition = self._format_condition(weather_info.condition)
            condition_y = weather_y + icon_height + 5
            self.draw_text(
                draw,
                formatted_condition,
                weather_x_center,
                condition_y,
                self.fonts['large'],
                self.black,
                align='center',
                max_width=right_width - 24
            )
            
            # Draw today's high and low temperatures with weather icons on the left
            today = date.today()
            high_low_y = condition_y + 32  # Below condition text
            if weather_info.forecast:
                date_key = today.isoformat()
                today_forecast = weather_info.forecast.get(date_key)
                if today_forecast:
                    high_str = f"{int(today_forecast.temperature)}°"
                    low_str = f"{int(today_forecast.temperature_low)}°" if today_forecast.temperature_low is not None else ""
                    
                    if high_str and low_str:
                        # Thermometer icon with high/low temps and humidity on same line
                        thermo_icon = '\uf055'  # Thermometer icon
                        humidity_icon = '\uf07a'  # Humidity icon
                        
                        weather_icon_font = self.fonts.get('weather_medium', self.fonts['large'])
                        temp_font = self.fonts['large']
                        gap_between = 8
                        
                        # Format temperatures as "high/low"
                        temp_text = f"{high_str}/{low_str}"
                        humidity_text = f"{weather_info.humidity}%"
                        
                        # Measure dimensions
                        thermo_bbox = draw.textbbox((0, 0), thermo_icon, font=weather_icon_font)
                        thermo_width = thermo_bbox[2] - thermo_bbox[0]
                        temp_bbox = draw.textbbox((0, 0), temp_text, font=temp_font)
                        temp_width = temp_bbox[2] - temp_bbox[0]
                        humidity_icon_bbox = draw.textbbox((0, 0), humidity_icon, font=weather_icon_font)
                        humidity_icon_width = humidity_icon_bbox[2] - humidity_icon_bbox[0]
                        
                        # Calculate total width: thermo + gap + temp + gap + humidity_icon + gap + humidity_percent
                        total_width = thermo_width + gap_between + temp_width + gap_between + humidity_icon_width + gap_between + len(humidity_text) * 8
                        
                        # Position closer to center of weather panel
                        high_low_x = weather_x_center - (total_width // 2)
                        
                        # Draw thermometer icon
                        x_pos = high_low_x
                        self.draw_text(draw, thermo_icon, x_pos, high_low_y, weather_icon_font, self.black)
                        
                        # Draw high/low temps
                        x_pos += thermo_width + gap_between
                        self.draw_text(draw, temp_text, x_pos, high_low_y, temp_font, self.black)
                        
                        # Draw humidity icon in blue
                        x_pos += temp_width + gap_between
                        humidity_icon_rgb = self.color_manager.get_rgb('blue')
                        self.draw_text(draw, humidity_icon, x_pos, high_low_y, weather_icon_font, humidity_icon_rgb)
                        
                        # Draw humidity percentage
                        x_pos += humidity_icon_width + gap_between
                        self.draw_text(draw, humidity_text, x_pos, high_low_y, temp_font, humidity_icon_rgb)
            
            # Calculate positions for forecast - bottoms of temps 3 pixels above footer
            footer_y = self.height - footer_height
            # Forecast layout: day_label at row_y, icon at row_y+24, temp at row_y+72
            # Assuming temp text height ~20px, bottom is at row_y+92
            # We want: row_y + 92 = footer_y - 3, so row_y = footer_y - 95
            forecast_y = footer_y - 95
            
            # Center humidity and wind between condition/high-low and forecast
            # condition/high-low ends at high_low_y + text_height (estimate ~24px)
            # We have 1 detail line, 30px tall
            condition_end = high_low_y + 30
            available_space = forecast_y - condition_end
            details_start_y = condition_end + (available_space - 30) // 2
            
            wind_arrow = self._bearing_to_arrow(weather_info.wind_bearing)
            wind_suffix = f" {wind_arrow}" if wind_arrow else ""
            
            # Draw wind details
            wind_detail = f"Wind: {weather_info.wind_speed:.0f} {weather_info.wind_speed_unit}{wind_suffix}"
            self.draw_text(
                draw,
                wind_detail,
                right_x + 12,
                details_start_y + 30,
                self.fonts['large'],
                self.black,
                max_width=right_width - 24
            )
        else:
            self.draw_text(
                draw,
                "Weather Unavailable",
                weather_x_center,
                weather_y,
                self.fonts['medium'],
                self.black,
                align='center'
            )
            weather_y += 40
            footer_y = self.height - footer_height
            forecast_y = weather_y + 16
            forecast_row2_y = forecast_y + 88

        # 4-day forecast (tomorrow + next 3 days) in a single row
        forecast_item_width = right_width // 4
        if weather_info and weather_info.forecast:
            today = date.today()
            from weather_data import WeatherDataProcessor
            weather_processor = WeatherDataProcessor()
            weather_icon_font = self.fonts.get('weather_medium', self.fonts['large'])

            for day_offset in range(1, 5):  # Skip today (day 0), show days 1-4
                forecast_date = today + timedelta(days=day_offset)
                date_key = forecast_date.isoformat()
                forecast = weather_info.forecast.get(date_key)
                if not forecast:
                    continue

                icon, icon_color = weather_processor.get_weather_icon_with_color(forecast.condition.lower())
                high_str = f"{int(forecast.temperature)}°"
                low_str = f"{int(forecast.temperature_low)}°" if forecast.temperature_low is not None else ""
                temp_str = f"{high_str}/{low_str}" if low_str else high_str
                day_label = forecast_date.strftime("%a")

                # Single row: 4 columns
                col = day_offset - 1  # 0, 1, 2, 3
                x_pos = right_x + (col * forecast_item_width) + (forecast_item_width // 2)
                row_y = forecast_y

                self.draw_text(draw, day_label, x_pos, row_y, self.fonts['large'], self.black, align='center')
                if icon:
                    icon_rgb = self.color_manager.get_rgb(icon_color)
                    # Use outlined text for gold icons to make them more visible
                    if icon_color == 'gold':
                        self.draw_text_with_outline(draw, icon, x_pos, row_y + 24, weather_icon_font, icon_rgb, align='center')
                    else:
                        self.draw_text(draw, icon, x_pos, row_y + 24, weather_icon_font, icon_rgb, align='center')
                self.draw_text(draw, temp_str, x_pos, row_y + 72, self.fonts['medium'], self.black, align='center')

        # Draw footer with last updated time and calendar legend
        footer_y = self.height - footer_height
        self.draw_footer(draw, footer_y, footer_height, footer_sensor_text)
        self.draw_calendar_legend(draw, footer_y, footer_height, calendar_legend)

        self.logger.info("Rendered agenda list view")
        return image

    def _format_condition(self, condition):
        """Format weather condition for display.
        
        Args:
            condition: Raw weather condition string
            
        Returns:
            Formatted condition string with proper capitalization
        """
        if not condition:
            return ""
        
        # Common weather condition mappings
        condition_map = {
            'partlycloudy': 'Partly Cloudy',
            'mostlycloudy': 'Mostly Cloudy',
            'mostlysunny': 'Mostly Sunny',
            'partlysunny': 'Partly Sunny',
            'clearnight': 'Clear Night',
            'cloudynight': 'Cloudy Night',
            'rainyday': 'Rainy Day',
            'rainynight': 'Rainy Night',
            'snowyday': 'Snowy Day',
            'snowynight': 'Snowy Night',
        }
        
        # Check if we have a direct mapping
        condition_lower = condition.lower().replace(' ', '').replace('-', '').replace('_', '')
        if condition_lower in condition_map:
            return condition_map[condition_lower]
        
        # Otherwise, try to intelligently split and capitalize
        # Replace common separators with spaces
        formatted = condition.replace('_', ' ').replace('-', ' ')
        
        # Title case each word
        return formatted.title()
    
    def _bearing_to_arrow(self, bearing):
        if bearing is None:
            return ""

        direction = bearing % 360
        if 22.5 <= direction < 67.5:
            return "NE"  # Northeast
        if 67.5 <= direction < 112.5:
            return "E"   # East
        if 112.5 <= direction < 157.5:
            return "SE"  # Southeast
        if 157.5 <= direction < 202.5:
            return "S"   # South
        if 202.5 <= direction < 247.5:
            return "SW"  # Southwest
        if 247.5 <= direction < 292.5:
            return "W"   # West
        if 292.5 <= direction < 337.5:
            return "NW"  # Northwest
        return "N"   # North
