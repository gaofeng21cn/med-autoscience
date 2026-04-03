# 001 Direct Migration Publication Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the remaining `001` direct-migration gap at the paper-facing export layer by requiring declared display requirements to actually appear in figure/table catalogs before publication export is treated as clear.

**Architecture:** Keep the change inside the existing publication/export chain instead of inventing a new side path. Read the semantic `display_shell_plan` from `paper/medical_reporting_contract.json`, derive the required `catalog_id` set for figures and tables, and make `medical_publication_surface` block whenever those required items are absent from the current catalogs. Add one submission-manifest acceptance test for the full `F2-F5 + T2` direct-migration set so the export surface is explicitly covered.

**Tech Stack:** Python, pytest, existing `medical_publication_surface` controller/policy, existing `submission_minimal` exporter, JSON file contracts

---

### Task 1: Add Publication-Gate Coverage Tests For Required Display Catalog IDs

**Files:**
- Modify: `tests/test_medical_publication_surface.py`

- [ ] **Step 1: Write the failing tests**

Add one test that builds a medicalized quest, writes `paper/medical_reporting_contract.json` with the semantic `F1-F5/T1-T2` display plan, then removes `F5` from `paper/figures/figure_catalog.json`. The publication-surface report must block on a deterministic coverage blocker and surface a precise hit mentioning the missing `F5`.

```python
dump_json(
    paper_root / "medical_reporting_contract.json",
    {
        "status": "resolved",
        "display_shell_plan": [
            {"display_id": "cohort_flow", "display_kind": "figure", "requirement_key": "cohort_flow_figure", "catalog_id": "F1"},
            {"display_id": "discrimination_calibration", "display_kind": "figure", "requirement_key": "time_to_event_discrimination_calibration_panel", "catalog_id": "F2"},
            {"display_id": "km_risk_stratification", "display_kind": "figure", "requirement_key": "kaplan_meier_grouped", "catalog_id": "F3"},
            {"display_id": "decision_curve", "display_kind": "figure", "requirement_key": "time_to_event_decision_curve", "catalog_id": "F4"},
            {"display_id": "multicenter_generalizability", "display_kind": "figure", "requirement_key": "multicenter_generalizability_overview", "catalog_id": "F5"},
            {"display_id": "baseline_characteristics", "display_kind": "table", "requirement_key": "table1_baseline_characteristics", "catalog_id": "T1"},
            {"display_id": "time_to_event_performance_summary", "display_kind": "table", "requirement_key": "table2_time_to_event_performance_summary", "catalog_id": "T2"},
        ],
    },
)
assert "required_display_catalog_coverage_incomplete" in report["blockers"]
assert any(hit["pattern_id"] == "required_display_catalog_item_missing" and hit["phrase"] == "F5" for hit in report["top_hits"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_medical_publication_surface.py::test_build_report_blocks_when_required_display_catalog_item_is_missing -q`
Expected: FAIL because `medical_publication_surface` currently validates only per-entry catalog shape, not required contract coverage.

- [ ] **Step 3: Add a clear-path companion test**

Add a second test that uses the same semantic `display_shell_plan`, but ensures all `F1-F5` and `T1-T2` items exist in the figure/table catalogs. The report should remain `clear`.

```python
assert report["status"] == "clear"
assert "required_display_catalog_coverage_incomplete" not in report["blockers"]
```

- [ ] **Step 4: Run the focused test slice**

Run: `uv run pytest tests/test_medical_publication_surface.py::test_build_report_blocks_when_required_display_catalog_item_is_missing tests/test_medical_publication_surface.py::test_build_report_accepts_complete_required_display_catalog_coverage -q`
Expected: FAIL on the missing-coverage case before implementation.

### Task 2: Implement Required Display Coverage Inspection In Publication Surface

**Files:**
- Modify: `src/med_autoscience/controllers/medical_publication_surface.py`

- [ ] **Step 1: Write minimal implementation**

