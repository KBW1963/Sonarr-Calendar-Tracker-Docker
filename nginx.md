
```conf
server {
    listen 80;
    server_name localhost;

    # Default root for the public calendar
    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
    }

    # New location for the local calendar (optional, if you have a subfolder)
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
