# Claude Code Delegate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Codex-oriented delegate skill that lets Codex act as supervisor and invoke local Claude Code CLI for scoped implementation-heavy work.

**Architecture:** Keep the original project's thin synchronous wrapper pattern, but reverse the direction: Codex writes a `.ai/claude_task_<name>.md` brief, runs `scripts/run_claude.*`, reads `<log>.result.json`, then reviews diff and verification before accepting. Do not build a persistent broker in this pass; one delegated run should produce one result contract.

**Tech Stack:** Codex skills, Claude Code CLI headless mode (`claude -p`), Bash, PowerShell, Python `pytest`, Git porcelain snapshots.

---

## Scope

This plan transforms the local fork from `codex-delegate` into `claude-code-delegate`.

The MVP supports:

- Codex supervisor instructions in `skills/claude-code-delegate/SKILL.md`
- Bash and PowerShell wrappers named `run_claude.sh` and `run_claude.ps1`
- Result files with `delegate: "claude"`
- Quota/rate-limit fallback back to Codex supervisor through `<log>.fallback_codex`
- Wrapper tests using fake Claude executables
- Reference docs for task briefs, wrapper usage, output contract, and acceptance review

The MVP excludes:

- A persistent background broker
- Slash commands
- Automatic GitHub fork creation
- Claude initiating calls back into Codex

## File Structure

- Create: `docs/superpowers/plans/2026-05-25-claude-code-delegate.md`
  - This implementation plan.
- Create: `scripts/run_claude.sh`
  - Bash wrapper around `claude -p`.
- Create: `scripts/run_claude.ps1`
  - PowerShell wrapper around `claude -p`.
- Modify: `tests/test_wrappers.py`
  - Replace Codex wrapper contract tests with Claude wrapper contract tests.
- Create: `skills/claude-code-delegate/SKILL.md`
  - Codex-facing skill instructions.
- Create: `skills/claude-code-delegate/references/task-template.md`
  - Brief template for `.ai/claude_task_<name>.md`.
- Create: `skills/claude-code-delegate/references/wrapper.md`
  - Wrapper invocation details.
- Create: `skills/claude-code-delegate/references/output-contract.md`
  - Result schema and status semantics.
- Create: `skills/claude-code-delegate/references/review-checklist.md`
  - Codex acceptance checklist after Claude returns.
- Delete after replacement tests pass: `scripts/run_codex.sh`
- Delete after replacement tests pass: `scripts/run_codex.ps1`
- Delete after replacement references exist: `skills/codex-delegate/`
- Modify only after README confirmation: `README.md`
- Modify only after README confirmation: `README_zh-TW.md`
- Modify only after README confirmation: `CHANGELOG.md`

## README Confirmation Gate

Before editing `README.md`, `README_zh-TW.md`, or `CHANGELOG.md`, stop and tell the user:

```text
This change reverses the user-visible behavior from Claude -> Codex delegation to Codex -> Claude delegation. README.md and README_zh-TW.md need synchronized updates covering installation, wrapper commands, result contract, and the new supervisor acceptance flow. Proposed docs plan: update README.md first, mirror the same sections in README_zh-TW.md, then add a CHANGELOG entry for the fork rename and reversed delegation direction.
```

Proceed with those docs only after the user confirms.

---

### Task 1: Baseline And Branch

**Files:**
- Verify: `README.md`
- Verify: `scripts/run_codex.sh`
- Verify: `scripts/run_codex.ps1`
- Verify: `tests/test_wrappers.py`

- [ ] **Step 1: Confirm the fork starts from a clean baseline**

Run:

```powershell
git status --short --branch
python -m pytest -q
```

Expected:

```text
## master...upstream/master
6 passed
```

If the exact test count differs because upstream changed, continue only when the test command exits 0.

- [ ] **Step 2: Create an implementation branch**

Run:

```powershell
git switch -c feat/claude-code-delegate
```

Expected:

```text
Switched to a new branch 'feat/claude-code-delegate'
```

- [ ] **Step 3: Commit the planning file**

Run:

```powershell
git add docs/superpowers/plans/2026-05-25-claude-code-delegate.md
git commit -m "docs: plan claude code delegate fork"
```

Expected:

```text
[feat/claude-code-delegate <hash>] docs: plan claude code delegate fork
```

---

### Task 2: Claude Wrapper Contract Tests

**Files:**
- Modify: `tests/test_wrappers.py`
- Test: `tests/test_wrappers.py`

- [ ] **Step 1: Replace Codex naming constants with Claude naming constants**

In `tests/test_wrappers.py`, keep the existing imports, `_resolve_bash()`, and `to_bash_path()` helpers. Replace Codex-specific test names and fixture executable names with Claude-specific ones.

Use this helper for fake JSON output in new tests:

```python
def read_result_json(log_file: Path) -> dict[str, object]:
    return json.loads(log_file.with_suffix(log_file.suffix + ".result.json").read_text(encoding="utf-8-sig"))
```

- [ ] **Step 2: Add the Bash success-contract test**

Add this test:

```python
@pytest.mark.skipif(_BASH is None, reason="bash (git-bash on Windows, system bash elsewhere) not available")
def test_run_claude_sh_writes_result_contract(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    fake_claude = tmp_path / "fake_claude.sh"
    fake_claude.write_text(
        "#!/usr/bin/env bash\n"
        "echo '{\"result\":\"delegate ok\"}'\n",
        encoding="utf-8",
        newline="\n",
    )
    if sys.platform != "win32":
        os.chmod(fake_claude, 0o755)

    log_file = repo / ".ai" / "claude_log.txt"
    env = os.environ.copy()
    env["CLAUDE_PATH"] = to_bash_path(fake_claude)

    proc = subprocess.run(
        [
            _BASH,
            "-lc",
            (
                f"chmod +x '{to_bash_path(fake_claude)}' && "
                f"CLAUDE_PATH='{to_bash_path(fake_claude)}' "
                f"'{to_bash_path(Path(_BASH))}' '{to_bash_path(ROOT / 'scripts' / 'run_claude.sh')}' "
                f"--prompt 'do work' "
                f"--repo '{to_bash_path(repo)}' "
                f"--log-file '{to_bash_path(log_file)}'"
            ),
        ],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    result = read_result_json(log_file)
    assert result["status"] == "success"
    assert result["delegate"] == "claude"
    assert result["model"] == "claude/default"
    assert result["log_file"].endswith("/repo/.ai/claude_log.txt")
    assert (repo / ".ai" / "claude_log.txt.done").exists()
```

