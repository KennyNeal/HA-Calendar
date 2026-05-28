"""Test to show difference between full dithering and selective dithering."""

import sys
sys.path.insert(0, 'src')

from PIL import Image, ImageDraw, ImageFont
from display.epaper_driver import EPaperDisplay

config = {'display': {'mock_mode': True}}

# Create a simple test image with text and colored elements
width, height = 800, 480
image = Image.new('RGB', (width, height), (255, 255, 255))
draw = ImageDraw.Draw(image)

# Try to load a font
try:
    font_large = ImageFont.truetype("arial.ttf", 36)
    font_small = ImageFont.truetype("arial.ttf", 24)
except:
    font_large = ImageFont.load_default()
    font_small = ImageFont.load_default()

# Draw some text (black on white)
draw.text((50, 50), "Black Text - Sharp!", fill=(0, 0, 0), font=font_large)
draw.text((450, 50), "Red Text - Sharp!", fill=(255, 0, 0), font=font_large)
draw.text((50, 100), "The quick brown fox jumps", fill=(0, 0, 0), font=font_small)
draw.text((50, 130), "Yellow text is native!", fill=(255, 255, 0), font=font_small)
draw.text((450, 130), "Green text is native!", fill=(0, 255, 0), font=font_small)

# Draw colored boxes with labels (native and dithered colors)
colors = [
    ("Red (native)", (255, 0, 0)),
    ("Yellow (native)", (255, 255, 0)),
    ("Green (native)", (0, 255, 0)),
    ("Blue (native)", (0, 0, 255)),
    ("Purple (dithered)", (128, 0, 128)),
    ("Orange (dithered)", (255, 165, 0)),
    ("Teal (dithered)", (0, 128, 128)),
]

y = 180
for name, rgb in colors:
    # Colored box
    draw.rectangle([(50, y), (200, y+40)], fill=rgb)
    # Label in black
    draw.text((220, y+10), f"{name} {rgb}", fill=(0, 0, 0), font=font_small)
    y += 60

print("\nText Sharpness Test")
print("=" * 60)
print("\nComparing rendering with selective dithering:")
print("-" * 60)
print("\nWith SELECTIVE dithering:")
print("  ✓ All 6 native colors stay sharp (black, white, red,")
print("    yellow, green, blue) - not dithered")
print("  ✓ Intermediate colors get dithered (purple, orange,")
print("    teal, etc.)")
print("\nWithout selective dithering:")
print("  ✗ ALL pixels dithered (including native colors)")
print("  ✗ Red, yellow, green, blue text looks fuzzy")
print("-" * 60)

# Save the original
image.save('text_test_original.png')
print("\n✓ Saved: text_test_original.png (true colors)")

# Test with selective dithering (current implementation)
display = EPaperDisplay(config)
quantized_selective = display.quantize_image(image.copy())
quantized_selective.convert('RGB').save('text_test_selective_dither.png')
print("✓ Saved: text_test_selective_dither.png (sharp text, dithered colors)")

# Test with full dithering (old approach) - modify temporarily
# We'll do this manually to show the difference
pal_image = Image.new("P", (1, 1))
pal_image.putpalette(
    (0, 0, 0,           # 0: Black
     255, 255, 255,     # 1: White
     255, 255, 0,       # 2: Yellow
     255, 0, 0,         # 3: Red
     0, 0, 0,           # 4: Black (duplicate)
     0, 0, 255,         # 5: Blue
     0, 255, 0)         # 6: Green
    + (0, 0, 0) * 249
)
quantized_full = image.convert("RGB").quantize(palette=pal_image, dither=Image.Dither.FLOYDSTEINBERG)
quantized_full.convert('RGB').save('text_test_full_dither.png')
print("✓ Saved: text_test_full_dither.png (everything dithered, text fuzzy)")

print("\n" + "=" * 60)
print("\nCompare the images:")
print("  1. text_test_selective_dither.png - Native colors crisp! ✓")
print("  2. text_test_full_dither.png - Everything fuzzy ✗")
print("\nZoom in on red, yellow, green, blue text to see they stay sharp!")
print("Purple, orange, teal show dithering pattern (as expected).")
print("=" * 60)
