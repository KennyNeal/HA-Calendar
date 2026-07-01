"""Home Assistant API client for fetching calendar and weather data."""

import socket
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from urllib.parse import urlparse
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
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

    def is_reachable(self):
        """Quick connectivity check via raw TCP connect to avoid DNS caching issues."""
        try:
            parsed = urlparse(self.base_url)
            host = parsed.hostname
            port = parsed.port or (443 if parsed.scheme == 'https' else 80)
            with socket.create_connection((host, port), timeout=5):
                return True
        except socket.gaierror as e:
            self.logger.debug(f"HA hostname not resolving ({host}): {e}")
            return False
        except OSError as e:
            self.logger.debug(f"HA TCP connection failed ({host}:{port}): {e}")
            return False

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
        """Fetch weather entity state. Returns dict or None if unavailable."""
        try:
            weather_entity = self.config['weather']['entity_id']
            weather_data = self.get_state(weather_entity)
            if weather_data:
                self.logger.info(f"Weather: {weather_data.get('state', 'unknown')}")
            else:
                self.logger.warning("Weather data unavailable")
            return weather_data
        except Exception as e:
            self.logger.warning(f"Failed to fetch weather: {e}")
            return None

    def get_weather_forecast(self):
        """Fetch multi-day forecast via HA weather.get_forecasts service. Returns dict or None."""
        try:
            weather_entity = self.config['weather']['entity_id']
            self.logger.info(f"Fetching weather forecast for: {weather_entity}")
            url = f"{self.base_url}/api/services/weather/get_forecasts?return_response"
            payload = {"entity_id": weather_entity, "type": "daily"}

            response = self._retry_request('post', url, json=payload, headers=self._get_headers())
            result = response.json()

            # Unwrap service_response or result envelope if present
            if isinstance(result, dict):
                if 'service_response' in result:
                    result = result['service_response']
                elif result.get('result'):
                    result = result['result']

            self.logger.info(f"Fetched weather forecast: {len(result) if result else 0} entities")
            return result if result else None

        except requests.exceptions.HTTPError as e:
            self.logger.warning(f"Weather forecast HTTP error {e.response.status_code}")
            return None
        except Exception as e:
            self.logger.warning(f"Weather forecast failed: {e}")
            return None

    def get_current_view(self):
        """
        Get the current view from input_select or use default.

        Returns:
            str: View name ('two_week', 'month', 'week', 'agenda')
        """
        override_view = self.config.get('view_selector', {}).get('override_view')
        if override_view:
            view = str(override_view).lower().replace(' ', '_').replace('-', '_')
            view_mappings = {
                '4_day': 'four_day',
                '2_week': 'two_week'
            }
            view = view_mappings.get(view, view)
            valid_views = ['two_week', 'four_day', 'month', 'week', 'agenda']
            if view in valid_views:
                self.logger.info(f"Using local override view: {view}")
                return view
            self.logger.warning(f"Invalid override view '{override_view}', ignoring")

        try:
            view_entity = self.config['view_selector']['entity_id']
            state_data = self.get_state(view_entity)
            view = state_data.get('state', '').lower().replace(' ', '_').replace('-', '_')

            # Map numeric view names to spelled-out versions
            view_mappings = {
                '4_day': 'four_day',
                '2_week': 'two_week'
            }
            view = view_mappings.get(view, view)

            # Validate view name
            valid_views = ['two_week', 'four_day', 'month', 'week', 'agenda']
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
        calendars = self.config.get('calendars', [])
        all_events = {}

        if not calendars:
            return all_events

        max_workers = min(8, len(calendars))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.get_calendar_events, cal['entity_id'], start_date, end_date): cal['entity_id']
                for cal in calendars
            }

            for future in as_completed(futures):
                entity_id = futures[future]
                try:
                    all_events[entity_id] = future.result()
                except Exception as e:
                    self.logger.error(f"Failed to fetch events from {entity_id}: {e}")
                    all_events[entity_id] = []

        return all_events
