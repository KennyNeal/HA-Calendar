"""Main entry point for HA-Calendar e-ink display."""

import sys
import os
import yaml
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

try:
    import fcntl
except ImportError:  # Windows
    fcntl = None

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import setup_logger, get_logger
from utils.color_manager import ColorManager
from utils.state_manager import save_state
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
        assigned_colors = color_manager.assign_calendar_colors(config['calendars'])

        # Debug: Log calendar color assignments
        logger.info("Calendar color assignments from config:")
        for calendar in config['calendars']:
            logger.info(f"  {calendar['entity_id']}: color={calendar.get('color', 'auto')}")
        logger.info("ColorManager assigned colors:")
        for entity_id, color_info in assigned_colors.items():
            logger.info(f"  {entity_id}: {color_info['name']} RGB{color_info['rgb']}")

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

        # Fetch optional footer sensor
        footer_sensor_text = None
        if 'footer_sensor' in config and config['footer_sensor']:
            footer_sensor_config = config['footer_sensor']
            sensor_entity_id = footer_sensor_config.get('entity_id')
            sensor_label = footer_sensor_config.get('label', 'Sensor')
            
            if sensor_entity_id:
                try:
                    logger.info(f"Fetching footer sensor: {sensor_entity_id}")
                    sensor_data = ha_client.get_state(sensor_entity_id)
                    sensor_value = sensor_data.get('state', 'Unknown')
                    footer_sensor_text = f"{sensor_label}: {sensor_value}"
                    logger.info(f"Footer sensor value: {footer_sensor_text}")
                except Exception as e:
                    logger.warning(f"Failed to fetch footer sensor {sensor_entity_id}: {e}")

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
        image = renderer.render(events_by_day, weather_info, footer_sensor_text)

        # Initialize and update display
        logger.info("Initializing display...")
        display.init_display()

        logger.info("Updating display...")
        display.display_image(image)

        # Put display to sleep to save power
        display.sleep()

        # Save state for health endpoint
        save_state(
            last_updated=datetime.now().isoformat(),
            current_view=current_view
        )

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
    # Use file locking to prevent concurrent display access
    lock_file = os.path.join(tempfile.gettempdir(), 'ha-calendar.lock')
    lock_fd = None

    try:
        # Try to acquire lock
        lock_fd = open(lock_file, 'a+')
        lock_fd.write('1')
        lock_fd.flush()

        if fcntl:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        elif os.name == 'nt':
            import msvcrt
            msvcrt.locking(lock_fd.fileno(), msvcrt.LK_NBLCK, 1)

        # Lock acquired, run main
        main()

    except OSError:
        # Could not acquire lock - another instance is running
        print("Another calendar update is already running. Exiting.")
        sys.exit(0)
    finally:
        # Release lock
        if lock_fd:
            try:
                if fcntl:
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
                elif os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(lock_fd.fileno(), msvcrt.LK_UNLCK, 1)
                lock_fd.close()
            except:
                pass
