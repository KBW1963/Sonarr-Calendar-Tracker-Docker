# src/sonarr_calendar/models.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import date, datetime, timezone
from collections import defaultdict
import logging

from sonarr_calendar.image_cache import get_poster_url
from sonarr_calendar.utils import get_progress_bar_color, days_until

logger = logging.getLogger(__name__)

# ============================================================================
# Data models
# ============================================================================

@dataclass
class SeriesInfo:
    id: int
    title: str
    year: Optional[int]
    network: Optional[str]
    runtime: Optional[int]
    genres: List[str]
    rating: float
    images: List[Dict[str, str]]
    seasons: List[Dict[str, Any]]
    season_count: int
    episode_count: int
    episode_file_count: int
    season_episode_counts: Dict[int, int] = field(default_factory=dict)

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'SeriesInfo':
        # First try top‑level fields, then fall back to statistics
        episode_count = data.get('episodeCount')
        if episode_count is None:
            episode_count = data.get('statistics', {}).get('episodeCount', 0)

        episode_file_count = data.get('episodeFileCount')
        if episode_file_count is None:
            episode_file_count = data.get('statistics', {}).get('episodeFileCount', 0)

        # Season episode counts for finale detection (from seasons list)
        season_ep_counts = {}
        for season in data.get('seasons', []):
            sn = season.get('seasonNumber')
            if sn and sn >= 0:
                stats = season.get('statistics', {})
                total = stats.get('totalEpisodeCount', 0)
                if total:
                    season_ep_counts[sn] = total

        return cls(
            id=data['id'],
            title=data['title'],
            year=data.get('year'),
            network=data.get('network'),
            runtime=data.get('runtime'),
            genres=data.get('genres', []),
            rating=data.get('ratings', {}).get('value', 0.0),
            images=data.get('images', []),
            seasons=data.get('seasons', []),
            season_count=data.get('seasonCount', 0),
            episode_count=episode_count,
            episode_file_count=episode_file_count,
            season_episode_counts=season_ep_counts
        )

@dataclass
class Episode:
    series_id: int
    season_number: int
    episode_number: int
    title: str
    air_date: Optional[date]
    has_file: bool
    monitored: bool
    overview: Optional[str]
    episode_type: Optional[str] = None
    # Additional computed fields for template
    days_until: int = 0
    formatted_season_episode: str = ""
    single_episode: bool = True
    full_title: str = ""
    individual_episode_count: int = 1
    titles_display: str = ""
    full_tooltip: str = ""

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'Episode':
        air_str = data.get('airDate')
        air_date = datetime.strptime(air_str, "%Y-%m-%d").date() if air_str else None
        days = days_until(air_date) if air_date else 999
        season = data.get('seasonNumber', 0)
        episode = data.get('episodeNumber', 0)
        formatted = f"S{season:02d}E{episode:02d}" if season and episode else ""
        title_str = data.get('title', 'TBA')
        return cls(
            series_id=data['seriesId'],
            season_number=season,
            episode_number=episode,
            title=title_str,
            air_date=air_date,
            has_file=data.get('hasFile', False),
            monitored=data.get('monitored', False),
            overview=data.get('overview', ''),
            episode_type=data.get('episodeType'),
            days_until=days,
            formatted_season_episode=formatted,
            full_title=title_str,
            titles_display=title_str,
            full_tooltip=title_str
        )

@dataclass
class ProcessedShow:
    # Non‑default fields first (in the order they appear in the __init__)
    series_id: int
    title: str
    year: Optional[int]
    network: Optional[str]
    runtime: Optional[int]
    genres: List[str]
    rating: float
    poster_url: Optional[str]                # primary image (fanart, based on config)
    progress_percentage: float
    progress_color: str
    total_episodes: int
    downloaded_episodes: int
    monitored_seasons: int
    unmonitored_seasons: int
    total_seasons: int
    current_season: int
    current_season_progress: float
    current_season_complete: bool
    current_season_episodes: int
    current_season_downloaded: int
    season_episode_counts: Dict[int, int]

    # Fields with default values (must come after all non‑default fields)
    poster_url_poster: Optional[str] = None  # poster image for completed seasons section
    episodes_in_range: List[Episode] = field(default_factory=list)
    date_range_episodes: int = 0
    date_range_downloaded: int = 0
    date_range_percentage: float = 0.0
    date_range_color: str = "#F44336"

# ============================================================================
# Helper functions
# ============================================================================

