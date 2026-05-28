# HA-Calendar E-Ink Display

A Python-based calendar display system for Waveshare e-Paper displays, powered by Home Assistant. Display your family calendar, sports schedules, and more on a beautiful 6-color e-ink screen.

## Features

- **Multiple View Modes**: Two-week grid, month, single week, and agenda views
- **Color-Coded Calendars**: Differentiate calendars with distinct colors - supports 50+ color names!
- **Weather Integration**: Display current weather conditions in the header
- **AI Weather Summary**: Show an AI-generated 2-3 line weather summary in the agenda view right panel (via Home Assistant LLM automation)
- **Dynamic View Switching**: Change views via Home Assistant input_select entity
- **Low Power**: E-ink displays retain image without power
- **Automatic Updates**: Refreshes hourly via cron job

## Hardware Requirements

- Raspberry Pi Zero W (or any Raspberry Pi model)
- Waveshare 7.3inch e-Paper HAT (E) - 800x480, 6-color display
- Home Assistant instance (accessible on your network)

## Supported Home Assistant Entities

- **Calendars**: Any calendar entities (e.g., `calendar.family`, `calendar.work`)
- **Weather**: Weather forecast entity (e.g., `weather.forecast_home`)
- **View Selector**: `input_select` entity with options: `two_week`, `month`, `week`, `agenda`

## Installation

### 1. Clone or Download

Clone this repository to your Raspberry Pi:

```bash
cd ~
git clone https://github.com/KennyNeal/HA-Calendar.git
cd HA-Calendar
```

Or download and extract the files manually.

**Recommended**: Use Git for easy updates and branch switching. See [docs/GIT_SETUP.md](docs/GIT_SETUP.md) for details.

### 2. Run Installation Script

```bash
chmod +x install.sh
./install.sh
```

The install script will:
- Install system dependencies
- Enable SPI interface for e-paper display
- Create Python virtual environment
- Install Python packages
- Download Waveshare e-Paper library
- Create configuration file

**Note**: You may need to reboot after installation if SPI was newly enabled.

### 3. Configure Home Assistant

#### Create Input Select for View Switching

Add to your `configuration.yaml`:

```yaml
input_select:
  calendar_view:
    name: Calendar Display View
    options:
      - two_week
      - month
      - week
      - agenda
    initial: two_week
    icon: mdi:calendar
```

Reload configuration or restart Home Assistant.

#### Generate Long-Lived Access Token

1. Go to your Home Assistant profile (click your username)
2. Scroll to "Long-Lived Access Tokens"
3. Click "Create Token"
4. Give it a name (e.g., "E-Ink Calendar")
5. Copy the token

### 4. Configure HA-Calendar

Edit the configuration file:

```bash
nano config/config.yaml
```

Update these fields:

```yaml
home_assistant:
  url: "http://your-homeassistant:8123"  # Your HA URL
  token: "YOUR_LONG_LIVED_ACCESS_TOKEN"  # Token from step 3

calendars:
  - entity_id: "calendar.family"  # Your calendar entity IDs
    display_name: "Family"
    color: "red"
  - entity_id: "calendar.prairieville_high_school_football"
    display_name: "Football"
    color: "yellow"

weather:
  entity_id: "weather.forecast_home"  # Your weather entity

view_selector:
  entity_id: "input_select.calendar_view"
```

### 5. Test the Display

#### Test in Mock Mode (saves PNG file):

```bash
python3 src/main.py
```

This will create `calendar_display.png` which you can view to test the rendering.

#### Test with Actual Hardware:

Edit `config/config.yaml` and set:

```yaml
display:
  mock_mode: false
```

Then run:

```bash
python3 src/main.py
```

The display should update on your e-paper screen.

### 6. Set Up Automatic Updates

Add a cron job to update the display every hour:

```bash
crontab -e
```

Add this line (adjust path if needed):

```
0 * * * * cd /home/pi/HA-Calendar && /home/pi/HA-Calendar/venv/bin/python3 src/main.py >> logs/cron.log 2>&1
```

