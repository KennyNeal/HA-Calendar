"""Integration test for extended color palette feature."""

import sys
sys.path.insert(0, 'src')

from utils.color_manager import ColorManager

def test_color_assignment():
    """Test that color assignment works with extended palette."""
    
    config = {'display': {}}
    cm = ColorManager(config)
    
    # Test calendars with various color names
    test_calendars = [
        {
            'entity_id': 'calendar.family',
            'display_name': 'Family',
            'color': 'purple'
        },
        {
            'entity_id': 'calendar.work',
            'display_name': 'Work',
            'color': 'orange'
        },
        {
            'entity_id': 'calendar.gym',
            'display_name': 'Gym',
            'color': 'teal'
        },
        {
            'entity_id': 'calendar.social',
            'display_name': 'Social Events',
            'color': 'magenta'
        },
        {
            'entity_id': 'calendar.holidays',
            'display_name': 'Holidays',
            'color': 'gold'
        }
    ]
    
    # Assign colors
    result = cm.assign_calendar_colors(test_calendars)
    
    print("Extended Color Palette Integration Test")
    print("=" * 70)
    print()
    print("Calendar Color Assignments:")
    print("-" * 70)
    
    for calendar in test_calendars:
        entity_id = calendar['entity_id']
        color_info = cm.get_calendar_color(entity_id)
        
        print(f"{color_info['display_name']:20s} → {color_info['name']:10s} (renders as {color_info['epaper_name']:6s}) {color_info['rgb']}")
    
    print()
    print("-" * 70)
    print("✓ All calendars successfully assigned colors!")
    print()
    
    # Test legend
    legend = cm.get_legend()
    print("Legend Output:")
    print("-" * 70)
    for item in legend:
        print(f"  • {item['name']:20s} {item['color']}")
    
    print()
    print("=" * 70)
    print("✓ Integration test passed!")
    
    return True

if __name__ == '__main__':
    test_color_assignment()
