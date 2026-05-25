# Codex acceptance checklist

Before accepting a Claude delegate run, Codex verifies each item below.

## Brief quality

- [ ] The task file was specific enough for a delegate to execute without follow-up.
- [ ] The write scope listed exact files or directories Claude was allowed to edit.
- [ ] The brief included runnable verification commands or an explicit reason verification is documentation-only.
- [ ] The brief did not ask Claude to call Codex or other agents.

## Execution scope

- [ ] Claude stayed inside the allowed write scope.
- [ ] No README changes were made unless the README gate was followed: Codex told the user what README change was needed, proposed a short plan, waited for user confirmation, and kept localized README files synchronized.
- [ ] No CHANGELOG, script, test, or unrelated skill files changed unless they were explicitly allowed.
- [ ] No credentials, tokens, secrets, invented APIs, invented paths, or absolute local paths were added.

## Diff quality

- [ ] The diff matches the requested intent.
- [ ] The implementation follows adjacent style and existing project conventions.
- [ ] There are no architecture, security, product, release, or policy decisions hidden in the delegate diff.
- [ ] Imports, references, generated paths, and command names are real and consistent with the repo.

## Verification

- [ ] The required checks from the brief were run by Codex or their absence is justified.
- [ ] The checks passed, or failures are understood and reported.
- [ ] Any skipped, flaky, or unavailable checks are called out.

## Decision

- [ ] Accept: scope was respected, verification is adequate, and the diff is ready.
- [ ] Repair locally: small issues remain but are faster for Codex to fix than to delegate again.
- [ ] Reject: Claude drifted, failed scope, invented details, or left the task incomplete.

If any gate fails, do not treat wrapper `success` as completion. Fix the work locally or write a tighter brief before another delegation.
