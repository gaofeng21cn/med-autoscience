# Medical Display Surface Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把论文展示面 Phase 1 的 registry、catalog、shell contract 和 publication gate 接成统一平台能力，并让 Figure 1 / Table 1 成为正式受控对象。

**Architecture:** 继续沿用 `contract -> controller -> overlay -> adapter` 主线，不新造手工 CLI 旁路。新增 display registry 作为官方模板真相面，再把 renderer contract、reporting contract、catalog 和 publication gate 收紧到同一组字段与校验规则上。

**Tech Stack:** Python 3.11、pytest、现有 MedAutoScience controller/policy 架构、R analysis bundle package registry

---

### Task 1: Display Registry 与 Renderer Contract

**Files:**
- Create: `src/med_autoscience/display_registry.py`
- Modify: `src/med_autoscience/figure_renderer_contract.py`
- Test: `tests/test_display_registry.py`
- Test: `tests/test_figure_renderer_contract.py`

- [ ] **Step 1: 写 registry 红灯测试**

```python
import importlib


def test_phase1_registry_exposes_official_templates_and_shells() -> None:
    module = importlib.import_module("med_autoscience.display_registry")

    evidence = module.list_evidence_figure_specs()
    illustrations = module.list_illustration_shell_specs()
    tables = module.list_table_shell_specs()

    assert {item.template_id for item in evidence} >= {
        "roc_curve_binary",
        "pr_curve_binary",
        "calibration_curve_binary",
        "decision_curve_binary",
        "kaplan_meier_grouped",
        "cumulative_incidence_grouped",
        "umap_scatter_grouped",
        "pca_scatter_grouped",
        "heatmap_group_comparison",
        "correlation_heatmap",
        "forest_effect_main",
        "shap_summary_beeswarm",
    }
    assert {item.shell_id for item in illustrations} == {"cohort_flow_figure"}
    assert {item.shell_id for item in tables} == {"table1_baseline_characteristics"}
```

- [ ] **Step 2: 跑 registry 红灯测试确认失败**

Run: `pytest tests/test_display_registry.py::test_phase1_registry_exposes_official_templates_and_shells -v`
Expected: FAIL with `ModuleNotFoundError` or missing registry APIs

- [ ] **Step 3: 写 renderer contract 红灯测试**

```python
import importlib


def test_validate_renderer_contract_requires_template_and_qc_fields() -> None:
    module = importlib.import_module("med_autoscience.figure_renderer_contract")

    errors = module.validate_renderer_contract(
        {
            "figure_semantics": "evidence",
            "renderer_family": "r_ggplot2",
            "selection_rationale": "Publication-facing ROC figure stays on the audited R stack.",
            "fallback_on_failure": False,
            "failure_action": "block_and_fix_environment",
        }
    )

    assert "template_id must be non-empty" in errors
    assert "layout_qc_profile must be non-empty" in errors
    assert "required_exports must contain at least one export format" in errors
```

- [ ] **Step 4: 跑 renderer 红灯测试确认失败**

Run: `pytest tests/test_figure_renderer_contract.py::test_validate_renderer_contract_requires_template_and_qc_fields -v`
Expected: FAIL because current contract does not validate `template_id` / `layout_qc_profile` / `required_exports`

- [ ] **Step 5: 最小实现 registry 与收紧 renderer contract**

```python
# src/med_autoscience/display_registry.py
@dataclass(frozen=True)
class EvidenceFigureSpec:
    template_id: str
    display_name: str
    evidence_class: str
    renderer_family: str
    input_schema_id: str
    layout_qc_profile: str
    required_exports: tuple[str, ...]


def get_evidence_figure_spec(template_id: str) -> EvidenceFigureSpec: ...
def list_evidence_figure_specs() -> tuple[EvidenceFigureSpec, ...]: ...
```

```python
# src/med_autoscience/figure_renderer_contract.py
def validate_renderer_contract(payload: object, *, label: str = "renderer_contract") -> list[str]:
    ...
    template_id = str(payload.get("template_id") or "").strip()
    layout_qc_profile = str(payload.get("layout_qc_profile") or "").strip()
    required_exports = payload.get("required_exports")
    ...
```

- [ ] **Step 6: 跑 Task 1 测试**

Run: `pytest tests/test_display_registry.py tests/test_figure_renderer_contract.py -v`
Expected: PASS

- [ ] **Step 7: 提交 Task 1**

```bash
git add src/med_autoscience/display_registry.py src/med_autoscience/figure_renderer_contract.py tests/test_display_registry.py tests/test_figure_renderer_contract.py
git commit -m "feat: add display registry and renderer contract fields"
```

### Task 2: Reporting Contract / Hydration / Audit 接入 Figure 1 与 Table 1 Shell

