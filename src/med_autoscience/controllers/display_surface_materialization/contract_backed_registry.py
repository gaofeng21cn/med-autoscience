from __future__ import annotations

from collections.abc import Callable

from .shared import Any, Path, _require_namespaced_registry_id, display_registry, load_json


def _append_unique_string(values: list[str], value: object) -> None:
    normalized = str(value or "").strip()
    if normalized and normalized not in values:
        values.append(normalized)


def _iter_reporting_contract_requirement_keys(
    *,
    paper_root: Path,
    display_id: str,
    figure_id: str,
) -> list[str]:
    reporting_contract_path = paper_root / "medical_reporting_contract.json"
    if not reporting_contract_path.exists():
        return []
    reporting_contract = load_json(reporting_contract_path)
    display_shell_plan = reporting_contract.get("display_shell_plan")
    if not isinstance(display_shell_plan, list):
        return []
    requirement_keys: list[str] = []
    for display_plan_item in display_shell_plan:
        if not isinstance(display_plan_item, dict):
            continue
        if str(display_plan_item.get("display_kind") or "").strip() != "figure":
            continue
        plan_display_id = str(display_plan_item.get("display_id") or "").strip()
        plan_catalog_id = str(display_plan_item.get("catalog_id") or "").strip()
        if plan_catalog_id not in {figure_id, display_id} and plan_display_id != display_id:
            continue
        _append_unique_string(requirement_keys, display_plan_item.get("requirement_key"))
    return requirement_keys


def resolve_contract_backed_figure_registry_fields(
    *,
    paper_root: Path,
    item: dict[str, Any],
    shell_payload: dict[str, Any],
    contract_payload: dict[str, Any],
    display_id: str,
    figure_id: str,
) -> dict[str, Any]:
    candidate_keys: list[str] = []
    for payload in (contract_payload, shell_payload, item):
        for field_name in ("template_id", "requirement_key", "shell_id"):
            _append_unique_string(candidate_keys, payload.get(field_name))
    for requirement_key in _iter_reporting_contract_requirement_keys(
        paper_root=paper_root,
        display_id=display_id,
        figure_id=figure_id,
    ):
        _append_unique_string(candidate_keys, requirement_key)

    for candidate_key in candidate_keys:
        if display_registry.is_evidence_figure_template(candidate_key):
            spec = display_registry.get_evidence_figure_spec(candidate_key)
            pack_id, _ = _require_namespaced_registry_id(spec.template_id, label=f"{candidate_key} template_id")
            return {
                "template_id": spec.template_id,
                "pack_id": pack_id,
                "renderer_family": spec.renderer_family,
                "input_schema_id": spec.input_schema_id,
                "qc_profile": spec.layout_qc_profile,
                "required_exports": list(spec.required_exports),
                "allowed_paper_roles": spec.allowed_paper_roles,
            }
        if display_registry.is_illustration_shell(candidate_key):
            spec = display_registry.get_illustration_shell_spec(candidate_key)
            pack_id, _ = _require_namespaced_registry_id(spec.shell_id, label=f"{candidate_key} shell_id")
            return {
                "template_id": spec.shell_id,
                "pack_id": pack_id,
                "renderer_family": spec.renderer_family,
                "input_schema_id": spec.input_schema_id,
                "qc_profile": spec.shell_qc_profile,
                "required_exports": list(spec.required_exports),
                "allowed_paper_roles": spec.allowed_paper_roles,
            }

    joined_candidates = ", ".join(candidate_keys) or "none"
    raise ValueError(
        f"contract-backed figure `{figure_id}` does not map to a registered display template; "
        f"candidate keys: {joined_candidates}"
    )


def resolve_contract_backed_layout_sidecar_path(
    *,
    workspace_path_resolver: Callable[[object], Path],
    contract_payload: dict[str, Any],
    export_paths: list[str],
) -> Path | None:
    for field_name in ("layout_sidecar_path", "rendered_layout_sidecar_path"):
        raw_path = str(contract_payload.get(field_name) or "").strip()
        if raw_path:
            resolved_path = workspace_path_resolver(raw_path)
            if resolved_path.exists():
                return resolved_path
    for export_path in export_paths:
        if not export_path.lower().endswith((".png", ".pdf", ".svg")):
            continue
        candidate_path = workspace_path_resolver(str(Path(export_path).with_suffix(".layout.json")))
        if candidate_path.exists():
            return candidate_path
    return None
