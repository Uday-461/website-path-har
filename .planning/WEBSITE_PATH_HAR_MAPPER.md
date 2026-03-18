# Website Path & HAR Mapper

## Context

Websites expose implicit API surfaces through their browser traffic — but there's no automated way to discover and document them. This tool solves that by launching AI-controlled browser instances that autonomously explore a website, execute user journeys, capture all network traffic as HAR files, and produce a structured site map with a complete API surface analysis.

Use cases:
- API surface discovery for integration or security review
- Automated regression baseline for site structure
- Journey mapping for QA and test coverage
- Understanding third-party dependencies a site calls

## Design

### Architecture

```
URL + auth_instruction
  → DiscoveryAgent       (1 browser, maps all pages + defines journeys)
  → JourneyAgents × N   (each: own browser, own HAR, DOM snapshots)
  → HarParser           (per-journey .har → endpoint summaries)
  → ResultAggregator    → SiteMap JSON
```

### Key decisions

- **Wraps browser-use, never forks it** — `Agent`, `BrowserSession`, `BrowserProfile`, `Tools` are used as-is from `browser-use==0.12.2`
- **LLM**: `ChatOpenRouter` via `browser_use.llm.openrouter.chat` pointing at `qwen/qwen2.5-vl-72b-instruct` (vision-capable, handles screenshots)
- **HAR isolation**: one `BrowserSession` per journey → one `.har` file per journey, no cross-contamination
- **Auth**: passed as a plain English instruction string in the agent prompt, never stored as credentials
- **Parallelism**: `asyncio.Semaphore` limits concurrent journey agents (default 3, max 10)
- **Path normalization**: `/api/products/123` → `/api/products/{id}` using regex patterns for numeric IDs, UUIDs, and Mongo ObjectIDs

## Implementation Plan

### Phase 0: Claude Code Setup ✅
- [x] `CLAUDE.md` at project root
- [x] `.claude/rules/` — python-style, browser-use-patterns, security
- [x] `.claude/commands/` — scan, parse-har, plans
- [x] `.claude/agents/` — site-explorer, har-analyst
- [x] `.claude/skills/browser-use-integration/SKILL.md`
- [x] `.claude/settings.json` — auto-format hook on Python file edits

### Phase 1: MVP — Sequential, Single Instance ✅
- [x] `pyproject.toml` + `.env.example` + `.python-version`
- [x] `src/pathhar/config.py` — Pydantic Settings (`OPENROUTER_API_KEY`, `LLM_MODEL`, etc.)
- [x] `src/pathhar/models/` — `SiteMap`, `Route`, `APISurface`, `APIEndpoint`, `JourneyDefinition`, `JourneyStep`, `JourneyResult`, `HarSummary`, `EndpointInfo`, `DOMSnapshot`
- [x] `src/pathhar/engine/llm_factory.py` — `create_llm()` → `ChatOpenRouter`
- [x] `src/pathhar/engine/custom_tools.py` — `report_route`, `report_journey`, `capture_dom_snapshot`, `log_step`, `mark_explored`, `is_explored`
- [x] `src/pathhar/engine/discovery_agent.py` — `run_discovery()` → routes + journeys
- [x] `src/pathhar/engine/journey_agent.py` — `run_journey()` with HAR recording
- [x] `src/pathhar/parsing/har_parser.py` — filter statics, extract endpoints
- [x] `src/pathhar/parsing/endpoint_extractor.py` — `extract_path_pattern()`, `group_endpoints()`
- [x] `src/pathhar/parsing/schema_inferrer.py` — `infer_schema()` from JSON bodies
- [x] `src/pathhar/orchestrator/service.py` — 4-phase pipeline
- [x] `src/pathhar/orchestrator/parallel.py` — `run_parallel()` with `asyncio.Semaphore`
- [x] `src/pathhar/orchestrator/result_aggregator.py` — `aggregate_results()` → `SiteMap`
- [x] `src/pathhar/output/writer.py` — `write_site_map()` → JSON
- [x] `src/pathhar/cli.py` — `pathhar scan <url>` and `pathhar parse-har <path>`
- [x] 28 unit tests, zero lint errors

### Phase 2: Polish & Parallel (Pending)
- [ ] Smarter schema inferrer — merge multiple samples of same endpoint
- [ ] HTML report output (`output/report.html`)
- [ ] Re-scan diffing — compare two `SiteMap` JSONs
- [ ] Progress output during scan (live journey status)
- [ ] `--max-steps` flag to cap discovery depth

### Phase 3: Platform (Future)
- [ ] FastAPI server with `/scan` endpoint
- [ ] WebSocket progress stream
- [ ] Incremental re-scanning (skip already-known routes)
- [ ] Authentication session persistence across journeys

## Files to Create/Modify

### Already created
```
src/pathhar/
  cli.py
  config.py
  models/site_map.py, journey.py, har_summary.py, dom_snapshot.py
  engine/llm_factory.py, custom_tools.py, discovery_agent.py, journey_agent.py
  parsing/har_parser.py, endpoint_extractor.py, schema_inferrer.py
  orchestrator/service.py, parallel.py, result_aggregator.py
  output/writer.py
tests/
  conftest.py, test_har_parser.py, test_orchestrator.py
```

### Phase 2 targets
```
src/pathhar/output/html_writer.py    (new)
src/pathhar/output/diff.py           (new)
src/pathhar/cli.py                   (add --max-steps, progress output)
src/pathhar/parsing/schema_inferrer.py  (improve merging)
```

## Testing Strategy

```bash
# Unit tests (28 passing)
uv run pytest tests/ -v

# Parse a HAR file standalone
uv run pathhar parse-har output/har/journey_000.har

# Full scan (needs OPENROUTER_API_KEY in .env)
uv run pathhar scan https://example.com

# Scan with auth
uv run pathhar scan https://example.com --auth "click Login, use email test@test.com password abc123"

# Parallel workers
uv run pathhar scan https://example.com --parallel 5
```

Output written to `output/sitemap_<domain>.json` on completion.

## Open Questions

- Should the discovery agent run a fixed number of steps or explore until convergence?
- How to handle single-page apps that use client-side routing (no page load events)?
- HAR files only capture HTTPS — should we warn loudly or fail on HTTP-only sites?
- Should journeys that require auth be skipped when no `--auth` flag is provided, or attempted anyway?
