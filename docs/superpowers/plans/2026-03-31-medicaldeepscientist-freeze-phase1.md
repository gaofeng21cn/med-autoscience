# MedicalDeepScientist Freeze Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在本机建立一个受控的 `MedicalDeepScientist` 冻结基线，带入首批确定性 runtime 修复，并让 `MedAutoScience` 的审计面能识别这个 fork，而不是继续把它当成普通 upstream checkout。

**Architecture:** Phase 1 只做三件事：一是在 `/Users/gaofeng/workspace/MedicalDeepScientist` 建立本地兄弟仓库，冻结到 `DeepScientist` 的 `a7853fda3432d37f6dee91fa6e66330f564bd8be` 并记录 machine-readable manifest；二是 cherry-pick `d4994dba3ae1720a60daa7c80f5043f3722f32d8` 修复 active worktree 下 PNG/SVG/PDF document asset 解析，并在 fork 内显式处理 `uv.lock`；三是在 `MedAutoScience` 中新增 repo manifest 解析与 upgrade-check / workspace contract 感知，让当前 runtime audit 能识别“这是受控 fork”这一事实。第一阶段不改 package/import 名称，不改 daemon API shape，不动 `study_runtime_router.py`、`python_environment_contract.py` 这些当前已有进行中修改的文件。

**Tech Stack:** Git, Python 3.12, JSON, PyYAML, pytest, `uv`, DeepScientist daemon tests

---

## File Structure

- Create: `/Users/gaofeng/workspace/MedicalDeepScientist/MEDICAL_FORK_MANIFEST.json`
- Create: `/Users/gaofeng/workspace/MedicalDeepScientist/docs/medical_fork_baseline.md`
- Modify: `/Users/gaofeng/workspace/MedicalDeepScientist/README.md`
- Modify: `/Users/gaofeng/workspace/MedicalDeepScientist/src/deepscientist/daemon/api/handlers.py`
- Modify: `/Users/gaofeng/workspace/MedicalDeepScientist/src/deepscientist/quest/service.py`
- Modify: `/Users/gaofeng/workspace/MedicalDeepScientist/tests/test_daemon_api.py`
- Modify: `/Users/gaofeng/workspace/MedicalDeepScientist/uv.lock`
- Create: `src/med_autoscience/deepscientist_repo_manifest.py`
- Modify: `src/med_autoscience/controllers/deepscientist_upgrade_check.py`
- Modify: `src/med_autoscience/workspace_contracts.py`
- Create: `tests/test_deepscientist_repo_manifest.py`
- Modify: `tests/test_deepscientist_upgrade_check.py`
- Modify: `tests/test_workspace_contracts.py`
- Modify: `guides/agent_runtime_interface.md`
- Modify: `guides/workspace_architecture.md`

说明：

- 本计划假定本地 sibling repo 路径固定为 `/Users/gaofeng/workspace/MedicalDeepScientist`。
- 本计划不处理 fork remote 命名与发布；这一点保留到下一阶段。
- 本计划不允许修改当前脏工作树中的 [study_runtime_router.py](/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/controllers/study_runtime_router.py)、[python_environment_contract.py](/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/python_environment_contract.py) 及对应测试。

### Task 1: 建立本地 `MedicalDeepScientist` 冻结基线与受控 fork manifest

**Files:**
- Create: `/Users/gaofeng/workspace/MedicalDeepScientist/MEDICAL_FORK_MANIFEST.json`
- Create: `/Users/gaofeng/workspace/MedicalDeepScientist/docs/medical_fork_baseline.md`
- Modify: `/Users/gaofeng/workspace/MedicalDeepScientist/README.md`

- [ ] **Step 1: 在本地 materialize 干净的 sibling repo，并固定到基线提交**

Run:

```bash
if [ -e /Users/gaofeng/workspace/MedicalDeepScientist ]; then
  echo "Refusing to overwrite existing /Users/gaofeng/workspace/MedicalDeepScientist" >&2
  exit 1
fi
git clone /Users/gaofeng/workspace/DeepScientist /Users/gaofeng/workspace/MedicalDeepScientist
git -C /Users/gaofeng/workspace/MedicalDeepScientist checkout --detach a7853fda3432d37f6dee91fa6e66330f564bd8be
git -C /Users/gaofeng/workspace/MedicalDeepScientist switch -c main
```

Expected:

- 新仓库存在于 `/Users/gaofeng/workspace/MedicalDeepScientist`
- `HEAD` 为 `a7853fda3432d37f6dee91fa6e66330f564bd8be`
- 工作树为 clean

