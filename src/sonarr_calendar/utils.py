# src/sonarr_calendar/utils.py
import signal
import sys
import logging
import re
from datetime import datetime, timedelta, date, timezone
from dataclasses import dataclass
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# Graceful Interrupt Handler
# ----------------------------------------------------------------------------

class GracefulInterruptHandler:
    def __init__(self):
        self.interrupt_received = False
        self.original_handler = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, self._handler)

    def _handler(self, sig, frame):
        if not self.interrupt_received:
            self.interrupt_received = True
            print("\n\n⚠️  Interrupt received - Cleaning up...")
            raise KeyboardInterrupt
        else:
            print("\n❌ Force exit")
            sys.exit(1)

    def check_interrupt(self) -> bool:
        return self.interrupt_received

    def restore(self):
        signal.signal(signal.SIGINT, self.original_handler)

# ----------------------------------------------------------------------------
# Date utilities
# ----------------------------------------------------------------------------

@dataclass(frozen=True)
class DateRange:
    start: date
    end: date

    @property
    def total_days(self) -> int:
        return (self.end - self.start).days + 1

def get_system_date_format() -> str:
    """Return the system's preferred date format string (e.g., '%d/%m/%Y')."""
    try:
        import locale
        locale.setlocale(locale.LC_TIME, '')
        test = datetime(2024, 1, 15)
        fmt = test.strftime('%x')
        if '/' in fmt:
            parts = fmt.split('/')
            if len(parts[0]) == 4:
                return '%Y/%m/%d'
            elif len(parts[2]) == 4:
                # heuristic: if first part > 12, it's day
                return '%m/%d/%Y' if int(parts[0]) <= 12 else '%d/%m/%Y'
        elif '-' in fmt:
            parts = fmt.split('-')
            if len(parts[0]) == 4:
                return '%Y-%m-%d'
            elif len(parts[2]) == 4:
                return '%m-%d-%Y' if int(parts[0]) <= 12 else '%d-%m-%Y'
    except:
        pass
    return '%d/%m/%Y'

def format_date_for_display(d: date) -> str:
    fmt = get_system_date_format()
    return d.strftime(fmt)

def days_until(air_date: Optional[date]) -> int:
    """Return number of days from today until air_date (negative if in the past)."""
    if not air_date:
        return 999
    today = datetime.now(timezone.utc).date()
    return (air_date - today).days

# ----------------------------------------------------------------------------
# Progress bar color helper
# ----------------------------------------------------------------------------

def get_progress_bar_color(pct: float) -> str:
    if pct >= 100:
        return "#4CAF50"
    if pct >= 75:
        return "#8BC34A"
    if pct >= 50:
        return "#FFC107"
    if pct >= 25:
        return "#FF9800"
    if pct > 0:
        return "#FF5722"
    return "#F44336"

# ----------------------------------------------------------------------------
# Episode badge and display helpers
# ----------------------------------------------------------------------------

def get_episode_badge(episode, season_episode_counts: Dict[int, int] = None) -> Optional[Dict[str, Any]]:
    """
    Determine if episode is a premiere or finale and return badge info.
    First uses Sonarr's episodeType if available (from the episode object or dict),
    otherwise falls back to heuristics (episode 1 = premiere, last episode = finale).
    As a fallback, any episode with season_number == 0 is considered a Special.
    """
    # Get episode type if present (from Episode object or dict)
    if hasattr(episode, 'episode_type'):
        ep_type = episode.episode_type
        season_number = episode.season_number
        episode_number = episode.episode_number
    else:
        ep_type = episode.get('episodeType')
        season_number = episode.get('seasonNumber')
        episode_number = episode.get('episodeNumber')

    # If Sonarr provided an episode type, use it directly
    if ep_type:
        # Mapping from Sonarr episode types to badge info
        type_map = {
            'seasonPremiere': {
                'type': 'premiere',
                'text': 'Season Premiere',
                'color': '#00FF00',
                'icon': 'fa-star'
            },
            'seriesPremiere': {
                'type': 'series-premiere',
                'text': 'Series Premiere',
                'color': '#FFD700',
                'icon': 'fa-star'
            },
            'midSeasonPremiere': {
                'type': 'midseason-premiere',
                'text': 'Mid‑Season Premiere',
                'color': '#00CED1',
                'icon': 'fa-star-half-alt'
            },
            'seasonFinale': {
                'type': 'season-finale',
                'text': 'Season Finale',
                'color': '#FFA500',
                'icon': 'fa-flag'
            },
            'midSeasonFinale': {
                'type': 'midseason-finale',
                'text': 'Mid‑Season Finale',
                'color': '#FF8C00',
                'icon': 'fa-flag-checkered'
            },
            'seriesFinale': {
                'type': 'series-finale',
                'text': 'Series Finale',
                'color': '#FF0000',
                'icon': 'fa-flag-checkered'
            },
            'special': {
                'type': 'special',
                'text': 'Special',
                'color': '#9C27B0',
                'icon': 'fa-gem'
            },
        }
        if ep_type in type_map:
            return type_map[ep_type]

    # Fallback for specials (season 0) even if episodeType is missing
    if season_number == 0:
        return {
            'type': 'special',
            'text': 'Special',
            'color': '#9C27B0',
            'icon': 'fa-gem'
        }

    # Fallback heuristics (for older Sonarr versions or missing episodeType)
    if not season_number or not episode_number:
        return None

    # Premiere (episode 1)
    if episode_number == 1:
        return {
            'type': 'premiere',
            'text': 'Premiere',
            'color': '#00FF00',
            'icon': 'fa-star'
        }

    # Season finale (using season episode counts)
    if season_episode_counts and season_number in season_episode_counts:
        if episode_number == season_episode_counts[season_number]:
            return {
                'type': 'season-finale',
                'text': 'Season Finale',
                'color': '#FFA500',
                'icon': 'fa-flag'
            }

    # Series finale detection would require additional data (seasonCount) – not implemented here
    return None

def get_days_class(days: int) -> str:
    if days == 0:
        return "days-today"
    elif days == 1:
        return "days-tomorrow"
    elif days > 0:
        return "days-future"
    elif days == -1:
        return "days-yesterday"
    else:
        return "days-past"

def get_days_text(days: int) -> str:
    if days == 0:
        return "Today"
    elif days == 1:
        return "Tomorrow"
    elif days > 0:
        return f"In {days} days"
    elif days == -1:
        return "Yesterday"
    else:
        return f"{abs(days)} days ago"

# ----------------------------------------------------------------------------
# Slugify for URLs
# ----------------------------------------------------------------------------

def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)   # remove punctuation
    text = re.sub(r'[-\s]+', '-', text)    # replace spaces/hyphens with single hyphen
    return text.strip('-')

# ----------------------------------------------------------------------------
# Logging setup
# ----------------------------------------------------------------------------

def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logging.getLogger('urllib3').setLevel(logging.WARNING)