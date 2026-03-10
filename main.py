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
from music_generator import generate_music, init_suno_key
from template_settings import load_settings, save_settings, DEFAULT_SETTINGS, ASSETS_DIR
import supabase_client as sb

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


async def _run_video_task(job_id: str, property_data: dict, photo_paths: list[str]):
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

    result = await generate_video(
        property_data, photo_paths, output_path, props_path,
        music_url=music_url,
        video_colors=settings["video"],
        branding=branding,
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
        if upload and hasattr(upload, "filename") and upload.filename and upload.size and upload.size > 0:
            content = await upload.read()
            if sb.is_supabase_mode():
                sb.upload_branding_asset(filename, content)
            else:
                dest = ASSETS_DIR / filename
                dest.write_bytes(content)
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

        # Build download URLs
        pdf_url = ""
        if row.get("pdf_storage_path"):
            pdf_url = f"/descargar/{row['id']}/{Path(row['pdf_storage_path']).name}"
        video_url = ""
        if row.get("video_storage_path"):
            video_url = f"/descargar/{row['id']}/{Path(row['video_storage_path']).name}"

        listings.append({
            "id": row["id"],
            "tipo_propiedad": pd.get("tipo_propiedad", ""),
            "operacion": pd.get("operacion", ""),
            "ciudad": pd.get("ciudad", ""),
            "pais_nombre": country["name"],
            "precio_fmt": precio_fmt,
            "status": row.get("status", ""),
            "video_status": row.get("video_status", ""),
            "pdf_url": pdf_url,
            "video_url": video_url,
            "created_at": row.get("created_at", ""),
        })

    return templates.TemplateResponse("historial.html", {
        "request": request,
        "listings": listings,
        "is_supabase": sb.is_supabase_mode(),
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

        generate_pdf(pdf_data, photo_paths, str(pdf_path), color_overrides=settings["pdf"], template=pdf_template, branding=branding)
    except Exception as e:
        return templates.TemplateResponse("form.html", {
            "request": request,
            "countries": COUNTRIES,
            "property_types": PROPERTY_TYPES,
            "operations": OPERATIONS,
            "amenities": AMENITIES,
            "error": f"Error al generar PDF: {str(e)}",
        })

    # Upload PDF to Supabase Storage
    pdf_storage_path = f"{job_id}/{pdf_filename}"
    if sb.is_supabase_mode():
        sb.upload_file_from_path("listings", pdf_storage_path, str(pdf_path))
        sb.update_listing_pdf(job_id, pdf_storage_path)

    # Launch video rendering in background
    video_data = {
        **property_data,
        "precio_formateado": precio_fmt,
        "pais_nombre": country["name"],
    }
    asyncio.create_task(_run_video_task(job_id, video_data, photo_paths))

    # Render results (immediately, video renders in background)
    country = COUNTRIES.get(pais, COUNTRIES["mexico"])
    mensaje_wa = ai_copy.get("mensaje_whatsapp", "")

    return templates.TemplateResponse("results.html", {
        "request": request,
        "tipo_propiedad": tipo_propiedad,
        "operacion": operacion,
        "ciudad": ciudad,
        "pais_nombre": country["name"],
        "pdf_filename": f"{job_id}/{pdf_filename}",
        "copy_instagram": ai_copy.get("copy_instagram", ""),
        "mensaje_whatsapp": mensaje_wa,
        "mensaje_whatsapp_encoded": quote(mensaje_wa),
        "descripcion_pdf": ai_copy.get("descripcion_pdf", ""),
        "job_id": job_id,
        "error": None,
    })


@app.get("/video/status/{job_id}")
async def video_status(job_id: str):
    """Poll endpoint for video rendering status."""
    # Check in-memory first (works in both modes during rendering)
    task = _video_tasks.get(job_id)
    if task:
        return JSONResponse(task)

    # Fallback to Supabase DB (e.g., after server restart)
    if sb.is_supabase_mode():
        db_status = sb.get_video_status(job_id)
        if db_status:
            return JSONResponse(db_status)

    return JSONResponse({"status": "not_found"})


@app.get("/descargar/{job_id}/{filename}")
async def descargar_archivo(job_id: str, filename: str):
    # In supabase mode, redirect to public URL
    if sb.is_supabase_mode():
        storage_path = f"{job_id}/{filename}"
        url = sb.get_public_url("listings", storage_path)
        if url:
            return RedirectResponse(url, status_code=302)

    # Local mode: serve from disk
    file_path = GENERATED_DIR / job_id / filename
    if not file_path.exists():
        return HTMLResponse("Archivo no encontrado", status_code=404)

    if filename.endswith(".mp4"):
        media_type = "video/mp4"
    else:
        media_type = "application/pdf"

    return FileResponse(
        str(file_path),
        media_type=media_type,
        filename=filename,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
