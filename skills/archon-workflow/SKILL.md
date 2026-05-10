---
name: archon-workflow
description: 'Deterministic AI coding workflow engine: YAML-defined repeatable workflows,
  isolated git worktrees, human approval gates, loop-with-until, composable bash+AI
  nodes.'
version: 1.0.0
author: Hermes Agent (based on coleam00/Archon)
license: MIT
metadata:
  hermes:
    tags:
    - workflow
    - deterministic
    - ai-coding
    - git
    - yaml
    - automation
    - ci-cd
    related_skills:
    - subagent-driven-development
    - writing-plans
    - requesting-code-review
    - test-driven-development
    category: software-development
    molin_owner: 墨码（软件工坊）
min_hermes_version: 0.13.0
---

# Archon Workflow

## Overview

Archon is a deterministic, YAML-defined workflow engine for AI-assisted coding. Think **GitHub Actions for AI coding** — define repeatable pipelines with composable nodes (bash + AI), isolated git worktrees for parallel execution, human approval gates, and loop-with-until conditions. Every run is reproducible and auditable.

**Core principle:** AI coding should be deterministic. Define the workflow once, run it endlessly with consistent, testable results. No more "the AI did something unpredictable" — the workflow constrains and validates every step.

## When to Use

Use this skill when:
- Automating repetitive AI coding tasks (refactoring, migrations, code generation)
- Building CI/CD-like pipelines that involve AI steps
- Enforcing code quality gates with human approval before merging
- Running parallel experiments on different branches simultaneously
- Creating repeatable, auditable development workflows
- Onboarding new projects with standardized setup workflows
- Running batch code transformations across a monorepo

**vs. ad-hoc AI coding:**
- **Deterministic:** Same input → same output, every time
- **Auditable:** Every step is logged, every output is versioned
- **Composable:** Build complex workflows from simple, tested nodes
- **Gated:** Human approval checkpoints prevent bad code from progressing
- **Isolated:** Git worktrees ensure parallel workflows never conflict

## Workflow Concepts

### Nodes

Every workflow is composed of nodes. Two node types:

#### Bash Node
Runs a shell command. Pure, deterministic, no AI.
```yaml
- name: "Install dependencies"
  type: bash
  command: "npm install"
  timeout: 120
  capture_output: true
```

#### AI Node
Invokes an LLM with a prompt and optional context. The prompt is a template with variable substitution.
```yaml
- name: "Generate unit tests"
  type: ai
  prompt: |
    Write comprehensive unit tests for the following code using {{test_framework}}.
    
    File: {{target_file}}
    
    Requirements:
    - Cover all public methods
    - Include edge cases
    - Follow the existing test patterns in {{test_dir}}
    
    Code to test:
    {{file_content}}
  model: "claude-sonnet-4-20250514"
  output_var: "generated_tests"
  max_tokens: 8000
  validation:
    - type: "contains"
      value: "import { describe, it, expect }"
      error_message: "Tests must use the project's test framework"
```

### Variables

Workflows use variables for parameterization:

```yaml
variables:
  target_file: "src/auth/login.ts"
  test_framework: "vitest"
  test_dir: "src/__tests__/"
```

Variables can be:
- **Static:** Defined in the workflow YAML
- **Derived:** Output from a previous node (`{{node_name.output_var}}`)
- **Environment:** Injected at runtime (`$ENV_VAR`)
- **CLI:** Passed via command line (`--var key=value`)

### Gates (Human Approval)

Insert human checkpoints where a person must review and approve before the workflow continues:

```yaml
- name: "Review generated code"
  type: gate
  title: "Approve generated tests?"
  description: |
    Please review the generated tests for `{{target_file}}`.
    
    The tests have been written to `{{output_path}}`.
    
    **Check:**
    - Do the tests cover the expected behavior?
    - Are edge cases handled?
    - Does the style match existing tests?
    
    Reply APPROVE to continue or REJECT with feedback.
  timeout: 3600  # 1 hour for human to respond
  on_reject: "stop"  # or "retry" to loop back with feedback
```

