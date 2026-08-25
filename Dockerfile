# Use an official Python runtime as base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=UTC \
    PYTHONPATH=/app/src

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
# CMD []
CMD ["python", "server.py"]