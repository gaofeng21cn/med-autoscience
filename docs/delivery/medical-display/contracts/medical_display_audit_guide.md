# Medical Display Audit Guide

Owner: `MedAutoScience`
Purpose: `current_medical_display_audit_boundary`
State: `active_support`
Machine boundary: Human-readable delivery contract support only. Enforceable truth remains in source, template descriptors, machine-readable contracts, generated artifacts, layout sidecars, tests, audit receipts, and owner receipts.

This guide defines the current deterministic lower-bound audit surface for MAS medical display work. It is narrower than the long-term roadmap and narrower than final publication judgment.

## What Counts As Current

A display counts as current implemented inventory only when it is present in the active pack descriptors and can be reached through the current registry/schema/materialization/QC path.

Current `fenggaolab.org.medical-display-core` inventory is generated, not hand-maintained:

- current counts and human visual Gallery: ScholarSkills compact review package at `/Users/gaofeng/workspace/mas-scholar-skills/gallery/medical-display/`;
- full descriptor inventory: `/Users/gaofeng/workspace/mas-scholar-skills/packs/medical-display-core/canonical_template_catalog.json`;
- compact capability index: [medical_display_arsenal.md](../catalogs/medical_display_arsenal.md).

Python evidence templates are absent from current inventory, hidden defaults, explicit-request inventory, Gallery comparison cards, and runtime fallback templates unless a future current audited template proves advantage over R/ggplot2.

## Source Of Truth

- `/Users/gaofeng/workspace/mas-scholar-skills/packs/medical-display-core/templates/*/template.toml`
- `/Users/gaofeng/workspace/mas-scholar-skills/packs/medical-display-core/canonical_template_catalog.json`
- `/Users/gaofeng/workspace/mas-scholar-skills/packs/medical-display-core/renderer_migration_ledger.json`
- `src/med_autoscience/display_registry.py`
- `src/med_autoscience/display_schema_contract.py`
- `src/med_autoscience/controllers/display_surface_materialization/`
- `src/med_autoscience/display_layout_qc/`
- ScholarSkills gallery manifest / snapshot under `/Users/gaofeng/workspace/mas-scholar-skills/gallery/medical-display/`

The Markdown catalog is an on-demand local snapshot produced by `./scripts/run-python-clean.sh scripts/build-display-pack-gallery.py --publish-docs`; it is not tracked inventory truth. The human Gallery is the ScholarSkills compact review package; it includes page-level recipes, visible design/flow shells, and R/ggplot2 evidence figure starters.

## Code, Assets, And Dependency Boundary

Medical display maintenance uses three separate surfaces:

- `/Users/gaofeng/workspace/mas-scholar-skills/packs/medical-display-core/` is the versioned template pack. It contains descriptors, renderer source, shared R helpers, and dependency requirement declarations.
- `/Users/gaofeng/workspace/mas-scholar-skills/gallery/medical-display/` is the compact human review package. MAS no longer commits gallery build output or single-figure gallery assets under `docs/delivery/medical-display/examples/`.
- OPL Runtime Environment Substrate owns dependency preparation. MAS consumes dependency run-context refs and fails closed when a required prepared receipt, profile, binary, or managed R library is missing.

`--package-only` is valid for document packaging, title/index changes, and PDF regeneration from existing assets. It is not evidence that renderer source, dependency environment, or real paper payloads were freshly rendered. Fresh rendering evidence requires render cache readback, layout sidecars, dependency run-context readback, and artifact inspection.

## Renderer Policy

| Surface | Renderer policy | Authority boundary |
| --- | --- | --- |
| Evidence figures | R/ggplot2 first; current pack has no Python evidence | May display data/statistical evidence only from structured payloads and renderer/QC contracts |
| Illustration shells | Python/SVG/composition allowed | May express workflow, cohort flow, graphical abstract, or design context; cannot carry statistical evidence authority |
| Table shells | Structured table renderer | May materialize tabular display artifacts; cannot sign publication readiness |

Future Python evidence may re-enter only after documented advantage over the R/ggplot2 baseline, checked-in current descriptors, layout/QC/audit evidence, and explicit user-visible current-pack status.

## Current Audit Families

Current audit-family membership is no longer maintained as a duplicate table in this guide. Use the ScholarSkills compact gallery review package for the user-facing current surface, and the generated template catalog for full descriptor inventory. This avoids treating input-schema variants or retired aliases as separate current templates.

## Visual QA Boundary

Renderer contracts, schema contracts, layout QC and Gallery generation prove only a minimum quality floor. A final manuscript figure still needs:

1. real paper payload and data refs;
2. render artifacts plus layout sidecar;
3. visual audit on the actual image;
4. concrete renderer/QC/style hardening when defects are found;
5. MAS owner / publication gate receipt for any readiness claim.

Green tests, Gallery generation, style-profile hash, visual-audit clear, display lock, or OPL smoke receipt cannot authorize publication readiness by themselves.

## External Exemplar Intake

External galleries, blogs, packages, and paper examples are read-only learning sources. They can justify a template gap, style rule, or audit check. They do not become current MAS display capabilities until the change lands through descriptor, schema, renderer, QC, catalog, Gallery/readback, and tests.
