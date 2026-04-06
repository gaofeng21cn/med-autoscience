# Docs

**English** | [中文](./README.zh-CN.md)

This file is the bilingual documentation index for `Med Auto Science`.

Public interpretation:

- Externally, `Med Auto Science` is the first mature medical implementation in the `Research Foundry` line.
- Operationally, it is the medical `Research Ops` gateway and domain harness OS.
- In federation terms, the current public chain is `One Person Lab -> Research Foundry -> Med Auto Science`.

## External Bilingual Surface

- [Repository Home](../README.md)

This bilingual index and the repository home are the default GitHub-facing public surface.
Any document promoted into that surface must ship with synchronized English `.md` and Chinese `.zh-CN.md` mirrors.

## Repo-Tracked Internal Operator Docs

These documents remain tracked in the repository, but they are internal operator references by default and currently stay Chinese-only unless explicitly promoted.

### For Medical Operators

- [Disease Workspace Quickstart](disease_workspace_quickstart.md) (Chinese only)
- [Medical Display Audit Guide](medical_display_audit_guide.md) (Chinese only)
- [Medical Display Template Catalog](medical_display_template_catalog.md) (Chinese only)

### For Technical Operators / AI Executors

- [Agent Runtime Interface](agent_runtime_interface.md) (Chinese only)
- [Agent Entry Modes](agent_entry_modes.md) (Chinese only)
- [Open Harness OS Architecture Boundary](open_harness_os_architecture.md) (Chinese only)
- [Outer-Loop Wakeup And Decision Loop](outer_loop_wakeup_and_decision_loop.md) (Chinese only)
- [Open Harness OS Freeze Plan](open_harness_os_freeze_plan.md) (Chinese only)
- [Mainline Integration And Cleanup Cadence](mainline_integration_and_cleanup.md) (Chinese only)
- [Research Foundry Medical Execution Map](research_foundry_medical_execution_map.md) (Chinese only)
- [Research Foundry Medical Mainline](research_foundry_medical_mainline.md) (Chinese only)
- [Research Foundry Positioning](research_foundry_positioning.md) (Chinese only)
- [Repo Split Between Research Foundry and Med Auto Science](repo_split_between_research_foundry_and_med_autoscience.md) (Chinese only)
- [Runtime Boundary](runtime_boundary.md) (Chinese only)
- [Workspace Architecture](workspace_architecture.md) (Chinese only)
- [Upstream Intake Guide](upstream_intake.md) (Chinese only)
- [Repository CI Preflight](repository_ci_preflight.md) (Chinese only)
- [Codex Plugin Integration](codex_plugin.md) (Chinese only)
- [Codex Plugin Release Guide](codex_plugin_release.md) (Chinese only)

## Stable Internal Rules

- [Policies Index](policies/README.md) (Chinese only)
- [Platform Operating Model](policies/platform_operating_model.md) (Chinese only)
- [Data Asset Management](policies/data_asset_management.md) (Chinese only)
- [Study Archetypes](policies/study_archetypes.md) (Chinese only)
- [Research Route Bias Policy](policies/research_route_bias_policy.md) (Chinese only)
- [Publication Gate Policy](policies/publication_gate_policy.md) (Chinese only)

## Documentation Boundary

- `README*` and `docs/README*`: the default external bilingual public surface
- `bootstrap/`, `controllers/`, and detailed `docs/*.md`: repo-tracked internal operator docs by default
- `docs/policies/`: repo-tracked internal stable rules by default
- `docs/superpowers/`: local AI / Superpowers plans, drafts, and process artifacts; keep untracked
