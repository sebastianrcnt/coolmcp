"""Offline regression tests for type parsing and lean view projections.

Synthetic fixtures reproduce edge cases seen in real Naver responses:
- ReviewPhoto with null mediaType / logId
- ReviewMedia.thumbnailRatio as a string ("portrait")
- PhotoViewerImage with null author / mediaType
- place-detail Apollo-state parsing
No network access.
"""

from naver_places import views
from naver_places.types.photos import ReviewPhoto, PhotoViewerResult
from naver_places.types.reviews import VisitorReviewsResult
from naver_places.types.search import PlaceItem, InstantSearchResponse
from naver_places.html import _parse_place_detail
from naver_places.graphql.client import _operation_name
from naver_places.graphql import queries
from graphql import print_ast


def test_review_photo_allows_null_mediatype_and_logid():
    photo = ReviewPhoto.model_validate(
        {
            "originalUrl": "https://img/x.jpg",
            "mediaType": None,
            "logId": None,
            "votedKeywords": [{"code": "k", "name": "좋아요"}],
            "author": {"nickname": "n", "from": "NAVER"},
            "text": "hello",
        }
    )
    out = views.review_photos([photo])
    assert out[0]["url"] == "https://img/x.jpg"
    assert out[0]["isVideo"] is False
    assert out[0]["author"] == "n"
    assert out[0]["keywords"] == ["좋아요"]


def test_visitor_review_media_thumbnailratio_string():
    result = VisitorReviewsResult.model_validate(
        {
            "total": 1,
            "items": [
                {
                    "id": "1",
                    "cursor": "CUR",
                    "author": {"nickname": "a", "from": "NAVER"},
                    "media": [{"type": "image", "thumbnailRatio": "portrait"}],
                    "votedKeywords": [{"code": "k", "name": "좋아요"}],
                    "visited": "2.25.수",
                    "body": "good",
                }
            ],
        }
    )
    view = views.visitor_reviews(result)
    assert view["total"] == 1
    assert view["nextCursor"] == "CUR"
    assert view["reviews"][0]["author"] == "a"
    assert view["reviews"][0]["keywords"] == ["좋아요"]
    assert view["reviews"][0]["photoCount"] == 1


def test_photo_viewer_allows_null_author_and_mediatype():
    result = PhotoViewerResult.model_validate(
        {
            "cursors": [
                {"id": "placeReview", "startIndex": 0, "hasNext": True, "lastCursor": None}
            ],
            "photos": [
                {"viewId": "v", "originalUrl": "u", "mediaType": None, "author": None}
            ],
        }
    )
    view = views.photo_gallery(result)
    assert view["cursors"][0]["id"] == "placeReview"
    assert view["photos"][0]["url"] == "u"
    assert view["photos"][0]["isVideo"] is False
    assert view["photos"][0]["author"] is None


def test_search_results_projection():
    item = PlaceItem.model_validate(
        {
            "id": "1",
            "title": "룰루레몬",
            "x": "127.0",
            "y": "37.5",
            "dist": 1.2345,
            "ctg": "의류",
            "roadAddress": "서울 강남",
            "totalScore": 200.5,
            "review": {"count": "42"},
        }
    )
    out = views.search_results([item])
    assert out[0] == {
        "id": "1",
        "title": "룰루레몬",
        "category": "의류",
        "roadAddress": "서울 강남",
        "distanceKm": 1.23,
        "reviewCount": 42,
        "rankingScore": 200.5,
        "lat": "37.5",
        "lng": "127.0",
    }


def test_merged_places_prefers_place():
    resp = InstantSearchResponse.model_validate({
        "place": [{"id": "1", "title": "A", "x": "127", "y": "37"}],
        "all": [{"place": {"id": "2", "title": "B", "x": "127", "y": "37"}}],
    })
    merged = resp.merged_places()
    assert [p.id for p in merged] == ["1"]  # place wins, all ignored


def test_merged_places_falls_back_to_all():
    resp = InstantSearchResponse.model_validate({
        "place": [],
        "all": [
            {"place": {"id": "2", "title": "B", "x": "127", "y": "37"}},
            {"address": None, "bus": None},  # non-place entry skipped
        ],
    })
    merged = resp.merged_places()
    assert [p.id for p in merged] == ["2"]


