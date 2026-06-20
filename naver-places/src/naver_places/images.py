"""Image fetching for review photos.

Downloads the bytes of review photos so MCP tools can return them as
viewable image content. Video entries (mediaType == "video") are skipped
because their URLs are stream/trailer URLs, not still images.
"""

import httpx

from .client import get_review_photos

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
    """Fetch up to `limit` still-image review photos as raw bytes.

    Skips videos. Returns a list of dicts:
        {"data": bytes, "format": str, "text": str | None, "url": str}
    Photos that fail to download are skipped.
    """
    photos = await get_review_photos(place_id, cookies)
    images = [p for p in photos if p.mediaType != "video"]

    results: list[dict] = []
    for photo in images[:limit]:
        try:
            data, fmt = await fetch_image_bytes(photo.originalUrl)
        except Exception:
            continue
        results.append(
            {"data": data, "format": fmt, "text": photo.text, "url": photo.originalUrl}
        )
    return results
