# Desktop Health Agent

A local Flask dashboard that watches your machine's vital signs (CPU, memory, disk, running processes), surfaces recent security vulnerabilities from the NVD CVE feed, and tracks new AI model releases — all in one browser tab, with no data leaving your machine except the outbound API calls it makes to fetch CVE and model-release data.

## Features

- **Live system stats** — CPU, memory, and disk usage, refreshed on demand via `/api/system`
- **Process monitor** — top 20 processes by CPU usage via `/api/processes`
- **Agent activity feed** — reads `agent_events.json` and shows the most recent events via `/api/activity`
- **Log viewer** — tails `computer_health.log`, auto-tagging lines as `INFO`, `WARNING`, or `ERROR` via `/api/logs`
- **CVE feed** — pulls the last 7 days of published vulnerabilities from the [NVD API](https://nvd.nist.gov/developers) via `/api/cves`
- **AI model release tracker** — a curated feed of major LLM/AI model releases from the last 3 years via `/api/models`, plus a background scraper (`model_agent.py`) that checks OpenAI, Anthropic, and Google DeepMind's news pages for new releases

## Project structure

```
Desktop-Health-Agent/
├── app.py               # Main Flask app — dashboard + all API endpoints
├── desktop_health.py     # Earlier/alternate version of the dashboard (simpler, no curated model feed)
├── model_agent.py        # Standalone scraper that discovers new AI model releases and writes models.json
├── templates/            # HTML template(s) for the dashboard
├── static/               # CSS/JS assets for the dashboard
└── .gitignore
```

> **Note:** `app.py` and `desktop_health.py` overlap heavily — `app.py` is the more complete, more defensive version (it handles missing files, cross-platform disk paths, and adds the model feed). If you're just getting started, run `app.py`.

## Requirements

- Python 3.9+
- Dependencies (no `requirements.txt` is committed yet — install these manually):

```bash
pip install flask psutil requests beautifulsoup4
```

## Getting started

1. Clone the repo:
   ```bash
   git clone https://github.com/aditya-srinivas-ganti/Desktop-Health-Agent.git
   cd Desktop-Health-Agent
   ```
2. Install dependencies (see above).
3. Run the dashboard:
   ```bash
   python app.py
   ```
4. Open your browser to `http://127.0.0.1:5000`.

### Running the model-release agent

`model_agent.py` is a separate script, meant to be run periodically (e.g. via a scheduled task or cron job), that scrapes OpenAI, Anthropic, and Google DeepMind's news pages, deduplicates against `models.json`, and logs its activity to `computer_health.log`:

```bash
python model_agent.py
```

It keeps only releases from the last 3 years (`LOOKBACK_YEARS` in the script) and writes results to `models.json` in the project root, which the dashboard can be extended to read from.

## API endpoints

| Endpoint | Description |
|---|---|
| `GET /` | Renders the dashboard |
| `GET /api/system` | Current CPU, memory, and disk usage |
| `GET /api/processes` | Top 20 processes by CPU usage |
| `GET /api/activity` | Last 50 events from `agent_events.json` |
| `GET /api/logs` | Last 100 lines from `computer_health.log` |
| `GET /api/cves` | Recent CVEs from NVD (last 7 days) |
| `GET /api/models` | Curated AI model releases from the last 3 years |

## Known limitations

- `desktop_health.py` hardcodes the `C:\` drive for disk usage, so it only works on Windows; `app.py` fixes this by using `Path.home().anchor`.
- No `requirements.txt` or dependency lock file is included yet.
- The app runs Flask's built-in dev server (`debug=True`) — don't expose this directly to the internet as-is.
- `model_agent.py`'s scraping logic relies on the current HTML structure of each source's news page and may need updates if those pages change.

