"""Home Assistant API client for fetching calendar and weather data."""

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
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
            self.logger.info(f"Fetching weather entity: {weather_entity}")
            weather_data = self.get_state(weather_entity)
            
            # Log forecast data availability
            if weather_data:
                state = weather_data.get('state')
                attributes = weather_data.get('attributes', {})
                
                # Log all available attributes
                self.logger.info(f"Weather state: {state}")
                self.logger.debug(f"Weather attributes keys: {list(attributes.keys())}")
                
                # Log full attributes for debugging
                self.logger.debug(f"Full weather attributes: {attributes}")
                
                # Check for forecast in multiple possible locations
                forecast = attributes.get('forecast', [])
                if not forecast:
                    # Try alternative names
                    forecast = attributes.get('forecasts', [])
                if not forecast:
                    forecast = attributes.get('daily_forecast', [])
                if not forecast:
                    forecast = attributes.get('hourly_forecast', [])
                
                self.logger.info(f"Fetched weather: {state}, Forecast items: {len(forecast)}")
                
                # Log first few forecast items
                for i, f in enumerate(forecast[:5]):
                    if isinstance(f, dict):
                        date_key = f.get('date') or f.get('datetime') or f.get('date_attr')
                        condition = f.get('condition', 'N/A')
                        temp = f.get('temperature', 'N/A')
                        self.logger.debug(f"  Forecast {i}: {date_key} -> {condition} ({temp}°)")
                    else:
                        self.logger.debug(f"  Forecast {i}: {f}")
            else:
                self.logger.warning("Weather data is None")
            
            return weather_data
        except Exception as e:
            self.logger.warning(f"Failed to fetch weather data: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return None

    def get_weather_forecast(self):
        """
        Fetch multi-day weather forecast using HA service.

        Returns:
            dict: Forecast service response or None if unavailable
        """
        try:
            weather_entity = self.config['weather']['entity_id']
            self.logger.info(f"Calling weather.get_forecasts service for: {weather_entity}")
            
            # Call weather.get_forecasts service with 'daily' type
            service_name = 'get_forecasts'
            url = f"{self.base_url}/api/services/weather/{service_name}?return_response"
            
            # Payload format for homeassistant.call_service
            payload = {
                "entity_id": weather_entity,
                "type": "daily"
            }
            
            self.logger.debug(f"  Request URL: {url}")
            self.logger.debug(f"  Payload: {payload}")
            
            response = self._retry_request('post', url, json=payload, headers=self._get_headers())
            result = response.json()
            
            self.logger.debug(f"Forecast service raw response type: {type(result).__name__}")
            if isinstance(result, dict):
                self.logger.debug(f"  Response keys: {list(result.keys())}")
            
            self.logger.debug(f"Full response: {result}")
            
            # Extract the forecast data from the response structure
            forecast_response = result
            
            # Check if wrapped in 'service_response'
            if isinstance(result, dict) and 'service_response' in result:
                forecast_response = result.get('service_response', {})
                self.logger.debug(f"Extracted from 'service_response' wrapper")
            elif isinstance(result, dict) and result.get('result'):
                forecast_response = result.get('result', {})
                self.logger.debug(f"Extracted from 'result' wrapper")
            
            # Log forecast data if available
            if isinstance(forecast_response, dict):
                for entity_id, entity_data in forecast_response.items():
                    self.logger.debug(f"Entity: {entity_id}")
                    
                    if isinstance(entity_data, dict):
                        # Check if forecast is under 'forecast' key
                        forecasts = entity_data.get('forecast', [])
                        if forecasts:
                            self.logger.debug(f"  Found {len(forecasts)} forecast items in 'forecast' key")
                        else:
                            self.logger.debug(f"  Entity data keys: {list(entity_data.keys())}")
                    elif isinstance(entity_data, list):
                        forecasts = entity_data
                        self.logger.debug(f"  Found {len(forecasts)} forecast items (direct array)")
                    else:
                        self.logger.debug(f"  Unknown data type: {type(entity_data).__name__}")
                        continue
                    
                    # Log first 3 forecasts with all details
                    if forecasts:
                        for i, f in enumerate(forecasts[:3]):
                            if isinstance(f, dict):
                                date_key = f.get('datetime', 'N/A')
                                condition = f.get('condition', 'N/A')
                                temp = f.get('temperature', 'N/A')
                                templow = f.get('templow', 'N/A')
                                wind = f.get('wind_speed', 'N/A')
                                humidity = f.get('humidity', 'N/A')
                                self.logger.debug(f"    [{i}] {date_key}")
                                self.logger.debug(f"        Condition: {condition}, Temp: {temp}°/{templow}°")
                                self.logger.debug(f"        Wind: {wind}, Humidity: {humidity}%")
            
            return forecast_response if forecast_response else None
                
        except requests.exceptions.HTTPError as e:
            # Forecast service returned an HTTP error
            self.logger.warning(f"Weather forecast service HTTP error {e.response.status_code}")
            try:
                error_detail = e.response.text
                self.logger.debug(f"  Error response: {error_detail}")
            except:
                pass
            return None
        except Exception as e:
            # Forecast service failed
            self.logger.warning(f"Weather forecast service failed: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
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
