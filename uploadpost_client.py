"""
API client for Upload Post (https://api.upload-post.com).
Handles Instagram publishing: posts, stories, carousels, and reels.
"""

import requests
from config import UPLOADPOST_API_KEY

BASE_URL = "https://api.upload-post.com/api"
UPLOADPOSTS_URL = f"{BASE_URL}/uploadposts"

HEADERS = {
    "Authorization": f"Apikey {UPLOADPOST_API_KEY}",
}

# Available profiles
PROFILES = {
    "sanmunozia": "sanmunoz.ia",
    "Horizontes": "automatizaloia",
}


def get_profiles() -> list[dict]:
    """GET /api/uploadposts/users - Returns list of profiles with connected accounts.

    Returns a clean list like:
        [{"user": "sanmunozia", "instagram": "sanmunoz.ia", "avatar": "https://..."}, ...]
    """
    try:
        response = requests.get(f"{UPLOADPOSTS_URL}/users", headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        # API returns {"success": True, "profiles": [...]}
        raw_profiles = []
        if isinstance(data, dict) and "profiles" in data:
            raw_profiles = data["profiles"]
        elif isinstance(data, list):
            raw_profiles = data

        result = []
        for p in raw_profiles:
            username = p.get("username", "")
            ig = p.get("social_accounts", {}).get("instagram", {})
            ig_handle = ""
            ig_avatar = ""
            if isinstance(ig, dict):
                ig_handle = ig.get("handle", "") or ig.get("display_name", "")
                ig_avatar = ig.get("social_images", "")
            result.append({
                "user": username,
                "instagram": ig_handle,
                "avatar": ig_avatar,
            })

        print(f"[UploadPost] Profiles retrieved: {len(result)}")
        return result
    except requests.RequestException as e:
        print(f"[UploadPost] Error fetching profiles: {e}")
        return []


def publish_instagram_post(user: str, image_path: str, caption: str) -> dict:
    """
    POST /api/uploadposts/upload/photos
    Publishes a single image post to Instagram.
    """
    try:
        with open(image_path, "rb") as img_file:
            files = [
                ("photos[]", (image_path.split("/")[-1], img_file, "image/jpeg")),
                ("platform[]", (None, "instagram")),
            ]
            data = {
                "user": user,
                "title": caption,
                "media_type": "IMAGE",
            }
            response = requests.post(
                f"{BASE_URL}/upload_photos",
                headers=HEADERS,
                data=data,
                files=files,
            )
            response.raise_for_status()
            result = response.json()
            print(f"[UploadPost] Post published for {user}: {result}")
            return result
    except FileNotFoundError:
        print(f"[UploadPost] Image not found: {image_path}")
        return {"success": False, "error": f"Image not found: {image_path}"}
    except requests.RequestException as e:
        print(f"[UploadPost] Error publishing post: {e}")
        return {"success": False, "error": str(e)}


def publish_instagram_story(user: str, image_path: str, caption: str = "") -> dict:
    """
    POST /api/uploadposts/upload/photos
    Publishes a story to Instagram.
    """
    try:
        with open(image_path, "rb") as img_file:
            files = [
                ("photos[]", (image_path.split("/")[-1], img_file, "image/jpeg")),
                ("platform[]", (None, "instagram")),
            ]
            data = {
                "user": user,
                "title": caption,
                "media_type": "STORIES",
            }
            response = requests.post(
                f"{BASE_URL}/upload_photos",
                headers=HEADERS,
                data=data,
                files=files,
            )
            response.raise_for_status()
            result = response.json()
            print(f"[UploadPost] Story published for {user}: {result}")
            return result
    except FileNotFoundError:
        print(f"[UploadPost] Image not found: {image_path}")
        return {"success": False, "error": f"Image not found: {image_path}"}
    except requests.RequestException as e:
        print(f"[UploadPost] Error publishing story: {e}")
        return {"success": False, "error": str(e)}


def publish_instagram_carousel(user: str, image_paths: list[str], caption: str) -> dict:
    """
    POST /api/uploadposts/upload/photos
    Publishes a carousel (multiple images) to Instagram.
    Multiple photos[] entries automatically become a carousel.
    """
    opened_files = []
    try:
        files = [
            ("platform[]", (None, "instagram")),
        ]
        for path in image_paths:
            f = open(path, "rb")
            opened_files.append(f)
            files.append(("photos[]", (path.split("/")[-1], f, "image/jpeg")))

        data = {
            "user": user,
            "title": caption,
            "media_type": "IMAGE",
        }
        response = requests.post(
            f"{BASE_URL}/upload_photos",
            headers=HEADERS,
            data=data,
            files=files,
        )
        response.raise_for_status()
        result = response.json()
        print(f"[UploadPost] Carousel published for {user} ({len(image_paths)} images): {result}")
        return result
    except FileNotFoundError as e:
        print(f"[UploadPost] Image not found: {e}")
        return {"success": False, "error": f"Image not found: {e}"}
    except requests.RequestException as e:
        print(f"[UploadPost] Error publishing carousel: {e}")
        return {"success": False, "error": str(e)}
    finally:
        for f in opened_files:
            f.close()


def publish_instagram_reel(user: str, video_path: str, caption: str) -> dict:
    """
    POST /api/upload
    Publishes a reel (video) to Instagram via Upload Post API.

    All fields sent via multipart form-data (files list) to match
    the curl -F pattern from the API docs. Mixing data + files dicts
    in Python requests can cause 400 errors with array fields like platform[].
    """
    try:
        import os
        file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
        print(f"[UploadPost] Uploading reel: {video_path} ({file_size_mb:.1f} MB)")

        with open(video_path, "rb") as video_file:
            # Send ALL fields via files list for consistent multipart encoding
            # This matches the curl -F pattern from the API documentation
            files = [
                ("video", (video_path.split("/")[-1], video_file, "video/mp4")),
                ("user", (None, user)),
                ("platform[]", (None, "instagram")),
                ("title", (None, caption)),
                ("media_type", (None, "REELS")),
                ("share_to_feed", (None, "true")),
            ]
            # Longer timeout for large video files
            timeout = 300 if file_size_mb > 20 else 180
            response = requests.post(
                f"{BASE_URL}/upload",
                headers=HEADERS,
                files=files,
                timeout=timeout,
            )
            print(f"[UploadPost] Reel response status: {response.status_code}")
            print(f"[UploadPost] Reel response body: {response.text[:500]}")

            # Don't raise_for_status — parse response and return meaningful error
            result = response.json()
            if response.status_code >= 400:
                error_msg = result.get("message") or result.get("error") or f"HTTP {response.status_code}"
                print(f"[UploadPost] Reel upload error: {error_msg}")
                return {"success": False, "error": error_msg}

            print(f"[UploadPost] Reel upload initiated for {user}: {result}")
            return result
    except FileNotFoundError:
        print(f"[UploadPost] Video not found: {video_path}")
        return {"success": False, "error": f"Video no encontrado: {video_path}"}
    except requests.RequestException as e:
        print(f"[UploadPost] Error publishing reel: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"[UploadPost] Error response: {e.response.text[:500]}")
        return {"success": False, "error": str(e)}