- [ ] **Step 2: 写 machine-readable fork manifest**

Create `/Users/gaofeng/workspace/MedicalDeepScientist/MEDICAL_FORK_MANIFEST.json`:

```json
{
  "schema_version": 1,
  "engine_id": "medicaldeepscientist",
  "engine_family": "MedicalDeepScientist",
  "freeze_mode": "thin_fork",
  "upstream_source": {
    "repo_path": "/Users/gaofeng/workspace/DeepScientist",
    "base_commit": "a7853fda3432d37f6dee91fa6e66330f564bd8be"
  },
  "compatibility_contract": {
    "package_rename_applied": false,
    "daemon_api_shape_preserved": true,
    "quest_layout_preserved": true,
    "worktree_layout_preserved": true
  },
  "applied_commits": [],
  "lock_policy": {
    "mode": "regenerate_in_fork",
    "source_repo_was_dirty": true,
    "source_dirty_paths": [
      "uv.lock"
    ]
  }
}
```

- [ ] **Step 3: 写冻结说明文档并在 README 顶部补 fork 身份说明**

Create `/Users/gaofeng/workspace/MedicalDeepScientist/docs/medical_fork_baseline.md`:

```md
# MedicalDeepScientist Freeze Baseline

- engine_family: `MedicalDeepScientist`
- freeze_mode: `thin_fork`
- upstream_repo_path: `/Users/gaofeng/workspace/DeepScientist`
- upstream_base_commit: `a7853fda3432d37f6dee91fa6e66330f564bd8be`
- phase: `phase1_local_freeze`
- package_rename_applied: `false`
- daemon_api_shape_preserved: `true`
- quest_layout_preserved: `true`
- worktree_layout_preserved: `true`

This repository is a controlled local fork used to stabilize runtime truth before protocol convergence work begins in `MedAutoScience`.
```

Prepend to `/Users/gaofeng/workspace/MedicalDeepScientist/README.md`:

```md
> Controlled local fork for MedAutoScience runtime stabilization.
> Base commit: `a7853fda3432d37f6dee91fa6e66330f564bd8be`
> See `MEDICAL_FORK_MANIFEST.json` and `docs/medical_fork_baseline.md`.
```

- [ ] **Step 4: 验证冻结基线与 manifest 一致**

Run:

```bash
git -C /Users/gaofeng/workspace/MedicalDeepScientist rev-parse HEAD
git -C /Users/gaofeng/workspace/MedicalDeepScientist status --short
python3 - <<'PY'
import json
from pathlib import Path
manifest = json.loads(Path("/Users/gaofeng/workspace/MedicalDeepScientist/MEDICAL_FORK_MANIFEST.json").read_text())
assert manifest["engine_family"] == "MedicalDeepScientist"
assert manifest["upstream_source"]["base_commit"] == "a7853fda3432d37f6dee91fa6e66330f564bd8be"
assert manifest["applied_commits"] == []
print("manifest-ok")
PY
```

Expected:

- `rev-parse HEAD` 输出基线提交
- `status --short` 只显示本任务引入的新文件和 README 修改
- Python 校验输出 `manifest-ok`

- [ ] **Step 5: 提交本地冻结基线**

```bash
git -C /Users/gaofeng/workspace/MedicalDeepScientist add README.md MEDICAL_FORK_MANIFEST.json docs/medical_fork_baseline.md
git -C /Users/gaofeng/workspace/MedicalDeepScientist commit -m "chore: establish medicaldeepscientist freeze baseline"
```

### Task 2: 带入 `d4994db` 并在 fork 内显式处理 `uv.lock`

**Files:**
- Modify: `/Users/gaofeng/workspace/MedicalDeepScientist/src/deepscientist/daemon/api/handlers.py`
- Modify: `/Users/gaofeng/workspace/MedicalDeepScientist/src/deepscientist/quest/service.py`
- Modify: `/Users/gaofeng/workspace/MedicalDeepScientist/tests/test_daemon_api.py`
- Modify: `/Users/gaofeng/workspace/MedicalDeepScientist/uv.lock`
- Modify: `/Users/gaofeng/workspace/MedicalDeepScientist/MEDICAL_FORK_MANIFEST.json`
- Modify: `/Users/gaofeng/workspace/MedicalDeepScientist/docs/medical_fork_baseline.md`

- [ ] **Step 1: cherry-pick worktree document asset 修复提交**

Run:

```bash
git -C /Users/gaofeng/workspace/MedicalDeepScientist cherry-pick d4994dba3ae1720a60daa7c80f5043f3722f32d8
```

Expected:

- `handlers.py` 改为通过公开的 `resolve_document()` 解析 asset
- `quest/service.py` 新增 `resolve_document()` 帮助层
- `tests/test_daemon_api.py` 增加 active worktree 下 `svg/png/pdf` 的参数化测试

- [ ] **Step 2: 运行最小 targeted test，确认修复真实落地**

Run:

```bash
cd /Users/gaofeng/workspace/MedicalDeepScientist
PYTHONPATH=src pytest -q tests/test_daemon_api.py -k 'document_asset_resolves_path_documents_from_active_worktree'
```

Expected: `passed`

- [ ] **Step 3: 在 fork 内显式重建 `uv.lock`，不接受把源仓库的脏 lock 漂移隐式带入**

Run:

```bash
cd /Users/gaofeng/workspace/MedicalDeepScientist
uv lock
git diff -- uv.lock
```

Expected:

- `uv lock` 成功
- `uv.lock` 的变化只体现为当前 fork 头部状态对应的受控锁文件，不引入无关依赖漂移

- [ ] **Step 4: 更新 fork manifest 与基线说明，记录已带入补丁与 lock 决策**

Update `/Users/gaofeng/workspace/MedicalDeepScientist/MEDICAL_FORK_MANIFEST.json`:

```json
{
  "schema_version": 1,
  "engine_id": "medicaldeepscientist",
  "engine_family": "MedicalDeepScientist",
  "freeze_mode": "thin_fork",
  "upstream_source": {
    "repo_path": "/Users/gaofeng/workspace/DeepScientist",
    "base_commit": "a7853fda3432d37f6dee91fa6e66330f564bd8be"
  },
  "compatibility_contract": {
    "package_rename_applied": false,
    "daemon_api_shape_preserved": true,
    "quest_layout_preserved": true,
    "worktree_layout_preserved": true
  },
  "applied_commits": [
    {
      "commit": "d4994dba3ae1720a60daa7c80f5043f3722f32d8",
      "kind": "runtime_bugfix",
      "summary": "Fix worktree document asset resolution"
    }
  ],
  "lock_policy": {
    "mode": "regenerate_in_fork",
    "source_repo_was_dirty": true,
    "source_dirty_paths": [
      "uv.lock"
    ],
    "regenerated_after_commit": "d4994dba3ae1720a60daa7c80f5043f3722f32d8"
  }
}
```

Append to `/Users/gaofeng/workspace/MedicalDeepScientist/docs/medical_fork_baseline.md`:

```md
## Applied Phase 1 Patch

- commit: `d4994dba3ae1720a60daa7c80f5043f3722f32d8`
- kind: `runtime_bugfix`
- reason: `document_asset` must resolve path documents from the active worktree so Web App previews for PNG / SVG / PDF remain correct.
- verification: `PYTHONPATH=src pytest -q tests/test_daemon_api.py -k 'document_asset_resolves_path_documents_from_active_worktree'`
```

- [ ] **Step 5: 再跑一次 targeted test，并确认 fork 工作树 clean**

Run:

```bash
cd /Users/gaofeng/workspace/MedicalDeepScientist
PYTHONPATH=src pytest -q tests/test_daemon_api.py -k 'document_asset_resolves_path_documents_from_active_worktree'
git status --short
```

Expected:

- targeted test 继续 `passed`
- `status --short` 只剩本任务预期改动

- [ ] **Step 6: 提交首批 runtime fix**

```bash
git -C /Users/gaofeng/workspace/MedicalDeepScientist add src/deepscientist/daemon/api/handlers.py src/deepscientist/quest/service.py tests/test_daemon_api.py uv.lock MEDICAL_FORK_MANIFEST.json docs/medical_fork_baseline.md
git -C /Users/gaofeng/workspace/MedicalDeepScientist commit -m "fix: preserve active worktree document asset resolution"
```

### Task 3: 让 `MedAutoScience` 审计面识别受控 fork manifest

**Files:**
- Create: `src/med_autoscience/deepscientist_repo_manifest.py`
- Modify: `src/med_autoscience/controllers/deepscientist_upgrade_check.py`
- Modify: `src/med_autoscience/workspace_contracts.py`
- Create: `tests/test_deepscientist_repo_manifest.py`
- Modify: `tests/test_deepscientist_upgrade_check.py`
- Modify: `tests/test_workspace_contracts.py`

