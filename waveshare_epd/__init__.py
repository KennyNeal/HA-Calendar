"""Local Waveshare e-Paper stub package used when the official library
is not installed. This provides a minimal `epd7in3e` module so imports
in `src/display/epaper_driver.py` succeed.

This file intentionally keeps the implementation minimal — only the
methods used by the project are provided. On real hardware you should
replace this with the official Waveshare library.
"""

__all__ = ["epd7in3e"]
