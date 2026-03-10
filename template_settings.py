"""Template settings module for ListaPro brand customization."""
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
GENERATED_DIR = BASE_DIR / "generated"
SETTINGS_FILE = GENERATED_DIR / "template_settings.json"

ASSETS_DIR = GENERATED_DIR / "assets"

DEFAULT_SETTINGS = {
    "pdf": {
        "color_primary": "#1a365d",
        "color_accent": "#e53e3e",
        "pdf_template": "clasico",
    },
    "video": {
        "color_background": "#0f2137",
        "color_accent": "#c9a84c",
        "color_cta": "#c8102e",
    },
    "music": {
        "style": "elegant ambient piano cinematic soft luxury real estate",
        "negative_tags": "vocals, singing, heavy metal, aggressive, loud",
    },
    "branding": {
        "logo_path": "",
        "agent_photo_path": "",
        "qr_enabled": False,
        "qr_url": "",
    },
}


def _merge_with_defaults(data: dict) -> dict:
    """Merge loaded data with defaults to ensure all keys exist."""
    merged = json.loads(json.dumps(DEFAULT_SETTINGS))
    for section in merged:
        if section in data and isinstance(data[section], dict):
            merged[section].update(data[section])
    return merged


def load_settings() -> dict:
    """Load settings from Supabase (if enabled) or local JSON file."""
    from supabase_client import is_supabase_mode, load_template_settings

    # Supabase mode: read from database
    if is_supabase_mode():
        try:
            data = load_template_settings()
            if data:
                return _merge_with_defaults(data)
        except Exception:
            pass
        return json.loads(json.dumps(DEFAULT_SETTINGS))

    # Local mode: read from JSON file
    try:
        if SETTINGS_FILE.exists():
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            return _merge_with_defaults(data)
    except Exception:
        pass
    return json.loads(json.dumps(DEFAULT_SETTINGS))


def save_settings(data: dict) -> None:
    """Validate and save settings to Supabase or local JSON file."""
    current = load_settings()
    current_branding = current.get("branding", DEFAULT_SETTINGS["branding"])
    settings = {
        "pdf": {
            "color_primary": data.get("pdf_color_primary", DEFAULT_SETTINGS["pdf"]["color_primary"]),
            "color_accent": data.get("pdf_color_accent", DEFAULT_SETTINGS["pdf"]["color_accent"]),
            "pdf_template": data.get("pdf_template", DEFAULT_SETTINGS["pdf"]["pdf_template"]),
        },
        "video": {
            "color_background": data.get("video_color_background", DEFAULT_SETTINGS["video"]["color_background"]),
            "color_accent": data.get("video_color_accent", DEFAULT_SETTINGS["video"]["color_accent"]),
            "color_cta": data.get("video_color_cta", DEFAULT_SETTINGS["video"]["color_cta"]),
        },
        "music": {
            "style": data.get("music_style", DEFAULT_SETTINGS["music"]["style"]),
            "negative_tags": data.get("music_negative_tags", DEFAULT_SETTINGS["music"]["negative_tags"]),
        },
        "branding": {
            "logo_path": data.get("logo_path", current_branding.get("logo_path", "")),
            "agent_photo_path": data.get("agent_photo_path", current_branding.get("agent_photo_path", "")),
            "qr_enabled": data.get("qr_enabled", "off") == "on",
            "qr_url": data.get("qr_url", ""),
        },
    }

    from supabase_client import is_supabase_mode, save_template_settings

    if is_supabase_mode():
        save_template_settings(settings)
    else:
        GENERATED_DIR.mkdir(exist_ok=True)
        SETTINGS_FILE.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8")


def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color string to RGB tuple for FPDF."""
    hex_color = hex_color.lstrip("#")
    return (
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
    )
