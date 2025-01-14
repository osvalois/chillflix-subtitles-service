from pydantic import BaseModel, Field
from typing import List, Optional

class UploaderInfo(BaseModel):
    uploader_id: Optional[int] = None  # Hacemos el campo opcional
    name: Optional[str] = None         # También hacemos el nombre opcional
    rank: Optional[str] = None         # Y el rank

class FeatureDetails(BaseModel):
    feature_id: Optional[int] = None
    feature_type: Optional[str] = None
    year: Optional[int] = None
    title: Optional[str] = None
    movie_name: Optional[str] = None
    imdb_id: Optional[int] = None
    tmdb_id: Optional[int] = None

class SubtitleFile(BaseModel):
    file_id: int
    cd_number: Optional[int] = 1
    file_name: str

class SubtitleAttributes(BaseModel):
    subtitle_id: str
    language: str
    download_count: Optional[int] = 0
    new_download_count: Optional[int] = 0
    hearing_impaired: Optional[bool] = False
    hd: Optional[bool] = False
    fps: Optional[float] = 0.0
    votes: Optional[int] = 0
    points: Optional[int] = 0
    ratings: Optional[float] = 0.0
    from_trusted: Optional[bool] = False
    foreign_parts_only: Optional[bool] = False
    ai_translated: Optional[bool] = False
    machine_translated: Optional[bool] = False
    upload_date: Optional[str] = None
    release: Optional[str] = None
    comments: Optional[str] = ""
    legacy_subtitle_id: Optional[int] = None
    provider: Optional[str] = None
    url: Optional[str] = None
    uploader: Optional[UploaderInfo] = None
    feature_details: Optional[FeatureDetails] = None
    files: Optional[List[SubtitleFile]] = None

    class Config:
        extra = "allow"

class SubtitleAPIV1(BaseModel):
    id: str
    type: str
    attributes: SubtitleAttributes

    class Config:
        extra = "allow"

class SearchResponseV1(BaseModel):
    data: List[SubtitleAPIV1]
    total_pages: int
    total_count: int
    page: int

class DownloadRequestV1(BaseModel):
    file_id: Optional[int] = None
    sub_format: Optional[str] = None
    url: Optional[str] = None
    full_link: Optional[str] = None  # Necesario para SubSource

class DownloadResponseV1(BaseModel):
    link: str
    file_name: str
    requests: int
    remaining: int
    message: str
    reset_time: str
    reset_time_utc: str

class SearchParams(BaseModel):
    query: Optional[str] = None
    imdb_id: Optional[str] = None
    tmdb_id: Optional[int] = None
    type: Optional[str] = None
    year: Optional[int] = None
    languages: Optional[str] = None
    season_number: Optional[int] = None
    episode_number: Optional[int] = None
    parent_imdb_id: Optional[str] = None
    parent_tmdb_id: Optional[int] = None
    page: Optional[int] = 1
    
    def dict(self, *args, **kwargs):
        d = super().dict(*args, **kwargs)
        return {k: v for k, v in d.items() if v is not None}