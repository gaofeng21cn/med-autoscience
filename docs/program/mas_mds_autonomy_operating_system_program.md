# MAS/MDS Autonomy Operating System Program

Status: `active program board`  
Owner: `MedAutoScience`  
Scope: long-running autonomy, medical-paper quality, MAS single-project evolution, quality-preserving acceleration, natural-boundary maintainability

## Target State

`MedAutoScience` is the single medical-research product and quality-control plane. It owns research entry, study truth, quality contract, publication gate, progress projection, and submission authority. `MedDeepScientist` remains a controlled runtime backend, behavior oracle, and upstream intake buffer.

This program does not make physical monorepo absorb a current completion signal. Physical absorb, runtime core ingest, and broader cutover remain post-gate work after runtime protocol, parity proof, and MAS-owned contract surfaces are stable.

## Program Board

The repo-tracked program board is exposed by `med_autoscience.controllers.autonomy_operating_system_program`.

It fixes eight lanes:

1. `P0_baseline_freeze`
2. `P1_autonomy_reliability_core`
3. `P2_observability_and_profiling`
4. `P3_medical_quality_os`
5. `P4_quality_preserving_fast_lane`
6. `P5_mas_mds_strangler_program`
7. `P6_natural_boundary_refactor`
8. `P7_incident_learning_loop`

`P2_observability_and_profiling` also owns delivery metrics / forecasting projection so ETA, blocker, next confirmation, and human-gate wording stay on the same operator truth surface instead of becoming a separate owner lane.

The board is deliberately stricter than a prose roadmap: every lane has an owner, primary surfaces, and an acceptance gate. The program is not release-ready until every lane is completed or absorbed and none are blocked.

The `2026-04-30` one-shot learning program folds external agent / research / orchestration learning into this board. New sources are no longer accepted as prose-only lessons: each source must be classified as `adopt_contract`, `adopt_template`, `watch_only`, or `reject`, and any `adopt_*` decision must land on runtime, controller, eval_hygiene, operator projection, or tests.

## Non-Negotiable Gates

- MAS remains the product owner.
- MDS remains runtime/backend/oracle/intake, not a second product owner.
- Quality-preserving acceleration keeps `gate_relaxation_allowed = false`.
- Long-running studies must expose state, blocker, owner, recovery route, and ETA evidence.
- New implementation must enter natural modules and avoid mechanical `chunk` / `part` splits.

## One-Shot External Learning Rules

External learning is complete only when it becomes repo truth. The accepted source families are:

- orchestration systems: work unit, retry/backoff, workspace isolation, observability.
- research-agent systems: hypothesis, baseline, analysis campaign, failed-path learning.
- evaluation systems: evidence ledger, review ledger, claim/evidence consistency, AI reviewer gate.
- safety/runtime systems: trust boundary, secret handling, authorization scope, fail-closed worker.
- product ops systems: operator projection, incident learning, handoff, soak proof.

Stop learning the current source snapshot when an equivalent MAS contract exists, or when the remaining material is only external owner mechanics, tracker-specific workflow, persona routing, marketing lifecycle, generic QA label, or another expression that cannot change runtime, controller, eval_hygiene, operator projection, or tests.

The current parallel landing lanes are:

1. `codex/mas-program-board-one-shot`
2. `codex/mas-work-unit-runtime-registry`
3. `codex/mas-medical-quality-os`
4. `codex/mas-learning-incident-loop`
5. `codex/mas-product-truth-projection`

## Operating Rule

Every later lane should either strengthen one of these program surfaces or explain why it is out of scope. Incidents such as no-live, stalled, wrong milestone claim, status drift, quality reopen, runtime recovery failure, or surface ownership drift must end as a guard, test, contract, runbook, runtime taxonomy, or strangler rule.
