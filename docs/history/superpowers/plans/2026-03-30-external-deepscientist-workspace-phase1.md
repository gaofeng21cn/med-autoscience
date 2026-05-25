# External DeepScientist Workspace Phase 1 Implementation Plan

Owner: `MedAutoScience`
Purpose: `superpowers_history_record`
State: `history_provenance`
Machine boundary: 人读历史过程稿。当前 contract、runtime truth、policy truth、regression oracle 和 owner boundary 继续归核心 docs、contracts、source、tests、runtime/controller surfaces 和 owner receipts。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 先把医学 workspace 的 `DeepScientist` 入口收敛成显式、可审计的 contract，并补上 Phase 2.5 行为等价门，为后续真正切到“外部程序 + 本地运行状态”结构打基础。

**Architecture:** 第一阶段不处理 `runtime/python-env`、`uv-cache`、`bundle` 等重依赖外置，也不改变当前执行代码仍主要来自现有受管 runtime 这一事实。它只先做四件事：一是把 workspace state 路径 contract 以 machine-readable 形式从 profile 导出；二是新增一个显式的 Phase 2.5 行为等价 gate 文件，让 `MedAutoScience` 能阻断任何过早的程序来源切换；三是建立 launcher/runtime contract，要求 workspace 用显式 launcher 路径和 `--home <deepscientist_runtime_root>` 驱动当前 runtime，而不是靠 PATH 猜测；四是把这些 contract 接进 `MedAutoScience` 的 doctor / upgrade-check。真正改变执行程序来源，必须在行为等价 gate 明确 ready 之后，另起下一阶段实施。

**Tech Stack:** Python 3.12, pytest, TOML, POSIX shell, DeepScientist `ds` launcher

---

## File Structure

- Create: `src/med_autoscience/workspace_contracts.py`
- Modify: `src/med_autoscience/profiles.py`
- Modify: `src/med_autoscience/doctor.py`
- Modify: `src/med_autoscience/cli.py`
- Modify: `src/med_autoscience/controllers/deepscientist_upgrade_check.py`
- Create: `tests/test_workspace_contracts.py`
- Modify: `tests/test_profiles.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_deepscientist_upgrade_check.py`
- Modify: `bootstrap/README.md`
- Modify: `guides/agent_runtime_interface.md`
- Modify: `guides/workspace_architecture.md`
- Modify: `<workspace_root>/ops/medautoscience/profiles/nfpitnet.workspace.toml`
- Create: `<workspace_root>/ops/deepscientist/behavior_equivalence_gate.yaml`
- Create: `<workspace_root>/ops/deepscientist/config.env`
- Create: `<workspace_root>/ops/deepscientist/bin/_shared.sh`
- Create: `<workspace_root>/ops/deepscientist/bin/show-config`
- Create: `<workspace_root>/ops/deepscientist/bin/doctor`
- Create: `<workspace_root>/ops/deepscientist/bin/status`
- Create: `<workspace_root>/ops/deepscientist/bin/start-web`
- Create: `<workspace_root>/ops/deepscientist/bin/stop`
- Create: `<workspace_root>/ops/deepscientist/README.md`

说明：

- 这里的 `<workspace_root>` 指 profile 中声明的 `workspace_root`，当前第一落地对象是 `NF-PitNET` workspace。
- 本轮不改 `<workspace_root>/ops/deepscientist/runtime/**` 的 quest、logs、memory、config 布局，也不移动现有 `site-packages` 遗留。
- 本轮也不把运行中的 Python 代码执行面从当前受管 runtime 切到外部 repo；任何这类动作都必须先通过 `guides/workspace_architecture.md` 里定义的 Phase 2.5 行为等价门。
- 本轮不会让 `deepscientist_repo_root` 直接改变运行命令；它先作为被审计的目标 repo 路径存在，直到行为等价 gate 明确 ready。

### Task 1: 导出 machine-readable state contract

