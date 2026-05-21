# Codex Delegate

> [繁體中文](README_zh-TW.md)

`codex-delegate` is a Claude-oriented skill for using Codex CLI as an execution specialist for implementation-heavy coding work while keeping planning, review, and acceptance in Claude.

> 📚 Part of the [**agentic AI learning roadmap**](https://github.com/WenyuChiou/awesome-agentic-ai-zh) — a 7-stage curated path for building agentic AI, multilingual (zh-TW · zh-CN · English). This skill is referenced in §13 (Multi-LLM Delegation).

## Positioning

This skill is for tasks that are expensive in tokens but cheap in judgment:

- multi-file implementation
- mechanical refactors
- boilerplate generation
- test scaffolding
- large batch edits

It is not meant for architecture, root-cause debugging, security review, or ambiguous product decisions.

## What Changed In This Version

- clearer routing boundary between Claude, Codex, and Gemini
- explicit supervisor acceptance gate
- machine-readable wrapper output via `<log>.result.json`
- regression tests for bash and PowerShell wrappers

## Core Pattern

1. Claude writes a task file describing scope and constraints.
2. Claude launches Codex synchronously through the wrapper.
3. The wrapper emits sentinel files plus `result.json`.
4. Claude reviews the diff and runs verification before accepting the result.

Wrapper success is not final acceptance. Claude still owns the judgment.

## Relation to `openai/codex-plugin-cc`

OpenAI ships an official Codex integration for Claude Code,
[`openai/codex-plugin-cc`](https://github.com/openai/codex-plugin-cc). It is a
capable, broker-based plugin — and a different design point from this skill.
The two are complementary; the table below is meant to help you pick, not to
rank them.

| Aspect | `codex-delegate` (this repo) | `openai/codex-plugin-cc` |
|---|---|---|
| Form | A single Claude Code skill | A multi-command plugin suite |
| Execution model | Thin **synchronous** wrapper: run → write `result.json` → exit | Persistent **broker** process with background jobs |
| Job tracking | None by design — one run, one result | `/codex:status`, `/codex:result`, `/codex:cancel` |
| Invocation | Claude invokes the skill; the wrapper script runs Codex | Slash commands (`/codex:review`, `/codex:rescue`, …) plus a proactive subagent |
| Review gate | Claude's own acceptance gate (`skills/codex-delegate/references/review-checklist.md`) | Optional `Stop`-hook review gate |
| Platform | `bash` + PowerShell wrappers, Windows-tested, no Node runtime | Node.js 18.18+ runtime |
| Delegate routing | Three-way Claude / Codex / Gemini routing table | Codex-focused |
| Maintainer · License | Wenyu Chiou · MIT | OpenAI · Apache-2.0 |

In short: reach for `codex-plugin-cc` when you want background async jobs, a
slash-command UX, and an OpenAI-maintained integration. Reach for
`codex-delegate` when you want a thin, synchronous, supervisor-gated skill that
keeps acceptance in Claude, behaves the same on Windows and Linux, and routes
across Claude / Codex / Gemini.

`codex-delegate` also borrows from the official plugin: the prompt-engineering
reference (`skills/codex-delegate/references/codex-prompt-blocks.md`) is adapted
from its `gpt-5-4-prompting` skill (Apache-2.0).

## Repository Layout

```text
codex-delegate/
├── SKILL.md
├── README.md
├── README_zh-TW.md
├── scripts/
│   ├── run_codex.sh
│   └── run_codex.ps1
├── tests/
│   └── test_wrappers.py
└── references/
```

## Testing

```bash
python -m pytest -q
```

Current wrapper tests cover:

- success-path `result.json` generation
- PowerShell wrapper contract behavior

## Installation

**1. Install the skill** via the [`ai-research-skills` Claude Code marketplace](https://github.com/WenyuChiou/ai-research-skills):

```bash
claude plugin marketplace add WenyuChiou/ai-research-skills
claude plugin install codex-delegate@ai-research-skills
```

Default scope is `user` (this OS account, all projects). Add
`--scope project` to install only for the current project.

**2. Make sure Codex CLI is on `$PATH`:**

```bash
npm install -g @openai/codex
codex --version
```

## License

MIT
