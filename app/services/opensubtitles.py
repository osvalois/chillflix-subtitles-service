import logging
from typing import Optional, Dict, Any
import aiohttp
from app.models.v1 import SearchParams
from fastapi import HTTPException
from pydantic import BaseModel

# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# app/services/opensubtitles.py
from app.core.config import settings

class OpenSubtitlesAPI:
    """
    Cliente para la API de OpenSubtitles v1
    """
    def __init__(self, base_url: str = "https://api.opensubtitles.com/api/v1"):
        """
        Inicializa el cliente de OpenSubtitles
        
        Args:
            base_url: URL base de la API (por defecto: https://api.opensubtitles.com/api/v1)
        """
        self.api_key = settings.OPENSUBTITLES_API_KEY
        self.base_url = base_url
        self.headers = {
            "Api-Key": self.api_key,
            "Content-Type": "application/json"
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Realiza una petición HTTP a la API
        
        Args:
            method: Método HTTP (GET, POST, etc)
            endpoint: Endpoint de la API
            params: Parámetros de query string
            data: Datos para el body de la petición
            
        Returns:
            Dict con la respuesta de la API
        """
        url = f"{self.base_url}/{endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=self.headers,
                    ssl=False  # Solo para desarrollo
                ) as response:
                    response_text = await response.text()
                    
                    if response.status != 200:
                        logger.error(f"Error en API OpenSubtitles: {response_text}")
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"Error en API OpenSubtitles: {response_text}"
                        )
                        
                    return await response.json()

        except aiohttp.ClientError as e:
            logger.error(f"Error de conexión con OpenSubtitles: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail=f"Error de conexión con OpenSubtitles: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error inesperado: {str(e)}"
            )

    def _format_imdb_id(self, imdb_id: str) -> str:
        """
        Formatea el ID de IMDB para asegurar que tiene el prefijo 'tt' y 7 dígitos
        
        Args:
            imdb_id: ID de IMDB con o sin prefijo 'tt'
            
        Returns:
            ID de IMDB formateado
        """
        if imdb_id is None:
            return None
            
        # Eliminar el prefijo 'tt' si existe
        clean_id = imdb_id.lower().replace('tt', '')
        
        # Asegurar que tiene 7 dígitos y agregar el prefijo 'tt'
        return f"tt{clean_id.zfill(7)}"

    async def search_subtitles(self, imdb_id: str) -> Dict[str, Any]:
        """
        Busca subtítulos usando solo el IMDB ID
        
        Args:
            imdb_id: ID de IMDB
            
        Returns:
            Dict con los resultados de la búsqueda
        """
        params = {
            "imdb_id": imdb_id
        }
        
        logger.info(f"Búsqueda por IMDB ID: {imdb_id}")
        
        return await self._make_request(
            method="GET",
            endpoint="subtitles",
            params=params
        )

    async def download_subtitle(self, file_id: int, sub_format: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene el enlace de descarga para un subtítulo
        
        Args:
            file_id: ID del archivo de subtítulos
            sub_format: Formato deseado del subtítulo (opcional)
            
        Returns:
            Dict con la información de descarga
        """
        data = {
            "file_id": file_id
        }
        
        if sub_format:
            data["sub_format"] = sub_format
            
        return await self._make_request(
            method="POST",
            endpoint="download",
            data=data
        )

    async def languages(self) -> Dict[str, Any]:
        """
        Obtiene la lista de idiomas soportados
        
        Returns:
            Dict con la lista de idiomas
        """
        return await self._make_request(
            method="GET",
            endpoint="infos/languages"
        )

    async def formats(self) -> Dict[str, Any]:
        """
        Obtiene la lista de formatos soportados
        
        Returns:
            Dict con la lista de formatos
        """
        return await self._make_request(
            method="GET",
            endpoint="infos/formats"
        )