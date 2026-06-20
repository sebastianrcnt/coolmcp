from pydantic import BaseModel, Field


# ── Instant Search ──────────────────────────────────────────────────────────

class ReviewInfo(BaseModel):
    count: str = ""


class PlaceItem(BaseModel):
    id: str
    title: str
    x: str  # longitude
    y: str  # latitude
    dist: float = 0.0
    sid: str = ""
    ctg: str = ""
    cid: str = ""
    jibunAddress: str = ""
    roadAddress: str = ""
    shortAddress: list[str] = Field(default_factory=list)
    totalScore: float = 0.0
    review: ReviewInfo = Field(default_factory=ReviewInfo)
    hasBooking: bool = False
    type: str = "place"


class InstantSearchResponse(BaseModel):
    meta: dict = Field(default_factory=dict)
    ac: list[str] = Field(default_factory=list)
    place: list[PlaceItem] = Field(default_factory=list)
    address: list = Field(default_factory=list)
    bus: list = Field(default_factory=list)


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


# ── Visitor Rating Reviews ───────────────────────────────────────────────────

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


class VisitorReviewItem(BaseModel):
    id: str
    cursor: str = ""
    rating: float | None = None
    author: ReviewAuthor
    visitCount: int = 0
    visited: str = ""
    originType: str | None = None
    reply: ReviewReply | None = None
    votedKeywords: list[VotedKeyword] = Field(default_factory=list)
    businessName: str | None = None
    status: str | None = None
    userIdno: str | None = None
    loginIdno: str | None = None
    receiptInfoUrl: str | None = None
    reactionStat: ReactionStat | None = None
    hasViewerReacted: HasViewerReacted | None = None
    nickname: str | None = None


class VisitorReviewsResult(BaseModel):
    total: int = 0
    items: list[VisitorReviewItem] = Field(default_factory=list)


# ── Review Photos ────────────────────────────────────────────────────────────

class ExternalLink(BaseModel):
    title: str | None = None
    url: str | None = None


class PhotoAuthor(BaseModel):
    id: str = ""
    nickname: str = ""
    from_: str = Field("", alias="from")
    imageUrl: str | None = None
    objectId: str = ""
    url: str = ""
    borderImageUrl: str | None = None

    model_config = {"populate_by_name": True}


class VideoInfo(BaseModel):
    videoId: str
    videoUrl: str
    trailerUrl: str | None = None


class ReviewPhoto(BaseModel):
    viewId: str = ""
    originalUrl: str = ""
    photoType: str = ""
    mediaType: str = ""  # "image" | "video"
    logId: str = ""
    relation: str | None = None
    title: str | None = None
    text: str | None = None
    date: str | None = None
    link: str | None = None
    sourceTitle: str | None = None
    externalLink: ExternalLink | None = None
    author: PhotoAuthor | None = None
    votedKeywords: list[VotedKeyword] = Field(default_factory=list)
    visitCount: int | None = None
    originType: str | None = None
    isFollowing: bool | None = None
    rating: float | None = None
    video: VideoInfo | None = None


# ── Following Reviews ────────────────────────────────────────────────────────

class ReviewMedia(BaseModel):
    type: str | None = None
    thumbnail: str | None = None
    thumbnailRatio: float | None = None
    class_: str | None = Field(None, alias="class")
    videoId: str | None = None
    videoUrl: str | None = None
    trailerUrl: str | None = None

    model_config = {"populate_by_name": True}


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


class FollowingReview(BaseModel):
    id: str
    apolloCacheId: str | None = None
    rating: float | None = None
    author: ReviewAuthor
    body: str | None = None
    thumbnail: str | None = None
    media: list[ReviewMedia] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
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


# ── Theme Lists ──────────────────────────────────────────────────────────────

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
