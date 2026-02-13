"""Weather data processing from Home Assistant."""

from dataclasses import dataclass
from utils.logger import get_logger


@dataclass
class WeatherInfo:
    """Represents weather information for display."""
    condition: str
    temperature: float
    temperature_unit: str
    humidity: int
    wind_speed: float
    wind_speed_unit: str


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

    def parse_weather(self, weather_data):
        """
        Parse weather data from HA API response.

        Args:
            weather_data: Weather entity state data from API

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

            weather_info = WeatherInfo(
                condition=state.capitalize(),
                temperature=temperature if temperature is not None else 0,
                temperature_unit=temperature_unit,
                humidity=humidity,
                wind_speed=wind_speed,
                wind_speed_unit=wind_speed_unit
            )

            self.logger.info(
                f"Parsed weather: {weather_info.condition}, "
                f"{weather_info.temperature}{weather_info.temperature_unit}"
            )
            return weather_info

        except Exception as e:
            self.logger.error(f"Failed to parse weather data: {e}")
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
