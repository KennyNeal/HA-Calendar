"""Simple test script to render "Hello, world!" and send to the e-paper display.

Place this file in the repository root under `tools/` and run:

    python tools/test_display.py

It uses the project's `config/config.yaml` (falls back to
`config/config.example.yaml`) and the `EPaperDisplay` driver.
"""

from pathlib import Path
import sys
import yaml

from PIL import Image, ImageDraw, ImageFont

# Make project `src` available for imports
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / 'src'))

from display.epaper_driver import EPaperDisplay


def load_config(repo_root: Path):
    cfg_path = repo_root / 'config' / 'config.yaml'
    if not cfg_path.exists():
        cfg_path = repo_root / 'config' / 'config.example.yaml'

    with open(cfg_path, 'r') as f:
        return yaml.safe_load(f)


def make_hello_image(width: int, height: int) -> Image.Image:
    img = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Choose a reasonable font size based on display height
    try:
        font_size = max(18, height // 10)
        # Try a common TTF first; fall back to default if not available
        font = ImageFont.truetype('DejaVuSans-Bold.ttf', font_size)
    except Exception:
        font = ImageFont.load_default()

    text = "Hello, world!"
    w, h = draw.textsize(text, font=font)
    x = (width - w) // 2
    y = (height - h) // 2
    draw.text((x, y), text, fill=(0, 0, 0), font=font)

    return img


def main():
    config = load_config(REPO_ROOT)
    display_cfg = config.get('display', {})
    width = display_cfg.get('width', 800)
    height = display_cfg.get('height', 480)

    img = make_hello_image(width, height)

    # Save locally as a quick sanity check
    local_out = REPO_ROOT / 'hello_test.png'
    img.save(local_out)
    print(f"Saved local test image to: {local_out}")

    # Initialize and use the EPaperDisplay
    display = EPaperDisplay(config)
    display.init_display()
    display.display_image(img)
    display.sleep()

    print("Sent image to EPaperDisplay (check calendar_display.png or calendar_display_stub.png if present)")


if __name__ == '__main__':
    main()
