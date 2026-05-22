# Med-DeepScientist Authority Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 Med Auto Science 活动控制面彻底切到 `med-deepscientist`，移除 `deepscientist_*` 活动命名、旧 skill seed 与旧 workspace bootstrap 依赖。

**Architecture:** `med-autoscience` 作为唯一 installer / bootstrap / overlay authority，直接把 `med-deepscientist` runtime 与 workspace-local skill 物化到目标 workspace。profile、workspace contract、wrapper、overlay target 与模板测试统一改名，不保留双写兼容。

**Tech Stack:** Python 3, pytest, TOML, YAML, shell wrapper, workspace-local Codex skills

---

### Task 1: 锁定 authoritative 命名与 profile contract

**Files:**
- Modify: `/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/profiles.py`
- Modify: `/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/doctor.py`
- Modify: `/Users/gaofeng/workspace/med-autoscience/tests/test_profiles.py`
- Modify: `/Users/gaofeng/workspace/med-autoscience/tests/test_cli.py`
- Modify: `/Users/gaofeng/workspace/med-autoscience/tests/test_mcp_server.py`
- Modify: `/Users/gaofeng/workspace/med-autoscience/tests/test_submission_targets.py`
- Modify: `/Users/gaofeng/workspace/med-autoscience/tests/test_submission_targets_controller.py`

- [ ] **Step 1: 先把 profile contract 的失败测试改成新字段**

```toml
med_deepscientist_runtime_root = "/ABS/PATH/TO/workspace/ops/med-deepscientist/runtime"
med_deepscientist_repo_root = "/ABS/PATH/TO/med-deepscientist"
```

- [ ] **Step 2: 运行最小测试，确认旧字段断言失败**

Run: `pytest /Users/gaofeng/workspace/med-autoscience/tests/test_profiles.py -q`
Expected: FAIL，错误集中在 `deepscientist_runtime_root` / `deepscientist_repo_root` 断言或缺失字段

- [ ] **Step 3: 实现 profile dataclass / loader / renderer 新字段**

```python
class WorkspaceProfile:
    med_deepscientist_runtime_root: Path
    med_deepscientist_repo_root: Path | None
```

- [ ] **Step 4: 跑回 profile 与入口测试**

Run: `pytest /Users/gaofeng/workspace/med-autoscience/tests/test_profiles.py /Users/gaofeng/workspace/med-autoscience/tests/test_cli.py /Users/gaofeng/workspace/med-autoscience/tests/test_mcp_server.py /Users/gaofeng/workspace/med-autoscience/tests/test_submission_targets.py /Users/gaofeng/workspace/med-autoscience/tests/test_submission_targets_controller.py -q`
Expected: PASS

### Task 2: 切换 runtime contract、quest 布局与 workspace init 物化路径

**Files:**
- Modify: `/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/workspace_contracts.py`
- Modify: `/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/runtime_protocol/topology.py`
- Modify: `/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/controllers/workspace_init.py`
- Modify: `/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/controllers/study_runtime_router.py`
- Modify: `/Users/gaofeng/workspace/med-autoscience/tests/test_workspace_contracts.py`
- Modify: `/Users/gaofeng/workspace/med-autoscience/tests/test_workspace_init.py`
- Modify: `/Users/gaofeng/workspace/med-autoscience/tests/test_study_runtime_router.py`
- Modify: `/Users/gaofeng/workspace/med-autoscience/tests/test_medical_startup_contract_support.py`
- Modify: `/Users/gaofeng/workspace/med-autoscience/tests/test_domain_health_diagnostic.py`

- [ ] **Step 1: 先把 contract / init / router 测试改成 `ops/med-deepscientist`**

```yaml
runtime_root: /tmp/workspace/ops/med-deepscientist/runtime/quests
med_deepscientist_runtime_root: /tmp/workspace/ops/med-deepscientist/runtime
```

- [ ] **Step 2: 运行 contract / init / router 测试确认失败**

Run: `pytest /Users/gaofeng/workspace/med-autoscience/tests/test_workspace_contracts.py /Users/gaofeng/workspace/med-autoscience/tests/test_workspace_init.py /Users/gaofeng/workspace/med-autoscience/tests/test_study_runtime_router.py /Users/gaofeng/workspace/med-autoscience/tests/test_medical_startup_contract_support.py /Users/gaofeng/workspace/med-autoscience/tests/test_domain_health_diagnostic.py -q`
Expected: FAIL，错误集中在旧路径 `ops/deepscientist` 与旧字段名

