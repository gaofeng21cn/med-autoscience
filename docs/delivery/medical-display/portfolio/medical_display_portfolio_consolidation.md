# Medical Display Portfolio Consolidation

Status: `active capability governance`
Date: `2026-05-06`
Owner: `MedAutoScience`
Purpose: `Maintain medical-display family roadmap and portfolio support material.`
State: `active_support`
Machine boundary: Human-readable portfolio support only; current capability truth remains in registries, source, tests, generated artifacts, contracts, and audit receipts.

## Role

本文是 `docs/delivery/medical-display/` 的 portfolio map，用来区分当前执行面、合同面、历史 provenance、exemplar intake 和一次性 owner brief。

本子树入口是 [README.md](../README.md)。

## Lifecycle Map

| lifecycle role | active path | status |
| --- | --- | --- |
| active execution surface | `medical_display_active_board.md` | current owner-round board and reroute surface |
| current inventory / reference | `medical_display_audit_guide.md`, `medical_display_template_catalog.md`, `medical_display_arsenal.md` | strict audited inventory and human inventory reference |
| roadmap / backlog | `medical_display_family_roadmap.md`, `medical_display_template_backlog.md` | long-horizon direction and inactive candidate pool |
| platform / template-pack support | `medical_display_template_pack_architecture.md`, `medical_display_platform_mainline.md` | platform and template-pack execution model |
| implementation provenance | `../../../history/capabilities/medical-display/medical_display_template_pack_implementation_plan_2026_04.md` | historical Phase 1-2 execution packet; not active work queue |
| review discipline / route references | `medical_display_visual_audit_protocol.md`, `medical_figure_route_cookbook.md`, `domain_handler_figure_routes.md` | review and route references |
| anchor-paper provenance | `medical_display_anchor_paper_audit.md` | dated 001/003 closure snapshot; not active route board or current execution queue |
| history / provenance | `../../../history/capabilities/medical-display/` | historical records only |

## Active Tree Set

| role | files |
| --- | --- |
| active execution | `medical_display_active_board.md` |
| platform charter | `medical_display_platform_mainline.md` |
| current inventory / truth | `medical_display_audit_guide.md`, `medical_display_template_catalog.md`, `medical_display_arsenal.md` |
| long-horizon roadmap | `medical_display_family_roadmap.md` |
| visual review discipline | `medical_display_visual_audit_protocol.md` |
| candidate backlog | `medical_display_template_backlog.md` |
| template-pack architecture | `medical_display_template_pack_architecture.md` |
| route / cookbook references | `medical_figure_route_cookbook.md`, `domain_handler_figure_routes.md` |
| real-paper audit provenance | `medical_display_anchor_paper_audit.md` |

## Historical Records

Historical and provenance-only records live in `docs/history/capabilities/medical-display/`:

- `medical_display_arsenal_history.md`
- `medical_display_family_baseline_program.md`
- `medical_display_g_pathway_integrated_composite_owner_brief.md`
- `medical_display_template_pack_implementation_plan_2026_04.md`
- `paperplothub_exemplar_intake.md`
- `paperplothub_exemplar_exhaustion_ledger.md`

These files are readable context, not active owner boards.

## Governance Rules

1. New owner-round planning starts from `medical_display_active_board.md`.
2. Current template truth is `medical_display_audit_guide.md` plus `medical_display_template_catalog.md`.
3. Historical exemplar intake remains link-only provenance unless a real MAS paper demand reopens it through the active board.
4. Inactive backlog and historical exemplar records must not be reported as active blockers.
5. Tests and code must not use these narrative docs as machine truth. Machine truth belongs in schemas, registries, runtime surfaces, generated catalogs, and durable artifacts.
6. If a historical document is needed for human context, link to the `docs/history/capabilities/medical-display/` path rather than moving it back into the active capability directory.
