import aiohttp
from fastapi import HTTPException
from app.models.v1 import (
    SearchResponseV1, 
    DownloadResponseV1, 
    SearchParams, 
    DownloadRequestV1,
    SubtitleAPIV1
)
from app.services.base import SubtitleServiceBase
from typing import List, Optional

class OpenSubtitlesAPI(SubtitleServiceBase):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.opensubtitles.com/api/v1"
        self.headers = {
            "Api-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "SubtitlesAPI v1.0"
        }

    async def search_subtitles(self, params: SearchParams) -> SearchResponseV1:
        """
        Search for subtitles using the provided parameters
        """
        try:
            query_params = params.dict(exclude_none=True, exclude_unset=True)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/subtitles",
                    headers=self.headers,
                    params=query_params
                ) as response:
                    if response.status == 401:
                        raise HTTPException(
                            status_code=401,
                            detail="Invalid or expired API key"
                        )
                    elif response.status == 429:
                        raise HTTPException(
                            status_code=429,
                            detail="Rate limit exceeded"
                        )
                    elif response.status != 200:
                        error_text = await response.text()
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"OpenSubtitles API error: {error_text}"
                        )
                    
                    response_data = await response.json()
                    return SearchResponseV1(**response_data)
                    
        except aiohttp.ClientError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Error connecting to OpenSubtitles API: {str(e)}"
            )

    async def download_subtitle(self, download_request: DownloadRequestV1) -> DownloadResponseV1:
        """
        Download a specific subtitle file
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/download",
                    headers=self.headers,
                    json=download_request.dict(exclude_none=True)
                ) as response:
                    if response.status == 401:
                        raise HTTPException(
                            status_code=401,
                            detail="Invalid or expired API key"
                        )
                    elif response.status == 429:
                        raise HTTPException(
                            status_code=429,
                            detail="Rate limit exceeded"
                        )
                    elif response.status != 200:
                        error_text = await response.text()
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"OpenSubtitles API error: {error_text}"
                        )
                    
                    response_data = await response.json()
                    return DownloadResponseV1(**response_data)
                    
        except aiohttp.ClientError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Error connecting to OpenSubtitles API: {str(e)}"
            )