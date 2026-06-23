import json
import re

import httpx

from . import cache
from .errors import NaverAPIError
from .types.place import PlaceDetail, PlaceReviewSummary

PCMAP_PLACE_URL = "https://pcmap.place.naver.com/place/{place_id}/home"

_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "ko,en-US;q=0.9,en;q=0.8",
    "sec-ch-ua": '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "iframe",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-site",
    "upgrade-insecure-requests": "1",
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/149.0.0.0 Safari/537.36"
    ),
}

_APOLLO_STATE_RE = re.compile(
    r"window\.__APOLLO_STATE__\s*=\s*(\{.*?\});\s*\n",
    re.DOTALL,
)


def _extract_apollo_state(html: str) -> dict:
    m = _APOLLO_STATE_RE.search(html)
    if not m:
        raise NaverAPIError(
            "Could not parse place page (Naver layout changed or access was blocked)."
        )
    return json.loads(m.group(1))


def _parse_place_detail(place_id: str, state: dict) -> PlaceDetail:
    base_key = f"PlaceDetailBase:{place_id}"
    base = state.get(base_key, {})

    stats_key = f"VisitorReviewStatsResult:{place_id}"
    stats_raw = state.get(stats_key)
    review_summary = None
    if stats_raw:
        review_summary = PlaceReviewSummary.model_validate(stats_raw)

    coord_raw = base.get("coordinate")
    coordinate = None
    if coord_raw and isinstance(coord_raw, dict):
        from .types.place import Coordinate
        coordinate = Coordinate.model_validate(coord_raw)

    category = base.get("category")
    if isinstance(category, str):
        category = [c.strip() for c in category.split(",")]
    elif not isinstance(category, list):
        category = []

    return PlaceDetail(
        id=place_id,
        name=base.get("name", ""),
        category=category,
        categoryCode=base.get("categoryCode", ""),
        roadAddress=base.get("roadAddress", ""),
        address=base.get("address", ""),
        phone=base.get("phone", ""),
        virtualPhone=base.get("virtualPhone", ""),
        coordinate=coordinate,
        openingHours=base.get("openingHours"),
        visitorReviewsTotal=base.get("visitorReviewsTotal", 0),
        visitorReviewsScore=base.get("visitorReviewsScore", 0.0),
        cafeBlogReviewsTotal=base.get("cafeBlogReviewsTotal", 0),
        reviewSummary=review_summary,
        naverBlog=base.get("naverBlog"),
        talktalkUrl=base.get("talktalkUrl"),
        isGoodStore=base.get("isGoodStore", False),
    )


async def fetch_place_detail(
    place_id: str,
    cookies: dict[str, str],
    params: dict[str, str] | None = None,
) -> PlaceDetail:
    """Fetch pcmap place home page and parse embedded Apollo state.

    Args:
        place_id: Naver place ID
        cookies: Naver session cookies
        params: Optional query params (e.g. locale, svcName)
    """
    url = PCMAP_PLACE_URL.format(place_id=place_id)
    default_params = {"locale": "ko", "svcName": "map_pcv5"}
    if params:
        default_params.update(params)

    async def _fetch() -> PlaceDetail:
        async with httpx.AsyncClient(
            headers=_HEADERS, cookies=cookies, follow_redirects=True
        ) as client:
            try:
                response = await client.get(url, params=default_params)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise NaverAPIError(
                    f"Naver place page failed (HTTP {exc.response.status_code})"
                ) from exc
            except httpx.RequestError as exc:
                raise NaverAPIError(f"Naver place page failed: {exc}") from exc

        state = _extract_apollo_state(response.text)
        return _parse_place_detail(place_id, state)

    key = ("detail", place_id, tuple(sorted(default_params.items())))
    return await cache.get_or_set(key, _fetch)
