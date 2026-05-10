#!/usr/bin/env python3
"""
MemPalace Helper — Enhanced Memory Backend for Hermes Agent
============================================================

Provides a Python API wrapper around the MemPalace library for semantic
memory operations beyond Hermes' built-in file-based memory.

Usage:
    python mempalace_helper.py <action> [args...]

Actions:
    init                    Initialize a new palace
    status                  Show palace status (drawer count, wings, rooms)
    add     <wing> <room>   Add a drawer (reads content from stdin)
    search  <query>         Semantic search across the palace
    list-wings              List all wings with drawer counts
    list-rooms [wing]       List rooms (optionally within a wing)
    forget  <drawer_id>     Delete a specific drawer by ID
    kg-add  <subj> <pred> <obj>  Add a knowledge graph triple
    kg-query <entity>       Query knowledge graph for an entity
    mine    <directory>     Mine a project directory into the palace
    sync-from-hermes        Import MEMORY.md / USER.md as wing drawers
    wake-up                 Generate L0+L1 context for system prompt injection

Environment:
    MEMPALACE_PALACE_PATH   Path to the palace (default: ~/.mempalace/palace)
    HERMES_HOME             Path to Hermes home (default: ~/.hermes)
"""

import json
import os
import sys
import textwrap

# ── Resolve paths ──────────────────────────────────────────────────────────

HERMES_HOME = os.path.expanduser(
    os.environ.get("HERMES_HOME", "~/.hermes")
)
PALACE_PATH = os.path.expanduser(
    os.environ.get("MEMPALACE_PALACE_PATH", "~/.mempalace/palace")
)
CONFIG_DIR = os.path.expanduser("~/.mempalace")

# Ensure the import works from venv
try:
    import mempalace
    from mempalace.searcher import search_memories
    from mempalace.config import (
        MempalaceConfig,
        sanitize_name,
        sanitize_content,
    )
    from mempalace.knowledge_graph import KnowledgeGraph
    from mempalace.palace import get_collection
    from mempalace.layers import Layer0, Layer1
except ImportError:
    print("ERROR: mempalace not installed. Run: pip install mempalace", file=sys.stderr)
    sys.exit(1)


# ── Helpers ────────────────────────────────────────────────────────────────


def _get_col():
    """Get the palace collection, creating it if needed."""
    return get_collection(PALACE_PATH, create=True)


def _get_kg():
    """Get the knowledge graph instance."""
    kg_path = os.path.join(CONFIG_DIR, "knowledge_graph.sqlite3")
    return KnowledgeGraph(db_path=kg_path)


def _ensure_palace():
    """Ensure palace directory and default config exist."""
    os.makedirs(PALACE_PATH, exist_ok=True)
    cfg = MempalaceConfig()
    cfg.init()
    return cfg


def _render_results(results_dict: dict) -> str:
    """Format search results into a readable string."""
    results = results_dict.get("results", [])
    if not results:
        return "No results found."

    lines = [
        f"Query: {results_dict.get('query', '?')}",
        f"Results: {len(results)}",
        "─" * 60,
    ]
    for i, r in enumerate(results, 1):
        lines.extend([
            f"\n[{i}] {r.get('wing', '?')} / {r.get('room', '?')}",
            f"    Similarity: {r.get('similarity', '?')}",
            f"    Source: {r.get('source_file', '?')}",
            f"    Boost: {r.get('closet_boost', 0)}  Matched: {r.get('matched_via', '?')}",
            "",
        ])
        text = r.get("text", "")
        # Indent and wrap the verbatim content
        for line in text.strip().split("\n")[:20]:
            lines.append(f"    {line}")
        if len(text.split("\n")) > 20:
            lines.append("    [...truncated]")
        lines.append("")
    return "\n".join(lines)


# ── Actions ────────────────────────────────────────────────────────────────


def action_init(args):
    """Initialize a new palace."""
    cfg = _ensure_palace()
    col = _get_col()
    # Also initialize KG
    kg = _get_kg()
    print(json.dumps({
        "success": True,
        "palace_path": PALACE_PATH,
        "config_file": str(cfg._config_file),
        "collection": "mempalace_drawers" if col else None,
        "knowledge_graph": kg.db_path,
    }, indent=2))


def action_status(args):
    """Show palace status."""
    _ensure_palace()
    try:
        col = _get_col()
        # Get all metadata for counts
        all_meta = col.get(include=["metadatas"]) if col else {"ids": [], "metadatas": []}
        ids = all_meta.get("ids", [])
        metadatas = all_meta.get("metadatas", [])

        wings = {}
        rooms = {}
        for m in metadatas:
            m = m or {}
            w = m.get("wing", "unknown")
            r = m.get("room", "unknown")
            wings[w] = wings.get(w, 0) + 1
            rooms[r] = rooms.get(r, 0) + 1

        print(json.dumps({
            "success": True,
            "palace_path": PALACE_PATH,
            "total_drawers": len(ids),
            "unique_wings": len(wings),
            "unique_rooms": len(rooms),
            "wings": dict(sorted(wings.items(), key=lambda x: -x[1])),
            "rooms": dict(sorted(rooms.items(), key=lambda x: -x[1])),
        }, indent=2))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}, indent=2))


