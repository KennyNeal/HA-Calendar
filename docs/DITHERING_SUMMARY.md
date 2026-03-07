# Dithering Implementation Summary

## What Changed

✅ **Enabled Floyd-Steinberg dithering** in the e-paper display driver  
✅ **Colors now display as their true appearance** using pixel patterns  
✅ **Purple looks purple, orange looks orange, teal looks teal, etc.**

## How It Works

Instead of snapping colors to the nearest of 6 base colors, the system now uses **Floyd-Steinberg dithering** to create patterns of pixels that your eye blends into the desired color.

### Examples:
- **Purple** (128, 0, 128) → Pattern of red + blue pixels that looks purple
- **Orange** (255, 165, 0) → Pattern of red + yellow pixels that looks orange  
- **Teal** (0, 128, 128) → Pattern of green + blue pixels that looks teal
- **Brown** (165, 42, 42) → Pattern of red + yellow + black pixels that looks brown

## Files Modified

### 1. `src/display/epaper_driver.py`
**Changed:** Line 104
```python
# Before:
quantized = image.convert("RGB").quantize(palette=pal_image, dither=Image.Dither.NONE)

# After:
quantized = image.convert("RGB").quantize(palette=pal_image, dither=Image.Dither.FLOYDSTEINBERG)
```
**Effect:** Enables dithering instead of hard quantization to nearest color

### 2. `src/utils/color_manager.py`
**Changed:** `get_rgb()` method
- No longer calls `quantize_to_palette()` for intermediate colors
- Returns actual RGB values (128, 0, 130) instead of quantized (255, 0, 0)
- Lets the display driver handle dithering

**Result:** 
- Purple = (128, 0, 128) ← true purple
- Orange = (255, 165, 0) ← true orange
- etc.

### 3. Documentation
- Updated `README.md` to explain dithering
- Updated `docs/EXTENDED_COLORS.md` with dithering details & examples
- Created `test_full_palette.py` for before/after dithering comparison

## Testing Your Colors

### Visual Test (Recommended)
```bash
python test_full_palette.py
```

This creates two images:
- **palette_preview.png** - True RGB colors (what you specify)
- **palette_dithered.png** - How it looks with e-paper dithering

Compare them side-by-side to see how dithering approximates each color!

### Your Calendar
```bash
python src/main.py
```

Check **calendar_display.png** to see:
- LSU Baseball events in **purple** (red+blue dithered pixels)
- Family events in **yellow** (with black border for contrast)
- Football events in **green**

## Visual Appearance

**What to expect:**
- Colors look natural and recognizable from normal viewing distance (1-2 feet)
- Up close, you'll see the pixel pattern (like oldnewspaper photos)
- The effect works best for calendars with colored bars/dots/boxes
- The dithering pattern is fine enough that it blends well

## Comparison: Before vs After

### Before (Hard Quantization)
- Purple (128, 0, 128) → **Solid red** (255, 0, 0) ❌
- Orange (255, 165, 0) → **Solid yellow** (255, 255, 0) ⚠️
- Teal (0, 128, 128) → **Solid green** (0, 255, 0) ⚠️

### After (Dithering)
- Purple (128, 0, 128) → **Mixed red+blue pixels = purple** ✅
- Orange (255, 165, 0) → **Mixed red+yellow pixels = orange** ✅
- Teal (0, 128, 128) → **Mixed green+blue pixels = teal** ✅

## If You Want to Disable Dithering

Edit `src/display/epaper_driver.py` line 104:

```python
# Change back to:
quantized = image.convert("RGB").quantize(palette=pal_image, dither=Image.Dither.NONE)
```

All colors will snap to the nearest of the 6 base colors (old behavior).

## Benefits

1. **True color representation** - You get what you ask for
2. **More distinct calendars** - Purple, orange, teal all look different
3. **Natural appearance** - From viewing distance, colors blend smoothly
4. **No configuration needed** - Just specify any color name, dithering is automatic
5. **Works with 60+ color names** - Full CSS color palette support

## Your Current Config

```yaml
calendars:
  - entity_id: "calendar.family"
    color: "yellow"    # → Solid yellow (with black border)
    
  - entity_id: "calendar.prairieville_high_school_football"
    color: "green"     # → Solid green
    
  - entity_id: "calendar.lsu_baseball"
    color: "purple"    # → Dithered red+blue = purple! ✅
```

Purple now looks like actual purple instead of solid red or blue!
