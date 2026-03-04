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
└── README.md
```
---
2. Create a `.dockerignore` File

Hopefully this keeps the image small by excluding unnecessary files.
```
.git
**pycache**
_.pyc
_.pyo
.pytest_cache
.coverage
htmlcov
sonarr_images
sonarr_calendar.html
sonarr_calendar_data.json
*.md

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
services:
  sonarr-calendar:
    build: .
    container_name: sonarr_calendar
    restart: unless-stopped
    environment:
      # Required
      - SONARR_URL=http://192.168.0.100:8989              # URL to your Sonarr instance (use the service name 'sonarr' if it's in the same Docker network) 
      - SONARR_API_KEY=Your_Secret_API_key                # API key from Sonarr (Settings > General > Security)
      - DAYS_PAST=7
      - DAYS_FUTURE=30
      - OUTPUT_HTML_FILE=/output/TV.html                  # output HTML file path (must be in a mounted volume)
      # Optional (with defaults shown)
      # - OUTPUT_JSON_FILE=/output/sonarr_data.json       # optional – remove if not wanted
      - IMAGE_CACHE_DIR=/cache                            # default: sonarr_images
      - REFRESH_INTERVAL_HOURS=6                          # default: 6
      - HTML_THEME=dark                                   # default: dark
      - GRID_COLUMNS=4                                    # default: 4
      - IMAGE_QUALITY=fanart                              # default: fanart
      - ENABLE_IMAGE_CACHE=true                           # default: true
      - HTML_TITLE="My Sonarr Dashboard"                  # default: Sonarr Calendar Pro
      - TZ=Europe/London                                  # for correct log timestamps
    volumes:
      - ./output:/output
      - ./cache:/cache
    networks:
      - sonarr-network
 

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




