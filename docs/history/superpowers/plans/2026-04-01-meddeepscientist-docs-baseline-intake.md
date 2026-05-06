# MedDeepScientist Docs Baseline Intake Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align `med-autoscience` public docs with the `MedDeepScientist` runtime naming/install model, then unblock the first audited upstream intake by fixing the pre-existing baseline failure and absorbing `bf97bfb`.

**Architecture:** Keep `MedAutoScience` as the only human/agent entrypoint, document `MedDeepScientist` (`med-deepscientist` repo) as the controlled runtime, and treat upstream `DeepScientist` as the intake source rather than the default installed runtime. Fix the baseline failure on `med-deepscientist/main` first, then cherry-pick the single approved runtime bugfix in the dedicated intake worktree.

**Tech Stack:** Markdown docs, Python/pytest, git worktrees, controlled-fork intake flow.

---

### Task 1: Repair `med-autoscience` public runtime wording

**Files:**
- Modify: `README.md`
- Modify: `guides/runtime_boundary.md`
- Modify: `guides/disease_workspace_quickstart.md`
- Modify: `guides/workspace_architecture.md`
- Modify: `guides/agent_runtime_interface.md`
- Modify: `guides/sidecar_figure_routes.md`
- Modify: `bootstrap/README.md`
- Modify: `profiles/workspace.profile.template.toml`

- [ ] **Step 1: Update public wording**
- [ ] **Step 2: Verify that install/entry docs now point to `MedDeepScientist` / `med-deepscientist` instead of treating upstream `DeepScientist` as the default runtime**
- [ ] **Step 3: Commit and push the documentation repair on `med-autoscience/main`**

### Task 2: Fix the pre-existing baseline failure on `med-deepscientist`

**Files:**
- Modify: `/Users/gaofeng/workspace/med-deepscientist/src/...` (to be determined by root-cause investigation)
- Modify: `/Users/gaofeng/workspace/med-deepscientist/tests/test_daemon_api.py` only if a stricter regression assertion is needed

- [ ] **Step 1: Reproduce `tests/test_daemon_api.py::test_bash_exec_handlers_expose_sessions_logs_and_stop` on `main`**
- [ ] **Step 2: Trace root cause in bash exec/log persistence without mixing intake changes**
- [ ] **Step 3: Implement the minimal root-cause fix**
- [ ] **Step 4: Re-run the targeted daemon regression tests**
- [ ] **Step 5: Commit the baseline fix on `med-deepscientist/main`**

### Task 3: Execute round-1 upstream intake

**Files:**
- Modify: `/Users/gaofeng/workspace/med-deepscientist/.worktree/intake-2026-04-01-bootstrap-routing/...`
- Modify: `/Users/gaofeng/workspace/med-deepscientist/MEDICAL_FORK_MANIFEST.json`
- Modify: `/Users/gaofeng/workspace/med-deepscientist/docs/medical_fork_baseline.md`
- Modify: `/Users/gaofeng/workspace/med-deepscientist/docs/upstream_intake_round_2026_04_01.md`

- [ ] **Step 1: Rebase or fast-forward the intake worktree to the baseline-fix commit**
- [ ] **Step 2: Cherry-pick `bf97bfbf3fa4119924b10e2ff2c9edabece0b402`**
- [ ] **Step 3: Run the fork-side targeted regression suite**
- [ ] **Step 4: Run the relevant `med-autoscience` compatibility regression**
- [ ] **Step 5: Update intake audit and manifest, then commit the intake branch**
