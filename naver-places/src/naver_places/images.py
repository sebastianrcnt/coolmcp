"""Image fetching for review photos.

Downloads review photo bytes so MCP tools can return them as viewable image
content. Images are downscaled (long edge <= 1024px, re-encoded as JPEG) to keep
the payload and vision-token cost small. Video entries are skipped.
"""

import io
from urllib.parse import urlparse

import httpx
from PIL import Image as PILImage

from .client import get_review_photos

_MAX_DIMENSION = 1024
_JPEG_QUALITY = 80

# SSRF guard: only fetch images from Naver's CDN/domains.
_ALLOWED_IMAGE_HOST_SUFFIXES = (".pstatic.net", ".naver.net", ".naver.com")


def _is_allowed_image_url(url: str) -> bool:
    """True only if url's host is a Naver CDN/domain (SSRF guard)."""
    try:
        host = (urlparse(url).hostname or "").lower()
    except Exception:
        return False
    if not host:
        return False
    return any(
        host == suffix.lstrip(".") or host.endswith(suffix)
        for suffix in _ALLOWED_IMAGE_HOST_SUFFIXES
    )


_IMAGE_HEADERS = {
    "accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "referer": "https://pcmap.place.naver.com/",
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/149.0.0.0 Safari/537.36"
    ),
}

_CONTENT_TYPE_TO_FORMAT = {
    "image/jpeg": "jpeg",
    "image/jpg": "jpeg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}


def _format_from_content_type(content_type: str | None) -> str:
    if not content_type:
        return "jpeg"
    ct = content_type.split(";")[0].strip().lower()
    return _CONTENT_TYPE_TO_FORMAT.get(ct, "jpeg")


def _downscale(data: bytes) -> tuple[bytes, str]:
    """Downscale to <= _MAX_DIMENSION on the long edge, re-encode as JPEG.

    Returns (jpeg_bytes, "jpeg"). On any failure returns the original bytes
    with format "jpeg" (best effort).
    """
    try:
        img = PILImage.open(io.BytesIO(data))
        img.load()
        # Already a small JPEG within bounds: keep as-is to avoid re-encoding
        # (which can enlarge an already well-compressed image and lose quality).
        if img.format == "JPEG" and max(img.size) <= _MAX_DIMENSION:
            return data, "jpeg"
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        img.thumbnail((_MAX_DIMENSION, _MAX_DIMENSION))
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=_JPEG_QUALITY)
        return out.getvalue(), "jpeg"
    except Exception:
        return data, "jpeg"


async def fetch_image_bytes(url: str) -> tuple[bytes, str]:
    """Download a single image. Returns (raw_bytes, format) e.g. (b'...', 'jpeg')."""
    async with httpx.AsyncClient(headers=_IMAGE_HEADERS) as client:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()
        fmt = _format_from_content_type(response.headers.get("content-type"))
        return response.content, fmt


async def fetch_place_images(
    place_id: str,
    cookies: dict[str, str],
    limit: int = 5,
) -> list[dict]:
    """Fetch up to `limit` still-image review photos, downscaled.

    Skips videos and entries without a URL. Returns a list of dicts:
        {"data": bytes, "format": "jpeg", "text": str | None, "url": str}
    Photos that fail to download or decode are skipped.
    """
    photos = await get_review_photos(place_id, cookies)
    images = [
        p
        for p in photos
        if p.mediaType != "video"
        and p.originalUrl
        and _is_allowed_image_url(p.originalUrl)
    ]

    results: list[dict] = []
    for photo in images[:limit]:
        try:
            raw, _ = await fetch_image_bytes(photo.originalUrl)
            data, fmt = _downscale(raw)
        except Exception:
            continue
        results.append(
            {"data": data, "format": fmt, "text": photo.text, "url": photo.originalUrl}
        )
    return results


async def fetch_images_from_urls(urls: list[str], limit: int = 5) -> list[dict]:
    """Fetch specific image URLs (downscaled). Non-Naver-CDN URLs are rejected
    (SSRF guard). Returns dicts: {"data": bytes, "format": "jpeg", "text": None, "url": str}.
    URLs that fail or are rejected are skipped.
    """
    results: list[dict] = []
    for url in urls[:limit]:
        if not _is_allowed_image_url(url):
            continue
        try:
            raw, _ = await fetch_image_bytes(url)
            data, fmt = _downscale(raw)
        except Exception:
            continue
        results.append({"data": data, "format": fmt, "text": None, "url": url})
    return results
