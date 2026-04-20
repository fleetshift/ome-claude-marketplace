---
name: memory-ops
description: Start, stop, and check the shared memory infrastructure (pgvector DB and MCP server). No repo checkout needed — uses docker run and uvx directly.
---

# Memory Ops

Manage the ome-memory infrastructure. Everything runs without checking out any repo.

## Start the database

```bash
docker run -d --name ome-memory-pgvector \
  -e POSTGRES_USER=memory \
  -e POSTGRES_PASSWORD=memory \
  -e POSTGRES_DB=memory \
  -p 5488:5432 \
  -v ome-memory-pgdata:/var/lib/postgresql/data \
  pgvector/pgvector:pg17
```

## Stop the database

```bash
docker stop ome-memory-pgvector && docker rm ome-memory-pgvector
```

## Reset the database (destructive — deletes all memories)

```bash
docker stop ome-memory-pgvector && docker rm ome-memory-pgvector && docker volume rm ome-memory-pgdata
```

Then start it again with the command above.

## Check database status

```bash
docker ps --filter name=ome-memory-pgvector --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

## Connect the MCP server to Claude Code

After the database is running:

```bash
claude mcp add --scope project memory \
  -e DATABASE_URL=postgresql://memory:memory@localhost:5488/memory \
  -- uvx --from "git+https://github.com/fleetshift/ome-claude-marketplace.git#subdirectory=plugins/ome-memory" ome-memory-mcp
```

Then reload with `/mcp`.

## Full setup from scratch (one-shot)

```bash
# Start pgvector
docker run -d --name ome-memory-pgvector \
  -e POSTGRES_USER=memory \
  -e POSTGRES_PASSWORD=memory \
  -e POSTGRES_DB=memory \
  -p 5488:5432 \
  -v ome-memory-pgdata:/var/lib/postgresql/data \
  pgvector/pgvector:pg17

# Register MCP server
claude mcp add --scope project memory \
  -e DATABASE_URL=postgresql://memory:memory@localhost:5488/memory \
  -- uvx --from "git+https://github.com/fleetshift/ome-claude-marketplace.git#subdirectory=plugins/ome-memory" ome-memory-mcp
```

Then restart Claude Code or run `/mcp` to connect.

## Troubleshooting

**MCP server stuck on "connecting"**: The first run downloads the embedding model (~80MB). Wait 30-60s or pre-warm it:
```bash
DATABASE_URL="postgresql://memory:memory@localhost:5488/memory" \
  uvx --from "git+https://github.com/fleetshift/ome-claude-marketplace.git#subdirectory=plugins/ome-memory" ome-memory-mcp &
sleep 30 && kill %1
```
Subsequent starts are instant.

**Port 5488 in use**: Change the port in both the `docker run` command and the `DATABASE_URL`.
