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
        # Stub: accept buffer and do nothing
        return None

    def Clear(self):
        # Stub: do nothing
        return None

    def sleep(self):
        # Stub: do nothing
        return None