- [ ] **Step 3: 实现新 contract 与 bootstrap**

```python
runtime_root_expected = profile.med_deepscientist_runtime_root / "quests"
med_deepscientist_ops_root = profile.workspace_root / "ops" / "med-deepscientist"
```

- [ ] **Step 4: 跑回 contract / init / router 测试**

Run: `pytest /Users/gaofeng/workspace/med-autoscience/tests/test_workspace_contracts.py /Users/gaofeng/workspace/med-autoscience/tests/test_workspace_init.py /Users/gaofeng/workspace/med-autoscience/tests/test_study_runtime_router.py /Users/gaofeng/workspace/med-autoscience/tests/test_medical_startup_contract_support.py /Users/gaofeng/workspace/med-autoscience/tests/test_domain_health_diagnostic.py -q`
Expected: PASS

### Task 3: 切换 overlay installer 到 med-deepscientist skill surface

**Files:**
- Modify: `/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/overlay/installer.py`
- Modify: `/Users/gaofeng/workspace/med-autoscience/tests/test_overlay_installer.py`
- Modify: `/Users/gaofeng/workspace/med-autoscience/profiles/workspace.profile.template.toml`
- Modify: `/Users/gaofeng/workspace/med-autoscience/bootstrap/README.md`

- [ ] **Step 1: 先把 overlay 测试目标目录改成 `med-deepscientist-*`**

```python
target_root = skills_root / f"med-deepscientist-{skill_id}"
```

- [ ] **Step 2: 运行 overlay 测试确认旧 installer 失败**

Run: `pytest /Users/gaofeng/workspace/med-autoscience/tests/test_overlay_installer.py -q`
Expected: FAIL，错误集中在旧 target root `deepscientist-*`

- [ ] **Step 3: 修改 installer authoritative target root**

```python
target_root=skills_root / f"med-deepscientist-{skill_id}"
```

- [ ] **Step 4: 跑回 overlay 测试**

Run: `pytest /Users/gaofeng/workspace/med-autoscience/tests/test_overlay_installer.py -q`
Expected: PASS

### Task 4: 同步两个 workspace 的活动 profile、wrapper 与活动说明

**Files:**
- Modify: `/Users/gaofeng/workspace/Yang/无功能垂体瘤/ops/medautoscience/profiles/nfpitnet.workspace.toml`
- Modify: `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/ops/medautoscience/profiles/dm-cvd-mortality-risk.workspace.toml`
- Modify: `/Users/gaofeng/workspace/Yang/无功能垂体瘤/ops/med-deepscientist/bin/_shared.sh`
- Modify: `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/ops/med-deepscientist/bin/_shared.sh`
- Modify: `/Users/gaofeng/workspace/Yang/无功能垂体瘤/ops/medautoscience/README.md`
- Modify: `/Users/gaofeng/workspace/Yang/无功能垂体瘤/ops/medautoscience/compatibility_inventory.md`
- Modify: `/Users/gaofeng/workspace/Yang/无功能垂体瘤/ops/med-deepscientist/README.md`
- Modify: `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/ops/med-deepscientist/README.md`
- Modify: `/Users/gaofeng/workspace/Yang/无功能垂体瘤/ops/med-deepscientist/local_overrides_manifest.md`

- [ ] **Step 1: 用新字段名同步两个 profile**

```toml
med_deepscientist_runtime_root = "/Users/gaofeng/workspace/.../ops/med-deepscientist/runtime"
med_deepscientist_repo_root = "/Users/gaofeng/workspace/med-deepscientist"
```

- [ ] **Step 2: 调整 wrapper 读取与导出键值**

```bash
med_deepscientist_runtime_root) MED_DEEPSCIENTIST_HOME="${value}" ;;
med_deepscientist_repo_root) MED_DEEPSCIENTIST_REPO_ROOT_AUDIT="${value}" ;;
```

- [ ] **Step 3: 更新活动 README / manifest，只承认 `med-deepscientist`**

```md
唯一 authoritative runtime: `ops/med-deepscientist/`
唯一 authoritative repo: `/Users/gaofeng/workspace/med-deepscientist`
workspace-local skill target: `.codex/skills/med-deepscientist-*`
```

- [ ] **Step 4: 用 `rg` 复核两个 workspace 活动层**

