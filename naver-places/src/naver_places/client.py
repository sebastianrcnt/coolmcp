import asyncio

import httpx

from . import cache
from .graphql.client import NaverPlaceGraphQLClient
from .graphql import queries
from .errors import NaverAPIError
from .types import (
    InstantSearchResponse,
    FollowingReviewsResult,
    PhotoViewerResult,
    ReviewPhoto,
    ThemeListsResult,
    VisitorReviewsResult,
)
from .types.place import PlaceDetail
from .types.search import PlaceItem

INSTANT_SEARCH_URL = "https://map.naver.com/p/api/search/instant-search"

# Default map center (Seoul City Hall) used when no coords/near are given.
# Naver instant-search requires coords; they only affect distance ranking.
DEFAULT_COORDS = "37.5666,126.9784"

# Initial cursor for the photo viewer: start of the visitor-review photo section.
_INITIAL_PHOTO_CURSORS = [
    {"id": "placeReview", "startIndex": 0, "hasNext": True, "lastCursor": None}
]

_SEARCH_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "ko-KR,ko;q=0.8,en-US;q=0.6,en;q=0.4",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://map.naver.com/p?c=15.00,0,0,0,dh",
    "sec-ch-ua": '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
    "sec-ch-ua-arch": '"arm"',
    "sec-ch-ua-bitness": '"64"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": '""',
    "sec-ch-ua-platform": '"macOS"',
    "sec-ch-ua-platform-version": '"26.5.1"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/149.0.0.0 Safari/537.36"
    ),
}


