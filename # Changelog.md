# Changelog

All notable changes to the Docker version of the Sonarr Calendar Tracker are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).  
Version numbers starting from 3.0.0 correspond to the Docker‑ready release.

---

## [3.6.0] - 2026-03-15

### Added

- **Dual Image Caching** – Both fanart (for main cards) and poster (for completed seasons) are now cached and served locally. This eliminates all Sonarr authentication prompts for external users.
- **Separate Cached URL Dictionaries** – `cached_fanart_urls` and `cached_poster_urls` are built in `cli.py` and passed to the template, allowing precise image type selection.
- **Completed Seasons Poster Fix** – The completed seasons section now uses poster images (portrait) again, as originally intended, served from the local cache.

### Changed

- **Image Cache Logic** – `download_all_posters` now downloads both fanart and poster images for each series. `get_cached_image_url` accepts an `image_type` parameter to retrieve the appropriate URL.
- **Template Updates** – Main card header uses `cached_fanart_urls`; completed seasons section uses `cached_poster_urls`. No fallback to Sonarr URLs remains, ensuring zero authentication prompts.

### Fixed

- **Sonarr Authentication Loop** – External users no longer see login prompts because all image requests are now served from the local nginx cache.

## [3.5.1] - 2026-03-12

### Performance

- **`cli.py`** – Consolidated multiple loops over `all_series` into a single loop when logging series status, reducing redundant passes and improving startup speed for large libraries.
- **`models.py`** - `calculate_progress`\*\* – Now iterates through seasons only once, reducing overhead.
- **`utils.py`**`calculate_overall_statistics`\*\* – Replaced multiple `sum` comprehensions with a single loop, cutting the number of passes over the shows list from ~8 to 1.

- **`process_calendar_data`** – Simplified episode collection by removing unnecessary date grouping; episodes are now appended directly to a list and sorted once, improving efficiency for large calendars.

### Changed

- **Internal logic only** – No user‑visible changes; all optimisations are purely for speed and maintainability.
- **Date Format Caching** – `format_date_for_display` now uses a cached system date format string, computed once at module load. This eliminates repeated locale lookups and date parsing, significantly speeding up template rendering, especially on pages with many dates.

### Added

- New environment variable `IMAGE_BASE_URL` (default empty) to allow relative image paths.
- Support for serving images directly from a mounted MediaCover folder via relative URLs (e.g., `/MediaCover/...`).

### Changed

- `config.py`: Added `image_base_url` field to `Config` dataclass (optional, default `""`). Reordered fields to satisfy Python dataclass requirements (all required fields first, optional fields after).
- `models.py`: Modified `process_calendar_data` to use `config.image_base_url` (instead of `config.sonarr_url`) when calling `get_poster_url`. This ensures image URLs in the generated HTML are relative when `IMAGE_BASE_URL` is empty.

### Fixed

- Resolved `TypeError` caused by a required field (`days_past`) appearing after a default field in the `Config` dataclass.

### Notes

- The `IMAGE_CACHE_DIR` and `ENABLE_IMAGE_CACHE` variables are now redundant if you are serving images via the MediaCover mount. Consider setting `ENABLE_IMAGE_CACHE=false` to disable unnecessary downloads.
- No changes were required in `image_cache.py` or `cli.py` – they already handle the new `base_url` parameter correctly.

## [3.5.0] - 2026-03-10

### Changed

- **Episode Display** – Removed grouping of multiple episodes airing on the same date. Each episode now appears individually in the preview list, allowing proper badges (e.g., premiere, finale) to be shown for every episode. The preview limit (2 episodes) and expand/collapse functionality still apply, keeping the card compact while providing more accurate episode information.

### Fixed

- **Badge Accuracy** – Previously, when multiple episodes aired on the same day, only the first episode's badge was shown. Now each episode retains its own badge, improving clarity for shows with season premieres and finales on the same date.

## [3.4.1] - 2026-03-10

