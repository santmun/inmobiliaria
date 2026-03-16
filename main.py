import os
import asyncio
import uuid
import shutil
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional

from config import COUNTRIES, PROPERTY_TYPES, OPERATIONS, AMENITIES, format_price, SUNO_API_KEY
from ai_generator import generate_listing_copy
from pdf_generator import generate_pdf
from video_generator import generate_video
from instagram_generator import generate_instagram_post
from story_generator import generate_instagram_story
from carousel_generator import generate_carousel
from music_generator import generate_music, init_suno_key
from voiceover_generator import generate_voiceover_script, generate_voiceover_script_scenes, generate_voiceover_audio
from email_generator import generate_email_html
from template_settings import load_settings, save_settings, DEFAULT_SETTINGS, ASSETS_DIR
import supabase_client as sb
import uploadpost_client as up

BASE_DIR = Path(__file__).parent
GENERATED_DIR = BASE_DIR / "generated"
GENERATED_DIR.mkdir(exist_ok=True)

app = FastAPI(title="ListaPro")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.mount("/generated", StaticFiles(directory=str(GENERATED_DIR)), name="generated")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Initialize Suno API key
init_suno_key(SUNO_API_KEY)

# In-memory video task tracker
_video_tasks: dict[str, dict] = {}


async def _run_video_task(job_id: str, property_data: dict, photo_paths: list[str],
                          frase_gancho: str = "", voiceover_path: str = "",
                          video_type: str = "reel"):
    """Background task: generate music via Suno, then render video with Remotion."""
    job_dir = GENERATED_DIR / job_id
    video_filename = f"listapro_{job_id}.mp4"
    output_path = str(job_dir / video_filename)
    props_path = str(job_dir / "props.json")

    settings = load_settings()

    def _set_status(status: str, **kwargs):
        _video_tasks[job_id] = {"status": status, **kwargs}
        sb.update_listing_video(job_id, status, **kwargs)

    _set_status("generating_music")

    # Step 1: Generate background music via Suno API
    music_url = ""
    if SUNO_API_KEY:
        try:
            music_style = settings["music"]["style"]
            negative_tags = settings["music"]["negative_tags"]
            music_result = await generate_music(
                style=music_style,
                negative_tags=negative_tags,
            )
            if music_result["status"] == "ready":
                music_url = music_result["audio_url"]
                print(f"[{job_id}] Music ready: {music_url[:60]}...")
            else:
                print(f"[{job_id}] Music failed: {music_result}")
        except Exception as e:
            print(f"[{job_id}] Music exception: {type(e).__name__}: {e}")

    # Step 2: Render video with Remotion (with or without music)
    _set_status("rendering")

    # In supabase mode, ensure branding assets are cached locally
    branding = settings.get("branding")
    if sb.is_supabase_mode() and branding:
        branding = sb.ensure_branding_local(branding)

    video_style = settings["video"].get("video_style", "elegante")
    result = await generate_video(
        property_data, photo_paths, output_path, props_path,
        music_url=music_url,
        video_colors=settings["video"],
        branding=branding,
        frase_gancho=frase_gancho,
        video_style=video_style,
        voiceover_path=voiceover_path,
        video_type=video_type,
    )

    if result["status"] == "ready":
        video_storage_path = None
        # Upload video to Supabase Storage
        if sb.is_supabase_mode():
            video_storage_path = f"{job_id}/{video_filename}"
            sb.upload_file_from_path("listings", video_storage_path, output_path)

        _video_tasks[job_id] = {
            "status": "ready",
            "filename": f"{job_id}/{video_filename}",
        }
        sb.update_listing_video(job_id, "ready", video_storage_path=video_storage_path)
    else:
        error_msg = result.get("error", "Error desconocido")
        _video_tasks[job_id] = {"status": "failed", "error": error_msg}
        sb.update_listing_video(job_id, "failed", video_error=error_msg)


@app.get("/plantilla", response_class=HTMLResponse)
async def template_editor(request: Request, saved: bool = False, reset: bool = False):
    settings = load_settings()
    branding = settings.get("branding", {})

    if sb.is_supabase_mode():
        logo_url = sb.get_public_url("branding", "logo.png") if branding.get("logo_path") else ""
        agent_photo_url = sb.get_public_url("branding", "agent_photo.png") if branding.get("agent_photo_path") else ""
    else:
        logo_exists = bool(branding.get("logo_path")) and (GENERATED_DIR / branding["logo_path"]).exists()
        photo_exists = bool(branding.get("agent_photo_path")) and (GENERATED_DIR / branding["agent_photo_path"]).exists()
        logo_url = f"/generated/{branding['logo_path']}" if logo_exists else ""
        agent_photo_url = f"/generated/{branding['agent_photo_path']}" if photo_exists else ""

    return templates.TemplateResponse("template_editor.html", {
        "request": request,
        "settings": settings,
        "saved": saved,
        "reset": reset,
        "logo_url": logo_url,
        "agent_photo_url": agent_photo_url,
    })


