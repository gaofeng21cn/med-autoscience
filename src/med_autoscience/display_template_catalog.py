from __future__ import annotations

from collections.abc import Mapping

from med_autoscience import display_registry, display_schema_contract


def _template_metadata_by_id() -> dict[str, dict[str, str]]:
    metadata: dict[str, dict[str, str]] = {}
    for spec in display_registry.list_evidence_figure_specs():
        metadata[spec.template_id] = {
            "display_name": spec.display_name,
            "renderer_family": spec.renderer_family,
            "input_schema_id": spec.input_schema_id,
            "qc_profile": spec.layout_qc_profile,
            "required_exports": ", ".join(f"`{item}`" for item in spec.required_exports),
            "display_kind": "evidence_figure",
        }
    for spec in display_registry.list_illustration_shell_specs():
        metadata[spec.shell_id] = {
            "display_name": spec.display_name,
            "renderer_family": spec.renderer_family,
            "input_schema_id": spec.input_schema_id,
            "qc_profile": spec.shell_qc_profile,
            "required_exports": ", ".join(f"`{item}`" for item in spec.required_exports),
            "display_kind": "illustration_shell",
        }
    for spec in display_registry.list_table_shell_specs():
        metadata[spec.shell_id] = {
            "display_name": spec.display_name,
            "renderer_family": "n/a",
            "input_schema_id": spec.input_schema_id,
            "qc_profile": spec.table_qc_profile,
            "required_exports": ", ".join(f"`{item}`" for item in spec.required_exports),
            "display_kind": "table_shell",
        }
    return metadata


def _format_field_tuple(fields: tuple[str, ...]) -> str:
    if not fields:
        return "None"
    return ", ".join(f"`{field}`" for field in fields)


def _format_field_mapping(mapping: Mapping[str, tuple[str, ...]]) -> str:
    if not mapping:
        return "None"
    return "<br>".join(f"`{key}` -> {_format_field_tuple(value)}" for key, value in mapping.items())


def _ordered_unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _evidence_display_classes() -> list[display_schema_contract.DisplaySchemaClass]:
    return [
        display_class
        for display_class in display_schema_contract.list_display_schema_classes()
        if display_class.class_id != "publication_shells_and_tables"
    ]