def test_enriched_search_results_merges_detail():
    from naver_places.types.place import PlaceDetail

    item = PlaceItem.model_validate(
        {"id": "1", "title": "A", "x": "127", "y": "37", "ctg": "한식",
         "review": {"count": "10"}}
    )
    detail = PlaceDetail(id="1", name="A", phone="02-1", visitorReviewsScore=4.5,
                         visitorReviewsTotal=99, cafeBlogReviewsTotal=7)
    rows = views.enriched_search_results([(item, detail), (item, None)])
    # Enriched row carries the real rating + phone from detail.
    assert rows[0]["score"] == 4.5
    assert rows[0]["visitorReviewTotal"] == 99
    assert rows[0]["phone"] == "02-1"
    # Failed detail fetch degrades gracefully to null score, not an error.
    assert rows[1]["score"] is None
    assert rows[1]["topKeywords"] == []


def test_drop_none_model_applies_defaults():
    # Regression: Naver returns explicit null for missing rating fields; the
    # null must not blow up non-optional int/float/str fields.
    from naver_places.types.place import PlaceDetail

    d = PlaceDetail.model_validate({
        "id": "1",
        "visitorReviewsTotal": None,
        "visitorReviewsScore": None,
        "roadAddress": None,
    })
    assert d.visitorReviewsTotal == 0
    assert d.visitorReviewsScore == 0.0
    assert d.roadAddress == ""


def test_cache_get_or_set_hits_and_expires():
    import asyncio
    from naver_places import cache

    cache.clear()
    calls = {"n": 0}

    async def factory():
        calls["n"] += 1
        return calls["n"]

    async def run():
        # Fresh ttl: second call served from cache (factory not re-run).
        hit1 = await cache.get_or_set("k", factory, ttl=100)
        hit2 = await cache.get_or_set("k", factory, ttl=100)
        # Stale ttl: each call stores an already-expired entry, so it refetches.
        miss1 = await cache.get_or_set("stale", factory, ttl=-1)
        miss2 = await cache.get_or_set("stale", factory, ttl=-1)
        return hit1, hit2, miss1, miss2

    hit1, hit2, miss1, miss2 = asyncio.run(run())
    assert (hit1, hit2) == (1, 1)       # cached: one factory call
    assert (miss1, miss2) == (2, 3)     # stale entries never serve
    cache.clear()


def test_naverblog_accepts_object():
    # Regression: some places return naverBlog/talktalkUrl as an object, which
    # previously failed the whole detail parse.
    state = {
        "PlaceDetailBase:9": {
            "name": "X",
            "naverBlog": {"url": "http://x"},
            "talktalkUrl": {"url": "http://t"},
        },
    }
    detail = _parse_place_detail("9", state)
    assert detail.name == "X"


def test_place_detail_parse_and_view():
    state = {
        "PlaceDetailBase:1": {
            "name": "룰루레몬 강남",
            "roadAddress": "서울 강남대로",
            "address": "강남동",
            "phone": "02-000-0000",
            "category": "의류,스포츠",
            "coordinate": {"x": "127.0", "y": "37.5"},
            "visitorReviewsTotal": 213,
            "visitorReviewsScore": 4.25,
            "cafeBlogReviewsTotal": 3,
        },
        "VisitorReviewStatsResult:1": {
            "id": "1",
            "review": {"avgRating": 4.25, "totalCount": 213},
            "analysis": {
                "votedKeyword": {
                    "details": [
                        {"code": "quality_good", "displayName": "품질이 좋아요", "count": 113}
                    ]
                }
            },
            "ratingReviewsTotal": 87,
        },
    }
    detail = _parse_place_detail("1", state)
    view = views.place_detail(detail)
    assert view["name"] == "룰루레몬 강남"
    assert view["category"] == ["의류", "스포츠"]
    assert view["score"] == 4.25
    assert view["visitorReviewTotal"] == 213
    assert view["ratingCount"] == 87
    assert view["topKeywords"] == [{"name": "품질이 좋아요", "count": 113}]


def test_graphql_queries_have_operation_names_and_print():
    assert _operation_name(queries.VISITOR_REVIEWS) == "getVisitorReviews"
    assert _operation_name(queries.PHOTO_VIEWER) == "getPhotoViewerItems"
    printed = print_ast(queries.VISITOR_REVIEWS.document)
    assert "visitorReviews" in printed


def test_image_url_allowlist():
    from naver_places.images import _is_allowed_image_url

    assert _is_allowed_image_url("https://pup-review-phinf.pstatic.net/x.jpg")
    assert _is_allowed_image_url("https://phinf.pstatic.net/y.jpg")
    assert not _is_allowed_image_url("https://evil.com/x.jpg")
    assert not _is_allowed_image_url("http://localhost/x")
    assert not _is_allowed_image_url("not a url")