def calculate_progress(series: SeriesInfo) -> Tuple[
    float, str, int, int, int, float, bool, int, int, int
]:
    """
    Calculate overall progress and related stats.

    Returns:
        overall_percentage (float)
        color (str)
        monitored_seasons (int)
        unmonitored_seasons (int)
        total_seasons (int)
        current_season_progress (float)
        current_season_complete (bool)
        current_season_episodes (int)
        current_season_downloaded (int)
        current_season_number (int)
    """
    total_ep = series.episode_count
    downloaded = series.episode_file_count

    monitored = 0
    unmonitored = 0
    for s in series.seasons:
        sn = s.get('seasonNumber', 0)
        if sn < 0:
            continue
        if s.get('monitored'):
            monitored += 1
        else:
            unmonitored += 1

    # Find current season (largest monitored season with episodes)
    current_season = 0
    for s in series.seasons:
        sn = s.get('seasonNumber', 0)
        if sn > current_season and s.get('monitored') and s.get('statistics', {}).get('totalEpisodeCount', 0) > 0:
            current_season = sn

    # Progress for current season
    current_season_total = 0
    current_season_downloaded = 0
    for s in series.seasons:
        if s.get('seasonNumber') == current_season:
            stats = s.get('statistics', {})
            current_season_total = stats.get('totalEpisodeCount', 0)
            current_season_downloaded = stats.get('episodeFileCount', 0)
            break
    current_progress = (current_season_downloaded / current_season_total * 100) if current_season_total else 0
    current_complete = current_progress >= 100

    overall = (downloaded / total_ep * 100) if total_ep else 0

    if overall >= 100:
        color = "#4CAF50"
    elif overall >= 75:
        color = "#8BC34A"
    elif overall >= 50:
        color = "#FFC107"
    elif overall >= 25:
        color = "#FF9800"
    elif overall > 0:
        color = "#FF5722"
    else:
        color = "#F44336"

    return (
        overall, color,
        monitored, unmonitored, series.season_count,
        current_progress, current_complete,
        current_season_total, current_season_downloaded,
        current_season
    )

def process_calendar_data(
    episodes: List[Dict],
    all_series: List[Dict],
    date_range,
    sonarr_client,
    config
) -> List[ProcessedShow]:
    """Group episodes by series, compute stats, and return list of ProcessedShow."""
    series_map = {s['id']: SeriesInfo.from_api(s) for s in all_series}
    ep_by_series = defaultdict(list)
    for ep in episodes:
        ep_by_series[ep['seriesId']].append(Episode.from_api(ep))

    processed = []
    for series_id, eps in ep_by_series.items():
        series = series_map.get(series_id)
        if not series:
            logger.warning(f"Series {series_id} not found, skipping")
            continue

        # Primary image (fanart) – will be cached
        poster_url = get_poster_url(series, preferred_type=config.image_quality, base_url=config.sonarr_url)
        # Poster image (for completed seasons) – not cached, used directly from Sonarr
        poster_url_poster = get_poster_url(series, preferred_type='poster', base_url=config.sonarr_url)

        (overall, color,
         monitored, unmonitored, tot_seasons,
         cur_prog, cur_comp,
         cur_eps, cur_down,
         cur_cur) = calculate_progress(series)

        in_range = [e for e in eps if e.air_date and date_range.start <= e.air_date <= date_range.end]
        range_downloaded = sum(1 for e in in_range if e.has_file)
        range_percent = (range_downloaded / len(in_range) * 100) if in_range else 0
        range_color = get_progress_bar_color(range_percent)

        processed.append(ProcessedShow(
            series_id=series_id,
            title=series.title,
            year=series.year,
            network=series.network,
            runtime=series.runtime,
            genres=series.genres,
            rating=series.rating,
            poster_url=poster_url,
            progress_percentage=overall,
            progress_color=color,
            total_episodes=series.episode_count,
            downloaded_episodes=series.episode_file_count,
            monitored_seasons=monitored,
            unmonitored_seasons=unmonitored,
            total_seasons=tot_seasons,
            current_season=cur_cur,
            current_season_progress=cur_prog,
            current_season_complete=cur_comp,
            current_season_episodes=cur_eps,
            current_season_downloaded=cur_down,
            season_episode_counts=series.season_episode_counts,
            poster_url_poster=poster_url_poster,
            episodes_in_range=in_range,
            date_range_episodes=len(in_range),
            date_range_downloaded=range_downloaded,
            date_range_percentage=range_percent,
            date_range_color=range_color
        ))

    processed.sort(key=lambda x: (-x.date_range_percentage, x.title))
    return processed

