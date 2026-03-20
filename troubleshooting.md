# Sonarr Calendar Tracker – Troubleshooting Guide

This guide helps you diagnose and fix common issues when deploying the Sonarr Calendar Tracker. Follow the steps in order, or jump to the section that matches your problem.

---

## 1. Prerequisites & Initial Setup

### 1.1 Docker & Docker Compose

**Symptoms**

- `docker: command not found`
- `docker-compose: command not found`

**Diagnosis**  
Run `docker --version` and `docker compose version`. If either fails, Docker is not installed.

**Solution**  
Install Docker and Docker Compose according to your operating system:

- **Linux** – Use your package manager or the official [Docker Engine](https://docs.docker.com/engine/install/) installation.
- **Windows / macOS** – Install Docker Desktop.
- **TrueNAS Scale** – Docker is built‑in; ensure the container network is properly configured.

---

### 1.2 Sonarr Access

**Symptoms**

- Container logs show `404 Client Error` or `401 Unauthorized` for Sonarr API calls.
- Calendar shows no data or missing images.

**Diagnosis**

- Verify that Sonarr is running and reachable from the Docker host.
- Test connectivity with:

  ```bash
  curl -I http://<sonarr_url>/api/v3/system/status

  ```

Replace <sonarr_url> with the internal URL you plan to use (e.g., `http://192.168.1.100:8989`).
Check firewall rules and network settings.

**Solution**

Set SONARR_URL to the internal IP of your Sonarr instance (e.g., `http://192.168.1.100:8989`).

If Sonarr is also in Docker, use its service name (e.g., `http://sonarr:8989`) and ensure both containers share a Docker network.

Double‑check the API key: `SONARR_API_KEY` must match the key shown in Sonarr Settings → General → Security.

### 1.3 Volume Permissions

Symptoms

- Container logs contain PermissionError or OSError when writing files.
- HTML file is not created, or images are missing.

Diagnosis

- Run ls -la /path/to/host/output to see ownership and permissions.

**Solution**
The container runs as a non‑root user with UID 1000. Make the host directory writable by this user:

```bash
sudo chown -R 1000:1000 /path/to/host/output
```

Or, as a temporary test, set world‑writable permissions (less secure):

```bash
sudo chmod 777 /path/to/host/output
```

# 2. Environment Variables & Configuration

### 2.1 Missing Required Variables

Symptoms

- Container exits with ValueError: Missing required environment variables: ...

Diagnosis

- Check your docker-compose.yml or .env file for missing entries.

**Solution**
Add all required variables. The minimum set is:

```bash
SONARR_URL
SONARR_API_KEY
DAYS_PAST
DAYS_FUTURE
OUTPUT_HTML_FILE
```

### 2.2 Sonarr URL – Internal vs. Public

Symptoms

- Images fail to download (401 errors in logs).
- Links in the calendar point to internal IPs that don’t work externally.

Diagnosis

- Inspect generated HTML – image URLs may contain internal IP or public domain.
- Look for `401 Client Error` in logs during image downloads.

**Solution**

- Set `SONARR_URL` to an internal, reachable address (e.g., `http://192.168.1.100:8989`) for API calls and image downloads.
- Set `SONARR_PUBLIC_URL` to the public domain (e.g., `https://sonarr.example.com`) for user‑facing links.
- Ensure `IMAGE_BASE_URL` matches SONARR_URL (if you haven’t switched to relative paths).

### 2.3 Custom Logo Not Appearing

Symptoms

- Logo shows as a broken image, or does not appear at all.

Diagnosis

- Open browser developer tools (F12), go to the Network tab, and reload the page. Look for the logo request and check its status.
- Verify the file exists in the directory served by nginx.

**Solution**

- Use a relative path like /logo.png and place the logo file in the same directory as your HTML file (the root of the nginx web server).
- Avoid internal IPs – they won’t work externally.
- Ensure the file has read permissions for the nginx user.

# 3. Docker Deployment & Logs

### 3.1 Container Keeps Restarting

Symptoms

- Container starts, then stops, and restarts repeatedly.

Diagnosis

- Run `docker logs sonarr-monitor` to see the error message.

**Common Causes & Solutions**

- Syntax error in `docker-compose.yml` – Validate with docker compose config.
- Missing environment variable – Check required variables are set.
- Python module not found – If you mounted source code, ensure `PYTHONPATH` is set and `__main__.py` exists in the package.

### 3.2 No “Image Count” Logs

Symptoms

- Logs do not show lines like `✅ Found 91 fanart images, 91 poster images`.

Diagnosis

- The running container does not contain the code with those log lines.

**Solution**

- If using the public image, consider building your own image with the modified source, or mount your source code into the container (see Advanced section).
- Verify the mounted source is being used with:

```bash
docker exec sonarr-monitor python -c "import sonarr_calendar; print(sonarr_calendar.__file__)"
```

The output should point to your mounted source, not the system site‑packages.

### 3.3 Image Downloads Fail (401)

Symptoms

- Logs show `WARNING - Failed to download poster for series X: 401 Client Error`.

Diagnosis
The tracker is attempting to download images from a URL that requires authentication (e.g., the public Sonarr URL).

**Solution**

- Set `SONARR_URL` to an internal, trusted address that does not require login.
- If you use a reverse proxy like Pangolin, ensure the tracker uses the internal URL, not the public one.

### 3.4 Images Still Not Showing (404)

Symptoms

- Generated HTML contains relative URLs like /images/123_fanart.jpg, but the image returns 404 in the browser.

Diagnosis

- Check if the image file exists in the cache directory on the host.
- Verify that nginx is configured to serve the `/images/` location and that the alias points to the correct directory.

**Solution**
Add or verify the nginx location block:

```bash
nginx
location /images/ {
    alias /usr/share/nginx/html/sonarr_images/;
    expires 30d;
    add_header Cache-Control "public, immutable";
    try_files $uri =404;
}
```

- Ensure the cache directory is mounted into the nginx container at the path used in the alias.
- Restart nginx after configuration changes.

# 4. Web Server (nginx) & External Access

### 4.1 Images Load in HTML but Not Displayed (Mixed Content)

Symptoms

- Images are blocked by the browser; console shows “Mixed Content” warnings.

Diagnosis

- The page is served over HTTPS, but image URLs are HTTP.

**Solution**

- Use relative paths (`/images/...`) – they inherit the page’s protocol.
- If you must use absolute URLs, ensure they use HTTPS.

### 4.2 Internal Access Works, External Does Not

Symptoms

- Calendar works on local network but not from the internet.

Diagnosis

- Check router port forwarding for ports 80/443 to the machine running nginx.
- Verify DNS resolves your domain to the correct public IP.
- If using a reverse proxy (e.g., Pangolin), confirm it is forwarding traffic to the nginx container.

**Solution**

- Set up port forwarding and configure your reverse proxy correctly.
- Ensure `SONARR_PUBLIC_URL` is set to the public domain for links.

### 4.3 External Access Works, Internal Access Fails (Hairpin NAT)

Symptoms

- From inside the network, `https://calendar.example.com` does not load or is slow.

Diagnosis

- DNS resolves to the public IP, but your router cannot route the traffic back (hairpin NAT issue).

**Solution**

- Use a local DNS override (e.g., hosts file or router DNS) to point the domain to the internal IP of your nginx server.
- Alternatively, access the calendar directly via internal IP and port (e.g., `http://192.168.1.100:8081`).

### 4.4 nginx Serves on Non‑Standard Port

Symptoms

- You must include `:8081` in the URL to reach the calendar.

**Solution**

- Option A (simple): Keep the port and use the local DNS with the port in the URL.
- Option B (port 80): Change the port mapping in docker-compose.yml to 80:80, but ensure no other service uses port 80 on the host.

# 5. Image Caching & Poster/Fanart

### 5.1 Completed Seasons Show Placeholders (or Fanart) Instead of Posters

Symptoms

- Posters are not used even though they appear to be cached.

Diagnosis

- Check logs for “Found X poster images” – if zero, posters were not cached.
- Verify the template uses `cached_poster_urls` for the completed seasons section.

**Solution**

- Ensure `get_cached_image_url` returns a relative path like `/images/123_poster.jpg`.
- Confirm the template contains the proper fallback:

```jinja
{% if cached_poster_urls and cached_poster_urls.get(cs.series_id) %}
    <img src="{{ cached_poster_urls[cs.series_id] }}" ...>
{% elif cached_fanart_urls and cached_fanart_urls.get(cs.series_id) %}
    <img src="{{ cached_fanart_urls[cs.series_id] }}" ...>
{% else %}
    <div class="poster-placeholder-small">🎬</div>
{% endif %}
```

# 5.2 Cache Directory Fills Up

Symptoms

- Disk space issues due to many image files.

Solution

- The cache is designed to hold one fanart and one poster per series. You can manually delete old files if needed.
- Consider setting up a cron job to remove files older than X days if disk space is a concern.

# 6. HTML Template Customizations

### 6.1 Custom Logo Not Aligned Correctly

Symptoms

- Logo appears in the wrong place or is too large.

Solution

- Adjust the CSS for `.custom-logo-inline` (e.g., `change max-height` and `max-width`).
- Ensure the header container uses Flexbox as described in the documentation.

# 6.2 Progress Bars Not Appearing

Symptoms

- Progress bars are missing or broken.

Diagnosis

- Check browser console for JavaScript errors.
- Verify that data attributes (`data-progress`, `data-season-progress`, etc.) are present on the `.show-card` element.

Solution

- Ensure the template correctly sets these attributes (they are automatically set if the data is available).
- If you modified the template, double‑check that the loops are correct.

# 7. Logging & Debugging

### 7.1 Enable Verbose Logging

To see detailed output, run the generator manually with the --verbose flag:

```bash
docker exec -it sonarr-monitor python -m sonarr_calendar --once --verbose
```

This prints all API requests and image download attempts.

### 7.2 Inspect Generated HTML

- View page source to check image URLs, links, and data attributes.
- Use browser developer tools to inspect network traffic, especially image requests.

### 7.3 Check Container Logs

- `docker logs sonarr-monitor` – shows stdout/stderr from the container.
- Use `docker logs -f sonarr-monitor` to follow logs in real time.

# 8. Advanced: Building a Custom Docker Image

If you’ve made modifications to the source and want to avoid mounting the code every time, build your own image:

1.Copy your modified source into a directory.
2.Create a Dockerfile:

```dockerfile
FROM tomita2022/sonarr-calendar:latest
COPY sonarr_calendar /app/src/sonarr_calendar
ENV PYTHONPATH=/app/src
WORKDIR /app
```

3.Build: `docker build -t my-sonarr-calendar:latest .`
4.Use `image: my-sonarr-calendar:latest` in your `docker-compose.yml`.

This ensures your changes are always present without a separate source volume mount.

# 9. Final Checklist

Before reporting an issue, verify the following:

- Sonarr is reachable from the tracker container (internal IP, no proxy).
- All required environment variables are set correctly.
- The host output directory exists and has correct permissions.
- The generated HTML contains relative image paths (/images/...).
- nginx serves the /images/ location with the correct alias.
- If using a reverse proxy, the backend points to the correct port (8081).
- The logo file is placed in the web root and the URL is correct.

If you still encounter problems after following this guide, please open an issue on the project repository with relevant logs and configuration details.
