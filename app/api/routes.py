from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import Optional, Literal
import logging
from app.models.v1 import (
    SearchResponseV1,
    DownloadResponseV1,
    SearchParams,
    DownloadRequestV1
)
from app.services.opensubtitles import OpenSubtitlesAPI
from app.services.bsplayer import BSPlayerAPI
from app.api.dependencies import get_api_key

router = APIRouter(prefix="/api/v1")
logger = logging.getLogger(__name__)

def get_subtitle_service(provider: str, api_key: str):
    """Factory function to get the appropriate subtitle service"""
    providers = {
        "opensubtitles": OpenSubtitlesAPI,
        "bsplayer": BSPlayerAPI
    }
    
    if provider not in providers:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid provider. Available providers: {', '.join(providers.keys())}"
        )
    
    return providers[provider](api_key)

@router.get("/subtitles/search", response_model=SearchResponseV1)
async def search_subtitles(
    provider: str = Query(..., description="Subtitle provider (opensubtitles or bsplayer)"),
    query: Optional[str] = None,
    imdb_id: Optional[int] = None,
    languages: str = Query(..., description="Comma separated language codes"),
    type: Optional[str] = None,
    year: Optional[int] = None,
    season_number: Optional[int] = None,
    episode_number: Optional[int] = None,
    page: Optional[int] = 1,
    api_key: str = Depends(get_api_key)
):
    """
    Search for subtitles using various parameters.
    """
    try:
        params = SearchParams(
            query=query,
            imdb_id=imdb_id,
            languages=languages,
            type=type,
            year=year,
            season_number=season_number,
            episode_number=episode_number,
            page=page
        )
        
        api = get_subtitle_service(provider, api_key)
        return await api.search_subtitles(params)
    
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while searching subtitles: {str(e)}"
        )

@router.post("/subtitles/download", response_model=DownloadResponseV1)
async def download_subtitle(
    download_request: DownloadRequestV1,
    api_key: str = Depends(get_api_key)
):
    """
    Download a specific subtitle file.
    """
    try:
        api = OpenSubtitlesAPI(api_key)
        return await api.download_subtitle(download_request)
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))