def _render_template_class_section() -> list[str]:
    metadata_by_id = _template_metadata_by_id()
    lines = ["## Template Classes", ""]
    for display_class in display_schema_contract.list_display_schema_classes():
        lines.extend(
            [
                f"### {display_class.display_name}",
                "",
                "| Template ID | Kind | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for template_id in display_class.template_ids:
            metadata = metadata_by_id[template_id]
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{template_id}`",
                        f"`{metadata['display_kind']}`",
                        metadata["display_name"],
                        f"`{metadata['renderer_family']}`",
                        f"`{metadata['input_schema_id']}`",
                        f"`{metadata['qc_profile']}`",
                        metadata["required_exports"],
                    ]
                )
                + " |"
            )
        lines.append("")
    return lines


def _render_input_schema_section() -> list[str]:
    lines = ["## Input Schemas", ""]
    for contract in display_schema_contract.list_input_schema_contracts():
        lines.extend(
            [
                f"### `{contract.input_schema_id}`",
                "",
                f"- Display kind: `{contract.display_kind}`",
                f"- Display name: {contract.display_name}",
                f"- Templates: {_format_field_tuple(contract.template_ids)}",
                f"- Required top-level fields: {_format_field_tuple(contract.required_top_level_fields)}",
                f"- Optional top-level fields: {_format_field_tuple(contract.optional_top_level_fields)}",
                f"- Required display fields: {_format_field_tuple(contract.display_required_fields)}",
                f"- Optional display fields: {_format_field_tuple(contract.display_optional_fields)}",
                f"- Required collection fields: {_format_field_mapping(contract.collection_required_fields)}",
                f"- Optional collection fields: {_format_field_mapping(contract.collection_optional_fields)}",
                f"- Required nested collection fields: {_format_field_mapping(contract.nested_collection_required_fields)}",
                f"- Optional nested collection fields: {_format_field_mapping(contract.nested_collection_optional_fields)}",
                f"- Additional constraints: {_format_field_tuple(contract.additional_constraints)}",
                "",
            ]
        )
    return lines


def _render_audit_class_map_section() -> list[str]:
    metadata_by_id = _template_metadata_by_id()
    lines = [
        "## Evidence Class Map",
        "",
        "| Class | Implemented Templates | Input Schemas | Primary QC Profiles |",
        "| --- | ---: | --- | --- |",
    ]
    for display_class in _evidence_display_classes():
        qc_profiles = _ordered_unique([metadata_by_id[template_id]["qc_profile"] for template_id in display_class.template_ids])
        lines.append(
            "| "
            + " | ".join(
                [
                    display_class.display_name,
                    str(len(display_class.template_ids)),
                    _format_field_tuple(display_class.input_schema_ids),
                    _format_field_tuple(tuple(qc_profiles)),
                ]
            )
            + " |"
        )
    lines.append("")
    return lines


def _render_audit_class_detail_section() -> list[str]:
    metadata_by_id = _template_metadata_by_id()
    lines = ["## Evidence Class Detail", ""]
    for display_class in _evidence_display_classes():
        renderer_families = _ordered_unique(
            [metadata_by_id[template_id]["renderer_family"] for template_id in display_class.template_ids]
        )
        qc_profiles = _ordered_unique([metadata_by_id[template_id]["qc_profile"] for template_id in display_class.template_ids])
        lines.extend(
            [
                f"### {display_class.display_name}",
                "",
                "Templates:",
                *[f"- `{template_id}`" for template_id in display_class.template_ids],
                "",
                "Authoritative contract:",
                f"- Input schemas: {_format_field_tuple(display_class.input_schema_ids)}",
                f"- Renderer families: {_format_field_tuple(tuple(renderer_families))}",
                f"- QC profiles: {_format_field_tuple(tuple(qc_profiles))}",
                "",
            ]
        )
    return lines


def render_display_audit_guide_markdown() -> str:
    illustration_specs = display_registry.list_illustration_shell_specs()
    table_specs = display_registry.list_table_shell_specs()
    evidence_specs = display_registry.list_evidence_figure_specs()
    evidence_classes = _evidence_display_classes()
    total_templates = len(evidence_specs) + len(illustration_specs) + len(table_specs)

    lines = [
        "# Medical Display Audit Guide",
        "",
        "This guide is the stable, human-auditable view of the medical display system in `med-autoscience`.",
        "",
        "Use this file when the goal is to answer which display classes are officially supported, which templates are fully audited, and which schema/QC path each class is bound to.",
        "",
        "For the exhaustive generated matrix, see [medical_display_template_catalog.md](./medical_display_template_catalog.md).",
        "",
        "## Current Audited Coverage",
        "",
        f"- Evidence figure classes: `{len(evidence_classes)}`",
        f"- Implemented evidence figure templates: `{len(evidence_specs)}`",
        f"- Illustration shells: `{len(illustration_specs)}`",
        f"- Table shells: `{len(table_specs)}`",
        f"- Total implemented display templates: `{total_templates}`",
        "",
    ]
    lines.extend(_render_audit_class_map_section())
    lines.extend(_render_audit_class_detail_section())
    lines.extend(
        [
            "## Publication Shell Layer",
            "",
            "| Kind | Implemented Templates | Input Schemas | Contract Gate |",
            "| --- | ---: | --- | --- |",
            "| "
            + " | ".join(
                [
                    "Illustration Shell",
                    str(len(illustration_specs)),
                    _format_field_tuple(tuple(spec.input_schema_id for spec in illustration_specs)),
                    "shell profile + catalog contract",
                ]
            )
            + " |",
            "| "
            + " | ".join(
                [
                    "Table Shell",
                    str(len(table_specs)),
                    _format_field_tuple(tuple(spec.input_schema_id for spec in table_specs)),
                    "table profile + catalog contract",
                ]
            )
            + " |",
            "",
            "## Change Protocol",
            "",
            "Whenever a new audited display template is added, update `display_registry.py`, `display_schema_contract.py`, `display_surface_materialization.py`, `display_layout_qc.py`, the checked-in guides, and the program reports in the same change.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_display_template_catalog_markdown() -> str:
    lines = [
        "# Medical Display Template Catalog",
        "",
        "Generated from `med_autoscience.display_registry` and `med_autoscience.display_schema_contract`.",
        "",
        "For the stable human-auditable overview, completion counts, and change protocol, see [medical_display_audit_guide.md](./medical_display_audit_guide.md).",
        "",
        "## Publication Style and Override Governance",
        "",
        "- `paper/publication_style_profile.json` is the article-level visual truth source for publication-facing figures.",
        "- `paper/display_overrides.json` is the figure-level structured adjustment surface for manuscript-specific layout and readability decisions.",
        "- Templates preserve a stable lower bound; article-level style and figure-level overrides may refine expression without bypassing the audited renderer path.",
        "",
    ]
    lines.extend(_render_template_class_section())
    lines.extend(_render_input_schema_section())
    return "\n".join(lines).rstrip() + "\n"