Add helpers that read semantic `display_shell_plan` items from `paper/medical_reporting_contract.json`, extract required `catalog_id` values separately for figures and tables, and emit report hits whenever the current catalogs do not cover those required IDs.

```python
def load_required_display_catalog_ids(path: Path) -> tuple[set[str], set[str]]:
    ...

def inspect_required_display_catalog_coverage(
    *,
    reporting_contract_path: Path,
    figure_ids: set[str],
    table_ids: set[str],
) -> tuple[bool, list[dict[str, Any]]]:
    ...
```

Then wire the result into `build_surface_report`:

```python
required_display_coverage_valid, required_display_hits = inspect_required_display_catalog_coverage(
    reporting_contract_path=state.paper_root / "medical_reporting_contract.json",
    figure_ids=figure_ids,
    table_ids=table_ids,
)
if not required_display_coverage_valid:
    blockers.append("required_display_catalog_coverage_incomplete")
```

The missing-hit payload should use one deterministic pattern id:

```python
{
    "pattern_id": "required_display_catalog_item_missing",
    "phrase": "F5",
    "excerpt": "Required figure catalog item `F5` declared by medical_reporting_contract.display_shell_plan is missing from the current figure catalog.",
}
```

- [ ] **Step 2: Run test to verify it passes**

Run: `uv run pytest tests/test_medical_publication_surface.py::test_build_report_blocks_when_required_display_catalog_item_is_missing tests/test_medical_publication_surface.py::test_build_report_accepts_complete_required_display_catalog_coverage -q`
Expected: PASS for both tests.

### Task 3: Add A Direct-Migration Submission Manifest Acceptance Test

**Files:**
- Modify: `tests/test_submission_minimal_display_surface.py`

- [ ] **Step 1: Write the regression test**

Add one test that extends the workspace fixture into a realistic `001`-style direct-migration package with:

- `F2` discrimination/calibration
- `F3` Kaplan-Meier grouped
- `F4` decision curve
- `F5` multicenter generalizability
- `T2` time-to-event performance summary

and then asserts that `create_submission_minimal_package()` preserves all of them in `submission_manifest.json` with their audited metadata.

```python
assert set(figures_by_id) >= {"F1", "F2", "F3", "F4", "F5"}
assert figures_by_id["F5"]["template_id"] == "multicenter_generalizability_overview"
assert tables_by_id["T2"]["table_shell_id"] == "table2_time_to_event_performance_summary"
assert all((workspace_root / path).exists() for path in figures_by_id["F5"]["output_paths"])
```

- [ ] **Step 2: Run the regression test**

Run: `uv run pytest tests/test_submission_minimal_display_surface.py::test_create_submission_minimal_package_preserves_001_direct_migration_display_entries -q`
Expected: PASS if exporter already preserves the audited metadata; otherwise FAIL and fix only the minimal missing export-path propagation.

### Task 4: Full Verification

**Files:**
- Modify: `docs/superpowers/plans/2026-04-03-001-direct-migration-publication-gate.md`
- Test: `tests/test_medical_publication_surface.py`
- Test: `tests/test_submission_minimal_display_surface.py`

- [ ] **Step 1: Run the focused verification set**

Run: `uv run pytest tests/test_medical_publication_surface.py tests/test_submission_minimal_display_surface.py tests/test_medical_reporting_contract.py tests/test_medical_startup_contract_support.py tests/test_quest_hydration.py tests/test_medical_reporting_audit.py tests/test_startup_hydration_validation.py tests/test_display_surface_materialization.py -q`
Expected: PASS for the direct-migration contract -> hydration -> materialization -> publication/export slice.

- [ ] **Step 2: Commit**

```bash
git add src/med_autoscience/controllers/medical_publication_surface.py \
  tests/test_medical_publication_surface.py \
  tests/test_submission_minimal_display_surface.py
git add -f docs/superpowers/plans/2026-04-03-001-direct-migration-publication-gate.md
git commit -m "feat: gate publication surface on required display coverage"
```
