"""Minimal stub of the Waveshare `epd7in3e` driver.

This stub implements the small surface needed by `epaper_driver.py`:
- `EPD()` constructor
- `init()`
- `display(buffer)`
- `Clear()`
- `sleep()`

On Raspberry Pi with the official Waveshare library installed, remove
this stub and use the hardware driver instead.
"""

class EPD:
    def __init__(self):
        # Typical driver sets width/height attributes; provide sensible defaults
        self.width = 800
        self.height = 480

    def init(self):
        # No-op initialization for stub
        return None

    def display(self, buffer):
        """
        Stub display: decode the 4-bit-per-pixel buffer produced by
        `EPaperDisplay._image_to_buffer` and save a PNG for debugging.

        This makes local development on non-RPi machines visual — the
        official driver would drive hardware instead.
        """
        try:
            # Lazy import PIL to avoid adding dependency unless used
            from PIL import Image

            width = self.width
            height = self.height

            # Unpack 2 pixels per byte (high nibble then low nibble)
            pixels = []
            for b in buffer:
                high = (b & 0xF0) >> 4
                low = b & 0x0F
                pixels.append(high)
                pixels.append(low)

            # Ensure pixel count matches expected size
            expected = width * height
            if len(pixels) < expected:
                # If the buffer is shorter, pad with white
                pixels += [1] * (expected - len(pixels))
            elif len(pixels) > expected:
                pixels = pixels[:expected]

            # Map palette indices (0-6) to RGB values similar to driver palette
            palette_map = {
                0: (0, 0, 0),        # Black
                1: (255, 255, 255),  # White
                2: (255, 255, 0),    # Yellow
                3: (255, 0, 0),      # Red
                4: (0, 0, 0),        # Black (duplicate)
                5: (0, 0, 255),      # Blue
                6: (0, 255, 0),      # Green
            }

            img = Image.new('RGB', (width, height))
            px = img.load()

            idx = 0
            for y in range(height):
                for x in range(width):
                    palette_index = pixels[idx]
                    rgb = palette_map.get(palette_index, (255, 255, 255))
                    px[x, y] = rgb
                    idx += 1

            out_path = 'calendar_display_stub.png'
            img.save(out_path)
            print(f"Stub: saved display output to {out_path}")

        except Exception as e:
            print("Stub display failed:", e)

    def Clear(self):
        # Stub: do nothing
        return None

    def sleep(self):
        # Stub: do nothing
        return None
