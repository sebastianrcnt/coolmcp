from pydantic import BaseModel, Field


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
