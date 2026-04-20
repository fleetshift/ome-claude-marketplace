---
name: memory-share
description: Export and import ome-memory database dumps via Google Drive. Use to share knowledge bases between team members or create backups.
---

# Memory Share

Export and import full ome-memory database dumps via Google Drive.

> **Prerequisite:** This skill requires the `gws` CLI and its Drive skills (`gws-drive`, `gws-drive-upload`) to be installed. Install via: `gws generate-skills`

This uses `pg_dump`/`pg_restore` for a complete DB-level backup (schema + data including embeddings), not the MCP-level `memory_export` which strips embeddings and requires re-embedding on import.

## Export to Google Drive

```bash
# 1. Dump the database
pg_dump -Fc -h localhost -p 5488 -U memory -d memory \
  -f /tmp/ome-memory-dump.pgdump

# 2. Upload to Google Drive
gws drive +upload /tmp/ome-memory-dump.pgdump \
  --name "ome-memory-$(date +%Y%m%d).pgdump"

# 3. (Optional) Upload to a shared folder
gws drive +upload /tmp/ome-memory-dump.pgdump \
  --name "ome-memory-$(date +%Y%m%d).pgdump" \
  --parent SHARED_FOLDER_ID

# 4. Clean up
rm /tmp/ome-memory-dump.pgdump
```

## Import from Google Drive

```bash
# 1. Find the dump file on Drive
gws drive files list --params "q=name contains 'ome-memory'" \
  --params "fields=files(id,name,modifiedTime)"

# 2. Download it (replace FILE_ID)
gws drive files download FILE_ID --params "alt=media" > /tmp/ome-memory-import.pgdump

# 3. Restore into local database (merges with existing data)
pg_restore -h localhost -p 5488 -U memory -d memory \
  --clean --if-exists --no-owner \
  /tmp/ome-memory-import.pgdump

# 4. Clean up
rm /tmp/ome-memory-import.pgdump
```

## Share with a teammate

```bash
# 1. Export your database
pg_dump -Fc -h localhost -p 5488 -U memory -d memory \
  -f /tmp/ome-memory-dump.pgdump

# 2. Upload to a shared Drive folder
gws drive +upload /tmp/ome-memory-dump.pgdump \
  --name "ome-memory-$(whoami)-$(date +%Y%m%d).pgdump" \
  --parent SHARED_FOLDER_ID

# 3. Tell your teammate to run the import steps above
```

## Merge two knowledge bases

If you want to combine your memories with a teammate's without overwriting:

```bash
# 1. Download their dump
gws drive files download FILE_ID --params "alt=media" > /tmp/teammate-dump.pgdump

# 2. Restore into a temporary database
docker run -d --name ome-memory-tmp \
  -e POSTGRES_USER=memory -e POSTGRES_PASSWORD=memory -e POSTGRES_DB=memory \
  -p 5489:5432 pgvector/pgvector:pg17
sleep 3
pg_restore -h localhost -p 5489 -U memory -d memory \
  --no-owner /tmp/teammate-dump.pgdump

# 3. Use the MCP memory_export on the temp DB, then memory_import on your DB
#    This deduplicates by content hash and re-embeds as needed
DATABASE_URL="postgresql://memory:memory@localhost:5489/memory" \
  uvx ome-memory-mcp  # connect to temp DB, call memory_export

# Then import the JSON into your main DB via memory_import

# 4. Clean up
docker stop ome-memory-tmp && docker rm ome-memory-tmp && docker volume rm -f $(docker volume ls -q --filter name=ome-memory-tmp)
rm /tmp/teammate-dump.pgdump
```

## Notes

- `pg_dump -Fc` uses custom format (compressed, supports selective restore)
- `--clean --if-exists` drops and recreates objects — safe for a full overwrite
- The pgvector extension and schema are included in the dump
- No password prompt: set `PGPASSWORD=memory` or use a `.pgpass` file
- Dump files are typically small (embeddings compress well) — a few MB for thousands of entries
