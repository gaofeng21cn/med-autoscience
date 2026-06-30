from __future__ import annotations

from collections.abc import Mapping

from med_autoscience import display_registry, display_schema_contract
from med_autoscience.display_pack_canonical_catalog import load_canonical_template_catalog
from med_autoscience.display_pack_loader import default_display_pack_repo_root
from med_autoscience.display_pack_paths import core_medical_display_pack_root


_CORE_PACK_ID = "fenggaolab.org.medical-display-core"
_CORE_PACK_ROOT = core_medical_display_pack_root(default_display_pack_repo_root())


def _full_id(short_id: str) -> str:
    return f"{_CORE_PACK_ID}::{short_id}"


def _short_id(template_id: str) -> str:
    return str(template_id or "").split("::")[-1]


def _analysis_responsibility_by_id() -> dict[str, dict[str, str]]:
    catalog = load_canonical_template_catalog(_CORE_PACK_ROOT)
    if catalog is None:
        return {}
    return {
        _full_id(entry.template_id): {
            "analysis_responsibility": entry.analysis_responsibility,
            "analysis_input_state": entry.analysis_input_state,
        }
        for entry in catalog.entries_by_template_id.values()
        if entry.migration_status == "canonical"
    }


def _template_metadata_by_id() -> dict[str, dict[str, str]]:
    metadata: dict[str, dict[str, str]] = {}
    analysis_by_id = _analysis_responsibility_by_id()
    for spec in display_registry.list_evidence_figure_specs():
        analysis = analysis_by_id[_full_id(_short_id(spec.template_id))]
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
            "analysis_responsibility": analysis["analysis_responsibility"],
            "analysis_input_state": analysis["analysis_input_state"],
        }
    for spec in display_registry.list_illustration_shell_specs():
        analysis = analysis_by_id[_full_id(_short_id(spec.shell_id))]
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
            "analysis_responsibility": analysis["analysis_responsibility"],
            "analysis_input_state": analysis["analysis_input_state"],
        }
    for spec in display_registry.list_table_shell_specs():
        analysis = analysis_by_id[_full_id(_short_id(spec.shell_id))]
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
            "analysis_responsibility": analysis["analysis_responsibility"],
            "analysis_input_state": analysis["analysis_input_state"],
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
                "| Template ID | Kind | Paper Family | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports | Analysis Responsibility |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
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
                        f"`{metadata['analysis_responsibility']}` / `{metadata['analysis_input_state']}`",
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


def _render_paper_proven_baseline_section() -> list[str]:
    paper_families = ", ".join(
        f"`{display_registry.get_paper_family_label(item)}`" for item in ("A", "B", "H")
    )
    audit_families = ", ".join(
        f"`{item}`"
        for item in (
            "Clinical Utility",
            "Time-to-Event",
            "Generalizability",
            "Publication Shells and Tables",
        )
    )
    template_ids = ", ".join(
        f"`{item}`"
        for item in (
            _full_id("calibration_curve_binary"),
            _full_id("time_dependent_roc_horizon"),
            _full_id("risk_layering_monotonic_bars"),
            _full_id("time_to_event_decision_curve"),
            _full_id("generalizability_subgroup_composite_panel"),
            _full_id("submission_graphical_abstract"),
        )
    )
    return [
        "## Current Paper-Proven Baseline (001/003)",
        "",
        "The current audited inventory is broader than the subset already proven against real papers.",
        "",
        f"- Paper families: {paper_families}",
        f"- Audit families: {audit_families}",
        f"- Template instances: {template_ids}",
        "- Cross-paper golden regression priority: title policy, annotation placement, panel-label/header-band anchoring, grouped-separation readability, landmark/time-slice semantics, graphical-abstract arrow lanes, calibration axis-window fit, and generalizability interval readability",
        "",
    ]


def render_display_template_catalog_markdown() -> str:
    lines = [
        "# Medical Display Template Catalog",
        "",
        "Owner: `MedAutoScience`",
        "Purpose: `medical_display_template_catalog`",
        "State: `generated_catalog`",
        "Machine boundary: Generated human-readable template inventory. Machine truth remains in `med_autoscience.display_registry`, `med_autoscience.display_schema_contract`, renderer/QC source, tests, generated gallery status, manifests, and runtime/controller receipts.",
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
        "- Canonical paper-owned packaging surface remains `paper/submission_minimal/`; `manuscript/` is the human-facing mirror, while `artifacts/` is auxiliary evidence only and should not replace that fixed lookup path.",
        "- Canonical rendered assets live under `paper/figures/generated/` and `paper/tables/generated/`; legacy top-level `paper/figures/Figure*.png|pdf|svg` / `paper/tables/Table*.csv|md` mirrors should be removed once they are no longer referenced by the active catalogs.",
        "- `analysis_responsibility` is loaded from the canonical Display Pack catalog: raw analysis inputs may only enter templates marked `computed_in_template`; `validated_summary_required` templates require upstream validated analysis payloads.",
        "",
    ]
    lines.extend(_render_paper_proven_baseline_section())
    lines.extend(_render_template_class_section())
    lines.extend(_render_input_schema_section())
    return "\n".join(lines).rstrip() + "\n"
