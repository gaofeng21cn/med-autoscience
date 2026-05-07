# Medical Display Capability

**English** | [中文](./README.zh-CN.md)

This directory is the active entry point for the medical display capability family.
It indexes the current lifecycle surfaces without moving historical records back into the active tree.

## Lifecycle Map

| lifecycle role | start here | meaning |
| --- | --- | --- |
| Active execution surface | [medical_display_active_board.md](./medical_display_active_board.md) | Current owner-round state, phase, next baton, and opening rules for the next display round. |
| Current inventory / reference | [medical_display_audit_guide.md](./medical_display_audit_guide.md), [medical_display_template_catalog.md](./medical_display_template_catalog.md), [medical_display_arsenal.md](./medical_display_arsenal.md) | Current strict audited inventory, generated template matrix, and human-readable capability inventory. |
| Roadmap / backlog | [medical_display_family_roadmap.md](./medical_display_family_roadmap.md), [medical_display_template_backlog.md](./medical_display_template_backlog.md) | Long-horizon paper-family direction and inactive or candidate expansion pool. These files are not active blockers by themselves. |
| Implementation plan | [medical_display_template_pack_architecture.md](./medical_display_template_pack_architecture.md), [medical_display_template_pack_implementation_plan.md](./medical_display_template_pack_implementation_plan.md), [medical_display_platform_mainline.md](./medical_display_platform_mainline.md) | Template-pack architecture, implementation program, and platform operating model. |
| Review discipline and route references | [medical_display_visual_audit_protocol.md](./medical_display_visual_audit_protocol.md), [medical_figure_route_cookbook.md](./medical_figure_route_cookbook.md), [sidecar_figure_routes.md](./sidecar_figure_routes.md), [medical_display_anchor_paper_audit.md](./medical_display_anchor_paper_audit.md) | Visual audit protocol, route/cookbook references, and real-paper audit reference. |
| Historical provenance | [history archive](../../history/capabilities/medical-display/README.md) | Retired owner briefs, baseline-completion provenance, exemplar intake, and expansion history. |

## Operating Rules

Use [medical_display_active_board.md](./medical_display_active_board.md) for the current execution state.

Use the audit guide, template catalog, and arsenal for current inventory. Use the template backlog as the inactive candidate pool, not as the execution board. Use visual audit and route references to review display quality or choose a figure route; they do not reopen backlog items by themselves.

Active board, catalog, backlog, audit, and history have separate jobs:

- The active board owns the next executable display round.
- The catalog and arsenal describe what is currently available.
- The backlog holds candidates until a real paper demand admits them.
- The audit protocol and audit guide define review discipline and inventory checks.
- History preserves retired briefs, exemplar intake, and exhausted exploration records.

Historical exemplars, retired owner briefs, and exhausted intake ledgers are provenance only unless a real MAS paper demand reopens them through the active board.

Use [medical_display_portfolio_consolidation.md](./medical_display_portfolio_consolidation.md) when you need the compact portfolio map for this subtree.

This capability subtree keeps MAS domain ownership. OPL family lifecycle governance helps organize the docs, but MAS decides display capability truth through MAS papers, templates, audits, generated catalogs, and durable runtime / artifact surfaces.
