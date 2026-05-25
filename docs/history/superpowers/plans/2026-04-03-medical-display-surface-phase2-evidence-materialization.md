# Medical Display Surface Phase 2 Evidence Materialization Implementation Plan

Owner: `MedAutoScience`
Purpose: `superpowers_history_record`
State: `history_provenance`
Machine boundary: 人读历史过程稿。当前 contract、runtime truth、policy truth、regression oracle 和 owner boundary 继续归核心 docs、contracts、source、tests、runtime/controller surfaces 和 owner receipts。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让前 5 个高频 evidence figure 模板从“registry 已注册”升级为“controller 可正式物化并回写 figure catalog”。

**Architecture:** 继续复用 `display_surface_materialization` 作为唯一官方执行入口，不新建第二套 route truth。通过结构化输入 JSON 驱动 evidence template dispatch，先覆盖 `roc_curve_binary`、`pr_curve_binary`、`calibration_curve_binary`、`decision_curve_binary`、`kaplan_meier_grouped`，统一产出 `png/pdf` 和注册对齐的 catalog entry。

**Tech Stack:** Python 3.12、matplotlib、pytest、现有 MedAutoScience display registry / publication gate / catalog contract

---

### Task 1: Evidence Figure 输入夹具与红灯测试

**Files:**
- Modify: `tests/test_display_surface_materialization.py`

- [ ] **Step 1: 为前 5 个 evidence figure 增加结构化输入夹具**

```python
dump_json(
    paper_root / "binary_prediction_curve_inputs.json",
    {
        "schema_version": 1,
        "input_schema_id": "binary_prediction_curve_inputs_v1",
        "display_map": {
            "Figure2": {
                "template_id": "roc_curve_binary",
                "title": "ROC curve",
            }
        },
        "series": [
            {
                "label": "Model A",
                "x": [0.0, 0.1, 0.3, 1.0],
                "y": [0.0, 0.7, 0.9, 1.0],
                "auc": 0.83,
            }
        ],
    },
)
```

- [ ] **Step 2: 写 evidence materialization 红灯测试**

```python
def test_materialize_display_surface_generates_registered_evidence_figures(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path, include_evidence=True)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert "F2" in result["figures_materialized"]
    assert (paper_root / "figures" / "generated" / "F2_roc_curve_binary.png").exists()
    assert (paper_root / "figures" / "generated" / "F2_roc_curve_binary.pdf").exists()
```

- [ ] **Step 3: 跑红灯测试确认当前失败**

Run: `PYTHONPATH=src pytest tests/test_display_surface_materialization.py::test_materialize_display_surface_generates_registered_evidence_figures -v`
Expected: FAIL because evidence templates are not yet materialized

### Task 2: Controller 物化前 5 个 evidence figure

**Files:**
- Modify: `src/med_autoscience/controllers/display_surface_materialization.py`
- Modify: `src/med_autoscience/display_registry.py`

- [ ] **Step 1: 在 controller 中增加 evidence template dispatch**

```python
if requirement_key in _SUPPORTED_EVIDENCE_TEMPLATE_IDS:
    spec = display_registry.get_evidence_figure_spec(requirement_key)
    payload = _load_evidence_payload(...)
    output_png_path, output_pdf_path = _render_evidence_figure(...)
```

- [ ] **Step 2: 为 curve / survival 图实现最小但正式的 publication renderer**

```python
def _render_binary_prediction_curve(...): ...
def _render_decision_curve(...): ...
def _render_kaplan_meier_curve(...): ...
```

- [ ] **Step 3: 回写 registry 对齐的 figure catalog entry**

```python
entry = {
    "figure_id": figure_id,
    "template_id": spec.template_id,
    "renderer_family": spec.renderer_family,
    "paper_role": spec.allowed_paper_roles[0],
    "input_schema_id": spec.input_schema_id,
    "qc_profile": spec.layout_qc_profile,
    "qc_result": {"status": "pass", "issues": [], "checked_at": utc_now()},
    "export_paths": [...],
}
```

- [ ] **Step 4: 跑 Task 2 测试**

Run: `PYTHONPATH=src pytest tests/test_display_surface_materialization.py -v`
Expected: PASS

### Task 3: CLI 与 gate 对齐回归

**Files:**
- Modify: `tests/test_display_surface_materialization_cli.py`
- Test: `tests/test_medical_publication_surface.py`

- [ ] **Step 1: 扩展 CLI 测试验证 evidence figures 也被物化**

```python
assert payload["figures_materialized"] == ["F1", "F2", "F3", "F4", "F5", "F6"]
```

- [ ] **Step 2: 跑定向回归**

Run: `PYTHONPATH=src pytest tests/test_display_surface_materialization.py tests/test_display_surface_materialization_cli.py tests/test_medical_publication_surface.py -q`
Expected: PASS

- [ ] **Step 3: 跑相关全量回归**

Run: `PYTHONPATH=src pytest tests/test_display_registry.py tests/test_display_surface_materialization.py tests/test_display_surface_materialization_cli.py tests/test_figure_renderer_contract.py tests/test_medical_reporting_contract.py tests/test_medical_reporting_audit.py tests/test_quest_hydration.py tests/test_startup_hydration_validation.py tests/test_medical_publication_surface.py tests/test_submission_minimal.py tests/test_submission_minimal_display_surface.py tests/test_study_runtime_analysis_bundle.py tests/test_medical_startup_contract_support.py tests/test_policy_integration.py tests/test_runtime_protocol_study_runtime.py tests/test_study_runtime_router.py tests/test_overlay_installer.py -q`
Expected: PASS
