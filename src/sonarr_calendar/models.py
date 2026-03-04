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
# Constants for display formatting
# ============================================================================
MAX_EPISODE_TITLE_LENGTH = 25
MAX_MULTI_EPISODE_DISPLAY = 2
MAX_EPISODE_LIST_LENGTH = 15

# ============================================================================
# Helper functions for formatting multi‑episode displays
# ============================================================================

def truncate_text(text, max_length):
    if not text:
        return text
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def format_multi_episode_display(episodes_info):
    episode_count = len(episodes_info['episodes'])
    season_num = episodes_info['seasons'][0] if episodes_info['seasons'] else 0

    if len(episodes_info['episodes']) == 1:
        episode_range = f"E{episodes_info['episodes'][0]:02d}"
    else:
        ep_list = sorted(episodes_info['episodes'])
        consecutive = all(ep_list[i] + 1 == ep_list[i + 1] for i in range(len(ep_list) - 1))
        if consecutive and len(ep_list) > 1:
            episode_range = f"E{ep_list[0]:02d}-E{ep_list[-1]:02d}"
        else:
            if len(ep_list) > 3:
                first_few = [f"E{e:02d}" for e in ep_list[:2]]
                episode_range = f"{', '.join(first_few)} +{len(ep_list)-2} more"
            else:
                episode_range = f"{', '.join([f'E{e:02d}' for e in ep_list])}"

    formatted_number = f"S{season_num:02d} {episode_range}"

    titles = episodes_info.get('titles', [])
    truncated_titles = episodes_info.get('truncated_titles', [])

    if episode_count == 1:
        titles_display = truncated_titles[0] if truncated_titles else "Episode"
    else:
        if episode_count <= MAX_MULTI_EPISODE_DISPLAY:
            titles_display = f"{episode_count} Episodes: {', '.join(truncated_titles[:MAX_MULTI_EPISODE_DISPLAY])}"
        else:
            titles_display = f"{episode_count} Episodes: {', '.join(truncated_titles[:MAX_MULTI_EPISODE_DISPLAY])} +{episode_count - MAX_MULTI_EPISODE_DISPLAY} more"

    if len(titles_display) > MAX_EPISODE_LIST_LENGTH:
        titles_display = titles_display[:MAX_EPISODE_LIST_LENGTH-3] + "..."

    full_tooltip = f"Season {season_num}\n"
    for i, (ep_num, title) in enumerate(zip(episodes_info['episodes'], titles), 1):
        full_tooltip += f"E{ep_num:02d}: {title}\n"

    return {
        'formatted_number': formatted_number,
        'titles_display': titles_display,
        'full_tooltip': full_tooltip.strip(),
        'episode_count': episode_count
    }

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
        episode_count = data.get('episodeCount')
        if episode_count is None:
            episode_count = data.get('statistics', {}).get('episodeCount', 0)

        episode_file_count = data.get('episodeFileCount')
        if episode_file_count is None:
            episode_file_count = data.get('statistics', {}).get('episodeFileCount', 0)

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
        ep_type = data.get('episodeType')
        return cls(
            series_id=data['seriesId'],
            season_number=season,
            episode_number=episode,
            title=title_str,
            air_date=air_date,
            has_file=data.get('hasFile', False),
            monitored=data.get('monitored', False),
            overview=data.get('overview', ''),
            episode_type=ep_type,
            days_until=days,
            formatted_season_episode=formatted,
            full_title=title_str,
            titles_display=title_str,
            full_tooltip=title_str,
            single_episode=True,
            individual_episode_count=1
        )

