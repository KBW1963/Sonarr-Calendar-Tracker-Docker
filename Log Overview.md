# Sonarr Calendar Tracker – Log Overview

The Sonarr Calendar Tracker generates detailed logs that help you monitor its operation, diagnose issues, and understand what the application is doing. This guide explains the different log messages, where they come from, and how to interpret them.

---

## Log Sources

Logs are emitted by several Python modules inside the container:

| Module              | Purpose                                                                         |
| ------------------- | ------------------------------------------------------------------------------- |
| `cli.py`            | Main control flow: calendar fetch, series data, image caching, HTML generation. |
| `api_client.py`     | Sonarr API calls – calendar, series, wanted missing, etc.                       |
| `image_cache.py`    | Image downloading and caching (fanart and poster).                              |
| `models.py`         | Data processing (rarely logs; mostly warnings).                                 |
| `utils.py`          | Utility functions (rarely logs).                                                |
| `html_generator.py` | Template rendering and custom logo handling.                                    |

---

## Log Levels

- **INFO** – Normal operation messages (e.g., “✅ Found 79 episodes”).
- **WARNING** – Non‑fatal issues (e.g., missing image URL, failed download but continuing).
- **ERROR** – Failures that may affect functionality (e.g., API request failure).
- **DEBUG** – Detailed information, enabled only with `--verbose`.

---

## Common Log Messages (with Explanations)

### 1. Start of a generation cycle

📅 Fetching calendar from <Start_date> to <End_date>

- **Source:** `cli.py`
- **Meaning:** The tracker is about to retrieve episodes from Sonarr for the specified date range.

### 2. Calendar fetch results

✅ Found 79 episodes

- **Source:** `cli.py`
- **Meaning:** Successfully received `79` episodes from Sonarr’s calendar endpoint.

API request failed: 404 Client Error: Not Found for url: ...

- **Source:** `api_client.py`
- **Meaning:** The request to Sonarr failed (e.g., wrong URL, Sonarr not reachable). The calendar will continue with empty data.

### 3. Series details

ℹ️ Fetching series details...
✅ Loaded 91 series

- **Source:** `cli.py`
- **Meaning:** Successfully retrieved 91 series from Sonarr’s `/series` endpoint.

### 4. Series status distribution

📊 Series status distribution:
continuing: 66
ended: 23
upcoming: 2
📊 Monitored series: 69, Unmonitored series: 22
📊 Ended series: 23, Continuing series: 68

- **Source:** `cli.py`
- **Meaning:** Statistics about the library: counts by status, monitored/unmonitored series. Useful for verifying data.

### 5. Wanted missing episodes

ℹ️ Fetching wanted missing episodes...
✅ Found 0 missing monitored episodes

- **Source:** `cli.py`
- **Meaning:** No monitored episodes are currently missing (all downloaded). If >0, those are episodes you have not yet downloaded.

### 6. Future episodes

ℹ️ Fetching future episodes...
✅ Found 102 future episodes

- **Source:** `cli.py`
- **Meaning:** Number of episodes scheduled after today (up to 5 years ahead).

### 7. Image cache checking

ℹ️ Checking cached images...
✅ Found 91 fanart images, 91 poster images (cached)

- **Source:** `cli.py` / `image_cache.py`
- **Meaning:** The tracker found existing images in the cache directory. The numbers show how many fanart and poster files are already present.

### 8. Image downloads

ℹ️ Downloading missing images...
Downloading poster for series 1 from https://<Sonarr_url>/MediaCover/1/poster.jpg
Successfully downloaded poster for series 1

- **Source:** `image_cache.py`
- **Meaning:** The tracker is downloading a missing image. If a download fails, you’ll see a `WARNING` with the error.

### 9. Image download failures (401)

WARNING - Failed to download poster for series 1: 401 Client Error: Unauthorized for url: ...

- **Source:** `image_cache.py`
- **Meaning:** The image URL requires authentication. Usually because `SONARR_URL` is set to a public URL that requires login. Use an internal, non‑authenticated URL instead.

### 10. Image download failures (timeout)

WARNING - Failed to download poster for series 1: HTTPConnectionPool(host='192.168.1.100', port=8989): Max retries exceeded with url: ...

- **Source:** `image_cache.py`
- **Meaning:** The connection to Sonarr timed out. Check network connectivity and firewall settings.

### 11. Image cache rebuild after download

ℹ️ Rebuilding image URL cache after download...
✅ After download: 91 fanart images, 91 poster images

- **Source:** `cli.py`
- **Meaning:** After downloading any missing images, the tracker updates its internal dictionary of cached URLs.

### 12. HTML generation

ℹ️ Generating HTML calendar...
✅ Calendar saved to /output/index.html

- **Source:** `cli.py`
- **Meaning:** The HTML file has been written successfully.

### 13. Custom logo logging (if enabled)

✅ Custom logo configured: /logo.png
or
✅ Custom logo found at local path: /output/logo.png
or
⚠️ Custom logo path configured but file does not exist: /output/logo.png

- **Source:** `html_generator.py`
- **Meaning:** The tracker found a custom logo URL in the environment (`CUSTOM_LOGO_URL` or `CUSTOM_LOGO_PATH`) and will include it in the HTML. The log shows the resolved source (relative path or URL). If a local file path was used and the file does not exist, a warning would appear instead.