- [ ] **Step 3: Add the Bash changed-files test**

Add this test:

```python
@pytest.mark.skipif(_BASH is None, reason="bash (git-bash on Windows, system bash elsewhere) not available")
@pytest.mark.skipif(shutil.which("git") is None, reason="git not on PATH")
def test_run_claude_sh_reports_files_changed(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)

    fake_claude = tmp_path / "fake_claude.sh"
    fake_claude.write_text(
        "#!/usr/bin/env bash\n"
        'echo "delegated content" > delegated_file.txt\n'
        "echo '{\"result\":\"delegate ok\"}'\n",
        encoding="utf-8",
        newline="\n",
    )
    if sys.platform != "win32":
        os.chmod(fake_claude, 0o755)

    log_file = repo / ".ai" / "claude_log.txt"
    env = os.environ.copy()
    env["CLAUDE_PATH"] = to_bash_path(fake_claude)

    proc = subprocess.run(
        [
            _BASH,
            "-lc",
            (
                f"chmod +x '{to_bash_path(fake_claude)}' && "
                f"CLAUDE_PATH='{to_bash_path(fake_claude)}' "
                f"'{to_bash_path(Path(_BASH))}' '{to_bash_path(ROOT / 'scripts' / 'run_claude.sh')}' "
                f"--prompt 'do work' "
                f"--repo '{to_bash_path(repo)}' "
                f"--log-file '{to_bash_path(log_file)}'"
            ),
        ],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    result = read_result_json(log_file)
    assert result["status"] == "success"
    assert result["files_changed"] == ["delegated_file.txt"]
```

- [ ] **Step 4: Add the PowerShell success-contract test**

Add this test:

```python
@pytest.mark.skipif(shutil.which("powershell") is None, reason="powershell not on PATH")
def test_run_claude_ps1_writes_result_contract(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    fake_claude = tmp_path / "claude.cmd"
    fake_claude.write_text("@echo off\r\necho {\"result\":\"delegate ok\"}\r\n", encoding="utf-8")

    log_file = repo / ".ai" / "claude_ps_log.txt"
    env = os.environ.copy()
    env["CLAUDE_PATH"] = str(fake_claude)

    proc = subprocess.run(
        [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "scripts" / "run_claude.ps1"),
            "-Prompt",
            "do work",
            "-Repo",
            str(repo),
            "-LogFile",
            str(log_file),
        ],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    result = read_result_json(log_file)
    assert result["status"] == "success"
    assert result["delegate"] == "claude"
    assert result["model"] == "claude/default"
```

- [ ] **Step 5: Add the PowerShell changed-files test**

Add this test:

```python
@pytest.mark.skipif(shutil.which("powershell") is None, reason="powershell not on PATH")
@pytest.mark.skipif(shutil.which("git") is None, reason="git not on PATH")
def test_run_claude_ps1_reports_files_changed(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)

    fake_claude = tmp_path / "claude.cmd"
    fake_claude.write_text(
        "@echo off\r\n"
        'echo delegated content>"%CD%\\delegated_file.txt"\r\n'
        "echo {\"result\":\"delegate ok\"}\r\n",
        encoding="utf-8",
    )

    log_file = repo / ".ai" / "claude_ps_log.txt"
    env = os.environ.copy()
    env["CLAUDE_PATH"] = str(fake_claude)

    proc = subprocess.run(
        [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "scripts" / "run_claude.ps1"),
            "-Prompt",
            "do work",
            "-Repo",
            str(repo),
            "-LogFile",
            str(log_file),
        ],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    result = read_result_json(log_file)
    assert result["status"] == "success"
    assert result["files_changed"] == ["delegated_file.txt"]
```

- [ ] **Step 6: Run tests and verify the expected failure**

Run:

```powershell
python -m pytest tests/test_wrappers.py -q
```

Expected:

```text
FAILED ... scripts/run_claude.sh ...
FAILED ... scripts/run_claude.ps1 ...
```

The failure proves the tests are exercising missing wrappers.

- [ ] **Step 7: Commit failing tests**

Run:

```powershell
git add tests/test_wrappers.py
git commit -m "test: define claude delegate wrapper contract"
```

Expected:

```text
[feat/claude-code-delegate <hash>] test: define claude delegate wrapper contract
```

---

### Task 3: Bash Claude Wrapper

**Files:**
- Create: `scripts/run_claude.sh`
- Test: `tests/test_wrappers.py`

- [ ] **Step 1: Create the Bash wrapper file**

Create `scripts/run_claude.sh` with executable line endings and this structure:

