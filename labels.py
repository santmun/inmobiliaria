"""
Bilingual label system for ListaPro.
Centralizes all translatable strings for image generators, PDF, and carousel.
"""

LABELS = {
    # Stats (short labels for images)
    "recamaras": {"es": "Rec.", "en": "Bed."},
    "banos": {"es": "Baños", "en": "Bath."},
    "m2_construidos": {"es": "Constr.", "en": "Built"},
    "estacionamientos": {"es": "Estac.", "en": "Parking"},

    # Stats (full labels for PDF)
    "recamaras_full": {"es": "Recámaras", "en": "Bedrooms"},
    "banos_full": {"es": "Baños", "en": "Bathrooms"},
    "m2_construidos_full": {"es": "m² Construidos", "en": "Built Area (m²)"},
    "m2_terreno_full": {"es": "m² Terreno", "en": "Land Area (m²)"},
    "estacionamientos_full": {"es": "Estacionamientos", "en": "Parking Spots"},
    "pisos_full": {"es": "Pisos", "en": "Floors"},
    "direccion": {"es": "Dirección", "en": "Address"},
    "pisos_niveles": {"es": "Pisos / Niveles", "en": "Floors / Levels"},
    "superficie_construida": {"es": "Superficie construida", "en": "Built area"},
    "superficie_terreno": {"es": "Superficie terreno", "en": "Land area"},

    # Operations
    "Venta": {"es": "VENTA", "en": "FOR SALE"},
    "Renta": {"es": "RENTA", "en": "FOR RENT"},
    "Renta Temporal": {"es": "RENTA TEMPORAL", "en": "SHORT-TERM RENTAL"},

    # Operations (lowercase for headings)
    "venta_lower": {"es": "Venta", "en": "Sale"},
    "renta_lower": {"es": "Renta", "en": "Rent"},
    "renta_temporal_lower": {"es": "Renta Temporal", "en": "Short-term Rental"},

    # Property types
    "Casa": {"es": "Casa", "en": "House"},
    "Departamento": {"es": "Departamento", "en": "Apartment"},
    "Terreno": {"es": "Terreno", "en": "Land"},
    "Oficina": {"es": "Oficina", "en": "Office"},
    "Local Comercial": {"es": "Local Comercial", "en": "Commercial Space"},
    "Penthouse": {"es": "Penthouse", "en": "Penthouse"},
    "Bodega": {"es": "Bodega", "en": "Warehouse"},
    "Estudio": {"es": "Estudio", "en": "Studio"},

    # PDF section headers
    "amenidades": {"es": "Amenidades", "en": "Amenities"},
    "galeria": {"es": "Galería de Fotos", "en": "Photo Gallery"},
    "especificaciones": {"es": "Especificaciones", "en": "Specifications"},
    "descripcion": {"es": "Descripción", "en": "Description"},

    # PDF spec labels
    "tipo_propiedad": {"es": "Tipo de propiedad", "en": "Property type"},
    "operacion_label": {"es": "Operación", "en": "Operation"},
    "precio_label": {"es": "Precio", "en": "Price"},
    "ubicacion": {"es": "Ubicación", "en": "Location"},

    # Carousel text
    "slide_contact_title": {"es": "Agenda tu visita", "en": "Schedule a visit"},
    "slide_stats_title": {"es": "Características", "en": "Features"},
    "contacto": {"es": "Contacto", "en": "Contact"},

    # Heading pattern: "{tipo} en {operacion}"
    "heading_en": {"es": "en", "en": "for"},
}


def get_label(key: str, lang: str = "es") -> str:
    """Get a label in the specified language. Falls back to key itself."""
    entry = LABELS.get(key)
    if entry:
        return entry.get(lang, entry.get("es", key))
    return key


def get_operation(operation: str, lang: str = "es", uppercase: bool = True) -> str:
    """Translate operation. uppercase=True for badges, False for headings."""
    if uppercase:
        return get_label(operation, lang)
    # Map to lowercase variant
    lower_map = {"Venta": "venta_lower", "Renta": "renta_lower", "Renta Temporal": "renta_temporal_lower"}
    key = lower_map.get(operation, operation)
    return get_label(key, lang)


def get_property_type(tipo: str, lang: str = "es") -> str:
    """Translate property type."""
    return get_label(tipo, lang)
