# Extended Color Palette Guide

The HA-Calendar now supports **any common color name** for calendar assignments! The system uses **Floyd-Steinberg dithering** to approximate any color using patterns of the 6 available e-paper inks (black, white, red, yellow, green, blue).

**Smart text preservation:** Black and white text stays perfectly sharp while colored areas are dithered - giving you vibrant colors without sacrificing readability!

## How Dithering Works

**Dithering** creates the visual appearance of intermediate colors by arranging pixels of the available colors in patterns that your eye blends together:

- **Purple** = Pattern of red + blue pixels that looks purple from viewing distance
- **Orange** = Pattern of red + yellow pixels that looks orange
- **Teal** = Pattern of green + blue pixels that looks teal/cyan
- **Brown** = Pattern of red + yellow + black pixels that looks brown
- **Pink** = Pattern of red + white pixels that looks pink

This is the same technique used in old newspaper photos and color printers - you're not limited to just 6 solid colors anymore!

## Automatic Contrast Enhancement

Light colors (yellow and colors with high luminance) automatically get **black borders** for improved visibility on the e-paper display.

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
- `purple`, `indigo`, `blueviolet`, `darkviolet`, `mediumpurple`, `rebeccapurple` (map to **blue**)
- `violet`, `magenta`, `fuchsia`, `orchid`, `plum`, `lavender` (map to red/white)
- Special: `lsu` for official LSU purple

### Grays
- `gray`, `grey`, `silver`, `darkgray`, `lightgray`, `dimgray`

## Color Mapping Examples

With **dithering enabled**, colors are approximated using patterns of pixels:

| Requested Color | How It Appears |
|----------------|----------------|
| `purple`       | Mix of **red + blue** pixels (looks purple) |
| `indigo`       | Mix of **blue + black** pixels (looks deep purple/blue) |
| `orange`       | Mix of **red + yellow** pixels (looks orange) |
| `teal`         | Mix of **green + blue** pixels (looks teal) |
| `cyan`         | Mix of **green + blue + white** pixels (looks cyan) |
| `magenta`      | Mix of **red + blue** pixels (looks magenta) |
| `fuchsia`      | Mix of **red + blue** pixels (looks bright magenta) |
| `brown`        | Mix of **red + yellow + black** pixels (looks brown) |
| `navy`         | Mix of **blue + black** pixels (looks dark blue) |
| `gold`         | Mix of **yellow + red** pixels (looks gold) |
| `pink`         | Mix of **red + white** pixels (looks pink) |
| `gray`         | Mix of **black + white** pixels (looks gray) |

**The exact appearance depends on Floyd-Steinberg dithering, which creates natural-looking intermediate colors!**

## Configuration Example

```yaml
calendars:
  - entity_id: "calendar.family"
    display_name: "Family"
    color: "purple"     
    
  - entity_id: "calendar.work"
    display_name: "Work"
    color: "orange"     
    
  - entity_id: "calendar.gym"
    display_name: "Gym"
    color: "teal"     
    
  - entity_id: "calendar.social"
    display_name: "Social"
    color: "magenta"  
```

## How the Mapping Works

The system uses **Euclidean distance in RGB color space** with a preference for chromatic (saturated) colors. This means:

1. Saturated colors (like `cyan`, `magenta`, `purple`) will map to the nearest chromatic color rather than white or black
2. Very light/pastel colors (like `pink`, `lavender`) may map to white since they are essentially white with a slight tint
3. Dark colors will map to the nearest saturated color or black

## Testing Your Colors

Run the test scripts to see how colors will appear with dithering:

```bash
python test_full_palette.py    # Visual comparison of all colors before/after dithering
python test_colors.py           # Quick listing of color mappings
```

The `test_full_palette.py` script creates two images:
- `palette_preview.png` - Shows the true RGB colors you specify
- `palette_dithered.png` - Shows how they'll actually appear on e-paper with dithering

## How Dithering Looks

**Dithering creates a slightly "grainy" or textured appearance** as it uses patterns of pixels, but from normal viewing distance (1-2 feet), your brain blends these patterns into smooth intermediate colors. This is exactly how color photos appear in newspapers or how inkjet printers work!

### Selective Dithering

The system uses **selective dithering** to preserve text quality:
- ✅ **Black and white pixels (text) stay perfectly sharp** - Not dithered at all
- ✅ **Colored areas get dithered** - Purple, orange, teal blend smoothly

This means calendar text remains crisp and readable while colored event indicators show their true colors!

**Tradeoffs:**
- ✅ **Pro:** You get access to the full color spectrum (purple, orange, brown, teal, etc.)
- ✅ **Pro:** Colors look natural and recognizable from viewing distance  
- ✅ **Pro:** Text stays sharp and readable (no fuzzy edges)
- ⚠️ **Note:** Up close on colored areas, you'll see the pixel pattern (just like old newspaper photos)

For calendar displays where events are shown as colored bars or dots with black text, dithering works perfectly!

## Disabling Dithering

If you prefer solid colors only (no dithering), you can disable it in `src/display/epaper_driver.py`:

```python
# Change this line in quantize_image():
quantized = image.convert("RGB").quantize(palette=pal_image, dither=Image.Dither.NONE)
```

With dithering disabled, all colors will snap to the nearest of the 6 base colors.