def calculate_overall_statistics(shows: List[ProcessedShow], date_range) -> Dict[str, Any]:
    """Calculate overall statistics across all series."""
    total_series = len(shows)

    total_episodes_all = sum(s.total_episodes for s in shows)
    total_downloaded_all = sum(s.downloaded_episodes for s in shows)
    total_seasons_all = sum(s.total_seasons for s in shows)
    monitored_seasons = sum(s.monitored_seasons for s in shows)
    unmonitored_seasons = sum(s.unmonitored_seasons for s in shows)

    total_episodes_in_range = sum(s.date_range_episodes for s in shows)
    total_downloaded_in_range = sum(s.date_range_downloaded for s in shows)

    shows_with_episodes = sum(1 for s in shows if s.date_range_episodes > 0)
    shows_complete = sum(1 for s in shows if s.current_season_complete)

    overall_progress = (total_downloaded_all / total_episodes_all * 100) if total_episodes_all else 0
    overall_date_range_progress = (total_downloaded_in_range / total_episodes_in_range * 100) if total_episodes_in_range else 0

    shows_high_progress = sum(1 for s in shows if 75 <= s.progress_percentage < 100)
    shows_medium_progress = sum(1 for s in shows if 25 <= s.progress_percentage < 75)
    shows_low_progress = sum(1 for s in shows if 0 < s.progress_percentage < 25)
    shows_not_started = sum(1 for s in shows if s.progress_percentage == 0)

    return {
        'total_series': total_series,
        'total_episodes_all': total_episodes_all,
        'total_downloaded_all': total_downloaded_all,
        'total_seasons_all': total_seasons_all,
        'monitored_seasons': monitored_seasons,
        'unmonitored_seasons': unmonitored_seasons,
        'episodes_in_range': total_episodes_in_range,
        'downloaded_in_range': total_downloaded_in_range,
        'shows_with_episodes': shows_with_episodes,
        'shows_complete': shows_complete,
        'shows_high_progress': shows_high_progress,
        'shows_medium_progress': shows_medium_progress,
        'shows_low_progress': shows_low_progress,
        'shows_not_started': shows_not_started,
        'overall_progress': overall_progress,
        'overall_date_range_progress': overall_date_range_progress,
        'date_range': date_range
    }

def calculate_completed_seasons_in_range(
    shows: List[ProcessedShow],
    episodes: List[Dict],
    start_date: date,
    end_date: date,
    sonarr_client
) -> List[Dict]:
    """Find shows that completed their current season within the date range."""
    completed = []
    # DEBUG: The following lines are commented out for normal operation.
    # Uncomment them to see detailed information about why each show is (or isn't) added.
    # logger.info("=== DEBUG: calculate_completed_seasons_in_range ===")
    # logger.info(f"Date range: {start_date} to {end_date}")
    for show in shows:
        # logger.info(f"\nChecking show: {show.title} (ID: {show.series_id})")
        # logger.info(f"  current_season: {show.current_season}")
        # logger.info(f"  current_season_complete: {show.current_season_complete}")
        # logger.info(f"  current_season_episodes: {show.current_season_episodes}")
        # logger.info(f"  episodes_in_range count: {len(show.episodes_in_range)}")
        # for idx, ep in enumerate(show.episodes_in_range):
        #     logger.info(f"    Ep {idx+1}: S{ep.season_number:02d}E{ep.episode_number:02d} - {ep.air_date} - {ep.title}")

        if not show.current_season_complete:
            # logger.info("  --> Skipping because season not complete")
            continue

        season_eps = [e for e in show.episodes_in_range if e.season_number == show.current_season]
        # logger.info(f"  Season episodes in range: {len(season_eps)}")
        if season_eps:
            latest = max(season_eps, key=lambda e: e.air_date or date.min)
            # logger.info(f"  Latest episode air date: {latest.air_date}")
            if latest.air_date and start_date <= latest.air_date <= end_date:
                # logger.info(f"  --> Within range! Adding to completed seasons.")
                completed.append({
                    'title': show.title,
                    'series_id': show.series_id,
                    'season': show.current_season,
                    'completion_date': latest.air_date,
                    'total_episodes': show.current_season_episodes,
                    # Use poster image for this section (fallback to fanart if poster missing)
                    'poster_url': show.poster_url_poster or show.poster_url
                })
            # else:
            #     logger.info(f"  --> Not within range (air date {latest.air_date})")
        else:
            # logger.info("  --> No season episodes in range. Attempting fallback: fetching all episodes.")
            all_episodes = sonarr_client.get_series_episodes(show.series_id)
            season_eps_all = [e for e in all_episodes if e.get('seasonNumber') == show.current_season and e.get('airDate')]
            if not season_eps_all:
                # logger.info("  --> No episodes found for this season at all.")
                continue
            season_eps_all.sort(key=lambda e: e.get('episodeNumber', 0))
            last_ep = season_eps_all[-1]
            last_air_date = datetime.strptime(last_ep['airDate'], "%Y-%m-%d").date()
            # logger.info(f"  Last episode from series API: S{show.current_season}E{last_ep['episodeNumber']} - air date {last_air_date}")
            if start_date <= last_air_date <= end_date:
                # logger.info(f"  --> Within range! Adding to completed seasons (fallback).")
                completed.append({
                    'title': show.title,
                    'series_id': show.series_id,
                    'season': show.current_season,
                    'completion_date': last_air_date,
                    'total_episodes': show.current_season_episodes,
                    # Use poster image for this section (fallback to fanart if poster missing)
                    'poster_url': show.poster_url_poster or show.poster_url
                })
            # else:
            #     logger.info(f"  --> Not within range (air date {last_air_date})")

    # logger.info(f"\nTotal completed seasons found: {len(completed)}")
    return completed