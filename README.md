# fitai

fitai is a phone-first, multi-user local web app for fitness: track body metrics and
nutrition, set goals, and get an LLM-generated **adaptive training plan**. Self-host it on
your home LAN (e.g. a DietPi). UI is in French.

## Quick start (Docker)

```bash
# edit docker-compose.yml: set image: ghcr.io/OWNER/fitai:latest
docker compose pull && docker compose up -d
# open http://<host>:1313  →  create an account
```

Build from source: `docker compose -f docker-compose.yml -f docker-compose.build.yml up -d --build`.

| Variable | Default | Purpose |
|---|---|---|
| `FITAI_DB_PATH` | `/data/fitai.db` | SQLite location (on the `fitai-data` volume) |
| `ANTHROPIC_API_KEY` | _(unset)_ | Optional; enables direct LLM generation |
| `FITAI_LLM_MODEL` | `claude-sonnet-4-6` | Model for direct generation |

## Development

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest -q
uvicorn app.main:app --reload --port 1313
```

## Deploy on a DietPi (LAN)

1. Install Docker via `dietpi-software` (Docker + Docker Compose).
2. Copy this repo (or just `docker-compose.yml`) to the DietPi and set
   `image: ghcr.io/<owner>/fitai:latest`.
3. The published image is multi-arch (`amd64`, `arm64`):
   ```bash
   docker compose pull && docker compose up -d
   ```
4. Find the LAN address: `hostname -I`.
5. On your phone (same Wi-Fi), open `http://<dietpi-ip>:1313` and **create an account**.
6. Add to home screen for an app-like icon.

To enable direct LLM generation, set `ANTHROPIC_API_KEY` in `docker-compose.yml` and keep the
"Génération directe" toggle on in Réglages. Without a key, fitai shows copy-paste prompts.

## Backup / restore

State is one SQLite file on the `fitai-data` volume.

```bash
# Backup
docker run --rm -v fitai-data:/data -v "$PWD":/backup alpine cp /data/fitai.db /backup/fitai-backup.db
# Restore
docker run --rm -v fitai-data:/data -v "$PWD":/backup alpine cp /backup/fitai-backup.db /data/fitai.db
docker compose restart
```

## Security & the HTTPS upgrade path

Auth uses hashed passwords and an httponly, samesite=lax session cookie. Over plain LAN HTTP
the cookie isn't encrypted in transit — fine on a trusted home network. To harden (and to
unlock a full offline PWA + future camera features like progress photos), put fitai behind
HTTPS with a self-signed cert (e.g. a Caddy reverse proxy) trusted once on your phone, then
register a service worker.