@app.post("/plantilla/guardar")
async def save_template(request: Request):
    form = await request.form()
    form_data = {}

    # Extract text fields
    for key in form:
        value = form[key]
        if isinstance(value, str):
            form_data[key] = value

    # Handle file uploads (logo, agent_photo)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    for field_name, filename in [("logo", "logo.png"), ("agent_photo", "agent_photo.png")]:
        upload = form.get(field_name)
        if upload and hasattr(upload, "filename") and upload.filename:
            content = await upload.read()
            if content and len(content) > 0:
                # Always save locally so generators use the latest version
                dest = ASSETS_DIR / filename
                dest.write_bytes(content)
                if sb.is_supabase_mode():
                    sb.upload_branding_asset(filename, content)
                form_data[f"{field_name}_path"] = f"assets/{filename}"

    save_settings(form_data)
    return RedirectResponse("/plantilla?saved=1", status_code=303)


@app.get("/plantilla/reset")
async def reset_template():
    from template_settings import SETTINGS_FILE
    if sb.is_supabase_mode():
        sb.delete_template_settings()
        sb.delete_branding_assets()
    if SETTINGS_FILE.exists():
        SETTINGS_FILE.unlink()
    if ASSETS_DIR.exists():
        shutil.rmtree(ASSETS_DIR)
    return RedirectResponse("/plantilla?reset=1", status_code=303)


@app.get("/historial", response_class=HTMLResponse)
async def historial(request: Request):
    import datetime as _dt

    raw_listings = sb.list_listings()
    listings = []
    for row in raw_listings:
        pd = row.get("property_data", {})
        country_key = pd.get("pais", "mexico")
        country = COUNTRIES.get(country_key, COUNTRIES["mexico"])
        precio = pd.get("precio", 0)
        try:
            precio_fmt = format_price(float(precio), country_key)
        except (ValueError, TypeError):
            precio_fmt = ""

        job_id = row["id"]
        job_dir = GENERATED_DIR / job_id

        # Build download URLs — check disk as fallback for local mode
        pdf_url = ""
        if row.get("pdf_storage_path"):
            pdf_url = f"/descargar/{job_id}/{Path(row['pdf_storage_path']).name}"
        elif job_dir.exists():
            pdf_files = list(job_dir.glob("*.pdf"))
            if pdf_files:
                pdf_url = f"/descargar/{job_id}/{pdf_files[0].name}"

        video_url = ""
        if row.get("video_storage_path"):
            video_url = f"/descargar/{job_id}/{Path(row['video_storage_path']).name}"
        elif job_dir.exists():
            mp4_files = list(job_dir.glob("*.mp4"))
            if mp4_files:
                video_url = f"/descargar/{job_id}/{mp4_files[0].name}"

        # Detect video_status from disk if JSON says pending but mp4 exists
        video_status = row.get("video_status", "")
        if video_status in ("pending", "rendering") and video_url:
            video_status = "ready"

        # Detect overall status from disk
        status = row.get("status", "")
        if status == "processing" and pdf_url:
            status = "ready"

        # Fallback created_at from file modification time
        created_at = row.get("created_at", "")
        if not created_at and job_dir.exists():
            listing_json = job_dir / "listing.json"
            ref_file = listing_json if listing_json.exists() else job_dir
            mtime = ref_file.stat().st_mtime
            created_at = _dt.datetime.fromtimestamp(mtime).isoformat()

        listings.append({
            "id": job_id,
            "tipo_propiedad": pd.get("tipo_propiedad", ""),
            "operacion": pd.get("operacion", ""),
            "ciudad": pd.get("ciudad", ""),
            "pais_nombre": country["name"],
            "precio_fmt": precio_fmt,
            "status": status,
            "video_status": video_status,
            "pdf_url": pdf_url,
            "video_url": video_url,
            "created_at": created_at,
        })

    return templates.TemplateResponse("historial.html", {
        "request": request,
        "listings": listings,
    })


@app.get("/", response_class=HTMLResponse)
async def show_form(request: Request, error: Optional[str] = None):
    return templates.TemplateResponse("form.html", {
        "request": request,
        "countries": COUNTRIES,
        "property_types": PROPERTY_TYPES,
        "operations": OPERATIONS,
        "amenities": AMENITIES,
        "error": error,
    })


@app.post("/api/voiceover/generate-script")
async def api_generate_script(request: Request):
    """Generate voiceover script scenes via AJAX during form wizard."""
    data = await request.json()
    property_data = data.get("property_data", {})
    video_type = data.get("video_type", "tour")
    tone = data.get("vo_tone", "profesional")
    context = data.get("vo_context", "")
    lang = data.get("idioma", "es")

    scenes = []
    script = ""

    try:
        scenes = generate_voiceover_script_scenes(
            property_data, video_type=video_type,
            tone=tone, context=context, lang=lang,
        )
    except Exception as e:
        print(f"API script generation error: {e}")

    if not scenes:
        try:
            script = generate_voiceover_script(
                property_data, video_type=video_type,
                tone=tone, context=context, lang=lang,
            )
        except Exception as e2:
            print(f"API flat script fallback error: {e2}")

    return JSONResponse({"scenes": scenes, "script": script})