### Loops (Loop with Until)

Repeat a set of nodes until a condition is met:

```yaml
- name: "Refactor until tests pass"
  type: loop
  max_iterations: 5
  until:
    type: "bash"
    command: "npm test -- {{test_file}}"
    expected_exit_code: 0
  
  # Feedback: pass previous failure output to the AI
  context_from_last:
    - variable: "test_output"
      from: "loop.last.run.stderr"
  
  steps:
    - name: "Analyze test failures"
      type: ai
      prompt: |
        The tests for {{target_file}} failed with:
        ```
        {{test_output}}
        ```
        Analyze the failures and determine what code changes are needed.
      output_var: "failure_analysis"
    
    - name: "Fix the code"
      type: ai
      prompt: |
        Fix the code in {{target_file}} based on this analysis:
        {{failure_analysis}}
        
        Current code:
        {{file_content}}
        
        Output ONLY the corrected file content.
      output_var: "fixed_code"
    
    - name: "Apply fix"
      type: bash
      command: "echo '{{fixed_code}}' > {{target_file}}"
```

### Git Worktrees

Isolate workflow execution in a dedicated git worktree so parallel workflows never conflict:

```yaml
workflow:
  name: "multi-branch-refactor"
  worktree:
    enabled: true
    base_branch: "main"
    branch_prefix: "archon/"
    cleanup: "on_success"  # or "always", "never"
```

With worktrees:
- Each workflow run gets its own isolated working directory
- Branches are created automatically (`archon/workflow-name/timestamp`)
- Parallel workflows on different branches never collide
- Cleanup removes the worktree after success (or keeps it for inspection on failure)

**Worktree lifecycle:**
```
1. Create worktree from base_branch at /tmp/archon-worktrees/{workflow}-{timestamp}/
2. Create new branch: archon/{workflow-name}/{timestamp}
3. Execute all nodes in the worktree
4. On success: commit changes → push branch → cleanup worktree (if configured)
5. On failure: keep worktree for debugging → notify
```

## Workflow File Format

Complete workflow example:

```yaml
# .archon/workflows/refactor-to-typescript.yaml
name: "Refactor to TypeScript"
description: "Convert a JavaScript file to TypeScript with tests and review"
version: "1.0"

variables:
  source_file: "src/utils/helpers.js"
  output_file: "src/utils/helpers.ts"
  test_file: "src/__tests__/helpers.test.ts"

worktree:
  enabled: true
  base_branch: "main"
  branch_prefix: "archon/ts-refactor/"

steps:
  # Step 1: Install dependencies
  - name: "Setup"
    type: bash
    command: "npm ci"
    timeout: 120

  # Step 2: Generate TypeScript types
  - name: "Infer types"
    type: ai
    prompt: |
      Analyze this JavaScript file and infer TypeScript types:
      
      ```javascript
      {{source_file_content}}
      ```
      
      Output a TypeScript interfaces/types definition block.
    output_var: "ts_types"
    model: "claude-sonnet-4-20250514"

  # Step 3: Convert to TypeScript
  - name: "Convert to TS"
    type: ai
    prompt: |
      Convert this JavaScript file to TypeScript. Use these inferred types:
      ```typescript
      {{ts_types}}
      ```
      
      Original JS:
      ```javascript
      {{source_file_content}}
      ```
      
      Rules:
      - No `any` types (use `unknown` if truly needed)
      - Preserve all existing functionality
      - Export all public functions with proper types
      - Add JSDoc for public API
      
      Output the complete TypeScript file.
    output_var: "ts_content"

  # Step 4: Write the file
  - name: "Write output"
    type: bash
    command: |
      cat > {{output_file}} << 'TYPESCRIPT_EOF'
      {{ts_content}}
      TYPESCRIPT_EOF
      npx prettier --write {{output_file}}

  # Step 5: Generate tests
  - name: "Generate tests"
    type: ai
    prompt: |
      Write comprehensive tests for {{output_file}} using vitest.
      
      Code:
      ```typescript
      {{ts_content}}
      ```
      
      Cover all exported functions with:
      - Happy path
      - Edge cases
      - Error handling
    output_var: "test_content"

  # Step 6: Write tests
  - name: "Write tests"
    type: bash
    command: |
      cat > {{test_file}} << 'TEST_EOF'
      {{test_content}}
      TEST_EOF
      npx prettier --write {{test_file}}

  # Step 7: Run tests (loop until pass)
  - name: "Validate tests pass"
    type: loop
    max_iterations: 3
    until:
      type: "bash"
      command: "npx vitest run {{test_file}}"
      expected_exit_code: 0
    context_from_last:
      - variable: "test_failures"
        from: "loop.last.run.stderr"
    steps:
      - name: "Fix failing tests"
        type: ai
        prompt: |
          Tests failed with:
          ```
          {{test_failures}}
          ```
          
          Fix the test file. Current content:
          ```typescript
          {{test_content}}
          ```
        output_var: "test_content"
      - name: "Apply test fix"
        type: bash
        command: |
          cat > {{test_file}} << 'FIXED_EOF'
          {{test_content}}
          FIXED_EOF

  # Step 8: TypeScript compilation check
  - name: "TypeScript check"
    type: bash
    command: "npx tsc --noEmit"
    expected_exit_code: 0

  # Step 9: Lint
  - name: "Lint"
    type: bash
    command: "npx eslint {{output_file}} {{test_file}} --fix"

  # Step 10: Human gate
  - name: "Review changes"
    type: gate
    title: "Approve TypeScript Conversion"
    description: |
      ## Changes to review:
      
      **Modified:** `{{output_file}}` (converted from JS)
      **Added:** `{{test_file}}` (generated tests)
      
      All tests pass ✅ | TypeScript compiles ✅ | Linting clean ✅
      
      Review the diff and reply:
      - `APPROVE` to commit and push
      - `REJECT: <feedback>` to send back for fixes
    on_reject: "retry"
    retry_from_step: "Convert to TS"

  # Step 11: Commit
  - name: "Commit and push"
    type: bash
    command: |
      git add {{output_file}} {{test_file}}
      git commit -m "refactor: convert {{source_file}} to TypeScript

      Auto-generated by Archon workflow: refactor-to-typescript
      
      - Inferred TypeScript types from JS source
      - Generated comprehensive unit tests
      - All tests pass, compilation clean"
      git push origin HEAD
```

## Running Workflows

```bash
# Run a workflow
archon run .archon/workflows/refactor-to-typescript.yaml \
  --var source_file=src/auth/login.js

# Run with environment variables
ARCHON_MODEL=claude-sonnet-4-20250514 archon run workflow.yaml

# Dry run (validate without executing)
archon run --dry-run workflow.yaml

# Run in parallel (multiple worktrees)
archon run --parallel 4 batch-refactor.yaml

# List available workflows
archon list

# View workflow run history
archon history
```

## Workflow Composition

Complex workflows compose from simpler ones:

```yaml
# .archon/workflows/full-migration.yaml
name: "Full migration pipeline"
description: "Lint → Refactor → Test → Review → Merge"

steps:
  - name: "Lint entire codebase"
    type: workflow
    workflow: ".archon/workflows/lint-all.yaml"
    
  - name: "Refactor to TypeScript"
    type: workflow
    workflow: ".archon/workflows/refactor-to-typescript.yaml"
    variables:
      source_file: "{{source_file}}"
    
  - name: "Security audit"
    type: workflow
    workflow: ".archon/workflows/security-audit.yaml"
    
  - name: "Final gate"
    type: gate
    title: "Ready to merge?"
    description: "All sub-workflows completed successfully. Review and approve merge."
```

## Built-in Node Reference

