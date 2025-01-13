from typing import Optional, Dict, List
from venv import logger
import aiohttp
import re
from app.services.base import SubtitleServiceBase
from app.models.v1 import SearchParams, SearchResponseV1, SubtitleAttributes, SubtitleAPIV1, DownloadRequestV1, DownloadResponseV1

class Addic7edAPI(SubtitleServiceBase):
    BASE_URL = 'https://www.addic7ed.com'
    
    def __init__(self, api_key: str):
        self.api_key = api_key  # Remove super().__init__() call since SubtitleServiceBase is ABC
        
    async def search_subtitles(self, params: SearchParams) -> SearchResponseV1:
        """
        Search for subtitles on Addic7ed.
        Only supports TV shows searches.
        """
        if not params.type or params.type.lower() != "episode":
            return SearchResponseV1(data=[], total_count=0, total_pages=1, page=1)
            
        if not all([params.query, params.season_number, params.episode_number]):
            return SearchResponseV1(data=[], total_count=0, total_pages=1, page=1)
            
        try:
            async with aiohttp.ClientSession() as session:
                # Format show title and build URL
                show_title = params.query.replace(' ', '_')
                url = f"{self.BASE_URL}/ajax_loadShow.php"
                
                # Parse language codes
                languages = params.languages.split(',')
                lang_ids = self._get_language_ids(languages)
                
                search_params = {
                    'show': show_title,
                    'season': str(params.season_number),
                    'langs': f"|{'|'.join(lang_ids)}|"
                }
                
                headers = {
                    'Referer': f"{self.BASE_URL}/serie/{show_title}/{params.season_number}/{params.episode_number}",
                    'User-Agent': 'Mozilla/5.0'  # Added User-Agent header
                }
                
                async with session.get(url, params=search_params, headers=headers) as response:
                    if response.status != 200:
                        return SearchResponseV1(data=[], total_count=0, total_pages=1, page=1)
                        
                    content = await response.text()
                    subtitles = self._parse_search_results(
                        content, 
                        params.season_number,
                        params.episode_number,
                        languages
                    )
                    
                    return SearchResponseV1(
                        data=subtitles,
                        total_count=len(subtitles),
                        total_pages=1,
                        page=1
                    )
        except Exception as e:
            logger.error(f"Addic7ed search error: {str(e)}")
            return SearchResponseV1(data=[], total_count=0, total_pages=1, page=1)
    def _get_language_ids(self, languages: List[str]) -> List[str]:
        """Map ISO language codes to Addic7ed language IDs"""
        language_map = {
            'en': '1',   # English
            'es': '5',   # Spanish
            'fr': '8',   # French
            'it': '7',   # Italian
            'pt': '10',  # Portuguese
            'de': '11',  # German
            # Add more mappings as needed
        }
        return [language_map.get(lang.lower(), '1') for lang in languages]
        
    def _parse_search_results(
        self, 
        html_content: str, 
        season: int, 
        episode: int,
        languages: List[str]
    ) -> List[SubtitleAPIV1]:
        results = []
        
        # Pattern to extract subtitle information
        pattern = (
            r'<td>(\d+)</td>' +                    # Season
            r'<td>(\d+)</td>' +                    # Episode
            r'<td>.*?</td>' +                      # Language number
            r'<td>(.*?)</td>' +                    # Language name
            r'<td.*?>(.*?)</td>' +                 # Version/Release
            r'\s*?<td.*?>.*?</td>' +              # Completed
            r'<td.*?>(.*?)</td>' +                 # HI
            r'<td.*?>.*?</td>' +                  # Corrected
            r'<td.*?>.*?</td>' +                  # HD
            r'<td.*?>.*?href=\"(.*?)\".*?</td>'   # Download link
        )
        
        matches = re.finditer(pattern, html_content, re.DOTALL)
        
        for match in matches:
            season_num = int(match.group(1))
            episode_num = int(match.group(2))
            
            if season_num != season or episode_num != episode:
                continue
                
            language = match.group(3).strip()
            if not any(lang.lower() in language.lower() for lang in languages):
                continue
                
            version = match.group(4).strip()
            hearing_impaired = match.group(5).strip() != ''
            download_link = self.BASE_URL + match.group(6)
            
            subtitle = SubtitleAPIV1(
                id=download_link,
                type="subtitle",
                attributes=SubtitleAttributes(
                    provider="addic7ed",
                    language=language[:2].lower(),
                    download_count=0,
                    hearing_impaired=hearing_impaired,
                    subtitle_id=download_link,
                    format="srt",
                    fps=0.0,
                    votes=0,
                    points=0,
                    ratings=0.0,
                    download_link=download_link,
                    release=version
                )
            )
            results.append(subtitle)
            
        return results
        
    async def download_subtitle(self, download_request: DownloadRequestV1) -> DownloadResponseV1:
        """Download subtitle from Addic7ed"""
        async with aiohttp.ClientSession() as session:
            headers = {
                'Referer': self.BASE_URL
            }
            
            async with session.get(download_request.subtitle_id, headers=headers) as response:
                if response.status != 200:
                    raise Exception("Failed to download subtitle")
                    
                content = await response.read()
                
                return DownloadResponseV1(
                    link=download_request.subtitle_id,
                    file_name=f"subtitle_{download_request.subtitle_id.split('/')[-1]}.srt",
                    content=content.decode('utf-8')
                )