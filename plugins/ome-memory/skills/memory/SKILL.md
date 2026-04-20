---
name: memory
description: Shared agent memory for storing and searching team knowledge. Store decisions, preferences, project context, and references that persist across conversations.
---

# Memory

Shared agent memory backed by PostgreSQL + pgvector.

## What you can do

When the user invokes `/ome-memory:memory`, help them with any of the following:

### Store knowledge
- **Always search before storing.** Before creating a new entry, run `memory_search` with the key concept. If a similar entry exists (similarity > 0.5), update or skip rather than creating a near-duplicate.
- If the existing entry is close but missing details, delete the old one and store a merged version.
- If no similar entry exists, store it.
- Types: `user`, `feedback`, `project`, `reference`, `general`

### Search
- Semantic search: `memory_search` finds related entries even with different wording
- Filter by type, project, or tag
- Results ranked by similarity score

### Browse & manage
- List recent entries with `memory_list`
- Delete outdated entries with `memory_delete`
- Review entries by type or project

### Export & import
- `memory_export` dumps all entries as JSON (without embeddings)
- `memory_import` imports entries additively — duplicates are skipped
- Use for backups or sharing knowledge between team members

## Quick examples

**Store a preference:**
> Store: Martin prefers minimal diffs in PRs (type: feedback, project: fleetshift)

**Search for context:**
> Search: how does the frontend architecture work?

**List recent project decisions:**
> List entries with type=project, project=fleetshift

## Guidelines

- **Search before store** — this is the most important rule. Never blindly create entries. Always check what already exists first.
- Always confirm before storing or deleting
- Keep entries self-contained — they should make sense without conversation context
- One fact or rule per entry — prefer updating an existing entry over adding a second one about the same topic
- Use tags for cross-cutting concerns (e.g. `["frontend", "webpack", "mf"]`)
- Show results as concise tables when listing multiple entries
