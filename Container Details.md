Provided as an overview for those who are interested and have a Docker environment to follow/test.
```
1. Project Structure
   Project has the following layout (relative to the Dockerfile):

sonarr-calendar/
├── src/
│ └── sonarr_calendar/
│ ├── **init**.py
│ ├── **main**.py
│ ├── cli.py
│ ├── config.py
│ ├── api_client.py
│ ├── models.py
│ ├── image_cache.py
│ ├── html_generator.py
│ ├── utils.py
│ └── templates/
│ └── calendar.html.j2
├── requirements.txt
├── setup.py (optional, not needed for container)
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
|── changelog.md
└── README.md
```
---
2. Create a `.dockerignore` File

Hopefully this keeps the image small by excluding unnecessary files.
```
.git
__pycache__
*.pyc
*.pyo
.pytest_cache
.coverage
htmlcov
sonarr_images
sonarr_calendar.html
sonarr_calendar_data.json
.env
# changelog.md
changelog.md
Docker Build Instrcutions.md
docker-compose_TrueNAS.yml
sonarr*.py

```
---
3. Create the Dockerfile
```
# Use an official Python runtime as base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=UTC

# Create a non-root user to run the app
RUN addgroup --system app && adduser --system --group app

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY src/ ./src/

# Ensure the templates are included
COPY src/sonarr_calendar/templates/ ./src/sonarr_calendar/templates/

# Change ownership to the non-root user
RUN chown -R app:app /app

# Switch to non-root user
USER app

# Set the entrypoint to run the module
ENTRYPOINT ["python", "-m", "sonarr_calendar"]

# Default command (auto-refresh mode)
CMD []
```
- Base image: python:3.11-slim is lightweight and Debian-based, suitable for all platforms.
- Non‑root user: Improves security.
- Entrypoint: Allows overriding the command (e.g., --once).
---
4. Create docker-compose.yml

```yaml
# docker-compose.yml
# Sonarr Calendar Tracker – Docker Compose configuration
# This file sets up the tracker container. All required environment variables must be provided.
# Optional variables have sensible defaults; uncomment and modify them as needed.

services:
  sonarr-monitor:
    image: tomita2022/sonarr-calendar:latest
    container_name: sonarr-monitor
    restart: unless-stopped
    environment:
      # ---------- REQUIRED ----------
      # Internal URL of your Sonarr instance (used for API calls and image downloads).
      # This must be reachable from within the Docker network.
      # Example: http://192.168.1.100:8989 or http://sonarr:8989 if Sonarr is also in Docker.
      - SONARR_URL=<your_sonarr_url>

      # Sonarr API key – obtain from Sonarr Settings → General.
      - SONARR_API_KEY=<your_api_key>

      # Number of days in the past to include in the calendar.
      - DAYS_PAST=7

      # Number of days in the future to include in the calendar.
      - DAYS_FUTURE=30

      # Path where the generated HTML file will be saved (inside the container).
      # Must be inside a mounted volume so the file persists.
      - OUTPUT_HTML_FILE=/output/index.html

      # ---------- OPTIONAL (with defaults) ----------
      # Public URL of your Sonarr instance (used for user‑facing links in the HTML).
      # If not set, the internal SONARR_URL will be used for links as well.
      # - SONARR_PUBLIC_URL=https://sonarr.example.com

      # Directory where images are cached (inside the container).
      # - IMAGE_CACHE_DIR=/output/sonarr_images

      # Base URL for constructing image download URLs – usually the same as SONARR_URL.
      # - IMAGE_BASE_URL=<your_sonarr_url>

      # How often to regenerate the calendar (in hours). Default: 6.
      # - REFRESH_INTERVAL_HOURS=6

      # Theme: dark or light. Default: dark.
      # - HTML_THEME=dark

      # Preferred image quality for main cards (fanart, poster, etc.). Default: fanart.
      # - IMAGE_QUALITY=fanart

      # Enable or disable image caching. Default: true.
      # - ENABLE_IMAGE_CACHE=true

      # Title displayed in the browser tab and page header. Default: My Sonarr Dashboard.
      # - HTML_TITLE=Upcoming TV Shows

      # Timezone for correct log timestamps (e.g., Europe/London, America/New_York). Default: UTC.
      # - TZ=Europe/London

    volumes:
      # Mount a host directory where the HTML file and cached images will be stored.
      # The directory must be writable by the container (user ID 1000 inside the container).
      # Replace `/path/on/host` with the actual path on your server.
      - /path/on/host:/output

    networks:
      - sonarr-network

# Define a custom network (optional). You can also use the default bridge network.
networks:
  sonarr-network:
    driver: bridge
```
---
5. Building and Running the Container

Build the image
```
docker-compose build
```
Run in auto‑refresh mode (default)
```
docker-compose up -d
```
Run once (to generate HTML and exit)
```
docker-compose run --rm sonarr-calendar --once
```
View logs
```
docker-compose logs -f
```







