![License](https://img.shields.io/badge/license-MIT-green)
![Sonarr](https://img.shields.io/badge/Sonarr-v3%2Fv4-orange)

# Sonarr Calendar Tracker 
A beautiful, feature‑rich HTML dashboard for your Sonarr shows.  
Monitor upcoming episodes over a specified date range, track overall progress, and see which seasons have been completed – all in a sleek, customisable interface.

### [Screenshot](https://github.com/KBW1963/sonarr_calendar/blob/main/sonarr_calendar_screenshot.png)

---
**NOTE: I am not a SW developer or a coder by trade. I have a little knowledge to be dangerous and have used some skills from my past working life and my hobbyist approach to build this project. 
And YES! a lot of research was needed to help me understand and develop the code, along with some AI suggestions, which to be fair is hard to not do with search engines today.

To hopefully assit those that may find this useful and do not want to use the python version [sonarr calendar tracker](https://github.com/KBW1963/Sonarr-Calendar-Tracker). Here is a docker version. 

The tracker has been designed to run locally on your own hardware and network. It hasn't been designed to be exposed to the outside world. 

I am releasing it to the community AS IS and provide no support or warranty. Use at your own risk.  ALWAYS backup before installing.

I am happy with it for my needs and will NOT be constantly developing it, sorry 😞. 

So, please be understanding! ☺️.
---
### Docker Deployment Guide
This guide hopes to provide a step‑by‑step of instructions for installing the Sonarr Calendar Tracker using Docker. It is written for users of TrueNAS SCALE, Portainer, Dockge, or any Docker‑compatible system. I 
assume you have basic familiarity with your container management tool.

I have tested the deployment via my own TrueNAS env which already has my ARR stack up and running. I deployed the Sonarr Calendar Tracker as a custom app via YAML with the HTML saved to a webdav location, this in turn is referenced by my homelab dashboard, currently [homepage](https://gethomepage.dev).

## ✨ Features

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
The python version [sonarr calendar tracker](https://github.com/KBW1963/Sonarr-Calendar-Tracker) referenced a config file, this is now handled exclusively via environment variables in the `docker-compose.yml`. 

Below is a complete list of supported variables, their requirements, descriptions, default values (if any), and examples.

| Variable | Required | Description | Default | Example |
|----------|----------|-------------|---------|---------|
| `SONARR_URL` | **Yes** | Full URL of your Sonarr instance, including protocol and port. | – | `http://192.168.1.100:8989` |
| `SONARR_API_KEY` | **Yes** | API key from Sonarr (Settings → General). | – | `your sonarr API key` |
| `DAYS_PAST` | **Yes** | Number of days before today to include in the calendar. | – | `7` |
| `DAYS_FUTURE` | **Yes** | Number of days after today to include. | – | `30` |
| `OUTPUT_HTML_FILE` | **Yes** | Full path inside the container where the HTML dashboard will be saved. Must be within a mounted volume to persist. | – | `/output/UpcomingTV.html` |
| `IMAGE_CACHE_DIR` | No | Directory where images (fanart, posters) are cached. If not set, images are stored inside the container (ephemeral). | `sonarr_images` (inside container) | `/cache` |
| `OUTPUT_JSON_FILE` | No | If set, a JSON file with metadata will be written to this path (inside a mounted volume). | (none) | `/output/data.json` |
| `REFRESH_INTERVAL_HOURS` | No | Hours between automatic refreshes when running in daemon mode. | `6` | `12` |
| `HTML_THEME` | No | Colour theme of the dashboard: `dark` or `light`. | `dark` | `light` |
| `GRID_COLUMNS` | No | Number of show cards per row in the grid layout. | `4` | `3` |
| `IMAGE_QUALITY` | No | Preferred image type. The actual selection priority is hard‑coded as: **fanart → poster → banner → any**. This variable is currently a hint; future versions may respect it more strictly. | `fanart` | `poster` |
| `ENABLE_IMAGE_CACHE` | No | Whether to cache images locally. | `true` | `false` |
| `HTML_TITLE` | No | Browser tab title for the generated HTML page. | `Sonarr Calendar Pro` | `My Sonarr Dashboard` |
| `TZ` | No | Container timezone (used for log timestamps and date calculations). | `UTC` | `America/New_York` |

### ⚠️ Important Notes

- **Required variables** must be provided; if any are missing, the application will exit with an error listing the missing ones.
- **Path variables** (`OUTPUT_HTML_FILE`, `OUTPUT_JSON_FILE`, `IMAGE_CACHE_DIR`) should point to locations inside **mounted volumes** to ensure data persists across container restarts.
- The container runs as a non‑root user with a fixed UID (usually `100`). When using host‑mounted directories, ensure they are owned by that UID (or set permissions accordingly). 
- Setting `TZ` to your local timezone ensures that logs and date calculations reflect your local time.

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





