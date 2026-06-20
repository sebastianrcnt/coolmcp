from pydantic import BaseModel, Field


class ExternalLink(BaseModel):
    title: str | None = None
    url: str | None = None


class VideoInfo(BaseModel):
    videoId: str
    videoUrl: str
    trailerUrl: str | None = None


class PhotoOption(BaseModel):
    channelName: str | None = None
    dateString: str | None = None
    playCount: int | None = None
    likeCount: int | None = None


class MomentInfo(BaseModel):
    channelId: str | None = None
    contentId: str | None = None
    momentId: str | None = None
    gdid: str | None = None
    blogRelation: str | None = None
    statAllowYn: str | None = None
    category: str | None = None
    docNo: str | None = None


class MusicInfo(BaseModel):
    artists: list[str] = Field(default_factory=list)
    title: str | None = None


class ClipInfo(BaseModel):
    serviceType: str | None = None
    createdAt: str | None = None
    contentType: str | None = None


class PhotoVotedKeyword(BaseModel):
    code: str = ""
    iconUrl: str | None = None
    iconCode: str | None = None
    name: str = ""


class PhotoAuthor(BaseModel):
    id: str | None = None
    nickname: str | None = None
    from_: str | None = Field(None, alias="from")
    imageUrl: str | None = None
    objectId: str | None = None
    url: str | None = None
    borderImageUrl: str | None = None
    officialYn: str | None = None

    model_config = {"populate_by_name": True}


# ── Visitor Review Photos (getVisitorReviewPhotosInVisitorReviewTab) ──────────

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
    votedKeywords: list[PhotoVotedKeyword] = Field(default_factory=list)
    visitCount: int | None = None
    originType: str | None = None
    isFollowing: bool | None = None
    rating: float | None = None
    video: VideoInfo | None = None


# ── Photo Viewer (getPhotoViewerItems) ───────────────────────────────────────

class PhotoViewerCursor(BaseModel):
    id: str
    startIndex: int
    hasNext: bool
    lastCursor: str | None = None


class PhotoViewerImage(BaseModel):
    viewId: str = ""
    originalUrl: str = ""
    originalDate: str | None = None
    width: int | None = None
    height: int | None = None
    title: str | None = None
    text: str | None = None
    desc: str | None = None
    link: str | None = None
    date: str | None = None
    photoType: str | None = None
    mediaType: str | None = None  # "image" | "video"
    option: PhotoOption | None = None
    to: str | None = None
    relation: str | None = None
    logId: str | None = None
    author: PhotoAuthor | None = None
    votedKeywords: list[PhotoVotedKeyword] | None = None
    visitCount: int | None = None
    originType: str | None = None
    isFollowing: bool | None = None
    businessName: str | None = None
    rating: float | None = None
    externalLink: ExternalLink | None = None
    sourceTitle: str | None = None
    moment: MomentInfo | None = None
    video: VideoInfo | None = None
    music: MusicInfo | None = None
    clip: ClipInfo | None = None


class PhotoViewerResult(BaseModel):
    cursors: list[PhotoViewerCursor] = Field(default_factory=list)
    photos: list[PhotoViewerImage] = Field(default_factory=list)
