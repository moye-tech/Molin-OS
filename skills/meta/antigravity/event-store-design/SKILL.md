     1|---
     2|name: ag-event-store-design
     3|description: "Design and implement event stores for event-sourced systems. Use when building event sourcing infrastructure, choosing event store technologies, or im"
     4|version: 1.0.0
     5|tags: [antigravity, devops]
     6|category: software-development
     7|source: https://github.com/sickn33/antigravity-awesome-skills
     8|---
     9|
    10|---
    11|name: event-store-design
    12|description: "Design and implement event stores for event-sourced systems. Use when building event sourcing infrastructure, choosing event store technologies, or implementing event persistence patterns."
    13|risk: unknown
    14|source: community
    15|date_added: "2026-02-27"
    16|---
    17|
    18|# Event Store Design
    19|
    20|Comprehensive guide to designing event stores for event-sourced applications.
    21|
    22|## Do not use this skill when
    23|
    24|- The task is unrelated to event store design
    25|- You need a different domain or tool outside this scope
    26|
    27|## Instructions
    28|
    29|- Clarify goals, constraints, and required inputs.
    30|- Apply relevant best practices and validate outcomes.
    31|- Provide actionable steps and verification.
    32|- If detailed examples are required, open `resources/implementation-playbook.md`.
    33|
    34|## Use this skill when
    35|
    36|- Designing event sourcing infrastructure
    37|- Choosing between event store technologies
    38|- Implementing custom event stores
    39|- Optimizing event storage and retrieval
    40|- Setting up event store schemas
    41|- Planning for event store scaling
    42|
    43|## Core Concepts
    44|
    45|### 1. Event Store Architecture
    46|
    47|```
    48|┌─────────────────────────────────────────────────────┐
    49|│                    Event Store                       │
    50|├─────────────────────────────────────────────────────┤
    51|│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
    52|│  │   Stream 1   │  │   Stream 2   │  │   Stream 3   │ │
    53|│  │ (Aggregate)  │  │ (Aggregate)  │  │ (Aggregate)  │ │
    54|│  ├─────────────┤  ├─────────────┤  ├─────────────┤ │
    55|│  │ Event 1     │  │ Event 1     │  │ Event 1     │ │
    56|│  │ Event 2     │  │ Event 2     │  │ Event 2     │ │
    57|│  │ Event 3     │  │ ...         │  │ Event 3     │ │
    58|│  │ ...         │  │             │  │ Event 4     │ │
    59|│  └─────────────┘  └─────────────┘  └─────────────┘ │
    60|├─────────────────────────────────────────────────────┤
    61|│  Global Position: 1 → 2 → 3 → 4 → 5 → 6 → ...     │
    62|└─────────────────────────────────────────────────────┘
    63|```
    64|
    65|### 2. Event Store Requirements
    66|
    67|| Requirement       | Description                        |
    68|| ----------------- | ---------------------------------- |
    69|| **Append-only**   | Events are immutable, only appends |
    70|| **Ordered**       | Per-stream and global ordering     |
    71|| **Versioned**     | Optimistic concurrency control     |
    72|| **Subscriptions** | Real-time event notifications      |
    73|| **Idempotent**    | Handle duplicate writes safely     |
    74|
    75|## Technology Comparison
    76|
    77|| Technology       | Best For                  | Limitations                      |
    78|| ---------------- | ------------------------- | -------------------------------- |
    79|| **EventStoreDB** | Pure event sourcing       | Single-purpose                   |
    80|| **PostgreSQL**   | Existing Postgres stack   | Manual implementation            |
    81|| **Kafka**        | High-throughput streaming | Not ideal for per-stream queries |
    82|| **DynamoDB**     | Serverless, AWS-native    | Query limitations                |
    83|| **Marten**       | .NET ecosystems           | .NET specific                    |
    84|
    85|## Templates
    86|
    87|### Template 1: PostgreSQL Event Store Schema
    88|
    89|```sql
    90|-- Events table
    91|CREATE TABLE events (
    92|    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    93|    stream_id VARCHAR(255) NOT NULL,
    94|    stream_type VARCHAR(255) NOT NULL,
    95|    event_type VARCHAR(255) NOT NULL,
    96|    event_data JSONB NOT NULL,
    97|    metadata JSONB DEFAULT '{}',
    98|    version BIGINT NOT NULL,
    99|    global_position BIGSERIAL,
   100|    created_at TIMESTAMPTZ DEFAULT NOW(),
   101|
   102|    CONSTRAINT unique_stream_version UNIQUE (stream_id, version)
   103|);
   104|
   105|-- Index for stream queries
   106|CREATE INDEX idx_events_stream_id ON events(stream_id, version);
   107|
   108|-- Index for global subscription
   109|CREATE INDEX idx_events_global_position ON events(global_position);
   110|
   111|-- Index for event type queries
   112|CREATE INDEX idx_events_event_type ON events(event_type);
   113|
   114|-- Index for time-based queries
   115|CREATE INDEX idx_events_created_at ON events(created_at);
   116|
   117|-- Snapshots table
   118|CREATE TABLE snapshots (
   119|    stream_id VARCHAR(255) PRIMARY KEY,
   120|    stream_type VARCHAR(255) NOT NULL,
   121|    snapshot_data JSONB NOT NULL,
   122|    version BIGINT NOT NULL,
   123|    created_at TIMESTAMPTZ DEFAULT NOW()
   124|);
   125|
   126|-- Subscriptions checkpoint table
   127|CREATE TABLE subscription_checkpoints (
   128|    subscription_id VARCHAR(255) PRIMARY KEY,
   129|    last_position BIGINT NOT NULL DEFAULT 0,
   130|    updated_at TIMESTAMPTZ DEFAULT NOW()
   131|);
   132|```
   133|
   134|### Template 2: Python Event Store Implementation
   135|
   136|```python
   137|from dataclasses import dataclass, field
   138|from datetime import datetime
   139|from typing import Any, Optional, List
   140|from uuid import UUID, uuid4
   141|import json
   142|import asyncpg
   143|
   144|@dataclass
   145|class Event:
   146|    stream_id: str
   147|    event_type: str
   148|    data: dict
   149|    metadata: dict = field(default_factory=dict)
   150|    event_id: UUID = field(default_factory=uuid4)
   151|    version: Optional[int] = None
   152|    global_position: Optional[int] = None
   153|    created_at: datetime = field(default_factory=datetime.utcnow)
   154|
   155|
   156|class EventStore:
   157|    def __init__(self, pool: asyncpg.Pool):
   158|        self.pool = pool
   159|
   160|    async def append_events(
   161|        self,
   162|        stream_id: str,
   163|        stream_type: str,
   164|        events: List[Event],
   165|        expected_version: Optional[int] = None
   166|    ) -> List[Event]:
   167|        """Append events to a stream with optimistic concurrency."""
   168|        async with self.pool.acquire() as conn:
   169|            async with conn.transaction():
   170|                # Check expected version
   171|                if expected_version is not None:
   172|                    current = await conn.fetchval(
   173|                        "SELECT MAX(version) FROM events WHERE stream_id = $1",
   174|                        stream_id
   175|                    )
   176|                    current = current or 0
   177|                    if current != expected_version:
   178|                        raise ConcurrencyError(
   179|                            f"Expected version {expected_version}, got {current}"
   180|                        )
   181|
   182|                # Get starting version
   183|                start_version = await conn.fetchval(
   184|                    "SELECT COALESCE(MAX(version), 0) + 1 FROM events WHERE stream_id = $1",
   185|                    stream_id
   186|                )
   187|
   188|                # Insert events
   189|                saved_events = []
   190|                for i, event in enumerate(events):
   191|                    event.version = start_version + i
   192|                    row = await conn.fetchrow(
   193|                        """
   194|                        INSERT INTO events (id, stream_id, stream_type, event_type,
   195|                                          event_data, metadata, version, created_at)
   196|                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
   197|                        RETURNING global_position
   198|                        """,
   199|                        event.event_id,
   200|                        stream_id,
   201|                        stream_type,
   202|                        event.event_type,
   203|                        json.dumps(event.data),
   204|                        json.dumps(event.metadata),
   205|                        event.version,
   206|                        event.created_at
   207|                    )
   208|                    event.global_position = row['global_position']
   209|                    saved_events.append(event)
   210|