**Files:**
- Modify: `src/med_autoscience/profiles.py`
- Modify: `src/med_autoscience/doctor.py`
- Modify: `src/med_autoscience/cli.py`
- Modify: `tests/test_profiles.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: 写失败测试，覆盖 `show-profile --format json` 与 profile 序列化**

```python
def test_workspace_profile_to_dict_emits_deepscientist_paths(tmp_path: Path) -> None:
    profile = load_profile(profile_path)
    payload = profile_to_dict(profile)
    assert payload["runtime_root"] == str(tmp_path / "workspace" / "ops" / "deepscientist" / "runtime" / "quests")
    assert payload["deepscientist_runtime_root"] == str(tmp_path / "workspace" / "ops" / "deepscientist" / "runtime")
    assert payload["deepscientist_repo_root"] == str(tmp_path / "DeepScientist")


def test_show_profile_command_supports_json_output(capsys, tmp_path: Path) -> None:
    exit_code = main(["show-profile", "--profile", str(profile_path), "--format", "json"])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["name"] == "demo"
```

- [ ] **Step 2: 运行测试确认 RED**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_profiles.py tests/test_cli.py -k 'profile_to_dict or show_profile_command_supports_json_output'`

Expected: 参数解析失败、`NameError` 或断言失败。

- [ ] **Step 3: 写最小实现**

实现要求：

- 在 `profiles.py` 中提供稳定的 `profile_to_dict()`。
- `show-profile` 新增 `--format text|json`，默认仍为 `text`，避免回归现有人类可读输出。
- JSON 输出中的路径全部转成绝对字符串，供 shell wrapper 直接消费，不允许再在 shell 层猜目录。
- JSON 输出必须同时包含 `runtime_root` 和 `deepscientist_runtime_root`，为后续一致性校验准备真相面。

- [ ] **Step 4: 运行测试确认 GREEN**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_profiles.py tests/test_cli.py -k 'profile_to_dict or show_profile_command_supports_json_output'`

Expected: `passed`

### Task 2: 建立 Phase 2.5 行为等价 gate 与 workspace contract 校验层

**Files:**
- Create: `src/med_autoscience/workspace_contracts.py`
- Modify: `src/med_autoscience/doctor.py`
- Modify: `src/med_autoscience/controllers/deepscientist_upgrade_check.py`
- Create: `tests/test_workspace_contracts.py`
- Modify: `tests/test_deepscientist_upgrade_check.py`
- Modify: `tests/test_cli.py`
- Create: `<workspace_root>/ops/deepscientist/behavior_equivalence_gate.yaml`

- [ ] **Step 1: 写失败测试，覆盖行为等价 gate、runtime 路径一致性与 workspace-local 入口契约**

```python
def test_workspace_contract_reports_runtime_root_mismatch(tmp_path: Path) -> None:
    profile = make_profile(tmp_path)
    profile = replace(profile, runtime_root=tmp_path / "workspace" / "custom-quests")
    result = inspect_workspace_contract(profile)
    assert result["runtime_contract"]["runtime_root_matches_home_quests"] is False


def test_workspace_contract_reports_behavior_gate_not_ready(tmp_path: Path) -> None:
    profile = make_profile(tmp_path)
    write_behavior_gate(tmp_path / "workspace" / "ops" / "deepscientist" / "behavior_equivalence_gate.yaml", phase_25_ready=False)
    result = inspect_workspace_contract(profile)
    assert result["behavior_gate"]["phase_25_ready"] is False


def test_upgrade_check_blocks_when_behavior_gate_not_ready(tmp_path: Path) -> None:
    profile = make_profile(tmp_path)
    write_behavior_gate(tmp_path / "workspace" / "ops" / "deepscientist" / "behavior_equivalence_gate.yaml", phase_25_ready=False)
    result = run_upgrade_check(profile, refresh=False)
    assert result["decision"] == "blocked_behavior_equivalence_gate"
```

- [ ] **Step 2: 运行测试确认 RED**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_workspace_contracts.py tests/test_deepscientist_upgrade_check.py`

Expected: `ModuleNotFoundError`、`ImportError` 或断言失败。

- [ ] **Step 3: 写最小实现**

实现要求：

