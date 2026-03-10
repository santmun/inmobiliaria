import tempfile
import qrcode
from pathlib import Path
from fpdf import FPDF
from PIL import Image

BASE_DIR = Path(__file__).parent
GENERATED_DIR = BASE_DIR / "generated"


class ListaProPDF(FPDF):
    """Custom PDF class for professional real estate listings."""

    def __init__(self):
        super().__init__("P", "mm", "A4")
        self.set_auto_page_break(auto=False)

        # Colors
        self.PRIMARY = (26, 54, 93)       # #1a365d
        self.ACCENT = (229, 62, 62)       # #e53e3e
        self.TEXT_DARK = (45, 55, 72)      # #2d3748
        self.TEXT_LIGHT = (113, 128, 150)  # #718096
        self.BG_LIGHT = (247, 250, 252)    # #f7fafc
        self.BORDER = (226, 232, 240)      # #e2e8f0
        self.WHITE = (255, 255, 255)
        self.STAT_BG = (26, 54, 93)


def resize_photo(photo_path: str, max_width: int = 1200) -> str:
    """Resize photo if too large."""
    try:
        img = Image.open(photo_path)
        if img.mode == "RGBA":
            img = img.convert("RGB")
        if img.width > max_width:
            ratio = max_width / img.width
            new_size = (max_width, int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
            resized_path = Path(photo_path).parent / f"r_{Path(photo_path).name}"
            if not str(resized_path).lower().endswith((".jpg", ".jpeg")):
                resized_path = resized_path.with_suffix(".jpg")
            img.save(str(resized_path), "JPEG", quality=85)
            return str(resized_path)
        elif img.mode != "RGB":
            converted = Path(photo_path).parent / f"c_{Path(photo_path).stem}.jpg"
            img.save(str(converted), "JPEG", quality=85)
            return str(converted)
    except Exception:
        pass
    return photo_path


def crop_to_fill(photo_path: str, target_w_mm: float, target_h_mm: float, prefix: str = "gal") -> str:
    """Crop photo to fill target aspect ratio (cover mode), center-cropped."""
    try:
        img = Image.open(photo_path)
        if img.mode == "RGBA":
            img = img.convert("RGB")
        target_ratio = target_w_mm / target_h_mm
        img_ratio = img.width / img.height

        if img_ratio > target_ratio:
            new_w = int(img.height * target_ratio)
            left = (img.width - new_w) // 2
            img = img.crop((left, 0, left + new_w, img.height))
        else:
            new_h = int(img.width / target_ratio)
            top = (img.height - new_h) // 3  # slight top bias
            top = max(0, min(top, img.height - new_h))
            img = img.crop((0, top, img.width, top + new_h))

        cropped_path = Path(photo_path).parent / f"{prefix}_{Path(photo_path).stem}.jpg"
        img.save(str(cropped_path), "JPEG", quality=85)
        return str(cropped_path)
    except Exception:
        return photo_path


# ──────────────────────────────────────────────────────────
# Shared helpers
# ──────────────────────────────────────────────────────────

def _extract_stats(property_data: dict) -> list:
    """Extract stats list from property data."""
    stats = []
    rec = property_data.get("recamaras", "0")
    if rec and rec != "0":
        stats.append((rec, "Recámaras"))
    ban = property_data.get("banos", "0")
    if ban and ban != "0":
        stats.append((ban, "Baños"))
    m2c = property_data.get("m2_construidos", "")
    if m2c:
        stats.append((m2c, "m² Constr."))
    m2t = property_data.get("m2_terreno", "")
    if m2t:
        stats.append((m2t, "m² Terreno"))
    est = property_data.get("estacionamientos", "0")
    if est and est != "0":
        stats.append((est, "Estac."))
    return stats


def _generate_qr_image(url: str) -> str:
    """Generate a QR code PNG and return its temp file path."""
    qr = qrcode.QRCode(version=1, box_size=10, border=1)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img.save(tmp.name)
    return tmp.name


def _render_logo(pdf, branding, x, y, max_w, max_h, bg=True):
    """Render branding logo at given position, fitting within max dimensions."""
    if not branding or not branding.get("logo_path"):
        return
    logo_path = GENERATED_DIR / branding["logo_path"]
    if not logo_path.exists():
        return
    try:
        img = Image.open(str(logo_path))
        iw, ih = img.size
        aspect = iw / ih
        w, h = max_w, max_w / aspect
        if h > max_h:
            h = max_h
            w = max_h * aspect
        actual_x = x + (max_w - w)
        if bg:
            pdf.set_fill_color(255, 255, 255)
            pdf.rect(actual_x - 2, y - 1, w + 4, h + 2, "F")
        pdf.image(str(logo_path), x=actual_x, y=y, w=w, h=h)
    except Exception:
        pass


def _render_footer(pdf, property_data: dict, footer_y: float = 275, branding=None):
    """Render contact footer bar (shared by both templates)."""
    agencia = property_data.get("agencia_nombre", "")
    tel = property_data.get("agente_telefono", "")
    email = property_data.get("agente_email", "")
    contact_str = tel
    if email:
        contact_str += f"  |  {email}"

    pdf.set_fill_color(*pdf.BG_LIGHT)
    pdf.rect(0, footer_y, 210, 22, "F")
    pdf.set_draw_color(*pdf.PRIMARY)
    pdf.set_line_width(0.5)
    pdf.line(0, footer_y, 210, footer_y)

    # Agent photo (if available)
    text_x = 15
    if branding and branding.get("agent_photo_path"):
        photo_path = GENERATED_DIR / branding["agent_photo_path"]
        if photo_path.exists():
            try:
                pdf.image(str(photo_path), x=15, y=footer_y + 3, w=16, h=16)
                text_x = 34
            except Exception:
                pass

    pdf.set_text_color(*pdf.PRIMARY)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_xy(text_x, footer_y + 3)
    pdf.cell(100, 5, property_data.get("agente_nombre", ""))

    if agencia:
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*pdf.TEXT_LIGHT)
        pdf.set_xy(text_x, footer_y + 8.5)
        pdf.cell(100, 5, agencia)

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*pdf.TEXT_DARK)
    pdf.set_xy(text_x, footer_y + 14)
    pdf.cell(100, 4, contact_str)

    # QR code (if enabled)
    qr_rendered = False
    if branding and branding.get("qr_enabled") and branding.get("qr_url"):
        try:
            qr_path = _generate_qr_image(branding["qr_url"])
            pdf.image(qr_path, x=178, y=footer_y + 1, w=18, h=18)
            qr_rendered = True
            Path(qr_path).unlink(missing_ok=True)
        except Exception:
            pass

    pdf.set_text_color(*pdf.TEXT_LIGHT)
    pdf.set_font("Helvetica", "I", 7)
    if qr_rendered:
        pdf.set_xy(120, footer_y + 14)
        pdf.cell(55, 4, "Generado con ListaPro", align="R")
    else:
        pdf.set_xy(140, footer_y + 14)
        pdf.cell(55, 4, "Generado con ListaPro", align="R")


