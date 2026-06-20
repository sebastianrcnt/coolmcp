import httpx

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

INSTANT_SEARCH_URL = "https://map.naver.com/p/api/search/instant-search"

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
