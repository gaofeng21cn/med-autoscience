# Medical Display Surface Phase 1B Shell Renderers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `cohort_flow_figure` 和 `table1_baseline_characteristics` 建立首个官方 shell materialization 闭环，让平台不仅声明需求，还能正式产出展示面 artifact 与 catalog entry。

**Architecture:** 新增一个 controller-first 的 materialization 控制器，读取 `paper/display_registry.json`、shell 文件和结构化 truth source，生成 figure/table 导出物并回写 catalog。先只覆盖 illustration shell 与 table shell，不碰 evidence figure script rerun。

**Tech Stack:** Python 3.12、matplotlib、pandas、pytest、现有 MedAutoScience controller/CLI 架构

---

### Task 1: Shell Materialization Controller

**Files:**
- Create: `src/med_autoscience/controllers/display_surface_materialization.py`
- Create: `tests/test_display_surface_materialization.py`
- Modify: `src/med_autoscience/display_registry.py`

- [ ] **Step 1: 写 controller 红灯测试**

```python
def test_materialize_display_surface_generates_official_shell_outputs(tmp_path):
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert (paper_root / "figures" / "generated" / "F1_cohort_flow.svg").exists()
    assert (paper_root / "figures" / "generated" / "F1_cohort_flow.png").exists()
    assert (paper_root / "tables" / "generated" / "T1_baseline_characteristics.md").exists()
    assert (paper_root / "tables" / "generated" / "T1_baseline_characteristics.csv").exists()
```

- [ ] **Step 2: 跑红灯测试确认失败**

Run: `PYTHONPATH=src pytest tests/test_display_surface_materialization.py::test_materialize_display_surface_generates_official_shell_outputs -v`
Expected: FAIL with missing controller

- [ ] **Step 3: 实现最小 materialization controller**

```python
def materialize_display_surface(*, paper_root: Path) -> dict[str, object]:
    registry = load_json(paper_root / "display_registry.json")
    for item in registry["displays"]:
        if item["requirement_key"] == "cohort_flow_figure":
            render_cohort_flow_shell(...)
        elif item["requirement_key"] == "table1_baseline_characteristics":
            render_table1_shell(...)
```

- [ ] **Step 4: 跑 Task 1 测试**

Run: `PYTHONPATH=src pytest tests/test_display_surface_materialization.py -v`
Expected: PASS

### Task 2: CLI 与 Catalog 回写

**Files:**
- Modify: `src/med_autoscience/cli.py`
- Modify: `src/med_autoscience/controllers/__init__.py`
- Test: `tests/test_display_surface_materialization_cli.py`

- [ ] **Step 1: 写 CLI 红灯测试**

```python
def test_cli_materialize_display_surface_emits_result_json(tmp_path, capsys):
    module = importlib.import_module("med_autoscience.cli")
    paper_root = build_display_surface_workspace(tmp_path)

    exit_code = module.main(["materialize-display-surface", "--paper-root", str(paper_root)])

    assert exit_code == 0
```

- [ ] **Step 2: 跑红灯测试确认失败**

Run: `PYTHONPATH=src pytest tests/test_display_surface_materialization_cli.py -v`
Expected: FAIL because CLI subcommand does not exist

- [ ] **Step 3: 实现 CLI 接入与 catalog 写回**

```python
if args.command == "materialize-display-surface":
    result = display_surface_materialization.materialize_display_surface(
        paper_root=Path(args.paper_root),
    )
```

- [ ] **Step 4: 跑 Task 2 测试**

Run: `PYTHONPATH=src pytest tests/test_display_surface_materialization_cli.py tests/test_display_surface_materialization.py -v`
Expected: PASS

### Task 3: 回归验证与 overlay 对齐

**Files:**
- Modify: `src/med_autoscience/overlay/templates/med-deepscientist-write.SKILL.md`
- Test: `tests/test_medical_publication_surface.py`
- Test: `tests/test_submission_minimal_display_surface.py`

- [ ] **Step 1: 更新 overlay 里 shell materialization 提示**

```markdown
- When `paper/display_registry.json` declares `cohort_flow_figure` or `table1_baseline_characteristics`,
  materialize them through `medautosci materialize-display-surface --paper-root paper`.
```

- [ ] **Step 2: 跑关键回归**

Run: `PYTHONPATH=src pytest tests/test_display_surface_materialization.py tests/test_display_surface_materialization_cli.py tests/test_medical_publication_surface.py tests/test_submission_minimal_display_surface.py -v`
Expected: PASS

- [ ] **Step 3: 全量相关回归**

Run: `PYTHONPATH=src pytest tests/test_display_registry.py tests/test_figure_renderer_contract.py tests/test_medical_reporting_contract.py tests/test_medical_reporting_audit.py tests/test_quest_hydration.py tests/test_startup_hydration_validation.py tests/test_display_surface_materialization.py tests/test_display_surface_materialization_cli.py tests/test_medical_publication_surface.py tests/test_submission_minimal.py tests/test_submission_minimal_display_surface.py tests/test_study_runtime_analysis_bundle.py tests/test_medical_startup_contract_support.py tests/test_policy_integration.py tests/test_runtime_protocol_study_runtime.py tests/test_study_runtime_router.py -q`
Expected: PASS
