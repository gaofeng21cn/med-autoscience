# Docs

**English** | [中文](./README.zh-CN.md)

This bilingual index is the default public surface for `Med Auto Science`.
Public pages must ship with synchronized English and Chinese mirrors. Internal technical and planning material defaults to Chinese unless explicitly promoted.
Documentation governance rules are maintained in [`AGENTS.md`](../AGENTS.md).
The current entry truth is also explicit: `operator entry` and `agent entry` are real today, while a mature medical `product entry` still remains future work behind the runtime gate. A repo-tracked lightweight product-entry shell now exists for launch / task submission / progress visibility, but it is not yet the same thing as a mature direct user-facing product.

## Core Skeleton

These five pages are the stable knowledge backbone (Chinese only unless mirrored):

- [Project](project.md)
- [Architecture](architecture.md)
- [Invariants](invariants.md)
- [Decisions](decisions.md)
- [Status](status.md)

## External Bilingual Surface

- [Repository home](../README.md)

## Current Baseline, Long-Line Target, And Task Ladder

Current frozen state:

- `P0 runtime native truth`: completed upstream in `med-deepscientist main@cb73b3d21c404d424e57d7765b5a9a409060700a`
- `P1 workspace canonical literature / knowledge truth`: completed in this repo
- `P2 controlled cutover -> physical monorepo migration`: still active

- Current repo-verified baseline: `MedAutoScience` is the sole research entry while `MedDeepScientist` remains the controlled research backend; upstream `Hermes-Agent` is still a target runtime substrate, not a landed fact.
- Long-line target: upstream `Hermes-Agent` owns the outer runtime substrate, while `MedDeepScientist` is reduced toward a research backend and gradually sheds reusable runtime capabilities.
- Product-entry target: add a lightweight medical direct entry that can be reached directly or through `OPL` handoff without rewriting the current research authority boundary.
- Repo-level status entry: `uv run python -m med_autoscience.cli mainline-status`
- Repo-level phase entry: `uv run python -m med_autoscience.cli mainline-phase --phase <current|next|phase_id>`
- Current user inbox entry: `uv run python -m med_autoscience.cli workspace-cockpit --profile <profile>` now folds repo mainline snapshot, workspace attention queue, and the practical start / submit-task / watch-progress loop into one surface.
- Fastest cutover board: [Upstream Hermes-Agent fast cutover board](program/upstream_hermes_agent_fast_cutover_board.md) (Chinese only)
- Independent side line: `medical display / paper-figure assetization` stays isolated from the runtime mainline.
- `external_runtime_dependency_gate.md` remains part of the blocker package, but it is no longer the whole-project stop state.

## Runtime Contracts And Control Surface

- [Agent runtime interface](runtime/agent_runtime_interface.md)
- [Agent entry modes](runtime/agent_entry_modes.md)
- [Runtime handle and durable surface contract](runtime/runtime_handle_and_durable_surface_contract.md)
- [Runtime backend interface contract](runtime/runtime_backend_interface_contract.md)
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
- [Research Foundry medical phase ladder](program/research_foundry_medical_phase_ladder.md)
- [Integration harness activation package](program/integration_harness_activation_package.md)
- [Hermes backend continuation board](program/hermes_backend_continuation_board.md)
- [Hermes backend activation package](program/hermes_backend_activation_package.md)
- [MedDeepScientist deconstruction map](program/med_deepscientist_deconstruction_map.md)
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
- [Lightweight product entry and OPL handoff](references/lightweight_product_entry_and_opl_handoff.md) (Chinese only)

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
- `docs/superpowers/`: existing repo-tracked historical design material may remain as internal archive, but new local AI / Superpowers drafts should stay untracked by default.
