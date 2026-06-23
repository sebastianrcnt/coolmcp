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
    # The "all" section interleaves place/address/bus hits. Naver sometimes
    # populates it even when the top-level `place` array is empty, so it is a
    # useful fallback for recall.
    all_results: list[dict] = Field(default_factory=list, alias="all")

    def merged_places(self) -> list[PlaceItem]:
        """Return `place`, falling back to place hits inside `all` when empty.

        Naver's instant-search is an autocomplete endpoint; for some queries it
        leaves `place` empty while `all` still carries place items. Merging
        recovers those without changing results when `place` is already filled.
        """
        if self.place:
            return self.place
        recovered: list[PlaceItem] = []
        for entry in self.all_results:
            raw = entry.get("place") if isinstance(entry, dict) else None
            if raw:
                recovered.append(PlaceItem.model_validate(raw))
        return recovered
