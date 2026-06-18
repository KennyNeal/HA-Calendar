"""Main entry point for HA-Calendar e-ink display."""

import sys
import os
import time
import yaml
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path

try:
    import fcntl
except ImportError:
    fcntl = None

sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import setup_logger, get_logger
from utils.color_manager import ColorManager
from utils.state_manager import save_state
from ha_client import HomeAssistantClient
from calendar_data import CalendarDataProcessor
from weather_data import WeatherDataProcessor
from display.epaper_driver import EPaperDisplay
from renderer.two_week_renderer import TwoWeekRenderer

RETRY_INTERVAL = 300  # seconds between connectivity retries when HA is unreachable
MAX_RETRIES = 12      # give up after 1 hour (12 × 5 min)


def load_config():
    config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
    if not config_path.exists():
        print(f"ERROR: Configuration file not found: {config_path}")
        print("Please copy config/config.example.yaml to config/config.yaml and configure it.")
        sys.exit(1)
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"ERROR: Failed to load configuration: {e}")
        sys.exit(1)


def select_renderer(view_name, config, color_manager):
    logger = get_logger()
    if view_name == 'two_week':
        return TwoWeekRenderer(config, color_manager)
    renderer_map = {
        'four_day': ('renderer.four_day_renderer', 'FourDayRenderer'),
        'month':    ('renderer.month_renderer',    'MonthRenderer'),
        'week':     ('renderer.week_renderer',     'WeekRenderer'),
        'agenda':   ('renderer.agenda_renderer',   'AgendaRenderer'),
    }
    if view_name not in renderer_map:
        logger.warning(f"Unknown view '{view_name}', using TwoWeekRenderer")
        return TwoWeekRenderer(config, color_manager)
    module_name, class_name = renderer_map[view_name]
    try:
        import importlib
        module = importlib.import_module(module_name)
        return getattr(module, class_name)(config, color_manager)
    except (ImportError, AttributeError):
        logger.warning(f"{class_name} not available, using TwoWeekRenderer")
        return TwoWeekRenderer(config, color_manager)