- `workspace_contracts.py` 至少显式检查：
  - `runtime_root == deepscientist_runtime_root / "quests"`
  - `runtime_root`、`deepscientist_runtime_root` 是否存在
  - `ops/medautoscience/config.env`
  - `ops/deepscientist/behavior_equivalence_gate.yaml`
  - `ops/deepscientist/config.env`
  - `ops/deepscientist/bin/`
  - profile 中 `deepscientist_repo_root`
- `behavior_equivalence_gate.yaml` 采用结构化 schema，至少显式声明：
  - `schema_version`
  - `phase_25_ready`
  - `critical_overrides[]`
  - 每个 override 的 `id / source_path / status / target_surface`
- `doctor` 输出里增加可审计的 `runtime_contract / launcher_contract / behavior_gate` 状态，不允许只报一个笼统 `true/false`。
- `deepscientist_upgrade_check` 必须先看 `behavior_gate.phase_25_ready`，未就绪时直接返回 `blocked_behavior_equivalence_gate`，而不是先谈 repo 是否可升级。

- [ ] **Step 4: 运行测试确认 GREEN**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_workspace_contracts.py tests/test_deepscientist_upgrade_check.py`

Expected: `passed`

### Task 3: 为 NF-PitNET workspace 建立 launcher/runtime 薄入口

**Files:**
- Modify: `<workspace_root>/ops/medautoscience/profiles/nfpitnet.workspace.toml`
- Create: `<workspace_root>/ops/deepscientist/behavior_equivalence_gate.yaml`
- Create: `<workspace_root>/ops/deepscientist/config.env`
- Create: `<workspace_root>/ops/deepscientist/bin/_shared.sh`
- Create: `<workspace_root>/ops/deepscientist/bin/show-config`
- Create: `<workspace_root>/ops/deepscientist/bin/doctor`
- Create: `<workspace_root>/ops/deepscientist/bin/status`
- Create: `<workspace_root>/ops/deepscientist/bin/start-web`
- Create: `<workspace_root>/ops/deepscientist/bin/stop`
- Create: `<workspace_root>/ops/deepscientist/README.md`

- [ ] **Step 1: 补齐 workspace profile 的 `deepscientist_repo_root`**

要求：

- 不复制 `DeepScientist` 程序到 workspace 内。
- 直接把外部共享 repo 路径写入当前 `nfpitnet.workspace.toml`。

- [ ] **Step 2: 写 `behavior_equivalence_gate.yaml`，把当前 local override 风险显式落盘**

实现要求：

- 必须把当前 `site-packages/deepscientist/prompts/builder.py` 这类升级敏感 override 作为 `critical_overrides[]` 明确登记。
- 在这些 override 没被迁出或验证可删除前，`phase_25_ready` 必须保持 `false`。
- 不允许靠自然语言 README 代替结构化 gate 文件。

- [ ] **Step 3: 写 `_shared.sh`，统一解析 profile 与 launcher**

实现要求：

- 读取 `ops/deepscientist/config.env`。
- 通过 `ops/medautoscience/bin/show-profile --format json` 解析：
  - `runtime_root`
  - `deepscientist_runtime_root`
  - `deepscientist_repo_root`
- 显式校验 `runtime_root == deepscientist_runtime_root/quests`，不一致就 fail-fast。
- `config.env` 必须显式提供 `DEEPSCIENTIST_LAUNCHER` 的绝对路径，不允许默认落回 PATH 里的 `ds`。
- 本阶段 operational wrapper 不导出 `DEEPSCIENTIST_REPO_ROOT` 给运行命令；repo root 只进入 `show-config / doctor / upgrade-check` 的审计面。
- 所有脚本都只走 `_shared.sh`，不允许重复拼路径。

- [ ] **Step 4: 写面向运维的薄脚本**

脚本职责：

- `show-config`
  - 打印解析后的 `workspace_root / runtime_root / deepscientist_runtime_root / deepscientist_repo_root / launcher / phase_25_ready`
- `doctor`
  - 运行 `"<DEEPSCIENTIST_LAUNCHER>" --home "<deepscientist_runtime_root>" doctor`
- `status`
  - 运行 `"<DEEPSCIENTIST_LAUNCHER>" --home "<deepscientist_runtime_root>" --status`
- `start-web`
  - 运行 `"<DEEPSCIENTIST_LAUNCHER>" --home "<deepscientist_runtime_root>" --port 20999`
- `stop`
  - 运行 `"<DEEPSCIENTIST_LAUNCHER>" --home "<deepscientist_runtime_root>" --stop`

- [ ] **Step 5: 为 workspace 写说明文档**

`<workspace_root>/ops/deepscientist/README.md` 至少要说明：

- 当前 workspace 仍暂时包含 `runtime/python-env`、`uv-cache`、`bundle`、`tools`
- 第一阶段只统一入口与 gate，不代表已经完成外部程序 / 本地状态彻底分离
- 程序升级与 repo 检查统一交给 `MedAutoScience` profile + `deepscientist-upgrade-check`

- [ ] **Step 6: 做 workspace smoke test**

Run:

```bash
cd /Users/gaofeng/workspace/Yang/无功能垂体瘤
ops/medautoscience/bin/show-profile --format json
ops/deepscientist/bin/show-config
ops/deepscientist/bin/status
```

Expected:

- `show-profile` 输出 JSON，且包含 `deepscientist_repo_root`
- `show-config` 输出解析后的 launcher、repo root、本地 runtime root 和 `phase_25_ready`
- `status` 能以当前 `ops/deepscientist/runtime` 作为 home 返回 JSON 状态，而不是再隐式用 `~/DeepScientist`
- wrapper 在 `runtime_root` 不一致或 `DEEPSCIENTIST_LAUNCHER` 未显式配置时直接失败

### Task 4: 同步文档并做回归验证

**Files:**
- Modify: `bootstrap/README.md`
- Modify: `guides/agent_runtime_interface.md`
- Modify: `guides/workspace_architecture.md`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_profiles.py`
- Modify: `tests/test_deepscientist_upgrade_check.py`
- Modify: `tests/test_workspace_contracts.py`

