from fastmcp import FastMCP
from fastmcp.utilities.types import Image

from .client import (
    get_following_reviews,
    get_photo_viewer,
    get_review_photos,
    get_theme_lists,
    get_visitor_reviews,
    search_places as _search_places,
)
from .cookies import list_chrome_profiles
from .html import fetch_place_detail
from .images import fetch_images_from_urls, fetch_place_images
from .session import check_naver_login, get_session_cookies
from . import views

mcp = FastMCP("naver-places")


@mcp.tool
def list_available_chrome_profiles() -> list[str]:
    """List Chrome profile names that have a Naver cookie database.

    Returns names such as "Default", "Profile 4". Set the NAVER_CHROME_PROFILE
    environment variable to one of these to choose which logged-in Naver
    session the server uses. Authentication is otherwise automatic.
    """
    return list_chrome_profiles()


@mcp.tool
def check_naver_auth() -> dict:
    """Check whether Naver tools will work, and in what mode.

    Reports:
    - mode: "logged_in" (Chrome session found), "anonymous" (no login but the
      anonymous fallback is enabled), or "none".
    - publicToolsWork: if true, search_places / get_place_detail /
      get_place_visitor_reviews / photos all work — even in anonymous mode.
      Do NOT abandon those tools just because isLoggedIn is false.
    - isLoggedIn: only personalized tools (get_place_following_reviews) need this.
    - cookieCount, hasNaverSession, message.

    Most public tasks need no login. Call this first only if a tool returns
    empty results or an auth error.
    """
    return check_naver_login()


@mcp.tool
async def search_places(
    query: str,
    coords: str | None = None,
    near: str | None = None,
) -> list[dict]:
    """Search Naver Maps for places by keyword.

    This is an AUTOCOMPLETE-style search, not full-text. Use a SHORT keyword:
    a dish or business name like "순두부찌개" or "스타벅스". Do NOT put a
    location in `query` (e.g. "성균관대 순두부찌개" returns nothing) — pass the
    location via `near` or `coords` instead.

    Location handling (controls distance ranking AND `distanceKm` in results):
    - `near`: a landmark/area name (e.g. "성균관대"). It is geocoded to
      coordinates automatically, so this is the easiest way to search "around X".
    - `coords`: an explicit "lat,lng" string (e.g. "37.5872,126.9930"). Takes
      precedence over `near`.
    - If you pass neither, a default Seoul-center point is used and `distanceKm`
      will be relative to that, so it is meaningless for local queries.

    Result fields: `rankingScore` is Naver's internal relevance weight (NOT a
    0–5 rating — get the real rating from get_place_detail). Results are ranked,
    not strictly filtered, so categories may be mixed.

    Args:
        query: Short keyword in Korean or English (e.g. "순두부찌개", "starbucks")
        coords: Optional explicit "lat,lng" center for ranking/distance
        near: Optional landmark/area name to search around (auto-geocoded)
    """
    items, _ = await _search_places(
        query, get_session_cookies(), coords=coords, near=near
    )
    return views.search_results(items)


@mcp.tool
async def get_place_detail(place_id: str) -> dict:
    """Fetch rich place details: name, address, phone, score, review totals,
    and top review keywords.

    Args:
        place_id: Naver place ID (e.g. "1709318030")
    """
    detail = await fetch_place_detail(place_id, get_session_cookies())
    return views.place_detail(detail)


@mcp.tool
async def get_place_visitor_reviews(
    place_id: str,
    size: int = 10,
    after: str | None = None,
) -> dict:
    """Fetch visitor reviews for a Naver place.

    Args:
        place_id: Naver place ID (e.g. "1709318030")
        size: Number of reviews to fetch (default 10)
        after: Pagination cursor (the nextCursor from a previous call) for the next page
    """
    result = await get_visitor_reviews(place_id, get_session_cookies(), size=size, after=after)
    return views.visitor_reviews(result)


@mcp.tool
async def get_place_images(
    place_id: str | None = None,
    urls: list[str] | None = None,
    limit: int = 5,
) -> list[Image]:
    """Fetch review photos as viewable image content (the model can SEE them).

    These image bytes are token-expensive. To minimize tokens, FIRST call
    get_place_review_photos to get photo URLs + captions cheaply, then pass only
    the URLs you actually want to view here as `urls`.

    Provide either `urls` (view those specific photos; only Naver CDN URLs are
    accepted) or `place_id` (view the first `limit` review photos). If both are
    given, `urls` wins. Videos are skipped.

    Args:
        place_id: Naver place ID (e.g. "1709318030"); used when `urls` is omitted
        urls: Specific Naver review-photo URLs to fetch and view
        limit: Maximum number of images to fetch (default 5)
    """
    if urls:
        items = await fetch_images_from_urls(urls, limit=limit)
    elif place_id:
        items = await fetch_place_images(place_id, get_session_cookies(), limit=limit)
    else:
        return []
    return [Image(data=item["data"], format=item["format"]) for item in items]


@mcp.tool
async def get_place_review_photos(place_id: str) -> list[dict]:
    """Fetch metadata (URLs, captions, media type) of review photos/videos for a
    Naver place. This is the CHEAP path: it returns URLs and captions only, no
    image bytes. To actually view chosen photos, pass their URLs to
    get_place_images(urls=...).

    Args:
        place_id: Naver place ID (e.g. "1709318030")
    """
    photos = await get_review_photos(place_id, get_session_cookies())
    return views.review_photos(photos)


@mcp.tool
async def get_place_photo_gallery(
    place_id: str,
    cursors: list[dict] | None = None,
) -> dict:
    """Fetch the paginated photo gallery (metadata) for a Naver place.

    Args:
        place_id: Naver place ID (e.g. "1709318030")
        cursors: Cursor list from a previous response's "cursors" field for the next page
    """
    result = await get_photo_viewer(place_id, get_session_cookies(), cursors=cursors)
    return views.photo_gallery(result)


@mcp.tool
async def get_place_following_reviews(place_id: str) -> dict:
    """Fetch reviews from accounts the logged-in user follows, for a Naver place.

    Args:
        place_id: Naver place ID (e.g. "1709318030")
    """
    result = await get_following_reviews(place_id, get_session_cookies())
    return views.following_reviews(result)


@mcp.tool
async def get_place_theme_lists(place_id: str, display: int = 3) -> dict:
    """Fetch curator theme lists that include a Naver place.

    Args:
        place_id: Naver place ID (e.g. "1709318030")
        display: Number of theme lists to return (default 3)
    """
    result = await get_theme_lists(place_id, get_session_cookies(), display=display)
    return views.theme_lists(result)


if __name__ == "__main__":
    mcp.run()
