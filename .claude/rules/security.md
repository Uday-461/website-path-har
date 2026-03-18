---
description: Security rules for the pathhar project
globs: "**/*.py"
---

# Security

- Never log auth instructions or credentials
- HAR files may contain sensitive data — warn in output
- No hardcoded API keys — use env vars via pydantic-settings
- Validate URLs before launching browsers (scheme must be http/https)
- Sanitize file paths in output writer
