"""
Voiceover Generator for ListaPro.
Integrates with ElevenLabs API for text-to-speech generation.
"""

import json
import requests
from pathlib import Path

from config import OPENAI_API_KEY, ELEVENLABS_API_KEY

# Pre-selected ElevenLabs voices
VOICES = {
    "masculina": {
        "id": "pNInz6obpgDQGcFmaJgB",  # Adam — deep, professional male
        "name": "Adam",
    },
    "femenina": {
        "id": "21m00Tcm4TlvDq8ikWAM",  # Rachel — warm, professional female
        "name": "Rachel",
    },
}

ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech"
ELEVENLABS_TTS_TIMESTAMPS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"


def generate_voiceover_script(property_data: dict, video_type: str = "reel",
                              tone: str = "profesional", context: str = "",
                              lang: str = "es") -> str:
    """Generate a voiceover script using OpenAI based on property data and video type."""
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)

    from config import COUNTRIES, format_price
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
    amenidades_str = ", ".join(amenidades) if amenidades else ""

    tone_descriptions = {
        "es": {
            "profesional": "Tono profesional, informativo y confiable. Como un asesor inmobiliario experto presentando la propiedad.",
            "lujo": "Tono aspiracional y exclusivo. Evoca lujo, sofisticación y estilo de vida premium. Usa lenguaje elegante y evocador.",
            "energetico": "Tono dinámico, entusiasta y con urgencia. Genera emoción y motivación para actuar. Directo y persuasivo.",
        },
        "en": {
            "profesional": "Professional, informative, and trustworthy tone. Like an expert real estate advisor presenting the property.",
            "lujo": "Aspirational and exclusive tone. Evoke luxury, sophistication, and premium lifestyle. Use elegant and evocative language.",
            "energetico": "Dynamic, enthusiastic tone with urgency. Generate excitement and motivation to act. Direct and persuasive.",
        },
    }

    tone_desc = tone_descriptions.get(lang, tone_descriptions["es"]).get(tone, tone_descriptions["es"]["profesional"])

    if lang == "en":
        if video_type == "tour":
            video_instruction = """Write a NARRATED PROPERTY TOUR script. Walk the viewer through the property room by room:
- Start with an engaging opening about the property and location
- Describe the exterior/entrance
- Walk through main living areas (living room, kitchen, dining)
- Describe bedrooms and bathrooms
- Mention outdoor areas, views, or special features
- Close with amenities, price, and a call to action
The script should feel like a personal walkthrough, using phrases like "As we enter...", "Moving to the...", "Notice the..."
Duration: 45-60 seconds when read aloud (approximately 120-160 words)."""
        else:
            video_instruction = """Write a SHORT REEL script for a quick property showcase:
- Start with a powerful hook phrase (first 3 seconds are critical)
- Highlight 3-4 key features quickly
- Mention price and location
- End with a call to action
Duration: 15-25 seconds when read aloud (approximately 40-65 words)."""

        system_prompt = f"""You are a professional real estate voiceover scriptwriter for the {country['name']} market.

{tone_desc}

{video_instruction}

RULES:
- Write ONLY the script text that will be read aloud — no stage directions, no brackets, no labels
- Make it sound natural when spoken, not like reading text
- IMPORTANT: Write prices in SPOKEN form, NOT abbreviated. For example: "seven million five hundred thousand pesos" instead of "MXN 7,500,000" or "$7,500,000 MXN". Never use currency codes like MXN, USD, COP etc. — write them as spoken words (pesos, dollars, etc.)
- Prices are in {country['currency']}
- DO NOT invent features not provided in the data
- ALL content must be in English
- Do NOT include hashtags, emojis, or social media formatting"""

        user_msg = f"""PROPERTY DATA:
- Type: {property_data.get('tipo_propiedad', '')}
- Operation: {property_data.get('operacion', 'Sale')}
- Price: {precio_fmt}
- Location: {property_data.get('ciudad', '')}, {country['name']}
- Bedrooms: {property_data.get('recamaras', '')}
- Bathrooms: {property_data.get('banos', '')}
- Built area: {property_data.get('m2_construidos', '')} m²
- Land area: {property_data.get('m2_terreno', '')} m²
- Parking: {property_data.get('estacionamientos', '')}
- Amenities: {amenidades_str}
- Notes: {property_data.get('notas', '')}
- Agent: {property_data.get('agente_nombre', '')}
- Phone: {property_data.get('agente_telefono', '')}"""

    else:
        if video_type == "tour":
            video_instruction = """Escribe un guión de TOUR NARRADO DE PROPIEDAD. Lleva al espectador recorriendo la propiedad espacio por espacio:
- Comienza con una apertura atractiva sobre la propiedad y ubicación
- Describe el exterior/entrada
- Recorre las áreas principales (sala, cocina, comedor)
- Describe recámaras y baños
- Menciona áreas exteriores, vistas o características especiales
- Cierra con amenidades, precio y llamado a la acción
El guión debe sentirse como un recorrido personal, usando frases como "Al entrar...", "Pasando a la...", "Observen el..."
Duración: 45-60 segundos al leerlo en voz alta (aproximadamente 120-160 palabras)."""
        else:
            video_instruction = """Escribe un guión CORTO DE REEL para un showcase rápido de propiedad:
- Comienza con una frase gancho poderosa (los primeros 3 segundos son críticos)
- Destaca 3-4 características clave rápidamente
- Menciona precio y ubicación
- Termina con un llamado a la acción
Duración: 15-25 segundos al leerlo en voz alta (aproximadamente 40-65 palabras)."""

        system_prompt = f"""Eres un guionista profesional de voiceover inmobiliario para el mercado de {country['name']}.

{tone_desc}

{video_instruction}

REGLAS:
- Escribe SOLO el texto del guión que se va a leer en voz alta — sin direcciones de escena, sin corchetes, sin etiquetas
- Debe sonar natural al hablarlo, no como texto leído
- IMPORTANTE: Escribe los precios en forma HABLADA, NO abreviada. Por ejemplo: "siete millones quinientos mil pesos" en lugar de "MXN 7,500,000" o "$7,500,000 MXN". Nunca uses códigos de moneda como MXN, USD, COP etc. — escríbelos como palabras habladas (pesos, dólares, etc.)
- Los precios están en {country['currency']}
- NO inventes características que no estén en los datos
- Todo el contenido debe estar en español
- NO incluyas hashtags, emojis, ni formato de redes sociales"""

        user_msg = f"""DATOS DE LA PROPIEDAD:
- Tipo: {property_data.get('tipo_propiedad', '')}
- Operación: {property_data.get('operacion', 'Venta')}
- Precio: {precio_fmt}
- Ubicación: {property_data.get('ciudad', '')}, {country['name']}
- Recámaras: {property_data.get('recamaras', '')}
- Baños: {property_data.get('banos', '')}
- Superficie construida: {property_data.get('m2_construidos', '')} m²
- Superficie terreno: {property_data.get('m2_terreno', '')} m²
- Estacionamientos: {property_data.get('estacionamientos', '')}
- Amenidades: {amenidades_str}
- Notas: {property_data.get('notas', '')}
- Agente: {property_data.get('agente_nombre', '')}
- Teléfono: {property_data.get('agente_telefono', '')}"""

    if context:
        extra = f"\n\nADDITIONAL CONTEXT FROM AGENT:\n{context}" if lang == "en" else f"\n\nCONTEXTO ADICIONAL DEL AGENTE:\n{context}"
        user_msg += extra

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=500,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
    )

    return response.choices[0].message.content.strip()


