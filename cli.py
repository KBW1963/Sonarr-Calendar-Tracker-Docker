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
from sonarr_calendar.models import process_calendar_data, calculate_overall_statistics, calculate_library_statistics
from sonarr_calendar.html_generator import HTMLGenerator
from sonarr_calendar.utils import (
    GracefulInterruptHandler,
    setup_logging,
    format_date_for_display,
    DateRange
)
from sonarr_calendar import __display_version__

logger = logging.getLogger(__name__)

def run_once(config: Config, handler: GracefulInterruptHandler, verbose: bool = False) -> None:
    """Run the calendar generation once."""
    error_message = None
    try:
        sonarr = SonarrClient(config.sonarr_url, config.sonarr_api_key, handler)
        image_cache = ImageCache(config.image_cache_dir, handler, config.sonarr_url)

        logger.info("📅 Fetching calendar from %s to %s",
                    format_date_for_display(datetime.now(timezone.utc).date() - timedelta(days=config.days_past)),
                    format_date_for_display(datetime.now(timezone.utc).date() + timedelta(days=config.days_future)))

        episodes = []
        date_range = DateRange(
            datetime.now(timezone.utc).date() - timedelta(days=config.days_past),
            datetime.now(timezone.utc).date() + timedelta(days=config.days_future)
        )
        try:
            episodes, date_range = sonarr.get_calendar(config.days_past, config.days_future)
            logger.info("✅ Found %d episodes", len(episodes))
        except Exception as e:
            error_message = f"Failed to fetch calendar: {str(e)}"
            logger.error(error_message)
            # Continue with empty episodes

        logger.info("ℹ️  Fetching series details...")
        all_series = []
        try:
            all_series = sonarr.get_all_series()
            logger.info("✅ Loaded %d series", len(all_series))
        except Exception as e:
            err = f"Failed to fetch series: {str(e)}"
            if error_message:
                error_message += f"; {err}"
            else:
                error_message = err
            logger.error(err)
            # Continue with empty series

        # ---- Consolidated debug logging for series ----
        if all_series:
            status_counts = {}
            monitored_series = 0
            ended_series = 0
            total_series = len(all_series)
            for s in all_series:
                status = s.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
                if s.get('monitored', False):
                    monitored_series += 1
                if status == 'ended':
                    ended_series += 1

            unmonitored_series = total_series - monitored_series
            continuing_series = total_series - ended_series

            logger.info("📊 Series status distribution:")
            for status, count in status_counts.items():
                logger.info(f"   {status}: {count}")
            logger.info(f"📊 Monitored series: {monitored_series}, Unmonitored series: {unmonitored_series}")
            logger.info(f"📊 Ended series: {ended_series}, Continuing series: {continuing_series}")
        else:
            ended_series = 0
            continuing_series = 0
            monitored_series = 0
            unmonitored_series = 0
        # -------------------------------------------------

        logger.info("ℹ️  Fetching wanted missing episodes...")
        missing_monitored_count = 0
        try:
            wanted_missing = sonarr.get_wanted_missing(monitored=True)
            missing_monitored_count = len(wanted_missing)
            logger.info(f"✅ Found {missing_monitored_count} missing monitored episodes")
        except Exception as e:
            err = f"Failed to fetch wanted missing: {str(e)}"
            if error_message:
                error_message += f"; {err}"
            else:
                error_message = err
            logger.error(err)

        logger.info("ℹ️  Fetching future episodes...")
        future_episodes_count = 0
        try:
            future_episodes = sonarr.get_future_episodes(years=5)
            future_episodes_count = len(future_episodes)
            logger.info(f"✅ Found {future_episodes_count} future episodes")
        except Exception as e:
            err = f"Failed to fetch future episodes: {str(e)}"
            if error_message:
                error_message += f"; {err}"
            else:
                error_message = err
            logger.error(err)

        # ---- Build cached image URLs dictionaries (initial) ----
        cached_fanart_urls = {}
        cached_poster_urls = {}
        if all_series and config.enable_image_cache:
            try:
                logger.info("ℹ️  Checking cached images...")
                for series in all_series:
                    series_id = series['id']
                    fanart_url = image_cache.get_cached_image_url(series_id, 'fanart')
                    if fanart_url:
                        cached_fanart_urls[series_id] = fanart_url
                    poster_url = image_cache.get_cached_image_url(series_id, 'poster')
                    if poster_url:
                        cached_poster_urls[series_id] = poster_url
                logger.info(f"✅ Found {len(cached_fanart_urls)} fanart images, {len(cached_poster_urls)} poster images (cached)")
            except Exception as e:
                logger.warning(f"Failed to check cached images: {e}")

        # ---- Download any missing images using the authenticated session ----
        if config.enable_image_cache and all_series:
            try:
                logger.info("ℹ️  Downloading missing images...")
                # Pass the authenticated session from sonarr client
                image_cache.download_all_posters(all_series, session=sonarr.session)
                logger.info("✅ Image cache updated")

                # ---- Rebuild URL dictionaries after download to include new images ----
                logger.info("ℹ️  Rebuilding image URL cache after download...")
                cached_fanart_urls = {}
                cached_poster_urls = {}
                for series in all_series:
                    series_id = series['id']
                    fanart_url = image_cache.get_cached_image_url(series_id, 'fanart')
                    if fanart_url:
                        cached_fanart_urls[series_id] = fanart_url
                    poster_url = image_cache.get_cached_image_url(series_id, 'poster')
                    if poster_url:
                        cached_poster_urls[series_id] = poster_url
                logger.info(f"✅ After download: {len(cached_fanart_urls)} fanart images, {len(cached_poster_urls)} poster images")
            except Exception as e:
                logger.warning(f"Image caching failed: {e}")

        # Process calendar data (only if we have episodes and series)
        processed_shows = []
        if episodes and all_series:
            try:
                processed_shows = process_calendar_data(episodes, all_series, date_range, sonarr, config)
            except Exception as e:
                err = f"Failed to process calendar data: {str(e)}"
                if error_message:
                    error_message += f"; {err}"
                else:
                    error_message = err
                logger.error(err)
        else:
            logger.warning("Skipping calendar processing due to missing data")

        logger.info("ℹ️  Generating HTML calendar...")

        # Calculate two sets of statistics
        library_stats = {}
        if all_series:
            try:
                library_stats = calculate_library_statistics(all_series)
            except Exception as e:
                err = f"Failed to calculate library stats: {str(e)}"
                if error_message:
                    error_message += f"; {err}"
                else:
                    error_message = err
                logger.error(err)

        # Add extra fields to library_stats
        library_stats['ended_series'] = ended_series
        library_stats['continuing_series'] = continuing_series
        library_stats['missing_monitored'] = missing_monitored_count
        library_stats['future_episodes'] = future_episodes_count

        range_stats = {}
        if processed_shows:
            try:
                range_stats = calculate_overall_statistics(processed_shows, date_range)
            except Exception as e:
                err = f"Failed to calculate range stats: {str(e)}"
                if error_message:
                    error_message += f"; {err}"
                else:
                    error_message = err
                logger.error(err)

        html_gen = HTMLGenerator(config)
        html_content = html_gen.generate(
            shows=processed_shows,
            episodes=episodes,
            date_range=date_range,
            sonarr_client=sonarr,
            library_stats=library_stats,
            range_stats=range_stats,
            cached_fanart_urls=cached_fanart_urls,
            cached_poster_urls=cached_poster_urls,
            error_message=error_message
        )
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
                'library_stats': library_stats,
                'range_stats': range_stats,
                'version': __display_version__,
                'error': error_message
            }
            json_path.write_text(json.dumps(json_data, indent=2), encoding='utf-8')
            logger.info("✅ JSON data saved to %s", json_path)

        if error_message:
            logger.warning("⚠️  Generation completed with errors: %s", error_message)
        else:
            logger.info("✅ Calendar generation complete!")

    except KeyboardInterrupt:
        logger.warning("⚠️  Interrupted by user during run")
        raise
    except Exception as e:
        logger.exception("❌ Unexpected error in run_once")
        # Even on catastrophic failure, try to generate an error page
        try:
            html_gen = HTMLGenerator(config)
            html_content = html_gen.generate(
                shows=[],
                episodes=[],
                date_range=DateRange(
                    datetime.now(timezone.utc).date() - timedelta(days=config.days_past),
                    datetime.now(timezone.utc).date() + timedelta(days=config.days_future)
                ),
                sonarr_client=None,
                library_stats={},
                range_stats={},
                cached_fanart_urls={},
                cached_poster_urls={},
                error_message=f"Critical error: {str(e)}"
            )
            output_path = Path(config.output_html_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html_content, encoding='utf-8')
            logger.info("✅ Error page generated")
        except:
            logger.exception("❌ Failed to generate error page")

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

    handler = GracefulInterruptHandler()

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