@dataclass
class ProcessedShow:
    series_id: int
    title: str
    year: Optional[int]
    network: Optional[str]
    runtime: Optional[int]
    genres: List[str]
    rating: float
    poster_url: Optional[str]
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
    poster_url_poster: Optional[str] = None
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
    total_ep = series.episode_count
    downloaded = series.episode_file_count

    monitored = 0
    unmonitored = 0
    for s in series.seasons:
        sn = s.get('seasonNumber', 0)
        if sn <= 0:                     # skip season 0 (specials) and negative
            continue
        if s.get('monitored'):
            monitored += 1
        else:
            unmonitored += 1

    current_season = 0
    for s in series.seasons:
        sn = s.get('seasonNumber', 0)
        if sn > current_season and s.get('monitored') and s.get('statistics', {}).get('totalEpisodeCount', 0) > 0:
            current_season = sn

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
    series_map = {s['id']: SeriesInfo.from_api(s) for s in all_series}

    # First, convert all episodes to Episode objects and group by series and date
    raw_episodes_by_series_and_date = defaultdict(lambda: defaultdict(list))
    for ep in episodes:
        episode_obj = Episode.from_api(ep)
        series_id = ep['seriesId']
        air_date = episode_obj.air_date
        if air_date:
            raw_episodes_by_series_and_date[series_id][air_date].append(episode_obj)

    processed = []
    for series_id, date_dict in raw_episodes_by_series_and_date.items():
        series = series_map.get(series_id)
        if not series:
            logger.warning(f"Series {series_id} not found, skipping")
            continue

        # Group episodes by date, creating multi‑episode objects when needed
        grouped_episodes = []
        total_individual_episodes = 0

        # Process dates in order (optional)
        for air_date, ep_list in sorted(date_dict.items()):
            ep_list.sort(key=lambda x: (x.season_number, x.episode_number))
            if len(ep_list) == 1:
                grouped_episodes.append(ep_list[0])
                total_individual_episodes += 1
            else:
                # Multiple episodes on same date – create a grouped episode object
                titles = [ep.title for ep in ep_list]
                truncated_titles = [truncate_text(ep.title, MAX_EPISODE_TITLE_LENGTH) for ep in ep_list]
                seasons = list(set(ep.season_number for ep in ep_list))
                episodes_nums = [ep.episode_number for ep in ep_list]

                episodes_info = {
                    'titles': titles,
                    'truncated_titles': truncated_titles,
                    'seasons': seasons,
                    'episodes': episodes_nums,
                    'episode_count': len(ep_list)
                }

                formatted = format_multi_episode_display(episodes_info)

                # Determine combined status: has_file if all have file, monitored if any monitored
                all_have_file = all(ep.has_file for ep in ep_list)
                any_monitored = any(ep.monitored for ep in ep_list)
                badge_type = ep_list[0].episode_type if ep_list else None

                first_ep = ep_list[0]
                grouped_ep = Episode(
                    series_id=first_ep.series_id,
                    season_number=seasons[0] if seasons else 0,
                    episode_number=episodes_nums[0],  # not used for display
                    title=first_ep.title,  # not used for display
                    air_date=air_date,
                    has_file=all_have_file,
                    monitored=any_monitored,
                    overview="",  # no overview for group
                    episode_type=badge_type,
                    single_episode=False,
                    formatted_season_episode=formatted['formatted_number'],
                    titles_display=formatted['titles_display'],
                    full_tooltip=formatted['full_tooltip'],
                    individual_episode_count=len(ep_list),
                    days_until=first_ep.days_until,
                    full_title=first_ep.full_title
                )
                grouped_episodes.append(grouped_ep)
                total_individual_episodes += len(ep_list)

        # Now we have grouped_episodes list for this series
        # Filter those within the date range (they already are, but ensure)
        in_range = [ep for ep in grouped_episodes if ep.air_date and date_range.start <= ep.air_date <= date_range.end]

        # Debug: log grouping results (uncomment if needed)
        # logger.info(f"Series {series_id}: {len(grouped_episodes)} grouped items, {len(in_range)} in range, total indiv episodes {total_individual_episodes}")

        # Calculate progress for the series
        poster_url = get_poster_url(series, config.image_quality, config.sonarr_url)
        poster_url_poster = get_poster_url(series, 'poster', config.sonarr_url)

        (overall, color,
         monitored, unmonitored, _,
         cur_prog, cur_comp,
         cur_eps, cur_down,
         cur_cur) = calculate_progress(series)

        # Count downloaded episodes in range (respecting multi‑episode counts)
        range_downloaded = 0
        for ep in in_range:
            if ep.has_file:
                range_downloaded += ep.individual_episode_count

        range_percent = (range_downloaded / total_individual_episodes * 100) if total_individual_episodes > 0 else 0
        range_color = get_progress_bar_color(range_percent)

        # Count only regular seasons (season number > 0)
        total_seasons = sum(1 for s in series.seasons if s.get('seasonNumber', 0) > 0)

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
            total_seasons=total_seasons,
            current_season=cur_cur,
            current_season_progress=cur_prog,
            current_season_complete=cur_comp,
            current_season_episodes=cur_eps,
            current_season_downloaded=cur_down,
            season_episode_counts=series.season_episode_counts,
            poster_url_poster=poster_url_poster,
            episodes_in_range=in_range,
            date_range_episodes=total_individual_episodes,
            date_range_downloaded=range_downloaded,
            date_range_percentage=range_percent,
            date_range_color=range_color
        ))

    processed.sort(key=lambda x: (-x.date_range_percentage, x.title))
    return processed