This will update the display every hour at the top of the hour.

### 7. Keep Up to Date

Pull the latest changes at any time:

```bash
cd ~/HA-Calendar
git pull
python3 src/main.py  # Test the changes
```

Your `config/config.yaml` is in `.gitignore` and will never be overwritten by updates.

For full Git instructions (branches, stashing, troubleshooting), see **[docs/GIT_SETUP.md](docs/GIT_SETUP.md)**.

## View Modes

### Two-Week Grid (Default)
- Shows current week and next week in a 2x7 grid
- Displays up to 3 events per day
- Shows event start times and titles
- Current date has bold outline

### Month View
- Traditional month calendar layout
- Shows entire month with previous/next month days
- Color-coded event indicators (dots)
- Displays up to 2 events per day

### Week View
- Single week with larger cells
- Shows up to 5 events per day
- More detail per event
- Current day highlighted

### Agenda View
- Chronological list of upcoming events
- Shows full event details including calendar name
- Groups events by day
- Great for seeing detailed schedule

## Color Assignments

The Waveshare 7.3" HAT (E) supports 6 hardware colors:

- **Black**: Text, borders, grid lines
- **White**: Background
- **Red**: Calendar events
- **Yellow**: Calendar events
- **Green**: Calendar events
- **Blue**: Calendar events

### Extended Color Palette with Dithering

**NEW!** You can now specify **any common color name** in your configuration (e.g., `purple`, `orange`, `teal`, `pink`), and the system uses **Floyd-Steinberg dithering** to approximate the color using patterns of the 6 available e-paper inks.

**How it works:** Intermediate colors are created by arranging pixels of the base colors in patterns that your eye blends together - purple appears as a mix of red+blue pixels, orange as red+yellow, etc. This is the same technique used in color printing!

**Selective dithering:** The system preserves all 6 native e-paper colors (black, white, red, yellow, green, blue) perfectly sharp while only dithering intermediate colors (purple, orange, teal, etc.). This means text and borders in any native color stay crisp while calendar events can still display vibrant dithered colors.

Light colors like **yellow automatically get black borders** for improved contrast and visibility on the e-paper display.

For example:
```yaml
calendars:
  - entity_id: "calendar.family"
    color: "purple"    # → dithered mix of red + blue pixels
  - entity_id: "calendar.work"
    color: "orange"    # → dithered mix of red + yellow (with black border)
  - entity_id: "calendar.gym"
    color: "teal"      # → dithered mix of green + blue pixels
```

Over 50 color names are supported. See [docs/EXTENDED_COLORS.md](docs/EXTENDED_COLORS.md) for the full list and dithering details.

## Configuration Options

### Display Settings

```yaml
display:
  width: 800
  height: 480
  mock_mode: false  # Set to true for development without hardware
  rotation: 0  # Rotate display: 0, 90, 180, 270
```

### View-Specific Settings

```yaml
views:
  two_week:
    show_time: true  # Show event start times
    max_events_per_day: 3  # Limit events shown
  month:
    show_time: false
    max_events_per_day: 2
  week:
    show_time: true
    max_events_per_day: 5
  agenda:
    days_ahead: 14  # Number of days to show
    show_all_events: true
```

### Logging

```yaml
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  file: "logs/calendar.log"
  max_bytes: 1048576  # 1MB
  backup_count: 3
```

### AI Weather Summary (Agenda View)

The agenda view's right panel can display a 2-3 line AI-generated weather summary below the current conditions. The summary is generated by a Home Assistant automation that calls your configured AI conversation agent and stores the result in an `input_text` helper.

Enable it in `config/config.yaml`:

```yaml
weather_summary_sensor:
  entity_id: "input_text.weather_summary"
```

See **[docs/ha-weather-summary.yaml](docs/ha-weather-summary.yaml)** for the complete HA `input_text` helper and automation configuration.

## Troubleshooting

