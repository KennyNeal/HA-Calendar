"""Calendar data processing and event management."""

from dataclasses import dataclass
from datetime import datetime, date, time, timedelta
from dateutil import parser
from collections import defaultdict
from utils.logger import get_logger


@dataclass
class CalendarEvent:
    """Represents a calendar event."""
    calendar_id: str
    calendar_name: str
    title: str
    start: datetime
    end: datetime
    all_day: bool
    color: tuple
    color_name: str


@dataclass
class DayEvents:
    """Represents events for a specific day."""
    date: date
    events: list
    is_today: bool


class CalendarDataProcessor:
    """Processes calendar event data from Home Assistant."""

    def __init__(self, color_manager):
        """
        Initialize calendar data processor.

        Args:
            color_manager: ColorManager instance for color assignment
        """
        self.color_manager = color_manager
        self.logger = get_logger()

    def parse_event(self, event_data, calendar_id):
        """
        Parse a single event from HA API response.

        Args:
            event_data: Event dictionary from API
            calendar_id: Source calendar entity ID

        Returns:
            CalendarEvent: Parsed event object
        """
        try:
            # Parse start and end times
            # Handle HA's nested date structure
            start_data = event_data['start']
            end_data = event_data['end']

            # Check if it's an all-day event (has 'date' key)
            if 'date' in start_data:
                # All-day event - make timezone-aware
                start = datetime.strptime(start_data['date'], '%Y-%m-%d')
                end = datetime.strptime(end_data['date'], '%Y-%m-%d')
                # Make timezone-aware (using local timezone)
                import pytz
                local_tz = pytz.timezone('America/Chicago')  # Adjust to your timezone
                start = local_tz.localize(start)
                end = local_tz.localize(end)
                all_day = True
            elif 'dateTime' in start_data:
                # Timed event
                start = parser.isoparse(start_data['dateTime'])
                end = parser.isoparse(end_data['dateTime'])
                # Check if it spans full days
                all_day = (
                    start.time() == time(0, 0, 0) and
                    end.time() == time(0, 0, 0) and
                    (end - start).days >= 1
                )
            else:
                # Fallback: try to parse as-is
                start = parser.isoparse(str(start_data))
                end = parser.isoparse(str(end_data))
                all_day = False

            # Get color for this calendar
            color_info = self.color_manager.get_calendar_color(calendar_id)
            self.logger.info(f"Event '{event_data.get('summary')}' from {calendar_id}: color={color_info['name']} RGB{color_info['rgb']}")

            return CalendarEvent(
                calendar_id=calendar_id,
                calendar_name=color_info['display_name'],
                title=event_data.get('summary', 'Untitled Event'),
                start=start,
                end=end,
                all_day=all_day,
                color=color_info['rgb'],
                color_name=color_info['name']
            )
        except Exception as e:
            self.logger.error(f"Failed to parse event: {e}")
            self.logger.error(f"Event data: {event_data}")
            return None

    def parse_all_events(self, all_calendar_events):
        """
        Parse events from all calendars.

        Args:
            all_calendar_events: Dict mapping calendar_id to list of event dicts

        Returns:
            list: List of CalendarEvent objects
        """
        parsed_events = []

        for calendar_id, events in all_calendar_events.items():
            for event_data in events:
                event = self.parse_event(event_data, calendar_id)
                if event:
                    parsed_events.append(event)

        # Sort by start time, then by title for consistency
        parsed_events.sort(key=lambda e: (e.start, e.title))

        self.logger.info(f"Parsed {len(parsed_events)} total events from all calendars")
        return parsed_events

    def group_events_by_day(self, events, start_date=None, end_date=None):
        """
        Group events by day.

        Args:
            events: List of CalendarEvent objects
            start_date: Optional start date to filter (inclusive)
            end_date: Optional end date to filter (exclusive)

        Returns:
            dict: Dictionary mapping date to DayEvents object
        """
        today = date.today()
        events_by_day = defaultdict(list)

        for event in events:
            event_start = event.start.date()
            event_end = event.end.date()
            
            # For multi-day events, add to each day they span
            current_date = event_start
            while current_date < event_end:
                # Filter by date range if specified
                if start_date and current_date < start_date:
                    current_date += timedelta(days=1)
                    continue
                if end_date and current_date >= end_date:
                    break

                events_by_day[current_date].append(event)
                current_date += timedelta(days=1)

        # Convert to DayEvents objects
        day_events_dict = {}
        for day, day_event_list in events_by_day.items():
            # Sort events within the day by start time, then all-day events first
            day_event_list.sort(key=lambda e: (not e.all_day, e.start))

            day_events_dict[day] = DayEvents(
                date=day,
                events=day_event_list,
                is_today=(day == today)
            )

        return day_events_dict

    def limit_events_per_day(self, events_by_day, max_events):
        """
        Limit the number of events shown per day.

        Args:
            events_by_day: Dictionary mapping date to DayEvents
            max_events: Maximum number of events to show per day

        Returns:
            dict: Dictionary with limited events per day
        """
        limited_events = {}

        for day, day_events in events_by_day.items():
            if len(day_events.events) > max_events:
                # Keep the first max_events and add an indicator for more
                limited_events[day] = DayEvents(
                    date=day_events.date,
                    events=day_events.events[:max_events],
                    is_today=day_events.is_today
                )
                # Store overflow count for display
                limited_events[day].overflow_count = len(day_events.events) - max_events
            else:
                limited_events[day] = day_events
                limited_events[day].overflow_count = 0

        return limited_events

    def get_events_for_range(self, events, days_ahead=14, max_per_day=None):
        """
        Get events for a date range starting from today.

        Args:
            events: List of CalendarEvent objects
            days_ahead: Number of days to include (default 14)
            max_per_day: Optional maximum events per day

        Returns:
            dict: Dictionary mapping date to DayEvents
        """
        today = date.today()
        end_date = today + timedelta(days=days_ahead)

        events_by_day = self.group_events_by_day(events, start_date=today, end_date=end_date)

        if max_per_day:
            events_by_day = self.limit_events_per_day(events_by_day, max_per_day)

        return events_by_day

    def get_events_for_month(self, events, year, month):
        """
        Get events for a specific month.

        Args:
            events: List of CalendarEvent objects
            year: Year
            month: Month (1-12)

        Returns:
            dict: Dictionary mapping date to DayEvents
        """
        from calendar import monthrange

        start_date = date(year, month, 1)
        _, last_day = monthrange(year, month)
        end_date = date(year, month, last_day)

        # Extend to include full weeks for calendar view
        # Find the Monday before or on start_date
        days_to_monday = start_date.weekday()
        calendar_start = start_date - timedelta(days=days_to_monday)

        # Find the Sunday after or on end_date
        days_to_sunday = 6 - end_date.weekday()
        calendar_end = end_date + timedelta(days=days_to_sunday + 1)

        events_by_day = self.group_events_by_day(events, start_date=calendar_start, end_date=calendar_end)

        return events_by_day
