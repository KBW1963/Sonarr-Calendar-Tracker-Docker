# Changelog

All notable changes to the Docker version of the Sonarr Calendar Tracker are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).  
Version numbers starting from 3.0.0 correspond to the Docker‑ready release.

---

## [3.3.2] – 2026-03-04

### Fixed

- **Episode frame overflow** – Resolved an issue where badges (special, premiere, etc.) could cause episode details to overflow the fixed‑height container. The episode header now uses `flex-wrap: nowrap` and its children have `min-width: 0`, ensuring all elements shrink to fit within the available space without breaking the layout.

## [3.3.1] – 2026-03-04

### Added

- **Fully responsive grid** – The main show grid now uses `grid-template-columns: repeat(auto-fit, minmax(280px, 1fr))`, automatically adjusting the number of columns based on screen width. This eliminates horizontal overflow on tablets and phones while maintaining readability.
- **Version display** – The HTML footer now shows the combined version and image type (e.g., `3.3.1-fanart`) by importing `__display_version__` from `__init__.py`.

### Changed

- **Grid columns configuration** – The `GRID_COLUMNS` environment variable is no longer used; the grid adapts dynamically. The variable remains in the code for backward compatibility but has no effect.
- **Multi‑episode specials** – Further refined grouping logic to ensure all specials (season 0) are correctly merged and display the purple left border.

### Fixed

- **Special badge placement** – Moved special badges to the episode header for better visibility, consistent with other episode types.
- **Episode grouping** – Ensured that episodes sharing the same air date are always grouped, even when they have `type=None`.

## [3.3.0] – 2026-03-04

### Added

- **Special badge (purple gem)** – Episodes with `season_number == 0` now display a **Special** badge, even when Sonarr does not provide an `episodeType`. This ensures all specials are visually distinct.
- **Series Premiere badge** – Distinct gold badge for series premieres (previously lumped with regular premieres).
- **Purple left border for specials** – Special episodes now have a solid purple left border, matching the status‑based border of regular episodes.
- **Multi‑episode grouping restored** – Episodes sharing the same air date (including specials) are grouped into a single card line with a compact display (e.g., “S00E01‑E03”) and a tooltip listing all titles.

### Changed

- **Badge placement** – Episode badges have been moved from the title line to the episode header, appearing between the episode number and the air date. This improves visibility and consistency.
- **Completed seasons poster** – The “Recently Completed Seasons” section now uses the dedicated poster image (portrait) instead of fanart, fitting better in the small container. Falls back to fanart if no poster exists.

### Fixed

- **Multi‑episode specials not grouping** – All episodes with the same air date, regardless of season (including season 0), are now correctly grouped.
- **Missing `episodeType` in Sonarr responses** – Fallback logic ensures season‑0 episodes are still badged as specials.

---

## [3.2.0] – 2026-03-03

### Added

- **Mid‑season badges** – Episodes now display `Mid‑Season Premiere` and `Mid‑Season Finale` badges using Sonarr's `episodeType` field.
- **Completed seasons fallback with caching** – If a complete show has no episodes in the date range, the app now fetches all episodes for that series (cached per run) to determine the last aired date. This ensures shows like “A Knight of the Seven Kingdoms” appear in the “Recently Completed Seasons” section even when the final episode is missing from the calendar data.

### Changed

- `api_client.py` added `get_series_episodes` with caching.
- `models.py` updated to use `episode_type` and implement fallback logic.
- `utils.py` extended to map additional Sonarr episode types.
- `html_generator.py` now passes the Sonarr client to the completed seasons function.

---

## [3.1.0] – 2026-02-28

### Added

- **Fanart priority** – The application now uses **fanart** as the primary image for show cards, with fallback to poster and then banner.
- **Graceful interrupt handling** – Press `Ctrl+C` once to exit cleanly, twice to force quit.
- **Responsive CSS** – The dashboard adapts to mobile, tablet, and desktop screens. Added fluid typography, touch‑friendly buttons, and improved grid breakpoints.
- **Fixed column width issue** – Added `min-width: 0` and `max-width: 100%` to cards to prevent long titles from stretching columns.

### Changed

- `config.py` now reads all settings from environment variables; no configuration file is needed. Required variables: `SONARR_URL`, `SONARR_API_KEY`, `DAYS_PAST`, `DAYS_FUTURE`, `OUTPUT_HTML_FILE`.
- `image_cache.py` implements the new fanart priority order.
- `Dockerfile` sets `PYTHONPATH=/app/src` and creates a non‑root user `app` (UID 1000).
- `docker-compose.yml` updated with environment variables and volume mounts for `/output` and `/cache`.

### Fixed

- Permission errors when writing to mounted volumes – directories must be owned by UID 1000.
- Timezone handling – the `TZ` environment variable now correctly sets the container’s timezone.
- Module import errors – `PYTHONPATH` ensures `sonarr_calendar` is found.

---

## [3.0.0] – 2026-02-26

### Added

- **Initial Docker release** – The application is now fully containerised.
- **Environment‑only configuration** – No JSON config file required; all settings are passed via environment variables.  
  Required: `SONARR_URL`, `SONARR_API_KEY`, `DAYS_PAST`, `DAYS_FUTURE`, `OUTPUT_HTML_FILE`.  
  Optional: `OUTPUT_JSON_FILE`, `IMAGE_CACHE_DIR`, `REFRESH_INTERVAL_HOURS`, `HTML_THEME`, `GRID_COLUMNS`, `IMAGE_QUALITY`, `ENABLE_IMAGE_CACHE`, `HTML_TITLE`, `TZ`.
- **Dockerfile** based on `python:3.11-slim` with a non‑root user (`app`).
- **docker-compose.yml** example with service definitions for the app and an optional nginx web server.
- **Documentation** in `README.md` covering building, running, and environment variables.
- **Graceful shutdown** – The app handles `SIGINT` and `SIGTERM` to exit cleanly.

### Changed

- `config.py` rewritten to load from environment variables only.
- `cli.py` updated to use the new `load_config` (no file search).
- `utils.py` enhanced with `days_until` and improved date formatting.
- `models.py` and `image_cache.py` adapted to work with environment‑based config.

### Removed

- Dependency on a local `.sonarr_calendar_config.json` file.
- File‑based configuration search (current dir, script dir, home) – all settings come from environment.

---

## [2.6.0] – 2026-02-18 (pre‑Docker version)

### Added

- Fanart priority implemented in `image_cache.py`.
- Configuration file search now includes home directory (`~/.sonarr_calendar_config/`).
- Improved CLI output and logging.

### Fixed

- Indentation error in `cli.py`.
- NameError in connection test (moved requests import inside class).

_Note: This version is the last pre‑Docker release. Docker versions start at 3.0.0._
