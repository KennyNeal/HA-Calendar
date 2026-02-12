"""Home Assistant API client for fetching calendar and weather data."""

import requests
from datetime import datetime, timedelta
import time
from utils.logger import get_logger


class HomeAssistantClient:
    """Client for interacting with Home Assistant API."""

    def __init__(self, config):
        """
        Initialize Home Assistant client.

        Args:
            config: Configuration dictionary with HA settings
        """
        self.config = config
        ha_config = config['home_assistant']
        self.base_url = ha_config['url'].rstrip('/')
        self.token = ha_config['token']
        self.timeout = ha_config.get('timeout', 10)
        self.logger = get_logger()

    def _get_headers(self):
        """
        Get HTTP headers for API requests.

        Returns:
            dict: HTTP headers with authorization
        """
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

    def _retry_request(self, method, url, **kwargs):
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method ('get', 'post', etc.)
            url: Request URL
            **kwargs: Additional request parameters

        Returns:
            requests.Response: HTTP response

        Raises:
            Exception: If all retries fail
        """
        max_retries = 3
        backoff_factor = 2

        for attempt in range(max_retries):
            try:
                response = requests.request(method, url, timeout=self.timeout, **kwargs)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    self.logger.warning(
                        f"Request failed (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Request failed after {max_retries} attempts: {e}")
                    raise

    def get_calendar_events(self, entity_id, start_date, end_date):
        """
        Fetch calendar events for a date range.

        Args:
            entity_id: Calendar entity ID (e.g., 'calendar.family')
            start_date: Start date/datetime
            end_date: End date/datetime

        Returns:
            list: List of calendar events

        Raises:
            Exception: If API request fails
        """
        url = f"{self.base_url}/api/calendars/{entity_id}"
        params = {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        }

        self.logger.debug(f"Fetching events for {entity_id} from {start_date} to {end_date}")

        try:
            response = self._retry_request('get', url, headers=self._get_headers(), params=params)
            events = response.json()
            self.logger.info(f"Fetched {len(events)} events from {entity_id}")
            return events
        except Exception as e:
            self.logger.error(f"Failed to fetch events from {entity_id}: {e}")
            return []

    def get_state(self, entity_id):
        """
        Get the current state of an entity.

        Args:
            entity_id: Entity ID (e.g., 'weather.forecast_home')

        Returns:
            dict: Entity state data

        Raises:
            Exception: If API request fails
        """
        url = f"{self.base_url}/api/states/{entity_id}"

        self.logger.debug(f"Fetching state for {entity_id}")

        try:
            response = self._retry_request('get', url, headers=self._get_headers())
            state_data = response.json()
            self.logger.debug(f"Fetched state for {entity_id}: {state_data.get('state')}")
            return state_data
        except Exception as e:
            self.logger.error(f"Failed to fetch state for {entity_id}: {e}")
            raise

    def get_weather(self):
        """
        Fetch weather forecast data.

        Returns:
            dict: Weather data or None if unavailable
        """
        try:
            weather_entity = self.config['weather']['entity_id']
            weather_data = self.get_state(weather_entity)
            self.logger.info(f"Fetched weather: {weather_data.get('state')}")
            return weather_data
        except Exception as e:
            self.logger.warning(f"Failed to fetch weather data: {e}")
            return None

    def get_current_view(self):
        """
        Get the current view from input_select or use default.

        Returns:
            str: View name ('two_week', 'month', 'week', 'agenda')
        """
        try:
            view_entity = self.config['view_selector']['entity_id']
            state_data = self.get_state(view_entity)
            view = state_data.get('state', '').lower().replace(' ', '_').replace('-', '_')

            # Validate view name
            valid_views = ['two_week', 'month', 'week', 'agenda']
            if view in valid_views:
                self.logger.info(f"Current view: {view}")
                return view
            else:
                self.logger.warning(f"Invalid view '{view}', using default")
                return self.config['view_selector']['default_view']
        except Exception as e:
            self.logger.warning(f"Failed to get view selector, using default: {e}")
            return self.config['view_selector']['default_view']

    def get_all_calendar_events(self, start_date, end_date):
        """
        Fetch events from all configured calendars.

        Args:
            start_date: Start date/datetime
            end_date: End date/datetime

        Returns:
            dict: Dictionary mapping entity_id to list of events
        """
        all_events = {}

        for calendar in self.config['calendars']:
            entity_id = calendar['entity_id']
            events = self.get_calendar_events(entity_id, start_date, end_date)
            all_events[entity_id] = events

        return all_events
