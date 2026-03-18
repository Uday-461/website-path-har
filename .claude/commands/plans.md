---
description: Search, create, or update planning documents in .planning/. Usage: /plans [feature name or keyword]
---

Manage feature planning documents in `.planning/`.

Arguments: $ARGUMENTS

## Behavior

**If no argument is given** — list all existing plans in `.planning/` with a one-line summary of each (title + checkbox completion ratio to show progress).

**If an argument is given**, determine intent:

### Searching existing plans
- List all `.planning/*.md` files
- Show any whose filename or content matches the argument
- Display a summary of matching plans (title, open questions, implementation status based on checkbox completion)
- If a strong match is found, read and display the full plan

### Creating or updating a plan
1. Convert the feature name to UPPER_SNAKE_CASE (e.g., "html report" → `HTML_REPORT.md`)
2. Check if `.planning/{FEATURE_NAME}.md` already exists
3. If it **exists** — read it, present the current state, then ask what to update
4. If it **does not exist** — create it using the template below

### Plan template
```markdown
# Feature Name

## Context
Why this feature exists and what problem it solves.

## Design
Key architectural decisions and approach.

## Implementation Plan
### Phase 1: ...
- [ ] Step 1
- [ ] Step 2

### Phase 2: ...

## Files to Create/Modify
List of files that need changes.

## Testing Strategy
How to verify the implementation.

## Open Questions
Unresolved decisions.
```

5. After writing or updating, summarize the plan and confirm with the user before any implementation begins.

## Usage examples
- `/plans` — list all existing plans with progress
- `/plans html report` — find existing HTML report plan or create a new one
- `/plans parallel` — search for any plan mentioning parallelism
