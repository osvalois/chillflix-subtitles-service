# app/services/subsource.py
import aiohttp
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class SubSourceAPI:
    API_URL = "https://api.subsource.net/api"
    
    def __init__(self):
        self.endpoints = {
            "search": f"{self.API_URL}/searchMovie",
            "get_movie": f"{self.API_URL}/getMovie",
            "get_sub": f"{self.API_URL}/getSub",
            "download": f"{self.API_URL}/downloadSub"
        }
        
        self.language_map = {
            "Big 5 code": "zh",
            "Brazilian Portuguese": "pt-BR",
            "Bulgarian": "bg",
            "Chinese BG code": "zh",
            "Farsi/Persian": "fa",
            "Chinese(Simplified)": "zh-Hans",
            "Chinese(Traditional)": "zh-Hant",
            "French(France)": "fr-FR",
            "Icelandic": "is",
            "Spanish(Latin America)": "es-419",
            "Spanish(Spain)": "es-ES"
        }

    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, stream: bool = False) -> Dict[Any, Any]:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            try:
                async with session.request(method, endpoint, json=data, headers=headers) as response:
                    if stream:
                        return await response.read()
                    return await response.json()
            except aiohttp.ClientError as e:
                logger.error(f"Error en la petición a SubSource: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

    def _convert_to_opensubtitles_format(self, subsource_subtitle: Dict) -> Dict:
        """Convierte el formato de SubSource al formato de OpenSubtitles"""
        return {
            "id": str(subsource_subtitle.get("subId", "")),
            "type": "subtitle",
            "attributes": {
                "subtitle_id": str(subsource_subtitle.get("subId", "")),
                "language": self._map_language(subsource_subtitle.get("lang", "")),
                "download_count": 0,
                "hearing_impaired": subsource_subtitle.get("hi", 0) != 0,
                "release": subsource_subtitle.get("releaseName", ""),
                "rating": subsource_subtitle.get("rating", 0),
                "url": subsource_subtitle.get("fullLink", ""),
                "upload_date": None,
                "provider": "subsource",
                "files": [{
                    "file_id": 0,
                    "file_name": subsource_subtitle.get("releaseName", "")
                }]
            }
        }

    def _map_language(self, lang: str) -> str:
        """Mapea los códigos de idioma de SubSource a códigos estándar"""
        return self.language_map.get(lang, lang.lower())

    async def search_subtitles(self, imdb_id: str, type: str = "movie", languages: str = "en", 
                             season_number: Optional[int] = None, episode_number: Optional[int] = None) -> Dict:
        """
        Proceso completo de búsqueda de subtítulos:
        1. Buscar película/serie
        2. Obtener información detallada
        3. Obtener subtítulos disponibles
        """
        # 1. Búsqueda inicial
        search_data = {
            "query": f"{imdb_id}"  # Podrías agregar más información si es necesario
        }
        search_results = await self._make_request("POST", self.endpoints["search"], search_data)

        if not search_results.get("found"):
            return {"data": [], "total_count": 0, "total_pages": 1, "page": 1}

        # 2. Obtener información detallada
        movie_data = {
            "movieName": search_results["found"][0]["linkName"],
            "langs": languages.split(",")
        }
        
        if type == "tv" and season_number:
            movie_data["season"] = f"season-{season_number}"

        movie_info = await self._make_request("POST", self.endpoints["get_movie"], movie_data)

        # 3. Convertir resultados
        if "subs" not in movie_info:
            return {"data": [], "total_count": 0, "total_pages": 1, "page": 1}

        converted_subtitles = [
            self._convert_to_opensubtitles_format(sub)
            for sub in movie_info["subs"]
        ]

        return {
            "data": converted_subtitles,
            "total_count": len(converted_subtitles),
            "total_pages": 1,
            "page": 1
        }

    async def download_subtitle(self, url: str) -> Dict:
        """
        Proceso de descarga:
        1. Extraer información de la URL
        2. Obtener token de descarga
        3. Descargar subtítulo
        """
        # Extraer información de la URL
        *_, movie, lang, sub_id = url.split("/")
        
        # Obtener token
        sub_data = {
            "movie": movie,
            "lang": lang,
            "id": sub_id
        }
        
        sub_info = await self._make_request("POST", self.endpoints["get_sub"], sub_data)
        download_token = sub_info["sub"]["downloadToken"]
        
        # Construir URL de descarga
        download_url = f"{self.endpoints['download']}/{download_token}"
        
        return {
            "link": download_url,
            "file_name": f"{movie}_{lang}.srt",
            "requests": 0,
            "remaining": 0,
            "message": "Success",
            "reset_time": "",
            "reset_time_utc": ""
        }

    async def languages(self) -> Dict:
        """Obtiene la lista de idiomas soportados"""
        return {"languages": list(self.language_map.values())}
    
    async def formats(self) -> Dict:
        """Obtiene la lista de formatos soportados"""
        return {"formats": ["srt"]}  # SubSource típicamente usa SRT