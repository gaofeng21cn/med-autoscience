# Docs

**English** | [中文](./README.zh-CN.md)

This bilingual index is the default public surface for `Med Auto Science`.
It stays aligned with the project truth that the repository is the medical `Research Ops` `Domain Harness OS` on the shared `Unified Harness Engineering Substrate`, with a `Codex-default host-agent runtime` as the current local execution shape. Its formal-entry matrix is `CLI` as default formal entry, `MCP` as supported protocol layer, and `controller` as internal control surface. The current repository mainline is `Auto-only`.

## Unified Documentation Governance

- External documents must ship as paired English `.md` and Chinese `.zh-CN.md` files that stay synchronized.
- Internal design, technical, planning, and memo documents default to Chinese unless a page is explicitly promoted into the bilingual surface.
- Terminology may stay in English when it is part of stable domain language, but avoid unnecessary mixed-language prose.
- `docs/README*` should consistently show which pages are public bilingual entry points and which remain internal holdings.
- For more detail, see [Documentation Governance](documentation-governance.md) (Chinese only).

## External Bilingual Surface

- [Repository home](../README.md)

This index together with the repository home defines the default GitHub-facing bilingual surface.
Any page that the public should read must live under this surface with fully mirrored English and Chinese variants.

## Repo-Tracked Internal Operator Docs

### Medical operators

- [Disease workspace quickstart](disease_workspace_quickstart.md)
- [Medical display audit guide](medical_display_audit_guide.md)
- [Medical display template catalog](medical_display_template_catalog.md)

### Technical operators / agent executors

- [Domain Harness OS Positioning On Unified Substrate](domain-harness-os-positioning.md)
- [Agent runtime interface](agent_runtime_interface.md)
- [Agent entry modes](agent_entry_modes.md)
- [Open Harness OS Architecture Boundary](open_harness_os_architecture.md)
- [Outer-Loop Wakeup And Decision Loop](outer_loop_wakeup_and_decision_loop.md)
- [Open Harness OS Freeze Plan](open_harness_os_freeze_plan.md)
- [Mainline Integration And Cleanup Cadence](mainline_integration_and_cleanup.md)
- [Research Foundry Medical Execution Map](research_foundry_medical_execution_map.md)
- [Research Foundry Medical Mainline](research_foundry_medical_mainline.md)
- [Research Foundry Positioning](research_foundry_positioning.md)
- [Repository Split Between Research Foundry And Med Auto Science](repo_split_between_research_foundry_and_med_autoscience.md)
- [Runtime Boundary](runtime_boundary.md)
- [Workspace Architecture](workspace_architecture.md)
- [Upstream Intake Guide](upstream_intake.md)
- [Repository CI Preflight](repository_ci_preflight.md)
- [Codex Plugin Integration](codex_plugin.md)
- [Codex Plugin Release Guide](codex_plugin_release.md)
- [Documentation Governance](documentation-governance.md) (Chinese only)

## Stable Internal Rules

- [Policies index](policies/README.md)
- [Platform operating model](policies/platform_operating_model.md)
- [Data asset management](policies/data_asset_management.md)
- [Study archetypes](policies/study_archetypes.md)
- [Research route bias policy](policies/research_route_bias_policy.md)
- [Publication gate policy](policies/publication_gate_policy.md)

## Documentation Boundary

- `README*` and `docs/README*`: default bilingual public surface.
- `bootstrap/`, `controllers/`, and detailed `docs/*.md`: internal operator references, Chinese by default unless explicitly promoted.
- `docs/policies/`: stable internal rules, Chinese by default.
- `docs/superpowers/`: local AI / Superpowers plans, drafts, and process artifacts; keep them untracked.
