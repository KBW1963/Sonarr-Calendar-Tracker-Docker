# src/sonarr_calendar/api_client.py
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta, timezone
from sonarr_calendar.utils import GracefulInterruptHandler, DateRange

logger = logging.getLogger(__name__)

class SonarrClient:
    def __init__(self, base_url: str, api_key: str, interrupt_handler: GracefulInterruptHandler):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.handler = interrupt_handler
        self.session = requests.Session()
        self.session.headers.update({'X-Api-Key': api_key})
        # Retry strategy
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

        # Cache for series episodes (key: series_id, value: list of episodes)
        self._episodes_cache = {}

    def _get(self, path: str, params: Optional[Dict] = None, timeout: int = 30) -> Optional[Dict]:
        if self.handler.check_interrupt():
            raise KeyboardInterrupt
        url = f"{self.base_url}{path}"
        try:
            resp = self.session.get(url, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            logger.error("API request failed: %s", e)
            return None

    def get_calendar(self, days_past: int, days_future: int) -> Tuple[List[Dict], DateRange]:
        today = datetime.now(timezone.utc)
        start = today - timedelta(days=days_past)
        end = today + timedelta(days=days_future)
        params = {
            'start': start.date().isoformat(),
            'end': end.date().isoformat(),
            'includeSeries': 'true',
            'includeEpisodeFile': 'true',
            'unmonitored': 'true'
        }
        data = self._get('/api/v3/calendar', params=params)
        if data is None:
            return [], DateRange(start.date(), end.date())
        # Filter again to be safe
        filtered = []
        start_date = start.date()
        end_date = end.date()
        for ep in data:
            air = ep.get('airDate')
            if air:
                air_date = datetime.fromisoformat(air).date()
                if start_date <= air_date <= end_date:
                    filtered.append(ep)
        return filtered, DateRange(start_date, end_date)

    def get_all_series(self) -> List[Dict]:
        data = self._get('/api/v3/series')
        return data if data is not None else []

    def get_series(self, series_id: int) -> Optional[Dict]:
        return self._get(f'/api/v3/series/{series_id}')

    def get_episode_file(self, file_id: int) -> Optional[Dict]:
        return self._get(f'/api/v3/episodefile/{file_id}')

    def get_series_episodes(self, series_id: int) -> List[Dict]:
        """
        Fetch all episodes for a given series.
        Uses a simple in‑memory cache to avoid repeated calls for the same series within a run.
        """
        if series_id in self._episodes_cache:
            logger.debug(f"Using cached episodes for series {series_id}")
            return self._episodes_cache[series_id]

        if self.handler.check_interrupt():
            raise KeyboardInterrupt
        try:
            response = self.session.get(
                f"{self.base_url}/api/v3/episode",
                params={"seriesId": series_id},
                timeout=30
            )
            response.raise_for_status()
            episodes = response.json()
            self._episodes_cache[series_id] = episodes
            return episodes
        except Exception as e:
            logger.error(f"Failed to fetch episodes for series {series_id}: {e}")
            return []

    def close(self):
        self.session.close()