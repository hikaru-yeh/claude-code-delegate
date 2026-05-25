"""Wrapper contract tests.

Bash test:
- Linux / macOS: `bash` from PATH, POSIX paths.
- Windows: explicitly use git-bash at `C:\\Program Files\\Git\\bin\\bash.exe`
  if present. Avoids WSL bash on PATH which (when no distro is installed,
  e.g. on GitHub Actions windows-latest) emits UTF-16 banner output that
  pollutes subprocess pipes. Skipif when git-bash isn't found so plain
  Windows hosts without Git for Windows skip cleanly instead of failing.

PowerShell test:
- Skipif when `powershell` isn't on PATH so the test is a no-op on
  Linux / macOS runners.
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _resolve_bash() -> str | None:
    """Return a path to a bash interpreter we trust for the wrapper test.

    On Windows we explicitly prefer git-bash at the standard
    Git-for-Windows install path, because `shutil.which("bash")` may
    return WSL bash and WSL bash on a host without an installed distro
    prints a UTF-16 banner that contaminates subprocess pipes.
    """
    if sys.platform == "win32":
        for candidate in (
            r"C:\Program Files\Git\bin\bash.exe",
            r"C:\Program Files\Git\usr\bin\bash.exe",
            r"C:\Program Files (x86)\Git\bin\bash.exe",
        ):
            if Path(candidate).is_file():
                return candidate
        return None
    return shutil.which("bash")


def to_bash_path(path: Path) -> str:
    """Convert a Path to a form bash can use on the current platform.

    Windows + git-bash: `C:\\Users\\foo` -> `/c/Users/foo` (drive letter
    becomes a top-level mount in MSYS2). Linux / macOS: POSIX path
    unchanged.
    """
    resolved = path.resolve()
    if sys.platform == "win32":
        drive = resolved.drive.rstrip(":").lower()
        tail = resolved.as_posix().split(":", 1)[1]
        return f"/{drive}{tail}"
    return resolved.as_posix()


def bash_quote(path_or_text: str | Path) -> str:
    if isinstance(path_or_text, Path):
        return shlex.quote(to_bash_path(path_or_text))
    return shlex.quote(path_or_text)


_BASH = _resolve_bash()


def read_result_json(log_file: Path) -> dict[str, object]:
    return json.loads(log_file.with_suffix(log_file.suffix + ".result.json").read_text(encoding="utf-8-sig"))


@pytest.mark.skipif(_BASH is None, reason="bash (git-bash on Windows, system bash elsewhere) not available")
def test_run_claude_sh_writes_result_contract(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    fake_claude = tmp_path / "fake_claude.sh"
    fake_claude.write_text(
        "#!/usr/bin/env bash\n"
        'echo \'{"result":"delegate ok"}\'\n',
        encoding="utf-8",
        newline="\n",
    )
    if sys.platform != "win32":
        os.chmod(fake_claude, 0o755)

    log_file = repo / ".ai" / "claude_log.txt"
    output_file = repo / "outputs" / "claude_result.json"
    env = os.environ.copy()
    env["CLAUDE_PATH"] = to_bash_path(fake_claude)

    proc = subprocess.run(
        [
            _BASH,
            "-lc",
            (
                f"chmod +x {bash_quote(fake_claude)} && "
                f"CLAUDE_PATH={bash_quote(fake_claude)} "
                f"{bash_quote(Path(_BASH))} {bash_quote(ROOT / 'scripts' / 'run_claude.sh')} "
                f"--prompt {bash_quote('do work')} "
                f"--repo {bash_quote(repo)} "
                f"--log-file {bash_quote(log_file)} "
                f"--output-file {bash_quote(output_file)}"
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
    assert result["output_file"].endswith("/repo/outputs/claude_result.json")
    assert (repo / ".ai" / "claude_log.txt.done").exists()
    assert output_file.exists()
    assert output_file.read_text(encoding="utf-8").strip() == '{"result":"delegate ok"}'
    assert "[MODEL_USED:" not in output_file.read_text(encoding="utf-8")


@pytest.mark.skipif(_BASH is None, reason="bash (git-bash on Windows, system bash elsewhere) not available")
@pytest.mark.skipif(shutil.which("git") is None, reason="git not on PATH")
def test_run_claude_sh_reports_files_changed(tmp_path: Path) -> None:
    """files_changed is auto-derived from a git porcelain snapshot diff."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)

    fake_claude = tmp_path / "fake_claude.sh"
    fake_claude.write_text(
        "#!/usr/bin/env bash\n"
        "printf 'delegated content\\n' > delegated_file.txt\n"
        'echo \'{"result":"delegate ok"}\'\n',
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
                f"chmod +x {bash_quote(fake_claude)} && "
                f"CLAUDE_PATH={bash_quote(fake_claude)} "
                f"{bash_quote(Path(_BASH))} {bash_quote(ROOT / 'scripts' / 'run_claude.sh')} "
                f"--prompt {bash_quote('do work')} "
                f"--repo {bash_quote(repo)} "
                f"--log-file {bash_quote(log_file)}"
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


@pytest.mark.skipif(shutil.which("powershell") is None, reason="powershell not on PATH")
@pytest.mark.skipif(sys.platform != "win32", reason="PowerShell wrapper test uses Windows cmd fake executable")
def test_run_claude_ps1_writes_result_contract(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    fake_claude = tmp_path / "claude.cmd"
    fake_claude.write_text(
        "@echo off\r\n"
        'echo {"result":"delegate ok"}\r\n',
        encoding="utf-8",
    )

    log_file = repo / ".ai" / "claude_log.txt"
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


@pytest.mark.skipif(shutil.which("powershell") is None, reason="powershell not on PATH")
@pytest.mark.skipif(sys.platform != "win32", reason="PowerShell wrapper test uses Windows cmd fake executable")
@pytest.mark.skipif(shutil.which("git") is None, reason="git not on PATH")
def test_run_claude_ps1_reports_files_changed(tmp_path: Path) -> None:
    """PowerShell wrapper: files_changed is auto-derived from git porcelain."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)

    fake_claude = tmp_path / "claude.cmd"
    fake_claude.write_text(
        "@echo off\r\n"
        'echo delegated content>"%CD%\\delegated_file.txt"\r\n'
        'echo {"result":"delegate ok"}\r\n',
        encoding="utf-8",
    )

    log_file = repo / ".ai" / "claude_log.txt"
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