- [ ] **Step 1: 写失败测试，覆盖受控 fork manifest 解析**

Create `tests/test_deepscientist_repo_manifest.py`:

```python
from __future__ import annotations

import importlib
import json
from pathlib import Path


def test_inspect_repo_manifest_recognizes_controlled_fork(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.deepscientist_repo_manifest")
    repo_root = tmp_path / "MedicalDeepScientist"
    repo_root.mkdir()
    (repo_root / "MEDICAL_FORK_MANIFEST.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "engine_id": "medicaldeepscientist",
                "engine_family": "MedicalDeepScientist",
                "freeze_mode": "thin_fork",
                "upstream_source": {"repo_path": "/tmp/DeepScientist", "base_commit": "abc123"},
                "compatibility_contract": {
                    "package_rename_applied": False,
                    "daemon_api_shape_preserved": True,
                    "quest_layout_preserved": True,
                    "worktree_layout_preserved": True,
                },
                "applied_commits": [],
                "lock_policy": {"mode": "regenerate_in_fork", "source_repo_was_dirty": True, "source_dirty_paths": ["uv.lock"]},
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    result = module.inspect_deepscientist_repo_manifest(repo_root)

    assert result["manifest_exists"] is True
    assert result["manifest_valid"] is True
    assert result["engine_family"] == "MedicalDeepScientist"
    assert result["is_controlled_fork"] is True
    assert result["freeze_base_commit"] == "abc123"
```

- [ ] **Step 2: 写失败测试，覆盖 upgrade-check 与 workspace contract 对 manifest 的感知**

Add to `tests/test_deepscientist_upgrade_check.py`:

```python
def test_run_upgrade_check_surfaces_controlled_fork_manifest(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.deepscientist_upgrade_check")
    doctor = importlib.import_module("med_autoscience.doctor")
    profile = make_profile(tmp_path)

    monkeypatch.setattr(module, "inspect_deepscientist_repo", lambda *, repo_root, refresh=False: {
        "configured": True,
        "repo_root": str(repo_root),
        "repo_exists": True,
        "is_git_repo": True,
        "refresh_attempted": refresh,
        "refresh_succeeded": False,
        "current_branch": "main",
        "head_commit": "5555555",
        "origin_main_commit": "5555555",
        "ahead_count": 0,
        "behind_count": 0,
        "working_tree_clean": True,
        "upstream_update_available": False,
    })
    monkeypatch.setattr(module, "inspect_deepscientist_repo_manifest", lambda repo_root: {
        "manifest_exists": True,
        "manifest_valid": True,
        "is_controlled_fork": True,
        "engine_family": "MedicalDeepScientist",
        "freeze_base_commit": "a7853fd",
        "applied_commits": [{"commit": "d4994db"}],
    })
    monkeypatch.setattr(module, "build_doctor_report", lambda profile: doctor.DoctorReport(
        python_version="3.12.0",
        profile=profile,
        workspace_exists=True,
        runtime_exists=True,
        studies_exists=True,
        portfolio_exists=True,
        deepscientist_runtime_exists=True,
        medical_overlay_enabled=True,
        medical_overlay_ready=True,
        runtime_contract={"ready": True, "checks": {}},
        launcher_contract={"ready": True, "checks": {}},
        behavior_gate={"ready": True, "phase_25_ready": True, "checks": {}, "critical_overrides": []},
    ))
    monkeypatch.setattr(module, "describe_medical_overlay", lambda **_: {"all_targets_ready": True, "targets": []})

    result = module.run_upgrade_check(profile, refresh=False)

    assert result["decision"] == "up_to_date"
    assert result["repo_check"]["manifest"]["is_controlled_fork"] is True
    assert result["repo_check"]["manifest"]["engine_family"] == "MedicalDeepScientist"
```

Add to `tests/test_workspace_contracts.py`:

