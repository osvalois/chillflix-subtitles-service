from abc import ABC, abstractmethod
from fastapi import HTTPException
import aiohttp
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Optional
import asyncio
import logging
from app.services.base import SubtitleServiceBase
from app.models.v1 import DownloadRequestV1, DownloadResponseV1, SearchParams, SearchResponseV1, SubtitleAPIV1

class BSPlayerAPI(SubtitleServiceBase):
    """
    Implementación del servicio BSPlayer para búsqueda y descarga de subtítulos.
    """

    def __init__(self, api_key: str):
        self.subdomains = [1, 2, 3, 4, 5, 6, 7, 8, 101, 102, 103, 104, 105, 106, 107, 108, 109]
        self.headers = {
            'User-Agent': 'BSPlayer/2.x (1022.12362)',
            'Content-Type': 'text/xml; charset=utf-8',
            'Connection': 'close'
        }
        self.token = None
        self.logger = logging.getLogger(__name__)
        self.language_mappings = {
            'eng': 'eng',
            'spa': 'spa',
            'fre': 'fre',
            'ger': 'ger',
            'ita': 'ita',
            'dut': 'dut',
            'por': 'por',
            'rus': 'rus',
            # Agregar más mappings según sea necesario
        }

    def __get_subdomain(self) -> int:
        """Obtiene un subdominio aleatorio basado en el tiempo actual."""
        time_seconds = datetime.now().second
        return self.subdomains[time_seconds % len(self.subdomains)]

    def __get_base_url(self) -> str:
        """Construye la URL base del servicio usando un subdominio aleatorio."""
        return f"http://s{self.__get_subdomain()}.api.bsplayer-subtitles.com/v1.php"

    def __create_soap_request(self, action: str, params: str) -> str:
        """
        Crea una solicitud SOAP con los parámetros especificados.
        """
        url = self.__get_base_url()
        soap_format = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" '
            'xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
            'xmlns:ns1="{url}">'
            '<SOAP-ENV:Body SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
            '<ns1:{action}>{params}</ns1:{action}>'
            '</SOAP-ENV:Body>'
            '</SOAP-ENV:Envelope>'
        )
        return soap_format.format(url=url, action=action, params=params)

    def __map_language_codes(self, languages: str) -> List[str]:
        """
        Mapea los códigos de idioma al formato esperado por BSPlayer.
        """
        lang_codes = []
        for lang in languages.split(','):
            lang = lang.lower().strip()
            if lang in self.language_mappings:
                lang_codes.append(self.language_mappings[lang])
            else:
                lang_codes.append(lang)
        return lang_codes

    async def __login(self) -> Optional[str]:
        """
        Autentica con el servicio BSPlayer.
        Retorna el token de sesión si es exitoso, None en caso contrario.
        """
        try:
            params = (
                '<username></username>'
                '<password></password>'
                '<AppID>BSPlayer v2.72</AppID>'
            )
            
            headers = self.headers.copy()
            headers['SOAPAction'] = f'"{self.__get_base_url()}#logIn"'
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.__get_base_url(),
                    headers=headers,
                    data=self.__create_soap_request('logIn', params),
                    timeout=30
                ) as response:
                    if response.status != 200:
                        self.logger.error(f"Login failed with status {response.status}")
                        return None
                        
                    text = await response.text()
                    try:
                        tree = ET.fromstring(text.strip())
                        result = tree.find('.//return')
                        
                        if result is None or result.find('result').text != '200':
                            self.logger.error("Invalid login response format")
                            return None
                            
                        return result.find('data').text
                    except ET.ParseError as e:
                        self.logger.error(f"Failed to parse login response: {e}")
                        return None
                        
        except Exception as e:
            self.logger.error(f"Login error: {str(e)}")
            return None

    async def __validate_session(self) -> bool:
        """
        Valida y refresca la sesión si es necesario.
        """
        if not self.token:
            self.token = await self.__login()
            if not self.token:
                return False
        return True

    async def search_subtitles(self, params: SearchParams) -> SearchResponseV1:
        """
        Busca subtítulos usando el servicio BSPlayer.
        """
        try:
            if not await self.__validate_session():
                raise HTTPException(
                    status_code=401,
                    detail="Failed to authenticate with BSPlayer service"
                )

            # Convertir y validar códigos de idioma
            lang_codes = self.__map_language_codes(params.languages)
            if not lang_codes:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid language codes provided"
                )

            # Construir parámetros de búsqueda según el tipo
            if params.query:
                search_params = (
                    f'<handle>{self.token}</handle>'
                    f'<movieName>{params.query}</movieName>'
                    f'<year>{params.year if params.year else "0"}</year>'
                    f'<languageId>{",".join(lang_codes)}</languageId>'
                )
                if params.type:
                    search_params += f'<movieType>{params.type}</movieType>'
                if params.imdb_id:
                    search_params += f'<imdbId>{str(params.imdb_id)[2:] if str(params.imdb_id).startswith("tt") else params.imdb_id}</imdbId>'
            else:
                search_params = (
                    f'<handle>{self.token}</handle>'
                    f'<languageId>{",".join(lang_codes)}</languageId>'
                    f'<movieHash>{getattr(params, "hash", "0")}</movieHash>'
                    f'<movieSize>{getattr(params, "filesize", "0")}</movieSize>'
                )

            headers = self.headers.copy()
            headers['SOAPAction'] = f'"{self.__get_base_url()}#searchSubtitles"'

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.__get_base_url(),
                    headers=headers,
                    data=self.__create_soap_request('searchSubtitles', search_params),
                    timeout=30
                ) as response:
                    if response.status != 200:
                        self.logger.error(f"Search failed with status {response.status}")
                        return SearchResponseV1(data=[], total_pages=0, total_count=0, page=1)

                    text = await response.text()
                    self.logger.debug(f"BSPlayer response: {text[:500]}...")  # Log primeros 500 caracteres

                    try:
                        tree = ET.fromstring(text.strip())
                        result = tree.find('.//return')

                        if result is None:
                            self.logger.warning("Empty response from BSPlayer")
                            return SearchResponseV1(data=[], total_pages=0, total_count=0, page=1)

                        status = result.find('result/result')
                        if status is None or status.text != '200':
                            self.logger.warning(f"BSPlayer returned status: {status.text if status else 'None'}")
                            return SearchResponseV1(data=[], total_pages=0, total_count=0, page=1)

                        items = result.findall('data/item')
                        if not items:
                            return SearchResponseV1(data=[], total_pages=0, total_count=0, page=1)

                        subtitles = []
                        for item in items:
                            try:
                                subtitle = {
                                    "id": item.find('subID').text,
                                    "type": "subtitle",
                                    "attributes": {
                                        "subtitle_id": item.find('subID').text,
                                        "language": item.find('subLang').text,
                                        "download_count": int(item.find('subDownloadsCnt').text) if item.find('subDownloadsCnt') is not None else 0,
                                        "new_download_count": 0,
                                        "rating": float(item.find('subRating').text) if item.find('subRating') is not None else 0,
                                        "hearing_impaired": False,
                                        "hd": False,
                                        "fps": 0,
                                        "votes": 0,
                                        "points": 0,
                                        "ratings": float(item.find('subRating').text) if item.find('subRating') is not None else 0,
                                        "from_trusted": True,
                                        "foreign_parts_only": False,
                                        "ai_translated": False,
                                        "machine_translated": False,
                                        "upload_date": datetime.now().isoformat(),
                                        "release": item.find('subName').text,
                                        "comments": "",
                                        "legacy_subtitle_id": int(item.find('subID').text),
                                        "provider": "bsplayer",
                                        "url": item.find('subDownloadLink').text,
                                        "uploader": {
                                            "uploader_id": 0,
                                            "name": "BSPlayer",
                                            "rank": "trusted"
                                        },
                                        "feature_details": {
                                            "feature_id": 0,
                                            "feature_type": params.type or "movie",
                                            "year": params.year or 0,
                                            "title": params.query or "",
                                            "movie_name": params.query or "",
                                            "imdb_id": params.imdb_id or 0,
                                            "tmdb_id": params.tmdb_id or 0
                                        },
                                        "files": [{
                                            "file_id": int(item.find('subID').text),
                                            "cd_number": 1,
                                            "file_name": item.find('subName').text
                                        }]
                                    }
                                }
                                subtitles.append(SubtitleAPIV1(**subtitle))
                            except Exception as e:
                                self.logger.error(f"Error parsing subtitle item: {e}")
                                continue

                        return SearchResponseV1(
                            data=subtitles,
                            total_count=len(subtitles),
                            total_pages=1,
                            page=1
                        )

                    except ET.ParseError as e:
                        self.logger.error(f"Failed to parse search response: {e}")
                        return SearchResponseV1(data=[], total_pages=0, total_count=0, page=1)

        except Exception as e:
            self.logger.error(f"Search error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error searching subtitles: {str(e)}"
            )
        finally:
            if self.token:
                asyncio.create_task(self.__logout())

    async def __logout(self):
        """Cierra la sesión con el servicio BSPlayer."""
        if not self.token:
            return

        try:
            params = f'<handle>{self.token}</handle>'
            headers = self.headers.copy()
            headers['SOAPAction'] = f'"{self.__get_base_url()}#logOut"'
            
            async with aiohttp.ClientSession() as session:
                await session.post(
                    self.__get_base_url(),
                    headers=headers,
                    data=self.__create_soap_request('logOut', params),
                    timeout=10
                )
        except Exception as e:
            self.logger.error(f"Logout error: {str(e)}")
        finally:
            self.token = None

    async def download_subtitle(self, download_request: DownloadRequestV1) -> DownloadResponseV1:
        """Descarga un subtítulo específico del servicio BSPlayer."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    download_request.url,
                    timeout=30
                ) as response:
                    if response.status != 200:
                        raise HTTPException(
                            status_code=response.status,
                            detail="Failed to download subtitle"
                        )

                    content = await response.read()
                    
                    return DownloadResponseV1(
                        link=download_request.url,
                        file_name=download_request.file_name or "subtitle.srt",
                        requests=1,
                        remaining=999,
                        message="Success",
                        reset_time="",
                        reset_time_utc=""
                    )

        except Exception as e:
            self.logger.error(f"Download error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error downloading subtitle: {str(e)}"
            )