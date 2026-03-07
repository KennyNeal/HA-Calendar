# Extended Color Palette Guide

The HA-Calendar now supports **any common color name** for calendar assignments! While the e-paper display hardware only supports 6 colors (black, white, red, yellow, green, blue), you can now specify colors like `purple`, `orange`, `teal`, `pink`, etc. in your configuration.

## How It Works

The system automatically maps your chosen color to the nearest available e-paper color using intelligent color matching. This is particularly useful for the **legend display**, making it easier to identify calendars with more intuitive color names.

## Supported Color Names

Over 50 common color names are supported, including:

### Reds & Pinks
- `red`, `pink`, `lightpink`, `hotpink`, `deeppink`, `crimson`, `darkred`, `maroon`
- `salmon`, `coral`, `tomato`

### Oranges & Browns  
- `orange`, `orangered`, `darkorange`, `brown`, `chocolate`, `sienna`, `tan`

### Yellows
- `yellow`, `gold`, `lightyellow`, `khaki`, `olive`

### Greens
- `green`, `lime`, `lightgreen`, `darkgreen`, `forestgreen`, `seagreen`, `mint`

### Blues & Cyans
- `blue`, `lightblue`, `skyblue`, `navy`, `darkblue`, `royalblue`, `steelblue`
- `cyan`, `aqua`, `turquoise`, `teal`

### Purples & Violets
- `purple`, `violet`, `magenta`, `fuchsia`, `orchid`, `plum`, `lavender`, `indigo`

### Grays
- `gray`, `grey`, `silver`, `darkgray`, `lightgray`, `dimgray`

## Color Mapping Examples

Here's how common colors map to the 6 available e-paper colors:

| Requested Color | Renders As |
|----------------|------------|
| `purple`       | **RED**    |
| `orange`       | **YELLOW** |
| `teal`         | **GREEN**  |
| `cyan`         | **GREEN**  |
| `magenta`      | **RED**    |
| `brown`        | **RED**    |
| `navy`         | **BLUE**   |
| `gold`         | **YELLOW** |
| `pink`         | **WHITE**  |
| `gray`         | **WHITE**  |

## Configuration Example

```yaml
calendars:
  - entity_id: "calendar.family"
    display_name: "Family"
    color: "purple"      # → renders as red
    
  - entity_id: "calendar.work"
    display_name: "Work"
    color: "orange"      # → renders as yellow
    
  - entity_id: "calendar.gym"
    display_name: "Gym"
    color: "teal"        # → renders as green
    
  - entity_id: "calendar.social"
    display_name: "Social"
    color: "magenta"     # → renders as red
```

## How the Mapping Works

The system uses **Euclidean distance in RGB color space** with a preference for chromatic (saturated) colors. This means:

1. Saturated colors (like `cyan`, `magenta`, `purple`) will map to the nearest chromatic color rather than white or black
2. Very light/pastel colors (like `pink`, `lavender`) may map to white since they are essentially white with a slight tint
3. Dark colors will map to the nearest saturated color or black

## Testing Your Colors

Run the test script to see which e-paper color any given color name will map to:

```bash
python test_colors.py
```

This will show you all supported colors and their mappings.

## Benefits for Legend Display

The main benefit of this feature is in the **legend** - instead of seeing:
- ⬤ Family (red)
- ⬤ Work (yellow)

You can think of your calendars with more intuitive names:
- ⬤ Family (purple)
- ⬤ Work (orange)

Even though they still render as red and yellow on the hardware, the conceptual color assignment in your configuration is more meaningful.

## Future Enhancements

To get true intermediate colors like purple or orange on the display, dithering could be enabled. This would use a pattern of pixels (e.g., red + blue pixels for purple) to create the illusion of more colors. However, this would make the display more "grainy" and is not currently implemented.