```python
def test_inspect_workspace_contracts_reports_controlled_fork_manifest(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.workspace_contracts")
    profile = make_profile(tmp_path)
    profile.workspace_root.mkdir(parents=True, exist_ok=True)
    profile.runtime_root.mkdir(parents=True, exist_ok=True)
    profile.deepscientist_runtime_root.mkdir(parents=True, exist_ok=True)
    (profile.workspace_root / "ops" / "medautoscience").mkdir(parents=True, exist_ok=True)
    (profile.workspace_root / "ops" / "medautoscience" / "config.env").write_text("", encoding="utf-8")
    (profile.workspace_root / "ops" / "deepscientist" / "bin").mkdir(parents=True, exist_ok=True)
    (profile.workspace_root / "ops" / "deepscientist" / "config.env").write_text("", encoding="utf-8")
    (profile.workspace_root / "ops" / "deepscientist" / "behavior_equivalence_gate.yaml").write_text(
        "schema_version: 1\nphase_25_ready: true\ncritical_overrides: []\n",
        encoding="utf-8",
    )
    profile.deepscientist_repo_root.mkdir(parents=True, exist_ok=True)
    (profile.deepscientist_repo_root / "MEDICAL_FORK_MANIFEST.json").write_text(
        '{\"schema_version\":1,\"engine_id\":\"medicaldeepscientist\",\"engine_family\":\"MedicalDeepScientist\",\"freeze_mode\":\"thin_fork\",\"upstream_source\":{\"repo_path\":\"/tmp/DeepScientist\",\"base_commit\":\"abc123\"},\"compatibility_contract\":{\"package_rename_applied\":false,\"daemon_api_shape_preserved\":true,\"quest_layout_preserved\":true,\"worktree_layout_preserved\":true},\"applied_commits\":[],\"lock_policy\":{\"mode\":\"regenerate_in_fork\",\"source_repo_was_dirty\":true,\"source_dirty_paths\":[\"uv.lock\"]}}\\n',
        encoding="utf-8",
    )

    result = module.inspect_workspace_contracts(profile)

    assert result["launcher_contract"]["checks"]["deepscientist_repo_manifest_exists"] is True
    assert result["launcher_contract"]["repo_manifest"]["engine_family"] == "MedicalDeepScientist"
```

- [ ] **Step 3: 运行测试确认 RED**

Run:

```bash
cd /Users/gaofeng/workspace/med-autoscience
PYTHONPATH=src pytest -q tests/test_deepscientist_repo_manifest.py tests/test_deepscientist_upgrade_check.py tests/test_workspace_contracts.py
```

Expected: `ModuleNotFoundError` 或断言失败

- [ ] **Step 4: 实现最小 manifest 解析模块**

Create `src/med_autoscience/deepscientist_repo_manifest.py`:

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def inspect_deepscientist_repo_manifest(repo_root: Path | None) -> dict[str, Any]:
    if repo_root is None:
        return {
            "manifest_path": None,
            "manifest_exists": False,
            "manifest_valid": False,
            "is_controlled_fork": False,
            "engine_family": None,
            "freeze_base_commit": None,
            "applied_commits": [],
            "issues": ["repo_manifest.repo_root_not_configured"],
        }

    manifest_path = Path(repo_root).expanduser().resolve() / "MEDICAL_FORK_MANIFEST.json"
    result = {
        "manifest_path": str(manifest_path),
        "manifest_exists": manifest_path.is_file(),
        "manifest_valid": False,
        "is_controlled_fork": False,
        "engine_family": None,
        "freeze_base_commit": None,
        "applied_commits": [],
        "issues": [],
    }
    if not manifest_path.is_file():
        result["issues"].append("repo_manifest.missing")
        return result

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    engine_family = payload.get("engine_family")
    upstream = payload.get("upstream_source") or {}
    applied_commits = payload.get("applied_commits") or []
    result["engine_family"] = engine_family if isinstance(engine_family, str) else None
    result["freeze_base_commit"] = upstream.get("base_commit") if isinstance(upstream, dict) else None
    result["applied_commits"] = applied_commits if isinstance(applied_commits, list) else []
    result["is_controlled_fork"] = result["engine_family"] == "MedicalDeepScientist"
    result["manifest_valid"] = bool(result["is_controlled_fork"] and result["freeze_base_commit"])
    if not result["manifest_valid"]:
        result["issues"].append("repo_manifest.invalid")
    return result
