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

Replace <sonarr_url> with the internal URL you plan to use (e.g., http://192.168.1.100:8989).
Check firewall rules and network settings.

## Solution

Set SONARR_URL to the internal IP of your Sonarr instance (e.g., http://192.168.1.100:8989).

If Sonarr is also in Docker, use its service name (e.g., http://sonarr:8989) and ensure both containers share a Docker network.

Double‑check the API key: SONARR_API_KEY must match the key shown in Sonarr Settings → General → Security.