@app.post("/generar", response_class=HTMLResponse)
async def generar_listado(
    request: Request,
    tipo_propiedad: str = Form(...),
    operacion: str = Form(...),
    pais: str = Form(...),
    ciudad: str = Form(...),
    direccion: str = Form(""),
    precio: float = Form(...),
    recamaras: Optional[str] = Form(None),
    banos: Optional[str] = Form(None),
    m2_construidos: str = Form(...),
    m2_terreno: Optional[str] = Form(None),
    estacionamientos: Optional[str] = Form(None),
    pisos: Optional[str] = Form(None),
    amenidades: list[str] = Form(default=[]),
    otras_amenidades: str = Form(""),
    agente_nombre: str = Form(...),
    agente_telefono: str = Form(...),
    agente_email: str = Form(""),
    agencia_nombre: str = Form(""),
    notas: str = Form(""),
    idioma: str = Form("es"),
    generar_story: Optional[str] = Form(None),
    generar_carousel: Optional[str] = Form(None),
    video_type: str = Form("reel"),
    generar_voiceover: Optional[str] = Form(None),
    vo_voice: str = Form("femenina"),
    vo_tone: str = Form("profesional"),
    vo_context: str = Form(""),
    scenes_data: str = Form(""),
    foto_portada: UploadFile = File(default=None),
    fotos_extra: list[UploadFile] = File(default=[]),
):
    # Collect property data
    property_data = {
        "tipo_propiedad": tipo_propiedad,
        "operacion": operacion,
        "pais": pais,
        "ciudad": ciudad,
        "direccion": direccion,
        "precio": precio,
        "recamaras": recamaras or "0",
        "banos": banos or "0",
        "m2_construidos": m2_construidos,
        "m2_terreno": m2_terreno or "",
        "estacionamientos": estacionamientos or "0",
        "pisos": pisos or "1",
        "amenidades": amenidades,
        "otras_amenidades": otras_amenidades,
        "agente_nombre": agente_nombre,
        "agente_telefono": agente_telefono,
        "agente_email": agente_email,
        "agencia_nombre": agencia_nombre,
        "notas": notas,
        "idioma": idioma,
        "video_type": video_type,
    }

    # Save uploaded photos to temp dir
    job_id = str(uuid.uuid4())[:8]
    job_dir = GENERATED_DIR / job_id
    job_dir.mkdir(exist_ok=True)
    photos_dir = job_dir / "photos"
    photos_dir.mkdir(exist_ok=True)

    photo_paths = []

    # Cover photo goes first (index 0 = hero in PDF)
    if foto_portada and foto_portada.filename and foto_portada.size and foto_portada.size > 0:
        ext = Path(foto_portada.filename).suffix or ".jpg"
        cover_path = photos_dir / f"portada{ext}"
        content = await foto_portada.read()
        cover_path.write_bytes(content)
        photo_paths.append(str(cover_path))

    # Extra photos follow
    for foto in fotos_extra:
        if foto.filename and foto.size and foto.size > 0:
            ext = Path(foto.filename).suffix or ".jpg"
            photo_name = f"extra_{len(photo_paths) + 1}{ext}"
            photo_path = photos_dir / photo_name
            content = await foto.read()
            photo_path.write_bytes(content)
            photo_paths.append(str(photo_path))

    # If no photos, use placeholder
    if not photo_paths:
        placeholder = BASE_DIR / "static" / "placeholder-house.jpg"
        if placeholder.exists():
            photo_paths.append(str(placeholder))

    # Generate AI copy
    try:
        ai_copy = generate_listing_copy(property_data)
    except Exception as e:
        return templates.TemplateResponse("form.html", {
            "request": request,
            "countries": COUNTRIES,
            "property_types": PROPERTY_TYPES,
            "operations": OPERATIONS,
            "amenities": AMENITIES,
            "error": f"Error al generar textos: {str(e)}. Verifica tu OPENAI_API_KEY.",
        })

    # Upload photos to Supabase Storage
    photo_storage_paths = []
    if sb.is_supabase_mode():
        for p in photo_paths:
            path_obj = Path(p)
            if path_obj.exists() and str(path_obj).startswith(str(GENERATED_DIR)):
                rel = path_obj.relative_to(GENERATED_DIR)
                storage_path = str(rel)
                sb.upload_file_from_path("listings", storage_path, p)
                photo_storage_paths.append(storage_path)

    # Save listing to Supabase DB
    sb.save_listing(job_id, property_data, ai_copy, photo_storage_paths)

    # Generate PDF
    pdf_filename = f"listapro_{job_id}.pdf"
    pdf_path = job_dir / pdf_filename

    settings = load_settings()

    try:
        country = COUNTRIES.get(pais, COUNTRIES["mexico"])
        precio_fmt = format_price(precio, pais)

        pdf_data = {
            **property_data,
            "precio_formateado": precio_fmt,
            "pais_nombre": country["name"],
            "descripcion": ai_copy.get("descripcion_pdf", ""),
        }
        pdf_template = settings["pdf"].get("pdf_template", "clasico")

        # In supabase mode, ensure branding assets are cached locally for PDF
        branding = settings.get("branding")
        if sb.is_supabase_mode() and branding:
            branding = sb.ensure_branding_local(branding)

        generate_pdf(pdf_data, photo_paths, str(pdf_path), color_overrides=settings["pdf"], template=pdf_template, branding=branding, lang=idioma)
    except Exception as e:
        return templates.TemplateResponse("form.html", {
            "request": request,
            "countries": COUNTRIES,
            "property_types": PROPERTY_TYPES,
            "operations": OPERATIONS,
            "amenities": AMENITIES,
            "error": f"Error al generar PDF: {str(e)}",
        })

    # Save PDF path (always, so local mode results page works)
    pdf_storage_path = f"{job_id}/{pdf_filename}"
    sb.update_listing_pdf(job_id, pdf_storage_path)
    if sb.is_supabase_mode():
        sb.upload_file_from_path("listings", pdf_storage_path, str(pdf_path))

    # Generate Instagram Post Image (1080x1350)
    instagram_filename = f"instagram_{job_id}.png"
    instagram_path = job_dir / instagram_filename
    try:
        cover = photo_paths[0] if photo_paths else str(BASE_DIR / "static" / "placeholder-house.jpg")
        insta_data = {
            **property_data,
            "precio_formateado": precio_fmt,
            "pais_nombre": country["name"],
        }
        generate_instagram_post(
            insta_data, cover, str(instagram_path),
            color_overrides=settings["pdf"], branding=branding, lang=idioma,
        )
        if sb.is_supabase_mode() and instagram_path.exists():
            sb.upload_file_from_path("listings", f"{job_id}/{instagram_filename}", str(instagram_path))
    except Exception as e:
        print(f"[{job_id}] Instagram image error: {e}")
        instagram_filename = ""

    # Generate Instagram Story (optional, 1080x1920)
    story_filename = ""
    if generar_story:
        try:
            story_filename = f"story_{job_id}.png"
            story_path = job_dir / story_filename
            generate_instagram_story(
                insta_data, cover, str(story_path),
                color_overrides=settings["pdf"], branding=branding, lang=idioma,
            )
            if sb.is_supabase_mode() and story_path.exists():
                sb.upload_file_from_path("listings", f"{job_id}/{story_filename}", str(story_path))
        except Exception as e:
            print(f"[{job_id}] Story error: {e}")
            story_filename = ""

    # Generate Instagram Carousel (optional, multiple slides + ZIP)
    carousel_slides = []
    carousel_zip = ""
    if generar_carousel:
        try:
            carousel_dir = job_dir / "carousel"
            result_carousel = generate_carousel(
                insta_data, photo_paths, str(carousel_dir),
                color_overrides=settings["pdf"], branding=branding, lang=idioma,
            )
            carousel_slides = [
                f"{job_id}/carousel/{Path(s).name}" for s in result_carousel["slides"]
            ]
            carousel_zip = f"{job_id}/carousel/{Path(result_carousel['zip_path']).name}"
            if sb.is_supabase_mode():
                for s in result_carousel["slides"]:
                    rel = f"{job_id}/carousel/{Path(s).name}"
                    sb.upload_file_from_path("listings", rel, s)
                sb.upload_file_from_path("listings", carousel_zip, result_carousel["zip_path"])
        except Exception as e:
            print(f"[{job_id}] Carousel error: {e}")
            carousel_slides = []
            carousel_zip = ""

    # Generate Email HTML
    email_filename = ""
    try:
        email_data = {
            **property_data,
            "precio_formateado": precio_fmt,
        }
        email_result = generate_email_html(
            email_data, ai_copy,
            cover_image_path=cover,
            agent_name=property_data.get("agente_nombre", ""),
            agent_phone=property_data.get("agente_telefono", ""),
            agency_name=branding.get("agency_name", "") if branding else "",
            lang=idioma,
        )
        email_filename = f"email_{job_id}.html"
        email_path = job_dir / email_filename
        email_path.write_text(email_result["html"], encoding="utf-8")
        if sb.is_supabase_mode():
            sb.upload_file_from_path("listings", f"{job_id}/{email_filename}", str(email_path))
    except Exception as e:
        print(f"[{job_id}] Email generation error: {e}")
        email_filename = ""

    # Save all asset paths to DB
    sb.update_listing_assets(
        job_id,
        instagram_storage_path=f"{job_id}/{instagram_filename}" if instagram_filename else "",
        story_storage_path=f"{job_id}/{story_filename}" if story_filename else "",
        carousel_storage_paths=carousel_slides,
        carousel_zip_path=carousel_zip,
        email_storage_path=f"{job_id}/{email_filename}" if email_filename else "",
    )

    # Voiceover flow
    import json as _json
    voiceover_path = ""

    if generar_voiceover and scenes_data:
        # NEW FLOW: scenes were already reviewed in the wizard
        print(f"[{job_id}] Voiceover with pre-reviewed scenes (voice={vo_voice}, type={video_type})")
        scenes = []
        try:
            scenes = _json.loads(scenes_data)
        except _json.JSONDecodeError:
            print(f"[{job_id}] Failed to parse scenes_data JSON from wizard")

        if scenes:
            full_script = " ".join(s.get("text", "") for s in scenes if s.get("text", "").strip())
            print(f"[{job_id}] Assembled script from {len(scenes)} scenes: {len(full_script)} chars")

            if full_script.strip():
                # Generate voiceover audio with timestamps
                voiceover_path = str(job_dir / "voiceover.mp3")
                vo_result = generate_voiceover_audio(
                    full_script, voice=vo_voice, output_path=voiceover_path,
                    scenes=scenes,
                )

                if vo_result["status"] != "ready":
                    print(f"[{job_id}] Voiceover audio error: {vo_result.get('error')}")
                    voiceover_path = ""
                else:
                    # Upload voiceover to Supabase
                    if sb.is_supabase_mode():
                        sb.upload_file_from_path("listings", f"{job_id}/voiceover.mp3", voiceover_path)

                # Save scene timings — photos are already in scene order
                elevenlabs_timings = vo_result.get("scene_timings", []) if vo_result.get("status") == "ready" else []
                scene_timings = []
                for i, scene in enumerate(scenes):
                    photo_name = Path(photo_paths[i]).name if i < len(photo_paths) else ""
                    if elevenlabs_timings and i < len(elevenlabs_timings):
                        timing = elevenlabs_timings[i]
                        scene_timings.append({
                            "id": scene.get("id", ""),
                            "words": len(scene.get("text", "").split()),
                            "photo": photo_name,
                            "weight": timing.get("weight", 0),
                            "start": timing.get("start", 0),
                            "end": timing.get("end", 0),
                        })
                    else:
                        scene_timings.append({
                            "id": scene.get("id", ""),
                            "words": len(scene.get("text", "").split()),
                            "photo": photo_name,
                        })

                timings_path = job_dir / "scene_timings.json"
                timings_path.write_text(_json.dumps(scene_timings, ensure_ascii=False))
                print(f"[{job_id}] Scene timings saved: {len(scene_timings)} scenes")

    elif generar_voiceover and not scenes_data:
        # OLD FLOW fallback: generate script server-side and show review page
        print(f"[{job_id}] Voiceover enabled (old flow) — generating script (voice={vo_voice}, tone={vo_tone})")
        scenes = []
        script = ""
        try:
            scenes = generate_voiceover_script_scenes(
                property_data, video_type=video_type,
                tone=vo_tone, context=vo_context, lang=idioma,
            )
        except Exception as e:
            print(f"[{job_id}] Scene generation error: {e}")

        if not scenes:
            try:
                script = generate_voiceover_script(
                    property_data, video_type=video_type,
                    tone=vo_tone, context=vo_context, lang=idioma,
                )
            except Exception as e:
                print(f"[{job_id}] Flat script error: {e}")

        if scenes or script:
            review_photos = []
            for p in photo_paths:
                pname = Path(p).name
                review_photos.append({
                    "filename": pname,
                    "url": f"/descargar/{job_id}/photos/{pname}",
                    "label": "Portada" if pname.startswith("portada") else f"Foto {pname.replace('extra_', '').split('.')[0]}",
                })
            return templates.TemplateResponse("script_review.html", {
                "request": request,
                "job_id": job_id,
                "script": script,
                "scenes": scenes,
                "scenes_json": _json.dumps(scenes, ensure_ascii=False),
                "review_photos": review_photos,
                "review_photos_json": _json.dumps(review_photos, ensure_ascii=False),
                "vo_voice": vo_voice,
                "vo_tone": vo_tone,
                "video_type": video_type,
            })
        else:
            print(f"[{job_id}] Voiceover script generation failed, falling back to normal video.")
    else:
        print(f"[{job_id}] Voiceover not requested")

    # Launch video rendering in background and redirect
    video_data = {
        **property_data,
        "precio_formateado": precio_fmt,
        "pais_nombre": country["name"],
    }
    frase_gancho = ai_copy.get("frase_gancho", "")
    asyncio.create_task(_run_video_task(
        job_id, video_data, photo_paths,
        frase_gancho=frase_gancho,
        voiceover_path=voiceover_path if voiceover_path and Path(voiceover_path).exists() else "",
        video_type=video_type,
    ))

    # Redirect to persistent results page
    return RedirectResponse(f"/resultado/{job_id}", status_code=303)