```bash
#!/usr/bin/env bash
# run_claude.sh - Run Claude Code CLI as a scoped implementation delegate.

set -euo pipefail

PYTHON_JSON_BIN="${PYTHON_BIN:-}"
if [[ -z "$PYTHON_JSON_BIN" ]]; then
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_JSON_BIN="python3"
    elif command -v python >/dev/null 2>&1; then
        PYTHON_JSON_BIN="python"
    else
        echo "Error: python3 or python is required for JSON escaping" >&2
        exit 1
    fi
fi

json_escape() {
    "$PYTHON_JSON_BIN" -c 'import json,sys; print(json.dumps(sys.stdin.read()))'
}

git_status_snapshot() {
    git -C "$1" -c core.quotePath=false status --porcelain 2>/dev/null || true
}

compute_files_changed_json() {
    "$PYTHON_JSON_BIN" -c '
import json, sys
before = set(sys.argv[1].splitlines())
after = set(sys.argv[2].splitlines())
paths = set()
for line in after - before:
    entry = line[3:] if len(line) > 3 else ""
    if " -> " in entry:
        entry = entry.split(" -> ", 1)[1]
    entry = entry.strip().strip(chr(34))
    if entry:
        paths.add(entry)
print(json.dumps(sorted(paths)))
' "$1" "$2" 2>/dev/null || printf '[]'
}

write_result_json() {
    local status="$1"
    local model="$2"
    local summary="$3"
    local files_changed_json="${4:-[]}"
    local timestamp
    timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

    {
        printf '{\n'
        printf '  "status": %s,\n' "$(printf '%s' "$status" | json_escape)"
        printf '  "delegate": "claude",\n'
        printf '  "model": %s,\n' "$(printf '%s' "$model" | json_escape)"
        printf '  "log_file": %s,\n' "$(printf '%s' "$LOG_PATH" | json_escape)"
        printf '  "output_file": %s,\n' "$(printf '%s' "$OUTPUT_FILE" | json_escape)"
        printf '  "summary": %s,\n' "$(printf '%s' "$summary" | json_escape)"
        printf '  "risks": [],\n'
        printf '  "files_changed": %s,\n' "$files_changed_json"
        printf '  "tests_run": [],\n'
        printf '  "timestamp_utc": %s\n' "$(printf '%s' "$timestamp" | json_escape)"
        printf '}\n'
    } > "$RESULT_PATH"
}
```

- [ ] **Step 2: Add argument parsing**

Append this exact argument parser:

```bash
PROMPT=""
REPO="${PWD}"
MODEL=""
OUTPUT_FILE=""
LOG_FILE=""
ALLOWED_TOOLS="Read,Edit,Bash"
BARE=1

while [[ $# -gt 0 ]]; do
    case "$1" in
        --prompt)        PROMPT="$2";        shift 2 ;;
        --repo)          REPO="$2";          shift 2 ;;
        --model)         MODEL="$2";         shift 2 ;;
        --output-file)   OUTPUT_FILE="$2";   shift 2 ;;
        --log-file)      LOG_FILE="$2";      shift 2 ;;
        --allowed-tools) ALLOWED_TOOLS="$2"; shift 2 ;;
        --no-bare)       BARE=0;             shift ;;
        --synchronous)   shift ;;
        *) echo "Unknown argument: $1" >&2; exit 1 ;;
    esac
done

if [[ -z "$PROMPT" ]]; then
    echo "Error: --prompt is required" >&2
    exit 1
fi

AI_DIR="$REPO/.ai"
LOG_PATH="${LOG_FILE:-$AI_DIR/claude_output.txt}"
DONE_PATH="$LOG_PATH.done"
ERROR_PATH="$LOG_PATH.error"
FALLBACK_PATH="$LOG_PATH.fallback_codex"
RESULT_PATH="$LOG_PATH.result.json"

mkdir -p "$AI_DIR"
rm -f "$FALLBACK_PATH" "$DONE_PATH" "$ERROR_PATH" "$RESULT_PATH"
```

- [ ] **Step 3: Add quota detection and Claude CLI invocation**

Append this execution block:

```bash
is_quota_error() {
    local output="$1"
    local exit_code="$2"

    [[ "$exit_code" -eq 429 ]] && return 0

    local patterns=(
        "quota exceeded"
        "rate limit"
        "rate_limit"
        "quota_exceeded"
        "insufficient_quota"
        "too many requests"
        "429"
    )
    for p in "${patterns[@]}"; do
        if echo "$output" | grep -qi "$p"; then
            return 0
        fi
    done
    return 1
}

CLAUDE_BIN="${CLAUDE_PATH:-claude}"
CLAUDE_ARGS=()
[[ "$BARE" -eq 1 ]] && CLAUDE_ARGS+=("--bare")
CLAUDE_ARGS+=("-p" "$PROMPT" "--output-format" "json" "--allowedTools" "$ALLOWED_TOOLS")
[[ -n "$MODEL" ]] && CLAUDE_ARGS+=("--model" "$MODEL")

MODEL_LABEL="claude/default"
[[ -n "$MODEL" ]] && MODEL_LABEL="claude/$MODEL"

OUTPUT=""
EXIT_CODE=0
CHANGED_BEFORE="$(git_status_snapshot "$REPO")"

OUTPUT=$(
    cd "$REPO"
    "$CLAUDE_BIN" "${CLAUDE_ARGS[@]}" </dev/null 2>&1
) || EXIT_CODE=$?

CHANGED_AFTER="$(git_status_snapshot "$REPO")"
FILES_CHANGED_JSON="$(compute_files_changed_json "$CHANGED_BEFORE" "$CHANGED_AFTER")"

if is_quota_error "$OUTPUT" "$EXIT_CODE"; then
    echo "Claude quota/rate-limit exceeded; creating .fallback_codex sentinel for Codex to handle" >&2
    {
        echo "[CLAUDE QUOTA EXCEEDED at $(date -u +%Y-%m-%dT%H:%M:%SZ)]"
        echo "$OUTPUT"
    } > "$LOG_PATH"
    echo "ALL_QUOTA_EXCEEDED|$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$ERROR_PATH"
    echo "FALLBACK_TO_CODEX|$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$FALLBACK_PATH"
    echo "FALLBACK|$MODEL_LABEL|$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$DONE_PATH"
    write_result_json "fallback" "$MODEL_LABEL" "Claude quota exceeded; Codex must take over." "$FILES_CHANGED_JSON"
    exit 0
fi

if [[ "$EXIT_CODE" -ne 0 ]]; then
    echo "Claude hard failure (exit $EXIT_CODE)" >&2
    echo "$OUTPUT" > "$ERROR_PATH"
    write_result_json "error" "$MODEL_LABEL" "Claude exited with a hard failure." "$FILES_CHANGED_JSON"
    exit 1
fi

{
    echo "[MODEL_USED: $MODEL_LABEL]"
    echo "$OUTPUT"
} > "$LOG_PATH"
echo "DONE|$MODEL_LABEL|$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$DONE_PATH"
write_result_json "success" "$MODEL_LABEL" "Claude completed successfully. Codex must still review diff and run verification." "$FILES_CHANGED_JSON"
```