async def instant_search(
    query: str,
    coords: str,
    cookies: dict[str, str],
) -> InstantSearchResponse:
    async def _fetch() -> InstantSearchResponse:
        async with httpx.AsyncClient(headers=_SEARCH_HEADERS, cookies=cookies) as client:
            try:
                response = await client.get(
                    INSTANT_SEARCH_URL,
                    params={"query": query, "coords": coords},
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise NaverAPIError(
                    f"Naver search failed (HTTP {exc.response.status_code})"
                ) from exc
            except httpx.RequestError as exc:
                raise NaverAPIError(f"Naver search failed: {exc}") from exc
            return InstantSearchResponse.model_validate(response.json())

    return await cache.get_or_set(("search", query, coords), _fetch)


async def resolve_coords(
    near: str, cookies: dict[str, str]
) -> tuple[str, str] | None:
    """Geocode a landmark/place name via instant-search.

    Returns (coords, resolvedName) of the top matching place — resolvedName lets
    a caller verify the geocode hit the intended landmark (not a same-named
    place elsewhere) — or None if nothing matched.
    """
    response = await instant_search(near, DEFAULT_COORDS, cookies)
    places = response.merged_places()
    if not places:
        return None
    top = places[0]
    return f"{top.y},{top.x}", top.title


async def search_places(
    query: str,
    cookies: dict[str, str],
    coords: str | None = None,
    near: str | None = None,
) -> tuple[list, dict]:
    """Search places, resolving `near` to coordinates when given.

    Resolution order for the ranking center: explicit `coords` > geocoded
    `near` > DEFAULT_COORDS.

    Returns (merged place items, searchedNear) where searchedNear describes how
    the ranking center was chosen so callers can verify/expose it:
        {"coords": <used>, "near": <input or None>,
         "resolvedTo": <place name geocoded from near, or None>,
         "source": "coords" | "near" | "default"}
    """
    used_coords = coords
    resolved_to = None
    if coords is not None:
        source = "coords"
    elif near:
        geo = await resolve_coords(near, cookies)
        if geo is not None:
            used_coords, resolved_to = geo
            source = "near"
        else:
            used_coords, source = DEFAULT_COORDS, "default"
    else:
        used_coords, source = DEFAULT_COORDS, "default"

    response = await instant_search(query, used_coords, cookies)
    searched_near = {
        "coords": used_coords,
        "near": near,
        "resolvedTo": resolved_to,
        "source": source,
    }
    return response.merged_places(), searched_near


async def enrich_places(
    items: list[PlaceItem],
    cookies: dict[str, str],
    top: int,
) -> list[tuple[PlaceItem, PlaceDetail | None]]:
    """Fetch place details for the first `top` items concurrently.

    Collapses the search→detail round trips: instead of the agent calling
    get_place_detail once per candidate, the server fans out in parallel here.
    A failed detail fetch yields (item, None) rather than aborting the batch.
    """
    # Imported lazily to avoid a module-load cycle (html imports nothing from
    # client, but keep the dependency direction explicit at call time).
    from .html import fetch_place_detail

    targets = items[: max(0, top)]

    async def _one(item: PlaceItem) -> tuple[PlaceItem, PlaceDetail | None]:
        try:
            detail = await fetch_place_detail(item.id, cookies)
            return item, detail
        except Exception:
            return item, None

    return await asyncio.gather(*(_one(it) for it in targets))


async def get_visitor_reviews(
    place_id: str,
    cookies: dict[str, str],
    size: int = 10,
    after: str | None = None,
) -> VisitorReviewsResult:
    variables: dict = {
        "input": {
            "businessId": place_id,
            "businessType": "place",
            "item": "0",
            "bookingBusinessId": None,
            "size": size,
            "isPhotoUsed": False,
            "includeContent": True,
            "getUserStats": True,
            "includeReceiptPhotos": True,
            "getReactions": True,
            "getTrailer": True,
        }
    }
    if after:
        variables["input"]["after"] = after

    gql_client = NaverPlaceGraphQLClient(place_id, cookies)
    data = await gql_client.execute(queries.VISITOR_REVIEWS, variables)
    return VisitorReviewsResult.model_validate(data["visitorReviews"])


async def get_review_photos(
    place_id: str,
    cookies: dict[str, str],
) -> list[ReviewPhoto]:
    variables = {
        "input": {
            "businessId": place_id,
            "businessType": "place",
            "type": "FLAT",
        }
    }
    gql_client = NaverPlaceGraphQLClient(place_id, cookies)
    data = await gql_client.execute(queries.VISITOR_REVIEW_PHOTOS, variables)
    return [ReviewPhoto.model_validate(p) for p in data["visitorReviewPhotos"]]


async def get_photo_viewer(
    place_id: str,
    cookies: dict[str, str],
    cursors: list[dict] | None = None,
    exclude_author_ids: list[str] | None = None,
    date_range: str = "",
) -> PhotoViewerResult:
    """Fetch photo gallery with cursor-based pagination.

    Args:
        place_id: Naver place ID
        cookies: Naver session cookies
        cursors: List of cursor dicts from a previous response to paginate.
                 Each dict: {"id": str, "startIndex": int, "hasNext": bool, "lastCursor": str|None}
                 When omitted, starts from the beginning of the visitor-review photo section.
        exclude_author_ids: Author IDs to exclude
        date_range: Date filter string
    """
    variables = {
        "input": {
            "businessId": place_id,
            "businessType": "place",
            "cursors": cursors if cursors is not None else _INITIAL_PHOTO_CURSORS,
            "excludeAuthorIds": exclude_author_ids or [],
            "excludeSection": [],
            "excludeClipIds": [],
            "dateRange": date_range,
        },
    }
    gql_client = NaverPlaceGraphQLClient(place_id, cookies)
    data = await gql_client.execute(queries.PHOTO_VIEWER, variables)
    return PhotoViewerResult.model_validate(data["photoViewer"])


async def get_following_reviews(
    place_id: str,
    cookies: dict[str, str],
) -> FollowingReviewsResult:
    variables = {"input": {"businessId": place_id}}
    gql_client = NaverPlaceGraphQLClient(place_id, cookies)
    data = await gql_client.execute(queries.FOLLOWING_REVIEWS, variables)
    return FollowingReviewsResult.model_validate(data["followingReviews"])


async def get_theme_lists(
    place_id: str,
    cookies: dict[str, str],
    display: int = 3,
) -> ThemeListsResult:
    variables = {"input": {"businessId": place_id, "display": display}}
    gql_client = NaverPlaceGraphQLClient(place_id, cookies)
    data = await gql_client.execute(queries.VISITOR_REVIEW_THEME_LISTS, variables)
    return ThemeListsResult.model_validate(data["themeLists"])
