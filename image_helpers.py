"""
Shared image generation helpers for ListaPro.
Used by instagram_generator, story_generator, and carousel_generator.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Optional

try:
    import qrcode
except ImportError:
    qrcode = None

from labels import get_label

BASE_DIR = Path(__file__).parent
GENERATED_DIR = BASE_DIR / "generated"
FONTS_DIR = BASE_DIR / "static" / "fonts"
ICONS_DIR = BASE_DIR / "video" / "public" / "icons"
PLACEHOLDER = BASE_DIR / "static" / "placeholder-house.jpg"

# Colors
GOLD = (201, 168, 76)
WHITE = (255, 255, 255)
WHITE_DIM = (220, 220, 220)
BLACK = (0, 0, 0)

# Icon mapping
STAT_ICONS = {
    "recamaras": "bed.png",
    "banos": "bathroom.png",
    "m2_construidos": "area.png",
    "estacionamientos": "parking.png",
}


# ─── Helpers ───────────────────────────────────────────────


def hex_to_rgb(hex_color: str) -> tuple:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    """Load font from static/fonts/, fallback to default."""
    try:
        return ImageFont.truetype(str(FONTS_DIR / name), size)
    except Exception:
        return ImageFont.load_default()


def crop_to_fill(img: Image.Image, tw: int, th: int) -> Image.Image:
    """Center-crop with slight top bias to fill target dimensions."""
    if img.mode == "RGBA":
        img = img.convert("RGB")
    target_r = tw / th
    img_r = img.width / img.height
    if img_r > target_r:
        new_w = int(img.height * target_r)
        left = (img.width - new_w) // 2
        img = img.crop((left, 0, left + new_w, img.height))
    else:
        new_h = int(img.width / target_r)
        top = max(0, min((img.height - new_h) // 3, img.height - new_h))
        img = img.crop((0, top, img.width, top + new_h))
    return img.resize((tw, th), Image.LANCZOS)


def draw_gradient(canvas: Image.Image, start_y: int, end_y: int,
                  max_alpha: int = 230, width: int = 1080) -> Image.Image:
    """Vertical gradient: transparent -> dark overlay."""
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    span = end_y - start_y
    for y in range(span):
        a = int(max_alpha * (y / span) ** 1.3)
        draw.line([(0, start_y + y), (width, start_y + y)], fill=(0, 0, 0, a))
    return Image.alpha_composite(canvas, overlay)


def make_circular(img: Image.Image, size: int) -> Image.Image:
    """Circular crop with anti-aliased mask."""
    img = img.resize((size, size), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    result.paste(img, (0, 0), mask)
    return result


def load_icon(name: str, size: int = 40) -> Optional[Image.Image]:
    """Load and resize a stat icon."""
    path = ICONS_DIR / name
    if not path.exists():
        return None
    try:
        icon = Image.open(str(path)).convert("RGBA")
        return icon.resize((size, size), Image.LANCZOS)
    except Exception:
        return None


def rounded_rect(draw: ImageDraw.ImageDraw, xy: tuple, radius: int, fill: tuple):
    """Draw a rounded rectangle (compatible with older Pillow versions)."""
    x0, y0, x1, y1 = xy
    r = radius
    draw.rectangle([x0 + r, y0, x1 - r, y1], fill=fill)
    draw.rectangle([x0, y0 + r, x1, y1 - r], fill=fill)
    draw.pieslice([x0, y0, x0 + 2 * r, y0 + 2 * r], 180, 270, fill=fill)
    draw.pieslice([x1 - 2 * r, y0, x1, y0 + 2 * r], 270, 360, fill=fill)
    draw.pieslice([x0, y1 - 2 * r, x0 + 2 * r, y1], 90, 180, fill=fill)
    draw.pieslice([x1 - 2 * r, y1 - 2 * r, x1, y1], 0, 90, fill=fill)


def extract_stats(data: dict, lang: str = "es") -> list:
    """Extract stats as (value, label, icon_key) tuples with language support."""
    stats = []
    rec = str(data.get("recamaras", "0") or "0")
    if rec != "0":
        stats.append((rec, get_label("recamaras", lang), "recamaras"))
    ban = str(data.get("banos", "0") or "0")
    if ban != "0":
        stats.append((ban, get_label("banos", lang), "banos"))
    m2 = str(data.get("m2_construidos", "") or "")
    if m2 and m2 != "0":
        stats.append((f"{m2}m\u00b2", get_label("m2_construidos", lang), "m2_construidos"))
    est = str(data.get("estacionamientos", "0") or "0")
    if est != "0":
        stats.append((est, get_label("estacionamientos", lang), "estacionamientos"))
    return stats


def parse_colors(color_overrides: dict = None) -> tuple:
    """Parse color overrides, return (primary, accent) RGB tuples."""
    primary = (26, 54, 93)
    accent = (229, 62, 62)
    if color_overrides:
        if "color_primary" in color_overrides:
            primary = hex_to_rgb(color_overrides["color_primary"])
        if "color_accent" in color_overrides:
            accent = hex_to_rgb(color_overrides["color_accent"])
    return primary, accent


def render_logo(canvas: Image.Image, branding: dict, x_right: int = 40,
                y: int = 35, max_w: int = 200, max_h: int = 80) -> Image.Image:
    """Render logo on top-right corner with white backing. Returns updated canvas."""
    if not branding or not branding.get("logo_path"):
        return canvas
    try:
        logo_full = GENERATED_DIR / branding["logo_path"]
        if not logo_full.exists():
            return canvas
        logo = Image.open(str(logo_full)).convert("RGBA")
        ratio = min(max_w / logo.width, max_h / logo.height)
        new_size = (int(logo.width * ratio), int(logo.height * ratio))
        logo = logo.resize(new_size, Image.LANCZOS)
        lx = canvas.width - new_size[0] - x_right
        canvas.paste(logo, (lx, y), logo)
    except Exception:
        pass
    return canvas


def render_badge(draw: ImageDraw.ImageDraw, text: str, accent: tuple,
                 x: int = 40, y: int = 40, font_obj=None):
    """Render an operation badge (top-left rounded rect)."""
    if font_obj is None:
        font_obj = font("DMSans-Variable.ttf", 22)
    bbox = draw.textbbox((0, 0), text, font=font_obj)
    bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 18, 10
    rounded_rect(draw,
                 (x, y, x + bw + pad_x * 2, y + bh + pad_y * 2),
                 radius=8, fill=accent + (230,))
    draw.text((x + pad_x, y + pad_y - 2), text, font=font_obj, fill=WHITE)
    return bh + pad_y * 2  # return badge height


def render_qr(canvas: Image.Image, branding: dict, x: int = None,
              y: int = None, size: int = 110) -> Image.Image:
    """Render QR code if enabled. Returns updated canvas."""
    if not branding or not branding.get("qr_enabled") or not branding.get("qr_url") or not qrcode:
        return canvas
    try:
        qr = qrcode.QRCode(version=1, box_size=4, border=2)
        qr.add_data(branding["qr_url"])
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
        qr_img = qr_img.resize((size, size), Image.LANCZOS)
        if x is None:
            x = canvas.width - size - 50
        if y is None:
            y = canvas.height - size - 50
        canvas.paste(qr_img, (x, y), qr_img)
    except Exception:
        pass
    return canvas