- [ ] **Step 4: Make the wrapper executable on non-Windows hosts**

Run:

```powershell
git update-index --chmod=+x scripts/run_claude.sh
```

Expected:

```text
```

The command exits 0 and prints no output.

- [ ] **Step 5: Run Bash-focused wrapper tests**

Run:

```powershell
python -m pytest tests/test_wrappers.py -q -k "run_claude_sh"
```

Expected:

```text
2 passed
```

- [ ] **Step 6: Commit Bash wrapper**

Run:

```powershell
git add scripts/run_claude.sh tests/test_wrappers.py
git commit -m "feat: add bash claude delegate wrapper"
```

Expected:

```text
[feat/claude-code-delegate <hash>] feat: add bash claude delegate wrapper
```

---

### Task 4: PowerShell Claude Wrapper

**Files:**
- Create: `scripts/run_claude.ps1`
- Test: `tests/test_wrappers.py`

- [ ] **Step 1: Create the PowerShell wrapper header and parameters**

Create `scripts/run_claude.ps1` with this header:

```powershell
param(
    [Parameter(Mandatory = $true)][string]$Prompt,
    [string]$Repo = "",
    [string]$Model = "",
    [string]$OutputFile = "",
    [string]$LogFile = "",
    [string]$AllowedTools = "Read,Edit,Bash",
    [bool]$Bare = $true,
    [bool]$Synchronous = $true
)

if (-not $Repo) { $Repo = (Get-Location).Path }

$ErrorActionPreference = "Continue"

[Console]::InputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
chcp 65001 | Out-Null

$logPath = if ($LogFile) { $LogFile } else { Join-Path (Join-Path $Repo ".ai") "claude_output.txt" }
$donePath = "$logPath.done"
$errorPath = "$logPath.error"
$fallbackPath = "$logPath.fallback_codex"
$resultPath = "$logPath.result.json"

$aiDir = Join-Path $Repo ".ai"
if (!(Test-Path $aiDir)) { New-Item -ItemType Directory -Path $aiDir -Force | Out-Null }

Remove-Item $fallbackPath -ErrorAction SilentlyContinue
Remove-Item $donePath -ErrorAction SilentlyContinue
Remove-Item $errorPath -ErrorAction SilentlyContinue
Remove-Item $resultPath -ErrorAction SilentlyContinue
```

- [ ] **Step 2: Add helper functions**

Append these helpers:

```powershell
function Test-QuotaError {
    param([string]$Output, [int]$ExitCode)

    if ($ExitCode -eq 429) { return $true }
    $patterns = @(
        "quota exceeded", "rate limit", "rate_limit", "quota_exceeded",
        "insufficient_quota", "too many requests", "429"
    )
    foreach ($pattern in $patterns) {
        if ($Output -ilike "*$pattern*") { return $true }
    }
    return $false
}

function ConvertTo-JsonScalar($value) {
    if ($null -eq $value) { $value = "" }
    return ([string]$value | ConvertTo-Json -Compress)
}

function Write-ResultJson {
    param(
        [string]$Status,
        [string]$ModelUsed,
        [string]$Summary,
        [string[]]$FilesChanged = @()
    )

    $filesArr =
        if ($FilesChanged -and @($FilesChanged).Count -gt 0) {
            "[" + ((@($FilesChanged) | ForEach-Object { ConvertTo-JsonScalar $_ }) -join ",") + "]"
        } else { "[]" }

    $timestamp = [DateTime]::UtcNow.ToString("o")
    $json = (@(
        "{",
        ('  "status": ' + (ConvertTo-JsonScalar $Status) + ","),
        '  "delegate": "claude",',
        ('  "model": ' + (ConvertTo-JsonScalar $ModelUsed) + ","),
        ('  "log_file": ' + (ConvertTo-JsonScalar $logPath) + ","),
        ('  "output_file": ' + (ConvertTo-JsonScalar $OutputFile) + ","),
        ('  "summary": ' + (ConvertTo-JsonScalar $Summary) + ","),
        '  "risks": [],',
        ('  "files_changed": ' + $filesArr + ","),
        '  "tests_run": [],',
        ('  "timestamp_utc": ' + (ConvertTo-JsonScalar $timestamp)),
        "}"
    ) -join "`n")

    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($resultPath, $json, $utf8NoBom)
}

function Get-GitStatusSnapshot {
    param([string]$Path)
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { return @() }
    $out = & git -C $Path -c core.quotePath=false status --porcelain 2>$null
    if ($LASTEXITCODE -ne 0) { return @() }
    return @($out | Where-Object { $null -ne $_ })
}

