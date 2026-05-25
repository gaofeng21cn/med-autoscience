# Third-Party Agent Entry Implementation Plan

Owner: `MedAutoScience`
Purpose: `superpowers_history_record`
State: `history_provenance`
Machine boundary: 人读历史过程稿。当前 contract、runtime truth、policy truth、regression oracle 和 owner boundary 继续归核心 docs、contracts、source、tests、runtime/controller surfaces 和 owner receipts。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把第三方 Agent 接入设计落成一套可执行、可校验、可同步的实现，包括单一事实源、公开 guide、`Codex` 薄入口 Skill、`OpenClaw` 入口 prompt，以及 README / 技术入口文档中的统一兼容表述。

**Architecture:** 继续保持 `policy -> controller -> overlay -> adapter` 分层，不把入口层做成新的主接口。实现上新增一个很薄的 `agent_entry` 模块，负责加载 canonical entry-mode 定义、渲染公开资产、同步导出文件；正式机器接口仍然保持在 `profile / bootstrap / controller / overlay`。`Codex / Claude Code / OpenClaw` 对外统一表述为兼容，但只实现 `Codex` 与 `OpenClaw` 的薄包装，`Claude Code` 仅复用同一事实源。

**Tech Stack:** Python 3.12, pytest, PyYAML, pathlib, argparse, dataclasses, importlib.resources

---

## File Structure

- Create: `src/med_autoscience/agent_entry/__init__.py`
- Create: `src/med_autoscience/agent_entry/modes.py`
- Create: `src/med_autoscience/agent_entry/renderers.py`
- Create: `src/med_autoscience/agent_entry/resources/__init__.py`
- Create: `src/med_autoscience/agent_entry/resources/agent_entry_modes.yaml`
- Modify: `src/med_autoscience/cli.py`
- Modify: `pyproject.toml`
- Create: `tests/test_agent_entry_modes.py`
- Create: `tests/test_agent_entry_assets.py`
- Modify: `tests/test_cli.py`
- Create: `guides/agent_entry_modes.md`
- Create: `templates/agent_entry_modes.yaml`
- Create: `templates/codex/medautoscience-entry.SKILL.md`
- Create: `templates/openclaw/medautoscience-entry.prompt.md`
- Modify: `guides/agent_runtime_interface.md`
- Modify: `README.md`

### Responsibility Split

- `src/med_autoscience/agent_entry/modes.py`
  - 从 package resource 加载 canonical entry-mode 定义
  - 校验五类入口、两种运行模式、升级条件、兼容对象、正式主链是否自洽

- `src/med_autoscience/agent_entry/renderers.py`
  - 从 canonical 定义渲染：
    - 公共 guide markdown
    - 公共 YAML 镜像 `templates/agent_entry_modes.yaml`
    - `Codex` 薄入口 Skill
    - `OpenClaw` 入口 prompt
  - 提供同步导出函数，避免手工复制文本

- `src/med_autoscience/cli.py`
  - 增加只读展示和同步导出命令
  - 不新增新的研究执行接口

- `tests/test_agent_entry_modes.py`
  - 校验 canonical 定义与字段约束

- `tests/test_agent_entry_assets.py`
  - 校验导出资产与仓库内 checked-in 文件保持一致

- `guides/agent_entry_modes.md`
  - 面向第三方 Agent 的稳定入口说明

- `templates/codex/medautoscience-entry.SKILL.md`
  - `Codex` 用的薄入口 Skill 模板

- `templates/openclaw/medautoscience-entry.prompt.md`
  - `OpenClaw` 用的入口 prompt 模板

## Task 1: 建立 canonical entry-mode 事实源与加载器

**Files:**
- Create: `tests/test_agent_entry_modes.py`
- Create: `src/med_autoscience/agent_entry/__init__.py`
- Create: `src/med_autoscience/agent_entry/modes.py`
- Create: `src/med_autoscience/agent_entry/resources/__init__.py`
- Create: `src/med_autoscience/agent_entry/resources/agent_entry_modes.yaml`
- Modify: `pyproject.toml`

