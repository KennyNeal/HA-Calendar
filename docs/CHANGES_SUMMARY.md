# Summary of Changes

## Features Implemented

### 1. Extended Color Palette (50+ Color Names)
- Added support for any common color name in calendar configuration
- Colors are automatically mapped to the nearest of 6 available e-paper colors
- Includes: purple, orange, teal, pink, brown, cyan, magenta, navy, gold, etc.

**How it works:**
- User specifies color name like `purple` or `orange` in config
- System maps to nearest hardware color using Euclidean distance in RGB space
- Original color name is preserved for reference

**Example color mappings:**
- `purple` → red
- `orange` → yellow
- `teal` → green
- `cyan` → green
- `magenta` → red
- `navy` → blue

### 2. Automatic Contrast Borders
- Light colors (yellow, white) automatically get black borders
- Ensures visibility on white e-paper background
- Uses ITU-R BT.709 luminance formula
- Threshold: luminance > 200 triggers border

**Where borders are applied:**
- Legend color indicators
- Event dots/squares in month view
- Event bars in week/two-week/four-day views
- All colored event indicators across all views

**Luminance values:**
- Yellow: 236.6 → **gets border**
- White: 255.0 → **gets border**
- Green: 182.4 → no border
- Red: 54.2 → no border
- Blue: 18.4 → no border

## Files Modified

### Core Color Management
- `src/utils/color_manager.py`:
  - Added `COMMON_COLORS` dictionary with 50+ color names
  - Updated `get_rgb()` to accept any color name and quantize to palette
  - Added `get_color_name_for_display()` to show which e-paper color is used
  - Modified `assign_calendar_colors()` to track both original and rendered color

### Rendering System
- `src/renderer/base_renderer.py`:
  - Added `is_light_color()` method using ITU-R BT.709 luminance
  - Updated `draw_calendar_legend()` to add borders for light colors
  - Updated multi-day event rendering with borders

- `src/renderer/agenda_renderer.py`:
  - Updated event indicators with automatic borders

- `src/renderer/month_renderer.py`:
  - Updated `_draw_event_indicators()` with automatic borders

- `src/renderer/week_renderer.py`:
  - Updated event bars with automatic borders

- `src/renderer/two_week_renderer.py`:
  - Updated event bars with automatic borders

- `src/renderer/four_day_renderer.py`:
  - Updated event bars with automatic borders

### Documentation
- `docs/EXTENDED_COLORS.md`: Complete guide to extended colors
- `README.md`: Updated with color feature info

### Test Files
- `test_colors.py`: Shows all color mappings
- `test_integration.py`: Verifies color assignment system
- `test_light_colors.py`: Demonstrates border logic

## Usage Example

In `config/config.yaml`:
```yaml
calendars:
  - entity_id: "calendar.family"
    display_name: "Family"
    color: "purple"      # → renders as red
    
  - entity_id: "calendar.work"
    display_name: "Work"
    color: "orange"      # → renders as yellow with black border
    
  - entity_id: "calendar.gym"
    display_name: "Gym"
    color: "teal"        # → renders as green
```

## Benefits

1. **More intuitive configuration** - Use color names that make sense conceptually
2. **Better visibility** - Yellow events now have black borders for contrast
3. **Maintains hardware limits** - Still only uses 6 e-paper colors
4. **Future-proof** - Easy to add dithering later for true mixed colors
5. **Zero configuration** - Borders are added automatically based on color science

## Testing

Run these tests to verify:
```bash
python test_colors.py          # See all color mappings
python test_integration.py     # Verify color assignment
python test_light_colors.py    # Test border logic
python src/main.py             # Generate full calendar
```

All tests pass successfully!
