"""Weather data processing from Home Assistant."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from utils.logger import get_logger


@dataclass
class DayForecast:
    """Represents weather forecast for a single day."""
    date: str  # ISO format date YYYY-MM-DD
    condition: str
    temperature: float
    wind_speed: float
    temperature_low: Optional[float] = None


@dataclass
class WeatherInfo:
    """Represents weather information for display."""
    condition: str
    temperature: float
    temperature_unit: str
    humidity: int
    wind_speed: float
    wind_speed_unit: str
    wind_bearing: Optional[float] = None
    forecast: dict = None  # Maps date string (YYYY-MM-DD) to DayForecast


class WeatherDataProcessor:
    """Processes weather data from Home Assistant."""

    # Map HA weather conditions to Weather Icons font Unicode characters
    # Weather Icons font: https://erikflowers.github.io/weather-icons/
    # Install font file: weathericons-regular-webfont.ttf
    WEATHER_ICONS = {
        'clear-night': '\uf02e',      # Night
        'cloudy': '\uf013',           # Cloud
        'fog': '\uf014',              # Fog
        'hail': '\uf015',             # Hail
        'lightning': '\uf016',        # Lightning
        'lightning-rainy': '\uf017',  # Lightning with rain
        'partlycloudy': '\uf002',     # Partly cloudy
        'pouring': '\uf018',          # Pouring rain
        'rainy': '\uf019',            # Rain
        'snowy': '\uf01b',            # Snow
        'snowy-rainy': '\uf01c',      # Rain and snow
        'sunny': '\uf00d',            # Sunny
        'windy': '\uf021',            # Windy
        'windy-variant': '\uf021',    # Windy variant
        'exceptional': '\uf03b',      # Tornado/exceptional
    }

    def __init__(self):
        """Initialize weather data processor."""
        self.logger = get_logger()

    def parse_weather(self, weather_data, forecast_service_data=None):
        """
        Parse weather data from HA API response.

        Args:
            weather_data: Weather entity state data from API
            forecast_service_data: Optional forecast data from weather.get_forecasts service

        Returns:
            WeatherInfo: Parsed weather object or None if unavailable
        """
        if not weather_data:
            self.logger.warning("No weather data available")
            return None

        try:
            state = weather_data.get('state', 'unknown')
            attributes = weather_data.get('attributes', {})

            # Extract weather information
            temperature = attributes.get('temperature')
            temperature_unit = attributes.get('temperature_unit', '°F')
            humidity = attributes.get('humidity', 0)
            wind_speed = attributes.get('wind_speed', 0)
            wind_speed_unit = attributes.get('wind_speed_unit', 'mph')
            wind_bearing = attributes.get('wind_bearing')
            if wind_bearing is None:
                wind_bearing = attributes.get('wind_direction')
            if isinstance(wind_bearing, str):
                cardinal_map = {
                    'N': 0.0,
                    'NE': 45.0,
                    'E': 90.0,
                    'SE': 135.0,
                    'S': 180.0,
                    'SW': 225.0,
                    'W': 270.0,
                    'NW': 315.0,
                }
                wind_bearing = cardinal_map.get(wind_bearing.strip().upper())
            try:
                wind_bearing = float(wind_bearing) if wind_bearing is not None else None
            except (TypeError, ValueError):
                wind_bearing = None

            # Extract and parse forecast data
            forecast_dict = {}
            
            # First try forecast service data (preferred - has multi-day forecasts)
            if forecast_service_data:
                self.logger.info(f"Processing forecast service data with {len(forecast_service_data)} entities")
                
                # Extract forecast from service response
                # forecast_service_data is dict with entity_id as key
                # Each entity has either:
                #   - 'forecast' key with array of forecasts
                #   - or directly an array of forecasts
                
                for entity_id, entity_data in forecast_service_data.items():
                    if 'weather' not in entity_id:
                        continue
                    
                    self.logger.debug(f"Processing {entity_id}")
                    forecasts_list = None
                    
                    # Check if entity_data is a dict with 'forecast' key
                    if isinstance(entity_data, dict) and 'forecast' in entity_data:
                        forecasts_list = entity_data.get('forecast', [])
                        self.logger.info(f"  Entity has forecast key with {len(forecasts_list)} items")
                    elif isinstance(entity_data, list):
                        # Forecast data is directly an array
                        forecasts_list = entity_data
                        self.logger.info(f"  Entity is direct array with {len(forecasts_list)} items")
                    
                    if forecasts_list:
                        for i, forecast_item in enumerate(forecasts_list):
                            if not isinstance(forecast_item, dict):
                                self.logger.warning(f"Forecast item {i} is not a dict: {type(forecast_item)}")
                                continue
                            
                            # Service returns datetime key
                            date_str = forecast_item.get('datetime', '')
                            if date_str:
                                # Extract just the date part (YYYY-MM-DD)
                                date_key = date_str.split('T')[0] if 'T' in date_str else date_str
                                
                                day_forecast = DayForecast(
                                    date=date_key,
                                    condition=forecast_item.get('condition', 'unknown'),
                                    temperature=forecast_item.get('temperature', 0),
                                    wind_speed=forecast_item.get('wind_speed', 0),
                                    temperature_low=forecast_item.get('templow')
                                )
                                forecast_dict[date_key] = day_forecast
                                if i < 5:
                                    self.logger.info(f"  Forecast {i}: {date_key} -> {day_forecast.condition} ({day_forecast.temperature}°)")
            
            # If no forecast from service, try entity attributes
            if not forecast_dict:
                self.logger.debug("No forecast from service, trying entity attributes")
                
                # Try multiple possible attribute names
                forecast_data = attributes.get('forecast', [])
                if not forecast_data:
                    forecast_data = attributes.get('forecasts', [])
                if not forecast_data:
                    forecast_data = attributes.get('daily_forecast', [])
                if not forecast_data:
                    forecast_data = attributes.get('hourly_forecast', [])
                
                self.logger.debug(f"Raw forecast data type: {type(forecast_data)}, length: {len(forecast_data) if forecast_data else 0}")
                
                if forecast_data:
                    for i, forecast_item in enumerate(forecast_data):
                        # Handle both date and datetime keys
                        date_str = forecast_item.get('date') or forecast_item.get('datetime')
                        if date_str:
                            # Extract just the date part (YYYY-MM-DD)
                            date_key = date_str.split('T')[0] if 'T' in str(date_str) else str(date_str)
                            
                            day_forecast = DayForecast(
                                date=date_key,
                                condition=forecast_item.get('condition', 'unknown'),
                                temperature=forecast_item.get('temperature', 0),
                                wind_speed=forecast_item.get('wind_speed', 0),
                                temperature_low=forecast_item.get('templow')
                            )
                            forecast_dict[date_key] = day_forecast
                            self.logger.debug(f"Forecast {i}: {date_key} -> {day_forecast.condition}")

            # Also add today's weather to forecast if not already there (fallback)
            today_key = datetime.now().date().isoformat()
            if today_key not in forecast_dict:
                today_forecast = DayForecast(
                    date=today_key,
                    condition=state,
                    temperature=temperature if temperature is not None else 0,
                    wind_speed=wind_speed
                )
                forecast_dict[today_key] = today_forecast
                self.logger.debug(f"Added today's weather as fallback: {today_key} -> {state}")

            weather_info = WeatherInfo(
                condition=state.capitalize(),
                temperature=temperature if temperature is not None else 0,
                temperature_unit=temperature_unit,
                humidity=humidity,
                wind_speed=wind_speed,
                wind_speed_unit=wind_speed_unit,
                wind_bearing=wind_bearing,
                forecast=forecast_dict if forecast_dict else None
            )

            self.logger.info(
                f"Parsed weather: {weather_info.condition}, "
                f"{weather_info.temperature}{weather_info.temperature_unit}, "
                f"Forecast days: {len(forecast_dict)}"
            )
            return weather_info

        except Exception as e:
            self.logger.error(f"Failed to parse weather data: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None

        except Exception as e:
            self.logger.error(f"Failed to parse weather data: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None

    def format_weather_text(self, weather_info):
        """
        Format weather information as display text.

        Args:
            weather_info: WeatherInfo object

        Returns:
            str: Formatted weather text
        """
        if not weather_info:
            return "Weather Unavailable"

        # Format temperature with degree symbol
        temp_str = f"{weather_info.temperature:.0f}{weather_info.temperature_unit}"

        # Combine condition and temperature
        return f"{weather_info.condition}, {temp_str}"

    def format_weather_detailed(self, weather_info):
        """
        Format detailed weather information for display.

        Args:
            weather_info: WeatherInfo object

        Returns:
            dict: Dictionary with formatted weather components
        """
        if not weather_info:
            return {
                'condition': 'N/A',
                'temperature': '---',
                'humidity': '---',
                'wind': '---'
            }

        return {
            'condition': weather_info.condition,
            'temperature': f"{weather_info.temperature:.0f}{weather_info.temperature_unit}",
            'humidity': f"{weather_info.humidity}%",
            'wind': f"{weather_info.wind_speed:.0f} {weather_info.wind_speed_unit}"
        }

    def get_weather_icon(self, condition):
        """
        Get Weather Icons font character for weather condition.

        Args:
            condition: Weather condition string (e.g., 'sunny', 'rainy')

        Returns:
            str: Unicode character from Weather Icons font
        """
        # Normalize condition to lowercase and match against known conditions
        condition_key = condition.lower() if condition else None
        return self.WEATHER_ICONS.get(condition_key, '\uf03b')  # Default to exceptional

    def get_weather_icon_with_color(self, condition):
        """
        Get Weather Icons font character with appropriate color for e-paper display.

        Args:
            condition: Weather condition string (e.g., 'sunny', 'rainy')

        Returns:
            tuple: (icon, color_name) - Weather icon character and e-paper color
        """
        # Map weather conditions to colors for e-paper display
        WEATHER_COLORS = {
            'sunny': 'gold',             # Bright sun - gold is more visible than yellow
            'clear-night': 'blue',       # Night
            'partlycloudy': 'gold',      # Sun behind cloud
            'cloudy': 'black',           # Gray cloud
            'rainy': 'blue',             # Rain
            'pouring': 'blue',           # Heavy rain
            'snowy': 'blue',             # Snow
            'snowy-rainy': 'blue',       # Mixed precipitation
            'lightning': 'gold',         # Lightning - bright gold
            'lightning-rainy': 'gold',   # Thunder with rain
            'hail': 'blue',              # Hail
            'windy': 'black',            # Wind
            'windy-variant': 'black',    # Wind variant
            'fog': 'black',              # Fog
            'exceptional': 'red',        # Warning/alert
        }
        
        condition_key = condition.lower() if condition else None
        icon = self.WEATHER_ICONS.get(condition_key, '\uf03b')
        color = WEATHER_COLORS.get(condition_key, 'black')
        
        return icon, color

    def format_weather_with_icon(self, weather_info):
        """
        Format weather with icon and temperature.

        Args:
            weather_info: WeatherInfo object

        Returns:
            str: Formatted string with weather icon and temperature
        """
        if not weather_info:
            return "N/A"

        icon = self.get_weather_icon(weather_info.condition.lower())
        temp_str = f"{weather_info.temperature:.0f}{weather_info.temperature_unit}"
        return f"{icon} {temp_str}"