function Get-FilesChanged {
    param([string[]]$Before = @(), [string[]]$After = @())
    $beforeSet = New-Object 'System.Collections.Generic.HashSet[string]'
    foreach ($line in $Before) { [void]$beforeSet.Add($line) }
    $paths = New-Object 'System.Collections.Generic.List[string]'
    foreach ($line in $After) {
        if ($beforeSet.Contains($line)) { continue }
        $entry = if ($line.Length -gt 3) { $line.Substring(3) } else { "" }
        if ($entry -match ' -> ') { $entry = ($entry -split ' -> ', 2)[1] }
        $entry = $entry.Trim().Trim('"')
        if ($entry) { [void]$paths.Add($entry) }
    }
    return @($paths | Sort-Object -Unique)
}
```

- [ ] **Step 3: Add Claude CLI execution**

Append this execution block:

```powershell
$claudeBin = if ($env:CLAUDE_PATH) { $env:CLAUDE_PATH } else { "claude" }
$claudeArgs = @()
if ($Bare) { $claudeArgs += @("--bare") }
$claudeArgs += @("-p", $Prompt, "--output-format", "json", "--allowedTools", $AllowedTools)
if ($Model) { $claudeArgs += @("--model", $Model) }

$modelLabel = if ($Model) { "claude/$Model" } else { "claude/default" }

$changedBefore = Get-GitStatusSnapshot -Path $Repo
$filesChanged = @()

try {
    Push-Location $Repo
    try {
        $output = & $claudeBin @claudeArgs 2>&1 | Out-String
        $exitCode = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }

    $changedAfter = Get-GitStatusSnapshot -Path $Repo
    $filesChanged = @(Get-FilesChanged -Before $changedBefore -After $changedAfter)

    if (Test-QuotaError -Output $output -ExitCode $exitCode) {
        Write-Warning "Claude quota/rate-limit exceeded; creating .fallback_codex sentinel for Codex to handle"
        "[CLAUDE QUOTA EXCEEDED at $(Get-Date -Format o)]`n$output" | Out-File $logPath -Encoding utf8
        "ALL_QUOTA_EXCEEDED|$(Get-Date -Format o)" | Out-File $errorPath -Encoding utf8
        "FALLBACK_TO_CODEX|$(Get-Date -Format o)" | Out-File $fallbackPath -Encoding utf8
        "FALLBACK|$modelLabel|$(Get-Date -Format o)" | Out-File $donePath -Encoding utf8
        Write-ResultJson -Status "fallback" -ModelUsed $modelLabel -Summary "Claude quota exceeded; Codex must take over." -FilesChanged $filesChanged
        exit 0
    }

    if ($exitCode -ne 0) {
        $output | Out-File $errorPath -Encoding utf8
        Write-ResultJson -Status "error" -ModelUsed $modelLabel -Summary "Claude exited with a hard failure." -FilesChanged $filesChanged
        exit 1
    }

    "[MODEL_USED: $modelLabel]`n$output" | Out-File $logPath -Encoding utf8
    "DONE|$modelLabel|$(Get-Date -Format o)" | Out-File $donePath -Encoding utf8
    Write-ResultJson -Status "success" -ModelUsed $modelLabel -Summary "Claude completed successfully. Codex must still review diff and run verification." -FilesChanged $filesChanged
}
catch {
    $errMsg = $_.Exception.Message
    $changedAfter = Get-GitStatusSnapshot -Path $Repo
    $filesChanged = @(Get-FilesChanged -Before $changedBefore -After $changedAfter)

    if (Test-QuotaError -Output $errMsg -ExitCode 0) {
        "[CLAUDE QUOTA EXCEPTION at $(Get-Date -Format o)]`n$errMsg" | Out-File $logPath -Encoding utf8
        "ALL_QUOTA_EXCEEDED|$(Get-Date -Format o)" | Out-File $errorPath -Encoding utf8
        "FALLBACK_TO_CODEX|$(Get-Date -Format o)" | Out-File $fallbackPath -Encoding utf8
        "FALLBACK|$modelLabel|$(Get-Date -Format o)" | Out-File $donePath -Encoding utf8
        Write-ResultJson -Status "fallback" -ModelUsed $modelLabel -Summary "Claude quota exception triggered fallback to Codex." -FilesChanged $filesChanged
        exit 0
    }

    $errMsg | Out-File $errorPath -Encoding utf8
    Write-ResultJson -Status "error" -ModelUsed $modelLabel -Summary "Claude exited with a hard failure." -FilesChanged $filesChanged
    exit 1
}
```

- [ ] **Step 4: Run PowerShell-focused wrapper tests**

Run:

```powershell
python -m pytest tests/test_wrappers.py -q -k "run_claude_ps1"
```

Expected:

```text
2 passed
```

- [ ] **Step 5: Run all wrapper tests**

Run:

```powershell
python -m pytest tests/test_wrappers.py -q
```

Expected:

```text
4 passed
```

If old Codex tests are still present, the expected count will be higher; all tests must pass.

- [ ] **Step 6: Commit PowerShell wrapper**

Run:

```powershell
git add scripts/run_claude.ps1 tests/test_wrappers.py
git commit -m "feat: add powershell claude delegate wrapper"
```

Expected:

```text
[feat/claude-code-delegate <hash>] feat: add powershell claude delegate wrapper
```

---

### Task 5: Codex-Facing Skill And References

**Files:**
- Create: `skills/claude-code-delegate/SKILL.md`
- Create: `skills/claude-code-delegate/references/task-template.md`
- Create: `skills/claude-code-delegate/references/wrapper.md`
- Create: `skills/claude-code-delegate/references/output-contract.md`
- Create: `skills/claude-code-delegate/references/review-checklist.md`

- [ ] **Step 1: Create the skill directory**

Run:

```powershell
New-Item -ItemType Directory -Force -Path 'skills/claude-code-delegate/references' | Out-Null
```

Expected:

```text
```

The command exits 0 and prints no output.

- [ ] **Step 2: Create `SKILL.md`**

Create `skills/claude-code-delegate/SKILL.md` with:

````markdown
---
name: claude-code-delegate
description: Delegates implementation-heavy or repetitive coding work from Codex to local Claude Code CLI. Use when Codex should keep planning and review authority while Claude performs scoped edits, test scaffolding, or mechanical multi-file implementation. Avoid for architecture, security review, product decisions, or tasks where Claude would need to call Codex back.
license: MIT
compatibility: Designed for Codex skill hosts. Wrapper scripts live at <skill-root>/scripts/run_claude.sh and <skill-root>/scripts/run_claude.ps1; adapt paths to the installed skill directory.
---

# Claude Code Delegate Skill

Codex is the supervisor. Claude Code CLI runs the scoped implementation work. Codex writes the brief, launches Claude through the wrapper, reviews the diff, runs verification, and decides acceptance.

## Hard Rules

- Before invoking the wrapper, run `claude --version`. If it fails, stop and tell the user to install or authenticate Claude Code CLI.
- Use the wrapper for delegated shipping work; do not call `claude -p` directly unless diagnosing the wrapper itself.
- Wrapper success is not acceptance. Codex must inspect the diff and run the verification commands from the task brief.
- Do not ask Claude to call Codex. The delegate must only edit, test, and summarize.
- Prefer `--bare` through the wrapper unless the task explicitly needs Claude Code local hooks or plugins.
- Keep write scope narrow. Reject a run that edits outside the brief's allowed files.

## When To Delegate

Delegate to Claude when the task is clear, bounded, and implementation-heavy:

- mechanical multi-file edits
- boilerplate generation
- test scaffolding
- repetitive migration work
- implementation of a previously accepted plan checkpoint

Keep the work in Codex when the task needs supervisor judgment:

- architecture
- ambiguous debugging
- security review
- acceptance decisions
- prompt design for the next checkpoint

## Workflow

1. Write `.ai/claude_task_<name>.md` using `references/task-template.md`.
2. Run the wrapper from the repository root:
   ```bash
   bash scripts/run_claude.sh \
     --prompt "Read .ai/claude_task_<name>.md and execute all instructions inside." \
     --log-file .ai/claude_log_<name>.txt
   ```
3. Read `.ai/claude_log_<name>.txt.result.json`.
4. If `status` is `success`, review the diff and run verification.
5. If `status` is `fallback`, Codex takes over the same brief directly.
6. If `status` is `error`, read `<log>.error`, adjust the brief or wrapper invocation, and rerun only after the cause is understood.

## Output Contract

The wrapper writes `<log-file>.result.json` with `status`, `delegate`, `model`, `log_file`, `output_file`, `summary`, `risks`, `files_changed`, `tests_run`, and `timestamp_utc`. See `references/output-contract.md`.

## See Also

- `references/task-template.md`
- `references/wrapper.md`
- `references/output-contract.md`
- `references/review-checklist.md`
````

- [ ] **Step 3: Create the task template reference**

Create `skills/claude-code-delegate/references/task-template.md` with:

````markdown
# Claude task brief template

Save the brief at `.ai/claude_task_<name>.md`.

```markdown
# Task: <descriptive name>

