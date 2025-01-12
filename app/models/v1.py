from pydantic import BaseModel, Field
from typing import List, Optional

class UploaderInfo(BaseModel):
    uploader_id: int
    name: str
    rank: str

class FeatureDetails(BaseModel):
    feature_id: int
    feature_type: str
    year: int
    title: str
    movie_name: str
    imdb_id: int
    tmdb_id: int

class SubtitleFile(BaseModel):
    file_id: int
    cd_number: int
    file_name: str

class SubtitleAttributes(BaseModel):
    subtitle_id: str
    language: str
    download_count: int
    new_download_count: int
    hearing_impaired: bool
    hd: bool
    fps: float
    votes: int
    points: int
    ratings: float
    from_trusted: bool
    foreign_parts_only: bool
    ai_translated: bool
    machine_translated: bool
    upload_date: str
    release: str
    comments: str
    legacy_subtitle_id: int
    uploader: UploaderInfo
    feature_details: FeatureDetails
    url: str
    files: List[SubtitleFile]

class SubtitleAPIV1(BaseModel):
    id: str
    type: str
    attributes: SubtitleAttributes

class SearchResponseV1(BaseModel):
    data: List[SubtitleAPIV1]
    total_pages: int
    total_count: int
    page: int

class DownloadRequestV1(BaseModel):
    file_id: int
    sub_format: Optional[str] = None
    file_name: Optional[str] = None
    url: Optional[str] = None  # Added for Addic7ed support

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
    imdb_id: Optional[int] = None
    tmdb_id: Optional[int] = None
    type: Optional[str] = Field(None, description="movie or episode")
    year: Optional[int] = None
    languages: str = Field(..., description="Comma separated language codes (e.g., eng,spa)")
    season_number: Optional[int] = None
    episode_number: Optional[int] = None
    parent_imdb_id: Optional[int] = None
    parent_tmdb_id: Optional[int] = None
    page: Optional[int] = 1

    def dict(self, *args, **kwargs):
        # Sobreescribimos el método dict para asegurar que los valores sean del tipo correcto
        d = super().dict(*args, **kwargs)
        # Filtrar None y convertir valores booleanos a strings
        return {k: str(v) if isinstance(v, bool) else v 
                for k, v in d.items() 
                if v is not None}
    query: Optional[str] = None
    imdb_id: Optional[int] = None
    tmdb_id: Optional[int] = None
    type: Optional[str] = Field(None, description="movie or episode")
    year: Optional[int] = None
    languages: str = Field(..., description="Comma separated language codes (e.g., eng,spa)")
    season_number: Optional[int] = None
    episode_number: Optional[int] = None
    parent_imdb_id: Optional[int] = None
    parent_tmdb_id: Optional[int] = None
    query_by_title: Optional[bool] = False
    page: Optional[int] = 1