# src/sonarr_calendar/cli.py
import argparse
import logging
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional

from sonarr_calendar.config import load_config, Config
from sonarr_calendar.api_client import SonarrClient
from sonarr_calendar.image_cache import ImageCache
from sonarr_calendar.models import process_calendar_data
from sonarr_calendar.html_generator import HTMLGenerator
from sonarr_calendar.utils import (
    GracefulInterruptHandler,
    setup_logging,
    format_date_for_display,
    DateRange
)

logger = logging.getLogger(__name__)

def run_once(config: Config, handler: GracefulInterruptHandler, verbose: bool = False) -> None:
    """Run the calendar generation once."""
    try:
        sonarr = SonarrClient(config.sonarr_url, config.sonarr_api_key, handler)
        image_cache = ImageCache(config.image_cache_dir, handler, config.sonarr_url)

        logger.info("📅 Fetching calendar from %s to %s",
                    format_date_for_display(datetime.now(timezone.utc).date() - timedelta(days=config.days_past)),
                    format_date_for_display(datetime.now(timezone.utc).date() + timedelta(days=config.days_future)))

        episodes, date_range = sonarr.get_calendar(config.days_past, config.days_future)
        logger.info("✅ Found %d episodes", len(episodes))

        logger.info("ℹ️  Fetching series details...")
        all_series = sonarr.get_all_series()
        logger.info("✅ Loaded %d series", len(all_series))

        if config.enable_image_cache:
            logger.info("ℹ️  Caching images...")
            image_cache.download_all_posters(all_series)
            logger.info("✅ Image cache updated")

        processed_shows = process_calendar_data(episodes, all_series, date_range, sonarr, config)
        logger.info("ℹ️  Generating HTML calendar...")
        html_gen = HTMLGenerator(config)
        html_content = html_gen.generate(processed_shows, episodes, date_range, sonarr)  # pass sonarr client
        output_path = Path(config.output_html_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_content, encoding='utf-8')
        logger.info("✅ Calendar saved to %s", output_path)

        if config.output_json_file:
            json_path = Path(config.output_json_file)
            json_path.parent.mkdir(parents=True, exist_ok=True)
            json_data = {
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'date_range': {
                    'start': date_range.start.isoformat(),
                    'end': date_range.end.isoformat(),
                    'total_days': date_range.total_days,
                },
                'total_shows': len(processed_shows),
                'version': "2.6.0"
            }
            json_path.write_text(json.dumps(json_data, indent=2), encoding='utf-8')
            logger.info("✅ JSON data saved to %s", json_path)

        logger.info("✅ Calendar generation complete!")

    except KeyboardInterrupt:
        logger.warning("⚠️  Interrupted by user during run")
        raise  # re-raise so caller can handle

def run_forever(config: Config, handler: GracefulInterruptHandler, verbose: bool = False) -> None:
    """Run with auto‑refresh."""
    logger.info("🔄 Auto‑refresh every %d hours", config.refresh_interval_hours)
    while not handler.check_interrupt():
        try:
            run_once(config, handler, verbose)
        except KeyboardInterrupt:
            logger.info("👋 Interrupted, exiting loop")
            break

        if handler.check_interrupt():
            break

        logger.info("⏰ Waiting %d hours until next refresh...", config.refresh_interval_hours)
        # Sleep with interrupt checking
        for _ in range(config.refresh_interval_hours * 3600):
            if handler.check_interrupt():
                logger.info("👋 Exiting during sleep")
                return
            time.sleep(1)

def main() -> int:
    parser = argparse.ArgumentParser(description="Sonarr Calendar Tracker")
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--config', type=Path, default=None,
                        help='Path to config file (default: .sonarr_calendar_config.json in current dir)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()

    setup_logging(args.verbose)
    config = load_config(args.config)

    handler = GracefulInterruptHandler()   # single handler for the whole application

    try:
        if args.once:
            run_once(config, handler, args.verbose)
        else:
            run_forever(config, handler, args.verbose)
    except KeyboardInterrupt:
        logger.info("👋 Shutdown complete. Goodbye!")
    finally:
        handler.restore()

    return 0

if __name__ == "__main__":
    sys.exit(main())