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
draw.text((50, 50), "Sharp Black Text Test", fill=(0, 0, 0), font=font_large)
draw.text((50, 100), "The quick brown fox jumps over the lazy dog", fill=(0, 0, 0), font=font_small)

# Draw colored boxes with labels
colors = [
    ("Purple", (128, 0, 128)),
    ("Orange", (255, 165, 0)),
    ("Teal", (0, 128, 128)),
    ("Yellow", (255, 255, 0))
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
print("\nComparing text quality with selective dithering:")
print("-" * 60)
print("\nWith SELECTIVE dithering:")
print("  ✓ Black/white text stays sharp (not dithered)")
print("  ✓ Colored areas get dithered (purple, orange, etc.)")
print("\nWithout selective dithering:")
print("  ✗ ALL pixels dithered (including text)")
print("  ✗ Text looks fuzzy/noisy")
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
print("  1. text_test_selective_dither.png - Text is crisp! ✓")
print("  2. text_test_full_dither.png - Text is fuzzy ✗")
print("\nZoom in on the black text to see the difference!")
print("=" * 60)