def _render_amenities(pdf, amenidades: list, start_y: float):
    """Render amenities section (shared by both templates)."""
    if not amenidades:
        return
    am_y = start_y
    if am_y > 250:
        am_y = 250
    pdf.set_text_color(*pdf.PRIMARY)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_xy(15, am_y)
    pdf.cell(180, 7, "Amenidades", ln=True)
    pdf.set_draw_color(*pdf.BORDER)
    pdf.line(15, am_y + 8, 195, am_y + 8)

    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*pdf.TEXT_DARK)
    tag_x = 15
    tag_y = am_y + 12
    for amenity in amenidades:
        tag_w = pdf.get_string_width(amenity) + 6
        if tag_x + tag_w > 195:
            tag_x = 15
            tag_y += 8
        if tag_y > 265:
            break
        pdf.set_fill_color(237, 242, 247)
        pdf.rect(tag_x, tag_y, tag_w, 6.5, "F")
        pdf.set_xy(tag_x, tag_y + 0.5)
        pdf.cell(tag_w, 5.5, amenity, align="C")
        tag_x += tag_w + 3


def _render_gallery_page(pdf, photos: list, property_data: dict, grid_uniform: bool = False, branding=None):
    """Render page 2: gallery + specs table."""
    pdf.add_page()

    tipo = property_data.get("tipo_propiedad", "")
    operacion = property_data.get("operacion", "")
    precio_fmt = property_data.get("precio_formateado", "")
    ciudad = property_data.get("ciudad", "")
    pais_nombre = property_data.get("pais_nombre", "")
    location = f"{ciudad}, {pais_nombre}" if pais_nombre else ciudad

    # Title
    pdf.set_text_color(*pdf.PRIMARY)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_xy(15, 15)
    pdf.cell(180, 8, "Galería de Fotos")
    pdf.set_draw_color(*pdf.BORDER)
    pdf.line(15, 24, 195, 24)

    gallery_photos = photos[1:7]  # Up to 6 additional
    photo_y = 28

    if grid_uniform:
        # Uniform 2×3 grid: each 88mm × 55mm
        col_w = 88
        row_h = 55
        for i, photo in enumerate(gallery_photos):
            col = i % 2
            row = i // 2
            x = 15 + col * (col_w + 4)
            y = photo_y + row * (row_h + 3)
            try:
                cropped = crop_to_fill(photo, col_w, row_h, f"gu{i}")
                pdf.image(cropped, x=x, y=y, w=col_w, h=row_h)
            except Exception:
                pass
        rows_used = (len(gallery_photos) + 1) // 2
        photo_y = photo_y + rows_used * (row_h + 3)
    else:
        # Classic: 1 large + 2-col grid
        if len(gallery_photos) >= 1:
            try:
                cropped = crop_to_fill(gallery_photos[0], 180, 70, "gl")
                pdf.image(cropped, x=15, y=photo_y, w=180, h=70)
            except Exception:
                pass
            photo_y += 73

        col_w = 88
        for i, photo in enumerate(gallery_photos[1:], 1):
            col = (i - 1) % 2
            x = 15 + col * (col_w + 4)
            try:
                cropped = crop_to_fill(photo, col_w, 55, f"gt{i}")
                pdf.image(cropped, x=x, y=photo_y, w=col_w, h=55)
            except Exception:
                pass
            if col == 1:
                photo_y += 58
        if (len(gallery_photos) - 1) % 2 == 1:
            photo_y += 58

    # Specs table
    specs_y = min(photo_y + 5, 200)
    pdf.set_text_color(*pdf.PRIMARY)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_xy(15, specs_y)
    pdf.cell(180, 7, "Especificaciones")
    pdf.set_draw_color(*pdf.BORDER)
    pdf.line(15, specs_y + 8, 195, specs_y + 8)

    rec = property_data.get("recamaras", "0")
    ban = property_data.get("banos", "0")
    m2c = property_data.get("m2_construidos", "")
    m2t = property_data.get("m2_terreno", "")
    est = property_data.get("estacionamientos", "0")

    specs = [
        ("Tipo de propiedad", tipo),
        ("Operación", operacion),
        ("Precio", precio_fmt),
        ("Ubicación", location),
    ]
    direccion = property_data.get("direccion", "")
    if direccion:
        specs.append(("Dirección", direccion))
    if rec and rec != "0":
        specs.append(("Recámaras", rec))
    if ban and ban != "0":
        specs.append(("Baños", ban))
    if m2c:
        specs.append(("Superficie construida", f"{m2c} m²"))
    if m2t:
        specs.append(("Superficie terreno", f"{m2t} m²"))
    if est and est != "0":
        specs.append(("Estacionamientos", est))
    pisos = property_data.get("pisos", "1")
    if pisos and pisos != "1":
        specs.append(("Pisos / Niveles", pisos))

    row_y = specs_y + 11
    for label, value in specs:
        if row_y > 265:
            break
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(*pdf.PRIMARY)
        pdf.set_xy(15, row_y)
        pdf.cell(70, 6, label)
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(*pdf.TEXT_DARK)
        pdf.set_xy(85, row_y)
        pdf.cell(110, 6, str(value))
        pdf.set_draw_color(*pdf.BORDER)
        pdf.line(15, row_y + 7, 195, row_y + 7)
        row_y += 8

    _render_footer(pdf, property_data, branding=branding)


