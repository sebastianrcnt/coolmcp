from pydantic import Field

from .base import DropNoneModel as _DropNoneModel


class Coordinate(_DropNoneModel):
    x: str = ""  # longitude
    y: str = ""  # latitude


class OpeningHours(_DropNoneModel):
    businessStatus: dict | None = None
    offdayHolidays: list | None = None
    regularlyDay: list | None = None


class VotedKeywordDetail(_DropNoneModel):
    category: str | None = None
    code: str = ""
    iconUrl: str | None = None
    iconCode: str | None = None
    displayName: str | None = None
    count: int = 0
    previousRank: int | None = None


class VotedKeywordStats(_DropNoneModel):
    totalCount: int = 0
    reviewCount: int = 0
    userCount: int = 0
    details: list[VotedKeywordDetail] = Field(default_factory=list)


class ReviewStatsAnalysis(_DropNoneModel):
    themes: list = Field(default_factory=list)
    menus: list = Field(default_factory=list)
    votedKeyword: VotedKeywordStats | None = None


class VisitorReviewScore(_DropNoneModel):
    count: int = 0
    score: float | None = None


class VisitorReviewStats(_DropNoneModel):
    avgRating: float = 0.0
    totalCount: int = 0
    scores: list[VisitorReviewScore] = Field(default_factory=list)
    imageReviewCount: int = 0
    authorCount: int = 0


class PlaceReviewSummary(_DropNoneModel):
    id: str
    name: str | None = None
    review: VisitorReviewStats | None = None
    analysis: ReviewStatsAnalysis | None = None
    visitorReviewsTotal: int = 0
    ratingReviewsTotal: int = 0


class PlaceDetail(_DropNoneModel):
    id: str
    name: str = ""
    category: list[str] = Field(default_factory=list)
    categoryCode: str = ""
    roadAddress: str = ""
    address: str = ""
    phone: str | None = None
    virtualPhone: str | None = None
    coordinate: Coordinate | None = None
    openingHours: dict | None = None
    visitorReviewsTotal: int = 0
    visitorReviewsScore: float = 0.0
    cafeBlogReviewsTotal: int = 0
    reviewSummary: PlaceReviewSummary | None = None
    # Naver returns either a URL string or a structured object for these,
    # depending on the place, so accept both rather than failing the whole parse.
    naverBlog: dict | str | None = None
    talktalkUrl: dict | str | None = None
    isGoodStore: bool = False
