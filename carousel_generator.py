"""
Instagram Carousel Generator for ListaPro.
Generates N slides (1080x1350 each) + ZIP archive.

Slide structure:
  1. Cover: main photo + type + price + location + badge + slide indicator
  2. Stats: property specs (bedrooms, bathrooms, m², parking) with photo bg
  3. Amenities 1: first half of amenities with photo bg + decorative layout
  4. Amenities 2: second half of amenities with photo bg + decorative layout
  5..N-1. Photo slides: extra photos with overlay + slide number
  N. Contact slide: agent info, logo, QR, CTA
"""

import zipfile
from pathlib import Path
from PIL import Image, ImageDraw
from image_helpers import (
    font, crop_to_fill, draw_gradient, make_circular, load_icon,
    extract_stats, parse_colors, render_logo, render_badge, render_qr,
    rounded_rect, hex_to_rgb,
    GENERATED_DIR, PLACEHOLDER, GOLD, WHITE, WHITE_DIM, BLACK, STAT_ICONS,
)
from labels import get_operation, get_property_type, get_label

# Canvas
W, H = 1080, 1350

# Amenity emoji mapping for visual slides
AMENITY_EMOJIS = {
    "Jardín": "🌿", "Alberca": "🏊", "Gimnasio": "🏋️", "Roof Garden": "🌇",
    "Estacionamiento Techado": "🅿️", "Pet Friendly": "🐾", "Área de Juegos": "🎮",
    "Elevador": "🛗", "Seguridad 24/7": "🔒", "Cuarto de Servicio": "🧹",
    "Bodega": "📦", "Terraza": "🌅", "Balcón": "🌄", "Vigilancia": "👮",
    "Portón Eléctrico": "🚗", "Cisterna": "💧", "Calefacción": "🔥",
    "Aire Acondicionado": "❄️", "Cocina Integral": "🍳", "Walk-in Closet": "👔",
    "Sala de Cine": "🎬", "Área de BBQ": "🥩", "Cancha de Tenis": "🎾",
    "Salón de Eventos": "🎉", "Spa": "💆", "Sauna": "♨️",
    "Jacuzzi": "🛁", "Lobby": "🏛️", "Business Center": "💼",
    "Coworking": "💻", "Kids Club": "🧒", "Pista de Jogging": "🏃",
}


# ─── Slide Generators ──────────────────────────────────────


def _slide_indicator(draw, current: int, total: int, y: int = 40):
    """Draw slide indicator dots (top-center)."""
    dot_r = 8
    gap = 12
    total_w = total * (dot_r * 2) + (total - 1) * gap
    start_x = (W - total_w) // 2

    for i in range(total):
        x = start_x + i * (dot_r * 2 + gap)
        fill = WHITE if i == current else (255, 255, 255, 100)
        draw.ellipse((x, y, x + dot_r * 2, y + dot_r * 2), fill=fill)


