---
name: experiment
description: Use when a study line needs a primary managed run under a locked protocol and baseline.
---

# Experiment

Use this skill to run a primary managed experiment under a locked protocol and decide whether the result supports the current study question.

## Core renderer hook

The core lane renderer injects the generated stage skill surface here.

{{MED_AUTOSCIENCE_STAGE_SKILL_SURFACE}}

## Stage card and route contract

- Stage card ref: `docs/runtime/contracts/stage_surfaces.md#experiment`
- Route contract ref: `src/med_autoscience/agent_entry/resources/agent_entry_modes.yaml#/route_contracts/experiment`
- Key question: Does the primary result answer the current study question?
- Goal: Run a primary managed experiment when the study line needs fresh main-result execution.
- Runtime contract token: `{{MED_AUTOSCIENCE_MEDICAL_RUNTIME_CONTRACT}}`
- Route bias token: `{{MED_AUTOSCIENCE_ROUTE_BIAS}}`
- Study archetypes token: `{{MED_AUTOSCIENCE_STUDY_ARCHETYPES}}`
- Next routes: `analysis-campaign`, `write`, `decision`

## Knowledge obligations

- `stage_knowledge_packet_ref`
- `approved_experiment_protocol`
- `data_contract_and_cohort_lock`
- `endpoint_and_comparator_lock`
- `statistical_analysis_plan`
- `startup_run_context`
- `prior_result_lineage`
- `failed_comparator_history`
- Machine source refs: `src/med_autoscience/stage_knowledge_contract.py`, `docs/runtime/contracts/stage_surfaces.md#experiment`

## Quality pack refs

- `statistical_analysis_pack`
- `stop_loss_pack`
- `human_gate_pack`
- Machine source refs: `src/med_autoscience/stage_quality_contract.py`, `docs/runtime/contracts/stage_surfaces.md#experiment`

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
- Launch experiments when the startup boundary blocks compute-stage work
- Queue training or expand the locked claim boundary without a locked protocol
- Introduce Research Harness runtime, database, dashboard, MCP, auto-runner, or verdict authority
- Run legacy `refs/` or historical code unless the startup contract explicitly allows it

## Closeout packet

- `stage_memory_closeout_packet`
- `primary_result_with_run_context`
- `result_lineage_update`
- `endpoint_or_comparator_deviation`
- `negative_or_failed_comparator_lesson`

## Route back and human gate

- Route back: run outcome invalidates the current study line, result quality or reproducibility gaps block downstream review, or the controller boundary changes before interpretation stabilizes
- Human gate: the primary experiment target changes the locked study boundary or main claim family, or result interpretation would authorize a new externally visible claim

## OPL Boundary

- OPL may project, dispatch, and read refs.
- OPL must not write MAS truth, authorize quality verdicts, own canonical artifacts, or accept memory writeback.

## Clean-room boundary

- Treat source, gap, numeric trace, and claim-evidence material as MAS-owned inputs or gates only.
- no RH dependency: do not import Research Harness runtime, database, dashboard, MCP, runner, or verdict authority.