| Node Type | Purpose | Key Parameters |
|-----------|---------|---------------|
| `bash` | Run shell commands | `command`, `timeout`, `expected_exit_code`, `capture_output` |
| `ai` | LLM invocation | `prompt`, `model`, `output_var`, `max_tokens`, `validation` |
| `gate` | Human approval checkpoint | `title`, `description`, `timeout`, `on_reject` |
| `loop` | Repeat until condition | `until`, `max_iterations`, `steps`, `context_from_last` |
| `workflow` | Compose sub-workflows | `workflow`, `variables` |
| `parallel` | Run nodes concurrently | `steps` (all run in parallel) |
| `condition` | Branch on condition | `if`, `then`, `else` |
| `notify` | Send notification | `channel` (slack, email, webhook), `message` |

## Conditional Execution

```yaml
- name: "Check if file exists"
  type: condition
  if:
    type: "bash"
    command: "test -f {{output_file}}"
  then:
    - name: "File exists, run tests"
      type: bash
      command: "npm test -- {{test_file}}"
  else:
    - name: "File missing, generate"
      type: ai
      prompt: "Generate {{output_file}} from scratch..."
```

## Parallel Execution

```yaml
- name: "Generate multiple files in parallel"
  type: parallel
  steps:
    - name: "Generate types"
      type: ai
      prompt: "Generate TypeScript types for: {{source_file}}"
      output_var: "types_content"
    
    - name: "Generate tests"
      type: ai
      prompt: "Generate tests for: {{source_file}}"
      output_var: "test_content"
    
    - name: "Generate docs"
      type: ai
      prompt: "Generate documentation for: {{source_file}}"
      output_var: "docs_content"
```

## Best Practices

### 1. Name Everything Explicitly
Every node should have a descriptive `name`. It appears in logs, history, and error messages.

### 2. Always Include Gates for Destructive Operations
Any workflow that modifies code and could be merged should have a human gate before the final commit:
```yaml
- name: "Review before commit"
  type: gate
  title: "Approve changes?"
```

### 3. Set Reasonable Timeouts
AI nodes can hang. Set timeouts:
```yaml
- name: "Generate code"
  type: ai
  timeout: 300  # 5 minutes
```

### 4. Validate AI Output
Use the `validation` field on AI nodes:
```yaml
validation:
  - type: "contains"
    value: "export"
    error_message: "Output must contain at least one export"
  - type: "regex"
    pattern: "^```typescript"
    error_message: "Output must start with a TypeScript code block"
  - type: "max_length"
    value: 5000
    error_message: "Output too long"
```

### 5. Use Worktrees for Isolation
Always enable worktrees for workflows that modify files:
```yaml
worktree:
  enabled: true
  base_branch: "main"
```

### 6. Loop with Escape Hatches
Always set `max_iterations` on loops to prevent infinite loops:
```yaml
- type: loop
  max_iterations: 5  # Never omit this
```

### 7. Version Your Workflows
Workflows are code. Version them:
```yaml
version: "1.2.0"
```

### 8. Log Everything
Archon automatically logs all node inputs, outputs, and timings. Review the run log after each execution:
```bash
archon history --workflow refactor-to-typescript --limit 5
```

## Debugging Workflows

```bash
# Run with verbose logging
archon run --verbose workflow.yaml

# Step through interactively
archon run --interactive workflow.yaml

# Resume from a failed step
archon run --resume run-id-abc123

# Inspect a failed run's worktree
archon inspect run-id-abc123

# Export run artifacts
archon export run-id-abc123 --output ./debug/
```

## Tips

- **Start simple:** Begin with a 3-node workflow (bash → AI → gate) and expand
- **Gate everything mergeable:** Human eyes on AI-generated code before it hits main
- **Worktrees are free:** Use them liberally — they prevent so many issues
- **Template your prompts:** Use `{{variables}}` instead of hardcoding values
- **Fail fast:** Use `expected_exit_code` and `validation` to catch issues at the source
- **Chain workflows:** Build a library of small, tested workflows and compose them
- **Loop with feedback:** Pass failure output into the AI's next prompt for auto-healing
- **Think CI/CD for AI:** If you wouldn't trust a CI step without gates, don't trust an AI step without them