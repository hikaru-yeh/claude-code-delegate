# Codex prompt blocks — phrasing the task so Codex performs well

`task-template.md` defines the *shape of the brief file* (Context / Goal /
Constraints / Acceptance). This file defines the *phrasing layer*: a set of
composable XML-tagged blocks you drop **inside** the brief's Goal and
Constraints when the task is judgment-sensitive.

For a pure mechanical sweep (batch rename, docstring add) the flat template is
enough — do not bolt these blocks on. Reach for them when an unsupported guess,
a half-finished fix, or an unrelated refactor would actually hurt the result:
debugging, write-capable changes, review, research.

> Adapted from the `gpt-5-4-prompting` skill in
> [`openai/codex-plugin-cc`](https://github.com/openai/codex-plugin-cc)
> (Apache-2.0). Reframed for this skill's single-shot brief-file workflow.

## Where the blocks go

The wrapper runs `--prompt "Read .ai/codex_task_<name>.md and execute..."`, so
Codex reads the brief file. XML tags inside that markdown file are read fine.
Put the blocks under the brief's Goal (what done looks like) or Constraints
(how to stay safe). Keep them compact — a better contract beats raising the
reasoning effort or padding the prompt with prose.

Core rules:

- One clear task per Codex run. Split unrelated asks into separate runs.
- Tell Codex what *done* looks like; do not assume it infers the end state.
- Add a block only where the task needs it. Remove redundant ones before sending.
- Use the exact tag names below so briefs stay consistent across runs.

## Block library

Wrap each block in the XML tag shown. Pick the smallest set that fits.

### `task` — use in nearly every brief

```xml
<task>
The concrete job, the relevant repo or failure context, and the expected end state.
</task>
```

### `structured_output_contract` — when the response shape matters

```xml
<structured_output_contract>
Return exactly the requested output shape and nothing else.
Keep it compact. Put the highest-value findings or decisions first.
</structured_output_contract>
```

### `compact_output_contract` — concise prose instead of a schema

```xml
<compact_output_contract>
Keep the final answer compact and structured.
No long scene-setting, no repeated recap.
</compact_output_contract>
```

### `default_follow_through_policy` — when Codex should act, not ask

```xml
<default_follow_through_policy>
Default to the most reasonable low-risk interpretation and keep going.
Only stop to ask when a missing detail changes correctness, safety, or an
irreversible action.
</default_follow_through_policy>
```

### `completeness_contract` — multi-step work that must not stop early

```xml
<completeness_contract>
Resolve the task fully before stopping. Do not stop at the first plausible
answer. Check for follow-on fixes, edge cases, or cleanup needed for a
correct result.
</completeness_contract>
```

### `verification_loop` — when correctness matters

```xml
<verification_loop>
Before finalizing, verify the result against the task requirements and the
changed files or tool outputs. If a check fails, revise — do not report the
first draft.
</verification_loop>
```

### `missing_context_gating` — when Codex might otherwise guess

```xml
<missing_context_gating>
Do not guess missing repository facts. If required context is absent, retrieve
it with tools or state exactly what remains unknown.
</missing_context_gating>
```

### `grounding_rules` — review, research, root-cause analysis

```xml
<grounding_rules>
Ground every claim in the provided context or your tool outputs.
Do not present inferences as facts. Label any hypothesis clearly.
</grounding_rules>
```

### `action_safety` — write-capable or potentially broad tasks

```xml
<action_safety>
Keep changes tightly scoped to the stated task. Avoid unrelated refactors,
renames, or cleanup unless required for correctness. Call out any risky or
irreversible action before taking it.
</action_safety>
```

### `research_mode` — exploration, comparisons, recommendations

```xml
<research_mode>
Separate observed facts, reasoned inferences, and open questions.
Prefer breadth first, then go deeper only where evidence changes the answer.
</research_mode>
```

### `dig_deeper_nudge` — review and adversarial inspection

```xml
<dig_deeper_nudge>
After the first plausible issue, check for second-order failures, empty-state
behavior, retries, stale state, and rollback paths before finalizing.
</dig_deeper_nudge>
```

### `progress_updates` — long-running, tool-heavy runs

```xml
<progress_updates>
Keep progress updates brief and outcome-based. Mention only major phase
changes or blockers.
</progress_updates>
```

## Recipes

Copy the smallest recipe that fits, then trim. These slot into the brief's
Goal/Constraints; the brief still carries Context (file lists) and Acceptance
(verification commands) per `task-template.md`.

### Narrow fix

```xml
<task>
Implement the smallest safe fix for the identified issue. Preserve existing
behavior outside the failing path.
</task>
<structured_output_contract>
Return: 1. summary of the fix  2. touched files  3. verification performed
4. residual risks or follow-ups
</structured_output_contract>
<completeness_contract>
Resolve the task fully. Do not stop after identifying the issue without
applying the fix.
</completeness_contract>
<verification_loop>
Before finalizing, verify the fix matches the requirements and the changed
code is coherent.
</verification_loop>
<action_safety>
Keep changes tightly scoped. Avoid unrelated refactors or cleanup.
</action_safety>
```

### Diagnosis (read-only — pair with a read-only run)

```xml
<task>
Diagnose why the failing test or command breaks in this repository. Identify
the most likely root cause.
</task>
<compact_output_contract>
Return: 1. most likely root cause  2. evidence  3. smallest safe next step
</compact_output_contract>
<missing_context_gating>
Do not guess missing repository facts. State exactly what remains unknown.
</missing_context_gating>
<verification_loop>
Before finalizing, verify the proposed root cause matches the observed evidence.
</verification_loop>
```

### Root-cause review

```xml
<task>
Analyze this change for the most likely correctness or regression issues.
Focus on the provided repository context only.
</task>
<structured_output_contract>
Return: 1. findings ordered by severity  2. supporting evidence per finding
3. brief next steps
</structured_output_contract>
<grounding_rules>
Ground every claim in the repo context or tool outputs. Label inferences.
</grounding_rules>
<dig_deeper_nudge>
Check second-order failures, empty-state handling, retries, stale state, and
rollback paths before finalizing.
</dig_deeper_nudge>
```

### Research / recommendation

```xml
<task>
Research the available options and recommend the best path for this task.
</task>
<structured_output_contract>
Return: 1. observed facts  2. reasoned recommendation  3. tradeoffs
4. open questions
</structured_output_contract>
<research_mode>
Separate observed facts, reasoned inferences, and open questions.
</research_mode>
```

## Prompt anti-patterns

These are about *prompt phrasing*, distinct from the brief-file anti-patterns
in `task-template.md` (vague goals, missing scope fence).

| Anti-pattern | Bad | Fix |
|---|---|---|
| Vague task framing | "Take a look at this and let me know what you think." | Wrap a concrete job in `<task>`. |
| Missing output contract | "Investigate and report back." | Add `structured_output_contract` or `compact_output_contract`. |
| No follow-through default | "Debug this failure." (Codex stalls asking) | Add `default_follow_through_policy`. |
| Asking for more reasoning | "Think harder and be very smart." | Add `verification_loop` — a contract beats a pep talk. |
| Mixing unrelated jobs | "Review this diff, fix the bug, update docs, suggest a roadmap." | One job per run; split into separate runs. |
| Unsupported certainty | "Tell me exactly why production failed." | Add `grounding_rules` so inferences stay labeled. |

## Cross-references

- `task-template.md` — the brief-file shape these blocks slot into
- `patterns.md` — the five delegation shapes (which recipe pairs with which)
- `review-checklist.md` — Claude's acceptance gate after the run