def _slide_cover(property_data, cover_path, accent, branding, lang, total_slides):
    """Slide 1: Cover photo with property info."""
    try:
        cover = Image.open(cover_path)
    except Exception:
        cover = Image.open(str(PLACEHOLDER))
    canvas = crop_to_fill(cover, W, H).convert("RGBA")
    canvas = draw_gradient(canvas, start_y=500, end_y=H, max_alpha=235, width=W)
    draw = ImageDraw.Draw(canvas)

    # Slide indicator
    _slide_indicator(draw, 0, total_slides)

    # Badge
    operacion_raw = str(property_data.get("operacion", "Venta"))
    badge_text = get_operation(operacion_raw, lang, uppercase=True)
    font_badge = font("DMSans-Variable.ttf", 22)
    render_badge(draw, badge_text, accent, x=40, y=80, font_obj=font_badge)

    # Logo
    canvas = render_logo(canvas, branding)
    draw = ImageDraw.Draw(canvas)

    # Heading
    font_heading = font("PlayfairDisplay-Variable.ttf", 46)
    tipo = get_property_type(property_data.get("tipo_propiedad", "Propiedad"), lang)
    op_lower = get_operation(operacion_raw, lang, uppercase=False)
    connector = get_label("heading_en", lang)
    heading = f"{tipo} {connector} {op_lower}"
    draw.text((60, 900), heading, font=font_heading, fill=WHITE)

    # Gold line
    draw.rectangle([(60, 975), (200, 978)], fill=GOLD)

    # Price
    font_price = font("DMSans-Variable.ttf", 60)
    precio = property_data.get("precio_formateado", str(property_data.get("precio", "")))
    draw.text((60, 1000), precio, font=font_price, fill=WHITE)

    # Location
    font_location = font("DMSans-Variable.ttf", 30)
    ciudad = property_data.get("ciudad", "")
    pais = property_data.get("pais_nombre", "")
    location = f"{ciudad}, {pais}" if pais else ciudad
    if location:
        draw.text((60, 1090), location, font=font_location, fill=WHITE_DIM)

    # Stats (compact row at bottom)
    font_stat_val = font("DMSans-Variable.ttf", 28)
    font_stat_lbl = font("DMSans-Variable.ttf", 18)
    stats = extract_stats(property_data, lang)
    if stats:
        icon_size = 36
        stat_x = 60
        stat_y = 1160
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

    return canvas.convert("RGB")


def _slide_photo(photo_path, slide_index, total_slides, primary):
    """Photo slide: full-bleed photo with subtle overlay + slide number."""
    try:
        photo = Image.open(photo_path)
    except Exception:
        photo = Image.open(str(PLACEHOLDER))
    canvas = crop_to_fill(photo, W, H).convert("RGBA")

    # Subtle top gradient for indicator dots
    top_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    top_draw = ImageDraw.Draw(top_overlay)
    for y in range(100):
        a = int(100 * (1 - y / 100))
        top_draw.line([(0, y), (W, y)], fill=(0, 0, 0, a))
    canvas = Image.alpha_composite(canvas, top_overlay)

    draw = ImageDraw.Draw(canvas)
    _slide_indicator(draw, slide_index, total_slides)

    return canvas.convert("RGB")


