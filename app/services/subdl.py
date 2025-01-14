import aiohttp
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class SubDLAPI:
    BASE_URL = "https://api.subdl.com/api/v1"
    DL_BASE_URL = "https://dl.subdl.com"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def verify_api_key(self):
        """Verifica que la API key sea válida"""
        try:
            await self._make_request("GET", "verify")
            return True
        except HTTPException:
            return False
        
    async def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None) -> Dict[Any, Any]:
        async with aiohttp.ClientSession() as session:
            url = f"{self.BASE_URL}/{endpoint}"
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            }
            params = params or {}
            params["api_key"] = self.api_key
            
            try:
                async with session.request(method, url, params=params, headers=headers) as response:
                    try:
                        data = await response.json()
                    except aiohttp.ContentTypeError:
                        logger.error("Error decoding JSON response from SubDL")
                        raise HTTPException(status_code=500, detail="Invalid response from SubDL API")
                    
                    # La respuesta exitosa de SubDL siempre incluye status=true
                    if not data.get("status", False):
                        logger.error(f"SubDL API error: {data}")
                        raise HTTPException(
                            status_code=response.status,
                            detail=data.get("message", "Unknown error from SubDL")
                        )
                    
                    return data
                    
            except aiohttp.ClientError as e:
                logger.error(f"Network error with SubDL API: {str(e)}")
                raise HTTPException(status_code=500, detail="Network error connecting to SubDL API")

    def _convert_to_opensubtitles_format(self, subdl_subtitle: Dict) -> Dict:
        """Convierte el formato de SubDL al formato de OpenSubtitles"""
        return {
            "id": str(subdl_subtitle.get("sd_id", "")),
            "type": "subtitle",
            "attributes": {
                "subtitle_id": str(subdl_subtitle.get("sd_id", "")),
                "language": subdl_subtitle.get("language", "").lower(),
                "download_count": 0,
                "new_download_count": 0,
                "hearing_impaired": subdl_subtitle.get("hi", False),
                "hd": False,
                "fps": 0.0,
                "votes": 0,
                "points": 0,
                "ratings": 0.0,
                "from_trusted": False,
                "foreign_parts_only": False,
                "ai_translated": False,
                "machine_translated": False,
                "release": subdl_subtitle.get("release_name", ""),
                "comments": "",
                "legacy_subtitle_id": None,
                "url": subdl_subtitle.get("url", ""),
                "upload_date": None,
                "provider": "subdl",
                "uploader": {
                    "uploader_id": None,
                    "name": subdl_subtitle.get("author", "Anonymous"),
                    "rank": "anonymous"
                },
                "feature_details": {
                    "feature_id": subdl_subtitle.get("sd_id", 0),
                    "feature_type": "movie" if not subdl_subtitle.get("season") else "tv",
                    "year": None,
                    "title": subdl_subtitle.get("release_name", ""),
                    "movie_name": subdl_subtitle.get("release_name", ""),
                    "imdb_id": None,
                    "tmdb_id": None
                },
                "files": [{
                    "file_id": 0,
                    "cd_number": 1,
                    "file_name": subdl_subtitle.get("name", "")
                }]
            }
        }

    async def search_subtitles(self, imdb_id: str, type: str = "movie", languages: str = "en", 
                             season_number: Optional[int] = None, episode_number: Optional[int] = None) -> Dict:
        """
        Busca subtítulos en SubDL
        
        Args:
            imdb_id: ID de IMDB (con o sin el prefijo 'tt')
            type: Tipo de búsqueda ('movie' o 'tv')
            languages: Códigos de idioma separados por coma (ej: 'en,es')
            season_number: Número de temporada para series
            episode_number: Número de episodio para series
        """
        params = {
            "type": type,
            "languages": languages,
            "subs_per_page": 30
        }

        # Para películas
        if type == "movie":
            params["imdb_id"] = f"tt{imdb_id}" if not imdb_id.startswith('tt') else imdb_id
        # Para series
        else:
            if not imdb_id.startswith('tt'):
                imdb_id = f"tt{imdb_id}"
            params["imdb_id"] = imdb_id
            if season_number:
                params["season"] = season_number
            if episode_number:
                params["episode"] = episode_number

        try:
            data = await self._make_request("GET", "subtitles", params)
            
            # Convertir resultados al formato de OpenSubtitles
            converted_subtitles = [
                self._convert_to_opensubtitles_format(sub) 
                for sub in data.get("subtitles", [])
            ]
            
            return {
                "data": converted_subtitles,
                "total_count": len(converted_subtitles),
                "total_pages": data.get("totalPages", 1),
                "page": data.get("currentPage", 1)
            }
        except Exception as e:
            logger.error(f"Error searching subtitles: {str(e)}")
            raise

    async def download_subtitle(self, url: str) -> Dict:
        """
        Construye la URL de descarga para un subtítulo
        
        Args:
            url: URL relativa del subtítulo proporcionada por SubDL
        """
        if not url:
            raise HTTPException(status_code=400, detail="URL is required")
            
        full_url = f"{self.DL_BASE_URL}{url}"
        return {
            "link": full_url,
            "file_name": url.split("/")[-1],
            "requests": 0,
            "remaining": 0,
            "message": "Success",
            "reset_time": "",
            "reset_time_utc": ""
        }
        
    async def languages(self) -> Dict:
        """Obtiene la lista de idiomas soportados"""
        return await self._make_request("GET", "languages")
        
    async def formats(self) -> Dict:
        """Obtiene la lista de formatos soportados"""
        return await self._make_request("GET", "formats")