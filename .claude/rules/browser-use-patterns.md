---
description: How to work with the browser-use library
globs: "src/pathhar/engine/**/*.py"
---

# browser-use Patterns

- Always **wrap** `Agent`, never subclass it
- Custom tools via `Tools` class + `registry.action()` decorator
- One `BrowserSession` per journey for HAR isolation
- Reference `BrowserProfile` fields for browser configuration
- HAR recording: set `record_har_path` on `BrowserProfile`
- Use `ChatLiteLLM` from `browser_use.llm.litellm.chat` for OpenRouter
- Agent mode: `use_vision='auto'` for hybrid DOM + vision fallback
- Never mock browser-use in tests — use real objects
