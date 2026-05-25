# Changelog

All notable changes to `claude-code-delegate` are documented here. The project follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) formatting.

## Unreleased

### Changed

- Reversed the delegation direction: Codex is now the supervisor, and local Claude Code CLI is the execution specialist.
- Documented `scripts/run_claude.sh` and `scripts/run_claude.ps1` as the supported synchronous wrappers.
- Updated the machine-readable output contract around `delegate: "claude"` and Codex-owned acceptance.
- Reframed the skill docs and review checklist for Codex-facing planning, review, and acceptance.
- Removed the old Codex delegate surface from user-facing documentation.

## 0.1.0 - 2026-05-25

### Added

- Initial Claude Code delegate workflow, including Bash and PowerShell wrappers.
- Wrapper regression tests for success contract generation, shell behavior, and changed-file attribution.
- Codex-facing skill documentation for task briefs, wrapper execution, result review, and acceptance.