### Fixed

- **Legend Filtering** – The legend items for "Started (25‑49%)", "Just Started (1‑24%)", and "Not Started (0%)" now correctly apply distinct filters instead of all using the same "Low Season Progress" filter. Each now maps to its own range, and dropdown counts are updated accordingly.
- **Filter Logic** – Updated the `applyFilters` switch to handle the new filter values, ensuring accurate filtering based on current season progress.

### Added

- **Legend Clarification** – Added a small header above the legend: "Downloaded episodes" with a download icon, making it clear that the progress colors refer to downloaded episode counts.

### Changed

- **Filter Dropdown Options** – Split the generic "Low Season Progress (<25%)" into three separate options: "Started (25‑49%)", "Just Started (1‑24%)", and "Not Started (0%)" for finer-grained filtering.

### Notes

- All previous enhancements (sorting, error handling, mobile responsiveness, visual polish) remain intact.

## [3.4.0] - 2026-03-06

### Added

- **Sorting** – A new dropdown in the filter bar allows sorting shows by:
  - Title (A-Z)
  - Overall Progress (High to Low / Low to High)
  - Current Season Progress (High to Low / Low to High)
  - Next Episode Date (Earliest first)
    The sort order is maintained even after filtering.
- **Next Episode Timestamp** – Added `next_episode_timestamp` to `ProcessedShow` for sorting by the earliest episode in the date range (or a large value if none).

### Added

- **Error Handling** – The application now gracefully handles Sonarr API failures and other exceptions:
  - Errors are logged and an error message is displayed prominently in the generated HTML.
  - Partial data is still shown where available (e.g., if series fetch succeeds but calendar fails, library stats will still display).
  - A fallback error page is generated even on critical failures, ensuring the user always sees something.

### Changed

- **Progress Filters** – Replaced overall progress filters with **current season progress** filters for better relevance. Dropdown options now:
  - Season Complete (100%)
  - High Season Progress (75‑99%)
  - Medium Season Progress (25‑74%)
  - Low Season Progress (<25%)
- **Dynamic Filter Counts** – Added JavaScript to update the option counts based on visible shows, ensuring accuracy even after search or other filters are applied.
- **Card Data** – Added `data-season-progress` attribute to each show card to support the new filters.

### Fixed

- **Filter Logic** – Updated the switch statement to use `seasonProgress` for the new season‑based options.

### Changed

- **Dot Color** – The small status dot on each show card now reflects **date range progress** instead of overall progress. This makes it immediately clear whether episodes in the current range are downloaded (green) or missing (red), even if the overall series is complete.
- **Filter Dropdown Labels** – Clarified which filters apply to overall progress vs. date range progress:
  - "Overall Progress 75‑99%", "Overall Progress 25‑74%", "Overall Progress <25%" use overall progress.
  - "Date Range Progress ≥75%" and "Date Range Progress <25%" use date range progress.
  - Counts for overall progress filters now correctly show the number of visible shows that fall into each category.

### Fixed

- **Filter Consistency** – All filters now work correctly on the visible shows (those with episodes in the selected date range).

### Fixed

- **Filter Dropdown Clarification** – Options now correctly reflect that filters apply only to shows with episodes in the current date range.
  - "All Shows" now shows the count of visible shows (from `range_stats.total_series`).
  - Overall progress counts (High, Medium, Low/Not Started) now use `range_stats` counts for the visible shows, eliminating confusion with global library counts.
  - The dropdown text "Low/Not Started (<25%)" now correctly includes shows with 0% overall progress, matching the filter logic.
- **Filter Logic** – No changes; already working correctly on visible cards.

### Fixed

- **Filter Logic** – "Date Range <25%" and "Low Progress" now correctly include shows with 0% progress, addressing an issue where shows with premieres in the date range but no downloads were not listed.
- **Filter Label** – "Low Progress" renamed to "Low/Not Started (<25%)" to better reflect that it includes 0% progress shows.

