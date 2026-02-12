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

    # Map HA weather conditions to simple text icons that render well
    WEATHER_ICONS = {
        'clear-night': '(*)',  # Moon and stars
        'cloudy': '===',       # Clouds
        'fog': '~~~',          # Fog
        'hail': '*#*',         # Hail
        'lightning': 'ZAP',    # Lightning
        'lightning-rainy': 'ZAP',
        'partlycloudy': '(=)',  # Partly cloudy
        'pouring': '|||',      # Heavy rain
        'rainy': '\\|/',       # Rain
        'snowy': '***',        # Snow
        'snowy-rainy': '*|*',  # Snow/rain mix
        'sunny': '(O)',        # Sun
        'windy': '~>',         # Wind
        'windy-variant': '~>',
        'exceptional': '!',
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
