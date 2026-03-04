# src/sonarr_calendar/html_generator.py
import jinja2
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone
import base64
import logging

from sonarr_calendar import __display_version__ as version
from sonarr_calendar.models import ProcessedShow
from sonarr_calendar.utils import (
    DateRange,
    get_progress_bar_color,
    format_date_for_display,
    slugify,
    get_episode_badge,
    get_days_class,
    get_days_text
)
from sonarr_calendar.config import Config

logger = logging.getLogger(__name__)

# Sonarr icon (base64 encoded SVG)
SONARR_ICON_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M4 8 L8 4 L16 4 L20 8 L20 16 L16 20 L8 20 L4 16 L4 8" stroke="#00b4db" fill="none"/>
    <circle cx="12" cy="12" r="3" fill="#00b4db"/>
    <path d="M8 8 L10 10 M14 10 L16 8 M16 14 L14 16 M10 16 L8 14" stroke="#00b4db" stroke-width="2"/>
</svg>'''
SONARR_ICON_BASE64 = base64.b64encode(SONARR_ICON_SVG.encode('utf-8')).decode('utf-8')


class HTMLGenerator:
    def __init__(self, config: Config):
        self.config = config
        template_dir = Path(__file__).parent / 'templates'
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Register custom filters
        self.env.filters['format_date'] = format_date_for_display
        self.env.filters['slugify'] = slugify
        self.env.filters['get_episode_badge'] = get_episode_badge
        self.env.filters['get_days_class'] = get_days_class
        self.env.filters['get_days_text'] = get_days_text
        self.env.filters['get_progress_bar_color'] = get_progress_bar_color

        # Register global functions/variables
        self.env.globals['get_progress_bar_color'] = get_progress_bar_color
        self.env.globals['get_episode_badge'] = get_episode_badge
        self.env.globals['get_days_class'] = get_days_class
        self.env.globals['get_days_text'] = get_days_text
        self.env.globals['timedelta'] = timedelta
        self.env.globals['now'] = lambda: datetime.now(timezone.utc)

    def generate(self, shows: List[ProcessedShow], episodes: List[Dict], date_range: DateRange,
                 sonarr_client, library_stats: Dict[str, Any], range_stats: Dict[str, Any]) -> str:
        # DEBUG lines are commented out for normal operation
        # logger.info("\n=== DEBUG in html_generator.generate ===")
        # logger.info(f"shows list has {len(shows)} items")
        # if shows:
        #     logger.info(f"First show: {shows[0].title} (ID: {shows[0].series_id})")
        # else:
        #     logger.info("shows list is EMPTY!")

        from sonarr_calendar.models import calculate_completed_seasons_in_range

        completed_seasons = calculate_completed_seasons_in_range(
            shows, episodes, date_range.start, date_range.end, sonarr_client
        )
        # logger.info(f"DEBUG: completed_seasons returned {len(completed_seasons)} items")

        template = self.env.get_template('calendar.html.j2')
        return template.render(
            shows=shows,
            episodes=episodes,
            date_range=date_range,
            config=self.config,
            version=version,
            sonarr_icon_base64=SONARR_ICON_BASE64,
            library_stats=library_stats,
            range_stats=range_stats,
            completed_seasons=completed_seasons,
            DISPLAY_EPISODES_LIMIT=2,
            EPISODE_ITEM_HEIGHT=80,
            EXPAND_BUTTON_HEIGHT=42
        )