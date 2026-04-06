from __future__ import annotations

from collections.abc import Mapping

from med_autoscience import display_registry, display_schema_contract


def _template_metadata_by_id() -> dict[str, dict[str, str]]:
    metadata: dict[str, dict[str, str]] = {}
    for spec in display_registry.list_evidence_figure_specs():
        metadata[spec.template_id] = {
            "display_name": spec.display_name,
            "paper_families": ", ".join(
                f"`{display_registry.get_paper_family_label(item)}`" for item in spec.paper_family_ids
            ),
            "renderer_family": spec.renderer_family,
            "input_schema_id": spec.input_schema_id,
            "qc_profile": spec.layout_qc_profile,
            "required_exports": ", ".join(f"`{item}`" for item in spec.required_exports),
            "display_kind": "evidence_figure",
        }
    for spec in display_registry.list_illustration_shell_specs():
        metadata[spec.shell_id] = {
            "display_name": spec.display_name,
            "paper_families": ", ".join(
                f"`{display_registry.get_paper_family_label(item)}`" for item in spec.paper_family_ids
            ),
            "renderer_family": spec.renderer_family,
            "input_schema_id": spec.input_schema_id,
            "qc_profile": spec.shell_qc_profile,
            "required_exports": ", ".join(f"`{item}`" for item in spec.required_exports),
            "display_kind": "illustration_shell",
        }
    for spec in display_registry.list_table_shell_specs():
        metadata[spec.shell_id] = {
            "display_name": spec.display_name,
            "paper_families": ", ".join(
                f"`{display_registry.get_paper_family_label(item)}`" for item in spec.paper_family_ids
            ),
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


def _render_template_class_section() -> list[str]:
    metadata_by_id = _template_metadata_by_id()
    lines = ["## Template Classes", ""]
    for display_class in display_schema_contract.list_display_schema_classes():
        lines.extend(
            [
                f"### {display_class.display_name}",
                "",
                "| Template ID | Kind | Paper Family | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports |",
                "| --- | --- | --- | --- | --- | --- | --- | --- |",
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
                        metadata["paper_families"],
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


def render_display_template_catalog_markdown() -> str:
    lines = [
        "# Medical Display Template Catalog",
        "",
        "Generated from `med_autoscience.display_registry` and `med_autoscience.display_schema_contract`.",
        "",
        "Paper-family labels follow the roadmap in [medical_display_family_roadmap.md](./medical_display_family_roadmap.md).",
        "",
        "For the stable human-auditable overview, completion counts, and change protocol, see [medical_display_audit_guide.md](./medical_display_audit_guide.md).",
        "",
        "## Publication Style and Override Governance",
        "",
        "- `paper/publication_style_profile.json` is the article-level visual truth source for publication-facing figures.",
        "- `paper/display_overrides.json` is the figure-level structured adjustment surface for manuscript-specific layout and readability decisions.",
        "- Templates preserve a stable lower bound; article-level style and figure-level overrides may refine expression without bypassing the audited renderer path.",
        "- Final manuscript-facing polish is **AI-first above that lower bound**: use the generated image as the truth surface, let visual review identify concrete defects, then harden the audited renderer/QC path instead of paper-local patching.",
        "- Canonical paper-owned packaging surface remains `paper/submission_minimal/`; `manuscript/final/` is the human-facing mirror, while `artifacts/` is auxiliary evidence only and should not replace that fixed lookup path.",
        "- Canonical rendered assets live under `paper/figures/generated/` and `paper/tables/generated/`; legacy top-level `paper/figures/Figure*.png|pdf|svg` / `paper/tables/Table*.csv|md` mirrors should be removed once they are no longer referenced by the active catalogs.",
        "",
    ]
    lines.extend(_render_template_class_section())
    lines.extend(_render_input_schema_section())
    return "\n".join(lines).rstrip() + "\n"