- [ ] **Step 1: 写失败测试，锁定五类入口与正式主链约束**

```python
from med_autoscience.agent_entry.modes import load_entry_modes


def test_load_entry_modes_returns_canonical_five_modes() -> None:
    modes = load_entry_modes()
    assert [mode.mode_id for mode in modes] == [
        "full_research",
        "literature_scout",
        "idea_exploration",
        "project_optimization",
        "writing_delivery",
    ]
    assert "Claude Code" in modes[0].compatible_agents


def test_full_research_managed_chain_keeps_experiment() -> None:
    mode = next(item for item in load_entry_modes() if item.mode_id == "full_research")
    assert mode.default_runtime_mode == "managed"
    assert mode.preconditions == ("workspace/profile available",)
    assert mode.managed_routes == ("doctor", "bootstrap", "overlay-status", "scout", "idea", "experiment", "write", "finalize")
    assert mode.governance_routes == ("decision",)


def test_writing_delivery_keeps_auxiliary_journal_resolution_route() -> None:
    mode = next(item for item in load_entry_modes() if item.mode_id == "writing_delivery")
    assert mode.lightweight_routes == ("write",)
    assert mode.auxiliary_routes == ("journal-resolution",)
    assert "submission bundle or final delivery requested" in mode.upgrade_triggers


def test_templates_agent_entry_modes_yaml_is_valid_machine_contract() -> None:
    payload = load_entry_modes_payload()
    assert payload["compatible_agents"] == ["Codex", "Claude Code", "OpenClaw"]
    assert len(payload["modes"]) == 5
    for mode in payload["modes"]:
        assert mode["managed_entry_actions"] == ["doctor", "bootstrap", "overlay-status"]
```

- [ ] **Step 2: 运行测试确认 RED**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_agent_entry_modes.py`

Expected: `ModuleNotFoundError` 或断言失败，因为 `med_autoscience.agent_entry` 及 canonical YAML 尚不存在。

- [ ] **Step 3: 写最小实现**

```python
@dataclass(frozen=True)
class EntryMode:
    mode_id: str
    display_name: str
    default_runtime_mode: str
    compatible_agents: tuple[str, ...]
    preconditions: tuple[str, ...]
    lightweight_scope: tuple[str, ...]
    managed_entry_actions: tuple[str, ...]
    lightweight_routes: tuple[str, ...]
    managed_routes: tuple[str, ...]
    governance_routes: tuple[str, ...]
    auxiliary_routes: tuple[str, ...]
    upgrade_triggers: tuple[str, ...]


def load_entry_modes() -> tuple[EntryMode, ...]:
    payload = load_entry_modes_payload()
    return _validate_and_build(payload)


def load_entry_modes_payload(path: Path | None = None) -> dict[str, object]:
    resolved = path or resources.files("med_autoscience.agent_entry.resources").joinpath("agent_entry_modes.yaml")
    payload = yaml.safe_load(resolved.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}
```

`agent_entry_modes.yaml` 至少要显式保存：

```yaml
compatible_agents:
  - Codex
  - Claude Code
  - OpenClaw
modes:
  - mode_id: full_research
    display_name: 全自动科研推进
    default_runtime_mode: managed
    preconditions: ["workspace/profile available"]
    managed_entry_actions: [doctor, bootstrap, overlay-status]
    lightweight_routes: []
    managed_routes: [doctor, bootstrap, overlay-status, scout, idea, experiment, write, finalize]
    governance_routes: [decision]
    auxiliary_routes: []
  - mode_id: writing_delivery
    display_name: 稿件生成 / 投稿包导出
    default_runtime_mode: lightweight
    preconditions: ["accepted evidence or manuscript materials available"]
    managed_entry_actions: [doctor, bootstrap, overlay-status]
    lightweight_routes: [write]
    managed_routes: [doctor, bootstrap, overlay-status, write, finalize]
    governance_routes: []
    auxiliary_routes: [journal-resolution]