def generate_voiceover_script_scenes(property_data: dict, video_type: str = "tour",
                                      tone: str = "profesional", context: str = "",
                                      lang: str = "es") -> list[dict]:
    """Generate a structured voiceover script divided into scenes.

    Each scene maps to a specific part of the property so the user can
    assign the correct photo to each section.

    Returns a list of dicts:
        [{"id": "exterior", "label": "Fachada", "emoji": "🏠", "text": "..."}, ...]
    """
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)

    from config import COUNTRIES, format_price
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
    amenidades_str = ", ".join(amenidades) if amenidades else ""

    tone_descriptions = {
        "es": {
            "profesional": "Tono profesional, informativo y confiable.",
            "lujo": "Tono aspiracional y exclusivo. Lenguaje elegante y evocador.",
            "energetico": "Tono dinámico, entusiasta y con urgencia.",
        },
        "en": {
            "profesional": "Professional, informative, and trustworthy tone.",
            "lujo": "Aspirational and exclusive tone. Elegant and evocative language.",
            "energetico": "Dynamic, enthusiastic tone with urgency.",
        },
    }

    tone_desc = tone_descriptions.get(lang, tone_descriptions["es"]).get(
        tone, tone_descriptions["es"]["profesional"]
    )

    if lang == "en":
        system_prompt = f"""You are a professional real estate voiceover scriptwriter for the {country['name']} market.

{tone_desc}

Write a NARRATED PROPERTY TOUR script divided into SCENES. Each scene corresponds to a specific area of the property.

You MUST return ONLY valid JSON (no markdown, no backticks) — an array of scene objects.

Each scene object has these keys:
- "id": short identifier (lowercase, no spaces — e.g. "exterior", "kitchen", "bedroom")
- "label": human-readable name (e.g. "Kitchen", "Master Bedroom")
- "emoji": a single emoji representing the scene (e.g. "🏠", "🍳", "🛏️")
- "text": the voiceover narration for this scene (2-4 sentences, natural spoken language)

RULES:
- Generate 5-8 scenes total
- ALWAYS start with an "exterior" scene (property exterior / entrance)
- ALWAYS end with a "closing" scene (call to action, contact info)
- Middle scenes should cover the property's actual features (kitchen, living room, bedrooms, bathrooms, outdoor areas, etc.)
- Only include scenes for areas the property actually has (based on the data)
- Each scene text should be 15-30 words (natural spoken pace)
- Total script should be 120-180 words (45-70 seconds when read aloud)
- Write ONLY text to be read aloud — no stage directions, no brackets
- IMPORTANT: Write prices in SPOKEN form, NOT abbreviated. Example: "seven million five hundred thousand pesos" instead of "MXN 7,500,000". Never use currency codes (MXN, USD, COP) — write as spoken words.
- Prices in {country['currency']}
- DO NOT invent features not in the data
- ALL content in English"""

        user_msg = f"""PROPERTY DATA:
- Type: {property_data.get('tipo_propiedad', '')}
- Operation: {property_data.get('operacion', 'Sale')}
- Price: {precio_fmt}
- Location: {property_data.get('ciudad', '')}, {country['name']}
- Bedrooms: {property_data.get('recamaras', '')}
- Bathrooms: {property_data.get('banos', '')}
- Built area: {property_data.get('m2_construidos', '')} m²
- Land area: {property_data.get('m2_terreno', '')} m²
- Parking: {property_data.get('estacionamientos', '')}
- Amenities: {amenidades_str}
- Notes: {property_data.get('notas', '')}
- Agent: {property_data.get('agente_nombre', '')}
- Phone: {property_data.get('agente_telefono', '')}"""
    else:
        system_prompt = f"""Eres un guionista profesional de voiceover inmobiliario para el mercado de {country['name']}.

{tone_desc}

Escribe un guión de TOUR NARRADO dividido en ESCENAS. Cada escena corresponde a un área específica de la propiedad.

DEBES devolver ÚNICAMENTE JSON válido (sin markdown, sin backticks) — un array de objetos de escena.

Cada objeto de escena tiene estas claves:
- "id": identificador corto (minúsculas, sin espacios — ej: "exterior", "cocina", "recamara")
- "label": nombre legible (ej: "Cocina", "Recámara Principal")
- "emoji": un solo emoji representando la escena (ej: "🏠", "🍳", "🛏️")
- "text": la narración del voiceover para esta escena (2-4 oraciones, lenguaje natural hablado)

REGLAS:
- Genera entre 5 y 8 escenas en total
- SIEMPRE empieza con una escena "exterior" (fachada / entrada de la propiedad)
- SIEMPRE termina con una escena "cierre" (llamado a la acción, datos de contacto)
- Las escenas intermedias deben cubrir las áreas reales de la propiedad (cocina, sala, recámaras, baños, áreas exteriores, etc.)
- Solo incluye escenas para áreas que la propiedad realmente tiene (basado en los datos)
- Cada texto de escena debe tener 15-30 palabras (ritmo natural al hablar)
- El guión total debe ser de 120-180 palabras (45-70 segundos al leerlo en voz alta)
- Escribe SOLO texto que se va a leer en voz alta — sin direcciones de escena, sin corchetes
- IMPORTANTE: Escribe los precios en forma HABLADA, NO abreviada. Ejemplo: "siete millones quinientos mil pesos" en lugar de "MXN 7,500,000". Nunca uses códigos de moneda (MXN, USD, COP) — escríbelos como palabras habladas.
- Los precios están en {country['currency']}
- NO inventes características que no estén en los datos
- Todo el contenido en español"""

        user_msg = f"""DATOS DE LA PROPIEDAD:
- Tipo: {property_data.get('tipo_propiedad', '')}
- Operación: {property_data.get('operacion', 'Venta')}
- Precio: {precio_fmt}
- Ubicación: {property_data.get('ciudad', '')}, {country['name']}
- Recámaras: {property_data.get('recamaras', '')}
- Baños: {property_data.get('banos', '')}
- Superficie construida: {property_data.get('m2_construidos', '')} m²
- Superficie terreno: {property_data.get('m2_terreno', '')} m²
- Estacionamientos: {property_data.get('estacionamientos', '')}
- Amenidades: {amenidades_str}
- Notas: {property_data.get('notas', '')}
- Agente: {property_data.get('agente_nombre', '')}
- Teléfono: {property_data.get('agente_telefono', '')}"""

    if context:
        extra = f"\n\nADDITIONAL CONTEXT:\n{context}" if lang == "en" else f"\n\nCONTEXTO ADICIONAL:\n{context}"
        user_msg += extra

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=1500,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
    )

    raw = response.choices[0].message.content.strip()

    try:
        parsed = json.loads(raw)

        # Case 1: model returned a raw list (unlikely with json_object mode, but handle it)
        if isinstance(parsed, list):
            scenes_list = parsed
        elif isinstance(parsed, dict):
            scenes_list = None

            # Case 2: check well-known keys first
            for key in ("scenes", "escenas", "data", "guion", "script", "tour",
                         "tour_scenes", "resultado", "content"):
                if key in parsed and isinstance(parsed[key], list):
                    scenes_list = parsed[key]
                    break

            # Case 3: fallback — find ANY key whose value is a list of dicts with "text"
            if scenes_list is None:
                for key, val in parsed.items():
                    if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict) and "text" in val[0]:
                        scenes_list = val
                        print(f"Scene JSON: found scenes under unexpected key '{key}'")
                        break

            # Case 4: the dict itself is a single scene object
            if scenes_list is None and "id" in parsed and "text" in parsed:
                scenes_list = [parsed]

            if scenes_list is None:
                scenes_list = []
        else:
            scenes_list = []

        # Validate: each scene must have at least "text"
        valid_scenes = []
        for i, s in enumerate(scenes_list):
            if isinstance(s, dict) and s.get("text", "").strip():
                # Ensure required keys exist with defaults
                if "id" not in s:
                    s["id"] = f"scene_{i+1}"
                if "label" not in s:
                    s["label"] = f"Escena {i+1}" if lang != "en" else f"Scene {i+1}"
                if "emoji" not in s:
                    s["emoji"] = "🎬"
                valid_scenes.append(s)

        if valid_scenes:
            return valid_scenes

    except json.JSONDecodeError as e:
        print(f"Scene JSON parse error: {e}\nRaw: {raw[:300]}")

    # Fallback: return empty — caller should fall back to flat script
    return []


