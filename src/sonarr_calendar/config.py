# src/sonarr_calendar/config.py
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class Config:
    sonarr_url: str
    sonarr_api_key: str
    days_past: int
    days_future: int
    output_html_file: str
    # Optional fields with defaults
    output_json_file: Optional[str] = None
    image_cache_dir: str = "sonarr_images"
    refresh_interval_hours: int = 6
    html_theme: str = "dark"
    grid_columns: int = 4
    image_quality: str = "fanart"
    enable_image_cache: bool = True
    html_title: str = "Sonarr Calendar Pro"
    sonarr_public_url: Optional[str] = None
    custom_logo_path: Optional[str] = None   # local file path inside container
    custom_logo_url: Optional[str] = None    # remote URL
    instance_name: Optional[str] = None   # custom identifier for the footer

    def __post_init__(self):
        if not self.sonarr_url.startswith(('http://', 'https://')):
            raise ValueError("sonarr_url must start with http:// or https://")
        if self.days_past < 0 or self.days_future < 0:
            raise ValueError("days_past and days_future must be non‑negative")
        if self.refresh_interval_hours <= 0:
            raise ValueError("refresh_interval_hours must be positive")

def _get_env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.lower() in ('true', '1', 'yes', 'y')

def _get_env_int(name: str, default: int) -> int:
    val = os.getenv(name)
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        logger.warning(f"Invalid integer for {name}, using default {default}")
        return default

def load_config(config_path: Optional[Path] = None) -> Config:
    """
    Load configuration from environment variables.
    The config_path parameter is ignored; it's kept for compatibility with CLI.
    """
    # Required variables – will raise KeyError if missing
    required = {
        'SONARR_URL': os.environ['SONARR_URL'],
        'SONARR_API_KEY': os.environ['SONARR_API_KEY'],
        'DAYS_PAST': _get_env_int('DAYS_PAST', None),
        'DAYS_FUTURE': _get_env_int('DAYS_FUTURE', None),
        'OUTPUT_HTML_FILE': os.getenv('OUTPUT_HTML_FILE'),
    }
    # Check required
    missing = [k for k, v in required.items() if v is None]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    # Optional variables with defaults
    config = Config(
        sonarr_url=required['SONARR_URL'],
        sonarr_api_key=required['SONARR_API_KEY'],
        days_past=required['DAYS_PAST'],
        days_future=required['DAYS_FUTURE'],
        output_html_file=required['OUTPUT_HTML_FILE'],
        output_json_file=os.getenv('OUTPUT_JSON_FILE'),
        image_cache_dir=os.getenv('IMAGE_CACHE_DIR', 'sonarr_images'),
        refresh_interval_hours=_get_env_int('REFRESH_INTERVAL_HOURS', 6),
        html_theme=os.getenv('HTML_THEME', 'dark'),
        grid_columns=_get_env_int('GRID_COLUMNS', 4),
        image_quality=os.getenv('IMAGE_QUALITY', 'fanart'),
        enable_image_cache=_get_env_bool('ENABLE_IMAGE_CACHE', True),
        html_title=os.getenv('HTML_TITLE', 'Sonarr Calendar Pro'),
        sonarr_public_url=os.getenv('SONARR_PUBLIC_URL'),
        custom_logo_path=os.getenv('CUSTOM_LOGO_PATH'),
        custom_logo_url=os.getenv('CUSTOM_LOGO_URL'),
        instance_name=os.getenv('INSTANCE_NAME'),
    )
    return config