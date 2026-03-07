"""Test script to demonstrate extended color palette mapping."""

import sys
sys.path.insert(0, 'src')

from utils.color_manager import ColorManager

# Create a color manager
config = {'display': {}}
cm = ColorManager(config)

print("Extended Color Palette Test")
print("=" * 60)
print()

# Test some interesting color mappings
test_colors = [
    'purple', 'orange', 'teal', 'pink', 'brown', 'gray',
    'magenta', 'cyan', 'violet', 'coral', 'navy', 'lime',
    'crimson', 'gold', 'turquoise', 'lavender', 'maroon',
    'indigo', 'olive', 'salmon', 'orchid'
]

print("Color Mapping (what e-paper color each common color maps to):")
print("-" * 60)

# Group colors by their e-paper mapping
epaper_groups = {}
for color_name in test_colors:
    epaper_name = cm.get_color_name_for_display(color_name)
    rgb = cm.get_rgb(color_name)
    
    if epaper_name not in epaper_groups:
        epaper_groups[epaper_name] = []
    
    epaper_groups[epaper_name].append((color_name, rgb))

# Print grouped results
for epaper_color in ['red', 'yellow', 'green', 'blue', 'black', 'white']:
    if epaper_color in epaper_groups:
        print(f"\n{epaper_color.upper()} ({cm.get_rgb(epaper_color)}):")
        for color_name, rgb in sorted(epaper_groups[epaper_color]):
            print(f"  • {color_name:15s} {rgb}")

print("\n" + "=" * 60)
print("\nExample usage in config.yaml:")
print("-" * 60)
print("""
calendars:
  - entity_id: "calendar.family"
    display_name: "Family"
    color: "purple"      # → renders as red or blue (nearest match)
    
  - entity_id: "calendar.work"
    display_name: "Work"
    color: "orange"      # → renders as red or yellow (nearest match)
    
  - entity_id: "calendar.gym"
    display_name: "Gym"
    color: "teal"        # → renders as green or blue (nearest match)
    
  - entity_id: "calendar.social"
    display_name: "Social"
    color: "pink"        # → renders as red (nearest match)
""")

print("\nNote: The hardware only supports 6 colors (black, white, red,")
print("yellow, green, blue). All other colors are automatically mapped")
print("to the nearest available color using Euclidean distance in RGB space.")
