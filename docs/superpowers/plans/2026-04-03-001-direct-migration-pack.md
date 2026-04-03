# 001 Direct Migration Pack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the audited reporting-contract and hydration path so the current `001` time-to-event direct-migration set is scaffolded as first-class display requirements instead of ad hoc paper assets.

**Architecture:** Keep the change inside the existing contract -> hydration -> audit chain. First expand the reporting contract so `Figure 5` generalizability becomes a registered requirement for time-to-event prediction-model studies. Then extend hydration to emit the required input stub JSON files for direct-migration evidence/table assets, and tighten audit checks so missing stubs are caught before paper export.

**Tech Stack:** Python, pytest, existing `med_autoscience` controllers/policies, JSON file contracts

---

### Task 1: Expand The Time-to-Event Reporting Contract

**Files:**
- Modify: `src/med_autoscience/policies/medical_reporting_contract.py`
- Modify: `tests/test_medical_reporting_contract.py`
- Modify: `tests/test_medical_startup_contract_support.py`

- [ ] **Step 1: Write the failing tests**

Add assertions that the time-to-event prediction-model contract now includes `multicenter_generalizability_overview` as `F5`, and that `required_evidence_templates` is no longer empty for this route.

```python
assert contract.figure_shell_requirements == (
    "cohort_flow_figure",
    "time_to_event_discrimination_calibration_panel",
    "kaplan_meier_grouped",
    "time_to_event_decision_curve",
    "multicenter_generalizability_overview",
)
assert contract.required_evidence_templates == (
    "time_to_event_discrimination_calibration_panel",
    "kaplan_meier_grouped",
    "time_to_event_decision_curve",
    "multicenter_generalizability_overview",
)
assert contract.display_shell_plan[-1] == DisplayShellPlanItem(
    display_id="multicenter_generalizability",
    display_kind="figure",
    requirement_key="multicenter_generalizability_overview",
    catalog_id="F5",
)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_medical_reporting_contract.py tests/test_medical_startup_contract_support.py -q`
Expected: FAIL because the current contract ends at `F4` and reports no required evidence templates.

- [ ] **Step 3: Write minimal implementation**

Update `_DISPLAY_INSTANCE_MAP`, the time-to-event branch in `resolve_medical_reporting_contract`, and `required_evidence_templates` so the route explicitly carries `F2-F5`.

```python
    "multicenter_generalizability_overview": ("multicenter_generalizability", "figure", "F5"),
```

```python
        figure_shell_requirements = (
            "cohort_flow_figure",
            "time_to_event_discrimination_calibration_panel",
            "kaplan_meier_grouped",
            "time_to_event_decision_curve",
            "multicenter_generalizability_overview",
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_medical_reporting_contract.py tests/test_medical_startup_contract_support.py -q`
Expected: PASS for the updated contract expectations.

### Task 2: Emit Hydration Stubs For Direct-Migration Assets

**Files:**
- Modify: `src/med_autoscience/controllers/quest_hydration.py`
- Modify: `tests/test_medical_startup_contract_support.py`
- Modify: `tests/test_quest_hydration.py`

- [ ] **Step 1: Write the failing tests**

Add tests that hydration writes pending input stubs for:

- `time_to_event_performance_summary.json`
- `time_to_event_discrimination_calibration_inputs.json`
- `time_to_event_grouped_inputs.json`
- `time_to_event_decision_curve_inputs.json`
- `multicenter_generalizability_inputs.json`

and that each stub carries the semantic `display_id`/`catalog_id` from the reporting contract.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_medical_startup_contract_support.py tests/test_quest_hydration.py -q`
Expected: FAIL because hydration currently only writes `cohort_flow.json` and `baseline_characteristics_schema.json`.

- [ ] **Step 3: Write minimal implementation**

Add a small helper in `quest_hydration.py` that maps each requirement key to its stub file and pending payload shape, then call it from `_write_display_surface_stubs`.

```python
def _build_display_input_stub(*, item: dict[str, str], reporting_contract_relpath: str) -> tuple[Path, dict[str, Any]] | None:
    ...
```

The minimal new stub payloads should include:

- schema/input id
- display id
- optional catalog id
- source contract path
- status like `required_pending_materialization`

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_medical_startup_contract_support.py tests/test_quest_hydration.py -q`
Expected: PASS with the new stub files written.

### Task 3: Tighten Medical Reporting Audit For New Stub Coverage

**Files:**
- Modify: `src/med_autoscience/controllers/medical_reporting_audit.py`
- Modify: `tests/test_medical_reporting_audit.py`

- [ ] **Step 1: Write the failing test**

Add a test where a time-to-event reporting contract declares `F2-F5`/`T2`, but one of the new input stub files is missing; the audit should emit a deterministic blocker such as `missing_multicenter_generalizability_inputs`.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_medical_reporting_audit.py -q`
Expected: FAIL because the audit currently checks only `cohort_flow.json` and `baseline_characteristics_schema.json`.

- [ ] **Step 3: Write minimal implementation**

Extend the audit controller with the same requirement-key -> required-input-file mapping used by hydration, and append a blocker whenever a required stub file is absent.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_medical_reporting_audit.py -q`
Expected: PASS and the new blocker appears when the stub is missing.

### Task 4: Full Verification

**Files:**
- Modify: `docs/medical_display_template_backlog.md` only if implementation details need a short note; otherwise no doc change.
- Test: `tests/test_medical_reporting_contract.py`
- Test: `tests/test_medical_startup_contract_support.py`
- Test: `tests/test_quest_hydration.py`
- Test: `tests/test_medical_reporting_audit.py`

- [ ] **Step 1: Run the focused verification set**

Run: `uv run pytest tests/test_medical_reporting_contract.py tests/test_medical_startup_contract_support.py tests/test_quest_hydration.py tests/test_medical_reporting_audit.py -q`
Expected: PASS for the full direct-migration infra slice.

- [ ] **Step 2: Commit**

```bash
git add src/med_autoscience/policies/medical_reporting_contract.py \
  src/med_autoscience/controllers/quest_hydration.py \
  src/med_autoscience/controllers/medical_reporting_audit.py \
  tests/test_medical_reporting_contract.py \
  tests/test_medical_startup_contract_support.py \
  tests/test_quest_hydration.py \
  tests/test_medical_reporting_audit.py \
  docs/superpowers/plans/2026-04-03-001-direct-migration-pack.md
git commit -m "feat: scaffold direct migration display assets"
```
