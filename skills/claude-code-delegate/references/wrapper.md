# Claude wrapper reference

In this project, the `scripts/run_claude.sh` and `scripts/run_claude.ps1` wrappers live in the repository-root `scripts/` directory. They run Claude Code CLI synchronously, detect quota and rate-limit failures, write sentinel files, capture delegate output, and emit a machine-readable `<log>.result.json`.

For installed skill use outside this repo, run from this repo/project root or adapt/copy the wrapper path to wherever you installed the scripts.

## Bash invocation

```bash
bash scripts/run_claude.sh \
  --prompt "Read .ai/claude_task_<name>.md and execute all instructions inside." \
  --repo "$PWD" \
  --log-file .ai/claude_log_<name>.txt \
  --output-file .ai/claude_output_<name>.json
```

Optional flags:

- `--repo <path>`: project root. Defaults to the caller's `$PWD`.
- `--model <name>`: model string passed to `claude --model`.
- `--output-file <path>`: file where the wrapper writes captured delegate output.
- `--log-file <path>`: wrapper log path. Defaults to `.ai/claude_output.txt` under the repo.
- `--allowed-tools <list>`: comma-separated Claude tool allowlist. Defaults to `Read,Edit,Bash`.
- `--no-bare`: disables the wrapper's default `--bare` mode.
- `--synchronous`: accepted for parity with other wrappers; the wrapper already runs synchronously.

## PowerShell invocation

```powershell
& ".\scripts\run_claude.ps1" `
    -Prompt "Read .ai/claude_task_<name>.md and execute all instructions inside." `
    -Repo (Get-Location).Path `
    -LogFile ".ai\claude_log_<name>.txt" `
    -OutputFile ".ai\claude_output_<name>.json"
```

PowerShell parameters:

- `-Prompt` (required)
- `-Repo`
- `-Model`
- `-OutputFile`
- `-LogFile`
- `-AllowedTools`
- `-Bare`
- `-Synchronous`

Call the wrapper inline so the log, output file, sentinel files, and result JSON are written before Codex reads them.

## Environment variables

- `CLAUDE_PATH`: override the Claude executable, useful for custom installs or tests.
- `PYTHON_BIN`: Bash wrapper only; override the Python executable used for JSON escaping and changed-file calculation.

## Sentinels

| File | Meaning |
|---|---|
| `<log>.done` | Wrapper finished successfully or entered fallback. |
| `<log>.error` | Wrapper hit a hard failure or quota/rate-limit condition. |
| `<log>.fallback_codex` | Claude quota or rate limit was detected; Codex must take over. |
| `<log>.result.json` | Machine-readable status contract, always written when the wrapper reaches result handling. |

## Output file behavior

`--output-file` is not passed through to Claude Code CLI. The wrapper captures Claude's stdout/stderr output and writes it to the requested file itself. Treat this as the raw delegate transcript or JSON-formatted Claude response, depending on the active Claude CLI output format.
