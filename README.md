# pathhar — Website Path & HAR Mapper

AI-powered website explorer. Give it a URL, it opens a real browser, autonomously navigates the site like a user, captures all network traffic as HAR files, and hands you back a structured map of every page and API endpoint.

## How it works

```
URL → Discovery Agent → Journey Agents (parallel) → HAR Parser → sitemap.json
```

1. **Discovery** — One AI browser visits the site, clicks through navigation, and maps every page it finds. It also defines "user journeys" (search flow, checkout, login, etc.)
2. **Journey Execution** — A fresh browser executes each journey with HAR recording. Each journey gets its own isolated `.har` file.
3. **HAR Parsing** — Each HAR is parsed: static assets filtered out, API calls extracted, path patterns normalized (`/api/products/123` → `/api/products/{id}`), JSON schemas inferred.
4. **Output** — A single `sitemap_<domain>.json` with all routes, journeys, DOM snapshots, and API surface.

## Quickstart

### 1. Install

```bash
git clone https://github.com/Uday-461/website-path-har
cd website-path-har
uv venv --python 3.11 && source .venv/bin/activate
uv sync
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and add your OpenRouter API key:
# OPENROUTER_API_KEY=sk-or-v1-...
```

### 3. Scan a site

```bash
uv run pathhar scan https://example.com
```

### 4. View results

```bash
cat output/sitemap_https_example.com.json | python3 -m json.tool

# Or parse a specific HAR file
uv run pathhar parse-har output/har/journey_000.har
```

## Configuration

All parameters can be set via CLI flags or `.env` file.

| Parameter | CLI flag | `.env` variable | Default | Description |
|-----------|----------|-----------------|---------|-------------|
| API Key | — | `OPENROUTER_API_KEY` | *(required)* | OpenRouter API key |
| Model | — | `LLM_MODEL` | `qwen/qwen2.5-vl-72b-instruct` | LLM model to use |
| Parallel journeys | `--parallel N` | `MAX_CONCURRENT_JOURNEYS` | `3` | How many journey browsers run at once (1–10) |
| Discovery steps | `--max-steps N` | `MAX_DISCOVERY_STEPS` | `30` | Max steps the discovery agent gets (5–200) |
| Headless | `--headless` / `--no-headless` | `HEADLESS` | `true` | Show or hide the browser window |
| Output dir | `--output-dir PATH` | `OUTPUT_DIR` | `./output` | Where JSON + HARs are written |
| Auth | `--auth "..."` | — | *(none)* | Plain English login instruction for the agent |

### `.env` example

```env
OPENROUTER_API_KEY=sk-or-v1-...
LLM_MODEL=qwen/qwen2.5-vl-72b-instruct
MAX_CONCURRENT_JOURNEYS=3
MAX_DISCOVERY_STEPS=30
HEADLESS=true
OUTPUT_DIR=./output
```

## CLI reference

### `pathhar scan`

```
uv run pathhar scan <URL> [OPTIONS]

Arguments:
  URL                     Website to scan (http/https)

Options:
  --auth TEXT             Auth instruction for the LLM agent
  --parallel INTEGER      Max concurrent journeys (1-10)
  --max-steps INTEGER     Max discovery steps (5-200)
  --headless/--no-headless  Run browser in headless mode (default: headless)
  --output-dir TEXT       Output directory path
  -v, --verbose           Enable debug logging
```

**Examples:**

```bash
# Basic scan
uv run pathhar scan https://shop.example.com

# Watch the browser navigate (non-headless)
uv run pathhar scan https://shop.example.com --no-headless

# Scan with authentication
uv run pathhar scan https://shop.example.com \
  --auth "click Login, enter email test@example.com and password Test1234, click Submit"

# Fast shallow scan (5 discovery steps, 1 journey at a time)
uv run pathhar scan https://shop.example.com --max-steps 5 --parallel 1

# Deep parallel scan
uv run pathhar scan https://shop.example.com --max-steps 100 --parallel 5
```

### `pathhar parse-har`

Parse any HAR file and display the API endpoint summary.

```
uv run pathhar parse-har <HAR_PATH>

Arguments:
  HAR_PATH    Path to a .har file

Options:
  -v, --verbose   Enable debug logging
```

## Output format

A completed scan writes `output/sitemap_<domain>.json`:

```json
{
  "url": "https://shop.example.com",
  "scan_timestamp": "2026-03-18T07:51:05Z",
  "scan_duration_seconds": 150.9,
  "routes": [
    {
      "url": "https://shop.example.com/grocery",
      "title": "Grocery",
      "page_type": "listing",
      "description": "...",
      "linked_from": []
    }
  ],
  "journeys": [
    {
      "journey_id": "journey_000",
      "name": "Homepage to Grocery to Product Detail",
      "success": true,
      "steps_log": ["Navigated to Grocery category", "..."],
      "har_path": "output/har/journey_000.har",
      "dom_snapshots": [
        {
          "url": "https://shop.example.com/",
          "title": "Homepage",
          "element_count": 390,
          "html_summary": "..."
        }
      ]
    }
  ],
  "api_surface": {
    "total_requests": 348,
    "unique_paths": 13,
    "endpoints": [
      {
        "method": "POST",
        "path_pattern": "/api/__api_party/apiServer",
        "status_codes": [200],
        "request_content_type": "application/json",
        "response_content_type": "application/json",
        "request_schema": null,
        "response_schema": null,
        "sample_url": "https://shop.example.com/api/__api_party/apiServer"
      }
    ]
  }
}
```

HAR files are written per-journey to `output/har/journey_NNN.har`. They may contain sensitive data (auth tokens, cookies, request bodies) — handle accordingly.

## Architecture

```
src/pathhar/
  cli.py                    Click CLI entry point
  config.py                 Pydantic Settings (reads .env)
  engine/
    llm_factory.py          Creates ChatOpenRouter instance
    discovery_agent.py      browser-use Agent that maps routes + defines journeys
    journey_agent.py        browser-use Agent that executes journeys with HAR recording
    custom_tools.py         Custom tools: report_route, report_journey, capture_dom_snapshot
  parsing/
    har_parser.py           .har JSON → HarSummary
    endpoint_extractor.py   Path pattern normalization (/products/123 → /products/{id})
    schema_inferrer.py      JSON body → schema dict
  orchestrator/
    service.py              Main pipeline: discovery → journeys → parse → aggregate
    parallel.py             asyncio.Semaphore executor
    result_aggregator.py    Merges everything into SiteMap
  models/                   Pydantic v2 data models
  output/
    writer.py               Writes sitemap JSON to disk
```

**Key design decisions:**
- Wraps [browser-use](https://github.com/browser-use/browser-use) — does not fork it
- One `BrowserSession` per journey for isolated HAR files
- Auth passed as a plain English string to the agent prompt — no credentials stored
- HAR recording only captures HTTPS traffic (browser-use limitation)

## Development

```bash
# Run tests
uv run pytest tests/ -v

# Lint + format
uv run ruff check --fix src/ tests/
uv run ruff format src/ tests/
```

## Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)
- An [OpenRouter](https://openrouter.ai) API key
- Chrome/Chromium (installed automatically by browser-use)