**Files:**
- Modify: `src/med_autoscience/policies/medical_reporting_contract.py`
- Modify: `src/med_autoscience/controllers/medical_reporting_contract.py`
- Modify: `src/med_autoscience/controllers/medical_reporting_audit.py`
- Modify: `src/med_autoscience/controllers/quest_hydration.py`
- Test: `tests/test_medical_reporting_contract.py`
- Test: `tests/test_medical_reporting_audit.py`
- Test: `tests/test_quest_hydration.py`

- [ ] **Step 1: 写 reporting shell requirement 红灯测试**

```python
import importlib


def test_resolve_medical_reporting_contract_exposes_display_surface_requirements() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_reporting_contract")

    contract = module.resolve_medical_reporting_contract(
        study_archetype="clinical_classifier",
        manuscript_family="prediction_model",
        endpoint_type="binary",
        submission_target_family="general_medical_journal",
    )

    assert contract.required_illustration_shells == ("cohort_flow_figure",)
    assert contract.required_table_shells == ("table1_baseline_characteristics",)
    assert contract.required_evidence_templates == ()
```

- [ ] **Step 2: 跑红灯测试确认失败**

Run: `pytest tests/test_medical_reporting_contract.py::test_resolve_medical_reporting_contract_exposes_display_surface_requirements -v`
Expected: FAIL because current dataclass lacks the new fields

- [ ] **Step 3: 写 hydration / audit 红灯测试**

```python
import importlib
import json


def test_run_quest_hydration_writes_display_surface_contract_files(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.quest_hydration")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    (quest_root / "paper").mkdir(parents=True, exist_ok=True)

    module.run_hydration(
        quest_root=quest_root,
        hydration_payload={
            "medical_analysis_contract": {"status": "resolved"},
            "medical_reporting_contract": {
                "status": "resolved",
                "required_illustration_shells": ["cohort_flow_figure"],
                "required_table_shells": ["table1_baseline_characteristics"],
                "required_evidence_templates": [],
            },
            "entry_state_summary": "summary",
        },
    )

    assert (quest_root / "paper" / "cohort_flow.json").exists()
    assert (quest_root / "paper" / "baseline_characteristics_schema.json").exists()
```

- [ ] **Step 4: 跑红灯测试确认失败**

Run: `pytest tests/test_quest_hydration.py::test_run_quest_hydration_writes_display_surface_contract_files tests/test_medical_reporting_audit.py -v`
Expected: FAIL because hydration does not seed shell files and audit does not require baseline schema

- [ ] **Step 5: 最小实现 reporting/hydration/audit 接线**

```python
# src/med_autoscience/policies/medical_reporting_contract.py
@dataclass(frozen=True)
class MedicalReportingContract:
    ...
    required_illustration_shells: tuple[str, ...]
    required_table_shells: tuple[str, ...]
    required_evidence_templates: tuple[str, ...]
```

```python
# src/med_autoscience/controllers/quest_hydration.py
def _write_default_shell_payloads(*, quest_root: Path, reporting_contract: dict[str, object]) -> list[str]:
    ...
```

```python
# src/med_autoscience/controllers/medical_reporting_audit.py
if "table1_baseline_characteristics" in required_table_shells and not (paper_root / "baseline_characteristics_schema.json").exists():
    blockers.append("missing_baseline_characteristics_schema")
```

- [ ] **Step 6: 跑 Task 2 测试**

Run: `pytest tests/test_medical_reporting_contract.py tests/test_medical_reporting_audit.py tests/test_quest_hydration.py -v`
Expected: PASS

- [ ] **Step 7: 提交 Task 2**

```bash
git add src/med_autoscience/policies/medical_reporting_contract.py src/med_autoscience/controllers/medical_reporting_contract.py src/med_autoscience/controllers/medical_reporting_audit.py src/med_autoscience/controllers/quest_hydration.py tests/test_medical_reporting_contract.py tests/test_medical_reporting_audit.py tests/test_quest_hydration.py
git commit -m "feat: wire display surface shell requirements into hydration"
```

### Task 3: Catalog Contract 与 Publication Gate 收紧

**Files:**
- Modify: `src/med_autoscience/policies/medical_publication_surface.py`
- Modify: `src/med_autoscience/controllers/medical_publication_surface.py`
- Test: `tests/test_medical_publication_surface.py`

- [ ] **Step 1: 写 gate 红灯测试**

```python
import importlib


def test_validate_figure_semantics_manifest_requires_registry_aligned_renderer_contract() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_publication_surface")

    errors = module.validate_figure_semantics_manifest(
        {
            "figures": [
                {
                    "figure_id": "F4",
                    "story_role": "performance",
                    "research_question": "question",
                    "direct_message": "message",
                    "clinical_implication": "implication",
                    "interpretation_boundary": "boundary",
                    "panel_messages": [{"panel_id": "A", "message": "panel"}],
                    "legend_glossary": [{"term": "auc", "explanation": "area under curve"}],
                    "threshold_semantics": "semantic",
                    "stratification_basis": "basis",
                    "recommendation_boundary": "boundary",
                    "renderer_contract": {
                        "figure_semantics": "evidence",
                        "renderer_family": "r_ggplot2",
                        "selection_rationale": "reason",
                        "fallback_on_failure": False,
                        "failure_action": "block_and_fix_environment",
                    },
                }
            ]
        }
    )

    assert any("template_id" in item for item in errors)
```

