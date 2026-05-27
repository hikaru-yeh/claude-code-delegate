---
name: claude-code-delegate
description: Delegates implementation-heavy or repetitive coding work from Codex to local Claude Code CLI. Codex keeps planning, review, and acceptance. Avoid for architecture, security, or product decisions, and avoid tasks that need Claude to call Codex back.
license: MIT
compatibility: Designed for Codex skill hosts. The skill bundle includes wrapper scripts at scripts/run_claude.sh and scripts/run_claude.ps1 next to this SKILL.md.
---

# Claude Code Delegate Skill

Codex is the supervisor. Claude Code CLI runs scoped implementation. Codex writes the task brief, invokes the wrapper, reviews the diff, runs verification, and decides whether to accept the result.

Claude is a delegate, not a second supervisor. Give it bounded work with explicit files, constraints, and acceptance criteria. Do not ask Claude to call Codex, route work to other agents, or make architecture, security, or product decisions.

## Hard rules

- Before invoking the wrapper, check the same executable the wrapper will use: Bash `${CLAUDE_PATH:-claude} --version`; PowerShell `if ($env:CLAUDE_PATH) { & $env:CLAUDE_PATH --version } else { claude --version }`. If it fails, stop and tell the user to install and authenticate Claude Code CLI.
- Use the wrapper instead of raw `claude -p` for shipping tasks. The wrapper handles stdin closure, structured result JSON, quota fallback, and changed-file capture.
- Wrapper `success` is not acceptance. Codex still reviews the diff, confirms scope, and runs verification.
- Do not ask Claude to call Codex back, consult another agent, or continue the delegation chain.
- Prefer `--bare` to reduce UI/state overhead. The wrapper uses `--bare` by default; opt out only when the task genuinely requires normal Claude Code behavior.
- Keep write scope narrow. List allowed files or directories in the task brief and reject drift.

## When to delegate

Delegate when the task is implementation-heavy and bounded:

- repetitive edits across a clear list of files
- boilerplate, scaffolding, or mechanical migration work
- test scaffolding with precise expectations
- small feature implementation after Codex has already decided the design
- formatting or documentation updates that follow an explicit pattern

## Keep in Codex

Do not delegate when the task needs supervisor judgment:

- architecture, security, privacy, or product decisions
- root-cause debugging where the hypothesis is still unclear
- code review, acceptance, merge, release, or risk calls
- broad repository exploration without a narrow implementation goal
- tasks requiring Claude to ask Codex follow-up questions or call Codex back
- tasks involving secrets, credentials, or ambiguous local machine paths

## Workflow

1. **Check CLI**: check the same executable the wrapper will use: Bash `${CLAUDE_PATH:-claude} --version`; PowerShell `if ($env:CLAUDE_PATH) { & $env:CLAUDE_PATH --version } else { claude --version }`. If it fails, stop and report the missing dependency.

2. **Brief**: write `.ai/claude_task_<name>.md` with Context / Goal / Constraints / Acceptance. Use `references/task-template.md`.

3. **Run**: invoke the bundled wrapper from the installed skill directory:
   ```bash
   bash ~/.codex/skills/claude-code-delegate/scripts/run_claude.sh \
     --prompt "Read .ai/claude_task_<name>.md and execute all instructions inside." \
     --repo "$PWD" \
     --log-file .ai/claude_log_<name>.txt \
     --output-file .ai/claude_output_<name>.json
   ```

   On Windows, use the bundled PowerShell wrapper under `$env:USERPROFILE\.codex\skills\claude-code-delegate\scripts\run_claude.ps1`. PowerShell and optional flags are documented in `references/wrapper.md`.

4. **Read status**: open `.ai/claude_log_<name>.txt.result.json`.
   - `success` means Claude exited 0; review is still required.
   - `fallback` means Claude quota or rate limits were hit; Codex must take over directly.
   - `error` means the wrapper or Claude run failed; inspect `<log>.error` and the log before deciding next steps.

5. **Accept or reject**: inspect changed files, confirm the write scope, run the verification commands from the task brief, and decide. Use `references/review-checklist.md`.

## Output contract

Every wrapper run writes `<log-file>.result.json` with `status` (`success|fallback|error`), `delegate` (`claude`), `model`, `log_file`, `output_file`, `summary`, `risks`, `files_changed`, `tests_run`, and `timestamp_utc`.

The wrapper owns transport status. Codex owns acceptance. Full schema and semantics: `references/output-contract.md`.

## See also

- `references/task-template.md` - task brief template
- `references/wrapper.md` - Bash and PowerShell invocation, flags, env vars, and sentinels
- `references/output-contract.md` - full JSON result contract
- `references/review-checklist.md` - Codex acceptance checklist
