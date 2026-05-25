# Example AGENTS.md Delegation Rules

Copy the section below into your project's `AGENTS.md` to make Codex route
bounded implementation work through Claude Code Delegate. Adjust paths and
examples to match your project's structure.

---

## Claude Code Delegation Rules

- Read `skills/claude-code-delegate/SKILL.md` before delegating a task.
- Token-heavy implementation work with clear scope -> delegate to Claude Code CLI.
- Architecture decisions, root-cause debugging, security, multi-subsystem coupling, and final acceptance -> keep in Codex.
- Codex role: plan -> write task brief -> launch Claude Code -> review output -> run verification -> accept or reject.
- Claude Code role: execute the scoped brief, edit only allowed files, run requested checks, and summarize.
- If a `.fallback_codex` sentinel appears after launching Claude Code, Codex takes over the task directly.

### Decision Matrix

| Task | Where |
|------|-------|
| Write tests for an existing module | Claude Code |
| Batch rename a function across 15 files | Claude Code |
| Add type hints to an entire package | Claude Code |
| Generate boilerplate from a narrow spec | Claude Code |
| Migrate deprecated API calls across the codebase | Claude Code |
| Design a new module's API surface | Codex |
| Debug a subtle race condition | Codex |
| Review auth middleware | Codex |
| Refactor code that touches 3+ subsystems | Codex |

### Execution Pattern

**From a Bash-compatible shell:**

```bash
# 1. Write task file to .ai/claude_task_<name>.md
# 2. Launch Claude Code via helper script
bash scripts/run_claude.sh \
  --prompt "Read .ai/claude_task_<name>.md and execute all instructions." \
  --log-file .ai/claude_log_<name>.txt

# 3. Check for quota fallback
if [ -f ".ai/claude_log_<name>.txt.fallback_codex" ]; then
    echo "Claude quota exceeded; Codex must handle the task directly"
elif [ -f ".ai/claude_log_<name>.txt.done" ]; then
    # 4. Review: inspect result JSON, git diff, run tests, verify output
    cat .ai/claude_log_<name>.txt.result.json
    git diff
fi
```

**Windows PowerShell:**

```powershell
& ".\scripts\run_claude.ps1" `
    -Prompt "Read .ai/claude_task_<name>.md and execute all instructions." `
    -LogFile ".ai\claude_log_<name>.txt"

if (Test-Path ".ai\claude_log_<name>.txt.fallback_codex") {
    Write-Host "Claude quota exceeded; Codex must handle the task directly"
} elseif (Test-Path ".ai\claude_log_<name>.txt.done") {
    Get-Content ".ai\claude_log_<name>.txt.result.json"
    git diff
}
```
