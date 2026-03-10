import os
from pathlib import Path

# Load .env file if present
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text().strip().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY", "")
SUNO_API_KEY = os.getenv("SUNO_API_KEY", "")

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
STORAGE_MODE = os.getenv("STORAGE_MODE", "local")  # "local" or "supabase"

COUNTRIES = {
    "mexico": {
        "name": "México",
        "currency": "MXN",
        "symbol": "$",
        "locale_example": "Colonia, Ciudad, Estado",
    },
    "colombia": {
        "name": "Colombia",
        "currency": "COP",
        "symbol": "$",
        "locale_example": "Barrio, Ciudad, Departamento",
    },
    "argentina": {
        "name": "Argentina",
        "currency": "ARS",
        "symbol": "$",
        "locale_example": "Barrio, Ciudad, Provincia",
    },
    "chile": {
        "name": "Chile",
        "currency": "CLP",
        "symbol": "$",
        "locale_example": "Comuna, Ciudad, Región",
    },
    "peru": {
        "name": "Perú",
        "currency": "PEN",
        "symbol": "S/",
        "locale_example": "Distrito, Ciudad, Departamento",
    },
    "ecuador": {
        "name": "Ecuador",
        "currency": "USD",
        "symbol": "$",
        "locale_example": "Sector, Ciudad, Provincia",
    },
    "uruguay": {
        "name": "Uruguay",
        "currency": "UYU",
        "symbol": "$",
        "locale_example": "Barrio, Ciudad, Departamento",
    },
    "republica_dominicana": {
        "name": "Rep. Dominicana",
        "currency": "DOP",
        "symbol": "RD$",
        "locale_example": "Sector, Ciudad, Provincia",
    },
    "costa_rica": {
        "name": "Costa Rica",
        "currency": "CRC",
        "symbol": "₡",
        "locale_example": "Barrio, Ciudad, Provincia",
    },
    "panama": {
        "name": "Panamá",
        "currency": "USD",
        "symbol": "$",
        "locale_example": "Barrio, Ciudad, Provincia",
    },
}

PROPERTY_TYPES = [
    "Casa",
    "Departamento",
    "Terreno",
    "Oficina",
    "Local Comercial",
    "Penthouse",
    "Bodega",
    "Estudio",
]

OPERATIONS = ["Venta", "Renta", "Renta Temporal"]

AMENITIES = [
    "Estacionamiento",
    "Alberca",
    "Jardín",
    "Terraza",
    "Gimnasio",
    "Seguridad 24h",
    "Elevador",
    "Cuarto de servicio",
    "Bodega",
    "Roof Garden",
    "Área de juegos",
    "Pet Friendly",
    "Amueblado",
    "Aire acondicionado",
    "Calefacción",
    "Cocina integral",
]


def format_price(price: float, country_key: str) -> str:
    country = COUNTRIES.get(country_key, COUNTRIES["mexico"])
    symbol = country["symbol"]
    currency = country["currency"]
    if currency in ("USD", "CRC"):
        return f"{symbol}{price:,.2f} {currency}"
    return f"{symbol}{price:,.0f} {currency}"
