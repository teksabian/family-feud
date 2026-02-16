# Render.com Deployment Guide

**Platform:** Render.com
**Runtime:** Python 3.11
**Server:** Gunicorn

---

## Environment Detection

The app auto-detects whether it's running locally or on Render:

```python
if os.environ.get('RENDER'):
    # Cloud: logs to stdout (Render dashboard)
    # QR default: https://pubfeud.gamenightguild.net
else:
    # Local: logs to /logs/ directory
    # QR default: http://localhost:5000
```

## Environment Variables

Set these in Render dashboard under Environment:

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Flask session key (generate a random string) |
| `HOST_PASSWORD` | Yes | PIN for host panel access |
| `ANTHROPIC_API_KEY` | Optional | Claude API key for AI scoring |
| `RENDER` | Auto | Set automatically by Render |
| `GITHUB_TOKEN` | Optional | For AI corrections sync to GitHub |

## Files

- **`render.yaml`** — Tells Render how to build and run (Python 3.11, gunicorn, env vars)
- **`requirements.txt`** — Python dependencies installed automatically

## Deploy Process

1. Push to GitHub (`git push origin main`)
2. Render auto-detects the push and rebuilds
3. Dependencies installed from `requirements.txt`
4. Gunicorn starts the app
5. Nuclear reset runs (fresh game state)

## Local Development

```bash
pip install -r requirements.txt
python app.py
# Visit http://localhost:5000
```

Local behavior is unchanged — logs go to `/logs/`, QR codes default to localhost.

## Key Differences: Local vs Cloud

| Feature | Local | Render |
|---------|-------|--------|
| Server | Flask dev server | Gunicorn |
| Logs | `/logs/` directory | Render dashboard (stdout) |
| QR Base URL | `http://localhost:5000` | `https://pubfeud.gamenightguild.net` |
| Secret Key | Random per start | Persistent env var |
| Host Password | Default or env var | Required env var |