## Context
- Repo: current repository root
- Read these files first:
  - path/a.py
  - path/b.py
- Only modify:
  - path/c.py
  - path/d.py

## Goal
State the exact implementation result Claude should produce.

## Constraints
- Do not edit files outside the allowed list.
- Follow adjacent code style.
- Do not make architecture changes.
- Do not call Codex or any other agent.
- Do not update README files unless the supervisor explicitly confirms a README update.

## Acceptance
- Required tests:
  - `python -m pytest tests/path/test_file.py -q`
- Required files_changed expectation:
  - `path/c.py`
  - `path/d.py`
- Required result summary:
  - Write a concise summary in the final Claude response.
```

## Brief Quality Rules

- The read list must name concrete files.
- The modify list is the write fence.
- Acceptance must include runnable commands.
- Claude should execute, not decide between product or architecture alternatives.
````

- [ ] **Step 4: Create the wrapper reference**

Create `skills/claude-code-delegate/references/wrapper.md` with:

````markdown
# Claude wrapper reference

The `scripts/run_claude.sh` and `scripts/run_claude.ps1` wrappers run Claude Code CLI synchronously, detect quota or rate-limit failures, write sentinel files, and emit `<log>.result.json`.

## Bash

```bash
bash scripts/run_claude.sh \
  --prompt "Read .ai/claude_task_<name>.md and execute all instructions inside." \
  --log-file .ai/claude_log_<name>.txt
```

Optional flags:

- `--repo <path>`: project root, defaulting to the caller's working directory
- `--model <name>`: passed to `claude --model`
- `--output-file <path>`: reserved in the result contract for parity with the original project
- `--allowed-tools <tools>`: passed to `claude --allowedTools`, defaulting to `Read,Edit,Bash`
- `--no-bare`: omit `--bare` when Claude local config is required

## PowerShell

```powershell
& ./scripts/run_claude.ps1 `
    -Prompt "Read .ai/claude_task_<name>.md and execute all instructions inside." `
    -LogFile ".ai/claude_log_<name>.txt"
```

PowerShell parameters:

- `-Prompt`
- `-Repo`
- `-Model`
- `-OutputFile`
- `-LogFile`
- `-AllowedTools`
- `-Bare`
- `-Synchronous`

## Environment Variables

- `CLAUDE_PATH`: override the Claude executable for tests or custom environments
- `PYTHON_BIN`: Bash wrapper JSON escaping interpreter

## Sentinels

| File | Meaning |
|---|---|
| `<log>.done` | Wrapper finished with success or fallback |
| `<log>.error` | Wrapper hit hard failure or quota |
| `<log>.fallback_codex` | Claude quota exceeded; Codex must take over |
| `<log>.result.json` | Machine-readable status |
````

- [ ] **Step 5: Create the output contract reference**

Create `skills/claude-code-delegate/references/output-contract.md` with:

````markdown
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
  "files_changed": ["path/changed_by_claude.py"],
  "tests_run": [],
  "timestamp_utc": "2026-05-25T00:00:00Z"
}
```

## Status Semantics