```

同时在 `pyproject.toml` 增加 package data：

```toml
[tool.setuptools.package-data]
"med_autoscience.agent_entry.resources" = ["*.yaml"]
```

- [ ] **Step 4: 运行测试确认 GREEN**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_agent_entry_modes.py`

Expected: `4 passed`，且测试中能确认：

- `full_research` 的正式路由保留 `experiment`
- `writing_delivery` 保留 `journal-resolution` 作为附加路由
- preconditions / managed_entry_actions / lightweight_routes / managed_routes / auxiliary_routes 都来自 canonical YAML
- canonical YAML 本身是可解析、字段完整的机器契约

- [ ] **Step 5: Commit**

```bash
cd /Users/gaofeng/workspace/med-autoscience
git add pyproject.toml src/med_autoscience/agent_entry tests/test_agent_entry_modes.py
git commit -m "feat: add canonical agent entry mode definitions"
```

## Task 2: 增加渲染与同步层，不让 YAML 退化成摆设

**Files:**
- Create: `tests/test_agent_entry_assets.py`
- Modify: `tests/test_cli.py`
- Create: `src/med_autoscience/agent_entry/renderers.py`
- Modify: `src/med_autoscience/cli.py`

- [ ] **Step 1: 写失败测试，锁定 CLI 与导出资产行为**

```python
def test_show_agent_entry_modes_command_prints_canonical_json(capsys) -> None:
    exit_code = main(["show-agent-entry-modes"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert '"mode_id": "full_research"' in captured.out
    assert '"managed_routes": [' in captured.out
    assert '"managed_entry_actions": [' in captured.out


def test_sync_agent_entry_assets_writes_expected_files(tmp_path: Path) -> None:
    result = sync_agent_entry_assets(repo_root=tmp_path)
    assert (tmp_path / "guides" / "agent_entry_modes.md").exists()
    assert (tmp_path / "templates" / "agent_entry_modes.yaml").exists()
    assert (tmp_path / "templates" / "codex" / "medautoscience-entry.SKILL.md").exists()
    assert (tmp_path / "templates" / "openclaw" / "medautoscience-entry.prompt.md").exists()
    assert result["written_count"] == 4


def test_render_public_yaml_round_trips_to_same_mode_contract() -> None:
    rendered = yaml.safe_load(render_public_yaml())
    source = load_entry_modes_payload()
    assert rendered == source
```

- [ ] **Step 2: 运行测试确认 RED**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_agent_entry_assets.py tests/test_cli.py`

Expected: parser 不认识 `show-agent-entry-modes` / `sync-agent-entry-assets`，或 render / round-trip / `managed_entry_actions` 输出不存在。

- [ ] **Step 3: 写最小实现**

```python
def render_entry_modes_guide() -> str:
    modes = load_entry_modes()
    return _render_markdown_guide(modes)


def sync_agent_entry_assets(*, repo_root: Path) -> dict[str, object]:
    outputs = {
        "guide": repo_root / "guides" / "agent_entry_modes.md",
        "yaml": repo_root / "templates" / "agent_entry_modes.yaml",
        "codex_skill": repo_root / "templates" / "codex" / "medautoscience-entry.SKILL.md",
        "openclaw_prompt": repo_root / "templates" / "openclaw" / "medautoscience-entry.prompt.md",
    }
    for path in outputs.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    outputs["guide"].write_text(render_entry_modes_guide(), encoding="utf-8")
    outputs["yaml"].write_text(render_public_yaml(), encoding="utf-8")
    outputs["codex_skill"].write_text(render_codex_entry_skill(), encoding="utf-8")
    outputs["openclaw_prompt"].write_text(render_openclaw_entry_prompt(), encoding="utf-8")
    return {"written_count": 4, "paths": {key: str(path) for key, path in outputs.items()}}
