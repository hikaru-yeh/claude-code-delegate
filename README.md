# Claude Code Delegate

> [繁體中文](README_zh-TW.md)

`claude-code-delegate` is a Codex-oriented skill for using the local Claude Code CLI as an execution specialist while Codex keeps planning, review, and acceptance. Codex writes the brief, launches Claude Code through a thin wrapper, inspects the wrapper output and git diff, and only then decides whether the work is accepted.

This project was originally inspired by [WenyuChiou/codex-delegate](https://github.com/WenyuChiou/codex-delegate). It takes the same delegation idea in the opposite direction: recent Codex reasoning has become stronger than Claude Code for planning, review, and acceptance, so this reversed fork keeps Codex as the supervisor and uses Claude Code CLI as the executor.

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
3. Codex launches Claude Code synchronously through the bundled `scripts/run_claude.sh` or `scripts/run_claude.ps1` wrapper.
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
│       ├── SKILL.md
│       ├── scripts/
│       │   ├── run_claude.sh
│       │   └── run_claude.ps1
│       └── references/
├── scripts/              # development copy, kept in sync by tests
└── tests/
    └── test_wrappers.py
```

## Installation

Install Claude Code CLI separately and make sure it is available on `PATH`:

```bash
claude --version
```

Install the self-contained skill bundle into your user-scope Codex skills directory:

```bash
git clone https://github.com/<owner>/claude-code-delegate.git
mkdir -p ~/.codex/skills
cp -R claude-code-delegate/skills/claude-code-delegate ~/.codex/skills/
```

On Windows PowerShell:

```powershell
git clone https://github.com/<owner>/claude-code-delegate.git
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills" | Out-Null
Copy-Item ".\claude-code-delegate\skills\claude-code-delegate" "$env:USERPROFILE\.codex\skills\" -Recurse -Force
```

The installed skill folder includes the wrapper scripts, so users do not need to keep the repository root around after installation.

## Usage

Create a task brief for Claude Code:

```bash
mkdir -p .ai
$EDITOR .ai/claude_task_example.md
```

Run the Bash wrapper:

```bash
bash ~/.codex/skills/claude-code-delegate/scripts/run_claude.sh \
  --prompt "Read .ai/claude_task_example.md and execute all instructions inside." \
  --repo "$PWD" \
  --log-file .ai/claude_log_example.txt \
  --output-file .ai/claude_output_example.json
```

Or run the PowerShell wrapper:

```powershell
$SkillDir = Join-Path $env:USERPROFILE ".codex\skills\claude-code-delegate"
powershell -ExecutionPolicy Bypass -File (Join-Path $SkillDir "scripts\run_claude.ps1") `
  -Prompt "Read .ai/claude_task_example.md and execute all instructions inside." `
  -Repo (Get-Location).Path `
  -LogFile ".ai\claude_log_example.txt" `
  -OutputFile ".ai\claude_output_example.json"
```

After the wrapper exits, Codex reviews the generated `.result.json` and the git diff before accepting the work. If the wrapper reports success but the diff is wrong, incomplete, risky, or unverified, Codex rejects or revises the result instead of treating wrapper success as completion.

On Windows, if `claude --version` resolves to a broken shim, set `CLAUDE_PATH` to the working Claude executable before running the wrapper:

```powershell
$env:CLAUDE_PATH = Join-Path $env:APPDATA "npm\claude.cmd"
```

If you want Claude Code CLI to use your `claude.ai` subscription instead of API key billing, make sure `ANTHROPIC_API_KEY` is not set for the wrapper process and disable bare mode:

```powershell
$env:ANTHROPIC_API_KEY = $null
$env:CLAUDE_PATH = Join-Path $env:APPDATA "npm\claude.cmd"
$SkillDir = Join-Path $env:USERPROFILE ".codex\skills\claude-code-delegate"
& (Join-Path $SkillDir "scripts\run_claude.ps1") `
  -Prompt "Read .ai/claude_task_example.md and execute all instructions inside." `
  -Repo (Get-Location).Path `
  -Model haiku `
  -Bare $false `
  -LogFile ".ai\claude_log_example.txt" `
  -OutputFile ".ai\claude_output_example.json"
```

The wrapper defaults to bare mode, which is best for API-key-based automated runs. Bare mode does not read the normal Claude Code login state, so subscription-based local runs should use `-Bare $false`.

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
