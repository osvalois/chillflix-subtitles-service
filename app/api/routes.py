# app/api/routes.py
from fastapi import APIRouter, HTTPException
import logging
from app.models.v1 import DownloadRequestV1, DownloadResponseV1, SearchResponseV1
from app.services.opensubtitles import OpenSubtitlesAPI

# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Router para la API de OpenSubtitles
router = APIRouter()

@router.get("/api/v1/subtitles", response_model=SearchResponseV1)
async def search_subtitles(imdb_id: str):
    """
    Busca subtítulos usando la API de OpenSubtitles usando solo IMDB ID
    """
    try:
        # Inicializar el cliente de API
        client = OpenSubtitlesAPI()

        # Realizar la búsqueda
        response = await client.search_subtitles(imdb_id)
        
        # Convertir la respuesta al modelo SearchResponseV1
        return SearchResponseV1(
            data=response.get('data', []),
            total_count=response.get('total_count', 0),
            total_pages=response.get('total_pages', 1),
            page=response.get('page', 1)
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error inesperado durante la búsqueda de subtítulos: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error inesperado durante la búsqueda de subtítulos: {str(e)}"
        )

@router.get("/api/v1/subtitles/languages")
async def get_languages():
    """
    Obtiene la lista de idiomas soportados
    """
    try:
        client = OpenSubtitlesAPI()
        return await client.languages()
    except Exception as e:
        logger.error(f"Error obteniendo idiomas: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo idiomas: {str(e)}"
        )

@router.get("/api/v1/subtitles/formats")
async def get_formats():
    """
    Obtiene la lista de formatos soportados
    """
    try:
        client = OpenSubtitlesAPI()
        return await client.formats()
    except Exception as e:
        logger.error(f"Error obteniendo formatos: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo formatos: {str(e)}"
        )

@router.post("/api/v1/subtitles/download", response_model=DownloadResponseV1)
async def download_subtitle(request: DownloadRequestV1):
    """
    Descarga un subtítulo usando su file_id
    """
    try:
        # Inicializar el cliente de API
        client = OpenSubtitlesAPI()

        # Realizar la petición de descarga
        response = await client.download_subtitle(
            file_id=request.file_id,
            sub_format=request.sub_format
        )
        
        # Convertir la respuesta al modelo DownloadResponseV1
        return DownloadResponseV1(
            link=response.get('link', ''),
            file_name=response.get('file_name', ''),
            requests=response.get('requests', 0),
            remaining=response.get('remaining', 0),
            message=response.get('message', ''),
            reset_time=response.get('reset_time', ''),
            reset_time_utc=response.get('reset_time_utc', '')
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error inesperado durante la descarga del subtítulo: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error inesperado durante la descarga del subtítulo: {str(e)}"
        )