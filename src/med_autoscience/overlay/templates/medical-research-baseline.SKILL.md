---
name: baseline
description: Use when a study line needs a reproducible comparator baseline before experiment, write, or stop decisions.
---

# Baseline

Use this skill to lock a reproducible comparator surface for the active study line and decide whether the line should continue, reroute, or stop.

## Core renderer hook

The core lane renderer injects the generated stage skill surface here.

{{MED_AUTOSCIENCE_STAGE_SKILL_SURFACE}}

## Stage card and route contract

- Stage card ref: `docs/runtime/contracts/stage_surfaces.md#baseline`
- Route contract ref: `src/med_autoscience/agent_entry/resources/agent_entry_modes.yaml#/route_contracts/baseline`
- Key question: Does the current claim have reproducible baseline support?
- Goal: Establish the baseline, comparator, and readiness proof for the active study line.
- Route bias token: `{{MED_AUTOSCIENCE_ROUTE_BIAS}}`
- Study archetypes token: `{{MED_AUTOSCIENCE_STUDY_ARCHETYPES}}`
- Next routes: `analysis-campaign`, `write`, `decision`

## Knowledge obligations

- `stage_knowledge_packet_ref`
- `data_source_contract`
- `cohort_definition_and_inclusion_exclusion`
- `endpoint_definition_and_measurement_window`
- `comparator_definition_and_reference_baseline`
- `startup_run_context`
- `prior_result_lineage`
- `failed_comparator_history`
- Machine source refs: `src/med_autoscience/stage_knowledge_contract.py`, `docs/runtime/contracts/stage_surfaces.md#baseline`

## Quality pack refs

- `statistical_analysis_pack`
- `stop_loss_pack`
- `human_gate_pack`
- Machine source refs: `src/med_autoscience/stage_quality_contract.py`, `docs/runtime/contracts/stage_surfaces.md#baseline`

## Allowed MAS owner tools

- Controller-authorized CLI/MCP/product-entry/runtime surfaces
- `stage-knowledge-packet`
- `stage-memory-closeout-route`
- `runtime-supervisor-reconcile`
- `ai-reviewer-publication-eval`
- `publication-gate`

## Forbidden actions

- Write MAS domain truth
- Authorize quality verdicts
- Own canonical artifacts
- Accept memory writeback
- Introduce Research Harness runtime, database, dashboard, MCP, auto-runner, or verdict authority
- Widen the locked claim boundary without a controller-approved route change
- Run legacy `refs/` or historical code unless the startup contract explicitly allows it

## Closeout packet

- `stage_memory_closeout_packet`
- `baseline_cohort_endpoint_comparator_snapshot`
- `baseline_effect_size_or_feasibility_readout`
- `failed_comparator_lesson`
- `continue_reroute_or_stop_recommendation`

## Route back and human gate

- Route back: baseline result cannot support the active claim, comparator or cohort definition changes materially, or reviewer-first scan finds missing baseline proof
- Human gate: comparator, cohort, or endpoint redefinition changes the active claim boundary, or the baseline readout points to a stop decision or direction reset

## OPL boundary

- OPL may project, dispatch, and read refs.
- OPL must not write MAS truth, authorize quality verdicts, own canonical artifacts, or accept memory writeback.

## Clean-room boundary

- Treat source, gap, numeric trace, and claim-evidence material as MAS-owned inputs or gates only.
- Do not import Research Harness runtime, database, dashboard, MCP, runner, or verdict authority.