| Status | Meaning | Codex next move |
|---|---|---|
| `success` | Claude exited 0 | Read the diff, run verification, decide acceptance |
| `fallback` | Claude hit quota or rate limit | Codex takes over the same task brief directly |
| `error` | Claude exited non-zero with a hard failure | Read `<log>.error`, diagnose, and rerun only after the cause is understood |

## Field Ownership

| Field | Source |
|---|---|
| `status` | wrapper |
| `delegate` | wrapper |
| `model` | wrapper |
| `log_file` | wrapper |
| `output_file` | wrapper |
| `summary` | wrapper |
| `risks` | Codex acceptance review |
| `files_changed` | wrapper, derived from Git porcelain snapshot diff |
| `tests_run` | Codex acceptance review |
| `timestamp_utc` | wrapper |

## Acceptance Rule

`success` means the delegate process finished. It does not mean the change is accepted. Codex must review scope, inspect changed files, and run the brief's verification commands.
````

- [ ] **Step 6: Create the review checklist reference**

Create `skills/claude-code-delegate/references/review-checklist.md` with:

````markdown
# Claude delegate review checklist

Before accepting a Claude run, Codex must verify each item.

## Brief Quality

- [ ] The task file named concrete files to read.
- [ ] The task file listed allowed files to modify.
- [ ] The task file specified runnable verification commands.

## Execution Scope

- [ ] Claude stayed inside the allowed write scope.
- [ ] There are no unexpected file additions or deletions.
- [ ] There are no README changes unless the user confirmed the README gate.

## Diff Quality

- [ ] The diff matches the requested checkpoint.
- [ ] The change follows adjacent style.
- [ ] There are no invented APIs, paths, credentials, or absolute local paths.

## Verification

- [ ] The verification commands listed in the brief ran.
- [ ] The verification commands passed.
- [ ] Skipped or unavailable checks are recorded in the supervisor response.

## Decision

If any answer is no, reject the run, tighten the brief, or finish the work directly in Codex.
````

- [ ] **Step 7: Commit skill references**

Run:

```powershell
git add skills/claude-code-delegate
git commit -m "docs: add codex-facing claude delegate skill"
```

Expected:

```text
[feat/claude-code-delegate <hash>] docs: add codex-facing claude delegate skill
```

---

### Task 6: Remove Original Codex Delegate Surface

**Files:**
- Delete: `scripts/run_codex.sh`
- Delete: `scripts/run_codex.ps1`
- Delete: `skills/codex-delegate/`
- Modify: `tests/test_wrappers.py`

- [ ] **Step 1: Remove original Codex wrapper files**

Run:

```powershell
git rm scripts/run_codex.sh scripts/run_codex.ps1
```

Expected:

```text
rm 'scripts/run_codex.sh'
rm 'scripts/run_codex.ps1'
```

- [ ] **Step 2: Remove original Codex skill directory**

Run:

```powershell
git rm -r skills/codex-delegate
```

Expected:

```text
rm 'skills/codex-delegate/SKILL.md'
```

Git will also list the removed reference files.

- [ ] **Step 3: Remove remaining Codex-specific wrapper tests**

In `tests/test_wrappers.py`, remove test functions whose names start with `test_run_codex_`. Keep all helper functions that the Claude tests use.

Run:

```powershell
rg "run_codex|codex-delegate|CODEX_PATH" tests scripts skills
```

Expected:

```text
```

The command exits 1 when no matches are found. That is acceptable for `rg` no-match output.

- [ ] **Step 4: Run the wrapper test suite**

Run:

```powershell
python -m pytest tests/test_wrappers.py -q
```

Expected:

```text
4 passed
```

- [ ] **Step 5: Commit removal**

Run:

```powershell
git add tests/test_wrappers.py
git commit -m "refactor: remove codex delegate surface"
```

Expected:

```text
[feat/claude-code-delegate <hash>] refactor: remove codex delegate surface
```

---

### Task 7: README And Changelog After User Confirmation

**Files:**
- Modify after confirmation: `README.md`
- Modify after confirmation: `README_zh-TW.md`
- Modify after confirmation: `CHANGELOG.md`

- [ ] **Step 1: Ask for README confirmation**

Tell the user:

```text
This change reverses the user-visible behavior from Claude -> Codex delegation to Codex -> Claude delegation. README.md and README_zh-TW.md need synchronized updates covering installation, wrapper commands, result contract, and the new supervisor acceptance flow. Proposed docs plan: update README.md first, mirror the same sections in README_zh-TW.md, then add a CHANGELOG entry for the fork rename and reversed delegation direction.
```

Continue only after the user confirms.

- [ ] **Step 2: Rewrite README identity and core pattern**

In `README.md`, set the title and opening to:

````markdown
# Claude Code Delegate

`claude-code-delegate` is a Codex-oriented skill for using local Claude Code CLI as an execution specialist for implementation-heavy coding work while keeping planning, review, and acceptance in Codex.
````

Replace the core pattern with:

````markdown
## Core Pattern

1. Codex writes a task file describing scope and constraints.
2. Codex launches Claude Code CLI synchronously through the wrapper.
3. The wrapper emits sentinel files plus `result.json`.
4. Codex reviews the diff and runs verification before accepting the result.

Wrapper success is not final acceptance. Codex still owns the judgment.
````

- [ ] **Step 3: Rewrite README installation and testing**

In `README.md`, set testing to:

````markdown
## Testing

```bash
python -m pytest -q
```

Current wrapper tests cover:

- success-path `result.json` generation
- Bash and PowerShell wrapper contract behavior
- changed-file attribution through Git porcelain snapshots
````

Set installation to:

````markdown
## Installation

1. Copy or install `skills/claude-code-delegate` into your Codex skills directory.
2. Make sure Claude Code CLI is on `PATH`:

```bash
claude --version
```

