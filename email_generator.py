"""
Email HTML generator for ListaPro.
Creates luxury responsive HTML email templates for property listings.
"""

import base64
from pathlib import Path
from labels import get_label, get_operation, get_property_type


# Amenity → emoji mapping
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

# Email-specific labels per language
_EMAIL_LABELS = {
    "salutation": {"es": "Estimado cliente,", "en": "Dear client,"},
    "advisor": {"es": "Su asesor", "en": "Your advisor"},
    "cta": {"es": "Solicitar Información", "en": "Request Information"},
    "cta_hint": {"es": "Respuesta garantizada en menos de 24 horas", "en": "Guaranteed response within 24 hours"},
    "footer": {"es": "Generado con", "en": "Generated with"},
    "footer_rights": {"es": "Todos los derechos reservados", "en": "All rights reserved"},
    "en_venta": {"es": "En Venta", "en": "For Sale"},
    "en_renta": {"es": "En Renta", "en": "For Rent"},
    "en_renta_temporal": {"es": "En Renta Temporal", "en": "Short-Term Rental"},
}


def _el(key: str, lang: str = "es") -> str:
    entry = _EMAIL_LABELS.get(key, {})
    return entry.get(lang, entry.get("es", key))


def _op_badge(operacion: str, lang: str = "es") -> str:
    op_map = {
        "Venta": "en_venta",
        "Renta": "en_renta",
        "Renta Temporal": "en_renta_temporal",
    }
    return _el(op_map.get(operacion, "en_venta"), lang)