### 14. Overall completion

✅ Calendar generation complete!

- **Source:** `cli.py`
- **Meaning:** The generation finished successfully.

### 15. Auto‑refresh waiting

⏰ Waiting 6 hours until next refresh..

- **Source:** `cli.py`
- **Meaning:** The container is in daemon mode and will sleep before the next automatic generation.

---
## How Docker Logs Work
Docker captures stdout and stderr from the container and stores them in a JSON file on the host (usually `/var/lib/docker/containers/<container-id>/<container-id>-json.log`). 

The default logging driver is json-file, which supports rotation options.

Without rotation, the log file can grow very large, potentially filling the disk.

<details>
  <summary>Finding the Log File Path on TrueNAS</summary>
  
#### 1. Get the container ID
```bash
docker ps -a | grep sonarr-monitor
```
The first column is the container ID (e.g., a1b2c3d4e5f6).

#### 2. Find the log file location
```bash
docker inspect --format='{{.LogPath}}' <container-id>
```
This will print the full path to the JSON log file on the host (e.g., `/mnt/.../docker/containers/a1b2c3d4e5f6/a1b2c3d4e5f6-json.log`).

#### 3. Check its size
```bash
du -sh $(docker inspect --format='{{.LogPath}}' <container-id>)
```
#### Example Output:
```bash
$ docker inspect --format='{{.LogPath}}' a1b2c3d4e5f6
12K     /mnt/.ix-apps/docker/containers/a1b2c3d4e5f6-json.log
```
</details>

#### Alternative: Use TrueNAS GUI (if available)
TrueNAS Scale does not expose Docker log rotation in its UI. The recommended approach is to use the Docker Compose logging options as described.

If you prefer to manage logs via the TrueNAS command line, you can also set up a periodic task to truncate logs, but the built‑in Docker rotation is simpler and safer.

```bash
docker inspect --format='{{.LogPath}}' <container-id>
```
This will print the full path to the JSON log file on the host (e.g., `/mnt/.../docker/containers/a1b2c3d4e5f6/a1b2c3d4e5f6-json.log`).

## Reading Logs in Docker

View container logs: `docker logs sonarr-monitor`

Follow logs in real time: `docker logs -f sonarr-monitor`

Filter by module: `docker logs sonarr-monitor 2>&1 | grep image_cache`

### Interpreting Logs for Troubleshooting

| Problem                             | Look for...                                                                         |
| ----------------------------------- | ----------------------------------------------------------------------------------- |
| No data in calendar                 | `API request failed` for calendar or series; check `SONARR_URL`.                    |
| Missing images (broken)             | `WARNING - Failed to download` with 401 or 404; check `SONARR_URL` internal access. |
| Images not showing on external site | Check that nginx serves `/images/`; look for 404 in browser console.                |
| Container crashes on start          | Look for Python errors like `No module named sonarr_calendar`.                      |
| Logo not appearing                  | Look for `✅ Custom logo configured` or warning; verify file location.              |


## Log Rotation Configuration
Docker containers generate logs that are written to the host’s disk. By default, these logs can grow indefinitely. To prevent excessive disk usage, you should configure log rotation for your container by adding 
logging options to your docker-compose.yml.

#### Example: Basic Rotation

```yaml
services:
  sonarr-monitor:
    image: tomita2022/sonarr-calendar:latest
    # ... other configuration ...
    logging:
      driver: "json-file"
      options:
        max-size: "10m"       # maximum size of each log file
        max-file: "3"         # number of log files to keep
```

- `max-size` – When the log file reaches this size, it is rotated. Common units: k, m, g.
- `max-file` – Number of rotated log files to retain. The oldest file is deleted when the limit is exceeded.

With these settings, Docker will keep up to three log files, each up to 10 MB, for a maximum of 30 MB of logs.

#### Example with Compression (optional)
The `json-file` driver also supports compression. To enable compression (saves space), add:
```yaml
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        compress: "true"
```

### Applying Rotation to an Existing Container
If you add logging options to an existing service in `docker-compose.yml`, you must recreate the container for the changes to take effect:
```bash
docker compose down
docker compose up -d
```

### Alternative: Use a Dedicated Logging Driver
Docker supports several logging drivers (e.g., `syslog`, `journald`, `fluentd`). For example, to send logs to the systemd journal:
```yaml
    logging:
      driver: "journald"
      options:
        tag: "sonarr-monitor"
```
This sends logs to the host’s journal, which can be configured with its own rotation policies. However, for most users, the `json-file` driver with rotation is sufficient.

>[!Important]
>- Log rotation settings apply only to new containers (they are not retroactive).
>- If you use a different logging driver (e.g., none), logs are discarded. Use this only if you don't need logs.
>- For production environments, consider using a centralized logging solution (e.g., ELK stack, Loki) to manage logs across containers.

For further details, refer to the [Troubleshooting Guide](https://github.com/KBW1963/Sonarr-Calendar-Tracker-Docker/blob/main/troubleshooting.md).

## Enabling Verbose Logging

To see detailed DEBUG logs (including per‑series image checks and more), run the generator manually with the `--verbose` flag:

```bash
docker exec -it sonarr-monitor python -m sonarr_calendar --once --verbose
```

In Docker Compose, you can set the command to include `--verbose` for a single run, or modify the service to always run with verbose (not recommended for normal operation due to log volume).
