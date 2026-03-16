"""
Instagram Post Image Generator for ListaPro.
Generates a 1080x1350 PNG with cover photo, property data overlay, and branding.
"""

from PIL import Image, ImageDraw
from image_helpers import (
    font, crop_to_fill, draw_gradient, make_circular, load_icon,
    extract_stats, parse_colors, render_logo, render_badge, render_qr,
    GENERATED_DIR, PLACEHOLDER, GOLD, WHITE, WHITE_DIM, STAT_ICONS,
)
from labels import get_operation, get_property_type, get_label

# Canvas
W, H = 1080, 1350


# ─── Main Generator ────────────────────────────────────────


def generate_instagram_post(
    property_data: dict,
    cover_photo_path: str,
    output_path: str,
    color_overrides: dict = None,
    branding: dict = None,
    lang: str = "es",
) -> str:
    """
    Generate a 1080x1350 Instagram post image.
    Returns output_path on success.
    """

    # ── Colors ──
    primary, accent = parse_colors(color_overrides)

    # ── Fonts ──
    font_heading = font("PlayfairDisplay-Variable.ttf", 46)
    font_price = font("DMSans-Variable.ttf", 60)
    font_location = font("DMSans-Variable.ttf", 30)
    font_stat_val = font("DMSans-Variable.ttf", 28)
    font_stat_lbl = font("DMSans-Variable.ttf", 18)
    font_badge = font("DMSans-Variable.ttf", 22)
    font_agent_name = font("DMSans-Variable.ttf", 26)
    font_agent_info = font("DMSans-Variable.ttf", 21)

    # ── Cover photo → full canvas ──
    try:
        cover = Image.open(cover_photo_path)
    except Exception:
        cover = Image.open(str(PLACEHOLDER))
    canvas = crop_to_fill(cover, W, H).convert("RGBA")

    # ── Gradient overlay (bottom 60%) ──
    canvas = draw_gradient(canvas, start_y=500, end_y=H, max_alpha=235, width=W)

    draw = ImageDraw.Draw(canvas)

    # ── Operation badge (top-left) ──
    operacion_raw = str(property_data.get("operacion", "Venta"))
    badge_text = get_operation(operacion_raw, lang, uppercase=True)
    render_badge(draw, badge_text, accent, font_obj=font_badge)

    # ── Logo (top-right) ──
    canvas = render_logo(canvas, branding)
    draw = ImageDraw.Draw(canvas)

    # ── Property heading ──
    tipo = get_property_type(property_data.get("tipo_propiedad", "Propiedad"), lang)
    op_lower = get_operation(operacion_raw, lang, uppercase=False)
    connector = get_label("heading_en", lang)
    heading = f"{tipo} {connector} {op_lower}"
    draw.text((60, 830), heading, font=font_heading, fill=WHITE)

    # ── Gold separator line ──
    draw.rectangle([(60, 905), (200, 908)], fill=GOLD)

    # ── Price ──
    precio = property_data.get("precio_formateado", "")
    if not precio:
        precio = str(property_data.get("precio", ""))
    draw.text((60, 930), precio, font=font_price, fill=WHITE)

    # ── Location ──
    ciudad = property_data.get("ciudad", "")
    pais = property_data.get("pais_nombre", "")
    location = f"{ciudad}, {pais}" if pais else ciudad
    if location:
        draw.text((60, 1015), location, font=font_location, fill=WHITE_DIM)

    # ── Stats row with icons ──
    stats = extract_stats(property_data, lang)
    if stats:
        icon_size = 36
        stat_x = 60
        stat_y = 1080

        for val, lbl, icon_key in stats:
            icon_file = STAT_ICONS.get(icon_key)
            if icon_file:
                icon = load_icon(icon_file, icon_size)
                if icon:
                    canvas.paste(icon, (stat_x, stat_y), icon)
                    draw = ImageDraw.Draw(canvas)

            text_x = stat_x + icon_size + 8
            draw.text((text_x, stat_y + 2), val, font=font_stat_val, fill=WHITE)
            val_bbox = draw.textbbox((0, 0), val, font=font_stat_val)
            val_w = val_bbox[2] - val_bbox[0]

            draw.text((text_x, stat_y + 30), lbl, font=font_stat_lbl, fill=WHITE_DIM)

            stat_x += icon_size + 8 + max(val_w, 50) + 40

    # ── Footer dark bar ──
    footer_y = 1190
    footer_overlay = Image.new("RGBA", (W, H - footer_y), (0, 0, 0, 200))
    canvas.paste(footer_overlay, (0, footer_y), footer_overlay)
    draw = ImageDraw.Draw(canvas)

    # Thin gold line at footer top
    draw.rectangle([(0, footer_y), (W, footer_y + 3)], fill=GOLD + (180,))

    # ── Agent info in footer ──
    agent_name = property_data.get("agente_nombre", "")
    agent_phone = property_data.get("agente_telefono", "")
    agency = property_data.get("agencia_nombre", "")
    text_start_x = 60
    text_y = footer_y + 30

    # Agent photo (circular)
    if branding and branding.get("agent_photo_path"):
        try:
            ap_path = GENERATED_DIR / branding["agent_photo_path"]
            if ap_path.exists():
                ap = Image.open(str(ap_path))
                circ = make_circular(ap, 100)
                canvas.paste(circ, (50, footer_y + 25), circ)
                draw = ImageDraw.Draw(canvas)
                text_start_x = 170
        except Exception:
            pass

    if agent_name:
        draw.text((text_start_x, text_y), agent_name, font=font_agent_name, fill=WHITE)
        text_y += 35
    if agent_phone:
        draw.text((text_start_x, text_y), agent_phone, font=font_agent_info, fill=WHITE_DIM)
        text_y += 30
    if agency:
        draw.text((text_start_x, text_y), agency, font=font_agent_info, fill=WHITE_DIM)

    # ── QR code (footer right) ──
    canvas = render_qr(canvas, branding, x=W - 110 - 50, y=footer_y + 25)

    # ── Save ──
    final = canvas.convert("RGB")
    final.save(output_path, "PNG", optimize=True)
    return output_path
