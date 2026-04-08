from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from med_autoscience import display_registry, display_schema_contract
from med_autoscience.display_pack_resolver import split_full_template_id


CORE_PACK_ID = "fenggaolab.org.medical-display-core"
_DEFAULT_EXECUTION_MODE = "python_plugin"
_UNIFIED_ENTRYPOINT = "med_autoscience.controllers.display_surface_materialization:materialize_display_surface"
_PACK_LOCAL_ENTRYPOINTS = {
    f"{CORE_PACK_ID}::time_to_event_risk_group_summary": (
        "fenggaolab_org_medical_display_core.evidence_figures:render_time_to_event_risk_group_summary"
    )
}
_PUBLICATION_SHELL_CLASS_ID = "publication_shells_and_tables"
_PAPER_PROVEN_TEMPLATE_IDS = frozenset(
    (
        f"{CORE_PACK_ID}::binary_calibration_decision_curve_panel",
        f"{CORE_PACK_ID}::time_to_event_discrimination_calibration_panel",
        f"{CORE_PACK_ID}::time_to_event_risk_group_summary",
        f"{CORE_PACK_ID}::time_to_event_decision_curve",
        f"{CORE_PACK_ID}::multicenter_generalizability_overview",
        f"{CORE_PACK_ID}::submission_graphical_abstract",
    )
)


@dataclass(frozen=True)
class _TemplateManifestRecord:
    template_id: str
    full_template_id: str
    kind: str
    display_name: str
    paper_family_ids: tuple[str, ...]
    audit_family: str
    renderer_family: str
    input_schema_ref: str
    qc_profile_ref: str
    required_exports: tuple[str, ...]
    allowed_paper_roles: tuple[str, ...]
    execution_mode: str
    entrypoint: str
    paper_proven: bool


def _short_template_id(full_template_id: str) -> str:
    pack_id, short_id = split_full_template_id(full_template_id)
    if pack_id != CORE_PACK_ID:
        raise ValueError(f"unexpected core pack id in template `{full_template_id}`")
    return short_id


def _audit_family_map() -> dict[str, str]:
    return {
        display_class.class_id: display_class.display_name
        for display_class in display_schema_contract.list_display_schema_classes()
    }


def _build_manifest_records() -> tuple[_TemplateManifestRecord, ...]:
    audit_family_map = _audit_family_map()
    publication_shell_audit_family = audit_family_map[_PUBLICATION_SHELL_CLASS_ID]
    records: list[_TemplateManifestRecord] = []

    for spec in display_registry.list_evidence_figure_specs():
        short_id = _short_template_id(spec.template_id)
        records.append(
            _TemplateManifestRecord(
                template_id=short_id,
                full_template_id=spec.template_id,
                kind="evidence_figure",
                display_name=spec.display_name,
                paper_family_ids=spec.paper_family_ids,
                audit_family=audit_family_map[spec.evidence_class],
                renderer_family=spec.renderer_family,
                input_schema_ref=spec.input_schema_id,
                qc_profile_ref=spec.layout_qc_profile,
                required_exports=spec.required_exports,
                allowed_paper_roles=spec.allowed_paper_roles,
                execution_mode=_DEFAULT_EXECUTION_MODE,
                entrypoint=_PACK_LOCAL_ENTRYPOINTS.get(spec.template_id, _UNIFIED_ENTRYPOINT),
                paper_proven=spec.template_id in _PAPER_PROVEN_TEMPLATE_IDS,
            )
        )

    for spec in display_registry.list_illustration_shell_specs():
        short_id = _short_template_id(spec.shell_id)
        records.append(
            _TemplateManifestRecord(
                template_id=short_id,
                full_template_id=spec.shell_id,
                kind="illustration_shell",
                display_name=spec.display_name,
                paper_family_ids=spec.paper_family_ids,
                audit_family=publication_shell_audit_family,
                renderer_family=spec.renderer_family,
                input_schema_ref=spec.input_schema_id,
                qc_profile_ref=spec.shell_qc_profile,
                required_exports=spec.required_exports,
                allowed_paper_roles=spec.allowed_paper_roles,
                execution_mode=_DEFAULT_EXECUTION_MODE,
                entrypoint=_UNIFIED_ENTRYPOINT,
                paper_proven=spec.shell_id in _PAPER_PROVEN_TEMPLATE_IDS,
            )
        )

    for spec in display_registry.list_table_shell_specs():
        short_id = _short_template_id(spec.shell_id)
        records.append(
            _TemplateManifestRecord(
                template_id=short_id,
                full_template_id=spec.shell_id,
                kind="table_shell",
                display_name=spec.display_name,
                paper_family_ids=spec.paper_family_ids,
                audit_family=publication_shell_audit_family,
                renderer_family="n/a",
                input_schema_ref=spec.input_schema_id,
                qc_profile_ref=spec.table_qc_profile,
                required_exports=spec.required_exports,
                allowed_paper_roles=spec.allowed_paper_roles,
                execution_mode=_DEFAULT_EXECUTION_MODE,
                entrypoint=_UNIFIED_ENTRYPOINT,
                paper_proven=spec.shell_id in _PAPER_PROVEN_TEMPLATE_IDS,
            )
        )

    return tuple(sorted(records, key=lambda item: item.full_template_id))


def _quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _quote_list(values: tuple[str, ...]) -> str:
    return "[" + ", ".join(_quote(item) for item in values) + "]"


def _render_template_manifest(record: _TemplateManifestRecord) -> str:
    lines = (
        f"template_id = {_quote(record.template_id)}",
        f"full_template_id = {_quote(record.full_template_id)}",
        f"kind = {_quote(record.kind)}",
        f"display_name = {_quote(record.display_name)}",
        f"paper_family_ids = {_quote_list(record.paper_family_ids)}",
        f"audit_family = {_quote(record.audit_family)}",
        f"renderer_family = {_quote(record.renderer_family)}",
        f"input_schema_ref = {_quote(record.input_schema_ref)}",
        f"qc_profile_ref = {_quote(record.qc_profile_ref)}",
        f"required_exports = {_quote_list(record.required_exports)}",
        f"allowed_paper_roles = {_quote_list(record.allowed_paper_roles)}",
        f"execution_mode = {_quote(record.execution_mode)}",
        f"entrypoint = {_quote(record.entrypoint)}",
        f"paper_proven = {'true' if record.paper_proven else 'false'}",
    )
    return "\n".join(lines) + "\n"


def export_core_pack_template_manifests(pack_root: Path) -> None:
    records = _build_manifest_records()
    templates_root = pack_root / "templates"
    templates_root.mkdir(parents=True, exist_ok=True)

    for record in records:
        template_dir = templates_root / record.template_id
        template_dir.mkdir(parents=True, exist_ok=True)
        (template_dir / "template.toml").write_text(
            _render_template_manifest(record),
            encoding="utf-8",
        )
