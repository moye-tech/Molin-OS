# System Audit Recipe — v5.0.0 Session Record

> 2026-05-11 · Session: Comprehensive system standardization audit
> Context: User requested "全面梳理，标准化，规划化，清除冗余"

## Audit Results Summary

| Metric | Before | After |
|:--|:--|:--|
| `__pycache__` directories | 96 | 0 |
| `.pyc` files | 565 | 0 |
| Empty `references/` dirs | 10 | 0 |
| `$HOME` literal dir bug | 1 | 0 |
| `.gitignore` trapped source files | 2 | 0 restored |
| Module imports | — | 16/16 ✅ |
| Git sync | — | `960b2db` → `62754b6` |

## .gitignore Fixes Applied

### Rule 1: `**/auth.*` → `**/auth.json` + `**/auth.env`
- **File trapped**: `molib/core/middleware/auth.py` (22 lines, FastAPI auth middleware)
- **Root cause**: Glob `**/auth.*` matched `auth.py` source code
- **Fix**: Narrow to credential extensions only

### Rule 2: `*token*` → `**/token.*` + `!**/token_manager.*`
- **File trapped**: `molib/integrations/feishu/token_manager.py` (83 lines, Feishu token manager)
- **Root cause**: Contains "token" in name → matched broad `*token*` glob
- **Fix**: Match only files named exactly `token.*` (e.g. `token.json`), exclude source files

### Verification command
```bash
# Find all .py files incorrectly ignored by gitignore
git ls-files --others --exclude-standard -i | grep '\.py$' | grep -v '__pycache__'

# Find which rule ignores a specific file
git check-ignore -v path/to/file.py
```

## $HOME Literal Directory Bug

**Discovery**: `find ~/Molin-OS -maxdepth 2 -name '$HOME'` found a real directory:
```
/Users/moye/Molin-OS/$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/10-Daily
```

**Root cause**: The obsidian_sync.py script initially used `Path(os.environ.get(...))` with a fallback that string-interpolated `$HOME` literally instead of using `Path.home()`.

**Fix applied**:
1. Deleted the literal `$HOME` directory tree
2. Changed obsidian_sync.py to read OBSIDIAN_VAULT_PATH from `.env` file directly with `Path.home()` expansion

## Empty Directory Bulk Cleanup

```bash
# Empty references/ directories from molin-skills clone
find . -type d -name 'references' -empty -exec rmdir {} \;

# Empty output subdirectories
for d in output/comfy output/voice output/reports output/stt; do
    [ -d "$d" ] && rmdir "$d"
done

# Empty storage subdirectories
for d in molib/storage/default/{sop,molin.db,logs,qdrant}; do
    [ -d "$d" ] && rmdir "$d"
done
```

## Module Import Test (all 16 passed)

```python
MODULES = [
    'molib', 'molib.__main__', 'molib.agencies',
    'molib.agencies.workers', 'molib.agencies.workers.base',
    'molib.agencies.workers.__init__', 'molib.agencies.workers.designer',
    'molib.agencies.smart_dispatcher', 'molib.agencies.handoff',
    'molib.agencies.handoff_register', 'molib.shared.env_loader',
    'molib.infra.molib_db', 'molib.infra.molib_mail',
    'molib.infra.molib_order', 'molib.infra.molib_analytics',
    'molib.infra.molib_comfy',
]
# Result: 16/16 ✅
```

## CLI Health Verification

```bash
python -m molib health
# → {"status": "ok", "version": "v5.0.0"}
```