```

- [ ] **Step 5: 在 `upgrade_check` 和 `workspace_contracts` 中接入 manifest**

Implementation requirements:

- `deepscientist_upgrade_check.py` 新增：

```python
from med_autoscience.deepscientist_repo_manifest import inspect_deepscientist_repo_manifest
```

- `run_upgrade_check()` 返回的 `repo_check` 中必须包含：

```python
manifest = inspect_deepscientist_repo_manifest(profile.deepscientist_repo_root)
repo_check = inspect_deepscientist_repo(repo_root=profile.deepscientist_repo_root, refresh=refresh)
repo_check["manifest"] = manifest
```

- `workspace_contracts.py` 的 `launcher_checks` 中必须新增：

```python
"deepscientist_repo_manifest_exists": bool(repo_manifest.get("manifest_exists")),
```

- `workspace_contracts.py` 返回中必须新增：

```python
"repo_manifest": repo_manifest,
```

- `launcher_contract.ready` 不能因为缺少 manifest 而直接变 `False`；但 `checks` 和 `repo_manifest` 必须完整暴露，让人类和 controller 能明确区分“普通 checkout”和“受控 fork”。

- [ ] **Step 6: 运行测试确认 GREEN**

Run:

```bash
cd /Users/gaofeng/workspace/med-autoscience
PYTHONPATH=src pytest -q tests/test_deepscientist_repo_manifest.py tests/test_deepscientist_upgrade_check.py tests/test_workspace_contracts.py
```

Expected: `passed`

- [ ] **Step 7: 提交 manifest audit 支持**

```bash
git -C /Users/gaofeng/workspace/med-autoscience add src/med_autoscience/deepscientist_repo_manifest.py src/med_autoscience/controllers/deepscientist_upgrade_check.py src/med_autoscience/workspace_contracts.py tests/test_deepscientist_repo_manifest.py tests/test_deepscientist_upgrade_check.py tests/test_workspace_contracts.py
git -C /Users/gaofeng/workspace/med-autoscience commit -m "feat: detect controlled medicaldeepscientist fork manifests"
```

### Task 4: 更新文档并做 cross-repo 验证

**Files:**
- Modify: `guides/agent_runtime_interface.md`
- Modify: `guides/workspace_architecture.md`

- [ ] **Step 1: 更新接口文档，明确 Phase 1 已从“审计外部 repo”升级到“审计受控 fork”**

`guides/agent_runtime_interface.md` 必须补充：

- `deepscientist_repo_root` 现在可以指向 `/Users/gaofeng/workspace/MedicalDeepScientist`
- 若 repo 根目录存在 `MEDICAL_FORK_MANIFEST.json`，`deepscientist-upgrade-check` 必须把它作为受控 fork 元数据暴露出来
- 这并不代表 adapter 已可删除；只代表执行 repo 已开始受控

`guides/workspace_architecture.md` 必须补充：

- `MedicalDeepScientist` 是 Phase 1 的 execution truth freeze，不是 Phase 3 的 engine-neutral runtime
- `MEDICAL_FORK_MANIFEST.json` 是 repo 级长期 artifact
- 当前仍保留 `deepscientist_repo_root` 命名，仅因为 protocol 收口尚未完成

- [ ] **Step 2: 跑 MedAutoScience 回归测试**

Run:

```bash
cd /Users/gaofeng/workspace/med-autoscience
PYTHONPATH=src pytest -q tests/test_deepscientist_repo_manifest.py tests/test_deepscientist_upgrade_check.py tests/test_workspace_contracts.py
```

Expected: `passed`

- [ ] **Step 3: 跑 MedicalDeepScientist targeted smoke**

Run:

```bash
cd /Users/gaofeng/workspace/MedicalDeepScientist
PYTHONPATH=src pytest -q tests/test_daemon_api.py -k 'document_asset_resolves_path_documents_from_active_worktree'
python3 - <<'PY'
import json
from pathlib import Path
manifest = json.loads(Path("MEDICAL_FORK_MANIFEST.json").read_text())
assert manifest["engine_family"] == "MedicalDeepScientist"
assert manifest["applied_commits"][0]["commit"] == "d4994dba3ae1720a60daa7c80f5043f3722f32d8"
print("fork-smoke-ok")
PY
```

Expected:

- targeted daemon test `passed`
- Python 校验输出 `fork-smoke-ok`

- [ ] **Step 4: 提交文档**

```bash
git -C /Users/gaofeng/workspace/med-autoscience add guides/agent_runtime_interface.md guides/workspace_architecture.md
git -C /Users/gaofeng/workspace/med-autoscience commit -m "docs: document medicaldeepscientist phase1 freeze"
```

## Self-Review Checklist

- Spec coverage:
  - `MedicalDeepScientist` 本地冻结基线：Task 1
  - 首批 cherry-pick `d4994db`：Task 2
  - `uv.lock` 显式决策：Task 2
  - `MedAutoScience` 审计面识别 controlled fork：Task 3
  - 文档与 cross-repo 验证：Task 4
- Placeholder scan:
  - 无 `TODO` / `TBD` / `<path>` 类占位符
  - 所有仓库路径、提交哈希、文件名均已写死
- Scope check:
  - 本计划只覆盖 Phase 1 local freeze，不包含 runtime protocol convergence 与 adapter retirement