def _render_offline_screen(config):
    """Build a PIL image showing the network-unavailable message."""
    from PIL import Image, ImageDraw, ImageFont

    w = config['display']['width']
    h = config['display']['height']
    image = Image.new('RGB', (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    font_bold = font_normal = None
    for path in [
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        'C:/Windows/Fonts/arialbd.ttf',
    ]:
        if os.path.exists(path):
            try:
                font_bold = ImageFont.truetype(path, 36)
                font_normal = ImageFont.truetype(path, 20)
            except Exception:
                pass
            break
    if not font_bold:
        font_bold = font_normal = ImageFont.load_default()

    now_str = datetime.now().strftime("%I:%M %p  •  %b %d, %Y")
    lines = [
        ("Network Unavailable", font_bold, (0, 0, 0)),
        (now_str, font_normal, (100, 100, 100)),
        (f"Retrying every {RETRY_INTERVAL // 60} minutes", font_normal, (100, 100, 100)),
    ]

    line_gap = 14
    line_heights = [draw.textbbox((0, 0), t, font=f)[3] - draw.textbbox((0, 0), t, font=f)[1]
                    for t, f, _ in lines]
    total_h = sum(line_heights) + line_gap * len(lines)
    y = max(0, (h - total_h) // 2)

    for (text, font, color), lh in zip(lines, line_heights):
        bbox = draw.textbbox((0, 0), text, font=font)
        x = max(0, (w - (bbox[2] - bbox[0])) // 2)
        draw.text((x, y), text, font=font, fill=color)
        y += lh + line_gap

    return image


def main():
    """Run one display update cycle. Returns False if HA was unreachable."""
    start_time = datetime.now()
    config = load_config()
    logger = setup_logger(config)
    logger.info("=" * 60)
    logger.info("HA-Calendar Display Update Starting")
    logger.info("=" * 60)

    display = None
    try:
        color_manager = ColorManager(config)
        color_manager.assign_calendar_colors(config['calendars'])
        ha_client = HomeAssistantClient(config)
        calendar_processor = CalendarDataProcessor(color_manager)
        weather_processor = WeatherDataProcessor()

        if not ha_client.is_reachable():
            logger.warning("Home Assistant unreachable — showing offline screen")
            display = EPaperDisplay(config)
            display.init_display()
            display.display_image(_render_offline_screen(config))
            display.sleep()
            logger.info("=" * 60)
            return False

        display = EPaperDisplay(config)

        footer_sensor_text = None
        sensor_entity_id = None
        sensor_label = 'Sensor'
        override_entity_id = 'input_select.outdoor_scene_override'
        footer_sensor_config = config.get('footer_sensor')
        if footer_sensor_config:
            sensor_entity_id = footer_sensor_config.get('entity_id')
            sensor_label = footer_sensor_config.get('label', 'Sensor')

        weather_summary_entity_id = None
        weather_summary_config = config.get('weather_summary_sensor')
        if weather_summary_config:
            weather_summary_entity_id = weather_summary_config.get('entity_id')

        logger.info("Fetching data from Home Assistant...")
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {
                'view':     executor.submit(ha_client.get_current_view),
                'weather':  executor.submit(ha_client.get_weather),
                'forecast': executor.submit(ha_client.get_weather_forecast),
            }
            if sensor_entity_id:
                futures['footer'] = executor.submit(ha_client.get_state, sensor_entity_id)
                if sensor_entity_id == 'sensor.outdoor_scene':
                    futures['override'] = executor.submit(ha_client.get_state, override_entity_id)
            if weather_summary_entity_id:
                futures['weather_summary'] = executor.submit(ha_client.get_state, weather_summary_entity_id)

            current_view = futures['view'].result()
            logger.info(f"Current view: {current_view}")

            weather_data = futures['weather'].result()
            forecast_data = futures['forecast'].result()
            weather_info = weather_processor.parse_weather(weather_data, forecast_data)

            sensor_value = None
            if 'footer' in futures:
                try:
                    sensor_data = futures['footer'].result()
                    sensor_value = sensor_data.get('state', 'Unknown')
                except Exception as e:
                    logger.warning(f"Failed to fetch footer sensor {sensor_entity_id}: {e}")

            override_active = False
            if 'override' in futures:
                try:
                    override_data = futures['override'].result()
                    override_state = str(override_data.get('state', '')).strip().lower()
                    override_active = override_state not in {'', 'auto', 'none', 'off', 'unknown', 'unavailable'}
                except Exception as e:
                    logger.warning(f"Failed to fetch outdoor scene override: {e}")

            if sensor_value is not None:
                display_value = sensor_value
                if sensor_entity_id == 'sensor.outdoor_scene' and override_active:
                    display_value = f"{sensor_value} (Overridden)"
                footer_sensor_text = f"{sensor_label}: {display_value}"

            weather_summary = None
            if 'weather_summary' in futures:
                try:
                    summary_data = futures['weather_summary'].result()
                    raw = summary_data.get('state', '')
                    if raw and raw.lower() not in {'unknown', 'unavailable', ''}:
                        weather_summary = raw
                except Exception as e:
                    logger.warning(f"Failed to fetch weather summary: {e}")

        today = datetime.now().date()
        if current_view == 'month':
            start_date = datetime(today.year, today.month, 1)
            end_date = (
                datetime(today.year + 1, 1, 1) if today.month == 12
                else datetime(today.year, today.month + 1, 1)
            )
        else:
            start_date = datetime.combine(today, datetime.min.time())
            end_date = start_date + timedelta(days=14)

        logger.info(f"Fetching calendar events {start_date.date()} to {end_date.date()}...")
        all_events = ha_client.get_all_calendar_events(start_date, end_date)
        parsed_events = calendar_processor.parse_all_events(all_events)

        if current_view == 'two_week':
            max_per_day = config['views']['two_week'].get('max_events_per_day', 3)
            events_by_day = calendar_processor.get_events_for_range(parsed_events, days_ahead=14, max_per_day=max_per_day)
        elif current_view == 'week':
            max_per_day = config['views']['week'].get('max_events_per_day', 5)
            events_by_day = calendar_processor.get_events_for_range(parsed_events, days_ahead=7, max_per_day=max_per_day)
        elif current_view == 'month':
            max_per_day = config['views']['month'].get('max_events_per_day', 2)
            events_by_day = calendar_processor.get_events_for_month(parsed_events, today.year, today.month)
            events_by_day = calendar_processor.limit_events_per_day(events_by_day, max_per_day)
        elif current_view == 'agenda':
            days_ahead = config['views']['agenda'].get('days_ahead', 14)
            events_by_day = calendar_processor.get_events_for_range(parsed_events, days_ahead=days_ahead, max_per_day=None)
        else:
            events_by_day = calendar_processor.get_events_for_range(parsed_events, days_ahead=14)

        logger.info(f"Rendering {current_view} view...")
        renderer = select_renderer(current_view, config, color_manager)
        image = renderer.render(events_by_day, weather_info, footer_sensor_text, weather_summary=weather_summary)

        logger.info("Updating display...")
        display.init_display()
        display.display_image(image)
        display.sleep()

        save_state(last_updated=datetime.now().isoformat(), current_view=current_view)

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Update completed in {elapsed:.2f}s")
        logger.info("=" * 60)
        return True

    except KeyboardInterrupt:
        logger.info("Update interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error during update: {e}", exc_info=True)
        try:
            from PIL import Image, ImageDraw, ImageFont
            w = config['display']['width']
            h = config['display']['height']
            err_img = Image.new('RGB', (w, h), (255, 255, 255))
            draw = ImageDraw.Draw(err_img)
            font = ImageFont.load_default()
            draw.text((20, 20), f"ERROR: {str(e)[:120]}", font=font, fill=(0, 0, 0))
            draw.text((20, 40), "Check logs for details.", font=font, fill=(0, 0, 0))
            if display is None:
                display = EPaperDisplay(config)
            display.init_display()
            display.display_image(err_img)
            display.sleep()
        except Exception:
            pass
        sys.exit(1)


def _acquire_lock(lock_file):
    lock_fd = open(lock_file, 'a+')
    try:
        if fcntl:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        elif os.name == 'nt':
            import msvcrt
            lock_fd.write('1')
            lock_fd.flush()
            msvcrt.locking(lock_fd.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        lock_fd.close()
        raise
    return lock_fd


def _release_lock(lock_fd):
    try:
        if fcntl:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        elif os.name == 'nt':
            import msvcrt
            msvcrt.locking(lock_fd.fileno(), msvcrt.LK_UNLCK, 1)
    except Exception:
        pass
    finally:
        lock_fd.close()


if __name__ == '__main__':
    lock_file = os.path.join(tempfile.gettempdir(), 'ha-calendar.lock')
    retries = 0

    while retries <= MAX_RETRIES:
        try:
            lock_fd = _acquire_lock(lock_file)
        except OSError:
            print("Another calendar update is already running. Exiting.")
            sys.exit(0)

        try:
            result = main()
        finally:
            _release_lock(lock_fd)

        if result is not False:
            break  # Success or fatal error (sys.exit already called)

        retries += 1
        if retries > MAX_RETRIES:
            get_logger().error(f"HA unreachable after {MAX_RETRIES} retries. Giving up.")
            break
        get_logger().info(f"Retrying in {RETRY_INTERVAL // 60} minutes (attempt {retries}/{MAX_RETRIES})...")
        time.sleep(RETRY_INTERVAL)