@app.get("/resultado/{job_id}", response_class=HTMLResponse)
async def resultado(request: Request, job_id: str):
    """Persistent results page — loads listing from DB or local files."""
    listing = sb.get_listing(job_id)
    if not listing:
        job_dir = GENERATED_DIR / job_id
        if not job_dir.exists():
            return RedirectResponse("/", status_code=302)
        listing = {}

    pd = listing.get("property_data", {})
    ai_copy = listing.get("ai_copy", {})
    country_key = pd.get("pais", "mexico")
    country = COUNTRIES.get(country_key, COUNTRIES["mexico"])

    # Get Upload Post profiles for publish buttons
    upload_profiles = []
    try:
        upload_profiles = up.get_profiles()
    except Exception:
        pass

    # Load email HTML for preview if it exists
    email_storage_path = listing.get("email_storage_path", "")
    email_html_preview = ""
    if email_storage_path:
        email_local = GENERATED_DIR / email_storage_path
        if email_local.exists():
            try:
                email_html_preview = email_local.read_text(encoding="utf-8")
            except Exception:
                pass

    return templates.TemplateResponse("results.html", {
        "request": request,
        "tipo_propiedad": pd.get("tipo_propiedad", ""),
        "operacion": pd.get("operacion", ""),
        "ciudad": pd.get("ciudad", ""),
        "pais_nombre": country["name"],
        "pdf_filename": listing.get("pdf_storage_path", ""),
        "instagram_filename": listing.get("instagram_storage_path", ""),
        "story_filename": listing.get("story_storage_path", ""),
        "carousel_slides": listing.get("carousel_storage_paths") or [],
        "carousel_zip": listing.get("carousel_zip_path", ""),
        "copy_instagram": ai_copy.get("copy_instagram", ""),
        "copy_email": ai_copy.get("copy_email", ""),
        "email_filename": email_storage_path,
        "email_html_preview": email_html_preview,
        "job_id": job_id,
        "error": None,
        "upload_profiles": upload_profiles,
    })


