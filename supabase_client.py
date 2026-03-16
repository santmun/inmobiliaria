"""Supabase client abstraction for ListaPro dual-mode storage."""
import json
from pathlib import Path
from typing import Optional, List
from config import SUPABASE_URL, SUPABASE_KEY, STORAGE_MODE

BASE_DIR = Path(__file__).parent
GENERATED_DIR = BASE_DIR / "generated"

_client = None


def _get_client():
    global _client
    if _client is None:
        from supabase import create_client
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


def is_supabase_mode() -> bool:
    return STORAGE_MODE == "supabase" and bool(SUPABASE_URL) and bool(SUPABASE_KEY)


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

def upload_file(bucket: str, storage_path: str, file_bytes: bytes, content_type: str = "application/octet-stream") -> str:
    """Upload a file to Supabase Storage. Returns public URL."""
    if not is_supabase_mode():
        return ""
    client = _get_client()
    client.storage.from_(bucket).upload(
        storage_path, file_bytes,
        file_options={"content-type": content_type, "upsert": "true"},
    )
    return client.storage.from_(bucket).get_public_url(storage_path)


def upload_file_from_path(bucket: str, storage_path: str, local_path: str) -> str:
    """Upload a local file to Supabase Storage. Returns public URL."""
    p = Path(local_path)
    if not p.exists():
        return ""
    content_type = _guess_content_type(p.suffix)
    return upload_file(bucket, storage_path, p.read_bytes(), content_type)


def get_public_url(bucket: str, storage_path: str) -> str:
    """Get public URL for a file in Supabase Storage."""
    if not is_supabase_mode():
        return ""
    return _get_client().storage.from_(bucket).get_public_url(storage_path)


def get_signed_url(bucket: str, storage_path: str, expires_in: int = 3600) -> str:
    """Get a signed URL for a file in Supabase Storage."""
    if not is_supabase_mode():
        return ""
    resp = _get_client().storage.from_(bucket).create_signed_url(storage_path, expires_in)
    return resp.get("signedURL", "")


