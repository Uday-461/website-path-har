---
description: Python coding conventions for the pathhar project
globs: "**/*.py"
---

# Python Style

- Use **tabs** for indentation (browser-use compatibility)
- Modern typing syntax: `str | None`, `list[str]`, `dict[str, Any]`
- Pydantic v2 models with `model_config = ConfigDict(extra='forbid')`
- Async functions for all browser/network operations
- Use `logging` module, never `print()` for output
- Imports ordered: stdlib, third-party, local (enforced by ruff)
- All public functions must have type annotations
