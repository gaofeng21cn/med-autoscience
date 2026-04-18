# Docs Guide

**English** | [中文](./README.zh-CN.md)

This directory is the technical reading layer for `Med Auto Science`.
The repository home should stay readable for medical experts and potential users.
This guide is for readers who need the repo-tracked runtime, program, capability, and governance material behind that public entry.

## Start Here By Audience

| Audience | Start here | Why |
| --- | --- | --- |
| Potential users and medical experts | [Repository home](../README.md) | Understand what the system is for before reading technical internals |
| Technical readers and planners | [Project](./project.md), [Status](./status.md), [Architecture](./architecture.md), [Invariants](./invariants.md), [Decisions](./decisions.md) | Get the current truth, boundaries, and mainline direction quickly |
| Developers and maintainers | `docs/runtime/`, `docs/program/`, `docs/capabilities/`, `docs/references/`, `docs/policies/`, `docs/history/omx/` | Inspect implementation-facing material, operator guidance, and historical records |

## Current Baseline

- `OPL` is the top-level GUI and management shell for the family.
- `Med Auto Science` is the first-level medical domain module and agent under that shell.
- `Codex` is the default interaction and execution surface for MAS work through `CLI`, `MCP`, and controller commands.
- upstream `Hermes-Agent` is the external backup mode and long-running gateway for supervised runtime continuity.
- The default MAS loop is `product-frontdesk` -> `workspace-cockpit` -> `submit-study-task` -> `launch-study` -> `study-progress`.
- The medical display line stays separate as a downstream capability line.
- Internal program history still tracks `P0 runtime native truth`, `P1 workspace canonical literature / knowledge truth`, and `P2 controlled cutover -> physical monorepo migration`; the external runtime gate remains part of the blocker package for `P2`.

## Technical Working Set

Read these first before changing repo state:

- [Project](./project.md)
- [Status](./status.md)
- [Architecture](./architecture.md)
- [Invariants](./invariants.md)
- [Decisions](./decisions.md)

## Default Public Surface

- [Repository home](../README.md)

The repository home plus this guide are the default public entry surfaces.
Public-facing material should stay mirrored in English and Chinese.

## Repo-Tracked Technical Docs

### Runtime contracts and control surface

- [Agent runtime interface](runtime/agent_runtime_interface.md)
- [Agent entry modes](runtime/agent_entry_modes.md)
- [Runtime handle and durable surface contract](runtime/runtime_handle_and_durable_surface_contract.md)
- [Runtime backend interface contract](runtime/runtime_backend_interface_contract.md)
- [Runtime event and outer-loop input contract](runtime/runtime_event_and_outer_loop_input_contract.md)
- [Runtime event and outer-loop input implementation plan](runtime/runtime_event_and_outer_loop_input_implementation_plan.md)
- [Runtime boundary](runtime/runtime_boundary.md)
- [Runtime core convergence and controlled cutover](runtime/runtime_core_convergence_and_controlled_cutover.md)
- [Runtime core convergence and controlled cutover implementation plan](runtime/runtime_core_convergence_and_controlled_cutover_implementation_plan.md)
- [Runtime supervision loop](runtime/runtime_supervision_loop.md)
- [Study runtime control surface](runtime/study_runtime_control_surface.md)
- [Study runtime orchestration](runtime/study_runtime_orchestration.md)
- [Workspace knowledge and literature contract](runtime/workspace_knowledge_and_literature_contract.md)
- [Workspace knowledge and literature implementation plan](runtime/workspace_knowledge_and_literature_implementation_plan.md)

### Capability docs

- [Medical display platform mainline](capabilities/medical-display/medical_display_platform_mainline.md)
- [Medical display audit guide](capabilities/medical-display/medical_display_audit_guide.md)
- [Medical display template catalog](capabilities/medical-display/medical_display_template_catalog.md)
- [Medical display family roadmap](capabilities/medical-display/medical_display_family_roadmap.md)
- [Medical display visual audit protocol](capabilities/medical-display/medical_display_visual_audit_protocol.md)

### Program and gates

- [Research Foundry medical execution map](program/research_foundry_medical_execution_map.md)
- [Research Foundry medical mainline](program/research_foundry_medical_mainline.md)
- [Research Foundry medical phase ladder](program/research_foundry_medical_phase_ladder.md)
- [External runtime dependency gate](program/external_runtime_dependency_gate.md)
- [Merge and cutover gates](program/merge_and_cutover_gates.md)
- [Project repair priority map](program/project_repair_priority_map.md)
- [Hermes backend continuation board](program/hermes_backend_continuation_board.md)
- [Hermes backend activation package](program/hermes_backend_activation_package.md)
- [MedDeepScientist deconstruction map](program/med_deepscientist_deconstruction_map.md)
- [Manual runtime stabilization checklist](program/manual_runtime_stabilization_checklist.md)
- [Repository CI preflight](program/repository_ci_preflight.md)
- [Real study relaunch verification](program/real_study_relaunch_verification.md)
- [Study progress projection](program/study_progress_projection.md)

`P2 controlled cutover -> physical monorepo migration` remains open in internal program material, and the Hermes backend continuation / activation material is still part of the blocker package.

### MAS user loop and internal bridge references

- The public-facing MAS loop starts at `product-frontdesk`, continues through `workspace-cockpit`, then uses `submit-study-task`, `launch-study`, and `study-progress`.
- `operator entry` and `agent entry` remain internal reference terms for older runtime docs.
- The older phrase `lightweight medical direct entry` now maps to the internal bridge layer.
- `build-product-entry` remains the narrow machine-readable bridge for callers that need a structured envelope.
- [Lightweight product entry and OPL handoff](references/lightweight_product_entry_and_opl_handoff.md)

### References

- [Domain Harness OS positioning](references/domain-harness-os-positioning.md)
- [Research Foundry positioning](references/research_foundry_positioning.md)
- [Repo split between Research Foundry and Med Auto Science](references/repo_split_between_research_foundry_and_med_autoscience.md)
- [Workspace architecture](references/workspace_architecture.md)
- [Disease workspace quickstart](references/disease_workspace_quickstart.md)
- [Lightweight product entry and OPL handoff](references/lightweight_product_entry_and_opl_handoff.md)
- [Series doc governance checklist](references/series-doc-governance-checklist.md)

### Stable internal rules

- [Policies index](policies/README.md)
- [Platform operating model](policies/platform_operating_model.md)
- [Data asset management](policies/data_asset_management.md)
- [Research route bias policy](policies/research_route_bias_policy.md)
- [Publication gate policy](policies/publication_gate_policy.md)

### Repository history

- [OMX historical archive](history/omx/README.md)

## Documentation Rules

- Keep [Repository home](../README.md) understandable for clinicians and non-technical experts.
- Keep public-facing docs mirrored in English and Chinese.
- Keep runtime, program, capability, and policy material technical and repo-tracked without letting it take over the public home page.
- Keep historical material readable, but never present it as the active default workflow.

## Governance

- Documentation governance freezes in [series doc governance checklist](references/series-doc-governance-checklist.md), the technical working set, and the repo-tracked contract/doc surfaces rather than in `AGENTS.md` alone.
- `README*` and `docs/README*` are the default public entry.
- `docs/runtime/`, `docs/program/`, `docs/capabilities/`, and `docs/references/` are repo-tracked technical material.
- `docs/policies/` holds stable internal rules.
- `docs/history/omx/` is historical archive only.
