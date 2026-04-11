# Docs

**English** | [中文](./README.zh-CN.md)

This bilingual index is the default public surface for `Med Auto Science`.
Public pages must ship with synchronized English and Chinese mirrors. Internal technical and planning material defaults to Chinese unless explicitly promoted.
Documentation governance rules are maintained in [`AGENTS.md`](../AGENTS.md).

## Core Skeleton

These five pages are the stable knowledge backbone (Chinese only unless mirrored):

- [Project](project.md)
- [Architecture](architecture.md)
- [Invariants](invariants.md)
- [Decisions](decisions.md)
- [Status](status.md)

## External Bilingual Surface

- [Repository home](../README.md)

## Current Mainline And Blocker Package

The current repo-tracked runtime mainline is already absorbed.
The honest repo-side stop is `EXTERNAL_RUNTIME_DEPENDENCY_BLOCKED_AFTER_ABSORB`, not an open in-repo implementation baton.

## Runtime Contracts And Control Surface

- [Agent runtime interface](runtime/agent_runtime_interface.md)
- [Agent entry modes](runtime/agent_entry_modes.md)
- [Runtime handle and durable surface contract](runtime/runtime_handle_and_durable_surface_contract.md)
- [Runtime event and outer-loop input contract](runtime/runtime_event_and_outer_loop_input_contract.md)
- [Runtime event and outer-loop input implementation plan](runtime/runtime_event_and_outer_loop_input_implementation_plan.md)
- [Runtime core convergence and controlled cutover](runtime/runtime_core_convergence_and_controlled_cutover.md)
- [Runtime core convergence and controlled cutover implementation plan](runtime/runtime_core_convergence_and_controlled_cutover_implementation_plan.md)
- [Workspace knowledge and literature contract](runtime/workspace_knowledge_and_literature_contract.md)
- [Workspace knowledge and literature implementation plan](runtime/workspace_knowledge_and_literature_implementation_plan.md)
- [Runtime supervision loop](runtime/runtime_supervision_loop.md)
- [Study runtime control surface](runtime/study_runtime_control_surface.md)
- [Study runtime orchestration](runtime/study_runtime_orchestration.md)
- [Outer-loop wakeup and decision loop](runtime/outer_loop_wakeup_and_decision_loop.md)
- [Delivery plane contract map](runtime/delivery_plane_contract_map.md)
- [Runtime boundary](runtime/runtime_boundary.md)

## Capabilities

### Medical display

- [Medical display platform mainline](capabilities/medical-display/medical_display_platform_mainline.md)
- [Medical display audit guide](capabilities/medical-display/medical_display_audit_guide.md)
- [Medical display template catalog](capabilities/medical-display/medical_display_template_catalog.md)
- [Medical display family roadmap](capabilities/medical-display/medical_display_family_roadmap.md)
- [Medical display visual audit protocol](capabilities/medical-display/medical_display_visual_audit_protocol.md)
- [Sidecar figure routes](capabilities/medical-display/sidecar_figure_routes.md)

## Program And Gates

- [Research Foundry medical execution map](program/research_foundry_medical_execution_map.md)
- [Research Foundry medical mainline](program/research_foundry_medical_mainline.md)
- [Integration harness activation package](program/integration_harness_activation_package.md)
- [External runtime dependency gate](program/external_runtime_dependency_gate.md)
- [Merge and cutover gates](program/merge_and_cutover_gates.md)
- [Open Harness OS freeze plan](program/open_harness_os_freeze_plan.md)
- [Mainline integration and cleanup cadence](program/mainline_integration_and_cleanup.md)
- [Upstream intake guide](program/upstream_intake.md)
- [Repository CI preflight](program/repository_ci_preflight.md)
- [Real study relaunch verification](program/real_study_relaunch_verification.md)
- [Project repair priority map](program/project_repair_priority_map.md)
- [Study progress projection](program/study_progress_projection.md)
- [Manual runtime stabilization checklist](program/manual_runtime_stabilization_checklist.md) (Chinese only)

## References

- [Domain Harness OS positioning](references/domain-harness-os-positioning.md)
- [Domain gateway and harness OS overview](references/domain_gateway_harness_os.md)
- [Research Foundry positioning](references/research_foundry_positioning.md)
- [Repo split between Research Foundry and Med Auto Science](references/repo_split_between_research_foundry_and_med_autoscience.md)
- [Open Harness OS architecture boundary](references/open_harness_os_architecture.md)
- [Workspace architecture](references/workspace_architecture.md)
- [Disease workspace quickstart](references/disease_workspace_quickstart.md)
- [Codex plugin integration](references/codex_plugin.md)
- [Codex plugin release guide](references/codex_plugin_release.md)

## Stable Internal Rules

- [Policies index](policies/README.md)
- [Platform operating model](policies/platform_operating_model.md)
- [Data asset management](policies/data_asset_management.md)
- [Study archetypes](policies/study_archetypes.md)
- [Research route bias policy](policies/research_route_bias_policy.md)
- [Publication gate policy](policies/publication_gate_policy.md)

## History

- [OMX historical archive](history/omx/README.md) (historical reference only; not an active workflow entry)

## Documentation Boundary

- `README*` and `docs/README*`: default bilingual public surface.
- `docs/capabilities/`, `docs/program/`, `docs/runtime/`, `docs/references/`: repo-tracked operator docs, Chinese by default unless promoted.
- `docs/policies/`: stable internal rules, Chinese by default.
- `docs/history/omx/`: OMX historical archive entry only; never an active workflow surface.
- `docs/superpowers/`: local AI / Superpowers plans, drafts, and process artifacts; keep them untracked.
