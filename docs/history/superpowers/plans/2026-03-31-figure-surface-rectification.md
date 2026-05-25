# Figure Surface Rectification Implementation Plan

Owner: `MedAutoScience`
Purpose: `superpowers_history_record`
State: `history_provenance`
Machine boundary: 人读历史过程稿。当前 contract、runtime truth、policy truth、regression oracle 和 owner boundary 继续归核心 docs、contracts、source、tests、runtime/controller surfaces 和 owner receipts。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove manuscript-facing AutoFigure advertising, add an explicit AutoFigure-Edit capability/install contract, and split figure routes so evidence plots, AutoFigure illustrations, and programmatic illustrations have distinct controlled paths.

**Architecture:** Keep DeepScientist as the runtime of record, but move figure-surface governance into MedAutoScience. AutoFigure-Edit becomes a capability with explicit detection/bootstrap state rather than a prompt fiction, and manuscript-facing surface rules block poster-style or tooling-disclosure leakage from entering figures and captions.

**Tech Stack:** Python, pytest, MedAutoScience CLI/controllers/adapters, workspace profile contracts, official AutoFigure-Edit Docker deployment assumptions.

---

### Task 1: Freeze the figure-surface policy in code and tests

**Files:**
- Modify: `src/med_autoscience/overlay/templates/deepscientist-write.SKILL.md`
- Modify: `src/med_autoscience/policies/medical_publication_surface.py`
- Modify: `src/med_autoscience/controllers/medical_publication_surface.py`
- Test: `tests/test_overlay_installer.py`
- Test: `tests/test_medical_publication_surface.py`

- [ ] Remove manuscript-facing AutoFigure promotional text from the write overlay and replace it with an explicit prohibition on tooling disclosures in captions.
- [ ] Extend medical publication surface policy so manuscript-facing text blocks:
  - tool/vendor disclosures
  - `AutoFigure-Edit` / `deepscientist`
  - poster-style `Sources:` / `Why this matters` style labels where they appear in manuscript-facing assets
- [ ] Extend manuscript-facing scanning beyond `draft.md` and catalog strings so exported figure text assets can be audited.
- [ ] Add tests proving a manuscript-facing figure/caption cannot pass with the banned strings.

### Task 2: Add AutoFigure-Edit capability detection and bootstrap contract

**Files:**
- Create: `src/med_autoscience/adapters/autofigure_edit.py`
- Modify: `src/med_autoscience/doctor.py`
- Modify: `src/med_autoscience/cli.py`
- Modify: `src/med_autoscience/profiles.py`
- Modify: `src/med_autoscience/controllers/workspace_init.py`
- Test: `tests/test_autofigure_edit_adapter.py`
- Test: `tests/test_profiles.py`
- Test: `tests/test_cli.py`

- [ ] Add an adapter that models strict AutoFigure capability states such as `absent`, `repo_installed`, `configured`, `service_ready`, and `health_failed`.
- [ ] Base the adapter on official AutoFigure-Edit deployment assumptions:
  - official repo URL
  - Docker/Docker Compose runtime
  - required environment contract
  - health endpoint contract
- [ ] Add optional profile fields for AutoFigure bootstrap and installation roots/URLs.
- [ ] Teach `doctor` and `bootstrap` to surface this capability explicitly.
- [ ] Make bootstrap able to attempt installation/configuration bootstrap without pretending success when prerequisites are missing.

### Task 3: Split figure routes into explicit evidence, AutoFigure illustration, and programmatic illustration paths

**Files:**
- Modify: `src/med_autoscience/figure_routes.py`
- Modify: `src/med_autoscience/controllers/figure_loop_guard.py`
- Modify: `guides/sidecar_figure_routes.md`
- Test: `tests/test_figure_routes.py`
- Test: `tests/test_figure_loop_guard.py`
- Test: `tests/test_cli.py`

- [ ] Preserve `figure_script_fix:<figure-id>` for evidence-bearing plots only.
- [ ] Replace the single illustration route with two explicit routes:
  - `figure_illustration_autofigure:<figure-id>`
  - `figure_illustration_program:<figure-id>`
- [ ] Update controller messages and help text so no ambiguous route remains.
- [ ] Make AutoFigure routes require a ready capability state; programmatic illustration routes must remain available without AutoFigure.

### Task 4: Align sidecar gating with real capability state

**Files:**
- Modify: `src/med_autoscience/sidecars/registry.py`
- Modify: `src/med_autoscience/controllers/autofigure_edit_sidecar.py`
- Test: `tests/test_autofigure_edit_sidecar_controller.py`
- Test: `tests/test_sidecar_provider_registry.py`

- [ ] Require AutoFigure recommendation/provisioning to include a capability snapshot that proves the runtime is actually ready.
- [ ] Fail closed when the route is `figure_illustration_autofigure` but the capability state is not `service_ready`.
- [ ] Keep result plots outside AutoFigure scope.

### Task 5: Verify the policy surface end to end

**Files:**
- Modify as needed based on failing tests from earlier tasks.
- Test: targeted pytest suites covering overlay, publication surface, profiles, CLI, figure routes, and AutoFigure adapter/controller.

- [ ] Run focused pytest on all touched surfaces.
- [ ] Confirm no existing tests still encode the old “append AutoFigure-Edit to every main figure caption” behavior.
- [ ] Record any residual gap that still depends on DeepScientist upstream rather than MedAutoScience.