### Added

- **Library Overview Section**
  - New heading "Your current library overview" with a book icon, styled like the date box.
  - Four sentence‑style summary cards using `library_stats`:
    - Total shows and downloaded episodes.
    - Missing monitored episodes (with conditional messaging).
    - Continuing, ended, and upcoming series breakdown (now includes `upcoming` status).
    - Future episodes count.
- **Second Summary Row**
  - Two cards showing `range_stats`:
    - Number of shows with episodes in the selected date range.
    - Total episodes in range and how many are already downloaded.
- **Progress Legend**
  - Moved next to the progress bars, now using mini progress bars instead of coloured squares.
  - Integrated as a footer inside the unified filter bar.
- **Unified Filter Bar**
  - Combines search by title, progress filter dropdown, jump‑to‑show dropdown, and a clear‑filters button.
  - Progress filter dropdown replaces old radio‑button filters and now works via JavaScript.
  - Clear Filters button resets search, progress filter, and the jump dropdown.
- **Overall Progress Footnote**
  - Moved inside the "Complete Library Progress" box for better context.
  - Wording updated to: “\* Overall progress includes all episodes, whether monitored or not.”

### Changed

- **Continuing Series Count** – Now correctly includes `upcoming` status (previously only `continuing`). This fixes a discrepancy where Sonarr reported 68 continuing but the app showed 66.
- **Series‑Level Monitoring** – Added `monitored_series` and `unmonitored_series` to `library_stats` (available for future cards).
- **Layout Adjustments**
  - Date range line moved to between the two summary grids.
  - Library heading now placed above the first grid, styled consistently with the date box.
  - Progress legend and filter bar redesigned for a cleaner, more intuitive interface.
- **Filtering Logic** – Switched from CSS‑based radio filtering to JavaScript for reliability and better integration with search.

### Fixed

- **Continuing Count** – Now correctly counts series with status `'upcoming'` as continuing.
- **Progress Filter** – Previously non‑functional; now properly hides/shows cards based on the selected filter.
- **Clear Filters** – Now also resets the jump‑to‑show dropdown to its default option.

### Removed

- Old radio‑button filter labels (the previous filter row) – replaced by the unified filter bar.
- Outdated progress‑legend (the one with coloured squares) – replaced by the new mini‑bar legend.

## [3.3.7] – 2026-03-04

### Added

- **Library‑wide statistics** – The top progress bar now shows the complete library progress (all series, not just those with episodes in the date range). A new function `calculate_library_statistics` sums data from all series fetched from Sonarr.

### Changed

- **Template variables** – The summary cards and date‑range progress bar now use `range_stats` (previously `overall_stats`) to correctly reflect the filtered date range. The library progress uses `library_stats`.

### Fixed

- **Overall progress accuracy** – Previously, the overall progress bar only considered shows with episodes in the current date range, which could be misleading. Now it accurately reflects the entire library.

## [3.3.6] – 2026-03-04

### Fixed

- **Multi‑episode grouping** – Restored the logic that groups episodes with the same air date (including specials) into a single compact line with
  an ellipsis and tooltip.

## [3.3.5] – 2026-03-04

### Fixed

- **Monitored/unmonitored counts** – Specials (season 0) are now excluded from the monitored and unmonitored counts in the show footer. Only regular
  seasons are counted, resolving the issue where a show with one regular season and one special showed `1 monitored 1 unmonitored`.

## [3.3.4] – 2026-03-04

### Changed

- **Season count** – Now computed directly from the number of regular seasons (season number > 0) instead of relying on the `seasonCount` field.
  This ensures accurate totals.

## [3.3.3] – 2026-03-04

### Fixed

- **Episode list scrollbar** – Removed unwanted scrollbar in collapsed state by setting `max-height` to exactly fit preview episodes + message.
  Scroll now only appears when expanded.

## [3.3.2] – 2026-03-04

### Fixed

