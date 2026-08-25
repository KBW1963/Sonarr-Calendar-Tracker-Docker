# src/sonarr_calendar/web.py
from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse
import json
from datetime import datetime, timezone
from pathlib import Path

from sonarr_calendar.config import load_config
from sonarr_calendar.api_client import SonarrClient
from sonarr_calendar.image_cache import ImageCache
from sonarr_calendar.models import process_calendar_data, calculate_library_statistics
from sonarr_calendar.html_generator import HTMLGenerator
from sonarr_calendar.utils import GracefulInterruptHandler, DateRange
from sonarr_calendar import __display_version__

app = FastAPI(title="Sonarr Calendar API")

@app.get("/health")
def health_check():
    return {"status": "UP"}

@app.get("/calendar", response_class=HTMLResponse)
def get_calendar_html():
    config = load_config()
    handler = GracefulInterruptHandler()
    sonarr = SonarrClient(config.sonarr_url, config.sonarr_api_key, handler)

    episodes, date_range = sonarr.get_calendar(config.days_past, config.days_future)
    all_series = sonarr.get_all_series()

    processed_shows = process_calendar_data(episodes, all_series, date_range, sonarr, config)
    library_stats = calculate_library_statistics(all_series)

    html_gen = HTMLGenerator(config)
    html_content = html_gen.generate(
        shows=processed_shows,
        episodes=episodes,
        date_range=date_range,
        sonarr_client=sonarr,
        library_stats=library_stats,
        range_stats={},
        error_message=None
    )
    return HTMLResponse(content=html_content)

@app.get("/api/calendar")
def get_calendar_json():
    config = load_config()
    handler = GracefulInterruptHandler()
    sonarr = SonarrClient(config.sonarr_url, config.sonarr_api_key, handler)

    episodes, date_range = sonarr.get_calendar(config.days_past, config.days_future)
    all_series = sonarr.get_all_series()

    processed_shows = process_calendar_data(episodes, all_series, date_range, sonarr, config)
    library_stats = calculate_library_statistics(all_series)

    return {
        "version": __display_version__,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "date_range": {
            "start": date_range.start.isoformat(),
            "end": date_range.end.isoformat()
        },
        "shows": [
            {
                "title": show.title,
                "year": show.year,
                "progress": show.progress_percentage,
                "episodes": show.date_range_episodes,
                "downloaded": show.date_range_downloaded,
                "seasons": show.total_seasons,
            }
            for show in processed_shows
        ],
        "library_stats": library_stats
    }