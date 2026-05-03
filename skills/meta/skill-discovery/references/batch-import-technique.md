# Batch Skill Import Technique

## Proven pattern for converting 50+ external skills

Used successfully in the 2026-05-03 session to import 65 pm-skills + 23 agency-agents + 39 antigravity skills.

```python
from hermes_tools import terminal, write_file
import os

BASE = "https://raw.githubusercontent.com/OWNER/REPO/main"

skill_paths = [
    "path/to/skill1/SKILL.md",
    "path/to/skill2/SKILL.md",
    # ... up to 100 paths
]

batch_size = 8
for i in range(0, len(skill_paths), batch_size):
    batch = skill_paths[i:i+batch_size]
    for p in batch:
        url = f"{BASE}/{p}"
        parts = p.split("/")
        category = parts[0]
        skill_name = parts[-2]
        
        result = terminal(f"curl -sL --max-time 10 '{url}' 2>/dev/null | head -200", timeout=15)
        content = result.get("output", "")
        
        if content and len(content) > 50:
            hermes_dir = f"/home/ubuntu/.hermes/skills/{category}/{skill_name}"
            os.makedirs(hermes_dir, exist_ok=True)
            desc = content.split("\n")[0].replace("#", "").strip()[:200]
            hermes_content = f"""---
name: {skill_name}
description: "{desc}"
version: 1.0.0
tags: [imported]
category: productivity
source: {BASE}
---

{content}
"""
            write_file(f"{hermes_dir}/SKILL.md", hermes_content)
```

## Key numbers
- Batch size: 8-10 files per curl round
- Expected failure rate: 10-20% on first pass (network hiccups)
- Retry failed files separately with longer timeouts
- Total time for 65 skills: ~105 seconds

## INDEX.md generation
After import, create a catalog:
```python
for root, dirs, files in os.walk(base_dir):
    if "SKILL.md" in files:
        # Extract description, add to index
```
