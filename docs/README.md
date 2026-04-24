# Docs Guide

**English** | [中文](./README.zh-CN.md)

This directory is the technical reading layer for `Med Auto Science`.
The repository home stays user-facing for clinicians, PIs, and medical teams.
This guide is for readers who need product boundary, operator entry surfaces, runtime contracts, and maintenance records.

## Start Here By Audience

| Audience | Start here | Why |
| --- | --- | --- |
| Potential users and medical experts | [Repository home](../README.md) | Understand what problems MAS helps solve before reading technical internals |
| Technical readers and planners | [Project](./project.md), [Status](./status.md), [Architecture](./architecture.md), [Invariants](./invariants.md), [Decisions](./decisions.md) | Get the current role, boundary, and operating model quickly |
| Developers and maintainers | `docs/runtime/`, `docs/program/`, `docs/capabilities/`, `docs/references/`, `docs/policies/`, [History Archive](./history/README.md) | Inspect implementation-facing material, governance records, and historical traces |

## What This Layer Covers

- The repository home explains what `Med Auto Science` is for, who it helps, and how to start.
- The core docs explain product boundary, current status, architecture, invariants, and decisions.
- `docs/runtime/`, `docs/program/`, `docs/capabilities/`, `docs/references/`, and `docs/policies/` hold implementation, maintenance, and historical or technical material.

## Current Reading Baseline

- `Med Auto Science` is a disease-focused medical research domain agent with a single MAS app skill and a manuscript-delivery workspace.
- The default user concern is study question, workspace context, progress narration, and file delivery.
- `CLI`, `MCP`, and `controller` are operator and automation entry surfaces.
- The stable callable surface is exposed through the single MAS app skill and includes the local CLI, workspace commands/scripts, durable surfaces, and repo-tracked contracts.
- `OPL` integration, the product-entry manifest, and other machine-readable bridge surfaces belong to the integration and reference layers.
- Hosted runtime carriers such as `Hermes-Agent` stay in explicit optional or reference-layer positions; they do not redefine the default MAS capability contract.
- Historical migration terms and older naming stay in reference or history layers.

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

### Program and Maintenance Records

- [Research Foundry medical execution map](program/research_foundry_medical_execution_map.md)
- [Research Foundry medical mainline](program/research_foundry_medical_mainline.md)
- [MAS single-project quality and autonomy mainline](program/mas_single_project_quality_and_autonomy_mainline.md)
- [MedDeepScientist deconstruction map](program/med_deepscientist_deconstruction_map.md)
- [External runtime dependency gate](program/external_runtime_dependency_gate.md)
- [Merge and cutover gates](program/merge_and_cutover_gates.md)
- [Project repair priority map](program/project_repair_priority_map.md)
- [Study progress projection](program/study_progress_projection.md)

### Integration References

- [Lightweight product entry and OPL handoff](references/lightweight_product_entry_and_opl_handoff.md)
- [Disease workspace quickstart](references/disease_workspace_quickstart.md)
- [Workspace architecture](references/workspace_architecture.md)

### References

- [Domain Harness OS positioning](references/domain-harness-os-positioning.md)
- [Research Foundry positioning](references/research_foundry_positioning.md)
- [Repo split between Research Foundry and Med Auto Science](references/repo_split_between_research_foundry_and_med_autoscience.md)
- [Series doc governance checklist](references/series-doc-governance-checklist.md)

### Stable internal rules

- [Policies index](policies/README.md)
- [Platform operating model](policies/platform_operating_model.md)
- [Data asset management](policies/data_asset_management.md)
- [Research route bias policy](policies/research_route_bias_policy.md)
- [Publication gate policy](policies/publication_gate_policy.md)

### Traceability Records

- [Program directory](program/)
- [References directory](references/)
- [History archive](history/README.md)

## Documentation Rules

- Keep [Repository home](../README.md) understandable for clinicians and non-technical experts.
- Keep public-facing docs mirrored in English and Chinese.
- Keep runtime, program, capability, and policy material technical and repo-tracked without letting it take over the public home page.
- Keep historical material readable while keeping the active user path focused on research workspaces, progress, and files.

## Governance

- Documentation governance freezes in [series doc governance checklist](references/series-doc-governance-checklist.md), the technical working set, and the repo-tracked contract/doc surfaces rather than in `AGENTS.md` alone.
- `README*` and `docs/README*` are the default public entry.
- `docs/runtime/`, `docs/program/`, `docs/capabilities/`, and `docs/references/` are repo-tracked technical material.
- `docs/policies/` holds stable internal rules.
- `docs/history/` is historical archive only.
