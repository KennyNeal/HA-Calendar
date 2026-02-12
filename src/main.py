"""Main entry point for HA-Calendar e-ink display."""

import sys
import os
import yaml
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import setup_logger, get_logger
from utils.color_manager import ColorManager
from ha_client import HomeAssistantClient
from calendar_data import CalendarDataProcessor
from weather_data import WeatherDataProcessor
from display.epaper_driver import EPaperDisplay
from renderer.two_week_renderer import TwoWeekRenderer


def load_config():
    """
    Load configuration from YAML file.

    Returns:
        dict: Configuration dictionary

    Raises:
        SystemExit: If config file not found or invalid
    """
    config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'

    if not config_path.exists():
        print(f"ERROR: Configuration file not found: {config_path}")
        print("Please copy config/config.example.yaml to config/config.yaml and configure it.")
        sys.exit(1)

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"ERROR: Failed to load configuration: {e}")
        sys.exit(1)


def select_renderer(view_name, config, color_manager):
    """
    Select appropriate renderer based on view name.

    Args:
        view_name: View name ('two_week', 'month', 'week', 'agenda')
        config: Configuration dictionary
        color_manager: ColorManager instance

    Returns:
        BaseRenderer: Selected renderer instance
    """
    logger = get_logger()

    # Import renderers as needed
    if view_name == 'two_week':
        return TwoWeekRenderer(config, color_manager)
    elif view_name == 'four_day':
        try:
            from renderer.four_day_renderer import FourDayRenderer
            return FourDayRenderer(config, color_manager)
        except ImportError:
            logger.warning("FourDayRenderer not available, using TwoWeekRenderer")
            return TwoWeekRenderer(config, color_manager)
    elif view_name == 'month':
        try:
            from renderer.month_renderer import MonthRenderer
            return MonthRenderer(config, color_manager)
        except ImportError:
            logger.warning("MonthRenderer not available, using TwoWeekRenderer")
            return TwoWeekRenderer(config, color_manager)
    elif view_name == 'week':
        try:
            from renderer.week_renderer import WeekRenderer
            return WeekRenderer(config, color_manager)
        except ImportError:
            logger.warning("WeekRenderer not available, using TwoWeekRenderer")
            return TwoWeekRenderer(config, color_manager)
    elif view_name == 'agenda':
        try:
            from renderer.agenda_renderer import AgendaRenderer
            return AgendaRenderer(config, color_manager)
        except ImportError:
            logger.warning("AgendaRenderer not available, using TwoWeekRenderer")
            return TwoWeekRenderer(config, color_manager)
    else:
        logger.warning(f"Unknown view '{view_name}', using TwoWeekRenderer")
        return TwoWeekRenderer(config, color_manager)


def main():
    """Main execution function."""
    start_time = datetime.now()

    # Load configuration
    config = load_config()

    # Setup logging
    logger = setup_logger(config)
    logger.info("="* 60)
    logger.info("HA-Calendar Display Update Starting")
    logger.info("="* 60)

    try:
        # Initialize components
        logger.info("Initializing components...")
        color_manager = ColorManager(config)
        color_manager.assign_calendar_colors(config['calendars'])

        ha_client = HomeAssistantClient(config)
        calendar_processor = CalendarDataProcessor(color_manager)
        weather_processor = WeatherDataProcessor()
        display = EPaperDisplay(config)

        # Get current view selection
        logger.info("Fetching current view selection...")
        current_view = ha_client.get_current_view()
        logger.info(f"Current view: {current_view}")

        # Fetch weather data
        logger.info("Fetching weather data...")
        weather_data = ha_client.get_weather()
        weather_info = weather_processor.parse_weather(weather_data)

        # Determine date range based on view
        today = datetime.now().date()
        if current_view == 'month':
            # For month view, get full month
            start_date = datetime(today.year, today.month, 1)
            if today.month == 12:
                end_date = datetime(today.year + 1, 1, 1)
            else:
                end_date = datetime(today.year, today.month + 1, 1)
        else:
            # For other views, get 14 days ahead
            start_date = datetime.combine(today, datetime.min.time())
            end_date = start_date + timedelta(days=14)

        # Fetch calendar events
        logger.info(f"Fetching calendar events from {start_date.date()} to {end_date.date()}...")
        all_events = ha_client.get_all_calendar_events(start_date, end_date)

        # Process calendar events
        logger.info("Processing calendar events...")
        parsed_events = calendar_processor.parse_all_events(all_events)

        # Group events by day
        if current_view == 'two_week':
            view_config = config['views']['two_week']
            max_per_day = view_config.get('max_events_per_day', 3)
            events_by_day = calendar_processor.get_events_for_range(
                parsed_events,
                days_ahead=14,
                max_per_day=max_per_day
            )
        elif current_view == 'week':
            view_config = config['views']['week']
            max_per_day = view_config.get('max_events_per_day', 5)
            events_by_day = calendar_processor.get_events_for_range(
                parsed_events,
                days_ahead=7,
                max_per_day=max_per_day
            )
        elif current_view == 'month':
            events_by_day = calendar_processor.get_events_for_month(
                parsed_events,
                today.year,
                today.month
            )
            view_config = config['views']['month']
            max_per_day = view_config.get('max_events_per_day', 2)
            events_by_day = calendar_processor.limit_events_per_day(events_by_day, max_per_day)
        elif current_view == 'agenda':
            view_config = config['views']['agenda']
            days_ahead = view_config.get('days_ahead', 14)
            events_by_day = calendar_processor.get_events_for_range(
                parsed_events,
                days_ahead=days_ahead,
                max_per_day=None  # Show all events in agenda view
            )
        else:
            # Default to two-week
            events_by_day = calendar_processor.get_events_for_range(parsed_events, days_ahead=14)

        # Select and create renderer
        logger.info(f"Creating {current_view} renderer...")
        renderer = select_renderer(current_view, config, color_manager)

        # Render calendar image
        logger.info("Rendering calendar image...")
        image = renderer.render(events_by_day, weather_info)

        # Initialize and update display
        logger.info("Initializing display...")
        display.init_display()

        logger.info("Updating display...")
        display.display_image(image)

        # Put display to sleep to save power
        display.sleep()

        # Log completion
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Display update completed successfully in {elapsed:.2f} seconds")
        logger.info("="* 60)

    except KeyboardInterrupt:
        logger.info("Update interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error during update: {e}", exc_info=True)

        # Try to show error on display
        try:
            from PIL import Image, ImageDraw, ImageFont
            error_image = Image.new('RGB', (800, 480), (255, 255, 255))
            draw = ImageDraw.Draw(error_image)
            font = ImageFont.load_default()

            error_text = f"ERROR: {str(e)}\n\nCheck logs for details."
            draw.text((20, 20), error_text, font=font, fill=(0, 0, 0))

            display = EPaperDisplay(config)
            display.init_display()
            display.display_image(error_image)
            display.sleep()
        except:
            pass  # If error display fails, just log

        logger.error("Update failed")
        logger.info("="* 60)
        sys.exit(1)


if __name__ == '__main__':
    main()
