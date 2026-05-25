# Task: <Descriptive Task Name>
#
# INSTRUCTIONS FOR USE:
#   1. Copy this file to .ai/claude_task_<name>.md in your repo
#   2. Fill in each section below — be specific and include WHY not just WHAT
#   3. Launch with:
#      bash scripts/run_claude.sh \
#        --prompt "Read .ai/claude_task_<name>.md and execute all instructions." \
#        --log-file .ai/claude_log_<name>.txt
#   4. Codex reviews .result.json and git diff, runs tests, then accepts or rejects

## Context

- Repo root: current repository root
- Task type: [test generation / batch edit / migration / boilerplate / analysis]
- Key files to READ:
  - `src/module_a.py`
  - `src/module_b.py`
  - `tests/test_existing.py`  (reference for test style)
- Key files to WRITE:
  - `tests/test_module_a.py`

## Background

<!-- Why is this task needed? What problem does it solve? -->
<!-- Example: "We refactored the data loader in module_a.py and need test coverage before merging." -->

## Instructions

<!--
  Be explicit and step-by-step. Claude has no conversation history — everything it needs
  must be here. Include references to files by path, not by description.
-->

1. Read `src/module_a.py` to understand all public functions and their signatures.
2. Read `tests/test_existing.py` to understand the existing test style (fixtures, naming, assertions).
3. Generate pytest unit tests in `tests/test_module_a.py`:
   - Cover every public function
   - Include at least one happy-path and one edge-case test per function
   - Use fixtures for any repeated setup
   - Each test function must have a one-line docstring
4. In the final response, briefly summarize what was generated and any assumptions made.

## Constraints

- Do NOT modify any files outside the listed write paths
- Follow the existing code style exactly (indentation, naming conventions, import order)
- Do not add dependencies that aren't already in requirements.txt / pyproject.toml
- Do not call Codex or any other agent
- Do not edit README files unless Codex has already received explicit user confirmation
- If a function's behavior is ambiguous, add a comment in the test noting the assumption

## Expected Output

- `tests/test_module_a.py` — complete test file, all tests passing
- final response summary — which functions were covered, any issues encountered

## Verification (for Codex to run after Claude completes)

```bash
# Run after Claude finishes:
cd /path/to/repo
python -m pytest tests/test_module_a.py -v
```
