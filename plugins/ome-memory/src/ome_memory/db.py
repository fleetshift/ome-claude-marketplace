from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://memory:memory@localhost:5488/memory"
)

EMBEDDING_DIM = 384  # all-MiniLM-L6-v2


def get_conn() -> psycopg.Connection:
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def ensure_schema(conn: psycopg.Connection) -> None:
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'general',
            tags TEXT[] NOT NULL DEFAULT '{{}}',
            project TEXT NOT NULL DEFAULT '',
            source_agent TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            metadata JSONB NOT NULL DEFAULT '{{}}',
            embedding vector({EMBEDDING_DIM}) NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_memories_content_hash
        ON memories (content_hash)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_memories_type ON memories (type)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_memories_project ON memories (project)
    """)
    conn.commit()


def content_hash(content: str) -> str:
    return hashlib.sha256(content.strip().encode()).hexdigest()


def store(
    conn: psycopg.Connection,
    content: str,
    embedding: list[float],
    *,
    type: str = "general",
    tags: list[str] | None = None,
    project: str = "",
    source_agent: str = "",
    metadata: dict[str, Any] | None = None,
) -> dict:
    entry_id = uuid4().hex[:16]
    c_hash = content_hash(content)
    now = datetime.now(timezone.utc)

    existing = conn.execute(
        "SELECT id, tags, metadata FROM memories WHERE content_hash = %s",
        (c_hash,),
    ).fetchone()

    if existing:
        merged_tags = list(set((existing["tags"] or []) + (tags or [])))
        merged_meta = {**(existing["metadata"] or {}), **(metadata or {})}
        conn.execute(
            "UPDATE memories SET tags = %s, metadata = %s WHERE id = %s",
            (merged_tags, json.dumps(merged_meta), existing["id"]),
        )
        conn.commit()
        return {"id": existing["id"], "action": "merged", "content_hash": c_hash}

    conn.execute(
        """INSERT INTO memories
           (id, content, content_hash, type, tags, project, source_agent,
            created_at, metadata, embedding)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector)""",
        (
            entry_id,
            content,
            c_hash,
            type,
            tags or [],
            project,
            source_agent,
            now,
            json.dumps(metadata or {}),
            str(embedding),
        ),
    )
    conn.commit()
    return {"id": entry_id, "action": "created", "content_hash": c_hash}


def search_memories(
    conn: psycopg.Connection,
    query_embedding: list[float],
    *,
    limit: int = 10,
    type_filter: str | None = None,
    project_filter: str | None = None,
    tag_filter: str | None = None,
) -> list[dict]:
    emb_str = str(query_embedding)
    conditions = []
    params: list[Any] = []

    if type_filter:
        conditions.append("type = %s")
        params.append(type_filter)
    if project_filter:
        conditions.append("project = %s")
        params.append(project_filter)
    if tag_filter:
        conditions.append("%s = ANY(tags)")
        params.append(tag_filter)

    where = ""
    if conditions:
        where = "WHERE " + " AND ".join(conditions)

    params.append(limit)

    rows = conn.execute(
        f"""SELECT id, content, type, tags, project, source_agent,
                   created_at, metadata,
                   1 - (embedding <=> '{emb_str}'::vector) AS similarity
            FROM memories {where}
            ORDER BY embedding <=> '{emb_str}'::vector
            LIMIT %s""",
        params,
    ).fetchall()

    result = []
    for row in rows:
        r = dict(row)
        r["created_at"] = r["created_at"].isoformat() if r["created_at"] else None
        r["similarity"] = round(float(r["similarity"]), 4)
        result.append(r)
    return result


def list_memories(
    conn: psycopg.Connection,
    *,
    type_filter: str | None = None,
    project_filter: str | None = None,
    limit: int = 50,
) -> list[dict]:
    conditions = []
    params: list[Any] = []

    if type_filter:
        conditions.append("type = %s")
        params.append(type_filter)
    if project_filter:
        conditions.append("project = %s")
        params.append(project_filter)

    where = ""
    if conditions:
        where = "WHERE " + " AND ".join(conditions)

    params.append(limit)

    rows = conn.execute(
        f"""SELECT id, content, type, tags, project, source_agent,
                   created_at, metadata
            FROM memories {where}
            ORDER BY created_at DESC
            LIMIT %s""",
        params,
    ).fetchall()

    result = []
    for row in rows:
        r = dict(row)
        r["created_at"] = r["created_at"].isoformat() if r["created_at"] else None
        result.append(r)
    return result


def delete_memory(conn: psycopg.Connection, memory_id: str) -> bool:
    cur = conn.execute("DELETE FROM memories WHERE id = %s", (memory_id,))
    conn.commit()
    return cur.rowcount > 0


def export_all(conn: psycopg.Connection) -> list[dict]:
    rows = conn.execute(
        """SELECT id, content, content_hash, type, tags, project,
                  source_agent, created_at, metadata
           FROM memories ORDER BY created_at"""
    ).fetchall()
    result = []
    for row in rows:
        r = dict(row)
        r["created_at"] = r["created_at"].isoformat() if r["created_at"] else None
        result.append(r)
    return result


def import_memories(
    conn: psycopg.Connection,
    entries: list[dict],
    embed_fn,
) -> dict:
    created = 0
    skipped = 0

    for entry in entries:
        c_hash = content_hash(entry["content"])
        existing = conn.execute(
            "SELECT id FROM memories WHERE content_hash = %s", (c_hash,)
        ).fetchone()

        if existing:
            skipped += 1
            continue

        embedding = embed_fn(entry["content"])
        conn.execute(
            """INSERT INTO memories
               (id, content, content_hash, type, tags, project, source_agent,
                created_at, metadata, embedding)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector)""",
            (
                entry.get("id", uuid4().hex[:16]),
                entry["content"],
                c_hash,
                entry.get("type", "general"),
                entry.get("tags", []),
                entry.get("project", ""),
                entry.get("source_agent", ""),
                entry.get("created_at", datetime.now(timezone.utc).isoformat()),
                json.dumps(entry.get("metadata", {})),
                str(embedding),
            ),
        )
        created += 1

    conn.commit()
    return {"created": created, "skipped": skipped}