def _image_to_base64_data_url(image_path: str, max_width: int = 600) -> str:
    """Convert an image to a base64 data URL for email embedding."""
    p = Path(image_path)
    if not p.exists():
        return ""
    try:
        from PIL import Image
        import io
        img = Image.open(str(p))
        if img.width > max_width:
            ratio = max_width / img.width
            new_h = int(img.height * ratio)
            img = img.resize((max_width, new_h), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{b64}"
    except Exception:
        return ""


def generate_email_html(
    property_data: dict,
    ai_copy: dict,
    cover_image_path: str = "",
    agent_name: str = "",
    agent_phone: str = "",
    agency_name: str = "",
    lang: str = "es",
) -> dict:
    """Generate a luxury responsive HTML email for the property listing.

    Returns:
        {"html": str, "subject": str, "preview_text": str}
    """
    # ── Parse AI copy for subject and body ──
    copy_email = ai_copy.get("copy_email", "")
    subject = ""
    body_text = copy_email

    if copy_email.startswith("Asunto:") or copy_email.startswith("Subject:"):
        lines = copy_email.split("\n", 1)
        subject = lines[0].split(":", 1)[1].strip()
        body_text = lines[1].strip() if len(lines) > 1 else ""
    elif "\n" in copy_email:
        lines = copy_email.split("\n", 1)
        subject = lines[0].strip()
        body_text = lines[1].strip() if len(lines) > 1 else ""

    tipo = property_data.get("tipo_propiedad", "Propiedad")
    tipo_translated = get_property_type(tipo, lang)
    operacion = property_data.get("operacion", "Venta")
    ciudad = property_data.get("ciudad", "")
    direccion = property_data.get("direccion", "")
    precio_fmt = property_data.get("precio_formateado", "")
    recamaras = property_data.get("recamaras", "")
    banos = property_data.get("banos", "")
    m2 = property_data.get("m2_construidos", "")
    estacionamientos = property_data.get("estacionamientos", "")
    amenidades = property_data.get("amenidades", [])

    # Build subject if not from AI
    if not subject:
        prep = "in" if lang == "en" else "en"
        subject = f"{tipo_translated} {prep} {ciudad} · {precio_fmt}"

    # ── Body paragraphs ──
    body_paragraphs_html = ""
    paragraphs = [p.strip() for p in body_text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [body_text] if body_text else []
    for p in paragraphs:
        body_paragraphs_html += f'<p style="font-family:\'Jost\',Arial,sans-serif;font-size:15px;font-weight:300;line-height:1.75;color:#3a3a3a;margin:0 0 16px;">{p}</p>\n'

    # ── Preheader ──
    preheader = f"{tipo_translated} · {ciudad} · {precio_fmt}"

    # ── Stats labels ──
    lbl_rec = get_label("recamaras_full", lang)
    lbl_ban = get_label("banos_full", lang)
    lbl_m2 = "m² Const." if lang == "es" else "Sq m Built"
    lbl_est = get_label("estacionamientos", lang)

    # ── Stats cells ──
    stats_cells = ""
    stats_data = []
    if recamaras and str(recamaras) != "0":
        stats_data.append((recamaras, lbl_rec))
    if banos and str(banos) != "0":
        stats_data.append((banos, lbl_ban))
    if m2:
        stats_data.append((m2, lbl_m2))
    if estacionamientos and str(estacionamientos) != "0":
        stats_data.append((estacionamientos, lbl_est))

    width_pct = f"{100 // max(len(stats_data), 1)}%" if stats_data else "25%"
    for i, (val, label) in enumerate(stats_data):
        border = 'border-right:1px solid rgba(255,255,255,0.07);' if i < len(stats_data) - 1 else ''
        stats_cells += f'''<td width="{width_pct}" style="text-align:center;padding:18px 8px;{border}">
                                            <span style="display:block;font-family:'Cormorant Garamond',Georgia,serif;font-size:28px;font-weight:700;color:#faf8f4;line-height:1;">{val}</span>
                                            <span style="display:block;font-family:'Jost',Arial,sans-serif;font-size:9px;font-weight:500;letter-spacing:1.5px;text-transform:uppercase;color:#b8943f;margin-top:5px;">{label}</span>
                                        </td>\n'''

    # ── Amenity pills ──
    amenity_pills = ""
    if amenidades:
        for am in amenidades[:8]:
            emoji = AMENITY_EMOJIS.get(am, "✦")
            amenity_pills += f'<span style="display:inline-block;margin:0 6px 8px 0;padding:7px 14px;background:#f0ece4;border:1px solid #d9d0bc;font-family:\'Jost\',Arial,sans-serif;font-size:10px;font-weight:500;letter-spacing:1px;text-transform:uppercase;color:#5a4e36;">{emoji} {am}</span>\n'

    amenities_section = ""
    if amenity_pills:
        amenities_label = get_label("amenidades", lang)
        amenities_section = f'''<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin:0 0 8px;">
                                    <tr>
                                        <td>
                                            <p style="font-family:'Jost',Arial,sans-serif;font-size:9px;font-weight:600;letter-spacing:2px;text-transform:uppercase;color:#b8943f;margin:0 0 12px;">{amenities_label}</p>
                                            {amenity_pills}
                                        </td>
                                    </tr>
                                </table>'''

    # ── Operation badge ──
    badge_text = _op_badge(operacion, lang)

    # ── Price split (number + currency) ──
    # Try to extract currency suffix
    price_parts = precio_fmt.rsplit(" ", 1) if precio_fmt else ["", ""]
    if len(price_parts) == 2 and len(price_parts[1]) <= 4:
        price_number = price_parts[0]
        price_currency = price_parts[1]
    else:
        price_number = precio_fmt
        price_currency = ""

    price_currency_html = f' <span style="font-size:14px;font-weight:300;letter-spacing:1px;">{price_currency}</span>' if price_currency else ""

    # ── Location line ──
    location_line = ciudad
    if direccion:
        location_line = f"{ciudad} &nbsp;·&nbsp; {direccion}"

    # ── Hero title ──
    prep = "in" if lang == "en" else "en"
    hero_title = f"{tipo_translated} {prep} {ciudad}"

    # ── Agent block ──
    agent_initial = agent_name[0].upper() if agent_name else "A"
    agent_block = ""
    if agent_name or agent_phone:
        advisor_label = _el("advisor", lang)
        phone_html = f'<a href="tel:{agent_phone}" style="font-family:\'Jost\',Arial,sans-serif;font-size:14px;font-weight:400;color:#b8943f;text-decoration:none;letter-spacing:0.3px;">{agent_phone}</a>' if agent_phone else ""
        agent_block = f'''<tr>
                            <td style="padding:0 36px 36px;background:#faf8f4;">
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="padding:20px 24px;background:#f0ece4;border-left:3px solid #b8943f;">
                                    <tr>
                                        <td>
                                            <p style="font-family:'Jost',Arial,sans-serif;font-size:9px;font-weight:600;letter-spacing:2px;text-transform:uppercase;color:#b8943f;margin:0 0 8px;">{advisor_label}</p>
                                            <p style="font-family:'Cormorant Garamond',Georgia,serif;font-size:20px;font-weight:600;color:#1c1c24;margin:0 0 6px;">{agent_name}</p>
                                            {phone_html}
                                        </td>
                                        <td align="right" valign="middle">
                                            <div style="width:44px;height:44px;background:#1c1c24;border-radius:50%;display:inline-block;text-align:center;line-height:44px;font-family:'Cormorant Garamond',Georgia,serif;font-size:20px;font-weight:700;color:#b8943f;">{agent_initial}</div>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>'''

    # ── CTA ──
    cta_text = _el("cta", lang)
    cta_hint = _el("cta_hint", lang)
    mailto_subject = f"{tipo_translated} {prep} {ciudad}".replace(" ", "%20")
    cta_href = f"mailto:{agent_phone}?subject={mailto_subject}" if agent_phone else "#"

    # ── Footer ──
    footer_gen = _el("footer", lang)
    footer_rights = _el("footer_rights", lang)

    # ── Salutation ──
    salutation = _el("salutation", lang)

    # ── Build full HTML ──
    html = f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
    <!--[if mso]>
    <style type="text/css">
        body, table, td {{ font-family: Georgia, 'Times New Roman', serif !important; }}
        .btn-gold {{ background: #b8943f !important; }}
    </style>
    <![endif]-->
</head>
<body style="margin:0;padding:0;background-color:#ede8e0;font-family:'Jost',Georgia,sans-serif;-webkit-font-smoothing:antialiased;">
    <div style="display:none;font-size:1px;color:#ede8e0;line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;">{preheader}</div>
    <div style="width:100%;background-color:#ede8e0;padding:40px 16px;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
            <tr>
                <td align="center">
                    <table role="presentation" width="600" cellspacing="0" cellpadding="0" border="0" style="max-width:600px;width:100%;background:#faf8f4;border-radius:4px;overflow:hidden;box-shadow:0 8px 40px rgba(0,0,0,0.12),0 2px 8px rgba(0,0,0,0.06);">
                        <!-- TOP BADGE -->
                        <tr>
                            <td>
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#1c1c24;padding:14px 36px;">
                                    <tr>
                                        <td>
                                            <span style="font-family:'Jost',Arial,sans-serif;font-size:10px;font-weight:600;letter-spacing:3px;text-transform:uppercase;color:#b8943f;">{badge_text}</span>
                                        </td>
                                        <td align="right">
                                            <span style="font-family:'Cormorant Garamond',Georgia,serif;font-size:26px;font-weight:600;color:#faf8f4;letter-spacing:-0.5px;">{price_number}{price_currency_html}</span>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <!-- HERO IMAGE -->
                        <tr>
                            <td style="background:#1c1c24;padding:0;line-height:0;">
                                <img src="cid:cover-image" alt="{hero_title}" width="600" style="width:100%;height:auto;display:block;" />
                                <!--[if !mso]><!-->
                                <div style="background:linear-gradient(135deg,#1c1c24 0%,#2e2a20 100%);padding:36px 36px 28px;">
                                    <p style="font-family:'Cormorant Garamond',Georgia,serif;font-size:34px;font-weight:700;color:#faf8f4;margin:0 0 8px;line-height:1.2;">{hero_title}</p>
                                    <p style="font-family:'Jost',Arial,sans-serif;font-size:11px;font-weight:500;letter-spacing:2.5px;text-transform:uppercase;color:#b8943f;margin:0;">{location_line}</p>
                                </div>
                                <!--<![endif]-->
                            </td>
                        </tr>
                        <!-- GOLD RULE -->
                        <tr>
                            <td style="height:3px;background:linear-gradient(to right,#b8943f,#d4b86a,#b8943f);font-size:0;line-height:0;">&nbsp;</td>
                        </tr>
                        <!-- STATS BAR -->
                        <tr>
                            <td style="background:#1c1c24;padding:0;">
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                                    <tr>
                                        {stats_cells}
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <!-- GOLD RULE -->
                        <tr>
                            <td style="height:3px;background:linear-gradient(to right,#b8943f,#d4b86a,#b8943f);font-size:0;line-height:0;">&nbsp;</td>
                        </tr>
                        <!-- BODY CONTENT -->
                        <tr>
                            <td style="padding:36px 36px 24px;background:#faf8f4;">
                                <p style="font-family:'Jost',Arial,sans-serif;font-size:13px;font-weight:300;letter-spacing:0.3px;color:#999;margin:0 0 22px;">{salutation}</p>
                                {body_paragraphs_html}
                                {amenities_section}
                            </td>
                        </tr>
                        <!-- CTA -->
                        <tr>
                            <td align="center" style="padding:8px 36px 36px;background:#faf8f4;">
                                <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                                    <tr>
                                        <td style="background:#1c1c24;border-bottom:3px solid #b8943f;border-radius:2px;">
                                            <a href="{cta_href}" style="display:inline-block;padding:16px 48px;color:#faf8f4;text-decoration:none;font-family:'Jost',Arial,sans-serif;font-size:11px;font-weight:600;letter-spacing:3px;text-transform:uppercase;">{cta_text}</a>
                                        </td>
                                    </tr>
                                </table>
                                <p style="font-family:'Jost',Arial,sans-serif;font-size:12px;font-weight:300;color:#aaa;margin:12px 0 0;letter-spacing:0.2px;">{cta_hint}</p>
                            </td>
                        </tr>
                        <!-- AGENT -->
                        {agent_block}
                        <!-- FOOTER -->
                        <tr>
                            <td style="background:#1c1c24;padding:18px 36px;text-align:center;">
                                <p style="font-family:'Jost',Arial,sans-serif;font-size:10px;font-weight:400;letter-spacing:1.5px;text-transform:uppercase;color:rgba(255,255,255,0.25);margin:0;">{footer_gen} <span style="color:#b8943f;">ListaPro</span> &nbsp;·&nbsp; {footer_rights}</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </div>
</body>
</html>'''

    return {
        "html": html,
        "subject": subject,
        "preview_text": preheader,
    }