```

在 `src/med_autoscience/cli.py` 新增：

```python
show_agent_entry_modes_parser = subparsers.add_parser("show-agent-entry-modes")
sync_agent_entry_assets_parser = subparsers.add_parser("sync-agent-entry-assets")
sync_agent_entry_assets_parser.add_argument("--repo-root", default=".")
```

并在 `main()` 中分发到：

```python
if args.command == "show-agent-entry-modes":
    print(json.dumps(render_entry_modes_payload(), ensure_ascii=False, indent=2))
    return 0

if args.command == "sync-agent-entry-assets":
    result = sync_agent_entry_assets(repo_root=Path(args.repo_root).resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0
```

- [ ] **Step 4: 运行测试确认 GREEN**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_agent_entry_assets.py tests/test_cli.py`

Expected: 新增命令通过，`sync-agent-entry-assets` 能在临时目录中生成 4 份衍生资产，且 `render_public_yaml()` 与 canonical YAML round-trip 一致。

- [ ] **Step 5: Commit**

```bash
cd /Users/gaofeng/workspace/med-autoscience
git add src/med_autoscience/cli.py src/med_autoscience/agent_entry/renderers.py tests/test_agent_entry_assets.py tests/test_cli.py
git commit -m "feat: add agent entry asset renderers and sync commands"
```

## Task 3: 落盘公开 guide、Codex/OpenClaw 薄入口资产，并接回仓库文档

**Files:**
- Create: `guides/agent_entry_modes.md`
- Create: `templates/agent_entry_modes.yaml`
- Create: `templates/codex/medautoscience-entry.SKILL.md`
- Create: `templates/openclaw/medautoscience-entry.prompt.md`
- Modify: `guides/agent_runtime_interface.md`
- Modify: `README.md`
- Modify: `tests/test_agent_entry_assets.py`

- [ ] **Step 1: 写失败测试，锁定仓库内 checked-in 资产必须与 renderer 输出一致**

```python
REPO_ROOT = Path(__file__).resolve().parents[1]


def test_repo_agent_entry_assets_match_rendered_outputs() -> None:
    assert (REPO_ROOT / "guides" / "agent_entry_modes.md").read_text(encoding="utf-8") == render_entry_modes_guide()
    assert (REPO_ROOT / "templates" / "agent_entry_modes.yaml").read_text(encoding="utf-8") == render_public_yaml()
    assert (REPO_ROOT / "templates" / "codex" / "medautoscience-entry.SKILL.md").read_text(encoding="utf-8") == render_codex_entry_skill()
    assert (REPO_ROOT / "templates" / "openclaw" / "medautoscience-entry.prompt.md").read_text(encoding="utf-8") == render_openclaw_entry_prompt()


def test_rendered_assets_cover_all_mode_routes_and_upgrade_rules() -> None:
    guide = render_entry_modes_guide()
    codex_skill = render_codex_entry_skill()
    openclaw_prompt = render_openclaw_entry_prompt()
    for mode in load_entry_modes():
        assert mode.display_name in guide
        assert mode.display_name in codex_skill
        assert mode.display_name in openclaw_prompt
        assert mode.default_runtime_mode in guide
        for action in mode.managed_entry_actions:
            assert action in guide
            assert action in codex_skill
            assert action in openclaw_prompt
        for route in mode.lightweight_routes + mode.managed_routes + mode.auxiliary_routes + mode.governance_routes:
            if route:
                assert route in guide
                assert route in codex_skill
                assert route in openclaw_prompt
        for trigger in mode.upgrade_triggers:
            assert trigger in guide
            assert trigger in codex_skill
            assert trigger in openclaw_prompt
```

并补一个文档断言：

```python
def test_runtime_docs_link_to_agent_entry_guide() -> None:
    runtime_doc = (REPO_ROOT / "guides" / "agent_runtime_interface.md").read_text(encoding="utf-8")
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "guides/agent_entry_modes.md" in runtime_doc
    assert "guides/agent_entry_modes.md" in readme
    assert "Codex / Claude Code / OpenClaw" in readme
```

- [ ] **Step 2: 运行测试确认 RED**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_agent_entry_assets.py`

Expected: 因为 repo 内文件尚未创建或内容不一致而失败。

- [ ] **Step 3: 生成并整理公开资产**

先运行同步命令：

```bash
cd /Users/gaofeng/workspace/med-autoscience
PYTHONPATH=src python3 -m med_autoscience.cli sync-agent-entry-assets --repo-root .
```

Expected: 输出 4 个写入路径。

然后补充手工文档接线：

- 在 `guides/agent_runtime_interface.md` 新增对 `guides/agent_entry_modes.md` 的引用，说明第三方 Agent 应先看入口模式再决定是否进入 `profile/bootstrap/controller`
- 在 `README.md` 的技术执行者入口或 Quick Start 附近增加一句，明确兼容 `Codex / Claude Code / OpenClaw`，并指向新的入口 guide

`Codex` 薄入口 Skill 文本至少覆盖：

```md
1. 五类入口逐项列出，且每类都写明默认运行模式
2. 每类都写明 preconditions、lightweight route、managed route、auxiliary route（如有）
3. 若属于全自动科研推进，先走 doctor / bootstrap / overlay-status，再进入 managed routes
4. 若属于轻量专项任务，先在 lightweight routes 中执行
5. 一旦触发正式状态 / 正式变更 / 正式交付 / 后续接力，立即升级为正式纳管模式
```

`OpenClaw` prompt 至少覆盖同样五条，不引入第二套规则。

- [ ] **Step 4: 运行测试确认 GREEN**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_agent_entry_assets.py`

Expected: repo 内 guide / yaml / wrapper 资产全部与 renderer 输出一致，且对五类入口的默认模式、升级接入动作、路由、升级规则做了结构化覆盖校验。

- [ ] **Step 5: Commit**

```bash
cd /Users/gaofeng/workspace/med-autoscience
git add guides/agent_entry_modes.md templates/agent_entry_modes.yaml templates/codex/medautoscience-entry.SKILL.md templates/openclaw/medautoscience-entry.prompt.md guides/agent_runtime_interface.md README.md tests/test_agent_entry_assets.py
git commit -m "docs: publish third-party agent entry assets"
```

## Task 4: 全量验证与交接

**Files:**
- 无新增实现文件，仅验证与交接

- [ ] **Step 1: 跑本功能相关的 targeted tests**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_agent_entry_modes.py tests/test_agent_entry_assets.py tests/test_cli.py`

Expected: 全绿，且 `show-agent-entry-modes` / `sync-agent-entry-assets` 路径覆盖通过。

- [ ] **Step 2: 跑一次真实命令检查导出行为**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src python3 -m med_autoscience.cli show-agent-entry-modes`

Expected: JSON 输出中存在 `full_research`、`experiment`、`journal-resolution`、`Codex`、`Claude Code`、`OpenClaw`。

- [ ] **Step 3: 再跑一次 repo 同步命令，确认不会生成脏 diff**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src python3 -m med_autoscience.cli sync-agent-entry-assets --repo-root . && git diff --exit-code -- guides/agent_entry_modes.md templates/agent_entry_modes.yaml templates/codex/medautoscience-entry.SKILL.md templates/openclaw/medautoscience-entry.prompt.md`

Expected: `git diff --exit-code` 返回 0，说明 checked-in 资产与 renderer 同步。

- [ ] **Step 4: 跑全量 pytest**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q`

Expected: 全绿。

- [ ] **Step 5: 交接说明**

交接时必须明确：

- canonical facts 在 `src/med_autoscience/agent_entry/resources/agent_entry_modes.yaml`
- `templates/agent_entry_modes.yaml` 是由 canonical facts 导出的公开镜像
- repo 中衍生公开资产由 `sync-agent-entry-assets` 统一导出
- 正式主运行链必须保持 `scout -> idea -> experiment -> write -> finalize`
- `decision` 是治理/门控，不替代 `experiment`
