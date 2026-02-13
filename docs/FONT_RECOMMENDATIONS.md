# Font Recommendations for E-Paper Displays

This document explains font choices for optimal display quality on e-paper screens.

## Why Font Choice Matters for E-Paper

E-paper displays have unique characteristics that affect text rendering:
- **Lower resolution** than typical screens (typically 300-400 DPI but limited grayscale)
- **No anti-aliasing** in most modes
- **High contrast** (black on white or limited colors)
- **No subpixel rendering**

The right font can make the difference between crisp, readable text and jagged, hard-to-read characters.

## Recommended Fonts (In Order of Preference)

### 1. **Liberation Sans** ⭐ BEST for E-Paper
- **Package**: `fonts-liberation`
- **Why**: Excellent hinting, designed specifically for screen rendering
- **Characteristics**: Very clean edges, excellent readability at all sizes
- **Installation**: `sudo apt-get install fonts-liberation`

### 2. **Roboto**
- **Package**: `fonts-roboto-unhinted`
- **Why**: Google's font, optimized for low-res displays
- **Characteristics**: Clean, modern, good spacing
- **Installation**: `sudo apt-get install fonts-roboto-unhinted`

### 3. **Ubuntu**
- **Package**: `fonts-ubuntu`
- **Why**: Designed for screen clarity
- **Characteristics**: Clean and modern with good distinction between characters
- **Installation**: `sudo apt-get install fonts-ubuntu`

### 4. **Noto Sans**
- **Package**: `fonts-noto`
- **Why**: Very readable with excellent international character support
- **Characteristics**: Well-hinted, clean rendering
- **Installation**: `sudo apt-get install fonts-noto`

### 5. **DejaVu Sans** (Fallback)
- **Package**: `fonts-dejavu`
- **Why**: Widely available, decent quality
- **Characteristics**: Acceptable but can look slightly jagged on e-paper
- **Installation**: Usually pre-installed

## Current Font Setup

The calendar automatically selects the best available font from the list above. Check your logs to see which font is being used:

```bash
tail -f logs/calendar.log | grep "Using font"
```

## Installing All Recommended Fonts

For best results, install all recommended fonts:

```bash
sudo apt-get install -y \
    fonts-liberation \
    fonts-roboto-unhinted \
    fonts-ubuntu \
    fonts-noto \
    fonts-dejavu
```

This is automatically done by `install.sh`.

## Font Sizes

The calendar uses dynamic font sizing:
- **Fewer events per day** → Larger, more readable fonts
- **More events per day** → Smaller fonts to fit everything

This provides optimal readability in all situations.

## Fonts to Avoid on E-Paper

❌ **Serif fonts** (Times New Roman, Georgia) - Serifs create jaggy edges  
❌ **Script/Handwriting fonts** - Too complex for e-paper resolution  
❌ **Condensed fonts** - Characters too thin and pixelated  
❌ **Decorative fonts** - Details lost at low resolution  

## Testing Fonts

To test how different fonts look on your display:

1. Check which font is currently in use:
   ```bash
   grep "Using font" logs/calendar.log
   ```

2. If you want to force a specific font, you can temporarily rename others or modify `base_renderer.py`

3. Generate a test image:
   ```bash
   python3 src/main.py
   ```

4. Compare the output visually

## Font Rendering Improvements

The calendar now includes several rendering improvements:

1. **Slightly larger base sizes** - Better readability on e-paper
2. **Dynamic sizing** - Fonts automatically scale based on event density
3. **Better font selection** - Prioritizes clean-rendering fonts
4. **Optimized spacing** - Line heights adjusted for clarity

## Weather Icons Font

In addition to text fonts, we use the **Weather Icons** font for weather symbols:
- **Installation**: See `docs/WEATHER_ICONS_SETUP.md`
- **Why**: Professional weather symbols that render cleanly
- **Fallback**: Regular text if not installed

## Troubleshooting

### Text looks jagged or pixelated
- **Solution**: Install Liberation Sans - `sudo apt-get install fonts-liberation`
- **Check**: Verify font is being used in logs

### Text is too small
- **Solution**: Font sizes auto-adjust based on event count. Fewer events = larger text
- **Manual override**: Edit font sizes in `base_renderer.py` if needed

### Characters are cut off
- **Solution**: This is usually a wrapping issue, not a font issue
- **Check**: Verify line wrapping is working correctly

### Weather icons don't show
- **Solution**: Install Weather Icons font (separate from text fonts)
- **See**: `docs/WEATHER_ICONS_SETUP.md`

## Additional Resources

- **Liberation Fonts**: https://github.com/liberationfonts/liberation-fonts
- **Roboto**: https://fonts.google.com/specimen/Roboto
- **Ubuntu Font**: https://design.ubuntu.com/font/
- **Noto Sans**: https://fonts.google.com/noto
- **E-Paper Font Best Practices**: https://goodereader.com/blog/e-paper
