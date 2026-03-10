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

    amenidades = property_data.get("amenidades", [])
    if isinstance(amenidades, str):
        amenidades = [amenidades]
    otras = property_data.get("otras_amenidades", "")
    if otras:
        amenidades.extend([a.strip() for a in otras.split(",") if a.strip()])
    amenidades_str = ", ".join(amenidades) if amenidades else "No especificadas"

    system_prompt = f"""Eres un copywriter profesional de bienes raíces con amplia experiencia en el mercado inmobiliario de {country['name']}. Tu trabajo es crear textos atractivos y profesionales para listados de propiedades.

REGLAS:
- Usa vocabulario inmobiliario apropiado para {country['name']}
- Los precios se expresan en {country['currency']}
- Sé formal pero accesible
- Destaca las características más atractivas de la propiedad
- NO inventes datos que no estén en la información proporcionada
- Si algún dato no está disponible, simplemente no lo menciones

Responde ÚNICAMENTE con un JSON válido (sin markdown, sin backticks) con estas 3 claves:

1. "descripcion_pdf": Descripción profesional de 2-3 párrafos para un folleto inmobiliario. Tono elegante y descriptivo. Menciona ubicación, características principales y amenidades destacadas.

2. "copy_instagram": Post para Instagram/Facebook. Incluye emojis relevantes (sin exagerar), hashtags al final (5-8 hashtags incluyendo la ciudad), y un llamado a la acción. Máximo 250 palabras.

3. "mensaje_whatsapp": Mensaje corto para WhatsApp (3-4 líneas máximo). Incluye precio, ubicación y un dato atractivo. Con emojis mínimos. Debe ser directo y generar interés."""

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
        max_tokens=1500,
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
                "copy_instagram": "Error al generar el copy para redes sociales.",
                "mensaje_whatsapp": "Error al generar el mensaje de WhatsApp.",
            }

    return result
