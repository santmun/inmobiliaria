import json
from openai import OpenAI
from config import OPENAI_API_KEY, COUNTRIES, format_price


def generate_listing_copy(property_data: dict) -> dict:
    """Generate real estate listing copy using OpenAI API."""
    client = OpenAI(api_key=OPENAI_API_KEY)

    country_key = property_data.get("pais", "mexico")
    country = COUNTRIES.get(country_key, COUNTRIES["mexico"])
    precio = float(property_data.get("precio", 0))
    precio_fmt = format_price(precio, country_key)
    lang = property_data.get("idioma", "es")

    amenidades = property_data.get("amenidades", [])
    if isinstance(amenidades, str):
        amenidades = [amenidades]
    otras = property_data.get("otras_amenidades", "")
    if otras:
        amenidades.extend([a.strip() for a in otras.split(",") if a.strip()])
    amenidades_str = ", ".join(amenidades) if amenidades else ("No especificadas" if lang == "es" else "Not specified")

    if lang == "en":
        system_prompt = f"""You are a professional real estate copywriter with extensive experience in the {country['name']} property market. Your job is to create attractive, professional listing copy in English.

RULES:
- Use appropriate real estate vocabulary for the {country['name']} market
- Prices are expressed in {country['currency']}
- Be professional yet approachable
- Highlight the most attractive features of the property
- DO NOT make up information not provided in the data
- If any data is unavailable, simply don't mention it
- ALL content must be written in English

Respond ONLY with valid JSON (no markdown, no backticks) with these 5 keys:

1. "descripcion_pdf": Professional description of 2-3 paragraphs for a real estate brochure. Elegant and descriptive tone. Mention location, main features, and notable amenities.

2. "copy_instagram": Instagram/Facebook post in English. Include relevant emojis (don't overdo it), hashtags at the end (5-8 hashtags including the city), and a call to action. Maximum 250 words.

3. "mensaje_whatsapp": Short WhatsApp message (3-4 lines max) in English. Include price, location, and one attractive feature. Minimal emojis. Direct and engaging.

4. "frase_gancho": A short, impactful phrase (maximum 8 words) that captures the essence of the property. Examples: "Your dream home awaits you", "Luxury and comfort in every detail", "Live where elegance resides". NO emojis. Must be emotional and aspirational.

5. "copy_email": Professional email body for a property blast email. Write a compelling subject line as the FIRST line (prefixed with "Subject: "), then a blank line, then the email body. The body should be 3-4 short paragraphs: opening hook, key features/highlights, call to action. Professional but warm tone. Do NOT include HTML tags. Do NOT include the agent name/phone (those are added automatically)."""

        user_message = f"""PROPERTY DATA:
- Type: {property_data.get('tipo_propiedad', 'Not specified')}
- Operation: {property_data.get('operacion', 'Sale')}
- Price: {precio_fmt}
- Location: {property_data.get('ciudad', '')}, {country['name']}
- Address: {property_data.get('direccion', 'Not published')}
- Bedrooms: {property_data.get('recamaras', 'Not specified')}
- Bathrooms: {property_data.get('banos', 'Not specified')}
- Built area: {property_data.get('m2_construidos', 'Not specified')} m²
- Land area: {property_data.get('m2_terreno', 'Not specified')} m²
- Parking: {property_data.get('estacionamientos', 'Not specified')}
- Floors: {property_data.get('pisos', 'Not specified')}
- Amenities: {amenidades_str}
- Additional notes: {property_data.get('notas', 'None')}
- Agent: {property_data.get('agente_nombre', '')}
- Phone: {property_data.get('agente_telefono', '')}"""

    else:
        system_prompt = f"""Eres un copywriter profesional de bienes raíces con amplia experiencia en el mercado inmobiliario de {country['name']}. Tu trabajo es crear textos atractivos y profesionales para listados de propiedades.

REGLAS:
- Usa vocabulario inmobiliario apropiado para {country['name']}
- Los precios se expresan en {country['currency']}
- Sé formal pero accesible
- Destaca las características más atractivas de la propiedad
- NO inventes datos que no estén en la información proporcionada
- Si algún dato no está disponible, simplemente no lo menciones

Responde ÚNICAMENTE con un JSON válido (sin markdown, sin backticks) con estas 5 claves:

1. "descripcion_pdf": Descripción profesional de 2-3 párrafos para un folleto inmobiliario. Tono elegante y descriptivo. Menciona ubicación, características principales y amenidades destacadas.

2. "copy_instagram": Post para Instagram/Facebook. Incluye emojis relevantes (sin exagerar), hashtags al final (5-8 hashtags incluyendo la ciudad), y un llamado a la acción. Máximo 250 palabras.

3. "mensaje_whatsapp": Mensaje corto para WhatsApp (3-4 líneas máximo). Incluye precio, ubicación y un dato atractivo. Con emojis mínimos. Debe ser directo y generar interés.

4. "frase_gancho": Una frase corta e impactante (máximo 8 palabras) que capture la esencia de la propiedad. Ejemplos: "Tu hogar soñado te espera", "Lujo y confort en cada detalle", "Vive donde la elegancia habita". NO uses emojis. Debe ser emotiva y aspiracional.

5. "copy_email": Cuerpo profesional de email para un blast inmobiliario. Escribe un asunto atractivo en la PRIMERA línea (con prefijo "Asunto: "), luego una línea en blanco, y después el cuerpo del email. El cuerpo debe tener 3-4 párrafos cortos: apertura atractiva, características/highlights, llamado a la acción. Tono profesional pero cercano. NO incluyas etiquetas HTML. NO incluyas nombre/teléfono del agente (se agregan automáticamente)."""

        user_message = f"""DATOS DE LA PROPIEDAD:
- Tipo: {property_data.get('tipo_propiedad', 'No especificado')}
- Operación: {property_data.get('operacion', 'Venta')}
- Precio: {precio_fmt}
- Ubicación: {property_data.get('ciudad', '')}, {country['name']}
- Dirección: {property_data.get('direccion', 'No publicada')}
- Recámaras: {property_data.get('recamaras', 'No especificado')}
- Baños: {property_data.get('banos', 'No especificado')}
- Superficie construida: {property_data.get('m2_construidos', 'No especificado')} m²
- Superficie terreno: {property_data.get('m2_terreno', 'No especificado')} m²
- Estacionamientos: {property_data.get('estacionamientos', 'No especificado')}
- Pisos: {property_data.get('pisos', 'No especificado')}
- Amenidades: {amenidades_str}
- Notas adicionales: {property_data.get('notas', 'Ninguna')}
- Agente: {property_data.get('agente_nombre', '')}
- Teléfono: {property_data.get('agente_telefono', '')}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=2500,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )

    raw = response.choices[0].message.content.strip()

    # Try to parse as JSON
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        # Try extracting JSON from markdown code block
        if "```" in raw:
            json_str = raw.split("```")[1]
            if json_str.startswith("json"):
                json_str = json_str[4:]
            result = json.loads(json_str.strip())
        else:
            result = {
                "descripcion_pdf": raw,
                "copy_instagram": "Error generating social media copy." if lang == "en" else "Error al generar el copy para redes sociales.",
                "mensaje_whatsapp": "Error generating WhatsApp message." if lang == "en" else "Error al generar el mensaje de WhatsApp.",
            }

    return result
