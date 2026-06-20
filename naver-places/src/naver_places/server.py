from fastmcp import FastMCP
from fastmcp.utilities.types import Image

from .client import (
    get_following_reviews,
    get_photo_viewer,
    get_review_photos,
    get_theme_lists,
    get_visitor_reviews,
    instant_search,
)
from .cookies import list_chrome_profiles
from .html import fetch_place_detail
from .images import fetch_images_from_urls, fetch_place_images
from .session import check_naver_login, get_session_cookies
from . import views

mcp = FastMCP("naver-places")

# Default map center (Seoul City Hall) used when no coords are given.
# Naver instant-search requires coords; they only affect distance ranking.
DEFAULT_COORDS = "37.5666,126.9784"


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
    """Check whether the configured Chrome profile has a usable Naver session.

    Reports cookieCount, hasNaverSession (public search/reviews work),
    isLoggedIn (personalized features like following reviews work), and a
    human-readable message. Call this first if other tools return empty results
    or fail with an authentication error.
    """
    return check_naver_login()


@mcp.tool
async def search_places(query: str, coords: str | None = None) -> list[dict]:
    """Search Naver Maps for places matching a keyword.

    Args:
        query: Search term in Korean or English (e.g. "파리바게트", "starbucks")
        coords: Optional "lat,lng" string (e.g. "37.5144,127.0667"). Only affects
                distance ranking; if omitted a default Seoul-center coordinate is used.
    """
    response = await instant_search(query, coords or DEFAULT_COORDS, get_session_cookies())
    return views.search_results(response.place)


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