def download_to_local(bucket: str, storage_path: str, local_path: str) -> bool:
    """Download a file from Supabase Storage to local path. Returns True on success."""
    if not is_supabase_mode():
        return False
    try:
        client = _get_client()
        data = client.storage.from_(bucket).download(storage_path)
        p = Path(local_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        return True
    except Exception:
        return False


def delete_storage_path(bucket: str, storage_paths: List[str]) -> None:
    """Delete files from Supabase Storage."""
    if not is_supabase_mode() or not storage_paths:
        return
    try:
        _get_client().storage.from_(bucket).remove(storage_paths)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Database: Listings
# ---------------------------------------------------------------------------

def save_listing(job_id: str, property_data: dict, ai_copy: dict = None, photo_paths: List[str] = None) -> None:
    """Insert a new listing record."""
    from datetime import datetime, timezone
    row = {
        "id": job_id,
        "property_data": property_data,
        "ai_copy": ai_copy or {},
        "photo_paths": photo_paths or [],
        "status": "processing",
        "video_status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    # Always save locally so voiceover and results flows work in local mode
    _save_listing_local(job_id, row)
    if not is_supabase_mode():
        return
    _get_client().table("listings").insert(row).execute()


def update_listing_pdf(job_id: str, pdf_storage_path: str) -> None:
    """Update listing with PDF storage path."""
    _update_listing_local(job_id, {"pdf_storage_path": pdf_storage_path})
    if not is_supabase_mode():
        return
    _get_client().table("listings").update({
        "pdf_storage_path": pdf_storage_path,
    }).eq("id", job_id).execute()


def update_listing_assets(job_id: str, **kwargs) -> None:
    """Update listing with optional asset storage paths.

    Accepted kwargs:
        instagram_storage_path, story_storage_path,
        carousel_storage_paths (list), carousel_zip_path
    """
    allowed = {"instagram_storage_path", "story_storage_path",
               "carousel_storage_paths", "carousel_zip_path",
               "email_storage_path"}
    data = {k: v for k, v in kwargs.items() if k in allowed and v}
    if not data:
        return
    _update_listing_local(job_id, data)
    if not is_supabase_mode():
        return
    _get_client().table("listings").update(data).eq("id", job_id).execute()


def update_listing_video(job_id: str, video_status: str, video_storage_path: str = None, video_error: str = None) -> None:
    """Update listing video status and path."""
    data = {"video_status": video_status}
    if video_storage_path:
        data["video_storage_path"] = video_storage_path
    if video_error:
        data["video_error"] = video_error
    if video_status == "ready":
        data["status"] = "ready"
    _update_listing_local(job_id, data)
    if not is_supabase_mode():
        return
    _get_client().table("listings").update(data).eq("id", job_id).execute()


def get_video_status(job_id: str) -> Optional[dict]:
    """Get video status for a listing. Returns None if not found."""
    if not is_supabase_mode():
        return None
    resp = _get_client().table("listings").select(
        "video_status, video_storage_path, video_error"
    ).eq("id", job_id).maybe_single().execute()
    if not resp.data:
        return None
    row = resp.data
    result = {"status": row["video_status"]}
    if row.get("video_storage_path"):
        result["filename"] = row["video_storage_path"]
    if row.get("video_error"):
        result["error"] = row["video_error"]
    return result


def get_listing(job_id: str) -> Optional[dict]:
    """Get a listing by job_id."""
    if not is_supabase_mode():
        return _load_listing_local(job_id)
    resp = _get_client().table("listings").select("*").eq("id", job_id).maybe_single().execute()
    return resp.data


def list_listings(limit: int = 50) -> List[dict]:
    """List all listings ordered by creation date (newest first)."""
    if not is_supabase_mode():
        return _list_listings_local(limit)
    resp = _get_client().table("listings").select(
        "id, property_data, status, video_status, pdf_storage_path, video_storage_path, created_at"
    ).order("created_at", desc=True).limit(limit).execute()
    return resp.data or []


# ---------------------------------------------------------------------------
# Database: Template Settings
# ---------------------------------------------------------------------------

def load_template_settings() -> Optional[dict]:
    """Load template settings from Supabase. Returns None if not found or not in supabase mode."""
    if not is_supabase_mode():
        return None
    resp = _get_client().table("template_settings").select("settings").eq("id", "default").maybe_single().execute()
    if resp.data:
        return resp.data["settings"]
    return None


def save_template_settings(settings: dict) -> None:
    """Upsert template settings to Supabase."""
    if not is_supabase_mode():
        return
    _get_client().table("template_settings").upsert({
        "id": "default",
        "settings": settings,
    }).execute()


def delete_template_settings() -> None:
    """Delete template settings from Supabase (for reset)."""
    if not is_supabase_mode():
        return
    try:
        _get_client().table("template_settings").delete().eq("id", "default").execute()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Branding helpers
# ---------------------------------------------------------------------------

def upload_branding_asset(filename: str, file_bytes: bytes) -> str:
    """Upload a branding asset (logo, agent_photo) to Supabase. Returns public URL."""
    content_type = _guess_content_type(Path(filename).suffix)
    return upload_file("branding", filename, file_bytes, content_type)


def ensure_branding_local(branding: dict) -> dict:
    """Download branding assets from Supabase to local cache for PDF generation.
    Always re-downloads to ensure the latest version is used.
    Returns branding dict with local paths."""
    if not is_supabase_mode():
        return branding

    cache_dir = GENERATED_DIR / "assets"
    cache_dir.mkdir(parents=True, exist_ok=True)
    result = dict(branding)

    for key, filename in [("logo_path", "logo.png"), ("agent_photo_path", "agent_photo.png")]:
        if branding.get(key):
            local_file = cache_dir / filename
            # Always re-download to pick up updated branding assets
            download_to_local("branding", filename, str(local_file))
            if local_file.exists():
                result[key] = f"assets/{filename}"

    return result


def delete_branding_assets() -> None:
    """Delete all branding assets from Supabase Storage."""
    delete_storage_path("branding", ["logo.png", "agent_photo.png"])


# ---------------------------------------------------------------------------
# Local JSON storage (fallback when Supabase is not configured)
# ---------------------------------------------------------------------------

def _listing_json_path(job_id: str) -> Path:
    return GENERATED_DIR / job_id / "listing.json"


def _save_listing_local(job_id: str, data: dict) -> None:
    """Save listing data as JSON in the job directory."""
    p = _listing_json_path(job_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, default=str), encoding="utf-8")


def _load_listing_local(job_id: str) -> Optional[dict]:
    """Load listing data from local JSON file."""
    p = _listing_json_path(job_id)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _update_listing_local(job_id: str, updates: dict) -> None:
    """Merge updates into the local listing JSON file."""
    existing = _load_listing_local(job_id)
    if existing is None:
        return
    existing.update(updates)
    _save_listing_local(job_id, existing)


def _list_listings_local(limit: int = 50) -> List[dict]:
    """List all local listings by scanning generated directories."""
    listings = []
    if not GENERATED_DIR.exists():
        return listings
    for d in sorted(GENERATED_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if not d.is_dir():
            continue
        listing_file = d / "listing.json"
        if listing_file.exists():
            try:
                data = json.loads(listing_file.read_text(encoding="utf-8"))
                listings.append(data)
            except (json.JSONDecodeError, OSError):
                continue
        if len(listings) >= limit:
            break
    return listings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _guess_content_type(suffix: str) -> str:
    types = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".gif": "image/gif",
        ".webp": "image/webp", ".pdf": "application/pdf",
        ".mp4": "video/mp4", ".mp3": "audio/mpeg",
    }
    return types.get(suffix.lower(), "application/octet-stream")
