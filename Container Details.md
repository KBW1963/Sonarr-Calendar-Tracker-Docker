Provide as an overview for those who are interested.
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
README.md
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

