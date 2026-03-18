# CLAUDE.md — Website Path & HAR Mapper

## Project Overview
Python async platform that uses browser-use (LLM browser automation) to autonomously explore websites, capture HAR files per user journey, extract DOM snapshots, and produce a complete site map with API surface analysis.

## Architecture
- **Wraps browser-use** (v0.12.2) — do NOT fork or modify browser-use internals
- **Agent mode**: Hybrid DOM + vision fallback (`use_vision='auto'`)
- **LLM**: OpenRouter via LiteLLM (`ChatLiteLLM` with `api_base`)
- **HAR isolation**: One BrowserSession per journey → one HAR file per journey
- **Parallelism**: asyncio.Semaphore for concurrent journey execution

## Code Style
- Python >=3.11, async-first
- **Tabs** for indentation (matching browser-use convention)
- Modern typing: `str | None`, `list[str]`, `dict[str, Any]`
- Pydantic v2 models for all data structures
- `service.py` for main logic, dedicated model files for Pydantic models
- Use `ruff` for linting/formatting
- Use `uv` for dependency management

## Key Commands
- Setup: `uv venv --python 3.11 && source .venv/bin/activate && uv sync`
- Run: `uv run pathhar scan <url>`
- Test: `uv run pytest tests/ -vxs`
- Lint: `uv run ruff check --fix && uv run ruff format`

## Important Constraints
- NEVER modify files in `reference_repo/` — read-only reference
- browser-use is a pip dependency, not vendored code
- Auth instructions come as a single-line prompt string, NOT env credentials
- HAR files are HTTPS-only (browser-use limitation)
- All browser-use Agent params documented at: `reference_repo/browser-use/browser_use/agent/service.py`