def action_add(args):
    """Add a drawer. Usage: add <wing> <room> [content]

    If content is not provided, reads from stdin.
    """
    if len(args) < 2:
        print(json.dumps({"success": False, "error": "Usage: add <wing> <room> [content]"}))
        return

    wing = args[0]
    room = args[1]
    content = " ".join(args[2:]) if len(args) > 2 else sys.stdin.read().strip()

    if not content:
        print(json.dumps({"success": False, "error": "No content provided"}))
        return

    try:
        wing = sanitize_name(wing, "wing")
        room = sanitize_name(room, "room")
        content = sanitize_content(content)
    except ValueError as e:
        print(json.dumps({"success": False, "error": str(e)}))
        return

    _ensure_palace()
    col = _get_col()

    import hashlib
    from datetime import datetime

    drawer_id = (
        f"drawer_{wing}_{room}_"
        f"{hashlib.sha256((wing + room + content).encode()).hexdigest()[:24]}"
    )

    try:
        col.upsert(
            ids=[drawer_id],
            documents=[content],
            metadatas=[{
                "wing": wing,
                "room": room,
                "source_file": "hermes_memory",
                "chunk_index": 0,
                "added_by": "hermes_agent",
                "filed_at": datetime.now().isoformat(),
            }],
        )
        print(json.dumps({
            "success": True,
            "drawer_id": drawer_id,
            "wing": wing,
            "room": room,
            "content_length": len(content),
        }, indent=2))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}, indent=2))


def action_search(args):
    """Semantic search. Usage: search <query> [--wing WING] [--room ROOM] [--limit N]"""
    if not args:
        print(json.dumps({"success": False, "error": "Usage: search <query> [--wing WING] [--room ROOM] [--limit N]"}))
        return

    # Parse flags
    query_parts = []
    wing = None
    room = None
    limit = 5
    i = 0
    while i < len(args):
        if args[i] == "--wing" and i + 1 < len(args):
            wing = args[i + 1]
            i += 2
        elif args[i] == "--room" and i + 1 < len(args):
            room = args[i + 1]
            i += 2
        elif args[i] == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1])
            i += 2
        else:
            query_parts.append(args[i])
            i += 1

    query = " ".join(query_parts)
    if not query:
        print(json.dumps({"success": False, "error": "Query is required"}))
        return

    _ensure_palace()
    try:
        result = search_memories(
            query,
            palace_path=PALACE_PATH,
            wing=wing,
            room=room,
            n_results=limit,
        )
        # Also pretty-print the human-readable version
        print(_render_results(result))
        print("\n── JSON DATA ──")
        print(json.dumps(result, indent=2, default=str))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}, indent=2))


def action_list_wings(args):
    """List all wings with drawer counts."""
    _ensure_palace()
    try:
        col = _get_col()
        all_meta = col.get(include=["metadatas"])
        wings = {}
        for m in (all_meta.get("metadatas") or []):
            m = m or {}
            w = m.get("wing", "unknown")
            wings[w] = wings.get(w, 0) + 1

        print(json.dumps({
            "success": True,
            "wings": dict(sorted(wings.items(), key=lambda x: -x[1])),
        }, indent=2))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}, indent=2))


def action_list_rooms(args):
    """List rooms, optionally filtered by wing."""
    wing = args[0] if args else None
    _ensure_palace()
    try:
        col = _get_col()
        where = {"wing": wing} if wing else None
        kwargs = {"include": ["metadatas"]}
        if where:
            kwargs["where"] = where
        all_meta = col.get(**kwargs)
        rooms = {}
        for m in (all_meta.get("metadatas") or []):
            m = m or {}
            r = m.get("room", "unknown")
            rooms[r] = rooms.get(r, 0) + 1

        print(json.dumps({
            "success": True,
            "wing": wing or "all",
            "rooms": dict(sorted(rooms.items(), key=lambda x: -x[1])),
        }, indent=2))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}, indent=2))


def action_forget(args):
    """Delete a drawer by ID."""
    if not args:
        print(json.dumps({"success": False, "error": "Usage: forget <drawer_id>"}))
        return
    drawer_id = args[0]
    _ensure_palace()
    try:
        col = _get_col()
        col.delete(ids=[drawer_id])
        print(json.dumps({"success": True, "drawer_id": drawer_id}))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}, indent=2))