def calculate_overall_statistics(shows: List[ProcessedShow], date_range) -> Dict[str, Any]:
    """Calculate statistics for shows that have episodes in the date range."""
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

def calculate_library_statistics(all_series: List[Dict]) -> Dict[str, Any]:
    """
    Calculate overall statistics across all series in the library.
    Uses the raw API data, not just shows that have episodes in the date range.
    """
    total_series = len(all_series)

    total_episodes_all = 0
    total_downloaded_all = 0
    total_seasons_all = 0
    monitored_seasons = 0
    unmonitored_seasons = 0

    for series in all_series:
        # Use the same logic as in SeriesInfo.from_api but inline for efficiency
        stats = series.get('statistics', {})
        episode_count = series.get('episodeCount') or stats.get('episodeCount', 0)
        episode_file_count = series.get('episodeFileCount') or stats.get('episodeFileCount', 0)

        total_episodes_all += episode_count
        total_downloaded_all += episode_file_count

        # Count seasons (excluding specials)
        seasons = series.get('seasons', [])
        for season in seasons:
            sn = season.get('seasonNumber', 0)
            if sn <= 0:
                continue
            total_seasons_all += 1
            if season.get('monitored'):
                monitored_seasons += 1
            else:
                unmonitored_seasons += 1

    overall_progress = (total_downloaded_all / total_episodes_all * 100) if total_episodes_all else 0

    return {
        'total_series': total_series,
        'total_episodes_all': total_episodes_all,
        'total_downloaded_all': total_downloaded_all,
        'total_seasons_all': total_seasons_all,
        'monitored_seasons': monitored_seasons,
        'unmonitored_seasons': unmonitored_seasons,
        'overall_progress': overall_progress,
    }

def calculate_completed_seasons_in_range(
    shows: List[ProcessedShow],
    episodes: List[Dict],
    start_date: date,
    end_date: date,
    sonarr_client
) -> List[Dict]:
    completed = []
    for show in shows:
        if not show.current_season_complete:
            continue

        season_eps = [e for e in show.episodes_in_range if e.season_number == show.current_season]
        if season_eps:
            latest = max(season_eps, key=lambda e: e.air_date or date.min)
            if latest.air_date and start_date <= latest.air_date <= end_date:
                completed.append({
                    'title': show.title,
                    'series_id': show.series_id,
                    'season': show.current_season,
                    'completion_date': latest.air_date,
                    'total_episodes': show.current_season_episodes,
                    'poster_url': show.poster_url_poster or show.poster_url
                })
        else:
            all_episodes = sonarr_client.get_series_episodes(show.series_id)
            season_eps_all = [e for e in all_episodes if e.get('seasonNumber') == show.current_season and e.get('airDate')]
            if not season_eps_all:
                continue
            season_eps_all.sort(key=lambda e: e.get('episodeNumber', 0))
            last_ep = season_eps_all[-1]
            last_air_date = datetime.strptime(last_ep['airDate'], "%Y-%m-%d").date()
            if start_date <= last_air_date <= end_date:
                completed.append({
                    'title': show.title,
                    'series_id': show.series_id,
                    'season': show.current_season,
                    'completion_date': last_air_date,
                    'total_episodes': show.current_season_episodes,
                    'poster_url': show.poster_url_poster or show.poster_url
                })

    return completed