### Display not updating

1. Check logs: `tail -f logs/calendar.log`
2. Verify Home Assistant connection: Check URL and token
3. Ensure SPI is enabled: `ls /dev/spi*` should show devices
4. Test in mock mode to isolate hardware issues

### Events not showing

1. Verify calendar entity IDs in Home Assistant
2. Check date range - events outside the range won't show
3. Enable DEBUG logging in config to see API responses

### Weather not displaying

- Ensure weather entity exists and is accessible
- Weather failures are non-fatal; calendar will still display

### E-Paper display issues

- Ensure Waveshare library is installed: `ls waveshare_epd/`
- Check physical connections to Raspberry Pi
- Verify model compatibility (this code is for 7.3" HAT E)

### Permission errors

- Ensure user is in `gpio` and `spi` groups:
  ```bash
  sudo usermod -a -G gpio,spi $USER
  ```
- Log out and back in for group changes to take effect

## Adding More Calendars

Edit `config/config.yaml` and add calendar entities:

```yaml
calendars:
  - entity_id: "calendar.family"
    display_name: "Family"
    color: "purple"     # or red, orange, pink, etc.
  - entity_id: "calendar.work"
    display_name: "Work"
    color: "teal"       # or green, cyan, lime, etc.
  - entity_id: "calendar.holidays"
    display_name: "Holidays"
    color: "navy"       # or blue, indigo, etc.
```

You can use any common color name - see [docs/EXTENDED_COLORS.md](docs/EXTENDED_COLORS.md) for the full list. The display supports 4 distinct chromatic colors (red, yellow, green, blue), and additional calendars will cycle through them.

## Development

### Running in Mock Mode

For development on machines without the e-paper hardware:

1. Set `mock_mode: true` in `config/config.yaml`
2. Run `python3 src/main.py`
3. View the generated `calendar_display.png`

### Windows Local Setup (Mock Mode)

On Windows, the Pi-only packages (`spidev`, `RPi.GPIO`) will not install. Use a local venv and install only the cross-platform dependencies:

```powershell
cd C:\Users\<you>\HA-Calendar
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install requests PyYAML python-dateutil pytz pillow
```

Then set `mock_mode: true` and run `python src/main.py`.

### Project Structure

```
HA-Calendar/
├── config/
│   ├── config.example.yaml   # Template – copy to config.yaml and edit
│   └── config.yaml           # Your config (gitignored)
├── docs/                     # Reference documentation
│   ├── GIT_SETUP.md
│   ├── EXTENDED_COLORS.md
│   ├── WEATHER_ICONS_SETUP.md
│   ├── FONT_RECOMMENDATIONS.md
│   └── ha-weather-summary.yaml  # HA automation example for AI weather summary
├── src/
│   ├── main.py               # Entry point
│   ├── ha_client.py          # Home Assistant API client
│   ├── calendar_data.py      # Calendar event processing
│   ├── weather_data.py       # Weather data processing
│   ├── show_pic.py           # Easter-egg picture display
│   ├── webhook_server.py     # HTTP webhook server
│   ├── renderer/             # View renderers (two_week, month, week, agenda, four_day)
│   ├── display/              # E-paper display driver
│   └── utils/                # Logger, color manager, state manager
├── tests/                    # Development test scripts
├── waveshare_epd/            # Waveshare e-Paper library
└── logs/                     # Runtime logs (gitignored)
```

## Dependencies

- Python 3.7+
- requests
- PyYAML
- Pillow
- python-dateutil
- pytz
- RPi.GPIO *(Raspberry Pi only)*
- spidev *(Raspberry Pi only)*
- Waveshare e-Paper library *(included in `waveshare_epd/`)*

## License

This project is provided as-is for personal use.

## Credits

- Waveshare for the e-Paper library
- Home Assistant community

## Support

For issues and questions:
1. Check logs: `tail -f logs/calendar.log`
2. Review this README and the docs in `docs/`
3. Test in mock mode to isolate issues
