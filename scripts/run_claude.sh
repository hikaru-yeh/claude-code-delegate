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
