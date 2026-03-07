"""Visual test showing all extended palette colors with dithering."""

import sys
sys.path.insert(0, 'src')

from PIL import Image, ImageDraw, ImageFont
from utils.color_manager import ColorManager
from display.epaper_driver import EPaperDisplay

# Create config
config = {
    'display': {
        'width': 800,
        'height': 480,
        'mock_mode': True
    }
}

cm = ColorManager(config)
display = EPaperDisplay(config)

# Get all common colors organized by category
color_categories = {
    'Reds & Pinks': ['red', 'pink', 'lightpink', 'hotpink', 'deeppink', 'crimson', 'darkred', 'maroon', 'salmon', 'coral', 'tomato'],
    'Oranges & Browns': ['orange', 'orangered', 'darkorange', 'gold', 'brown', 'chocolate', 'sienna', 'tan'],
    'Yellows': ['yellow', 'lightyellow', 'khaki', 'olive'],
    'Greens': ['green', 'lime', 'lightgreen', 'darkgreen', 'forestgreen', 'seagreen', 'mint'],
    'Cyans & Teals': ['teal', 'cyan', 'aqua', 'turquoise'],
    'Blues': ['blue', 'lightblue', 'skyblue', 'navy', 'darkblue', 'royalblue', 'steelblue'],
    'Purples': ['purple', 'violet', 'magenta', 'fuchsia', 'orchid', 'plum', 'lavender', 'indigo'],
    'Grays': ['gray', 'grey', 'silver', 'darkgray', 'lightgray', 'dimgray', 'black', 'white']
}

# Create a large image to show all colors
img_width = 1600
img_height = 1200
image = Image.new('RGB', (img_width, img_height), (255, 255, 255))
draw = ImageDraw.Draw(image)

# Try to load a font
try:
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 14)
    title_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 16)
except:
    font = ImageFont.load_default()
    title_font = ImageFont.load_default()

# Title
draw.text((20, 20), "Extended Color Palette with Dithering", fill=(0, 0, 0), font=title_font)
draw.text((20, 45), "All colors will be approximated using the 6 available e-paper inks (black, white, red, yellow, green, blue)", 
          fill=(0, 0, 0), font=font)

y = 80
swatch_size = 40
spacing_x = 10

print("\n" + "="*70)
print("Extended Palette Test with Dithering")
print("="*70)
print()

for category, colors in color_categories.items():
    # Category header
    draw.text((20, y), category, fill=(0, 0, 0), font=title_font)
    print(f"\n{category}:")
    print("-" * 70)
    y += 25
    
    x = 20
    for color_name in colors:
        rgb = cm.get_rgb(color_name)
        epaper_name = cm.get_color_name_for_display(color_name)
        
        print(f"  {color_name:15s} RGB{str(rgb):20s} → {epaper_name}")
        
        # Draw color swatch
        draw.rectangle([(x, y), (x + swatch_size, y + swatch_size)], fill=rgb, outline=(0, 0, 0))
        
        # Draw color name and RGB
        draw.text((x, y + swatch_size + 3), color_name, fill=(0, 0, 0), font=font)
        draw.text((x, y + swatch_size + 18), f"RGB{rgb}", fill=(100, 100, 100), font=font)
        
        x += 150
        if x > img_width - 150:
            x = 20
            y += 75
    
    y += 75

# Save the preview image
image.save('palette_preview.png')
print()
print("="*70)
print("✓ Saved: palette_preview.png (True RGB colors)")
print()

# Now apply dithering like the display would
dithered_image = display.quantize_image(image)
dithered_rgb = dithered_image.convert('RGB')
dithered_rgb.save('palette_dithered.png')

print("✓ Saved: palette_dithered.png (6 colors + Floyd-Steinberg dithering)")
print()
print("Compare the two images:")
print("  - palette_preview.png  = What you specify in config")
print("  - palette_dithered.png = How it looks on e-paper")
print()
print("Purple, orange, brown, cyan, etc. appear as PATTERNS of the")
print("6 available inks that your eye blends into the desired color!")
print("="*70)

