"""Color management for e-paper display and calendar color assignment."""


class ColorManager:
    """
    Manages color palette and assignment for calendars.

    The Waveshare 7.3" HAT (E) supports 6 colors:
    - Black: Used for text, borders, grid lines
    - White: Used for background
    - Red, Yellow, Green, Blue: Available for calendar color coding
    
    Accepts any common color name - will automatically map to nearest e-paper color.
    """

    # E-paper hardware colors (what the display can actually render)
    EPAPER_COLORS = {
        'black': (0, 0, 0),
        'white': (255, 255, 255),
        'red': (255, 0, 0),
        'yellow': (255, 255, 0),
        'green': (0, 255, 0),
        'blue': (0, 0, 255)
    }

    # Common color names mapped to RGB (will be quantized to nearest e-paper color)
    COMMON_COLORS = {
        # Basic colors
        'black': (0, 0, 0),
        'white': (255, 255, 255),
        'red': (255, 0, 0),
        'green': (0, 255, 0),
        'blue': (0, 0, 255),
        'yellow': (255, 255, 0),
        
        # Shades of red/pink
        'pink': (255, 192, 203),
        'lightpink': (255, 182, 193),
        'hotpink': (255, 105, 180),
        'deeppink': (255, 20, 147),
        'crimson': (220, 20, 60),
        'darkred': (139, 0, 0),
        'maroon': (128, 0, 0),
        'salmon': (250, 128, 114),
        'coral': (255, 127, 80),
        'tomato': (255, 99, 71),
        
        # Shades of orange/brown
        'orange': (255, 165, 0),
        'orangered': (255, 69, 0),
        'darkorange': (255, 140, 0),
        'gold': (255, 215, 0),
        'brown': (165, 42, 42),
        'chocolate': (210, 105, 30),
        'sienna': (160, 82, 45),
        'tan': (210, 180, 140),
        
        # Shades of yellow
        'lightyellow': (255, 255, 224),
        'khaki': (240, 230, 140),
        'olive': (128, 128, 0),
        
        # Shades of green
        'lime': (0, 255, 0),
        'lightgreen': (144, 238, 144),
        'darkgreen': (0, 100, 0),
        'forestgreen': (34, 139, 34),
        'seagreen': (46, 139, 87),
        'teal': (0, 128, 128),
        'cyan': (0, 255, 255),
        'aqua': (0, 255, 255),
        'turquoise': (64, 224, 208),
        'mint': (152, 255, 152),
        
        # Shades of blue
        'lightblue': (173, 216, 230),
        'skyblue': (135, 206, 235),
        'navy': (0, 0, 128),
        'darkblue': (0, 0, 139),
        'royalblue': (65, 105, 225),
        'steelblue': (70, 130, 180),
        
        # Shades of purple/violet
        'purple': (128, 0, 128),
        'violet': (238, 130, 238),
        'magenta': (255, 0, 255),
        'fuchsia': (255, 0, 255),
        'orchid': (218, 112, 214),
        'plum': (221, 160, 221),
        'lavender': (230, 230, 250),
        'indigo': (75, 0, 130),
        
        # Grays
        'gray': (128, 128, 128),
        'grey': (128, 128, 128),
        'silver': (192, 192, 192),
        'darkgray': (169, 169, 169),
        'lightgray': (211, 211, 211),
        'dimgray': (105, 105, 105),
    }

    # Priority order for calendar color assignment (when not specified)
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
        Get RGB tuple for a color name, quantized to nearest e-paper color.
        
        Accepts any common color name (e.g., 'purple', 'orange', 'teal') and
        automatically maps it to the nearest available e-paper color.

        Args:
            color_name: Name of the color (e.g., 'red', 'purple', 'teal')

        Returns:
            tuple: RGB tuple (r, g, b) from e-paper palette
        """
        color_lower = color_name.lower()
        
        # Check if it's directly an e-paper color
        if color_lower in self.EPAPER_COLORS:
            return self.EPAPER_COLORS[color_lower]
        
        # Check if it's a known common color
        if color_lower in self.COMMON_COLORS:
            rgb = self.COMMON_COLORS[color_lower]
            # Quantize to nearest e-paper color
            return self.quantize_to_palette(rgb)
        
        # Default to black if unknown
        return self.EPAPER_COLORS['black']
    
    def get_color_name_for_display(self, color_name):
        """
        Get the e-paper color name that a given color will be rendered as.
        
        Args:
            color_name: Input color name (e.g., 'purple', 'orange')
            
        Returns:
            str: Name of the e-paper color it will render as (e.g., 'red', 'blue')
        """
        rgb = self.get_rgb(color_name)
        
        # Find which e-paper color this matches
        for name, color_rgb in self.EPAPER_COLORS.items():
            if color_rgb == rgb:
                return name
        
        return 'black'

    def assign_calendar_colors(self, calendars):
        """
        Assign colors to calendars based on configuration.
        
        Accepts any common color name - will be automatically mapped to the
        nearest e-paper color for display.

        Args:
            calendars: List of calendar configurations

        Returns:
            dict: Mapping of calendar entity_id to RGB color tuple
        """
        calendar_colors = {}

        for i, calendar in enumerate(calendars):
            # Use specified color if provided
            specified_color = calendar.get('color', '').lower()

            if specified_color and specified_color in self.COMMON_COLORS:
                # User specified a valid color name
                color_name = specified_color
                rgb = self.get_rgb(color_name)
                epaper_color = self.get_color_name_for_display(color_name)
            else:
                # No color specified or invalid - assign from priority list
                color_name = self.COLOR_PRIORITY[i % len(self.COLOR_PRIORITY)]
                rgb = self.get_rgb(color_name)
                epaper_color = color_name

            calendar_colors[calendar['entity_id']] = {
                'name': color_name,  # Original color name requested
                'epaper_name': epaper_color,  # What it actually renders as
                'rgb': rgb,
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
            dict: Color information (name, epaper_name, rgb, display_name)
        """
        return self.calendar_colors.get(
            entity_id,
            {
                'name': 'black',
                'epaper_name': 'black',
                'rgb': self.EPAPER_COLORS['black'],
                'display_name': entity_id
            }
        )

    def quantize_to_palette(self, rgb):
        """
        Find the nearest e-paper color for a given RGB value.
        
        Uses a weighted distance that favors saturated colors over white/black
        to better match human color perception.

        Args:
            rgb: RGB tuple (r, g, b)

        Returns:
            tuple: Nearest e-paper color RGB tuple
        """
        r, g, b = rgb
        min_distance = float('inf')
        nearest_color = self.EPAPER_COLORS['black']

        for color_name, color_rgb in self.EPAPER_COLORS.items():
            cr, cg, cb = color_rgb
            
            # Calculate Euclidean distance in RGB space
            distance = ((r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2) ** 0.5
            
            # Apply penalty for white/black to prefer chromatic colors
            # This helps colors like pink, cyan, magenta map to their nearest chromatic color
            # rather than white
            if color_name in ['white', 'black']:
                # Calculate saturation of input color (how far from grayscale)
                avg = (r + g + b) / 3
                saturation = max(abs(r - avg), abs(g - avg), abs(b - avg))
                
                # If input color is highly saturated, penalize achromatic colors
                if saturation > 50:  # Threshold for considering a color "chromatic"
                    distance *= 1.5  # Penalty factor

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
