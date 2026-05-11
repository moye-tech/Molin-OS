# pnpm + Corepack Pitfalls on macOS

## Problem 1: `corepack enable` needs sudo

```
Internal Error: EACCES: permission denied, symlink '../lib/node_modules/corepack/dist/pnpm.js' -> '/usr/local/bin/pnpm'
```

**Why:** `/usr/local/bin/pnpm` is owned by root on this Mac. Corepack tries to symlink there during `enable`.

**Fix:** Don't use `corepack enable`. Call corepack directly:
```bash
corepack pnpm@10.33.2 install
corepack pnpm@10.33.2 --version  # verify
```

## Problem 2: Version mismatch when running scripts

When `package.json` specifies `"packageManager": "pnpm@10.33.2"` but system pnpm is 11.0.9:

```
[ERROR] This project is configured to use 10.33.2 of pnpm. Your current pnpm is v11.0.9
Corepack invoked pnpm with this version, and pnpm does not switch versions when running under corepack.
```

**Why:** When corepack invokes pnpm@10.33.2, the inner pnpm detects that the outer (system) pnpm is 11.0.9 and refuses to proceed.

**Fix:** Use system pnpm directly for lifecycle scripts (`tools-dev`, etc.), corepack only for `install`:
```bash
# For install (no version check triggered):
corepack pnpm@10.33.2 install

# For scripts (use system pnpm, which auto-switches):
pnpm tools-dev start daemon
pnpm tools-dev status daemon
```

## Problem 3: Proxy interference with npm/pnpm

Clash Party proxy at 127.0.0.1:7890 can slow npm downloads to timeout. Always check:
```bash
env | grep -i proxy
```
If `https_proxy` or `HTTP_PROXY` is set, unset them before npm/pnpm install. Direct connection is faster for bulk package downloads.
