import asyncio
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
VIDEO_DIR = BASE_DIR / "video"
GENERATED_DIR = BASE_DIR / "generated"
STATIC_DIR = BASE_DIR / "static"

SERVER_PORT = 8000


def _local_path_to_url(photo_path: str) -> str:
    """Convert a local file path to an HTTP URL served by FastAPI."""
    path = Path(photo_path).resolve()

    # Photo in generated/ directory
    try:
        rel = path.relative_to(GENERATED_DIR.resolve())
        return f"http://localhost:{SERVER_PORT}/generated/{rel}"
    except ValueError:
        pass

    # Photo in static/ directory (placeholder)
    try:
        rel = path.relative_to(STATIC_DIR.resolve())
        return f"http://localhost:{SERVER_PORT}/static/{rel}"
    except ValueError:
        pass

    # Fallback
    return f"http://localhost:{SERVER_PORT}/static/{path.name}"


def _photo_path_to_url(photo_path: str, use_supabase: bool = False) -> str:
    """Convert photo path to URL. Uses Supabase public URLs in supabase mode."""
    if use_supabase:
        import supabase_client as sb
        path = Path(photo_path).resolve()
        try:
            rel = path.relative_to(GENERATED_DIR.resolve())
            return sb.get_public_url("listings", str(rel))
        except ValueError:
            pass
    return _local_path_to_url(photo_path)


async def generate_video(
    property_data: dict,
    photo_paths: list[str],
    output_path: str,
    props_path: str,
    music_url: str = "",
    video_colors=None,
    branding=None,
) -> dict:
    """Generate a video reel using Remotion. Returns status dict."""

    try:
        import supabase_client as sb
        use_supabase = sb.is_supabase_mode()

        # Convert paths to URLs (Supabase public URLs or localhost)
        urls = [_photo_path_to_url(p, use_supabase) for p in photo_paths if Path(p).exists()]

        cover_url = urls[0] if urls else ""
        extra_urls = list(urls[1:]) if len(urls) > 1 else []

        # Build props JSON for Remotion
        props = {
            "tipoPropiedad": property_data.get("tipo_propiedad", ""),
            "operacion": property_data.get("operacion", ""),
            "ciudad": property_data.get("ciudad", ""),
            "paisNombre": property_data.get("pais_nombre", ""),
            "precioFormateado": property_data.get("precio_formateado", ""),
            "recamaras": property_data.get("recamaras", "0"),
            "banos": property_data.get("banos", "0"),
            "m2Construidos": property_data.get("m2_construidos", ""),
            "estacionamientos": property_data.get("estacionamientos", "0"),
            "fotoPortada": cover_url,
            "fotosExtra": extra_urls,
            "agenteNombre": property_data.get("agente_nombre", ""),
            "agenteTelefono": property_data.get("agente_telefono", ""),
            "agenciaNombre": property_data.get("agencia_nombre", ""),
        }

        if music_url:
            props["musicUrl"] = music_url

        # Inject logo URL if available
        if branding and branding.get("logo_path"):
            if use_supabase:
                props["logoUrl"] = sb.get_public_url("branding", "logo.png")
            else:
                logo_full = GENERATED_DIR / branding["logo_path"]
                if logo_full.exists():
                    props["logoUrl"] = _local_path_to_url(str(logo_full))

        # Inject custom video colors if provided
        if video_colors:
            if "color_background" in video_colors:
                props["colorBackground"] = video_colors["color_background"]
            if "color_accent" in video_colors:
                props["colorAccent"] = video_colors["color_accent"]
            if "color_cta" in video_colors:
                props["colorCta"] = video_colors["color_cta"]

        # Write props to JSON file
        Path(props_path).write_text(json.dumps(props, ensure_ascii=False))

        process = await asyncio.create_subprocess_exec(
            "npx", "remotion", "render",
            "ListingReel",
            "--output", output_path,
            "--props", props_path,
            "--codec", "h264",
            "--concurrency", "1",
            cwd=str(VIDEO_DIR),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            return {"status": "ready", "path": output_path}
        else:
            error_msg = stderr.decode("utf-8", errors="replace")[-500:]
            return {"status": "failed", "error": error_msg}

    except Exception as e:
        return {"status": "failed", "error": str(e)}
