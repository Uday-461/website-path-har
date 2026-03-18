---
description: "Run a website scan. Usage: /scan <url> [--auth 'instructions'] [--parallel N]"
---

Parse the user's URL and optional flags, then execute the orchestrator pipeline:
1. Validate URL is reachable
2. Run DiscoveryAgent to map routes and plan journeys
3. Execute each journey with HAR capture
4. Parse HARs and aggregate results
5. Write output to OUTPUT_DIR

Run this command:
```
uv run pathhar scan $ARGUMENTS
```
