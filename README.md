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
