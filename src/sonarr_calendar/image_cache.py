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

    def _download_one(self, series_id: int, url: str, image_type: str, session: Optional[requests.Session] = None) -> bool:
        """
        Download one image, using an optional authenticated session.
        """
        if self.handler.check_interrupt():
            logger.warning("Download interrupted for series %d %s", series_id, image_type)
            return False
        dest = self.cache_dir / f"{series_id}_{image_type}.jpg"
        if dest.exists():
            logger.debug("Cached %s for series %d already exists", image_type, series_id)
            return True
        try:
            logger.debug("Downloading %s for series %d from %s", image_type, series_id, url)
            if session:
                resp = session.get(url, timeout=15)
            else:
                resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            dest.write_bytes(resp.content)
            logger.debug("Successfully downloaded %s for series %d", image_type, series_id)
            return True
        except Exception as e:
            logger.warning("Failed to download %s for series %d: %s", image_type, series_id, e)
            return False

    def download_all_posters(self, all_series: List[Dict], session: Optional[requests.Session] = None) -> int:
        """
        Download both fanart and poster for all series in parallel.
        If session is provided, it will be used for authentication.
        Returns number successfully downloaded/verified.
        """
        tasks = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            for series in all_series:
                series_id = series['id']
                # Fanart for main cards
                fanart_url = get_poster_url(series, preferred_type='fanart', base_url=self.base_url)
                if fanart_url:
                    tasks.append(executor.submit(self._download_one, series_id, fanart_url, 'fanart', session))
                else:
                    logger.warning("No fanart URL for series %d", series_id)
                # Poster for completed seasons
                poster_url = get_poster_url(series, preferred_type='poster', base_url=self.base_url)
                if poster_url:
                    tasks.append(executor.submit(self._download_one, series_id, poster_url, 'poster', session))
                else:
                    logger.warning("No poster URL for series %d", series_id)
            success = 0
            for future in as_completed(tasks):
                if self.handler.check_interrupt():
                    break
                if future.result():
                    success += 1
        logger.info(f"Downloaded/verified {success} images total")
        return success

    def get_cached_image_url(self, series_id: int, image_type: str = 'fanart') -> Optional[str]:
        """
        Return the public relative URL path for a cached image of the specified type if the file exists.
        The URL is relative (e.g., '/images/123_fanart.jpg') – your web server
        should serve the cache directory at '/images/'.
        """
        dest = self.cache_dir / f"{series_id}_{image_type}.jpg"
        if dest.exists():
            # Always return a relative path starting with /images/
            return f"/images/{series_id}_{image_type}.jpg"
        return None