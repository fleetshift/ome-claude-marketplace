---
name: memory-ops
description: Set up, start, stop, and check the shared memory infrastructure (pgvector DB and MCP server). Run this skill first if memory tools are not connected. No repo checkout needed.
---

# Memory Ops

Manage the ome-memory infrastructure. Everything runs without checking out any repo.

## First-time setup

The MCP server installs dependencies on first run (~80MB embedding model + Python packages). This takes 1-2 minutes and **will time out** if Claude Code tries to connect before installation finishes.

**Run these steps in order:**

### 1. Start the database

```bash
docker run -d --name ome-memory-pgvector \
  -e POSTGRES_USER=memory \
  -e POSTGRES_PASSWORD=memory \
  -e POSTGRES_DB=memory \
  -p 5488:5432 \
  -v ome-memory-pgdata:/var/lib/postgresql/data \
  pgvector/pgvector:pg17
```

### 2. Pre-warm the MCP server

This downloads and caches all dependencies. Run it and wait for the FastMCP banner to appear, then kill it:

```bash
DATABASE_URL="postgresql://memory:memory@localhost:5488/memory" \
  uvx --from "git+https://github.com/fleetshift/ome-claude-marketplace.git#subdirectory=plugins/ome-memory" ome-memory-mcp
```

Wait until you see the `Starting MCP server 'ome-memory'` message, then press Ctrl+C. This only needs to be done once — `uvx` caches the environment for future runs.

### 3. Restart the Claude Code session

The MCP server should now connect instantly on startup. If the memory MCP shows as "failed" in `/mcp`, restart the session — the cached environment will make the connection succeed.

---

## Day-to-day commands

### Check if the database is running

```bash
docker ps --filter name=ome-memory-pgvector --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Start the database

```bash
docker start ome-memory-pgvector
```

If the container doesn't exist yet, create it with the `docker run` command from the setup section.

### Stop the database

```bash
docker stop ome-memory-pgvector
```

### Reset the database (destructive — deletes all memories)

```bash
docker stop ome-memory-pgvector && docker rm ome-memory-pgvector && docker volume rm ome-memory-pgdata
```

Then recreate with the `docker run` command from the setup section.

## Troubleshooting

**MCP server shows "failed" or "connecting":**
- Check the database is running: `docker ps --filter name=ome-memory-pgvector`
- If this is the first run, you need to pre-warm (step 2 above)
- If already pre-warmed, restart the Claude Code session

**Port 5488 in use:** Change the port in both the `docker run` command and the `DATABASE_URL` environment variable in the MCP server config.
