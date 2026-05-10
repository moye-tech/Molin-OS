---
name: hermes-tool-development
description: Patterns and pitfalls for developing new tools in the Hermes Agent codebase.
  Covers tool registration, SQLite test isolation, feature-gating, schema design,
  and registry integration.
version: 1.0.0
tags:
- hermes
- tool-development
- testing
- sqlite
- feature-flags
- patterns
metadata:
  hermes:
    molin_owner: CEO
min_hermes_version: 0.13.0
---

# Hermes Agent Tool Development

## Overview

Patterns for adding new tools to Hermes Agent, learned from implementing the Task system (6 tools) and Feature Flag system. These are specifically about Hermes's `tools/registry.py` pattern — not general MCP or OpenClaw skills.

## The Tool Registration Pattern

Every tool file in `tools/` calls `registry.register()` at module level:

```python
from tools.registry import registry, tool_error, tool_result

MY_TOOL_SCHEMA = {
    "name": "my_tool",
    "description": "What this tool does",
    "parameters": {
        "type": "object",
        "properties": {
            "param1": {
                "type": "string",
                "description": "Description of param1"
            },
        },
        "required": []
    }
}

def handle_my_tool(param1=None, **kwargs):
    if not param1:
        return tool_error("param1 is required")
    return tool_result({"result": f"Processed {param1}"})

def check_requirements():
    return True

registry.register(
    name="my_tool",
    toolset="my_toolset",
    schema=MY_TOOL_SCHEMA,
    handler=lambda args, **kw: handle_my_tool(param1=args.get("param1")),
    check_fn=check_requirements,
    emoji="🔧",
    description="Description shown in tool lists",
)
```

## Auto-Discovery

Tools are auto-discovered by `discover_builtin_tools()` in `model_tools.py`. It scans `tools/*.py` for files containing top-level `registry.register(...)` calls. No manual registration needed.

## SQLite Test Isolation

When a tool uses SQLite, tests must not share the default database path:

```python
# In store module, add env-var override path:
def _get_default_path() -> str:
    env = os.environ.get("TEST_MY_STORE_DB_PATH")
    return env if env else str(DEFAULT_DB_PATH)

# In test file:
@pytest.fixture(autouse=True)
def _fresh_store(tmp_path, monkeypatch):
    db_path = tmp_path / f"test_{uuid.uuid4().hex}.db"
    monkeypatch.setenv("TEST_MY_STORE_DB_PATH", str(db_path))
    store = MyStore()
    import tools.my_tool as mod
    original = mod._store
    mod._store = store
    yield store
    mod._store = original
```

## Feature Gating

```python
from hermes_cli.features import is_enabled

def check_requirements():
    return is_enabled("my_feature")
```

## Multi-Tool Files

```python
registry.register(name="tool_one", toolset="group", schema=..., ...)
registry.register(name="tool_two", toolset="group", schema=..., ...)
```

## Pitfalls

1. **Registry test set** — `tests/tools/test_registry.py` has a hardcoded `EXPECTED_BUILTIN_TOOLS` set. Update it when adding a new tool.
2. **SQLite shared state** — Always use env-var override for test DB isolation.
3. **Return consistency** — `tool_error()` and `tool_result()` return different shapes. Tests must handle both.
4. **Subagent context** — `delegate_task` subagents need explicit venv activation to run tests.