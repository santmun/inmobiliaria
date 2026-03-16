import asyncio
import json
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent
VIDEO_DIR = BASE_DIR / "video"
GENERATED_DIR = BASE_DIR / "generated"
STATIC_DIR = BASE_DIR / "static"
REMOTION_PUBLIC = VIDEO_DIR / "public"

SERVER_PORT = 8000


def _copy_to_remotion_public(local_path: str, dest_name: str) -> str:
    """Copy a file into Remotion's public/ folder so it can be loaded via staticFile().
    Returns the URL that Remotion can use (http://localhost:3000/<dest_name>)."""
    src = Path(local_path)
    if not src.exists():
        return ""
    dest = REMOTION_PUBLIC / dest_name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src), str(dest))
    return dest_name  # Remotion staticFile() uses relative paths from public/


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
    frase_gancho: str = "",
    video_style: str = "",
    voiceover_path: str = "",
    video_type: str = "reel",
) -> dict:
    """Generate a video reel using Remotion. Returns status dict."""

    try:
        # Always use local URLs for Remotion rendering (runs on localhost).
        # Supabase public URLs cause ERR_BLOCKED_BY_ORB in the browser.
        use_supabase = False

        # Convert paths to localhost URLs for Remotion
        urls = [_local_path_to_url(p) for p in photo_paths if Path(p).exists()]

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

        # Inject logo URL if available — copy to Remotion public/ for reliable loading
        if branding and branding.get("logo_path"):
            logo_full = GENERATED_DIR / branding["logo_path"]
            if logo_full.exists():
                _copy_to_remotion_public(str(logo_full), "branding/logo.png")
                props["logoUrl"] = _local_path_to_url(str(logo_full))

        # Inject agent photo URL if available
        if branding and branding.get("agent_photo_path"):
            photo_full = GENERATED_DIR / branding["agent_photo_path"]
            if photo_full.exists():
                _copy_to_remotion_public(str(photo_full), "branding/agent_photo.png")
                props["agentPhotoUrl"] = _local_path_to_url(str(photo_full))

        # Inject QR code image if enabled
        if branding and branding.get("qr_enabled") and branding.get("qr_url"):
            try:
                import qrcode as qr_lib
                qr = qr_lib.QRCode(version=1, box_size=10, border=1)
                qr.add_data(branding["qr_url"])
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="black", back_color="white")
                qr_path = Path(output_path).parent / "qr_code.png"
                qr_img.save(str(qr_path))
                if use_supabase:
                    rel = qr_path.resolve().relative_to(GENERATED_DIR.resolve())
                    sb.upload_file_from_path("listings", str(rel), str(qr_path))
                    props["qrUrl"] = sb.get_public_url("listings", str(rel))
                else:
                    props["qrUrl"] = _local_path_to_url(str(qr_path))
            except Exception:
                pass  # Skip QR if generation fails

        # Inject hook phrase
        if frase_gancho:
            props["fraseGancho"] = frase_gancho

        # Inject video style
        if video_style:
            props["videoStyle"] = video_style

        # Inject video type (reel or tour)
        if video_type:
            props["videoType"] = video_type

        # Inject voiceover audio URL
        if voiceover_path and Path(voiceover_path).exists():
            if use_supabase:
                vo_rel = Path(voiceover_path).resolve().relative_to(GENERATED_DIR.resolve())
                props["voiceoverUrl"] = sb.get_public_url("listings", str(vo_rel))
            else:
                props["voiceoverUrl"] = _local_path_to_url(voiceover_path)
            # When voiceover is present, lower music volume
            props["musicVolume"] = 0.15

        # Inject custom video colors if provided
        if video_colors:
            if "color_background" in video_colors:
                props["colorBackground"] = video_colors["color_background"]
            if "color_accent" in video_colors:
                props["colorAccent"] = video_colors["color_accent"]
            if "color_cta" in video_colors:
                props["colorCta"] = video_colors["color_cta"]

        # Inject scene timings if available (for voiceover sync)
        # For voiceover tours: Gallery shows ALL photos (portada + extras),
        # so we pass ALL scene weights without skipping.
        # For standard reels: Gallery only shows fotosExtra, so skip first weight.
        scene_timings_path = Path(output_path).parent / "scene_timings.json"
        has_voiceover = bool(voiceover_path and Path(voiceover_path).exists())
        if scene_timings_path.exists():
            try:
                scene_timings = json.loads(scene_timings_path.read_text())
                if scene_timings and len(scene_timings) > 0:
                    # Voiceover tours: ALL photos in Gallery → ALL weights
                    # Standard reels: skip first (hero/cover separate from Gallery)
                    if has_voiceover:
                        relevant_timings = scene_timings
                    else:
                        relevant_timings = scene_timings[1:] if len(scene_timings) > 1 else scene_timings

                    has_precise_weights = any(s.get("weight", 0) > 0 for s in relevant_timings)
                    if has_precise_weights:
                        raw = [s.get("weight", 0) for s in relevant_timings]
                        total = sum(raw) or 1
                        props["sceneWeights"] = [round(w / total, 4) for w in raw]
                        label = "all scenes" if has_voiceover else "gallery only"
                        print(f"Scene weights (ElevenLabs, {label}): {props['sceneWeights']}")
                    else:
                        total_words = sum(s.get("words", 0) for s in relevant_timings)
                        if total_words > 0:
                            props["sceneWeights"] = [
                                round(s.get("words", 0) / total_words, 3)
                                for s in relevant_timings
                            ]
                            label = "all scenes" if has_voiceover else "gallery only"
                            print(f"Scene weights (word-count, {label}): {props['sceneWeights']}")
            except Exception as e:
                print(f"Scene timings error: {e}")

        # Write props to JSON file
        Path(props_path).write_text(json.dumps(props, ensure_ascii=False))

        # Copy job photos into Remotion public/ via symlink for reliable loading
        # The symlink public/generated -> ../../generated makes files accessible
        # to Remotion's bundler without depending on the FastAPI server

        process = await asyncio.create_subprocess_exec(
            "npx", "remotion", "render",
            "ListingReel",
            "--output", output_path,
            "--props", props_path,
            "--codec", "h264",
            "--concurrency", "1",
            "--delay-render-timeout", "90000",
            "--port", "3199",
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
