# MAS Domain Tool Affordances

Owner: `med-autoscience`
Purpose: `domain_tool_affordance_catalog`
State: `advisory_current_contract`
Machine boundary: This file declares available medical research tool affordances for MAS stage attempts. It is not a workflow script, executor sequence, quality verdict, publication verdict, owner receipt, typed blocker, or medical research truth source.

## Boundary

MAS stage attempts may use tools to read declared study material, literature refs, dataset refs, analysis workspaces, manuscript drafts, figure outputs, and body-free evidence refs. Tool use stays inside the permission, credential, write-scope, side-effect, and forbidden-authority boundaries declared by `contracts/pack_compiler_input.json`, `agent/stages/manifest.json`, the OPL-generated stage control plane, and MAS owner contracts.

## Affordances

- `medical_source_literature_and_dataset_context_reading`: Read declared sources, literature references, data dictionaries, cohort definitions, and source-readiness refs needed for grounded medical research work.
- `medical_analysis_manuscript_figure_and_review_workspace_operation`: Draft, analyze, revise, and render stage outputs only inside owner-authorized workspaces or artifact refs.
- `publication_quality_and_integrity_review_support`: Support MAS-owned publication quality, citation, calculation, figure-code, and source-integrity review without declaring final verdicts by tool output alone.
- `refs_only_receipt_and_stage_artifact_materialization`: Materialize manifests, lineage refs, pointer refs, receipt refs, and typed blocker refs without storing medical artifact bodies in OPL-owned runtime state.

## Forbidden Authority

- Tools do not declare study-ready, publication-ready, quality-ready, journal-ready, App release-ready, production-ready, or owner-accepted states.
- Tools do not write medical research truth, clinical truth, publication memory body, manuscript body, figure body, owner receipt body, or typed blocker body unless the MAS authority surface for that stage explicitly authorizes it.
- Tools do not prescribe executor order, candidate strategy, stage goal, or required parallelism.
