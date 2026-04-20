from __future__ import annotations

import json

from fastmcp import FastMCP

from . import db
from .embeddings import embed

mcp = FastMCP("ome-memory", instructions="""
Shared agent memory backed by PostgreSQL + pgvector.
Use memory_store to save knowledge, memory_search to find relevant entries.
Types: user, feedback, project, reference, general.
""")


@mcp.tool()
def memory_store(
    content: str,
    type: str = "general",
    tags: list[str] | None = None,
    project: str = "",
    source_agent: str = "",
    metadata: dict | None = None,
) -> str:
    """Store a knowledge entry in the shared memory.

    Automatically deduplicates by content hash. If the same content
    already exists, metadata and tags are merged additively.

    Args:
        content: The knowledge to store (will be embedded for semantic search)
        type: Category — user, feedback, project, reference, or general
        tags: Optional tags for filtering
        project: Project identifier for scoping
        source_agent: Which agent stored this entry
        metadata: Arbitrary key-value metadata
    """
    embedding = embed(content)
    conn = db.get_conn()
    try:
        result = db.store(
            conn,
            content,
            embedding,
            type=type,
            tags=tags,
            project=project,
            source_agent=source_agent,
            metadata=metadata,
        )
        return json.dumps(result)
    finally:
        conn.close()


@mcp.tool()
def memory_search(
    query: str,
    limit: int = 10,
    type: str | None = None,
    project: str | None = None,
    tag: str | None = None,
) -> str:
    """Search memory semantically. Returns entries ranked by similarity.

    Args:
        query: Natural language search query
        limit: Max results to return (default 10)
        type: Filter by type (user, feedback, project, reference, general)
        project: Filter by project identifier
        tag: Filter by tag
    """
    query_embedding = embed(query)
    conn = db.get_conn()
    try:
        results = db.search_memories(
            conn,
            query_embedding,
            limit=limit,
            type_filter=type,
            project_filter=project,
            tag_filter=tag,
        )
        return json.dumps(results, default=str)
    finally:
        conn.close()


@mcp.tool()
def memory_list(
    type: str | None = None,
    project: str | None = None,
    limit: int = 50,
) -> str:
    """List memory entries, newest first.

    Args:
        type: Filter by type
        project: Filter by project
        limit: Max results (default 50)
    """
    conn = db.get_conn()
    try:
        results = db.list_memories(
            conn, type_filter=type, project_filter=project, limit=limit
        )
        return json.dumps(results, default=str)
    finally:
        conn.close()


@mcp.tool()
def memory_delete(memory_id: str) -> str:
    """Delete a memory entry by ID.

    Args:
        memory_id: The ID of the entry to delete
    """
    conn = db.get_conn()
    try:
        deleted = db.delete_memory(conn, memory_id)
        return json.dumps({"deleted": deleted, "id": memory_id})
    finally:
        conn.close()


@mcp.tool()
def memory_export() -> str:
    """Export all memory entries as JSON for backup or sharing.

    Returns all entries without embeddings. Use with memory_import
    to transfer knowledge between instances.
    """
    conn = db.get_conn()
    try:
        entries = db.export_all(conn)
        return json.dumps(entries, default=str)
    finally:
        conn.close()


@mcp.tool()
def memory_import(entries_json: str) -> str:
    """Import memory entries additively. Deduplicates by content hash.

    Existing entries with the same content are skipped.
    New entries are embedded and stored.

    Args:
        entries_json: JSON array of memory entries (from memory_export)
    """
    entries = json.loads(entries_json)
    conn = db.get_conn()
    try:
        result = db.import_memories(conn, entries, embed)
        return json.dumps(result)
    finally:
        conn.close()


def main():
    conn = db.get_conn()
    try:
        db.ensure_schema(conn)
    finally:
        conn.close()
    mcp.run()


if __name__ == "__main__":
    main()
