![Sonarr](https://img.shields.io/badge/Sonarr-v3%2Fv4-orange)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.9%2B-blue?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)
![AI Assisted Yes](https://img.shields.io/badge/AI%20Assisted-Yes-red)
![Last Commit](https://img.shields.io/github/last-commit/KBW1963/sonarr-calendar-tracker?style=flat-square)

---

# Sonarr Calendar Tracker - Docker version

The Sonarr Calendar Tracker is a self‑hosted tool that generates a beautiful, interactive HTML dashboard from your Sonarr library. It fetches episode and series data, caches images, and displays upcoming episodes in a card‑based layout with progress bars, filters, and sorting. It is designed to be run in Docker, producing a static HTML file that can be served by any web server (e.g., nginx). The project has evolved significantly through user feedback, adding features like dual‑image caching, custom logos, season‑based progress filters, and a responsive design.

### [Screenshot](https://github.com/KBW1963/sonarr_calendar/blob/main/sonarr_calendar_screenshot.png)

---

>[!NOTE]
>I am not a SW developer or a coder by trade. I have a little knowledge to be dangerous and have used some skills from my past working life and my hobbyist approach to build this project.
>And YES! a lot of research was needed to help me understand and develop the code, along with some AI suggestions, which to be fair is hard to not do with search engines today.
>
>To hopefully assit those that find this useful and do not want to use the python version [sonarr calendar tracker](https://github.com/KBW1963/Sonarr-Calendar-Tracker). Here is a docker version.
>The tracker has been designed to run locally on your own hardware and network. However, I am currently reunning behind a proxy utilising [Pangolin](https://pangolin.net) on a VPS and [Nginx](https://nginx.org/) running on TrueNAS.
>I am releasing it to the community AS IS and provide no support or warranty.


>[!CAUTION]
>Use at your own risk. ALWAYS backup before installing.
>I am happy with it for my needs and will NOT be constantly developing it, sorry 😞.

## So, please be understanding! ☺️.

# Docker Deployment Guide

This guide hopes to provide a step‑by‑step of instructions for installing the Sonarr Calendar Tracker using Docker. It is written for users of TrueNAS SCALE, Portainer, Dockge, or any Docker‑compatible system. I
assume you have basic familiarity with your container management tool.

I have tested the deployment via my own TrueNAS env which already has my ARR stack up and running. I deployed the Sonarr Calendar Tracker as a custom app via YAML with the HTML saved to a WebDAV location, this in turn is referenced by my homelab dashboard, currently [homepage](https://gethomepage.dev).

## ✨ Dashboard Features

- 📅 **Customisable date range** – Choose how many days past and future to display (configurable).
- 🖼️ **Image caching** – Show posters or fanart are downloaded and stored locally for faster loading. **Fanart is now the default priority**, with fallback to poster and banner.
- 🎨 **Dark/light theme toggle** – Switch between themes with a click (your choice is saved in your browser).
- 📊 **Overall & per‑show progress** – See at a glance how much of your library is downloaded, and drill down into each series. Badges are used to highlight, Premiere episodes and Season Finale.
- 🏆 **Recently completed seasons** – Shows that finished their current season within the date range are highlighted. Poster is forced for a more professional UI.
- 🔄 **Auto‑refresh mode** – Keep the dashboard running and update periodically (configurable).
- 🌍 **OS‑aware date formatting** – Dates automatically adapt to your system’s locale (e.g. `DD/MM/YYYY` or `MM/DD/YYYY`).
- 🔗 **Direct links to Sonarr** – Click any show card to open its page in Sonarr.

---

## 🗃️ Prerequisites

- A working Docker environment – either TrueNAS SCALE Apps, Portainer, Dockge, or a machine with Docker and docker‑compose installed.
- Sonarr instance – you need its URL and API key (Settings → General in Sonarr).
- Since the dashboard defaults to fanart, it would be useful to have fanart for your shows (see image caching above).
- Basic knowledge of your container platform’s web UI (for TrueNAS users) or the command line (for docker‑compose users).
- A place to store persistent data – directories on your host where the container will write the HTML file and cache images. These should be on a dataset (TrueNAS) or any folder with appropriate permissions.

---

## 🔏 Understanding User IDs (UID) and Permissions

The container runs as a non‑root user for security. The Dockerfile creates a user named app with a specific UID (User ID). In the official image, the UID is 1000, but we will show you how to verify and adjust it.

Why this matters: When you mount a host directory into the container, that directory must be writable by the container’s user. If the UID inside the container (e.g., 1000) does not match the owner of the host
directory, you will see permission errors and files will not be saved.

---

## ⛃ Volume Mounts and Storage

The volumes mount host directories to these container paths.

- Output directory – must be writable by the container user. The HTML file (and optionally JSON) will be written here.
- Cache directory – must be writable by the container user. Images will be stored here in subdirectories named after series IDs (e.g., `123_fanart.jpg`). If you set `IMAGE_CACHE_DIR` to a path inside the output directory (e.g., `/output/sonarr_images`), then the images will appear alongside the HTML file, making them accessible via the same web server.

### ℹ️ Permission Tips

- Always check the container’s UID with docker run --rm <image> id.
- Set host directory ownership to that UID: chown UID:UID /path/to/dir
- Set directory permissions to at least 755 (owner can write, others can read).
- If you use a NAS with NFS, ensure the NFS export allows the UID to write.

---

## 🔡 Environment Variables Reference

The 🐍 python version [sonarr calendar tracker](https://github.com/KBW1963/Sonarr-Calendar-Tracker) referenced a config file, which you created via the config apps. This is now handled exclusively via environment variables in the `docker-compose.yml`.

## Example - `docker-compose.yml`

```yaml
services:
  sonarr-calendar:
    image: tomita2022/sonarr-calendar:latest
    container_name: sonarr-calendar
    restart: unless-stopped
    environment:
      # Required
      - SONARR_URL=http://192.168.0.100:8989        # URL to your Sonarr instance (use the service name 'sonarr' if it's in the same Docker network)
      - SONARR_API_KEY=your_super_secret_key        # API key from Sonarr (Settings > General > Security)
      - DAYS_PAST=7
      - DAYS_FUTURE=30
      - OUTPUT_HTML_FILE=/output/TV.html             # output HTML file path (must be in a mounted volume)
# Optional (with defaults shown)
# - OUTPUT_JSON_FILE=/output/sonarr_data.json        # optional – remove if not wanted
      - IMAGE_CACHE_DIR=/cache                       # default: sonarr_images
      - REFRESH_INTERVAL_HOURS=6                     # default: 6
      - HTML_THEME=dark                              # default: dark
      - IMAGE_QUALITY=fanart                         # default: fanart
      - ENABLE_IMAGE_CACHE=true                      # default: true
      - HTML_TITLE="My Sonarr Dashboard"             # default: Sonarr Calendar Pro
      - TZ=Europe/London                             # for correct log timestamps
    volumes:
      # Mount a directory for the generated HTML and JSON
      #- /mnt/truenas/app_configs/sonarr-calendar/output:/output  # Example
       ./output:/output

      # Mount a directory for cached images
      #- /mnt/truenas/app_configs/sonarr-calendar/cache:/cache    # Example
      - ./cache:/cache


networks:
      - sonarr-network

networks:
  sonarr-network:
    driver: bridge
```

---

## Configuration

All configuration is done via environment variables. Required variables must be set; optional ones have sensible defaults.

| Variable                  | Required | Description                                                                                                                                                                     | Default              | Example                                   |
|---------------------------|----------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------|-------------------------------------------|
| `SONARR_URL`              | **Yes**  | Internal URL of your Sonarr instance, used for API calls and image downloads. Must be reachable from the container.                                                             | –                    | `http://192.168.1.100:8989`               |
| `SONARR_API_KEY`          | **Yes**  | API key from Sonarr (Settings → General).                                                                                                                                       | –                    | `your_api_key_here`                       |
| `DAYS_PAST`               | **Yes**  | Number of days before today to include in the calendar.                                                                                                                         | –                    | `7`                                       |
| `DAYS_FUTURE`             | **Yes**  | Number of days after today to include.                                                                                                                                          | –                    | `30`                                      |
| `OUTPUT_HTML_FILE`        | **Yes**  | Full path inside the container where the HTML dashboard will be saved. Must be inside a mounted volume to persist.                                                              | –                    | `/output/index.html`                      |
| `SONARR_PUBLIC_URL`       | No       | Public URL of your Sonarr instance, used for user‑facing links (e.g., clicking a show title). If not set, falls back to `SONARR_URL`.                                          | (same as `SONARR_URL`) | `https://sonarr.example.com`              |
| `IMAGE_CACHE_DIR`         | No       | Directory inside the container where images (fanart, posters) are cached.                                                                                                       | `sonarr_images` (relative to working dir) | `/output/sonarr_images`                   |
| `IMAGE_BASE_URL`          | No       | Base URL for constructing image download URLs. Normally set to the same internal URL as `SONARR_URL`. Use only if your images are served from a different endpoint.             | (same as `SONARR_URL`) | `http://192.168.1.100:8989`               |
| `REFRESH_INTERVAL_HOURS`  | No       | Hours between automatic refreshes when running in daemon mode.                                                                                                                  | `6`                  | `12`                                      |
| `HTML_THEME`              | No       | Colour theme of the dashboard: `dark` or `light`.                                                                                                                               | `dark`               | `light`                                   |
| `IMAGE_QUALITY`           | No       | Preferred image type for main cards (`fanart` or `poster`). Fallback order is hard‑coded: fanart → poster → banner → any.                                                      | `fanart`             | `poster`                                  |
| `ENABLE_IMAGE_CACHE`      | No       | Whether to cache images locally. Disable only if you serve images directly from Sonarr without authentication.                                                                  | `true`               | `false`                                   |
| `HTML_TITLE`              | No       | Browser tab title for the generated HTML page.                                                                                                                                  | `Sonarr Calendar Pro`| `My Sonarr Dashboard`                     |
| `TZ`                      | No       | Container timezone (used for log timestamps and date calculations).                                                                                                              | `UTC`                | `Europe/London`                           |
| `CUSTOM_LOGO_URL`         | No       | Public URL of a logo image (e.g., `/logo.png` if the file is in the web root). Overrides `CUSTOM_LOGO_PATH`.                                                                    | –                    | `/logo.png` or `https://example.com/logo.png` |
| `CUSTOM_LOGO_PATH`        | No       | Path inside the container to a logo file (e.g., a mounted volume). Use if the logo is not served by the web server.                                                              | –                    | `/output/logo.png`                        |

>[!IMPORTANT]
>- **Required variables** must be provided; if any are missing, the application will exit with an error listing the missing ones.
>- **Path variables** (`OUTPUT_HTML_FILE`, `OUTPUT_JSON_FILE`, `IMAGE_CACHE_DIR`) should point to locations inside **mounted volumes** to ensure data persists across container restarts.
>- The container runs as a non‑root user with a fixed UID (usually `100`). When using host‑mounted directories, ensure they are owned by that UID (or set permissions accordingly).
>- Setting `TZ` to your local timezone ensures that logs and date calculations reflect your local time.
>- **Logo size** The logo is automatically constrained to a maximum height of 60px (adjustable in CSS if needed). It will not stretch the header.
>- **File format** Any common image format (PNG, JPG, SVG) works. Use a transparent background for best results.
>- **No additional volume mount required** if you place the logo in the existing output directory. If you need a separate mount, you can mount a file.
>
> If you wish to add/use your own logo then:
>- The internal `SONARR_URL` should be reachable from the container (use an IP or hostname that resolves internally). The `SONARR_PUBLIC_URL` is used for links in the HTML and can be a public domain.
>- Public URL (`SONARR_PUBLIC_URL`) is used for links in the HTML (e.g., clicking a show title). If omitted, it defaults to `SONARR_URL`.
>- For the logo, using a relative path like `/logo.png` is recommended if the file is placed in the web root. The web server must serve the logo file.
>- Image caching is enabled by default. The cache directory is inside the output volume (`/output/sonarr_images`). This directory must be served by your web server (see nginx.md for further details).
>- Custom logo – place a logo file in the web root and set `CUSTOM_LOGO_URL=/logo.png`. The logo appears inline with the page title.
>- All paths inside the container must be within a mounted volume to survive container restarts (except for ephemeral data).
---

## 🐳 Setting Environment Variables in Docker

#### With `docker run`:

```bash
docker run -e SONARR_URL="http://192.168.1.100:8989" \
           -e SONARR_API_KEY="your_key" \
           -e DAYS_PAST=7 \
           -e DAYS_FUTURE=30 \
           -e OUTPUT_HTML_FILE="/output/UpcomingTV.html" \
           -e IMAGE_CACHE_DIR="/cache" \
           -v /host/output:/output \
           -v /host/cache:/cache \
           your-image:latest
```

---

## 🌐 Accessing the Dashboard

### </> If You Use WebDAV on TrueNAS

If your output directory is on a WebDAV share (e.g., `/mnt/truenas/media/sonarr730`), you can access the HTML file via your WebDAV client or by mounting the share in your OS. However, the images must be placed so
that the relative path `sonarr_images/...` resolves correctly. The easiest way is to set `IMAGE_CACHE_DIR=/output/sonarr_images`. Then both HTML and images live under the same WebDAV root.

### Of you could use nginx (Optional)

To view the dashboard in a browser, you can add an nginx container that serves the output directory. Example `docker-compose` addition:

>[!NOTE]
>As stated I am running my version behind a proxy to serve the images.
>Example below:

```
services:
  web:
    image: nginx:alpine
    container_name: truenas-web
    restart: unless-stopped
    ports:
      - <TrueNAS IP>:8081:80
    volumes:
      # public HTML (root)
      - /mnt/truenas/media/sonarr730:/usr/share/nginx/html:ro
      # local HTML (subfolder)  
      - /mnt/truenas/media/sonarr730/sonarr_images:/usr/share/nginx/images_cache:ro
      # nginx conf  
      - /mnt/truenas/app_configs/nginx/custom.conf:/etc/nginx/conf.d/default.conf:ro
networks: {}
    - sonarr-calendar
```
Ensure the alias points to the correct host directory (the one mounted as /output in the tracker container).

Then access `http://your-host-ip:8081/UpcomingTV.html`.

Refer to the [nginx.md](https://github.com/KBW1963/Sonarr-Calendar-Tracker-Docker/edit/main/README.md) for further details.