Run: `rg -n "deepscientist_runtime_root|deepscientist_repo_root|\\.codex/skills/deepscientist-|ops/deepscientist" /Users/gaofeng/workspace/Yang/无功能垂体瘤/ops/medautoscience /Users/gaofeng/workspace/Yang/无功能垂体瘤/ops/med-deepscientist /Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/ops/medautoscience /Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/ops/med-deepscientist`
Expected: 只剩历史文档或运行时历史产物；活动 profile / wrapper / README 不再命中

### Task 5: 重新物化 workspace-local skills 并删除旧 seeds

**Files:**
- Modify: `/Users/gaofeng/workspace/Yang/无功能垂体瘤/.codex/skills/*`
- Modify: `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/.codex/skills/*`
- Delete: `/Users/gaofeng/.codex/skills/deepscientist-*`

- [ ] **Step 1: 用更新后的 installer 对两个 workspace 重新执行 workspace-local reapply**

Run: `PYTHONPATH=/Users/gaofeng/workspace/med-autoscience/src python3 -m med_autoscience.cli reapply-medical-overlay --profile /Users/gaofeng/workspace/Yang/无功能垂体瘤/ops/medautoscience/profiles/nfpitnet.workspace.toml`
Expected: `.codex/skills/med-deepscientist-*` 被创建或重写

- [ ] **Step 2: 对糖尿病 workspace 执行同样命令**

Run: `PYTHONPATH=/Users/gaofeng/workspace/med-autoscience/src python3 -m med_autoscience.cli reapply-medical-overlay --profile /Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/ops/medautoscience/profiles/dm-cvd-mortality-risk.workspace.toml`
Expected: `.codex/skills/med-deepscientist-*` 被创建或重写

- [ ] **Step 3: 删除旧 workspace-local 与 user-level `deepscientist-*` seed**

Run: `rm -rf /Users/gaofeng/workspace/Yang/无功能垂体瘤/.codex/skills/deepscientist-* /Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/.codex/skills/deepscientist-* /Users/gaofeng/.codex/skills/deepscientist-*`
Expected: 旧 `deepscientist-*` 目录不存在

- [ ] **Step 4: 审计新物化结果**

Run: `find /Users/gaofeng/workspace/Yang/无功能垂体瘤/.codex/skills /Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/.codex/skills -maxdepth 1 -type d | sort`
Expected: 只保留 `med-deepscientist-*` 的医学 overlay 目录

### Task 6: 全量验证与残留扫描

**Files:**
- Verify only

- [ ] **Step 1: 运行本次改动覆盖到的 pytest 子集**

Run: `pytest /Users/gaofeng/workspace/med-autoscience/tests/test_profiles.py /Users/gaofeng/workspace/med-autoscience/tests/test_overlay_installer.py /Users/gaofeng/workspace/med-autoscience/tests/test_workspace_contracts.py /Users/gaofeng/workspace/med-autoscience/tests/test_workspace_init.py /Users/gaofeng/workspace/med-autoscience/tests/test_study_runtime_router.py /Users/gaofeng/workspace/med-autoscience/tests/test_cli.py /Users/gaofeng/workspace/med-autoscience/tests/test_mcp_server.py /Users/gaofeng/workspace/med-autoscience/tests/test_submission_targets.py /Users/gaofeng/workspace/med-autoscience/tests/test_submission_targets_controller.py /Users/gaofeng/workspace/med-autoscience/tests/test_medical_startup_contract_support.py /Users/gaofeng/workspace/med-autoscience/tests/test_domain_health_diagnostic.py -q`
Expected: PASS

- [ ] **Step 2: 扫描活动控制面残留**

Run: `rg -n "deepscientist_runtime_root|deepscientist_repo_root|\\.codex/skills/deepscientist-|ops/deepscientist" /Users/gaofeng/workspace/med-autoscience/src /Users/gaofeng/workspace/med-autoscience/tests /Users/gaofeng/workspace/med-autoscience/profiles /Users/gaofeng/workspace/Yang/无功能垂体瘤/ops /Users/gaofeng/workspace/Yang/无功能垂体瘤/.codex /Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/ops /Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/.codex`
Expected: 不再命中活动控制面；历史文档与运行日志可单独记录为后续非阻塞清理

- [ ] **Step 3: 验证 doctor / wrapper 可读**

Run: `PYTHONPATH=/Users/gaofeng/workspace/med-autoscience/src python3 -m med_autoscience.cli show-profile --profile /Users/gaofeng/workspace/Yang/无功能垂体瘤/ops/medautoscience/profiles/nfpitnet.workspace.toml`
Expected: 输出 `med_deepscientist_runtime_root` 与 `med_deepscientist_repo_root`
