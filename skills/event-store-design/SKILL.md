---
name: ag-event-store-design
description: Design and implement event stores for event-sourced systems. Use when
  building event sourcing infrastructure, choosing event store technologies, or im
version: 1.0.0
tags:
- antigravity
- devops
category: software-development
source: https://github.com/sickn33/antigravity-awesome-skills
min_hermes_version: 0.13.0
---

---
name: event-store-design
description: "Design and implement event stores for event-sourced systems. Use when building event sourcing infrastructure, choosing event store technologies, or implementing event persistence patterns."
risk: unknown
source: community
date_added: "2026-02-27"
metadata:
  hermes:
    molin_owner: 墨码（软件工坊）
---

# Event Store Design

Comprehensive guide to designing event stores for event-sourced applications.

## Do not use this skill when

- The task is unrelated to event store design
- You need a different domain or tool outside this scope

## Instructions

- Clarify goals, constraints, and required inputs.
- Apply relevant best practices and validate outcomes.
- Provide actionable steps and verification.
- If detailed examples are required, open `resources/implementation-playbook.md`.

## Use this skill when

- Designing event sourcing infrastructure
- Choosing between event store technologies
- Implementing custom event stores
- Optimizing event storage and retrieval
- Setting up event store schemas
- Planning for event store scaling

## Core Concepts

### 1. Event Store Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Event Store                       │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │   Stream 1   │  │   Stream 2   │  │   Stream 3   │ │
│  │ (Aggregate)  │  │ (Aggregate)  │  │ (Aggregate)  │ │
│  ├─────────────┤  ├─────────────┤  ├─────────────┤ │
│  │ Event 1     │  │ Event 1     │  │ Event 1     │ │
│  │ Event 2     │  │ Event 2     │  │ Event 2     │ │
│  │ Event 3     │  │ ...         │  │ Event 3     │ │
│  │ ...         │  │             │  │ Event 4     │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
├─────────────────────────────────────────────────────┤
│  Global Position: 1 → 2 → 3 → 4 → 5 → 6 → ...     │
└─────────────────────────────────────────────────────┘
```

### 2. Event Store Requirements

| Requirement       | Description                        |
| ----------------- | ---------------------------------- |
| **Append-only**   | Events are immutable, only appends |
| **Ordered**       | Per-stream and global ordering     |
| **Versioned**     | Optimistic concurrency control     |
| **Subscriptions** | Real-time event notifications      |
| **Idempotent**    | Handle duplicate writes safely     |

## Technology Comparison

| Technology       | Best For                  | Limitations                      |
| ---------------- | ------------------------- | -------------------------------- |
| **EventStoreDB** | Pure event sourcing       | Single-purpose                   |
| **PostgreSQL**   | Existing Postgres stack   | Manual implementation            |
| **Kafka**        | High-throughput streaming | Not ideal for per-stream queries |
| **DynamoDB**     | Serverless, AWS-native    | Query limitations                |
| **Marten**       | .NET ecosystems           | .NET specific                    |

## Templates

### Template 1: PostgreSQL Event Store Schema

```sql
-- Events table
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stream_id VARCHAR(255) NOT NULL,
    stream_type VARCHAR(255) NOT NULL,
    event_type VARCHAR(255) NOT NULL,
    event_data JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    version BIGINT NOT NULL,
    global_position BIGSERIAL,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_stream_version UNIQUE (stream_id, version)
);

-- Index for stream queries
CREATE INDEX idx_events_stream_id ON events(stream_id, version);

-- Index for global subscription
CREATE INDEX idx_events_global_position ON events(global_position);

-- Index for event type queries
CREATE INDEX idx_events_event_type ON events(event_type);

-- Index for time-based queries
CREATE INDEX idx_events_created_at ON events(created_at);

-- Snapshots table
CREATE TABLE snapshots (
    stream_id VARCHAR(255) PRIMARY KEY,
    stream_type VARCHAR(255) NOT NULL,
    snapshot_data JSONB NOT NULL,
    version BIGINT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Subscriptions checkpoint table
CREATE TABLE subscription_checkpoints (
    subscription_id VARCHAR(255) PRIMARY KEY,
    last_position BIGINT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Template 2: Python Event Store Implementation

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, List
from uuid import UUID, uuid4
import json
import asyncpg

@dataclass
class Event:
    stream_id: str
    event_type: str
    data: dict
    metadata: dict = field(default_factory=dict)
    event_id: UUID = field(default_factory=uuid4)
    version: Optional[int] = None
    global_position: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


class EventStore:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def append_events(
        self,
        stream_id: str,
        stream_type: str,
        events: List[Event],
        expected_version: Optional[int] = None
    ) -> List[Event]:
        """Append events to a stream with optimistic concurrency."""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # Check expected version
                if expected_version is not None:
                    current = await conn.fetchval(
                        "SELECT MAX(version) FROM events WHERE stream_id = $1",
                        stream_id
                    )
                    current = current or 0
                    if current != expected_version:
                        raise ConcurrencyError(
                            f"Expected version {expected_version}, got {current}"
                        )

                # Get starting version
                start_version = await conn.fetchval(
                    "SELECT COALESCE(MAX(version), 0) + 1 FROM events WHERE stream_id = $1",
                    stream_id
                )

                # Insert events
                saved_events = []
                for i, event in enumerate(events):
                    event.version = start_version + i
                    row = await conn.fetchrow(
                        """
                        INSERT INTO events (id, stream_id, stream_type, event_type,
                                          event_data, metadata, version, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        RETURNING global_position
                        """,
                        event.event_id,
                        stream_id,
                        stream_type,
                        event.event_type,
                        json.dumps(event.data),
                        json.dumps(event.metadata),
                        event.version,
                        event.created_at
                    )
                    event.global_position = row['global_position']
                    saved_events.append(event)