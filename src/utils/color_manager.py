"""Color management for e-paper display and calendar color assignment."""


class ColorManager:
    """
    Manages color palette and assignment for calendars.

    The Waveshare 7.3" HAT (E) supports 6 colors:
    - Black: Used for text, borders, grid lines
    - White: Used for background
    - Red, Yellow, Green, Blue: Available for calendar color coding
    """

    # E-paper color palette (RGB tuples)
    EPAPER_COLORS = {
        'black': (0, 0, 0),
        'white': (255, 255, 255),
        'red': (255, 0, 0),
        'yellow': (255, 255, 0),
        'gold': (255, 180, 0),      # Gold/orange - more visible than yellow on e-paper
        'green': (0, 255, 0),
        'blue': (0, 0, 255)
    }

    # Priority order for calendar color assignment
    COLOR_PRIORITY = ['red', 'yellow', 'green', 'blue']

    def __init__(self, config):
        """
        Initialize color manager.

        Args:
            config: Configuration dictionary with display color settings
        """
        self.config = config
        self.calendar_colors = {}

    def get_rgb(self, color_name):
        """
        Get RGB tuple for a color name.

        Args:
            color_name: Name of the color (e.g., 'red', 'black')

        Returns:
            tuple: RGB tuple (r, g, b)
        """
        return self.EPAPER_COLORS.get(color_name.lower(), self.EPAPER_COLORS['black'])

    def assign_calendar_colors(self, calendars):
        """
        Assign colors to calendars based on configuration.

        Args:
            calendars: List of calendar configurations

        Returns:
            dict: Mapping of calendar entity_id to RGB color tuple
        """
        calendar_colors = {}

        for i, calendar in enumerate(calendars):
            # Use specified color if valid, otherwise assign from priority list
            specified_color = calendar.get('color', '').lower()

            if specified_color in self.COLOR_PRIORITY:
                color_name = specified_color
            else:
                # Round-robin assignment if more calendars than available colors
                color_name = self.COLOR_PRIORITY[i % len(self.COLOR_PRIORITY)]

            calendar_colors[calendar['entity_id']] = {
                'name': color_name,
                'rgb': self.get_rgb(color_name),
                'display_name': calendar.get('display_name', calendar['entity_id'])
            }

        self.calendar_colors = calendar_colors
        return calendar_colors

    def get_calendar_color(self, entity_id):
        """
        Get the assigned color for a calendar.

        Args:
            entity_id: Calendar entity ID

        Returns:
            dict: Color information (name, rgb, display_name)
        """
        return self.calendar_colors.get(
            entity_id,
            {'name': 'black', 'rgb': self.EPAPER_COLORS['black'], 'display_name': entity_id}
        )

    def quantize_to_palette(self, rgb):
        """
        Find the nearest e-paper color for a given RGB value.

        Args:
            rgb: RGB tuple (r, g, b)

        Returns:
            tuple: Nearest e-paper color RGB tuple
        """
        r, g, b = rgb
        min_distance = float('inf')
        nearest_color = self.EPAPER_COLORS['black']

        for color_rgb in self.EPAPER_COLORS.values():
            cr, cg, cb = color_rgb
            # Calculate Euclidean distance in RGB space
            distance = ((r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2) ** 0.5

            if distance < min_distance:
                min_distance = distance
                nearest_color = color_rgb

        return nearest_color

    def get_legend(self):
        """
        Get a list of calendar names and their colors for legend display.

        Returns:
            list: List of dicts with calendar info for legend
        """
        legend = []
        for entity_id, color_info in self.calendar_colors.items():
            legend.append({
                'name': color_info['display_name'],
                'color': color_info['rgb']
            })
        return legend
