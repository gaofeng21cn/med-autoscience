# Progress projection JSON alias retirement closeout 2026-06-06

Owner: `MedAutoScience`
Purpose: `progress_projection_json_alias_retirement_closeout`
State: `history_provenance`
Machine boundary: 本文是人读退役 closeout。当前 CLI truth 继续归 `src/med_autoscience/cli_parts/parser.py`、`src/med_autoscience/cli_parts/study_read_commands.py`、workspace entry renderer、runtime contracts、tests 和 repo-native verification。

## Scope

本轮退役 `progress-projection <study_id> --json` 旧 JSON alias，统一结构化读面到 `--format json`。这是 CLI compatibility surface 清理；不改变 `progress-projection` 命令本身、不改变 `study-progress` 读模型、不改变 runtime truth、publication truth、owner receipt 或 OPL provider state。

## Current Contract

当前单 study Progress-first 结构化读面为：

```bash
ops/medautoscience/bin/progress-projection <study_id> --format json
```

Workspace 级矩阵读面为：

```bash
ops/medautoscience/bin/study-state-matrix --format json
```

`progress-projection <study_id> --json` 已退役。新文档、脚本、自动化、workspace README 和测试不得重新引入该 alias；需要 JSON 时必须显式使用 `--format json`。

## Changes

- `src/med_autoscience/cli_parts/parser.py`：删除 `progress-projection --json` parser alias。
- `src/med_autoscience/controllers/workspace_entry_rendering.py`：生成 workspace README 时只暴露 `--format json`。
- `src/med_autoscience/controllers/workspace_agents_template.py`：生成 workspace `AGENTS.md` 时只暴露 `--format json`。
- `docs/runtime/contracts/agent_runtime_interface.md`、`docs/runtime/projections/study_progress_projection.md`：把旧 alias 从兼容表述改为已退役表述。
- `tests/test_cli_cases/study_progress_monitoring_commands.py`：新增 parser negative guard，确认 `--json` fail closed，同时保留 `--format json`；同步修正 `progress-projection` 测试桩到当前 stage-native `study_progress.read_study_progress` 调用面。

## Root Cause Of Test Drift

旧测试仍 monkeypatch `domain_status_projection.progress_projection`，但当前 `progress-projection` 已通过 `study_read_commands.handle_study_read_command` 调用 `study_progress.read_study_progress`。这导致 focused tests 在读取默认 fixture profile 时误触真实 workspace 路径。修复方式是把测试绑定到当前实际调用面，并加旧 projection fail-fast 断言，防止 alias 路径回退。

## Verification

本轮已执行：

```bash
rtk ./scripts/run-pytest-clean.sh tests/test_cli_cases/study_progress_monitoring_commands.py tests/test_workspace_init_cases/workspace_creation.py tests/test_workspace_init_cases/legacy_entry_upgrades.py -q
rtk rg -n "progress-projection <study_id> --json|progress-projection.*--json|--json.*progress-projection|JSON alias|仍作为 JSON alias|仅作为 JSON alias|只作为旧 JSON alias" src tests docs/runtime docs/active docs/product docs/policies contracts || true
rtk git diff --check
rtk rg -n "^(<<<<<<<|=======|>>>>>>>)" docs/runtime/contracts/agent_runtime_interface.md docs/runtime/projections/study_progress_projection.md src/med_autoscience/cli_parts/parser.py src/med_autoscience/controllers/workspace_agents_template.py src/med_autoscience/controllers/workspace_entry_rendering.py tests/test_cli_cases/study_progress_monitoring_commands.py || true
rtk /Users/gaofeng/.local/bin/opl-doc-doctor doctor . --format json
```

Observed results:

- focused pytest: `19 passed`
- retired-alias scan: only the two expected retired wording hits remain in runtime docs
- `git diff --check`: pass
- conflict marker scan: no matches
- OPL doc doctor: `finding_count=0`

Default `scripts/verify.sh` should remain the final gate before absorption.

## Remaining Risk

History/provenance docs may still mention old commands as historical context. They are not current truth. Any active doc, generated workspace entry, script or test that needs JSON must use `--format json`.
