# Remove AutoFigure Branch Implementation Plan

Owner: `MedAutoScience`
Purpose: `superpowers_history_record`
State: `history_provenance`
Machine boundary: 人读历史过程稿。当前 contract、runtime truth、policy truth、regression oracle 和 owner boundary 继续归核心 docs、contracts、source、tests、runtime/controller surfaces 和 owner receipts。

Read rule: 本文是 repo-tracked Superpowers 过程稿的历史快照。正文中的 REQUIRED SUB-SKILL、checkbox、File Structure、旧 CLI/MCP/runtime/workspace 路径、DeepScientist/MDS/Hermes 或 current/default wording 只按当时 design/plan provenance 读取；当前 MAS truth、执行顺序、runtime owner、quality/publication/artifact authority 和 regression oracle 以 active owner docs、核心五件套、contracts、source、tests 与 live read-model 为准。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the AutoFigure-Edit sidecar branch from MedAutoScience and converge all paper-facing figure generation onto MedAutoScience-controlled programmatic routes.

**Architecture:** Delete AutoFigure-specific bootstrap, profile, registry, controller, and route surfaces rather than leaving soft-disabled compatibility paths. Keep only evidence-figure repair and programmatic illustration routes, and tighten write/guide surfaces so figure quality is governed by MedAutoScience itself.

**Tech Stack:** Python, pytest, MedAutoScience CLI/controllers/profiles/guides.

---

### Task 1: Rewrite the expected contract in tests

**Files:**
- Modify: `tests/test_profiles.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_figure_routes.py`
- Modify: `tests/test_figure_loop_guard.py`
- Modify: `tests/test_sidecar_provider_registry.py`
- Delete: `tests/test_autofigure_edit_adapter.py`
- Delete: `tests/test_autofigure_edit_sidecar_controller.py`

- [ ] Remove AutoFigure-specific expectations from profile, bootstrap, registry, and route tests.
- [ ] Make figure route tests assert that only `figure_script_fix` and `figure_illustration_program` remain.
- [ ] Make registry tests assert that `autofigure_edit` is no longer a supported provider.
- [ ] Delete AutoFigure-only test files so the remaining test surface defines the target contract.

### Task 2: Remove AutoFigure-specific runtime and provider code

**Files:**
- Modify: `src/med_autoscience/profiles.py`
- Modify: `src/med_autoscience/doctor.py`
- Modify: `src/med_autoscience/cli.py`
- Modify: `src/med_autoscience/controllers/__init__.py`
- Modify: `src/med_autoscience/adapters/__init__.py`
- Modify: `src/med_autoscience/sidecars/registry.py`
- Modify: `src/med_autoscience/figure_routes.py`
- Modify: `src/med_autoscience/controllers/figure_loop_guard.py`
- Delete: `src/med_autoscience/adapters/autofigure_edit.py`
- Delete: `src/med_autoscience/controllers/autofigure_edit_runtime.py`
- Delete: `src/med_autoscience/controllers/autofigure_edit_sidecar.py`

- [ ] Remove AutoFigure fields from workspace profile parsing and serialization.
- [ ] Remove AutoFigure bootstrap/status reporting from doctor and CLI.
- [ ] Delete the AutoFigure provider from the sidecar registry.
- [ ] Collapse figure route handling so programmatic illustration is the only illustration route.
- [ ] Update guard messages so explanation figures are explicitly programmatic and never sidecar-based.

### Task 3: Recenter figure quality control on MedAutoScience

**Files:**
- Modify: `src/med_autoscience/overlay/templates/deepscientist-write.SKILL.md`
- Modify: `guides/sidecar_figure_routes.md`
- Modify: `src/med_autoscience/controllers/workspace_init.py`
- Modify: `README.md`

- [ ] Rewrite the guide so it documents only MedAutoScience-controlled figure routes.
- [ ] Remove AutoFigure setup from generated workspace defaults.
- [ ] Strengthen write-stage guidance to require programmatic, manuscript-safe illustration output with restrained paper styling.

### Task 4: Verify and clean the workspace residue

**Files:**
- Modify as needed after failing tests.
- Remove runtime residue from `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/ops/autofigure-edit`

- [ ] Run focused pytest on touched surfaces.
- [ ] Run full `pytest`.
- [ ] Remove the local AutoFigure checkout from the DM-CVD workspace so no dormant sidecar residue remains.