def _slide_stats(property_data, primary, accent, lang, slide_index, total_slides, bg_photo=None):
    """Stats slide: property specs ONLY (no amenities) with photo background."""
    # Use photo background with dark overlay
    if bg_photo:
        try:
            bg = Image.open(bg_photo)
            canvas = crop_to_fill(bg, W, H).convert("RGBA")
            overlay = Image.new("RGBA", (W, H), (0, 0, 0, 185))
            canvas = Image.alpha_composite(canvas, overlay)
        except Exception:
            canvas = Image.new("RGBA", (W, H), primary + (255,))
    else:
        canvas = Image.new("RGBA", (W, H), primary + (255,))
    draw = ImageDraw.Draw(canvas)

    _slide_indicator(draw, slide_index, total_slides)

    # Title
    font_title = font("PlayfairDisplay-Variable.ttf", 52)
    title = get_label("slide_stats_title", lang)
    title_bbox = draw.textbbox((0, 0), title, font=font_title)
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(((W - title_w) // 2, 140), title, font=font_title, fill=WHITE)

    # Gold separator centered
    draw.rectangle([((W - 140) // 2, 220), ((W + 140) // 2, 224)], fill=GOLD)

    # Stats with large icons — centered 2-column grid
    stats = extract_stats(property_data, lang)
    font_val = font("DMSans-Variable.ttf", 64)
    font_lbl = font("DMSans-Variable.ttf", 24)

    if stats:
        col_w = 420
        row_h = 220
        grid_w = col_w * 2 + 60
        start_x = (W - grid_w) // 2
        start_y = 300

        for i, (val, lbl, icon_key) in enumerate(stats):
            col = i % 2
            row = i // 2
            x = start_x + col * (col_w + 60)
            y = start_y + row * row_h

            # Glass card background
            card = Image.new("RGBA", (col_w, row_h - 30), (255, 255, 255, 25))
            canvas.paste(card, (x, y), card)

            # Gold top border on card
            gold_bar = Image.new("RGBA", (col_w, 4), GOLD + (200,))
            canvas.paste(gold_bar, (x, y), gold_bar)
            draw = ImageDraw.Draw(canvas)

            # Icon
            icon_size = 64
            icon_file = STAT_ICONS.get(icon_key)
            if icon_file:
                icon = load_icon(icon_file, icon_size)
                if icon:
                    canvas.paste(icon, (x + 25, y + 40), icon)
                    draw = ImageDraw.Draw(canvas)

            # Value (large)
            draw.text((x + 100, y + 25), val, font=font_val, fill=WHITE)

            # Label
            draw.text((x + 100, y + 105), lbl, font=font_lbl, fill=WHITE_DIM)

    # Property type + operation at bottom
    font_bottom = font("DMSans-Variable.ttf", 28)
    tipo = get_property_type(property_data.get("tipo_propiedad", "Propiedad"), lang)
    operacion = get_operation(property_data.get("operacion", "Venta"), lang, uppercase=False)
    connector = get_label("heading_en", lang)
    bottom_text = f"{tipo} {connector} {operacion}"
    bt_bbox = draw.textbbox((0, 0), bottom_text, font=font_bottom)
    bt_w = bt_bbox[2] - bt_bbox[0]
    draw.text(((W - bt_w) // 2, H - 160), bottom_text, font=font_bottom, fill=WHITE_DIM)

    # Price at bottom
    font_price = font("DMSans-Variable.ttf", 44)
    precio = property_data.get("precio_formateado", str(property_data.get("precio", "")))
    pr_bbox = draw.textbbox((0, 0), precio, font=font_price)
    pr_w = pr_bbox[2] - pr_bbox[0]
    draw.text(((W - pr_w) // 2, H - 110), precio, font=font_price, fill=GOLD)

    return canvas.convert("RGB")


def _slide_amenities(amenities_list, bg_photo, accent, lang, slide_index, total_slides, slide_label=""):
    """Amenities slide: attractive card layout with photo background.

    Each amenity displayed as a large pill/card with emoji + name.
    """
    # Photo background with dark overlay
    if bg_photo:
        try:
            bg = Image.open(bg_photo)
            canvas = crop_to_fill(bg, W, H).convert("RGBA")
            overlay = Image.new("RGBA", (W, H), (0, 0, 0, 180))
            canvas = Image.alpha_composite(canvas, overlay)
        except Exception:
            canvas = Image.new("RGBA", (W, H), (28, 28, 36, 255))
    else:
        canvas = Image.new("RGBA", (W, H), (28, 28, 36, 255))
    draw = ImageDraw.Draw(canvas)

    _slide_indicator(draw, slide_index, total_slides)

    # Title
    font_title = font("PlayfairDisplay-Variable.ttf", 48)
    title = get_label("amenidades", lang)
    title_bbox = draw.textbbox((0, 0), title, font=font_title)
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(((W - title_w) // 2, 100), title, font=font_title, fill=WHITE)

    # Gold separator
    draw.rectangle([((W - 140) // 2, 175), ((W + 140) // 2, 179)], fill=GOLD)

    if not amenities_list:
        return canvas.convert("RGB")

    # Layout: large amenity cards in a grid
    # Each card: glass bg + emoji + name
    font_amenity = font("DMSans-Variable.ttf", 28)
    font_emoji = font("DMSans-Variable.ttf", 40)

    card_margin = 20
    card_pad_x = 24
    card_pad_y = 20
    card_h = 90
    cols = 2
    card_w = (W - card_margin * 3) // cols  # ~347px per card

    start_y = 240
    start_x = card_margin

    for i, amenity in enumerate(amenities_list):
        col = i % cols
        row = i // cols
        x = start_x + col * (card_w + card_margin)
        y = start_y + row * (card_h + card_margin)

        if y + card_h > H - 100:
            break  # Don't overflow

        # Glass card background
        card_bg = Image.new("RGBA", (card_w, card_h), (255, 255, 255, 30))
        canvas.paste(card_bg, (x, y), card_bg)

        # Left gold accent bar
        gold_bar = Image.new("RGBA", (4, card_h), GOLD + (200,))
        canvas.paste(gold_bar, (x, y), gold_bar)
        draw = ImageDraw.Draw(canvas)

        # Emoji
        emoji = AMENITY_EMOJIS.get(amenity, "✦")
        try:
            draw.text((x + card_pad_x, y + 12), emoji, font=font_emoji, fill=WHITE)
        except Exception:
            draw.text((x + card_pad_x, y + 12), "✦", font=font_emoji, fill=GOLD)

        # Amenity name
        name_x = x + card_pad_x + 50
        # Truncate if too long
        max_name_w = card_w - card_pad_x - 60 - 10
        display_name = amenity
        name_bbox = draw.textbbox((0, 0), display_name, font=font_amenity)
        while (name_bbox[2] - name_bbox[0]) > max_name_w and len(display_name) > 8:
            display_name = display_name[:-2] + "…"
            name_bbox = draw.textbbox((0, 0), display_name, font=font_amenity)

        draw.text((name_x, y + (card_h - 30) // 2), display_name, font=font_amenity, fill=WHITE)

    # Slide label at bottom (e.g., "1/2" or "2/2")
    if slide_label:
        font_sl = font("DMSans-Variable.ttf", 22)
        sl_bbox = draw.textbbox((0, 0), slide_label, font=font_sl)
        sl_w = sl_bbox[2] - sl_bbox[0]
        draw.text(((W - sl_w) // 2, H - 70), slide_label, font=font_sl, fill=WHITE_DIM)

    return canvas.convert("RGB")


def _slide_contact(property_data, primary, accent, branding, lang, slide_index, total_slides, bg_photo=None):
    """Contact slide: agent info, logo, QR, CTA with photo background."""
    if bg_photo:
        try:
            bg = Image.open(bg_photo)
            canvas = crop_to_fill(bg, W, H).convert("RGBA")
            overlay = Image.new("RGBA", (W, H), (0, 0, 0, 185))
            canvas = Image.alpha_composite(canvas, overlay)
        except Exception:
            canvas = Image.new("RGBA", (W, H), primary + (255,))
    else:
        canvas = Image.new("RGBA", (W, H), primary + (255,))
    draw = ImageDraw.Draw(canvas)

    _slide_indicator(draw, slide_index, total_slides)

    # CTA title
    font_cta = font("PlayfairDisplay-Variable.ttf", 48)
    cta_text = get_label("slide_contact_title", lang)
    cta_bbox = draw.textbbox((0, 0), cta_text, font=font_cta)
    cta_w = cta_bbox[2] - cta_bbox[0]
    draw.text(((W - cta_w) // 2, 200), cta_text, font=font_cta, fill=WHITE)

    # Gold separator
    draw.rectangle([((W - 140) // 2, 280), ((W + 140) // 2, 284)], fill=GOLD)

    # Agent photo (large, circular, centered)
    center_y = 380
    photo_size = 200
    if branding and branding.get("agent_photo_path"):
        try:
            ap_path = GENERATED_DIR / branding["agent_photo_path"]
            if ap_path.exists():
                ap = Image.open(str(ap_path))
                circ = make_circular(ap, photo_size)
                canvas.paste(circ, ((W - photo_size) // 2, center_y), circ)
                draw = ImageDraw.Draw(canvas)
                center_y += photo_size + 30
        except Exception:
            center_y += 30
    else:
        center_y = 350

    # Agent name
    font_name = font("DMSans-Variable.ttf", 40)
    font_info = font("DMSans-Variable.ttf", 28)
    agent_name = property_data.get("agente_nombre", "")
    agent_phone = property_data.get("agente_telefono", "")
    agent_email = property_data.get("agente_email", "")
    agency = property_data.get("agencia_nombre", "")

    if agent_name:
        name_bbox = draw.textbbox((0, 0), agent_name, font=font_name)
        name_w = name_bbox[2] - name_bbox[0]
        draw.text(((W - name_w) // 2, center_y), agent_name, font=font_name, fill=WHITE)
        center_y += 55

    if agent_phone:
        phone_bbox = draw.textbbox((0, 0), agent_phone, font=font_info)
        phone_w = phone_bbox[2] - phone_bbox[0]
        draw.text(((W - phone_w) // 2, center_y), agent_phone, font=font_info, fill=WHITE_DIM)
        center_y += 42

    if agent_email:
        email_bbox = draw.textbbox((0, 0), agent_email, font=font_info)
        email_w = email_bbox[2] - email_bbox[0]
        draw.text(((W - email_w) // 2, center_y), agent_email, font=font_info, fill=WHITE_DIM)
        center_y += 42

    if agency:
        agency_bbox = draw.textbbox((0, 0), agency, font=font_info)
        agency_w = agency_bbox[2] - agency_bbox[0]
        draw.text(((W - agency_w) // 2, center_y), agency, font=font_info, fill=GOLD)
        center_y += 50

    # Logo (centered)
    if branding and branding.get("logo_path"):
        try:
            logo_full = GENERATED_DIR / branding["logo_path"]
            if logo_full.exists():
                logo = Image.open(str(logo_full)).convert("RGBA")
                max_logo_w, max_logo_h = 300, 100
                ratio = min(max_logo_w / logo.width, max_logo_h / logo.height)
                new_size = (int(logo.width * ratio), int(logo.height * ratio))
                logo = logo.resize(new_size, Image.LANCZOS)
                lx = (W - new_size[0]) // 2
                ly = center_y + 10
                canvas.paste(logo, (lx, ly), logo)
                draw = ImageDraw.Draw(canvas)
                center_y = ly + new_size[1] + 20
        except Exception:
            pass

    # QR code (centered, bottom area)
    canvas = render_qr(canvas, branding, x=(W - 140) // 2, y=max(center_y, 1050), size=140)

    # Contact label at bottom
    font_contact = font("DMSans-Variable.ttf", 22)
    contact_lbl = get_label("contacto", lang)
    draw = ImageDraw.Draw(canvas)
    lbl_bbox = draw.textbbox((0, 0), contact_lbl, font=font_contact)
    lbl_w = lbl_bbox[2] - lbl_bbox[0]
    draw.text(((W - lbl_w) // 2, H - 80), contact_lbl, font=font_contact, fill=WHITE_DIM)

    return canvas.convert("RGB")


# ─── Main Generator ────────────────────────────────────────


def generate_carousel(
    property_data: dict,
    photo_paths: list,
    output_dir: str,
    color_overrides: dict = None,
    branding: dict = None,
    lang: str = "es",
) -> dict:
    """
    Generate an Instagram carousel (multiple 1080x1350 slides) + ZIP.

    Slide order:
      1. Cover (photo 1)
      2. Stats (photo 2 as background)
      3. Amenities part 1 (photo 3 as background, or photo 2)
      4. Amenities part 2 (photo 4 as background, or photo 3)
      5+. Extra photo slides
      Last. Contact slide

    Returns:
        {"slides": [list of slide paths], "zip_path": "path/to/carousel.zip"}
    """
    primary, accent = parse_colors(color_overrides)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    cover_path = photo_paths[0] if photo_paths else str(PLACEHOLDER)

    # Collect all amenities
    amenidades = property_data.get("amenidades", [])
    if isinstance(amenidades, str):
        amenidades = [amenidades]
    otras = property_data.get("otras_amenidades", "")
    if otras:
        amenidades.extend([a.strip() for a in otras.split(",") if a.strip()])

    # Determine amenity slides needed (0, 1, or 2)
    amenity_slides_count = 0
    if len(amenidades) > 0:
        amenity_slides_count = 1 if len(amenidades) <= 6 else 2

    # Photo assignments:
    # photo_paths[0] = cover
    # photo_paths[1] = stats background (slide 2)
    # photo_paths[2] = amenity slide 1 background
    # photo_paths[3] = amenity slide 2 background
    # Remaining photos become photo gallery slides
    stats_bg = photo_paths[1] if len(photo_paths) > 1 else cover_path
    amenity_bg_1 = photo_paths[2] if len(photo_paths) > 2 else (photo_paths[1] if len(photo_paths) > 1 else cover_path)
    amenity_bg_2 = photo_paths[3] if len(photo_paths) > 3 else amenity_bg_1

    # Photos for gallery slides: everything after the ones used for backgrounds
    bg_used = min(4, len(photo_paths))  # cover + up to 3 bg photos
    gallery_photos = photo_paths[bg_used:bg_used + 4] if len(photo_paths) > bg_used else []

    # Calculate total slides
    # cover(1) + stats(1) + amenity_slides(0-2) + gallery + contact(1)
    total_slides = 1 + 1 + amenity_slides_count + len(gallery_photos) + 1

    slides = []
    slide_idx = 0

    # ── Slide 1: Cover ──
    cover_img = _slide_cover(property_data, cover_path, accent, branding, lang, total_slides)
    cover_out = str(out / "carousel_01_cover.png")
    cover_img.save(cover_out, "PNG", optimize=True)
    slides.append(cover_out)
    slide_idx += 1

    # ── Slide 2: Stats (photo background, NO amenities) ──
    stats_img = _slide_stats(property_data, primary, accent, lang, slide_idx, total_slides, bg_photo=stats_bg)
    stats_out = str(out / f"carousel_{slide_idx + 1:02d}_stats.png")
    stats_img.save(stats_out, "PNG", optimize=True)
    slides.append(stats_out)
    slide_idx += 1

    # ── Amenity slides (1 or 2) ──
    if amenity_slides_count == 1:
        am_img = _slide_amenities(
            amenidades, amenity_bg_1, accent, lang, slide_idx, total_slides,
        )
        am_out = str(out / f"carousel_{slide_idx + 1:02d}_amenities.png")
        am_img.save(am_out, "PNG", optimize=True)
        slides.append(am_out)
        slide_idx += 1
    elif amenity_slides_count == 2:
        mid = (len(amenidades) + 1) // 2
        am1 = amenidades[:mid]
        am2 = amenidades[mid:]

        am_img1 = _slide_amenities(
            am1, amenity_bg_1, accent, lang, slide_idx, total_slides,
            slide_label="1 / 2",
        )
        am_out1 = str(out / f"carousel_{slide_idx + 1:02d}_amenities1.png")
        am_img1.save(am_out1, "PNG", optimize=True)
        slides.append(am_out1)
        slide_idx += 1

        am_img2 = _slide_amenities(
            am2, amenity_bg_2, accent, lang, slide_idx, total_slides,
            slide_label="2 / 2",
        )
        am_out2 = str(out / f"carousel_{slide_idx + 1:02d}_amenities2.png")
        am_img2.save(am_out2, "PNG", optimize=True)
        slides.append(am_out2)
        slide_idx += 1

    # ── Gallery photo slides ──
    for i, photo in enumerate(gallery_photos):
        photo_img = _slide_photo(photo, slide_idx, total_slides, primary)
        photo_out = str(out / f"carousel_{slide_idx + 1:02d}_photo.png")
        photo_img.save(photo_out, "PNG", optimize=True)
        slides.append(photo_out)
        slide_idx += 1

    # ── Contact slide (last) ──
    contact_bg = gallery_photos[-1] if gallery_photos else (photo_paths[-1] if len(photo_paths) > 1 else cover_path)
    contact_img = _slide_contact(property_data, primary, accent, branding, lang, slide_idx, total_slides, bg_photo=contact_bg)
    contact_out = str(out / f"carousel_{slide_idx + 1:02d}_contact.png")
    contact_img.save(contact_out, "PNG", optimize=True)
    slides.append(contact_out)

    # ── ZIP archive ──
    zip_path = str(out / "carousel.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for slide in slides:
            zf.write(slide, Path(slide).name)

    return {"slides": slides, "zip_path": zip_path}
