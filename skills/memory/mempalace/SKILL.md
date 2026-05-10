---

name: mempalace
description: Enhanced semantic memory backend using MemPalace — verbatim storage, semantic search, knowledge graph, cross-session correlation, and automatic memory consolidation. Supersedes the built-in file-based memory (MEMORY.md/USER.md) for advanced operations.
metadata:
  hermes:
    molin_owner: 墨脑（知识管理）
---

# MemPalace — Enhanced Memory Backend for Hermes

## Overview

MemPalace (v3.3.4) is an open-source AI memory system that stores **every word verbatim** in a local ChromaDB vector database. It provides:

- **Semantic search** (BM25 + vector hybrid, 96.6% R@5 on LongMemEval)
- **Knowledge graph** (temporal entity-relationship store, SQLite-backed)
- **Cross-wing tunnels** (connect related topics across projects)
- **L0-L3 memory wake-up** (4-layer stack for system prompt injection)
- **Write-ahead log** (audit trail for every write operation)

**Location:** `~/.hermes/skills/intelligence/memory/mempalace/scripts/`

**Palace data:** `~/.mempalace/palace/` (configurable via `MEMPALACE_PALACE_PATH`)

**Default Hermes memory** (`MEMORY.md` / `USER.md`) **is still injected** at startup. MemPalace adds *semantic search and correlation* on top of that — use both.

---

## Quick Start

### 1. Initialize the Palace

```bash
~/.hermes/hermes-agent/venv/bin/python3 \
  ~/.hermes/skills/intelligence/memory/mempalace/scripts/mempalace_helper.py init
```

This creates:
- `~/.mempalace/config.json` — configuration
- `~/.mempalace/palace/` — ChromaDB vector store
- `~/.mempalace/knowledge_graph.sqlite3` — entity-relationship graph

### 2. Import Existing Hermes Memory

```bash
~/.hermes/hermes-agent/venv/bin/python3 \
  ~/.hermes/skills/intelligence/memory/mempalace/scripts/mempalace_helper.py sync-from-hermes
```

This imports every entry from `MEMORY.md` and `USER.md` as individual drawers in the `hermes_memory` wing, making them searchable semantically.

### 3. Test Semantic Search

```bash
~/.hermes/hermes-agent/venv/bin/python3 \
  ~/.hermes/skills/intelligence/memory/mempalace/scripts/mempalace_helper.py search "user preferences or project conventions"
```

---

## Conceptual Model: The Palace

MemPalace organizes memories using an architectural metaphor:

| Concept | Meaning | Example |
|---------|---------|---------|
| **Palace** | Your entire memory store | `~/.mempalace/palace/` |
| **Wing** | Broad category / project | `hermes_memory`, `user_profile`, `project_hermes`, `python_tooling` |
| **Room** | Specific topic or area | `agent_notes`, `user_preferences`, `api_design`, `bug_fixes` |
| **Drawer** | A single verbatim text chunk | One memory entry, conversation snippet, or fact |
| **Closet** | Compact topic index (AAAK) | Auto-generated pointers to relevant drawers |
| **Tunnel** | Cross-wing connection | Links `api_design` in wing_a to `database_schema` in wing_b |

---

## Core Operations

### Semantic Search (Beyond Keyword Matching)

Unlike Hermes' built-in memory (exact substring matching), MemPalace uses **hybrid search** combining:
1. **Vector similarity** — finds conceptually related content even with different wording
2. **BM25 keyword ranking** — ensures exact term matches are boosted
3. **Closet boost** — uses pre-computed topic indexes for ranking signal

```bash
# Basic search
mempalace_helper.py search "database connection pooling"

# Scoped to a wing/project
mempalace_helper.py search "authentication flow" --wing project_hermes

# Scoped to a specific room
mempalace_helper.py search "error handling" --room bug_fixes

# Adjust result count
mempalace_helper.py search "test infrastructure" --limit 10
```

### Cross-Session Memory Correlation

MemPalace automatically correlates information across sessions because all drawers live in the same vector space. A search naturally finds related content regardless of when it was stored:

```python
# Same search finds content from any session
search_memories("deployment pipeline", palace_path=palace_path)
# Returns: [drawer from session A, drawer from session B, ...]
```

### Knowledge Graph (Structured Relationships)

The knowledge graph stores **temporal entity-relationship triples** — facts about people, projects, and their relationships with validity windows.

```bash
# Add a relationship
mempalace_helper.py kg-add "User" "works_on" "Project Hermes"

# Add a personal fact
mempalace_helper.py kg-add "User" "prefers" "vim for editing"

# Query everything known about an entity
mempalace_helper.py kg-query "User"
```

The knowledge graph supports:
- **Temporal validity**: facts have `valid_from` / `valid_to` dates
- **Source references**: each triple links back to the verbatim drawer
- **Entity disambiguation**: name normalization via `people_map.json`

### Memory Importance Scoring

MemPalace doesn't assign explicit importance scores, but the **hybrid rank score** from `search_memories()` gives a composite relevance signal:

```python
result = search_memories(query, palace_path)
for hit in result["results"]:
    print(f"Drawer: {hit['wing']}/{hit['room']}")
    print(f"  Similarity: {hit['similarity']}")       # 0.0-1.0 range
    print(f"  BM25 score: {hit['bm25_score']}")         # keyword match strength
    print(f"  Closet boost: {hit['closet_boost']}")     # topical match bonus
    print(f"  Matched via: {hit['matched_via']}")        # "drawer", "drawer+closet"
```

