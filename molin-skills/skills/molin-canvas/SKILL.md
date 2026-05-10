---
name: molin-canvas
description: Create and edit Molin Canvas files (.mcanvas) for visual knowledge mapping. Use when creating mind maps, flowcharts, knowledge graphs, or visual layouts of Molin-OS data.
version: 1.0.0
min_hermes_version: 0.13.0
dependencies: [molin-cli, molin-markdown]
tags: [molin-os, canvas, visualization, knowledge-graph, mindmap]
category: visualization
---

# Molin Canvas Skill

Create and edit Molin Canvas files (.mcanvas) — 对标 Obsidian JSON Canvas。

## File Structure

```json
{
  "nodes": [],
  "edges": [],
  "metadata": {
    "title": "My Canvas",
    "created": "2026-05-10T18:00:00+08:00",
    "version": "1.0.0"
  }
}
```

## Node Types

### Text Node
```json
{
  "id": "a1b2c3d4e5f6g7h8",
  "type": "text",
  "x": 0,
  "y": 0,
  "width": 300,
  "height": 200,
  "text": "## 墨麟OS 架构\n\n22 Workers, 20 Subsidiaries",
  "color": "1"
}
```

### Skill Node
```json
{
  "id": "b2c3d4e5f6g7h8i9",
  "type": "skill",
  "x": 400,
  "y": 0,
  "width": 250,
  "height": 150,
  "skill_id": "molin-mql",
  "show_description": true
}
```

### Worker Node
```json
{
  "id": "c3d4e5f6g7h8i9j0",
  "type": "worker",
  "x": 800,
  "y": 0,
  "width": 250,
  "height": 150,
  "worker_id": "content_writer",
  "show_status": true
}
```

### Data Node
```json
{
  "id": "d4e5f6g7h8i9j0k1",
  "type": "data",
  "x": 400,
  "y": 300,
  "width": 350,
  "height": 200,
  "mql_query": "FROM skills WHERE category = 'engineering' LIMIT 10",
  "view_type": "table"
}
```

### Note Node
```json
{
  "id": "e5f6g7h8i9j0k1l2",
  "type": "note",
  "x": 0,
  "y": 300,
  "width": 300,
  "height": 200,
  "note_path": "Projects/Molin-OS/Architecture.md"
}
```

## Edge Types

```json
{
  "id": "edge1",
  "fromNode": "a1b2c3d4e5f6g7h8",
  "fromSide": "right",
  "toNode": "b2c3d4e5f6g7h8i9",
  "toSide": "left",
  "label": "uses"
}
```

## Common Workflows

### 1. Create Architecture Diagram

```
1. Create .mcanvas file with base structure
2. Add text nodes for main components
3. Add worker/skill nodes for 墨麟 Workers
4. Connect with edges showing relationships
5. Set colors by category:
   - VP 营销: #FF6B6B (red)
   - VP 技术: #4ECDC4 (teal)
   - VP 运营: #45B7D1 (blue)
   - VP 财务: #96CEB4 (green)
   - VP 战略: #FFEAA7 (yellow)
6. Validate: check all edge references
```

### 2. Create Knowledge Map from MQL

```
1. Run MQL query to get entries
2. Create .mcanvas file
3. For each entry: create a node at calculated position
4. Group by category (horizontal bands)
5. Connect related items with edges
6. Validate JSON
```

### 3. Create Worker Dependency Graph

```bash
python -m molib canvas create --type worker-deps \
  --output ~/.hermes/canvas/worker-deps.mcanvas
```

## Node Color Presets

| Color | Hex | Use |
|-------|-----|-----|
| 1 | #EF4444 | Errors, critical |
| 2 | #F97316 | Warnings, attention |
| 3 | #EAB308 | In-progress, active |
| 4 | #22C55E | Success, complete |
| 5 | #3B82F6 | Info, neutral |
| 6 | #8B5CF6 | Special, creative |

## Layout Algorithms

- **grid** — evenly spaced grid
- **horizontal** — left-to-right flow
- **vertical** — top-to-bottom flow
- **radial** — center-outward
- **force** — force-directed graph
- **manual** — user-defined positions

## Python API

```python
from molib.shared.visual.canvas import MolinCanvas

# Create
canvas = MolinCanvas("Architecture Overview")

# Add nodes
canvas.add_text_node("Main", x=0, y=0, text="墨麟OS")
canvas.add_skill_node("MQL", x=300, y=0, skill_id="molin-mql")
canvas.add_worker_node("Writer", x=600, y=0, worker_id="content_writer")

# Connect
canvas.add_edge("Main", "MQL", label="uses")
canvas.add_edge("Main", "Writer", label="delegates to")

# Auto-layout
canvas.auto_layout("horizontal")

# Save
canvas.save("architecture.mcanvas")
```

## Validation

Before finalizing a canvas:
1. Parse JSON — ensure valid syntax
2. Check all node IDs are unique (16-char hex)
3. Verify all edge `fromNode`/`toNode` references exist
4. Check no nodes overlap too closely (< 20px gap)
5. Verify file size < 10MB

## Pitfalls

- Use `\n` for newlines in JSON strings — NOT `\\n`
- Node IDs must be unique across nodes AND edges
- X/Y coordinates are in pixels (0,0 = top-left)
- File paths in note nodes are relative to Obsidian vault root
- Large canvases (> 500 nodes) should use force layout
