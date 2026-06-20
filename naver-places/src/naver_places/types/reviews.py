from pydantic import BaseModel, Field


# ── Shared ──────────────────────────────────────────────────────────────────

class VotedKeyword(BaseModel):
    code: str = ""
    iconUrl: str | None = None
    iconCode: str | None = None
    displayName: str | None = None
    name: str = ""


class ReactionTypeCount(BaseModel):
    name: str
    count: int


class ReactionStat(BaseModel):
    id: str
    typeCount: list[ReactionTypeCount] = Field(default_factory=list)
    totalCount: int = 0


class HasViewerReacted(BaseModel):
    id: str
    reacted: bool


class ReactionType(BaseModel):
    name: str
    emojiUrl: str
    label: str


class ReviewReply(BaseModel):
    editUrl: str | None = None
    body: str | None = None
    editedBy: str | None = None
    created: str | None = None
    date: str | None = None
    replyTitle: str | None = None
    isReported: bool | None = None
    isSuspended: bool | None = None
    status: str | None = None


class ReviewItem(BaseModel):
    name: str | None = None
    code: str | None = None
    options: list | None = None


class VisitCategoryKeyword(BaseModel):
    code: str
    name: str


class VisitCategory(BaseModel):
    code: str
    name: str
    keywords: list[VisitCategoryKeyword] = Field(default_factory=list)


class ReviewMedia(BaseModel):
    type: str | None = None
    thumbnail: str | None = None
    thumbnailRatio: float | str | None = None
    class_: str | None = Field(None, alias="class")
    videoId: str | None = None
    videoUrl: str | None = None
    trailerUrl: str | None = None

    model_config = {"populate_by_name": True}


class HighlightRange(BaseModel):
    start: int
    end: int


# ── Author ───────────────────────────────────────────────────────────────────

class AuthorReviewStats(BaseModel):
    totalCount: int = 0
    imageCount: int = 0
    avgRating: float = 0.0


class AuthorThemeStats(BaseModel):
    totalCount: int = 0


class ReviewAuthor(BaseModel):
    id: str = ""
    nickname: str = ""
    from_: str = Field("", alias="from")
    imageUrl: str | None = None
    borderImageUrl: str | None = None
    objectId: str = ""
    url: str = ""
    review: AuthorReviewStats | None = None
    theme: AuthorThemeStats | None = None
    isFollowing: bool | None = None
    followerCount: str = ""
    followRequested: bool | None = None

    model_config = {"populate_by_name": True}


# ── Visitor Reviews (getVisitorReviews) ──────────────────────────────────────

class StarDistribution(BaseModel):
    score: float | None = None
    count: int = 0


class ItemReviewStats(BaseModel):
    score: float = 0.0
    count: int = 0
    itemId: str | None = None
    starDistribution: list[StarDistribution] = Field(default_factory=list)


class VisitorReviewItem(BaseModel):
    id: str
    cursor: str = ""
    reviewId: str | None = None
    rating: float | None = None
    author: ReviewAuthor
    body: str | None = None
    thumbnail: str | None = None
    media: list[ReviewMedia] = Field(default_factory=list)
    tags: list[str] | None = None
    status: str | None = None
    visitCount: int = 0
    viewCount: int = 0
    visited: str = ""
    created: str | None = None
    reply: ReviewReply | None = None
    originType: str | None = None
    item: ReviewItem | None = None
    language: str | None = None
    highlightRanges: list[HighlightRange] | None = None
    apolloCacheId: bool | None = None
    translatedText: str | None = None
    businessName: str | None = None
    showBookingItemName: bool | None = None
    bookingItemName: str | None = None
    votedKeywords: list[VotedKeyword] = Field(default_factory=list)
    userIdno: str | None = None
    loginIdno: str | None = None
    receiptInfoUrl: str | None = None
    reactionStat: ReactionStat | None = None
    hasViewerReacted: HasViewerReacted | None = None
    nickname: str | None = None
    showPaymentInfo: bool | None = None
    visitCategories: list[VisitCategory] = Field(default_factory=list)
    representativeVisitDateTime: str | None = None
    showRepresentativeVisitDateTime: bool | None = None


class VisitorReviewsResult(BaseModel):
    items: list[VisitorReviewItem] = Field(default_factory=list)
    starDistribution: list[StarDistribution] | None = None
    hideProductSelectBox: bool | None = None
    total: int = 0
    showRecommendationSort: bool = False
    itemReviewStats: ItemReviewStats | None = None


# ── Following Reviews (getFollowingReviews) ──────────────────────────────────

class FollowingReview(BaseModel):
    id: str
    apolloCacheId: str | None = None
    rating: float | None = None
    author: ReviewAuthor
    body: str | None = None
    thumbnail: str | None = None
    media: list[ReviewMedia] = Field(default_factory=list)
    tags: list[str] | None = None
    status: str | None = None
    visitCount: int = 0
    viewCount: int = 0
    visited: str | None = None
    created: str | None = None
    reply: ReviewReply | None = None
    originType: str | None = None
    item: ReviewItem | None = None
    businessName: str | None = None
    votedKeywords: list[VotedKeyword] = Field(default_factory=list)
    visitCategories: list[VisitCategory] = Field(default_factory=list)
    userIdno: str | None = None
    loginIdno: str | None = None
    reactionStat: ReactionStat | None = None
    hasViewerReacted: HasViewerReacted | None = None
    nickname: str | None = None
    representativeVisitDateTime: str | None = None


class FollowingReviewsResult(BaseModel):
    reviews: list[FollowingReview] = Field(default_factory=list)
    reactionTypes: list[ReactionType] = Field(default_factory=list)


# ── Theme Lists (getVisitorReviewThemeLists) ─────────────────────────────────

class ThemeListReview(BaseModel):
    businessName: str | None = None
    reviewBody: str | None = None
    imageUrl: str | None = None


class ThemeList(BaseModel):
    id: str
    title: str
    viewCount: int = 0
    itemCount: int = 0
    reviews: list[ThemeListReview] = Field(default_factory=list)
    authorNickname: str | None = None
    authorImageUrl: str | None = None
    isFollowing: bool | None = None
    themeListUrl: str | None = None
    authorUrl: str | None = None
    cursor: str | None = None


class ThemeListsResult(BaseModel):
    themeLists: list[ThemeList] = Field(default_factory=list)
    total: int = 0
