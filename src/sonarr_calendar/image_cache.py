# src/sonarr_calendar/image_cache.py
import os
from pathlib import Path
from datetime import datetime
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Union
import logging
from sonarr_calendar.utils import GracefulInterruptHandler

logger = logging.getLogger(__name__)

def get_poster_url(series_info: Union[Dict, 'SeriesInfo'], preferred_type: Optional[str] = None, base_url: str = '') -> Optional[str]:
    """
    Extract the best available image URL from series information.
    
    If preferred_type is given, that cover type is tried first.
    If not found, falls back to a hardcoded priority: fanart → poster → banner → any image.
    
    Args:
        series_info: SeriesInfo dataclass or dict from API.
        preferred_type: Specific cover type to try first (e.g., 'poster', 'fanart').
        base_url: Sonarr base URL for resolving relative paths.

    Returns:
        URL string or None.
    """
    # Get images list
    if hasattr(series_info, 'images'):
        images = series_info.images
    else:
        images = series_info.get('images', [])

    # If a preferred type is provided, try it first
    if preferred_type:
        for img in images:
            if img.get('coverType') == preferred_type:
                url = img.get('url')
                if url:
                    if url.startswith('http'):
                        return url
                    elif base_url:
                        return f"{base_url.rstrip('/')}/{url.lstrip('/')}"
                    else:
                        return url

    # Fallback priority list (fanart, poster, banner, any)
    priority = ['fanart', 'poster', 'banner']
    for cover_type in priority:
        for img in images:
            if img.get('coverType') == cover_type:
                url = img.get('url')
                if url:
                    if url.startswith('http'):
                        return url
                    elif base_url:
                        return f"{base_url.rstrip('/')}/{url.lstrip('/')}"
                    else:
                        return url

    # Last resort – any image
    for img in images:
        url = img.get('url')
        if url:
            if url.startswith('http'):
                return url
            elif base_url:
                return f"{base_url.rstrip('/')}/{url.lstrip('/')}"
            else:
                return url
    return None


class ImageCache:
    def __init__(self, cache_dir: Path, interrupt_handler: GracefulInterruptHandler, base_url: str = ''):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.handler = interrupt_handler
        self.base_url = base_url

    def _download_one(self, series_id: int, url: str, image_type: str = 'fanart') -> bool:
        if self.handler.check_interrupt():
            return False
        dest = self.cache_dir / f"{series_id}_{image_type}.jpg"
        if dest.exists():
            # Optionally check age – for now, just return True (cached)
            return True
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            dest.write_bytes(resp.content)
            return True
        except Exception as e:
            logger.debug("Failed to download %s: %s", url, e)
            return False

    def download_all_posters(self, all_series: List[Dict]) -> int:
        """Download posters for all series in parallel. Returns number successfully downloaded/verified."""
        tasks = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            for series in all_series:
                series_id = series['id']
                # Use preferred_type='fanart' to get fanart for main cards
                url = get_poster_url(series, preferred_type='fanart', base_url=self.base_url)
                if url:
                    tasks.append(executor.submit(self._download_one, series_id, url, 'fanart'))
            success = 0
            for future in as_completed(tasks):
                if self.handler.check_interrupt():
                    break
                if future.result():
                    success += 1
        return success