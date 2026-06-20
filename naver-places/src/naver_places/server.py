from fastmcp import FastMCP

from .client import (
    get_following_reviews,
    get_photo_viewer,
    get_review_photos,
    get_theme_lists,
    get_visitor_reviews,
    instant_search,
)
from .html import fetch_place_detail

mcp = FastMCP("naver-places")


@mcp.tool
async def search_places(
    query: str,
    coords: str,
    cookies: dict[str, str],
) -> list[dict]:
    """Search Naver Maps for places matching a query near given coordinates.

    Args:
        query: Search term in Korean or English (e.g. "파리바게트", "starbucks")
        coords: "lat,lng" decimal string (e.g. "37.5144,127.0667")
        cookies: Naver session cookies from a logged-in browser session
    """
    response = await instant_search(query, coords, cookies)
    return [item.model_dump() for item in response.place]


@mcp.tool
async def get_place_detail(
    place_id: str,
    cookies: dict[str, str],
) -> dict:
    """Fetch rich place details by parsing the pcmap place home page.

    Returns name, address, phone, coordinates, opening hours, review stats,
    and keyword analysis (votedKeyword breakdown).

    Args:
        place_id: Naver place ID (e.g. "1709318030")
        cookies: Naver session cookies from a logged-in browser session
    """
    detail = await fetch_place_detail(place_id, cookies)
    return detail.model_dump()


@mcp.tool
async def get_place_visitor_reviews(
    place_id: str,
    cookies: dict[str, str],
    size: int = 10,
    after: str | None = None,
) -> dict:
    """Fetch visitor reviews for a Naver place.

    Args:
        place_id: Naver place ID (e.g. "1709318030")
        cookies: Naver session cookies from a logged-in browser session
        size: Number of reviews to fetch (default 10)
        after: Pagination cursor (cursor field from a previous item) for next page
    """
    result = await get_visitor_reviews(place_id, cookies, size=size, after=after)
    return result.model_dump()


@mcp.tool
async def get_place_review_photos(
    place_id: str,
    cookies: dict[str, str],
) -> list[dict]:
    """Fetch the flat list of visitor review photos/videos for a Naver place.

    Args:
        place_id: Naver place ID (e.g. "1709318030")
        cookies: Naver session cookies from a logged-in browser session
    """
    photos = await get_review_photos(place_id, cookies)
    return [p.model_dump() for p in photos]


@mcp.tool
async def get_place_photo_gallery(
    place_id: str,
    cookies: dict[str, str],
    cursors: list[dict] | None = None,
) -> dict:
    """Fetch the photo gallery viewer for a Naver place with cursor pagination.

    Returns photos with full metadata (dimensions, music, clip, moment info)
    and cursors for fetching the next page.

    Args:
        place_id: Naver place ID (e.g. "1709318030")
        cookies: Naver session cookies from a logged-in browser session
        cursors: Cursor list from a previous response to fetch the next page
    """
    result = await get_photo_viewer(place_id, cookies, cursors=cursors)
    return result.model_dump()


@mcp.tool
async def get_place_following_reviews(
    place_id: str,
    cookies: dict[str, str],
) -> dict:
    """Fetch reviews from users the logged-in user follows, for a Naver place.

    Args:
        place_id: Naver place ID (e.g. "1709318030")
        cookies: Naver session cookies from a logged-in browser session
    """
    result = await get_following_reviews(place_id, cookies)
    return result.model_dump()


@mcp.tool
async def get_place_theme_lists(
    place_id: str,
    cookies: dict[str, str],
    display: int = 3,
) -> dict:
    """Fetch curator theme lists that include a Naver place.

    Args:
        place_id: Naver place ID (e.g. "1709318030")
        cookies: Naver session cookies from a logged-in browser session
        display: Number of theme lists to return (default 3)
    """
    result = await get_theme_lists(place_id, cookies, display=display)
    return result.model_dump()


if __name__ == "__main__":
    mcp.run()
