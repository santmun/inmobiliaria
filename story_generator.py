"""
Instagram Story Image Generator for ListaPro.
Generates a 1080x1920 PNG with cover photo, property data overlay, and branding.
"""

from PIL import Image, ImageDraw
from image_helpers import (
    font, crop_to_fill, draw_gradient, make_circular, load_icon,
    extract_stats, parse_colors, render_logo, render_badge, render_qr,
    GENERATED_DIR, PLACEHOLDER, GOLD, WHITE, WHITE_DIM, STAT_ICONS,
)
from labels import get_operation, get_property_type, get_label

# Canvas
W, H = 1080, 1920


# ─── Main Generator ────────────────────────────────────────


def generate_instagram_story(
    property_data: dict,
    cover_photo_path: str,
    output_path: str,
    color_overrides: dict = None,
    branding: dict = None,
    lang: str = "es",
) -> str:
    """
    Generate a 1080x1920 Instagram Story image.
    Returns output_path on success.
    """

    # ── Colors ──
    primary, accent = parse_colors(color_overrides)

    # ── Fonts (larger than post for story format) ──
    font_heading = font("PlayfairDisplay-Variable.ttf", 56)
    font_price = font("DMSans-Variable.ttf", 72)
    font_location = font("DMSans-Variable.ttf", 34)
    font_stat_val = font("DMSans-Variable.ttf", 36)
    font_stat_lbl = font("DMSans-Variable.ttf", 20)
    font_badge = font("DMSans-Variable.ttf", 26)
    font_agent_name = font("DMSans-Variable.ttf", 30)
    font_agent_phone = font("DMSans-Variable.ttf", 24)

    # ── Cover photo → full canvas ──
    try:
        cover = Image.open(cover_photo_path)
    except Exception:
        cover = Image.open(str(PLACEHOLDER))
    canvas = crop_to_fill(cover, W, H).convert("RGBA")

    # ── Gradient overlay (bottom 55%) — stronger than post ──
    canvas = draw_gradient(canvas, start_y=850, end_y=H, max_alpha=245, width=W)

    draw = ImageDraw.Draw(canvas)

    # ── Operation badge (top-left) ──
    operacion_raw = str(property_data.get("operacion", "Venta"))
    badge_text = get_operation(operacion_raw, lang, uppercase=True)
    render_badge(draw, badge_text, accent, x=50, y=60, font_obj=font_badge)

    # ── Logo (top-right) ──
    canvas = render_logo(canvas, branding, x_right=50, y=55, max_w=220, max_h=90)
    draw = ImageDraw.Draw(canvas)

    # ── Property heading ──
    tipo = get_property_type(property_data.get("tipo_propiedad", "Propiedad"), lang)
    op_lower = get_operation(operacion_raw, lang, uppercase=False)
    connector = get_label("heading_en", lang)
    heading = f"{tipo} {connector} {op_lower}"
    draw.text((60, 1250), heading, font=font_heading, fill=WHITE)

    # ── Gold separator line ──
    draw.rectangle([(60, 1340), (220, 1344)], fill=GOLD)

    # ── Price ──
    precio = property_data.get("precio_formateado", "")
    if not precio:
        precio = str(property_data.get("precio", ""))
    draw.text((60, 1370), precio, font=font_price, fill=WHITE)

    # ── Location ──
    ciudad = property_data.get("ciudad", "")
    pais = property_data.get("pais_nombre", "")
    location = f"{ciudad}, {pais}" if pais else ciudad
    if location:
        draw.text((60, 1480), location, font=font_location, fill=WHITE_DIM)

    # ── Stats row with icons (max 3 for story) ──
    stats = extract_stats(property_data, lang)[:3]
    if stats:
        icon_size = 48
        stat_x = 60
        stat_y = 1560

        for val, lbl, icon_key in stats:
            icon_file = STAT_ICONS.get(icon_key)
            if icon_file:
                icon = load_icon(icon_file, icon_size)
                if icon:
                    canvas.paste(icon, (stat_x, stat_y), icon)
                    draw = ImageDraw.Draw(canvas)

            text_x = stat_x + icon_size + 10
            draw.text((text_x, stat_y + 2), val, font=font_stat_val, fill=WHITE)
            val_bbox = draw.textbbox((0, 0), val, font=font_stat_val)
            val_w = val_bbox[2] - val_bbox[0]

            draw.text((text_x, stat_y + 38), lbl, font=font_stat_lbl, fill=WHITE_DIM)

            stat_x += icon_size + 10 + max(val_w, 60) + 50

    # ── Footer pill (semi-transparent, agent info) ──
    footer_y = 1740
    agent_name = property_data.get("agente_nombre", "")
    agent_phone = property_data.get("agente_telefono", "")

    if agent_name or agent_phone:
        # Semi-transparent pill background
        pill_h = 120
        pill = Image.new("RGBA", (W - 100, pill_h), (0, 0, 0, 160))
        canvas.paste(pill, (50, footer_y), pill)
        draw = ImageDraw.Draw(canvas)

        # Thin gold line at pill top
        draw.rectangle([(50, footer_y), (W - 50, footer_y + 3)], fill=GOLD + (180,))

        text_start_x = 80
        text_y = footer_y + 20

        # Agent photo (circular)
        if branding and branding.get("agent_photo_path"):
            try:
                ap_path = GENERATED_DIR / branding["agent_photo_path"]
                if ap_path.exists():
                    ap = Image.open(str(ap_path))
                    circ = make_circular(ap, 80)
                    canvas.paste(circ, (70, footer_y + 20), circ)
                    draw = ImageDraw.Draw(canvas)
                    text_start_x = 170
            except Exception:
                pass

        if agent_name:
            draw.text((text_start_x, text_y), agent_name, font=font_agent_name, fill=WHITE)
            text_y += 40
        if agent_phone:
            draw.text((text_start_x, text_y), agent_phone, font=font_agent_phone, fill=WHITE_DIM)

        # QR code (pill right side)
        canvas = render_qr(canvas, branding, x=W - 50 - 90 - 20, y=footer_y + 15, size=90)

    # ── Save ──
    final = canvas.convert("RGB")
    final.save(output_path, "PNG", optimize=True)
    return output_path