@app.post("/generar-con-voiceover", response_class=HTMLResponse)
async def generar_con_voiceover(
    request: Request,
    job_id: str = Form(...),
    vo_script: str = Form(""),
    vo_voice: str = Form("femenina"),
    video_type: str = Form("reel"),
    scenes_data: str = Form(""),
):
    """Generate voiceover audio from reviewed script, then launch video rendering.

    If scenes_data is provided (JSON), photos are reordered to match scene assignments
    and the voiceover script is assembled from scene texts in order.
    """
    import json as _json

    listing = sb.get_listing(job_id)
    if not listing:
        return RedirectResponse("/", status_code=302)

    job_dir = GENERATED_DIR / job_id

    # Parse scene data if provided
    scenes = []
    if scenes_data:
        try:
            scenes = _json.loads(scenes_data)
        except _json.JSONDecodeError:
            print(f"[{job_id}] Failed to parse scenes_data JSON")

    # Build the full voiceover script from scenes (or use flat script)
    if scenes:
        # Concatenate scene texts in order, separated by pauses
        full_script = " ".join(s.get("text", "") for s in scenes if s.get("text", "").strip())
        print(f"[{job_id}] Assembled script from {len(scenes)} scenes: {len(full_script)} chars")
    else:
        full_script = vo_script
        print(f"[{job_id}] Using flat script: {len(full_script)} chars")

    if not full_script.strip():
        return RedirectResponse(f"/resultado/{job_id}", status_code=303)

    # Generate voiceover audio with ElevenLabs (with timestamps if scenes available)
    voiceover_path = str(job_dir / "voiceover.mp3")
    vo_result = generate_voiceover_audio(
        full_script, voice=vo_voice, output_path=voiceover_path,
        scenes=scenes if scenes else None,
    )

    if vo_result["status"] != "ready":
        print(f"[{job_id}] Voiceover audio error: {vo_result.get('error')}")
        voiceover_path = ""

    # Store ElevenLabs scene timings if available (precise timestamps)
    elevenlabs_timings = vo_result.get("scene_timings", [])

    # Upload voiceover to Supabase if available
    if voiceover_path and Path(voiceover_path).exists() and sb.is_supabase_mode():
        sb.upload_file_from_path("listings", f"{job_id}/voiceover.mp3", voiceover_path)

    # Reconstruct data needed for video generation
    pd = listing.get("property_data", {})
    ai_copy = listing.get("ai_copy", {})
    country_key = pd.get("pais", "mexico")
    country = COUNTRIES.get(country_key, COUNTRIES["mexico"])
    precio = float(pd.get("precio", 0))
    precio_fmt = format_price(precio, country_key)

    video_data = {
        **pd,
        "precio_formateado": precio_fmt,
        "pais_nombre": country["name"],
    }

    # Rebuild photo_paths from local files (only originals: portada* and extra_*)
    photos_dir = job_dir / "photos"
    all_original_photos = {}  # filename -> full path
    photo_paths = []
    if photos_dir.exists():
        for p in photos_dir.iterdir():
            if p.is_file() and (p.name.startswith("portada") or p.name.startswith("extra_")):
                all_original_photos[p.name] = str(p)

    # If scenes have photo assignments, reorder photos to match scene order
    if scenes:
        scene_photo_order = []
        used_photos = set()
        for scene in scenes:
            photo_filename = scene.get("photo", "")
            if photo_filename and photo_filename in all_original_photos:
                scene_photo_order.append(all_original_photos[photo_filename])
                used_photos.add(photo_filename)

        # Add any unassigned photos at the end (cover first)
        for name in sorted(all_original_photos.keys()):
            if name not in used_photos:
                scene_photo_order.append(all_original_photos[name])

        photo_paths = scene_photo_order
        print(f"[{job_id}] Scene-ordered photos: {[Path(p).name for p in photo_paths]}")

        # Use ElevenLabs precise timestamps if available, else word-count estimation
        if elevenlabs_timings:
            scene_timings = []
            for i, scene in enumerate(scenes):
                timing = elevenlabs_timings[i] if i < len(elevenlabs_timings) else {}
                scene_timings.append({
                    "id": scene.get("id", ""),
                    "words": len(scene.get("text", "").split()),
                    "photo": scene.get("photo", ""),
                    "weight": timing.get("weight", 0),
                    "start": timing.get("start", 0),
                    "end": timing.get("end", 0),
                })
            print(f"[{job_id}] Using ElevenLabs precise timestamps for {len(scene_timings)} scenes")
        else:
            scene_timings = []
            for scene in scenes:
                text = scene.get("text", "")
                words = len(text.split()) if text.strip() else 0
                scene_timings.append({
                    "id": scene.get("id", ""),
                    "words": words,
                    "photo": scene.get("photo", ""),
                })
            print(f"[{job_id}] Using word-count estimation for {len(scene_timings)} scenes")
        # Save scene timings for video generator
        timings_path = job_dir / "scene_timings.json"
        timings_path.write_text(_json.dumps(scene_timings, ensure_ascii=False))
    else:
        # No scenes — use default photo order
        cover = sorted([v for k, v in all_original_photos.items() if k.startswith("portada")])
        extras = sorted([v for k, v in all_original_photos.items() if k.startswith("extra_")])
        photo_paths = cover + extras

    frase_gancho = ai_copy.get("frase_gancho", "")
    asyncio.create_task(_run_video_task(
        job_id, video_data, photo_paths,
        frase_gancho=frase_gancho,
        voiceover_path=voiceover_path if voiceover_path and Path(voiceover_path).exists() else "",
        video_type=video_type,
    ))

    return RedirectResponse(f"/resultado/{job_id}", status_code=303)


