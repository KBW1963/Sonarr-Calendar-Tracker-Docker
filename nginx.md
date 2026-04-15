# Nginx Configuration (External Web Server)

To view the dashboard in a browser, you can add an nginx container that serves the output directory.
>[!NOTE]
>As stated I am running my version behind a proxy to serve the images.

Example nginx `docker-compose.yml` below:

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
Ensure the alias points to the correct host directory (the one mounted as `/output` in the tracker container).

## `custom.conf`
If you serve the calendar via nginx, add a location block to serve images. This was done using a `custom.conf`.
This file was placed inside the nginx container at `/etc/nginx/conf.d/default.conf` (or mounted as a volume). It serves the static HTML from the root directory and handles image requests under `/images/`.

The `custom.conf` file is a minimal nginx configuration that serves both your public calendar (root) and a local version under `/local`, as well as the image cache. 

Example below:

```conf
server {
    listen 80;
    server_name localhost;

    # Default root for the public calendar
    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
    }

    # New location for the local calendar
    location /local {
        alias /usr/share/nginx/local_html;
        autoindex on;
    }

    # Serve cached images from the Sonarr Calendar Tracker
    location /images/ {
        alias /usr/share/nginx/html/sonarr_images/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        try_files $uri =404;
    }
}

```
### Explanation of each section
- `listen 80`; server_name localhost;
The server listens on port 80 for requests with `Host: localhost`. In your setup, this configuration is used by the nginx container to serve static files.

- `location /`
Serves the public calendar HTML from `/usr/share/nginx/html`. This is where your generated `index.html` (or `upcomingTV.html`) and any other static assets (like a logo) live.

- `location /local`
An optional location to serve a different version of the calendar (if you have one) from `/usr/share/nginx/local_html`. This is not used by the main calendar.


### This is the critical addition for serving cached images.
`location /images/`

- `alias /usr/share/nginx/html/sonarr_images/` maps requests for `/images/...` to the subdirectory sonarr_images inside the web root.

- `expires 30d` sets a long cache lifetime.

- `add_header Cache-Control "public, immutable"` allows browsers to cache the images aggressively.

- `try_files $uri =404`; returns a 404 if the image file does not exist.

Here's the relevant volume mount from the `nginx.yml`:
```yaml
volumes:
  - /mnt/truenas/app_configs/nginx/custom.conf:/etc/nginx/conf.d/default.conf:ro
```
This maps the host file `/mnt/truenas/app_configs/nginx/custom.conf` to the container path `/etc/nginx/conf.d/default.conf`. So nginx loads that configuration on startup. The file name on the host (`custom.conf`) is arbitrary; what matters is the mount point inside the container. As long as the mount is correct, nginx will use that configuration.

## 🧩 How it fits the  deployment
- The tracker writes images to `/output/sonarr_images` inside its container, which is mapped to the host directory `/mnt/truenas/media/sonarr730/sonarr_images` (your output volume).

- Your nginx container mounts the same host directory to `/usr/share/nginx/html/sonarr_images` (via the volumes section in your `nginx.yml`).

- The `location /images/` block uses that mount to serve the images under the `/images/` URL path.

Thus, when the HTML contains `<img src="/images/109_fanart.jpg">`, the browser requests `https://<domain URL>.co.uk/images/109_fanart.jpg`, and nginx serves the file from `/usr/share/nginx/html/sonarr_images/109_fanart.jpg`.

>[!IMPORTANT]
>The server_name localhost means this configuration only responds to requests for `localhost`. For your public domain (<your_domain>.co.uk), you need another server block (likely managed by Pangolin or a separate nginx >config). In your setup, Pangolin handles the public domain and forwards traffic to this nginx container on port 8081.
>
>If you want the images to work both internally and externally, ensure that the public-facing server (Pangolin) also passes `/images/` requests to this same nginx container. Since the image URLs are relative, they will be >requested from the same domain, so as long as the domain points to a server that serves them, they will work.

## Mounting in Docker (nginx container)
In your `nginx.yml` (or compose file), the volume mapping would be something like:

```yaml
volumes:
  - /mnt/truenas/media/sonarr730:/usr/share/nginx/html:ro
  - /mnt/truenas/app_configs/nginx/custom.conf:/etc/nginx/conf.d/default.conf:ro
```

This makes the generated HTML and image cache available to nginx.

If you need to serve the calendar on a different port (e.g., `8088`), the listen line would be `listen 8088;` and the port mapping in Docker would reflect that.

>[!NOTE]
>This is the configuration I used successfully with my external reverse proxy (Pangolin) running on a VPS to make the calendar publicly accessible with nginx and the calendar deployed via dockge on TrueNAS Scale.

