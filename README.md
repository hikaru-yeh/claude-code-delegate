# Claude Code Delegate

> [繁體中文](README_zh-TW.md)

`claude-code-delegate` is a Codex-oriented skill for using the local Claude Code CLI as an execution specialist while Codex keeps planning, review, and acceptance. Codex writes the brief, launches Claude Code through a thin wrapper, inspects the wrapper output and git diff, and only then decides whether the work is accepted.

This repository is the reversed fork of the earlier delegation direction: Codex is now the supervisor, and Claude Code CLI is the executor.

## Positioning

This skill is for work where Codex benefits from delegating execution while retaining judgment:

- multi-file implementation
- mechanical refactors
- boilerplate generation
- test scaffolding
- large batch edits

It is not a replacement for Codex's planning, architecture decisions, root-cause analysis, security review, or final acceptance.

## Core Pattern

1. Codex decides that a task is bounded enough to delegate.
2. Codex writes `.ai/claude_task_<name>.md` with scope, constraints, expected output, and verification notes.
3. Codex launches Claude Code synchronously through `scripts/run_claude.sh` or `scripts/run_claude.ps1`.
4. The wrapper emits logs, sentinels, and `<log>.result.json`.
5. Codex reviews the `.result.json`, the changed-file attribution, the git diff, and any relevant test output before accepting or rejecting the result.

Wrapper success is not acceptance. It means the Claude Code execution returned a valid wrapper result; Codex still owns review and final judgment.

## Repository Layout

```text
claude-code-delegate/
├── README.md
├── README_zh-TW.md
├── CHANGELOG.md
├── skills/
│   └── claude-code-delegate/
├── scripts/
│   ├── run_claude.sh
│   └── run_claude.ps1
└── tests/
    └── test_wrappers.py
```

## Installation

Install Claude Code CLI separately and make sure it is available on `PATH`:

```bash
claude --version
```

Install or copy `skills/claude-code-delegate` into the Codex skills location you use for local workflows. Keep the wrapper scripts in this repository or copy them with the skill if your workflow expects a standalone bundle.

## Usage

Create a task brief for Claude Code:

```bash
mkdir -p .ai
$EDITOR .ai/claude_task_example.md
```

Run the Bash wrapper:

```bash
bash scripts/run_claude.sh .ai/claude_task_example.md
```

Or run the PowerShell wrapper:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_claude.ps1 .ai/claude_task_example.md
```

After the wrapper exits, Codex reviews the generated `.result.json` and the git diff before accepting the work. If the wrapper reports success but the diff is wrong, incomplete, risky, or unverified, Codex rejects or revises the result instead of treating wrapper success as completion.

## Output Contract

The wrapper writes a machine-readable result file next to its log. The contract includes:

- `delegate: "claude"` to identify Claude Code as the executor.
- `fallback_codex` for cases where Codex should resume directly instead of relying on the delegated run.
- wrapper status and sentinel metadata.
- changed-file attribution used during Codex review.

The wrapper result is evidence for review, not an acceptance decision.

## Testing

```bash
python -m pytest -q
```

Wrapper tests cover:

- success contract generation
- Bash behavior
- PowerShell behavior
- changed-file attribution

## License

MIT
