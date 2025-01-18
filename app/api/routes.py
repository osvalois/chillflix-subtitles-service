# app/api/routes.py
from fastapi import APIRouter, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import logging
from typing import Optional
from app.models.v1 import DownloadRequestV1, DownloadResponseV1, SearchResponseV1
from app.services.opensubtitles import OpenSubtitlesAPI
from app.services.subdl import SubDLAPI
from app.services.subsource import SubSourceAPI

# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Router para la API de subtítulos
router = APIRouter()

# Configuración de CORS
origins = [
    "http://localhost:5173/movie/346",
    "https://chillflix.win"
]

# Agregar middleware de CORS al router
router.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mapa de proveedores de subtítulos
subtitle_providers = {
    "opensubtitles": OpenSubtitlesAPI,
    "subdl": lambda: SubDLAPI("_fwrdNVkOW19Ni1xuYG_mfghv45o_Key"),
    "subsource": lambda: SubSourceAPI()
}

@router.get("/api/v1/subtitles", response_model=SearchResponseV1)
async def search_subtitles(
    imdb_id: str,
    provider: str = Query("opensubtitles", enum=["opensubtitles", "subdl", "subsource"]),
    type: Optional[str] = Query("movie", enum=["movie", "tv"]),
    languages: Optional[str] = "en",
    season_number: Optional[int] = None,
    episode_number: Optional[int] = None
):
    """
    Busca subtítulos usando la API del proveedor especificado
    """
    try:
        # Inicializar el cliente del proveedor seleccionado
        client = subtitle_providers[provider]()

        # Realizar la búsqueda según el proveedor
        if provider == "opensubtitles":
            response = await client.search_subtitles(imdb_id)
        elif provider == "subsource":
            response = await client.search_subtitles(
                imdb_id=imdb_id,
                type=type,
                languages=languages,
                season_number=season_number,
                episode_number=episode_number
            )
        else:  # subdl
            response = await client.search_subtitles(
                imdb_id=imdb_id,
                type=type,
                languages=languages,
                season_number=season_number,
                episode_number=episode_number
            )
        
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
async def get_languages(
    provider: str = Query("opensubtitles", enum=["opensubtitles", "subdl", "subsource"])
):
    """
    Obtiene la lista de idiomas soportados por el proveedor
    """
    try:
        client = subtitle_providers[provider]()
        return await client.languages()
    except Exception as e:
        logger.error(f"Error obteniendo idiomas: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo idiomas: {str(e)}"
        )

@router.get("/api/v1/subtitles/formats")
async def get_formats(
    provider: str = Query("opensubtitles", enum=["opensubtitles", "subdl", "subsource"])
):
    """
    Obtiene la lista de formatos soportados por el proveedor
    """
    try:
        client = subtitle_providers[provider]()
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
    Descarga un subtítulo usando su file_id o URL según el proveedor
    """
    try:
        provider = None
        # Determinar el proveedor basado en la estructura de la solicitud
        if request.url:
            if "subsource" in request.url:
                provider = "subsource"
            else:
                provider = "subdl"
        else:
            provider = "opensubtitles"

        client = subtitle_providers[provider]()

        # Realizar la petición de descarga según el proveedor
        if provider == "subsource":
            response = await client.download_subtitle(request.url)
        elif provider == "subdl":
            response = await client.download_subtitle(request.url)
        else:  # opensubtitles
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