- [ ] **Step 1: 更新文档，明确第一阶段已经实现到什么边界**

必须写清楚：

- 第一阶段只完成“state contract + behavior gate + launcher/runtime 入口统一”
- 第一阶段没有跨过 Phase 2.5 行为等价门，也没有把执行代码面真正迁出当前受管 runtime
- `runtime/python-env`、`uv-cache`、`bundle`、`tools` 仍在下一阶段处理
- 新 workspace 若要复用本轮结果，至少需要准备 `ops/deepscientist/behavior_equivalence_gate.yaml`、`ops/deepscientist/config.env` 与 `ops/deepscientist/bin/*`

- [ ] **Step 2: 跑定向测试**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_profiles.py tests/test_workspace_contracts.py tests/test_cli.py tests/test_deepscientist_upgrade_check.py`

Expected: 全绿

- [ ] **Step 3: 跑 workspace 真实 dry-run**

Run:

```bash
cd /Users/gaofeng/workspace/med-autoscience
PYTHONPATH=src python3 -m med_autoscience.cli doctor --profile /Users/gaofeng/workspace/Yang/无功能垂体瘤/ops/medautoscience/profiles/nfpitnet.workspace.toml
PYTHONPATH=src python3 -m med_autoscience.cli deepscientist-upgrade-check --profile /Users/gaofeng/workspace/Yang/无功能垂体瘤/ops/medautoscience/profiles/nfpitnet.workspace.toml
```

Expected:

- `doctor` 能显式报告 `runtime_contract / launcher_contract / behavior_gate`
- `upgrade-check` 在 `phase_25_ready=false` 时优先阻断，而不是继续假装可以进入外部程序切换

- [ ] **Step 4: 记录下一阶段入口**

下一阶段默认承接：

1. 在 `phase_25_ready=true` 后，再推进 launcher / repo source 的真正绑定
2. 再推进 `runtime/python-env / uv-cache / bundle / tools` 外置
3. 最后把新疾病 workspace skeleton 模板化成可复用模板