- [ ] **Step 2: 跑红灯测试确认失败**

Run: `pytest tests/test_medical_publication_surface.py::test_validate_figure_semantics_manifest_requires_registry_aligned_renderer_contract -v`
Expected: FAIL because current validator accepts the weaker renderer contract

- [ ] **Step 3: 扩展 catalog / gate 最小实现**

```python
# src/med_autoscience/policies/medical_publication_surface.py
def validate_figure_catalog(payload: object) -> list[str]: ...
def validate_table_catalog(payload: object) -> list[str]: ...
```

```python
# src/med_autoscience/controllers/medical_publication_surface.py
figure_catalog_valid, figure_catalog_hits = inspect_required_json_contract(...)
table_catalog_valid, table_catalog_hits = inspect_required_json_contract(...)
```

- [ ] **Step 4: 跑 Task 3 测试**

Run: `pytest tests/test_medical_publication_surface.py -v`
Expected: PASS

- [ ] **Step 5: 提交 Task 3**

```bash
git add src/med_autoscience/policies/medical_publication_surface.py src/med_autoscience/controllers/medical_publication_surface.py tests/test_medical_publication_surface.py
git commit -m "feat: validate display catalogs in medical publication gate"
```

### Task 4: Submission Export 与 Analysis Bundle 对齐

**Files:**
- Modify: `src/med_autoscience/controllers/submission_minimal.py`
- Modify: `src/med_autoscience/study_runtime_analysis_bundle.py`
- Test: `tests/test_submission_minimal.py`
- Test: `tests/test_study_runtime_analysis_bundle.py`

- [ ] **Step 1: 写 submission/export 红灯测试**

```python
import importlib


def test_create_submission_minimal_package_preserves_template_metadata_in_manifest(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)
    ...
    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    assert manifest["figures"][0]["template_id"] == "roc_curve_binary"
    assert manifest["tables"][0]["table_shell_id"] == "table1_baseline_characteristics"
```

- [ ] **Step 2: 跑红灯测试确认失败**

Run: `pytest tests/test_submission_minimal.py::test_create_submission_minimal_package_preserves_template_metadata_in_manifest -v`
Expected: FAIL because export manifest drops display-surface metadata

- [ ] **Step 3: 扩展 submission/export 与 R bundle**

```python
# src/med_autoscience/controllers/submission_minimal.py
figure_manifest_entries.append(
    {
        "figure_id": entry["figure_id"],
        "template_id": entry.get("template_id"),
        "renderer_family": entry.get("renderer_family"),
        "qc_profile": entry.get("qc_profile"),
        ...
    }
)
```

```python
# src/med_autoscience/study_runtime_analysis_bundle.py
DEFAULT_R_ANALYSIS_BUNDLE_PACKAGES = (
    ...
    "ggrepel",
    "ggsci",
    "cowplot",
    "pROC",
    "precrec",
    "dcurves",
    "ggsurvfit",
    "forestploter",
    "ComplexHeatmap",
    "circlize",
)
```

- [ ] **Step 4: 跑 Task 4 测试**

Run: `pytest tests/test_submission_minimal.py tests/test_study_runtime_analysis_bundle.py -v`
Expected: PASS

- [ ] **Step 5: 提交 Task 4**

```bash
git add src/med_autoscience/controllers/submission_minimal.py src/med_autoscience/study_runtime_analysis_bundle.py tests/test_submission_minimal.py tests/test_study_runtime_analysis_bundle.py
git commit -m "feat: carry display metadata into submission package"
```

### Task 5: 全量回归与收尾

**Files:**
- Modify: `src/med_autoscience/overlay/templates/med-deepscientist-write.SKILL.md`
- Test: `tests/test_policy_integration.py`

- [ ] **Step 1: 更新 overlay 最小 shape 文本**

```markdown
### `figure_catalog.json` minimum shape
- `template_id`
- `renderer_family`
- `input_schema_id`
- `qc_profile`
- `qc_result`
```

- [ ] **Step 2: 跑关键回归**

Run: `pytest tests/test_display_registry.py tests/test_figure_renderer_contract.py tests/test_medical_reporting_contract.py tests/test_medical_reporting_audit.py tests/test_quest_hydration.py tests/test_medical_publication_surface.py tests/test_submission_minimal.py tests/test_policy_integration.py tests/test_study_runtime_analysis_bundle.py -v`
Expected: PASS

- [ ] **Step 3: 最终提交**

```bash
git add src/med_autoscience tests docs/superpowers/plans/2026-04-03-medical-display-surface-phase1.md
git commit -m "feat: implement medical display surface phase 1"
```
