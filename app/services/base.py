from abc import ABC, abstractmethod
from typing import List, Optional
from app.models.v1 import SearchParams, DownloadRequestV1, SearchResponseV1, DownloadResponseV1

class SubtitleServiceBase(ABC):
    """
    Abstract base class that defines the interface for subtitle services.
    All subtitle services (OpenSubtitles, Addic7ed, etc.) should implement this interface.
    """
    
    @abstractmethod
    async def search_subtitles(self, params: SearchParams) -> SearchResponseV1:
        """
        Search for subtitles using the provided parameters.
        
        Args:
            params: Search parameters
            
        Returns:
            List of subtitles matching the search criteria
        """
        pass

    @abstractmethod
    async def download_subtitle(self, download_request: DownloadRequestV1) -> DownloadResponseV1:
        """
        Download a specific subtitle file.
        
        Args:
            download_request: Download request containing file information
            
        Returns:
            Download response with link and file information
            
        Raises:
            HTTPException: If download fails
        """
        pass