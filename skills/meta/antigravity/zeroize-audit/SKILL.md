     1|---
     2|name: ag-zeroize-audit
     3|description: "Detects missing zeroization of sensitive data in source code and identifies zeroization removed by compiler optimizations, with assembly-level analysi"
     4|version: 1.0.0
     5|tags: [antigravity, general]
     6|category: software-development
     7|source: https://github.com/sickn33/antigravity-awesome-skills
     8|---
     9|
    10|---
    11|name: zeroize-audit
    12|description: "Detects missing zeroization of sensitive data in source code and identifies zeroization removed by compiler optimizations, with assembly-level analysis, and control-flow verification. Use for auditing C/C++/Rust code handling secrets, keys, passwords, or other sensitive data."
    13|allowed-tools:
    14|  - Read
    15|  - Grep
    16|  - Glob
    17|  - Bash
    18|  - Write
    19|  - Task
    20|  - AskUserQuestion
    21|  - mcp__serena__activate_project
    22|  - mcp__serena__find_symbol
    23|  - mcp__serena__find_referencing_symbols
    24|  - mcp__serena__get_symbols_overview
    25|risk: unknown
    26|source: community
    27|---
    28|
    29|# zeroize-audit — Claude Skill
    30|
    31|## When to Use
    32|- Auditing cryptographic implementations (keys, seeds, nonces, secrets)
    33|- Reviewing authentication systems (passwords, tokens, session data)
    34|- Analyzing code that handles PII or sensitive credentials
    35|- Verifying secure cleanup in security-critical codebases
    36|- Investigating memory safety of sensitive data handling
    37|
    38|## When NOT to Use
    39|- General code review without security focus
    40|- Performance optimization (unless related to secure wiping)
    41|- Refactoring tasks not related to sensitive data
    42|- Code without identifiable secrets or sensitive values
    43|
    44|---
    45|
    46|## Purpose
    47|Detect missing zeroization of sensitive data in source code and identify zeroization that is removed or weakened by compiler optimizations (e.g., dead-store elimination), with mandatory LLVM IR/asm evidence. Capabilities include:
    48|- Assembly-level analysis for register spills and stack retention
    49|- Data-flow tracking for secret copies
    50|- Heap allocator security warnings
    51|- Semantic IR analysis for loop unrolling and SSA form
    52|- Control-flow graph analysis for path coverage verification
    53|- Runtime validation test generation
    54|
    55|## Scope
    56|- Read-only against the target codebase (does not modify audited code; writes analysis artifacts to a temporary working directory).
    57|- Produces a structured report (JSON).
    58|- Requires valid build context (`compile_commands.json`) and compilable translation units.
    59|- "Optimized away" findings only allowed with compiler evidence (IR/asm diff).
    60|
    61|---
    62|
    63|## Inputs
    64|
    65|See `{baseDir}/schemas/input.json` for the full schema. Key fields:
    66|
    67|| Field | Required | Default | Description |
    68||---|---|---|---|
    69|| `path` | yes | — | Repo root |
    70|| `compile_db` | no | `null` | Path to `compile_commands.json` for C/C++ analysis. Required if `cargo_manifest` is not set. |
    71|| `cargo_manifest` | no | `null` | Path to `Cargo.toml` for Rust crate analysis. Required if `compile_db` is not set. |
    72|| `config` | no | — | YAML defining heuristics and approved wipes |
    73|| `opt_levels` | no | `["O0","O1","O2"]` | Optimization levels for IR comparison. O1 is the diagnostic level: if a wipe disappears at O1 it is simple DSE; O2 catches more aggressive eliminations. |
    74|| `languages` | no | `["c","cpp","rust"]` | Languages to analyze |
    75|| `max_tus` | no | — | Limit on translation units processed from compile DB |
    76|| `mcp_mode` | no | `prefer` | `off`, `prefer`, or `require` — controls Serena MCP usage |
    77|| `mcp_required_for_advanced` | no | `true` | Downgrade `SECRET_COPY`, `MISSING_ON_ERROR_PATH`, and `NOT_DOMINATING_EXITS` to `needs_review` when MCP is unavailable |
    78|| `mcp_timeout_ms` | no | — | Timeout budget for MCP semantic queries |
    79|| `poc_categories` | no | all 11 exploitable | Finding categories for which to generate PoCs. C/C++ findings: all 11 categories supported. Rust findings: only `MISSING_SOURCE_ZEROIZE`, `SECRET_COPY`, and `PARTIAL_WIPE` are supported; other Rust categories are marked `poc_supported=false`. |
    80|| `poc_output_dir` | no | `generated_pocs/` | Output directory for generated PoCs |
    81|| `enable_asm` | no | `true` | Enable assembly emission and analysis (Step 8); produces `STACK_RETENTION`, `REGISTER_SPILL`. Auto-disabled if `emit_asm.sh` is missing. |
    82|| `enable_semantic_ir` | no | `false` | Enable semantic LLVM IR analysis (Step 9); produces `LOOP_UNROLLED_INCOMPLETE` |
    83|| `enable_cfg` | no | `false` | Enable control-flow graph analysis (Step 10); produces `MISSING_ON_ERROR_PATH`, `NOT_DOMINATING_EXITS` |
    84|| `enable_runtime_tests` | no | `false` | Enable runtime test harness generation (Step 11) |
    85|
    86|---
    87|
    88|## Prerequisites
    89|
    90|Before running, verify the following. Each has a defined failure mode.
    91|
    92|**C/C++ prerequisites:**
    93|
    94|| Prerequisite | Failure mode if missing |
    95||---|---|
    96|| `compile_commands.json` at `compile_db` path | Fail fast — do not proceed |
    97|| `clang` on PATH | Fail fast — IR/ASM analysis impossible |
    98|| `uvx` on PATH (for Serena) | If `mcp_mode=require`: fail. If `mcp_mode=prefer`: continue without MCP; downgrade affected findings per Confidence Gating rules. |
    99|| `{baseDir}/tools/extract_compile_flags.py` | Fail fast — cannot extract per-TU flags |
   100|| `{baseDir}/tools/emit_ir.sh` | Fail fast — IR analysis impossible |
   101|| `{baseDir}/tools/emit_asm.sh` | Warn and skip assembly findings (STACK_RETENTION, REGISTER_SPILL) |
   102|| `{baseDir}/tools/mcp/check_mcp.sh` | Warn and treat as MCP unavailable |
   103|| `{baseDir}/tools/mcp/normalize_mcp_evidence.py` | Warn and use raw MCP output |
   104|
   105|**Rust prerequisites:**
   106|
   107|| Prerequisite | Failure mode if missing |
   108||---|---|
   109|| `Cargo.toml` at `cargo_manifest` path | Fail fast — do not proceed |
   110|| `cargo check` passes | Fail fast — crate must be buildable |
   111|| `cargo +nightly` on PATH | Fail fast — nightly required for MIR and LLVM IR emission |
   112|| `uv` on PATH | Fail fast — required to run Python analysis scripts |
   113|| `{baseDir}/tools/validate_rust_toolchain.sh` | Warn — run preflight manually. Checks all tools, scripts, nightly, and optionally `cargo check`. Use `--json` for machine-readable output, `--manifest` to also validate the crate builds. |
   114|| `{baseDir}/tools/emit_rust_mir.sh` | Fail fast — MIR analysis impossible (`--opt`, `--crate`, `--bin/--lib` supported; `--out` can be file or directory) |
   115|| `{baseDir}/tools/emit_rust_ir.sh` | Fail fast — LLVM IR analysis impossible (`--opt` required; `--crate`, `--bin/--lib` supported; `--out` must be `.ll`) |
   116|| `{baseDir}/tools/emit_rust_asm.sh` | Warn and skip assembly findings (`STACK_RETENTION`, `REGISTER_SPILL`). Supports `--opt`, `--crate`, `--bin/--lib`, `--target`, `--intel-syntax`; `--out` can be `.s` file or directory. |
   117|| `{baseDir}/tools/diff_rust_mir.sh` | Warn and skip MIR-level optimization comparison. Accepts 2+ MIR files, normalizes, diffs pairwise, and reports first opt level where zeroize/drop-glue patterns disappear. |
   118|| `{baseDir}/tools/scripts/semantic_audit.py` | Warn and skip semantic source analysis |
   119|| `{baseDir}/tools/scripts/find_dangerous_apis.py` | Warn and skip dangerous API scan |
   120|| `{baseDir}/tools/scripts/check_mir_patterns.py` | Warn and skip MIR analysis |
   121|| `{baseDir}/tools/scripts/check_llvm_patterns.py` | Warn and skip LLVM IR analysis |
   122|| `{baseDir}/tools/scripts/check_rust_asm.py` | Warn and skip Rust assembly analysis (`STACK_RETENTION`, `REGISTER_SPILL`, drop-glue checks). Dispatches to `check_rust_asm_x86.py` (production) or `check_rust_asm_aarch64.py` (**EXPERIMENTAL** — AArch64 findings require manual verification). |
   123|| `{baseDir}/tools/scripts/check_rust_asm_x86.py` | Required by `check_rust_asm.py` for x86-64 analysis; warn and skip if missing |
   124|| `{baseDir}/tools/scripts/check_rust_asm_aarch64.py` | Required by `check_rust_asm.py` for AArch64 analysis (**EXPERIMENTAL**); warn and skip if missing |
   125|
   126|**Common prerequisite:**
   127|
   128|| Prerequisite | Failure mode if missing |
   129||---|---|
   130|| `{baseDir}/tools/generate_poc.py` | Fail fast — PoC generation is mandatory |
   131|
   132|---
   133|
   134|## Approved Wipe APIs
   135|
   136|The following are recognized as valid zeroization. Configure additional entries in `{baseDir}/configs/`.
   137|
   138|**C/C++**
   139|- `explicit_bzero`
   140|- `memset_s`
   141|- `SecureZeroMemory`
   142|- `OPENSSL_cleanse`
   143|- `sodium_memzero`
   144|- Volatile wipe loops (pattern-based; see `volatile_wipe_patterns` in `{baseDir}/configs/default.yaml`)
   145|- In IR: `llvm.memset` with volatile flag, volatile stores, or non-elidable wipe call
   146|
   147|**Rust**
   148|- `zeroize::Zeroize` trait (`zeroize()` method)
   149|- `Zeroizing<T>` wrapper (drop-based)
   150|- `ZeroizeOnDrop` derive macro
   151|
   152|---
   153|
   154|## Finding Capabilities
   155|
   156|Findings are grouped by required evidence. Only attempt findings for which the required tooling is available.
   157|
   158|| Finding ID | Description | Requires | PoC Support |
   159||---|---|---|---|
   160|| `MISSING_SOURCE_ZEROIZE` | No zeroization found in source | Source only | Yes (C/C++ + Rust) |
   161|| `PARTIAL_WIPE` | Incorrect size or incomplete wipe | Source only | Yes (C/C++ + Rust) |
   162|| `NOT_ON_ALL_PATHS` | Zeroization missing on some control-flow paths (heuristic) | Source only | Yes (C/C++ only) |
   163|| `SECRET_COPY` | Sensitive data copied without zeroization tracking | Source + MCP preferred | Yes (C/C++ + Rust) |
   164|| `INSECURE_HEAP_ALLOC` | Secret uses insecure allocator (malloc vs. secure_malloc) | Source only | Yes (C/C++ only) |
   165|| `OPTIMIZED_AWAY_ZEROIZE` | Compiler removed zeroization | IR diff required (never source-only) | Yes |
   166|| `STACK_RETENTION` | Stack frame may retain secrets after return | Assembly required (C/C++); LLVM IR `alloca`+`lifetime.end` evidence (Rust); assembly corroboration upgrades to `confirmed` | Yes (C/C++ only) |
   167|| `REGISTER_SPILL` | Secrets spilled from registers to stack | Assembly required (C/C++); LLVM IR `load`+call-site evidence (Rust); assembly corroboration upgrades to `confirmed` | Yes (C/C++ only) |
   168|| `MISSING_ON_ERROR_PATH` | Error-handling paths lack cleanup | CFG or MCP required | Yes |
   169|| `NOT_DOMINATING_EXITS` | Wipe doesn't dominate all exits | CFG or MCP required | Yes |
   170|| `LOOP_UNROLLED_INCOMPLETE` | Unrolled loop wipe is incomplete | Semantic IR required | Yes |
   171|
   172|---
   173|
   174|## Agent Architecture
   175|
   176|The analysis pipeline uses 11 agents across 8 phases, invoked by the orchestrator (`{baseDir}/prompts/task.md`) via `Task`. Agents write persistent finding files to a shared working directory (`/tmp/zeroize-audit-{run_id}/`), enabling parallel execution and protecting against context pressure.
   177|
   178|| Agent | Phase | Purpose | Output Directory |
   179||---|---|---|---|
   180|| `0-preflight` | Phase 0 | Preflight checks (tools, toolchain, compile DB, crate build), config merge, workdir creation, TU enumeration | `{workdir}/` |
   181|| `1-mcp-resolver` | Phase 1, Wave 1 (C/C++ only) | Resolve symbols, types, and cross-file references via Serena MCP | `mcp-evidence/` |
   182|| `2-source-analyzer` | Phase 1, Wave 2a (C/C++ only) | Identify sensitive objects, detect wipes, validate correctness, data-flow/heap | `source-analysis/` |
   183|| `2b-rust-source-analyzer` | Phase 1, Wave 2b (Rust only, parallel with 2a) | Rustdoc JSON trait-aware analysis + dangerous API grep | `source-analysis/` |
   184|| `3-tu-compiler-analyzer` | Phase 2, Wave 3 (C/C++ only, N parallel) | Per-TU IR diff, assembly, semantic IR, CFG analysis | `compiler-analysis/{tu_hash}/` |
   185|| `3b-rust-compiler-analyzer` | Phase 2, Wave 3R (Rust only, single agent) | Crate-level MIR, LLVM IR, and assembly analysis | `rust-compiler-analysis/` |
   186|| `4-report-assembler` | Phase 3 (interim) + Phase 6 (final) | Collect findings from all agents, apply confidence gates; merge PoC results and produce final report | `report/` |
   187|| `5-poc-generator` | Phase 4 | Craft bespoke proof-of-concept programs (C/C++: all categories; Rust: MISSING_SOURCE_ZEROIZE, SECRET_COPY, PARTIAL_WIPE) | `poc/` |
   188|| `5b-poc-validator` | Phase 5 | Compile and run all PoCs | `poc/` |
   189|| `5c-poc-verifier` | Phase 5 | Verify each PoC proves its claimed finding | `poc/` |
   190|| `6-test-generator` | Phase 7 (optional) | Generate runtime validation test harnesses | `tests/` |
   191|
   192|The orchestrator reads one per-phase workflow file from `{baseDir}/workflows/` at a time, and maintains `orchestrator-state.json` for recovery after context compression. Agents receive configuration by file path (`config_path`), not by value.
   193|
   194|### Execution flow
   195|
   196|```
   197|Phase 0: 0-preflight agent — Preflight + config + create workdir + enumerate TUs
   198|           → writes orchestrator-state.json, merged-config.yaml, preflight.json
   199|Phase 1: Wave 1:  1-mcp-resolver              (skip if mcp_mode=off OR language_mode=rust)
   200|         Wave 2a: 2-source-analyzer           (C/C++ only; skip if no compile_db)  ─┐ parallel
   201|         Wave 2b: 2b-rust-source-analyzer     (Rust only; skip if no cargo_manifest) ─┘
   202|Phase 2: Wave 3:  3-tu-compiler-analyzer x N  (C/C++ only; parallel per TU)
   203|         Wave 3R: 3b-rust-compiler-analyzer   (Rust only; single crate-level agent)
   204|Phase 3: Wave 4:  4-report-assembler          (mode=interim → findings.json; reads all agent outputs)
   205|Phase 4: Wave 5:  5-poc-generator             (C/C++: all categories; Rust: MISSING_SOURCE_ZEROIZE, SECRET_COPY, PARTIAL_WIPE; other Rust findings: poc_supported=false)
   206|Phase 5: PoC Validation & Verification
   207|           Step 1: 5b-poc-validator agent      (compile and run all PoCs)
   208|           Step 2: 5c-poc-verifier agent       (verify each PoC proves its claimed finding)
   209|           Step 3: Orchestrator presents verification failures to user via AskUserQuestion
   210|