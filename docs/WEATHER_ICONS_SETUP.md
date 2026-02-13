# Weather Icons Setup Guide

This guide explains how to install the Weather Icons font to display beautiful weather condition icons on your e-paper display.

## About Weather Icons

Weather Icons is a free, open-source icon font designed specifically for weather conditions. It includes dozens of weather-related icons that render perfectly on e-paper displays.

- **Project**: https://erikflowers.github.io/weather-icons/
- **License**: SIL Open Font License
- **Font File**: `weathericons-regular-webfont.ttf`

## Installation

### For Linux (Raspberry Pi - Recommended)

1. Download the Weather Icons font:
```bash
cd /usr/share/fonts/truetype
sudo mkdir -p weather-icons
cd weather-icons
sudo wget https://github.com/erikflowers/weather-icons/raw/master/font/weathericons-regular-webfont.ttf
```

2. Update font cache:
```bash
sudo fc-cache -f -v
```

3. Verify installation:
```bash
fc-list | grep -i weather
```

### For Windows

1. Download the font file from: https://github.com/erikflowers/weather-icons/releases
   - Look for `weathericons-regular-webfont.ttf` in the assets

2. Place the font in Windows Fonts directory:
   - Copy the `.ttf` file to `C:\Windows\Fonts\`
   - Or right-click the file and select "Install"

## Available Weather Icons

The system automatically maps Home Assistant weather conditions to Weather Icons:

| HA Condition | Icon | Unicode |
|-----------|------|---------|
| sunny | ☀ | \uf00d |
| clear-night | 🌙 | \uf02e |
| cloudy | ☁ | \uf013 |
| fog | 🌫 | \uf014 |
| rainy | 🌧 | \uf019 |
| pouring | ⛈ | \uf018 |
| snowy | ❄ | \uf01b |
| lightning | ⚡ | \uf016 |
| partlycloudy | ⛅ | \uf002 |

## Troubleshooting

### Icons not showing?
1. Verify the font file is in the correct location
2. Check the logs: `tail logs/*.log`
3. Look for "Weather Icons font not found" warning
4. Font cache may need refreshing (Linux): `sudo fc-cache -f -v`

### Icons show as squares or blank spaces?
- This typically means the font is not properly installed
- Try reinstalling and refreshing the font cache
- Verify the font file size is > 50KB (valid font file)

### Custom icon mappings
To add custom weather icons or modify mappings, edit:
```
src/weather_data.py
```

Look for the `WEATHER_ICONS` dictionary in the `WeatherDataProcessor` class and update Unicode values as needed. Consult the Weather Icons documentation for the full list of available icons.

## Font Resources

- **Full Icon List**: https://erikflowers.github.io/weather-icons/
- **GitHub Repository**: https://github.com/erikflowers/weather-icons
- **License**: https://opensource.org/licenses/OFL-1.1

## Alternative Icon Fonts

If Weather Icons doesn't work for your setup, consider these alternatives:

1. **FontAwesome** (free version): Has weather icons, widely supported
   - https://fontawesome.com/

2. **Material Design Icons**: Modern, clean icons
   - https://fonts.google.com/icons

3. **Noto Color Emoji**: For emoji weather symbols
   - https://fonts.google.com/?query=noto+emoji

## Integration Notes

The calendar system now:
- Automatically loads Weather Icons font when available
- Falls back to regular fonts if Weather Icons is not installed
- Displays weather with icon and temperature in the header
- Provides new methods for accessing weather icons in code:
  - `get_weather_icon(condition)` - Get icon for a condition
  - `format_weather_with_icon(weather_info)` - Get formatted icon + temperature
