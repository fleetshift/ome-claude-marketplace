---
name: memory-ops
description: Start, stop, and check the shared memory infrastructure (pgvector DB and MCP server). Use for operational tasks like spinning up the local dev environment.
---

# Memory Ops

Manage the ome-memory infrastructure — pgvector database and MCP server.

## Commands

### Start the database

```bash
cd /Users/martin/fleetshift/ome-claude-marketplace/plugins/ome-memory && docker compose up -d
```

Verify it's running:
```bash
docker compose -f /Users/martin/fleetshift/ome-claude-marketplace/plugins/ome-memory/docker-compose.yml ps
```

### Stop the database

```bash
cd /Users/martin/fleetshift/ome-claude-marketplace/plugins/ome-memory && docker compose down
```

Add `-v` to also remove the data volume (destructive — deletes all stored memories).

### Check database status

```bash
docker compose -f /Users/martin/fleetshift/ome-claude-marketplace/plugins/ome-memory/docker-compose.yml ps
```

### Connect the MCP server

After the database is running, connect the MCP server to Claude Code:

```bash
claude mcp add --scope project memory -e DATABASE_URL=postgresql://memory:memory@localhost:5488/memory -- uvx --from /Users/martin/fleetshift/ome-claude-marketplace/plugins/ome-memory ome-memory-mcp
```

Then reload with `/mcp`.

### Test the connection

Run a quick round trip to verify everything works:

```bash
cd /Users/martin/fleetshift/ome-claude-marketplace/plugins/ome-memory && DATABASE_URL="postgresql://memory:memory@localhost:5488/memory" uv run python -c "
from ome_memory import db
from ome_memory.embeddings import embed
conn = db.get_conn()
db.ensure_schema(conn)
result = db.search_memories(conn, embed('test'), limit=1)
print('Connected. Entries in DB:', len(result))
conn.close()
"
```

### Reset the database

Stop and remove the volume, then restart:

```bash
cd /Users/martin/fleetshift/ome-claude-marketplace/plugins/ome-memory && docker compose down -v && docker compose up -d
```

Then re-run schema setup by restarting the MCP server.
