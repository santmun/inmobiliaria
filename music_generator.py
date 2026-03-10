import asyncio
import httpx
from pathlib import Path

SUNO_BASE_URL = "https://api.sunoapi.org"


def _get_api_key() -> str:
    from config import SUNO_API_KEY
    return SUNO_API_KEY


# Keep for backwards compat but no longer needed
def init_suno_key(key: str):
    pass


async def generate_music(
    style: str = "elegant piano ambient cinematic",
    negative_tags: str = "vocals, singing, heavy metal, aggressive, loud",
) -> dict:
    """Generate a short instrumental track via Suno API.

    Returns dict with status and audio_url on success.
    """
    headers = {
        "Authorization": f"Bearer {_get_api_key()}",
        "Content-Type": "application/json",
    }

    body = {
        "customMode": True,
        "instrumental": True,
        "title": "ListaPro Background",
        "style": style,
        "model": "V4_5",
        "negativeTags": negative_tags,
        "callBackUrl": "https://example.com/noop",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{SUNO_BASE_URL}/api/v1/generate",
            headers=headers,
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 200:
            return {"status": "failed", "error": data.get("msg", "Unknown error")}

        task_id = data["data"]["taskId"]

    # Poll for completion (max 3 min, every 10s)
    for _ in range(18):
        await asyncio.sleep(10)
        result = await _poll_status(task_id)
        if result["status"] in ("ready", "failed"):
            return result

    return {"status": "failed", "error": "Music generation timed out after 3 minutes"}


async def _poll_status(task_id: str) -> dict:
    """Poll Suno API for music generation status."""
    headers = {"Authorization": f"Bearer {_get_api_key()}"}

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{SUNO_BASE_URL}/api/v1/generate/record-info",
            headers=headers,
            params={"taskId": task_id},
        )
        resp.raise_for_status()
        data = resp.json()

    if data.get("code") != 200:
        return {"status": "failed", "error": data.get("msg", "Poll error")}

    info = data.get("data", {})
    status = info.get("status", "")

    if status == "SUCCESS":
        suno_data = info.get("response", {}).get("sunoData", [])
        if suno_data:
            # Pick the shortest track (better for 20s video background)
            shortest = min(suno_data, key=lambda t: t.get("duration", 9999))
            audio_url = shortest.get("audioUrl", "")
            if audio_url:
                return {
                    "status": "ready",
                    "audio_url": audio_url,
                    "duration": shortest.get("duration", 0),
                }
        return {"status": "failed", "error": "No audio URL in response"}

    if status in ("CREATE_TASK_FAILED", "GENERATE_AUDIO_FAILED", "SENSITIVE_WORD_ERROR"):
        error_msg = info.get("errorMessage", status)
        return {"status": "failed", "error": error_msg}

    # Still processing (PENDING, TEXT_SUCCESS, FIRST_SUCCESS)
    return {"status": "pending"}


async def download_audio(audio_url: str, output_path: str) -> bool:
    """Download the generated audio file."""
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(audio_url)
        resp.raise_for_status()
        Path(output_path).write_bytes(resp.content)
    return True
