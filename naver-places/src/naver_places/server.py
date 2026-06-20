from fastmcp import FastMCP

from .client import (
    get_following_reviews,
    get_photo_viewer,
    get_review_photos,
    get_theme_lists,
    get_visitor_reviews,
    instant_search,
)
from .cookies import get_naver_cookies, list_chrome_profiles
from .html import fetch_place_detail

mcp = FastMCP("naver-places")


def _cookies(cookies: dict[str, str] | None, chrome_profile: str) -> dict[str, str]:
    return cookies if cookies is not None else get_naver_cookies(chrome_profile)


@mcp.tool
def list_available_chrome_profiles() -> list[str]:
    """List Chrome profile names that have a Naver cookie database.

    Returns profile names such as "Default", "Profile 4", etc.
    Pass one of these as chrome_profile to other tools.
    """
    return list_chrome_profiles()


@mcp.tool
async def search_places(
    query: str,
    coords: str,
    cookies: dict[str, str] | None = None,
    chrome_profile: str = "Default",
) -> list[dict]:
    """Search Naver Maps for places matching a query near given coordinates.

    Args:
        query: Search term in Korean or English (e.g. "파리바게트", "starbucks")
        coords: "lat,lng" decimal string (e.g. "37.5144,127.0667")
        cookies: Naver session cookies. If omitted, read automatically from Chrome.
        chrome_profile: Chrome profile to read cookies from (e.g. "Default", "Profile 4").
    """
    response = await instant_search(query, coords, _cookies(cookies, chrome_profile))
    return [item.model_dump() for item in response.place]


@mcp.tool
async def get_place_detail(
    place_id: str,
    cookies: dict[str, str] | None = None,
    chrome_profile: str = "Default",
) -> dict:
    """Fetch rich place details by parsing the pcmap place home page.

    Returns name, address, phone, coordinates, opening hours, review stats,
    and keyword analysis (votedKeyword breakdown).

    Args:
        place_id: Naver place ID (e.g. "1709318030")
        cookies: Naver session cookies. If omitted, read automatically from Chrome.
        chrome_profile: Chrome profile to read cookies from (e.g. "Default", "Profile 4").
    """
    detail = await fetch_place_detail(place_id, _cookies(cookies, chrome_profile))
    return detail.model_dump()


@mcp.tool
async def get_place_visitor_reviews(
    place_id: str,
    cookies: dict[str, str] | None = None,
    chrome_profile: str = "Default",
    size: int = 10,
    after: str | None = None,
) -> dict:
    """Fetch visitor reviews for a Naver place.

    Args:
        place_id: Naver place ID (e.g. "1709318030")
        cookies: Naver session cookies. If omitted, read automatically from Chrome.
        chrome_profile: Chrome profile to read cookies from (e.g. "Default", "Profile 4").
        size: Number of reviews to fetch (default 10)
        after: Pagination cursor (cursor field from a previous item) for next page
    """
    result = await get_visitor_reviews(place_id, _cookies(cookies, chrome_profile), size=size, after=after)
    return result.model_dump()


@mcp.tool
async def get_place_review_photos(
    place_id: str,
    cookies: dict[str, str] | None = None,
    chrome_profile: str = "Default",
) -> list[dict]:
    """Fetch the flat list of visitor review photos/videos for a Naver place.

    Args:
        place_id: Naver place ID (e.g. "1709318030")
        cookies: Naver session cookies. If omitted, read automatically from Chrome.
        chrome_profile: Chrome profile to read cookies from (e.g. "Default", "Profile 4").
    """
    photos = await get_review_photos(place_id, _cookies(cookies, chrome_profile))
    return [p.model_dump() for p in photos]


@mcp.tool
async def get_place_photo_gallery(
    place_id: str,
    cookies: dict[str, str] | None = None,
    chrome_profile: str = "Default",
    cursors: list[dict] | None = None,
) -> dict:
    """Fetch the photo gallery viewer for a Naver place with cursor pagination.

    Returns photos with full metadata (dimensions, music, clip, moment info)
    and cursors for fetching the next page.

    Args:
        place_id: Naver place ID (e.g. "1709318030")
        cookies: Naver session cookies. If omitted, read automatically from Chrome.
        chrome_profile: Chrome profile to read cookies from (e.g. "Default", "Profile 4").
        cursors: Cursor list from a previous response to fetch the next page
    """
    result = await get_photo_viewer(place_id, _cookies(cookies, chrome_profile), cursors=cursors)
    return result.model_dump()


@mcp.tool
async def get_place_following_reviews(
    place_id: str,
    cookies: dict[str, str] | None = None,
    chrome_profile: str = "Default",
) -> dict:
    """Fetch reviews from users the logged-in user follows, for a Naver place.

    Args:
        place_id: Naver place ID (e.g. "1709318030")
        cookies: Naver session cookies. If omitted, read automatically from Chrome.
        chrome_profile: Chrome profile to read cookies from (e.g. "Default", "Profile 4").
    """
    result = await get_following_reviews(place_id, _cookies(cookies, chrome_profile))
    return result.model_dump()


@mcp.tool
async def get_place_theme_lists(
    place_id: str,
    cookies: dict[str, str] | None = None,
    chrome_profile: str = "Default",
    display: int = 3,
) -> dict:
    """Fetch curator theme lists that include a Naver place.

    Args:
        place_id: Naver place ID (e.g. "1709318030")
        cookies: Naver session cookies. If omitted, read automatically from Chrome.
        chrome_profile: Chrome profile to read cookies from (e.g. "Default", "Profile 4").
        display: Number of theme lists to return (default 3)
    """
    result = await get_theme_lists(place_id, _cookies(cookies, chrome_profile), display=display)
    return result.model_dump()


if __name__ == "__main__":
    mcp.run()