- **Episode frame overflow** – Resolved an issue where badges (special, premiere, etc.) could cause episode details to overflow the fixed‑height
  container. The episode header now uses `flex-wrap: nowrap` and its children have `min-width: 0`, ensuring all elements shrink to fit within the
  available space without breaking the layout.

## [3.3.1] – 2026-03-04

### Added

- **Fully responsive grid** – The main show grid now uses `grid-template-columns: repeat(auto-fit, minmax(280px, 1fr))`, automatically adjusting the
  number of columns based on screen width. This eliminates horizontal overflow on tablets and phones while maintaining readability.
- **Version display** – The HTML footer now shows the combined version and image type (e.g., `3.3.1-fanart`) by importing `__display_version__` from

`__init__.py`.

### Changed

- **Grid columns configuration** – The `GRID_COLUMNS` environment variable is no longer used; the grid adapts dynamically. The variable remains in
  the code for backward compatibility but has no effect.
- **Multi‑episode specials** – Further refined grouping logic to ensure all specials (season 0) are correctly merged and display the purple left
  border.

### Fixed

- **Special badge placement** – Moved special badges to the episode header for better visibility, consistent with other episode types.
- **Episode grouping** – Ensured that episodes sharing the same air date are always grouped, even when they have `type=None`.

## [3.3.0] – 2026-03-04

### Added

- **Special badge (purple gem)** – Episodes with `season_number == 0` now display a **Special** badge, even when Sonarr does not provide an
  `episodeType`. This ensures all specials are visually distinct.
- **Series Premiere badge** – Distinct gold badge for series premieres (previously lumped with regular premieres).
- **Purple left border for specials** – Special episodes now have a solid purple left border, matching the status‑based border of regular episodes.
- **Multi‑episode grouping restored** – Episodes sharing the same air date (including specials) are grouped into a single card line with a compact
  display (e.g., “S00E01‑E03”) and a tooltip listing all titles.

### Changed

- **Badge placement** – Episode badges have been moved from the title line to the episode header, appearing between the episode number and the air
  date. This improves visibility and consistency.
- **Completed seasons poster** – The “Recently Completed Seasons” section now uses the dedicated poster image (portrait) instead of fanart, fitting
  better in the small container. Falls back to fanart if no poster exists.

### Fixed

- **Multi‑episode specials not grouping** – All episodes with the same air date, regardless of season (including season 0), are now correctly
  grouped.
- **Missing `episodeType` in Sonarr responses** – Fallback logic ensures season‑0 episodes are still badged as specials.

---

## [3.2.0] – 2026-03-03

### Added

- **Mid‑season badges** – Episodes now display `Mid‑Season Premiere` and `Mid‑Season Finale` badges using Sonarr's `episodeType` field.
- **Completed seasons fallback with caching** – If a complete show has no episodes in the date range, the app now fetches all episodes for that
  series (cached per run) to determine the last aired date. This ensures shows like “A Knight of the Seven Kingdoms” appear in the “Recently
  Completed
  Seasons” section even when the final episode is missing from the calendar data.

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
- **Responsive CSS** – The dashboard adapts to mobile, tablet, and desktop screens. Added fluid typography, touch‑friendly buttons, and improved
  grid breakpoints.
- **Fixed column width issue** – Added `min-width: 0` and `max-width: 100%` to cards to prevent long titles from stretching columns.

### Changed

- `config.py` now reads all settings from environment variables; no configuration file is needed. Required variables: `SONARR_URL`,
  `SONARR_API_KEY`, `DAYS_PAST`, `DAYS_FUTURE`, `OUTPUT_HTML_FILE`.
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
  Optional: `OUTPUT_JSON_FILE`, `IMAGE_CACHE_DIR`, `REFRESH_INTERVAL_HOURS`, `HTML_THEME`, `GRID_COLUMNS`, `IMAGE_QUALITY`, `ENABLE_IMAGE_CACHE`,
  `HTML_TITLE`, `TZ`.
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
