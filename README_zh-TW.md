# Claude Code Delegate

> [English](README.md)

`claude-code-delegate` 是一個以 Codex 為中心的 skill，用本機 Claude Code CLI 作為執行專家，同時由 Codex 保留規劃、審核與驗收。Codex 撰寫任務 brief，透過輕量 wrapper 啟動 Claude Code，檢查 wrapper 輸出與 git diff，最後才決定是否接受結果。

這個 repository 是早期委派方向的反轉 fork：現在 Codex 是 supervisor，Claude Code CLI 是 executor。

## 定位

這個 skill 適合 Codex 想保留判斷、但把執行委派出去的工作：

- 多檔案實作
- 機械式重構
- boilerplate 生成
- 測試骨架生成
- 大量批次修改

它不是 Codex 規劃、架構決策、root-cause analysis、安全性審查或最終驗收的替代品。

## 核心工作流

1. Codex 判斷任務已經足夠明確，可以委派。
2. Codex 撰寫 `.ai/claude_task_<name>.md`，描述範圍、限制、預期輸出與驗證重點。
3. Codex 透過 `scripts/run_claude.sh` 或 `scripts/run_claude.ps1` 同步啟動 Claude Code。
4. Wrapper 產生日誌、sentinel 檔與 `<log>.result.json`。
5. Codex 檢查 `.result.json`、changed-file attribution、git diff，以及相關測試輸出，再決定接受或拒絕結果。

Wrapper 成功不等於驗收通過。它只代表 Claude Code 執行產生了有效的 wrapper 結果；審核與最終判斷仍然由 Codex 負責。

## 專案結構

```text
claude-code-delegate/
├── README.md
├── README_zh-TW.md
├── CHANGELOG.md
├── skills/
│   └── claude-code-delegate/
├── scripts/
│   ├── run_claude.sh
│   └── run_claude.ps1
└── tests/
    └── test_wrappers.py
```

## 安裝

請先另外安裝 Claude Code CLI，並確認它在 `PATH` 上：

```bash
claude --version
```

將 `skills/claude-code-delegate` 安裝或複製到你本機 Codex workflow 使用的 skills 位置。如果你的 workflow 需要獨立 bundle，請讓 wrapper 腳本留在這個 repository，或和 skill 一起複製。

## 使用方式

先建立給 Claude Code 的任務 brief：

```bash
mkdir -p .ai
$EDITOR .ai/claude_task_example.md
```

執行 Bash wrapper：

```bash
bash scripts/run_claude.sh .ai/claude_task_example.md
```

或執行 PowerShell wrapper：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_claude.ps1 .ai/claude_task_example.md
```

Wrapper 結束後，Codex 會先審查產生的 `.result.json` 與 git diff，才接受工作。如果 wrapper 回報成功，但 diff 錯誤、不完整、風險太高或缺乏驗證，Codex 會拒絕或修正結果，而不是把 wrapper 成功當成任務完成。

## 輸出契約

Wrapper 會在 log 旁寫出機器可讀的 result file。契約包含：

- `delegate: "claude"`，表示執行者是 Claude Code。
- `fallback_codex`，用於 Codex 應該直接接手，而不是依賴本次委派結果的情境。
- wrapper 狀態與 sentinel metadata。
- Codex 審核時使用的 changed-file attribution。

Wrapper result 是審核依據，不是驗收決策。

## 測試

```bash
python -m pytest -q
```

Wrapper 測試涵蓋：

- success contract generation
- Bash behavior
- PowerShell behavior
- changed-file attribution

## License

MIT
