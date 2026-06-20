from fastmcp import FastMCP

from .client import (
    get_following_reviews,
    get_review_photos,
    get_theme_lists,
    get_visitor_reviews,
    instant_search,
)

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

    Returns:
        List of matching places with id, title, address, coordinates, category,
        review count, and distance.
    """
    response = await instant_search(query, coords, cookies)
    return [item.model_dump() for item in response.place]


@mcp.tool
async def get_place_visitor_reviews(
    place_id: str,
    cookies: dict[str, str],
    size: int = 10,
    cursor: str | None = None,
) -> dict:
    """Fetch visitor reviews for a Naver place.

    Args:
        place_id: Naver place ID (e.g. "1709318030")
        cookies: Naver session cookies from a logged-in browser session
        size: Number of reviews to fetch (default 10)
        cursor: Pagination cursor from a previous response to fetch the next page

    Returns:
        Dict with "total" count and "items" list. Each item includes rating,
        author info, visitCount, visited date, votedKeywords, reply, and reactionStat.
    """
    result = await get_visitor_reviews(place_id, cookies, size=size, cursor=cursor)
    return result.model_dump()


@mcp.tool
async def get_place_review_photos(
    place_id: str,
    cookies: dict[str, str],
) -> list[dict]:
    """Fetch visitor review photos for a Naver place.

    Args:
        place_id: Naver place ID (e.g. "1709318030")
        cookies: Naver session cookies from a logged-in browser session

    Returns:
        List of photos/videos with originalUrl, mediaType, review text, date,
        author, votedKeywords, and video stream URLs when mediaType is "video".
    """
    photos = await get_review_photos(place_id, cookies)
    return [p.model_dump() for p in photos]


@mcp.tool
async def get_place_following_reviews(
    place_id: str,
    cookies: dict[str, str],
) -> dict:
    """Fetch reviews from users the logged-in user follows, for a Naver place.

    Args:
        place_id: Naver place ID (e.g. "1709318030")
        cookies: Naver session cookies from a logged-in browser session

    Returns:
        Dict with "reviews" list and "reactionTypes". Reviews are empty when the
        logged-in user has no followings who visited this place.
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

    Returns:
        Dict with "total" count and "themeLists". Each theme list has title,
        viewCount, itemCount, sample reviews, and author info.
    """
    result = await get_theme_lists(place_id, cookies, display=display)
    return result.model_dump()


if __name__ == "__main__":
    mcp.run()
