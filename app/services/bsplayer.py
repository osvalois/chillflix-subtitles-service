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
    def __init__(self, api_key: str):
        self.subdomains = [1, 2, 3, 4, 5, 6, 7, 8, 101, 102, 103, 104, 105, 106, 107, 108, 109]
        self.headers = {
            'User-Agent': 'BSPlayer/2.x (1022.12362)',
            'Content-Type': 'text/xml; charset=utf-8',
            'Connection': 'close'
        }
        self.token = None
        self.logger = logging.getLogger(__name__)

    def __get_subdomain(self):
        time_seconds = datetime.now().second
        return self.subdomains[time_seconds % len(self.subdomains)]

    def __get_base_url(self):
        return f"http://s{self.__get_subdomain()}.api.bsplayer-subtitles.com/v1.php"

    def __create_soap_request(self, action: str, params: str) -> str:
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

    async def __login(self) -> Optional[str]:
        """Authenticate with BSPlayer service"""
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
                    data=self.__create_soap_request('logIn', params)
                ) as response:
                    if response.status != 200:
                        return None
                        
                    text = await response.text()
                    tree = ET.fromstring(text.strip())
                    result = tree.find('.//return')
                    
                    if result is None or result.find('result').text != '200':
                        return None
                        
                    return result.find('data').text
        except Exception as e:
            self.logger.error(f"Login error: {str(e)}")
            return None

    async def search_subtitles(self, params: SearchParams) -> SearchResponseV1:
        """Search for subtitles using BSPlayer service"""
        try:
            if not self.token:
                self.token = await self.__login()
                if not self.token:
                    raise HTTPException(
                        status_code=401,
                        detail="Failed to authenticate with BSPlayer service"
                    )

            search_params = (
                f'<handle>{self.token}</handle>'
                f'<movieHash>{params.hash or "0"}</movieHash>'
                f'<movieSize>{params.filesize or "0"}</movieSize>'
                f'<languageId>{params.languages}</languageId>'
                f'<imdbId>{params.imdb_id[2:] if params.imdb_id else "0"}</imdbId>'
            )

            headers = self.headers.copy()
            headers['SOAPAction'] = f'"{self.__get_base_url()}#searchSubtitles"'

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.__get_base_url(),
                    headers=headers,
                    data=self.__create_soap_request('searchSubtitles', search_params)
                ) as response:
                    if response.status != 200:
                        raise HTTPException(
                            status_code=response.status,
                            detail="Failed to search subtitles"
                        )

                    text = await response.text()
                    tree = ET.fromstring(text.strip())
                    result = tree.find('.//return')

                    if result is None or result.find('result/result').text != '200':
                        return SearchResponseV1(data=[], total_pages=0, total_count=0, page=1)

                    subtitles = []
                    for item in result.findall('data/item'):
                        subtitle = {
                            "id": item.find('subID').text,
                            "type": "subtitle",
                            "attributes": {
                                "subtitle_id": item.find('subID').text,
                                "language": item.find('subLang').text,
                                "download_count": int(item.find('subDownloadsCnt').text),
                                "rating": float(item.find('subRating').text) if item.find('subRating').text else 0,
                                "hearing_impaired": False,
                                "hd": False,
                                "fps": 0,
                                "name": item.find('subName').text,
                                "download_link": item.find('subDownloadLink').text,
                                "release": item.find('subName').text
                            }
                        }
                        subtitles.append(SubtitleAPIV1(**subtitle))

                    return SearchResponseV1(
                        data=subtitles,
                        total_count=len(subtitles),
                        total_pages=1,
                        page=1
                    )

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
        """Logout from BSPlayer service"""
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
                    data=self.__create_soap_request('logOut', params)
                )
        except Exception as e:
            self.logger.error(f"Logout error: {str(e)}")
        finally:
            self.token = None

    async def download_subtitle(self, download_request: DownloadRequestV1) -> DownloadResponseV1:
        """Download subtitle from BSPlayer service"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(download_request.url) as response:
                    if response.status != 200:
                        raise HTTPException(
                            status_code=response.status,
                            detail="Failed to download subtitle"
                        )

                    return DownloadResponseV1(
                        link=download_request.url,
                        file_name=download_request.file_name,
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