def action_kg_add(args):
    """Add a knowledge graph triple: kg-add <subject> <predicate> <object>"""
    if len(args) < 3:
        print(json.dumps({"success": False, "error": "Usage: kg-add <subject> <predicate> <object>"}))
        return
    subj, pred, obj = args[0], args[1], args[2]
    _ensure_palace()
    kg = _get_kg()
    try:
        kg.add_triple(subj, pred, obj)
        print(json.dumps({"success": True, "triple": {"subject": subj, "predicate": pred, "object": obj}}))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}, indent=2))


def action_kg_query(args):
    """Query knowledge graph for an entity."""
    if not args:
        print(json.dumps({"success": False, "error": "Usage: kg-query <entity_name>"}))
        return
    entity = args[0]
    _ensure_palace()
    kg = _get_kg()
    try:
        result = kg.query_entity(entity)
        if isinstance(result, dict):
            print(json.dumps(result, indent=2, default=str))
        else:
            print(result)
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}, indent=2))


def action_mine(args):
    """Mine a project directory. Usage: mine <directory> [--wing WING]"""
    if not args:
        print(json.dumps({"success": False, "error": "Usage: mine <directory> [--wing WING]"}))
        return

    directory = args[0]
    wing = None
    if "--wing" in args:
        idx = args.index("--wing")
        if idx + 1 < len(args):
            wing = args[idx + 1]

    _ensure_palace()
    try:
        from mempalace.miner import mine_project
        result = mine_project(directory, wing=wing)
        print(json.dumps({"success": True, "result": str(result)}, indent=2))
    except ImportError:
        print(json.dumps({
            "success": False,
            "error": "mine_project not directly importable — use CLI instead",
            "hint": f"cd {directory} && mempalace mine . --wing {wing or 'auto'}",
        }, indent=2))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}, indent=2))


def action_sync_from_hermes(args):
    """Import Hermes' MEMORY.md / USER.md as palace drawers.

    Each entry becomes a drawer in the 'hermes_memory' wing, under
    'agent_notes' or 'user_profile' rooms.
    """
    _ensure_palace()
    col = _get_col()
    memory_dir = os.path.join(HERMES_HOME, "memories")

    imported = 0
    for filename, room in [("MEMORY.md", "agent_notes"), ("USER.md", "user_profile")]:
        filepath = os.path.join(memory_dir, filename)
        if not os.path.exists(filepath):
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()

        if not content:
            continue

        # Split by the § delimiter Hermes uses
        import hashlib
        from datetime import datetime

        entries = [e.strip() for e in content.split("\n§\n") if e.strip()]
        for entry in entries:
            drawer_id = (
                f"drawer_hermes_memory_{room}_"
                f"{hashlib.sha256(entry.encode()).hexdigest()[:24]}"
            )
            try:
                col.upsert(
                    ids=[drawer_id],
                    documents=[entry],
                    metadatas=[{
                        "wing": "hermes_memory",
                        "room": room,
                        "source_file": f"hermes/{filename}",
                        "chunk_index": 0,
                        "added_by": "hermes_sync",
                        "filed_at": datetime.now().isoformat(),
                    }],
                )
                imported += 1
            except Exception:
                pass

    print(json.dumps({
        "success": True,
        "imported_drawers": imported,
        "from_files": ["MEMORY.md", "USER.md"],
    }, indent=2))


def action_wake_up(args):
    """Generate L0 (identity) + L1 (essential story) context.

    Output is formatted for system prompt injection.
    """
    _ensure_palace()

    wing = args[0] if args else None

    # Layer 0 — Identity
    l0 = Layer0()
    identity = l0.render()

    # Layer 1 — Essential Story
    l1 = Layer1(palace_path=PALACE_PATH, wing=wing)
    story = l1.generate()

    output = f"""{'=' * 60}
MEMORY OVERVIEW (MemPalace Wake-Up)
{'=' * 60}

{identity}

{story}

{'=' * 60
}"""
    print(output)


# ── Dispatch ────────────────────────────────────────────────────────────────

ACTIONS = {
    "init": action_init,
    "status": action_status,
    "add": action_add,
    "search": action_search,
    "list-wings": action_list_wings,
    "list-rooms": action_list_rooms,
    "forget": action_forget,
    "kg-add": action_kg_add,
    "kg-query": action_kg_query,
    "mine": action_mine,
    "sync-from-hermes": action_sync_from_hermes,
    "wake-up": action_wake_up,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("--help", "-h"):
        print(__doc__)
        return

    action = sys.argv[1]
    args = sys.argv[2:]

    if action not in ACTIONS:
        print(f"Unknown action: {action}", file=sys.stderr)
        print(f"Available: {', '.join(sorted(ACTIONS.keys()))}", file=sys.stderr)
        sys.exit(1)

    try:
        ACTIONS[action](args)
    except Exception as e:
        print(json.dumps({"success": False, "error": f"{type(e).__name__}: {e}"}, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
