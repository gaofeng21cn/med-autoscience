# MAS/MDS Autonomy Operating System Program

Status: `active program board`  
Owner: `MedAutoScience`  
Scope: long-running autonomy, medical-paper quality, MAS single-project evolution, quality-preserving acceleration, natural-boundary maintainability

## Target State

`MedAutoScience` is the single medical-research product and quality-control plane. It owns research entry, study truth, quality contract, publication gate, progress projection, and submission authority. `MedDeepScientist` remains a controlled runtime backend, behavior oracle, and upstream intake buffer.

This program does not make physical monorepo absorb a current completion signal. Physical absorb, runtime core ingest, and broader cutover remain post-gate work after runtime protocol, parity proof, and MAS-owned contract surfaces are stable.

## Program Board

The repo-tracked program board is exposed by `med_autoscience.controllers.autonomy_operating_system_program`.

It fixes nine lanes:

1. `P0_baseline_freeze`
2. `P1_autonomy_reliability_core`
3. `P2_observability_and_profiling`
4. `P3_medical_quality_os`
5. `P4_quality_preserving_fast_lane`
6. `P5_mas_mds_strangler_program`
7. `P6_natural_boundary_refactor`
8. `P7_delivery_metrics_and_forecasting`
9. `P8_autonomy_incident_learning_loop`

The board is deliberately stricter than a prose roadmap: every lane has an owner, primary surfaces, and an acceptance gate. The program is not release-ready until every lane is completed or absorbed and none are blocked.

## Non-Negotiable Gates

- MAS remains the product owner.
- MDS remains runtime/backend/oracle/intake, not a second product owner.
- Quality-preserving acceleration keeps `gate_relaxation_allowed = false`.
- Long-running studies must expose state, blocker, owner, recovery route, and ETA evidence.
- New implementation must enter natural modules and avoid mechanical `chunk` / `part` splits.

## Operating Rule

Every later lane should either strengthen one of these program surfaces or explain why it is out of scope. Incidents such as no-live, stalled, wrong milestone claim, status drift, quality reopen, runtime recovery failure, or surface ownership drift must end as a guard, test, contract, runbook, runtime taxonomy, or strangler rule.
