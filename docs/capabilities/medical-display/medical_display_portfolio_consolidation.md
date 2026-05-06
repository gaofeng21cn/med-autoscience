# Medical Display Portfolio Consolidation

Status: `active capability governance`
Date: `2026-05-06`
Owner: `MedAutoScience`

## Role

This document is the portfolio map for `docs/capabilities/medical-display/`.
It separates current execution and contract surfaces from historical provenance,
exemplar intake, and one-off owner briefs.

## Active Set

| role | files |
| --- | --- |
| active execution | `medical_display_active_board.md` |
| platform charter | `medical_display_platform_mainline.md` |
| current inventory / truth | `medical_display_audit_guide.md`, `medical_display_template_catalog.md`, `medical_display_arsenal.md` |
| long-horizon roadmap | `medical_display_family_roadmap.md` |
| visual review discipline | `medical_display_visual_audit_protocol.md` |
| candidate backlog | `medical_display_template_backlog.md` |
| template-pack architecture | `medical_display_template_pack_architecture.md`, `medical_display_template_pack_implementation_plan.md` |
| route / cookbook references | `medical_figure_route_cookbook.md`, `sidecar_figure_routes.md` |
| real-paper audit reference | `medical_display_anchor_paper_audit.md` |

## Historical Records

Historical and provenance-only records live in `docs/history/capabilities/medical-display/`:

- `medical_display_arsenal_history.md`
- `medical_display_family_baseline_program.md`
- `medical_display_g_pathway_integrated_composite_owner_brief.md`
- `paperplothub_exemplar_intake.md`
- `paperplothub_exemplar_exhaustion_ledger.md`

These files are readable context, not active owner boards.

## Governance Rules

1. New owner-round planning starts from `medical_display_active_board.md`.
2. Current template truth is `medical_display_audit_guide.md` plus `medical_display_template_catalog.md`.
3. Historical exemplar intake remains link-only provenance unless a real MAS paper demand reopens it through the active board.
4. Tests and code must not use these narrative docs as machine truth. Machine truth belongs in schemas, registries, runtime surfaces, generated catalogs, and durable artifacts.
5. If a historical document is needed for human context, link to the `docs/history/capabilities/medical-display/` path rather than moving it back into the active capability directory.