def generate_voiceover_audio(script: str, voice: str = "femenina",
                             output_path: str = "voiceover.mp3",
                             scenes: list[dict] | None = None) -> dict:
    """Generate voiceover audio using ElevenLabs TTS API with timestamps.

    When `scenes` is provided, uses the with-timestamps endpoint to get
    character-level timing data. This allows mapping each scene's text
    to its exact start/end time in the audio, producing precise scene_weights
    instead of word-count estimation.

    Returns:
        {
            "status": "ready",
            "path": output_path,
            "scene_timings": [{"id": ..., "start": float, "end": float, "weight": float}, ...]
        } on success
        {"status": "failed", "error": "..."} on failure
    """
    if not ELEVENLABS_API_KEY:
        return {"status": "failed", "error": "ELEVENLABS_API_KEY not configured"}

    voice_data = VOICES.get(voice, VOICES["femenina"])
    voice_id = voice_data["id"]

    payload = {
        "text": script,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.4,
            "use_speaker_boost": True,
        },
    }

    # Use with-timestamps endpoint when scenes are provided for precise timing
    use_timestamps = scenes is not None and len(scenes) > 0

    if use_timestamps:
        url = ELEVENLABS_TTS_TIMESTAMPS_URL.format(voice_id=voice_id)
        headers = {
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY,
        }
    else:
        url = f"{ELEVENLABS_TTS_URL}/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY,
        }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=90)

        if response.status_code != 200:
            error = response.text[:300]
            return {"status": "failed", "error": f"ElevenLabs API error ({response.status_code}): {error}"}

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        if use_timestamps:
            # with-timestamps returns JSON with audio_base64 + alignment
            data = response.json()
            import base64
            audio_b64 = data.get("audio_base64", "")
            if not audio_b64:
                return {"status": "failed", "error": "No audio_base64 in timestamps response"}

            audio_bytes = base64.b64decode(audio_b64)
            Path(output_path).write_bytes(audio_bytes)

            # Extract character-level timestamps from alignment
            alignment = data.get("alignment", {})
            characters = alignment.get("characters", [])
            char_starts = alignment.get("character_start_times_seconds", [])
            char_ends = alignment.get("character_end_times_seconds", [])

            # Map scenes to their timestamp ranges
            scene_timings = _compute_scene_timings(
                script, scenes, characters, char_starts, char_ends
            )

            return {
                "status": "ready",
                "path": output_path,
                "scene_timings": scene_timings,
            }
        else:
            # Standard endpoint returns raw audio bytes
            Path(output_path).write_bytes(response.content)
            return {"status": "ready", "path": output_path}

    except requests.exceptions.Timeout:
        return {"status": "failed", "error": "ElevenLabs API timeout"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


def _compute_scene_timings(
    full_script: str,
    scenes: list[dict],
    characters: list[str],
    char_starts: list[float],
    char_ends: list[float],
) -> list[dict]:
    """Map each scene's text to its exact start/end time using character-level timestamps.

    Finds each scene's text within the full script, looks up the character
    positions, and reads the corresponding start/end times from the alignment data.

    Returns list of dicts with id, start, end, duration, and weight per scene.
    """
    if not char_starts or not char_ends:
        # Fallback to word-count estimation if no timestamp data
        return _fallback_word_count_timings(scenes)

    total_audio_duration = max(char_ends) if char_ends else 1.0
    results = []
    search_from = 0

    for scene in scenes:
        scene_text = scene.get("text", "").strip()
        scene_id = scene.get("id", "")

        if not scene_text:
            results.append({"id": scene_id, "start": 0, "end": 0, "duration": 0, "weight": 0})
            continue

        # Find scene text position in full script
        pos = full_script.find(scene_text, search_from)
        if pos == -1:
            # Try fuzzy: first 30 chars
            snippet = scene_text[:30]
            pos = full_script.find(snippet, search_from)

        if pos == -1:
            # Can't locate — use word-count fallback for this scene
            results.append({"id": scene_id, "start": 0, "end": 0, "duration": 0, "weight": 0})
            continue

        char_start_idx = pos
        char_end_idx = min(pos + len(scene_text) - 1, len(char_starts) - 1)
        search_from = pos + len(scene_text)

        # Clamp indices to alignment array bounds
        char_start_idx = min(char_start_idx, len(char_starts) - 1)
        char_end_idx = min(char_end_idx, len(char_ends) - 1)

        start_time = char_starts[char_start_idx] if char_start_idx >= 0 else 0
        end_time = char_ends[char_end_idx] if char_end_idx >= 0 else total_audio_duration
        duration = max(0, end_time - start_time)

        results.append({
            "id": scene_id,
            "start": round(start_time, 3),
            "end": round(end_time, 3),
            "duration": round(duration, 3),
            "weight": 0,  # computed below
        })

    # Compute weights from durations
    total_duration = sum(r["duration"] for r in results)
    if total_duration > 0:
        for r in results:
            r["weight"] = round(r["duration"] / total_duration, 4)
    elif results:
        # Equal distribution fallback
        equal_w = round(1.0 / len(results), 4)
        for r in results:
            r["weight"] = equal_w

    return results


def _fallback_word_count_timings(scenes: list[dict]) -> list[dict]:
    """Fallback: estimate scene weights from word counts when timestamps unavailable."""
    word_counts = [len(s.get("text", "").split()) for s in scenes]
    total_words = sum(word_counts)
    results = []
    for i, scene in enumerate(scenes):
        weight = word_counts[i] / total_words if total_words > 0 else 1.0 / len(scenes)
        results.append({
            "id": scene.get("id", ""),
            "start": 0,
            "end": 0,
            "duration": 0,
            "weight": round(weight, 4),
        })
    return results