# ──────────────────────────────────────────────────────────
# Variante A — Clásico
# ──────────────────────────────────────────────────────────

def _render_clasico(pdf, property_data: dict, photos: list, branding=None):
    """Render classic template: full-bleed hero, gradient overlay, stats bar."""
    pdf.add_page()

    HERO_W_MM = 210
    HERO_H_MM = 140
    main_photo = photos[0] if photos else str(BASE_DIR / "static" / "placeholder-house.jpg")

    # Hero photo (full-bleed, crop to fill)
    try:
        img = Image.open(main_photo)
        if img.mode == "RGBA":
            img = img.convert("RGB")
        img_w, img_h = img.size
        target_ratio = HERO_W_MM / HERO_H_MM
        img_ratio = img_w / img_h
        if img_ratio > target_ratio:
            new_w = int(img_h * target_ratio)
            left = (img_w - new_w) // 2
            img = img.crop((left, 0, left + new_w, img_h))
        else:
            new_h = int(img_w / target_ratio)
            top = min((img_h - new_h) // 4, img_h - new_h)
            img = img.crop((0, top, img_w, top + new_h))
        cropped_path = Path(main_photo).parent / f"hero_{Path(main_photo).stem}.jpg"
        img.save(str(cropped_path), "JPEG", quality=90)
        display_h = HERO_H_MM
        pdf.image(str(cropped_path), x=0, y=0, w=HERO_W_MM, h=HERO_H_MM)
    except Exception:
        display_h = HERO_H_MM
        pdf.set_fill_color(*pdf.BG_LIGHT)
        pdf.rect(0, 0, HERO_W_MM, display_h, "F")

    # Dark gradient overlay
    for i in range(40):
        y_pos = display_h - 40 + i
        if y_pos > 0:
            pdf.set_fill_color(0, 0, 0)
            pdf.rect(0, y_pos, 210, 1, "F")

    # Operation badge
    operacion = property_data.get("operacion", "Venta").upper()
    pdf.set_fill_color(*pdf.ACCENT)
    pdf.set_text_color(*pdf.WHITE)
    pdf.set_font("Helvetica", "B", 11)
    badge_w = pdf.get_string_width(operacion) + 10
    pdf.rect(12, 12, badge_w, 9, "F")
    pdf.set_xy(12, 12.5)
    pdf.cell(badge_w, 8, operacion, align="C")

    # Property type badge
    tipo = property_data.get("tipo_propiedad", "")
    pdf.set_fill_color(*pdf.WHITE)
    pdf.set_text_color(*pdf.PRIMARY)
    pdf.set_font("Helvetica", "B", 9)
    type_w = pdf.get_string_width(tipo) + 8
    pdf.rect(210 - 12 - type_w, 12, type_w, 8, "F")
    pdf.set_xy(210 - 12 - type_w, 12.5)
    pdf.cell(type_w, 7, tipo, align="C")

    # Logo over hero (upper-right, white background)
    _render_logo(pdf, branding, x=160, y=5, max_w=35, max_h=12, bg=True)

    # Price on hero
    precio_fmt = property_data.get("precio_formateado", "")
    pdf.set_text_color(*pdf.WHITE)
    pdf.set_font("Helvetica", "B", 26)
    pdf.set_xy(15, display_h - 28)
    pdf.cell(180, 12, precio_fmt)

    # Location on hero
    ciudad = property_data.get("ciudad", "")
    pais_nombre = property_data.get("pais_nombre", "")
    location = f"{ciudad}, {pais_nombre}" if pais_nombre else ciudad
    pdf.set_font("Helvetica", "", 12)
    pdf.set_xy(15, display_h - 17)
    pdf.cell(180, 8, location)

    # Stats bar
    stats_y = display_h
    pdf.set_fill_color(*pdf.STAT_BG)
    pdf.rect(0, stats_y, 210, 22, "F")

    stats = _extract_stats(property_data)
    if stats:
        stat_width = 180 / len(stats)
        start_x = 15
        for i, (value, label) in enumerate(stats):
            x = start_x + i * stat_width
            pdf.set_text_color(*pdf.WHITE)
            pdf.set_font("Helvetica", "B", 16)
            pdf.set_xy(x, stats_y + 2)
            pdf.cell(stat_width, 9, str(value), align="C")
            pdf.set_font("Helvetica", "", 7)
            pdf.set_xy(x, stats_y + 12)
            pdf.cell(stat_width, 5, label, align="C")

    # Description
    desc_y = stats_y + 26
    pdf.set_text_color(*pdf.PRIMARY)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_xy(15, desc_y)
    pdf.cell(180, 8, "Descripción", ln=True)
    pdf.set_draw_color(*pdf.BORDER)
    pdf.line(15, desc_y + 9, 195, desc_y + 9)

    descripcion = property_data.get("descripcion", "")
    pdf.set_text_color(*pdf.TEXT_DARK)
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_xy(15, desc_y + 13)
    pdf.multi_cell(180, 5.5, descripcion, align="J")

    # Amenities
    amenidades = property_data.get("amenidades", [])
    if isinstance(amenidades, str):
        amenidades = [amenidades]
    otras = property_data.get("otras_amenidades", "")
    if otras:
        amenidades.extend([a.strip() for a in otras.split(",") if a.strip()])
    _render_amenities(pdf, amenidades, pdf.get_y() + 8)

    # Footer
    _render_footer(pdf, property_data, branding=branding)

    # Page 2: Gallery
    if len(photos) > 1:
        _render_gallery_page(pdf, photos, property_data, grid_uniform=False, branding=branding)


# ──────────────────────────────────────────────────────────
# Variante B — Moderno
# ──────────────────────────────────────────────────────────

def _render_moderno(pdf, property_data: dict, photos: list, branding=None):
    """Render modern template: clean white, header bar, centered photo, card stats."""
    pdf.add_page()

    tipo = property_data.get("tipo_propiedad", "")
    operacion = property_data.get("operacion", "Venta").upper()
    precio_fmt = property_data.get("precio_formateado", "")
    ciudad = property_data.get("ciudad", "")
    pais_nombre = property_data.get("pais_nombre", "")
    location = f"{ciudad}, {pais_nombre}" if pais_nombre else ciudad

    # ── Header bar ──
    pdf.set_fill_color(*pdf.PRIMARY)
    pdf.rect(0, 0, 210, 18, "F")
    pdf.set_text_color(*pdf.WHITE)
    pdf.set_font("Helvetica", "B", 12)
    header_text = f"{tipo}  •  {operacion}"
    pdf.set_xy(15, 4)
    pdf.cell(180, 10, header_text, align="C")

    # Logo in header (right side, no white bg since header is dark)
    _render_logo(pdf, branding, x=160, y=2, max_w=35, max_h=14, bg=False)

    # Thin accent line under header
    pdf.set_fill_color(*pdf.ACCENT)
    pdf.rect(0, 18, 210, 1.5, "F")

    # ── Main photo with margins ──
    PHOTO_W = 180
    PHOTO_H = 90
    photo_x = 15
    photo_y = 24
    main_photo = photos[0] if photos else str(BASE_DIR / "static" / "placeholder-house.jpg")

    try:
        cropped = crop_to_fill(main_photo, PHOTO_W, PHOTO_H, "mod_hero")
        pdf.image(cropped, x=photo_x, y=photo_y, w=PHOTO_W, h=PHOTO_H)
    except Exception:
        pdf.set_fill_color(*pdf.BG_LIGHT)
        pdf.rect(photo_x, photo_y, PHOTO_W, PHOTO_H, "F")

    # ── Accent divider line ──
    line_y = photo_y + PHOTO_H + 5
    pdf.set_fill_color(*pdf.ACCENT)
    pdf.rect(75, line_y, 60, 1, "F")

    # ── Price (large, centered) ──
    price_y = line_y + 5
    pdf.set_text_color(*pdf.PRIMARY)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_xy(15, price_y)
    pdf.cell(180, 12, precio_fmt, align="C")

    # ── Location (centered, lighter) ──
    loc_y = price_y + 13
    pdf.set_text_color(*pdf.TEXT_LIGHT)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_xy(15, loc_y)
    pdf.cell(180, 6, location, align="C")

    # ── Stats cards ──
    stats = _extract_stats(property_data)
    if stats:
        stats_y = loc_y + 12
        num_stats = len(stats)
        card_w = 42
        total_w = num_stats * card_w + (num_stats - 1) * 4
        start_x = (210 - total_w) / 2

        for i, (value, label) in enumerate(stats):
            x = start_x + i * (card_w + 4)
            # Card background
            pdf.set_fill_color(*pdf.BG_LIGHT)
            pdf.rect(x, stats_y, card_w, 24, "F")
            # Thin top accent
            pdf.set_fill_color(*pdf.ACCENT)
            pdf.rect(x, stats_y, card_w, 1, "F")
            # Value
            pdf.set_text_color(*pdf.PRIMARY)
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_xy(x, stats_y + 3)
            pdf.cell(card_w, 8, str(value), align="C")
            # Label
            pdf.set_text_color(*pdf.TEXT_LIGHT)
            pdf.set_font("Helvetica", "", 7)
            pdf.set_xy(x, stats_y + 14)
            pdf.cell(card_w, 5, label, align="C")

        content_y = stats_y + 30
    else:
        content_y = loc_y + 14

    # ── Description with accent left border ──
    desc_y = content_y + 2
    descripcion = property_data.get("descripcion", "")

    pdf.set_text_color(*pdf.PRIMARY)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_xy(15, desc_y)
    pdf.cell(180, 7, "Descripción", ln=True)

    # Accent left border
    pdf.set_fill_color(*pdf.ACCENT)
    desc_text_y = desc_y + 10
    pdf.rect(15, desc_text_y, 2, 20, "F")

    pdf.set_text_color(*pdf.TEXT_DARK)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_xy(20, desc_text_y + 1)
    pdf.multi_cell(175, 5, descripcion, align="J")

    # ── Amenities ──
    amenidades = property_data.get("amenidades", [])
    if isinstance(amenidades, str):
        amenidades = [amenidades]
    otras = property_data.get("otras_amenidades", "")
    if otras:
        amenidades.extend([a.strip() for a in otras.split(",") if a.strip()])

    current_y = pdf.get_y() + 6
    if current_y < 245:
        _render_amenities(pdf, amenidades, current_y)

    # Footer
    _render_footer(pdf, property_data, branding=branding)

    # Page 2: Gallery (uniform grid)
    if len(photos) > 1:
        _render_gallery_page(pdf, photos, property_data, grid_uniform=True, branding=branding)


# ──────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────

def generate_pdf(property_data: dict, photo_paths: list, output_path: str, color_overrides=None, template="clasico", branding=None) -> str:
    """Generate a professional PDF listing with selected template variant."""
    pdf = ListaProPDF()

    # Apply color overrides if provided
    if color_overrides:
        from template_settings import hex_to_rgb
        if "color_primary" in color_overrides:
            rgb = hex_to_rgb(color_overrides["color_primary"])
            pdf.PRIMARY = rgb
            pdf.STAT_BG = rgb
        if "color_accent" in color_overrides:
            pdf.ACCENT = hex_to_rgb(color_overrides["color_accent"])

    # Process photos
    photos = [resize_photo(p) for p in photo_paths]

    # Route to template renderer
    if template == "moderno":
        _render_moderno(pdf, property_data, photos, branding=branding)
    else:
        _render_clasico(pdf, property_data, photos, branding=branding)

    pdf.output(output_path)
    return output_path
