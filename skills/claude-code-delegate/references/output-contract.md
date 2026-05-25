# Claude wrapper output contract

Every wrapper run leaves machine-readable status at `<log-file>.result.json`. This is the transport contract; Codex still owns acceptance.

## Schema

```json
{
  "status": "success|fallback|error",
  "delegate": "claude",
  "model": "claude/<model-or-default>",
  "log_file": "<path>",
  "output_file": "<path or empty>",
  "summary": "",
  "risks": [],
  "files_changed": ["path/changed_by_claude.ext"],
  "tests_run": [],
  "timestamp_utc": "2026-05-25T00:00:00Z"
}
```

## Status semantics

| Status | Meaning | Codex next move |
|---|---|---|
| `success` | Claude exited 0 and no quota or hard error was detected. | Review the diff, confirm scope, run verification, then accept or reject. |
| `fallback` | Claude hit quota or rate limits. | Take the work over directly in Codex using the same brief. Do not retry in a loop. |
| `error` | Claude exited non-zero or the wrapper hit a hard failure. | Read `<log>.error`, inspect the log/output, and decide whether to fix locally or rerun after correcting the issue. |

## Field ownership

| Field | Owner | Notes |
|---|---|---|
| `status` | wrapper | Transport status only. |
| `delegate` | wrapper | Always `claude`. |
| `model` | wrapper | `claude/default` when no model was provided, otherwise `claude/<model>`. |
| `log_file` | wrapper | The log path used for this run. |
| `output_file` | wrapper | The requested output path, or empty string. |
| `summary` | wrapper | Brief wrapper-level summary. Codex may supplement after review. |
| `risks` | Codex | Wrapper initializes this to `[]`; risk assessment is supervisor judgment. |
| `files_changed` | wrapper | Derived from git status before and after the run. Treat as a starting point and still inspect the diff. |
| `tests_run` | Codex | Wrapper initializes this to `[]`; Codex must run or verify tests during acceptance. |
| `timestamp_utc` | wrapper | UTC timestamp when the result JSON was written. |

## Acceptance rule

`success` means only that the delegate process completed. It does not mean the implementation is correct, scoped, tested, safe, or accepted. Codex must read the changed files, compare the diff against the task brief, run the required checks, and reject or repair any drift before reporting completion.