@app.post("/api/video/retry/{job_id}")
async def video_retry(job_id: str):
    """Retry video generation for a failed or timed-out job."""
    listing = sb.get_listing(job_id)
    if not listing:
        return JSONResponse({"success": False, "error": "Listado no encontrado"}, status_code=404)

    job_dir = GENERATED_DIR / job_id
    pd = listing.get("property_data", {})
    ai_copy = listing.get("ai_copy", {})
    country_key = pd.get("pais", "mexico")
    country = COUNTRIES.get(country_key, COUNTRIES["mexico"])
    precio = float(pd.get("precio", 0))
    precio_fmt = format_price(precio, country_key)

    video_data = {**pd, "precio_formateado": precio_fmt, "pais_nombre": country["name"]}

    photos_dir = job_dir / "photos"
    photo_paths = []
    if photos_dir.exists():
        all_photos = [p for p in photos_dir.iterdir() if p.is_file()]
        cover = [str(p) for p in all_photos if p.name.startswith("portada")]
        extras = sorted([str(p) for p in all_photos if p.name.startswith("extra_")])
        photo_paths = cover + extras

    if not photo_paths:
        return JSONResponse({"success": False, "error": "No se encontraron fotos"}, status_code=404)

    frase_gancho = ai_copy.get("frase_gancho", "")
    voiceover_path = str(job_dir / "voiceover.mp3")
    if not Path(voiceover_path).exists():
        voiceover_path = ""

    video_type = listing.get("property_data", {}).get("video_type", "reel")

    # Clear previous failed state
    _video_tasks.pop(job_id, None)

    asyncio.create_task(_run_video_task(
        job_id, video_data, photo_paths,
        frase_gancho=frase_gancho,
        voiceover_path=voiceover_path,
        video_type=video_type,
    ))

    return JSONResponse({"success": True, "message": "Reintentando generación de video"})