The `similarity` field (higher = more relevant) serves as an importance indicator. You can also filter by `max_distance` to require a minimum similarity threshold.

### Automatic Memory Consolidation

**L0-L3 Memory Wake-Up Stack:**

The `wake-up` action generates compact context for system prompt injection:

```bash
mempalace_helper.py wake-up
```

This produces:
- **Layer 0 (~100 tokens)**: Identity — who the agent is
- **Layer 1 (~500-800 tokens)**: Essential story — top moments from the palace, condensed

**Closet auto-indexing:** When you add drawers via `mine`, MemPalace automatically builds compact `closet` entries (topic indexes) that enable faster semantic retrieval without scanning every drawer.

**Auto-save hooks:** MemPalace supports background hooks for periodic saves. For Hermes, run `status` before context compression to capture the current state.

---

## Python API Reference

The helper script wraps these key MemPalace Python APIs. You can also call them directly:

```python
# ── Semantic Search (the most important API) ──
from mempalace.searcher import search_memories

result = search_memories(
    query="deployment pipeline configuration",
    palace_path="~/.mempalace/palace",
    wing=None,          # Optional: scope to a wing
    room=None,          # Optional: scope to a room
    n_results=5,        # Max results
    max_distance=0.0,   # Cosine distance threshold (0=identical, 1=orthogonal)
)
# result = {
#   "query": "...",
#   "filters": {"wing": None, "room": None},
#   "results": [
#       {
#           "text": "verbatim content...",
#           "wing": "hermes_memory",
#           "room": "agent_notes",
#           "source_file": "MEMORY.md",
#           "similarity": 0.89,
#           "distance": 0.11,
#           "closet_boost": 0.25,
#           "bm25_score": 2.15,
#           "matched_via": "drawer+closet",
#       },
#   ]
# }


# ── Palace Operations ──
from mempalace.palace import get_collection
col = get_collection("~/.mempalace/palace", create=True)

# Add a drawer with metadata
import hashlib
from datetime import datetime
col.upsert(
    ids=[f"drawer_{wing}_{room}_{hashlib.sha256(content.encode()).hexdigest()[:24]}"],
    documents=[content],
    metadatas=[{
        "wing": "hermes_memory",
        "room": "agent_notes",
        "source_file": "hermes_agent",
        "chunk_index": 0,
        "added_by": "hermes_agent",
        "filed_at": datetime.now().isoformat(),
    }],
)


# ── Knowledge Graph ──
from mempalace.knowledge_graph import KnowledgeGraph
kg = KnowledgeGraph(db_path="~/.mempalace/knowledge_graph.sqlite3")

# Add facts
kg.add_triple("User", "works_on", "Hermes Agent", 
              valid_from="2025-01-01")
kg.add_triple("User", "prefers", "Python",
              valid_from="2025-01-01")

# Query
from datetime import date
result = kg.query_entity("User")
# Returns dict of {"as_subject": [...triples...], "as_object": [...triples...]}

# Temporally scoped query
result = kg.query_entity("User", as_of="2026-01-15")

# Invalidate a fact
kg.invalidate("User", "works_on", "Old Project", ended="2026-03-01")


# ── Layers (for system prompt injection) ──
from mempalace.layers import Layer0, Layer1
l0 = Layer0()
identity = l0.render()  # ~100 tokens

l1 = Layer1(palace_path="~/.mempalace/palace")
story = l1.generate()   # ~500-800 tokens

# Combine for system prompt injection
memory_block = f"{identity}\n\n{story}"
```

---

## Use Cases

### When to use MemPalace instead of built-in memory

| Situation | Built-in Memory | MemPalace |
|-----------|----------------|-----------|
| Simple fact storage | ✓ (add/replace/remove) | ✓ (add drawers) |
| Finding past info by keyword | ✓ (read all, grep) | ✓ (semantic search) |
| "What did we decide about X?" | ✗ (must remember exact phrasing) | ✓ (conceptual search) |
| Cross-session correlations | ✗ (flat file, no indexing) | ✓ (vector search finds related content) |
| Relationship tracking (who knows what) | ✗ | ✓ (knowledge graph) |
| Importance-weighted retrieval | ✗ | ✓ (similarity + BM25 scores) |
| Automatic topic indexing | ✗ | ✓ (closets built during mine) |

### Integration Pattern

At session start:
1. Hermes injects `MEMORY.md` / `USER.md` (built-in — always happens)
2. **Optionally**: call `mempalace_helper.py wake-up` to get L0+L1 context
3. **Optionally**: call `mempalace_helper.py search "relevant topic"` for on-demand retrieval

During session:
- Use `mempalace_helper.py add <wing> <room>` to file important facts
- Use `mempalace_helper.py search <query>` before answering questions about past decisions
- Use `mempalace_helper.py kg-add` for structured relationship facts

At session end:
- Bulk sync important insights: `mempalace_helper.py add hermes_memory session_summary < content.txt`

---

## References

- **GitHub:** https://github.com/MemPalace/mempalace
- **Docs:** https://mempalaceofficial.com/
- **Python API docs:** https://mempalaceofficial.com/reference/python-api.html
- **MCP tools:** https://mempalaceofficial.com/reference/mcp-tools.html
- **Helper script:** `~/.hermes/skills/intelligence/memory/mempalace/scripts/mempalace_helper.py`