3. From a repository root, create `.ai/claude_task_<name>.md` and invoke:

```bash
bash scripts/run_claude.sh \
  --prompt "Read .ai/claude_task_<name>.md and execute all instructions inside." \
  --log-file .ai/claude_log_<name>.txt
```
````

- [ ] **Step 4: Mirror README changes in Traditional Chinese**

In `README_zh-TW.md`, mirror the same sections in Traditional Chinese:

```markdown
# Claude Code Delegate

`claude-code-delegate` 是面向 Codex 的 skill，用來把實作量大、模式清楚的工作委派給本機 Claude Code CLI，同時保留 Codex 的規劃、審核與驗收權。

## 核心模式

1. Codex 撰寫描述範圍與限制的任務檔。
2. Codex 透過 wrapper 同步啟動 Claude Code CLI。
3. wrapper 產生 sentinel 檔案與 `result.json`。
4. Codex 審查 diff 並執行驗證後才接受結果。

wrapper 成功不代表最終驗收。判斷權仍在 Codex。
```

- [ ] **Step 5: Add CHANGELOG entry**

Add a top entry to `CHANGELOG.md`:

```markdown
## Unreleased

- Forked the project direction from Claude-supervised Codex delegation to Codex-supervised Claude Code delegation.
- Added `run_claude.sh` and `run_claude.ps1` wrappers with `delegate: "claude"` result contracts.
- Added Codex-facing skill documentation and review checklist.
```

- [ ] **Step 6: Run docs consistency checks**

Run:

```powershell
rg "codex-delegate|run_codex|CODEX_PATH|Claude is the supervisor|Codex CLI runs" README.md README_zh-TW.md CHANGELOG.md skills scripts tests
```

Expected:

```text
```

The command exits 1 when no matches remain. That no-match result is the desired docs state.

- [ ] **Step 7: Commit docs update**

Run:

```powershell
git add README.md README_zh-TW.md CHANGELOG.md
git commit -m "docs: describe claude code delegate workflow"
```

Expected:

```text
[feat/claude-code-delegate <hash>] docs: describe claude code delegate workflow
```

---

### Task 8: End-To-End Smoke Test

**Files:**
- Verify: `scripts/run_claude.sh`
- Verify: `scripts/run_claude.ps1`
- Verify: `skills/claude-code-delegate/SKILL.md`

- [ ] **Step 1: Verify Claude CLI is available**

Run:

```powershell
claude --version
```

Expected:

```text
<claude version output>
```

If this fails, stop and tell the user to install or authenticate Claude Code CLI.

- [ ] **Step 2: Create a smoke-test task brief**

Run:

```powershell
New-Item -ItemType Directory -Force -Path '.ai' | Out-Null
Set-Content -Path '.ai/claude_task_smoke.md' -Encoding utf8 -Value @'
# Task: smoke test

## Context
- Repo: current repository root
- Read these files first:
  - README.md
- Only modify:
  - .ai/claude_smoke_output.txt

## Goal
Create `.ai/claude_smoke_output.txt` containing exactly:
claude delegate smoke ok

## Constraints
- Do not edit files outside `.ai/claude_smoke_output.txt`.
- Do not call Codex.

## Acceptance
- Required tests:
  - `Get-Content .ai/claude_smoke_output.txt`
- Required files_changed expectation:
  - `.ai/claude_smoke_output.txt`
'@
```

Expected:

```text
```

The command exits 0 and prints no output.

- [ ] **Step 3: Run the PowerShell wrapper smoke test**

Run:

```powershell
& ./scripts/run_claude.ps1 `
  -Prompt "Read .ai/claude_task_smoke.md and execute all instructions inside." `
  -LogFile ".ai/claude_log_smoke.txt"
```

Expected:

```text
```

The command exits 0. Claude may print progress text; the required acceptance artifact is the result JSON.

- [ ] **Step 4: Inspect the result contract**

Run:

```powershell
Get-Content '.ai/claude_log_smoke.txt.result.json'
Get-Content '.ai/claude_smoke_output.txt'
```

Expected:

```json
"status": "success"
"delegate": "claude"
```

Expected file content:

```text
claude delegate smoke ok
```

- [ ] **Step 5: Clean smoke-test artifacts**

Run:

```powershell
Remove-Item '.ai/claude_task_smoke.md' -ErrorAction SilentlyContinue
Remove-Item '.ai/claude_log_smoke.txt*' -ErrorAction SilentlyContinue
Remove-Item '.ai/claude_smoke_output.txt' -ErrorAction SilentlyContinue
```

Expected:

```text
```

The command exits 0 and prints no output.

- [ ] **Step 6: Run final verification**

Run:

```powershell
python -m pytest -q
git status --short
```

Expected:

```text
4 passed
```

`git status --short` should show only intentional files that have not been committed.

- [ ] **Step 7: Final commit**

Run:

```powershell
git add .
git commit -m "test: verify claude delegate smoke path"
```

Expected:

```text
[feat/claude-code-delegate <hash>] test: verify claude delegate smoke path
```

---

## Self-Review

Spec coverage:

- Local fork creation is handled outside this implementation plan before execution.
- Reverse delegation direction is covered by Tasks 2 through 5.
- Codex supervisor acceptance is covered by `SKILL.md`, output contract, and review checklist.
- README consistency gate is covered by Task 7 before any README edits.
- Bash, PowerShell, and Windows behavior are covered by Tasks 3, 4, and 8.

Placeholder scan:

- The plan contains concrete file paths, commands, expected outcomes, and code blocks for code-writing steps.
- The plan does not rely on unspecified future design work.

Type and naming consistency:

- Wrapper names use `run_claude.*`.
- Environment override uses `CLAUDE_PATH`.
- Result contract uses `delegate: "claude"`.
- Fallback sentinel uses `<log>.fallback_codex`.
- Task brief names use `.ai/claude_task_<name>.md`.