@app.get("/video/status/{job_id}")
async def video_status(job_id: str):
    """Poll endpoint for video rendering status."""
    # Check in-memory first (works in both modes during rendering)
    task = _video_tasks.get(job_id)
    if task:
        # If status is "rendering" but the .mp4 already exists on disk,
        # the render finished but status wasn't updated (e.g., server restart).
        if task.get("status") == "rendering":
            job_dir = GENERATED_DIR / job_id
            mp4_files = list(job_dir.glob("*.mp4")) if job_dir.exists() else []
            if mp4_files and mp4_files[0].stat().st_size > 100_000:
                video_filename = f"{job_id}/{mp4_files[0].name}"
                _video_tasks[job_id] = {"status": "ready", "filename": video_filename}
                return JSONResponse({"status": "ready", "filename": video_filename})
        return JSONResponse(task)

    # Fallback: check if video file exists on disk (covers server restart scenarios)
    job_dir = GENERATED_DIR / job_id
    if job_dir.exists():
        mp4_files = list(job_dir.glob("*.mp4"))
        if mp4_files and mp4_files[0].stat().st_size > 100_000:
            video_filename = f"{job_id}/{mp4_files[0].name}"
            _video_tasks[job_id] = {"status": "ready", "filename": video_filename}
            return JSONResponse({"status": "ready", "filename": video_filename})

    # Fallback to Supabase DB (e.g., after server restart)
    if sb.is_supabase_mode():
        db_status = sb.get_video_status(job_id)
        if db_status:
            return JSONResponse(db_status)

    return JSONResponse({"status": "not_found"})


@app.get("/descargar/{job_id}/{filename:path}")
async def descargar_archivo(job_id: str, filename: str):
    # Always check local disk first — file may exist locally even in supabase mode
    file_path = GENERATED_DIR / job_id / filename
    local_exists = file_path.exists()

    # In supabase mode, try redirect to public URL only if file is NOT local
    if sb.is_supabase_mode() and not local_exists:
        storage_path = f"{job_id}/{filename}"
        url = sb.get_public_url("listings", storage_path)
        if url:
            return RedirectResponse(url, status_code=302)

    # Serve from disk
    if not local_exists:
        return HTMLResponse("Archivo no encontrado", status_code=404)

    if filename.endswith(".mp4"):
        media_type = "video/mp4"
    elif filename.endswith(".png"):
        media_type = "image/png"
    elif filename.endswith(".zip"):
        media_type = "application/zip"
    else:
        media_type = "application/pdf"

    return FileResponse(
        str(file_path),
        media_type=media_type,
        filename=filename,
    )


