# Claude task brief template

Save the brief at `.ai/claude_task_<name>.md`.

## Template

```markdown
# Task: <descriptive name>

## Context
- Repo: <repo root>
- Read these files first:
  - path/to/context-file.ext
- Only modify:
  - path/to/allowed-file.ext
  - path/to/allowed-directory/

## Goal
<what Claude should implement>

## Constraints
- Do not edit files outside the allowed list.
- Follow adjacent code style and existing helper APIs.
- Do not make architecture changes.
- Do not make security, product, or release decisions.
- Do not call Codex or other agents.
- Do not add credentials, tokens, secrets, or absolute local paths.
- Do not update README files unless Codex confirms the README gate: before any README edit, Codex must tell the user what README change is needed, propose a short plan, wait for user confirmation, and keep localized README files synchronized.

## Acceptance
- Required tests or checks: <commands>
- Expected files changed: <high-level expectation>
- Required summary: include what changed, risks, and tests run in the delegate output.
```

## Quality rules

- Keep Context specific. Point Claude to the files that matter.
- Make the write scope explicit. If Claude edits outside it, reject the run.
- Give runnable acceptance commands. Do not use vague acceptance like "looks good".
- Keep the Goal implementation-focused. Codex should decide the plan before delegating.
- Include known local pitfalls so Claude does not rediscover them expensively.
