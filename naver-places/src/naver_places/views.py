from .types import (
    InstantSearchResponse,
    PlaceItem,
    PlaceDetail,
    VisitorReviewsResult,
    FollowingReviewsResult,
    ThemeListsResult,
    ReviewPhoto,
    PhotoViewerResult,
)


def _as_int(value, default=0):
    """Helper to safely parse int from various types."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def search_results(items: list[PlaceItem]) -> list[dict]:
    """Project PlaceItems to lean search results.

    NOTE on fields:
    - `rankingScore` is Naver's internal relevance/popularity weight (roughly
      0–200+), NOT a user rating. Do not show it as a star score. The 0–5
      visitor rating only comes from get_place_detail (`score`).
    - `distanceKm` is measured from the `coords` you passed to the search (or
      the default Seoul-center point if you passed none), so it is only
      meaningful when you supplied coordinates near your area of interest.
    """
    result = []
    for item in items:
        result.append({
            "id": item.id,
            "title": item.title,
            "category": item.ctg,
            "roadAddress": item.roadAddress,
            "distanceKm": round(item.dist, 2),
            "reviewCount": _as_int(item.review.count, default=0),
            "rankingScore": item.totalScore,
            "lat": item.y,
            "lng": item.x,
        })
    return result


def place_detail(d: PlaceDetail) -> dict:
    """Project PlaceDetail to lean detail view."""
    # Extract topKeywords safely
    topKeywords = []
    if (d.reviewSummary is not None
            and d.reviewSummary.analysis is not None
            and d.reviewSummary.analysis.votedKeyword is not None):
        for detail in d.reviewSummary.analysis.votedKeyword.details:
            topKeywords.append({
                "name": detail.displayName,
                "count": detail.count,
            })

    # Extract ratingCount safely
    ratingCount = 0
    if d.reviewSummary is not None:
        ratingCount = d.reviewSummary.ratingReviewsTotal

    return {
        "id": d.id,
        "name": d.name,
        "category": d.category,
        "roadAddress": d.roadAddress,
        "address": d.address,
        "phone": d.phone,
        # 0–5 visitor rating (this is the real star score, unlike search's rankingScore).
        "score": d.visitorReviewsScore,
        # All visitor reviews, including photo/receipt/rating-only ones. This is
        # typically LARGER than the `total` from get_place_visitor_reviews, which
        # counts only the text reviews in that feed.
        "visitorReviewTotal": d.visitorReviewsTotal,
        "blogReviewTotal": d.cafeBlogReviewsTotal,
        "ratingCount": ratingCount,
        "topKeywords": topKeywords,
    }


def visitor_reviews(r: VisitorReviewsResult) -> dict:
    """Project VisitorReviewsResult to lean reviews view.

    `total` here is the count of TEXT reviews in this feed. It is usually lower
    than get_place_detail's `visitorReviewTotal`, which also counts
    rating-only / receipt / photo reviews. Use `nextCursor` to page.
    """
    reviews_list = []
    next_cursor = None

    for item in r.items:
        # Extract author nickname
        author_nickname = None
        if item.author is not None:
            author_nickname = item.author.nickname

        # Extract keywords
        keywords = [k.name for k in item.votedKeywords]

        # Extract reply body
        reply_body = None
        if item.reply is not None and item.reply.body is not None:
            reply_body = item.reply.body

        reviews_list.append({
            "author": author_nickname,
            "rating": item.rating,
            "body": item.body,
            "visited": item.visited,
            "keywords": keywords,
            "photoCount": len(item.media),
            "reply": reply_body,
        })

        # Capture cursor from last item
        if item.cursor:
            next_cursor = item.cursor

    return {
        "total": r.total,
        "nextCursor": next_cursor,
        "reviews": reviews_list,
    }


def review_photos(photos: list[ReviewPhoto]) -> list[dict]:
    """Project ReviewPhotos to lean photo view."""
    result = []
    for photo in photos:
        # Extract author nickname
        author_nickname = None
        if photo.author is not None:
            author_nickname = photo.author.nickname

        # Extract keywords
        keywords = [k.name for k in photo.votedKeywords]

        result.append({
            "url": photo.originalUrl,
            "mediaType": photo.mediaType,
            "isVideo": photo.mediaType == "video",
            "text": photo.text,
            "date": photo.date,
            "author": author_nickname,
            "keywords": keywords,
        })

    return result


def photo_gallery(r: PhotoViewerResult) -> dict:
    """Project PhotoViewerResult to lean gallery view."""
    # Cursor objects
    cursors = [c.model_dump() for c in r.cursors]

    # Photos
    photos_list = []
    for p in r.photos:
        # Extract author nickname
        author_nickname = None
        if p.author is not None:
            author_nickname = p.author.nickname

        photos_list.append({
            "url": p.originalUrl,
            "mediaType": p.mediaType,
            "isVideo": p.mediaType == "video",
            "text": p.text,
            "date": p.date,
            "author": author_nickname,
            "width": p.width,
            "height": p.height,
        })

    return {
        "cursors": cursors,
        "photos": photos_list,
    }


def following_reviews(r: FollowingReviewsResult) -> dict:
    """Project FollowingReviewsResult to lean reviews view."""
    reviews_list = []

    for item in r.reviews:
        # Extract author nickname
        author_nickname = None
        if item.author is not None:
            author_nickname = item.author.nickname

        # Extract keywords
        keywords = [k.name for k in item.votedKeywords]

        reviews_list.append({
            "author": author_nickname,
            "rating": item.rating,
            "body": item.body,
            "visited": item.visited,
            "keywords": keywords,
        })

    return {
        "count": len(r.reviews),
        "reviews": reviews_list,
    }


def theme_lists(r: ThemeListsResult) -> dict:
    """Project ThemeListsResult to lean theme lists view."""
    lists = []

    for t in r.themeLists:
        sample_reviews = []
        for rv in t.reviews:
            sample_reviews.append({
                "businessName": rv.businessName,
                "body": rv.reviewBody,
            })

        lists.append({
            "title": t.title,
            "viewCount": t.viewCount,
            "itemCount": t.itemCount,
            "author": t.authorNickname,
            "sampleReviews": sample_reviews,
        })

    return {
        "total": r.total,
        "lists": lists,
    }