# ---------------------------------------------------------------------------
# Upload Post: Publish to Social Media
# ---------------------------------------------------------------------------

@app.get("/api/upload-profiles")
async def api_upload_profiles():
    """Return connected Upload Post profiles for the frontend."""
    try:
        profiles = up.get_profiles()
        return JSONResponse({"success": True, "profiles": profiles})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


def _resolve_local_path(storage_path: str) -> str:
    """Resolve a storage path to a local file path."""
    # storage_path is like "job_id/filename.png"
    local = GENERATED_DIR / storage_path
    if local.exists():
        return str(local)
    return ""


def _check_ig_result(result: dict) -> dict:
    """Check Upload Post API response for nested Instagram errors.

    The API returns success:True at top level even when Instagram fails.
    We need to check results.instagram.success to get the real status.
    Also handles async upload responses (request_id) and scheduled (job_id).
    """
    if not isinstance(result, dict):
        return result

    # Async upload response — background processing started
    if result.get("request_id"):
        return {
            "success": True,
            "message": result.get("message", "Publicación en proceso..."),
            "request_id": result["request_id"],
        }

    # Scheduled response
    if result.get("job_id"):
        return {
            "success": True,
            "message": "Publicación programada",
            "job_id": result["job_id"],
        }

    # Synchronous response — check nested Instagram result
    ig = result.get("results", {}).get("instagram", {})
    if isinstance(ig, dict) and ig.get("success") is False:
        error_msg = ig.get("error", "Error desconocido de Instagram")
        return {"success": False, "error": error_msg}
    return result


@app.post("/api/publicar/post/{job_id}")
async def publicar_post(job_id: str, user: str = Form(...)):
    """Publish Instagram post image with caption."""
    listing = sb.get_listing(job_id)
    if not listing:
        return JSONResponse({"success": False, "error": "Listado no encontrado"}, status_code=404)

    instagram_path = _resolve_local_path(listing.get("instagram_storage_path", ""))
    if not instagram_path:
        return JSONResponse({"success": False, "error": "Imagen de post no encontrada"}, status_code=404)

    caption = listing.get("ai_copy", {}).get("copy_instagram", "")
    result = up.publish_instagram_post(user, instagram_path, caption)
    return JSONResponse(_check_ig_result(result))


@app.post("/api/publicar/story/{job_id}")
async def publicar_story(job_id: str, user: str = Form(...)):
    """Publish Instagram story."""
    listing = sb.get_listing(job_id)
    if not listing:
        return JSONResponse({"success": False, "error": "Listado no encontrado"}, status_code=404)

    story_path = _resolve_local_path(listing.get("story_storage_path", ""))
    if not story_path:
        return JSONResponse({"success": False, "error": "Imagen de story no encontrada"}, status_code=404)

    result = up.publish_instagram_story(user, story_path)
    return JSONResponse(_check_ig_result(result))


@app.post("/api/publicar/carousel/{job_id}")
async def publicar_carousel(job_id: str, user: str = Form(...), slides_order: str = Form("")):
    """Publish Instagram carousel. slides_order is comma-separated slide paths in desired order."""
    listing = sb.get_listing(job_id)
    if not listing:
        return JSONResponse({"success": False, "error": "Listado no encontrado"}, status_code=404)

    # Use custom order if provided, otherwise default
    if slides_order:
        slide_paths = [_resolve_local_path(s.strip()) for s in slides_order.split(",")]
        slide_paths = [p for p in slide_paths if p]
    else:
        slide_paths = [_resolve_local_path(s) for s in (listing.get("carousel_storage_paths") or [])]
        slide_paths = [p for p in slide_paths if p]

    if not slide_paths:
        return JSONResponse({"success": False, "error": "No hay slides de carrusel"}, status_code=404)

    caption = listing.get("ai_copy", {}).get("copy_instagram", "")
    result = up.publish_instagram_carousel(user, slide_paths, caption)
    return JSONResponse(_check_ig_result(result))


@app.post("/api/publicar/reel/{job_id}")
async def publicar_reel(job_id: str, user: str = Form(...)):
    """Publish Instagram reel video."""
    listing = sb.get_listing(job_id)
    if not listing:
        return JSONResponse({"success": False, "error": "Listado no encontrado"}, status_code=404)

    # Try storage path first, then fallback to finding .mp4 on disk
    video_storage = listing.get("video_storage_path") or ""
    video_path = _resolve_local_path(video_storage) if video_storage else ""
    if not video_path:
        # Fallback: find .mp4 file directly in job directory
        job_dir = GENERATED_DIR / job_id
        mp4_files = list(job_dir.glob("*.mp4")) if job_dir.exists() else []
        if mp4_files:
            video_path = str(mp4_files[0])

    if not video_path:
        return JSONResponse({"success": False, "error": "Video no encontrado"}, status_code=404)

    caption = listing.get("ai_copy", {}).get("copy_instagram", "")
    result = up.publish_instagram_reel(user, video_path, caption)
    return JSONResponse(_check_ig_result(result))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
