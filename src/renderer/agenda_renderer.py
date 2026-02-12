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

    def render(self, events_by_day, weather_info):
        """
        Render agenda/list view.

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

        # Calculate available space
        footer_height = 40
        available_height = self.height - header_height - footer_height
        content_y = y + 10

        # Draw agenda title
        self.draw_text(
            draw,
            "Upcoming Events",
            self.width // 2,
            content_y,
            self.fonts['large'],
            self.black,
            align='center'
        )

        content_y += 35

        # Get sorted dates
        sorted_dates = sorted(events_by_day.keys())

        # Draw events chronologically
        line_height = 24
        padding = 20
        max_width = self.width - (2 * padding)

        for event_date in sorted_dates:
            day_events = events_by_day[event_date]

            if not day_events.events:
                continue  # Skip days with no events

            # Check if we have space for this day's events
            if content_y + line_height + (len(day_events.events) * line_height) > header_height + available_height:
                # No more space, show "..." and break
                self.draw_text(
                    draw,
                    "... (more events not shown)",
                    padding,
                    content_y,
                    self.fonts['normal'],
                    self.black
                )
                break

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
                self.fonts['medium'],
                self.black
            )

            # Draw underline for date
            date_bbox = draw.textbbox((padding, content_y), date_str, font=self.fonts['medium'])
            date_width = date_bbox[2] - date_bbox[0]
            draw.line(
                [(padding, content_y + 18), (padding + date_width, content_y + 18)],
                fill=self.black,
                width=1
            )

            content_y += line_height + 5

            # Draw events for this day
            for event in day_events.events:
                if content_y + line_height > header_height + available_height:
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

                if event.all_day:
                    event_text = f"{event.title} (All Day) - {event.calendar_name}"
                else:
                    time_str = event.start.strftime("%I:%M %p")
                    event_text = f"{time_str} - {event.title} ({event.calendar_name})"

                # Draw event text
                self.draw_text(
                    draw,
                    event_text,
                    text_x,
                    content_y,
                    self.fonts['normal'],
                    self.black,
                    max_width=max_width - (text_x - padding)
                )

                content_y += line_height

            # Add spacing between days
            content_y += 10

        # Draw legend in footer
        footer_y = header_height + available_height
        legend_data = self.color_manager.get_legend()
        self.draw_legend(draw, footer_y + 5, legend_data)

        self.logger.info("Rendered agenda list view")
        return image
