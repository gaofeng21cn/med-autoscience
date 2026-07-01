from __future__ import annotations

from ..shared import Any, Path, display_registry, load_json


_PURPOSE_FIRST_RENDERER_FIELDS = (
    "source_renderer",
    "figure_purpose",
    "rendered_title_policy",
)


def _resolve_workspace_path(path_value: object, *, paper_root: Path) -> Path:
    raw_path = str(path_value or "").strip()
    if not raw_path:
        raise ValueError("expected non-empty paper workspace path")
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path.resolve()
    if path.parts and path.parts[0] == paper_root.name:
        return (paper_root.parent / path).resolve()
    return (paper_root / path).resolve()


def _as_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _claim_ids_for_table(
    *,
    table_catalog: dict[str, Any],
    claim_evidence_map: dict[str, Any],
    table_id: str,
) -> list[str]:
    for entry in table_catalog.get("tables", []) or []:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("table_id") or "").strip() != table_id:
            continue
        existing_claim_ids = _as_string_list(entry.get("claim_ids"))
        if existing_claim_ids:
            return existing_claim_ids

    claim_ids: list[str] = []
    for claim in claim_evidence_map.get("claims", []) or []:
        if not isinstance(claim, dict):
            continue
        display_bindings = _as_string_list(
            claim.get("display_bindings") or claim.get("display_refs") or claim.get("table_bindings")
        )
        if table_id not in display_bindings:
            continue
        claim_id = str(claim.get("claim_id") or "").strip()
        if claim_id and claim_id not in claim_ids:
            claim_ids.append(claim_id)
    return claim_ids


def _is_known_requirement_key(requirement_key: str) -> bool:
    return (
        display_registry.is_illustration_shell(requirement_key)
        or display_registry.is_evidence_figure_template(requirement_key)
        or display_registry.is_table_shell(requirement_key)
    )


def _purpose_first_renderer_fields(layout_sidecar: dict[str, Any]) -> dict[str, str]:
    metrics = layout_sidecar.get("metrics")
    if not isinstance(metrics, dict):
        return {}
    fields: dict[str, str] = {}
    for key in _PURPOSE_FIRST_RENDERER_FIELDS:
        value = str(metrics.get(key) or "").strip()
        if value:
            fields[key] = value
    return fields


def _existing_figure_catalog_entry(
    *,
    figure_catalog: dict[str, Any],
    figure_id: str,
) -> dict[str, Any] | None:
    for entry in figure_catalog.get("figures", []) or []:
        if not isinstance(entry, dict):
            continue
        observed_figure_id = str(entry.get("figure_id") or entry.get("catalog_id") or "").strip()
        if observed_figure_id == figure_id:
            return entry
    return None


def _active_generated_illustration_paths_from_catalog(
    *,
    paper_root: Path,
    figure_catalog: dict[str, Any],
    figure_id: str,
    template_id: str,
    pdf_required: bool,
) -> tuple[Path, Path | None, Path] | None:
    entry = _existing_figure_catalog_entry(figure_catalog=figure_catalog, figure_id=figure_id)
    if not entry or str(entry.get("template_id") or "").strip() != template_id:
        return None
    export_paths = _as_string_list(entry.get("export_paths"))
    png_ref = next((ref for ref in export_paths if ref == f"paper/figures/generated/{figure_id}.png"), "")
    pdf_ref = next((ref for ref in export_paths if ref == f"paper/figures/generated/{figure_id}.pdf"), "")
    qc_result = entry.get("qc_result")
    layout_ref = ""
    if isinstance(qc_result, dict):
        layout_ref = str(qc_result.get("layout_sidecar_path") or "").strip()
    if layout_ref != f"paper/figures/generated/{figure_id}.layout.json":
        layout_ref = ""
    if not png_ref or not layout_ref or (pdf_required and not pdf_ref):
        return None
    return (
        _resolve_workspace_path(png_ref, paper_root=paper_root),
        _resolve_workspace_path(pdf_ref, paper_root=paper_root) if pdf_ref else None,
        _resolve_workspace_path(layout_ref, paper_root=paper_root),
    )


def _load_display_shell_payload(*, paper_root: Path, item: dict[str, Any]) -> dict[str, Any] | None:
    shell_path = str(item.get("shell_path") or "").strip()
    if not shell_path:
        return None
    resolved_shell_path = _resolve_workspace_path(shell_path, paper_root=paper_root)
    if not resolved_shell_path.exists():
        requirement_key = str(item.get("requirement_key") or "").strip()
        if _is_known_requirement_key(requirement_key):
            return None
        raise ValueError(f"display shell_path does not exist: {shell_path}")
    return load_json(resolved_shell_path)


def _contract_path_from_shell_path(shell_path: str) -> str:
    if shell_path.endswith(".shell.json"):
        return f"{shell_path.removesuffix('.shell.json')}.contract.json"
    return str(Path(shell_path).with_suffix(".contract.json"))


def _contract_backed_figure_contract_candidates(
    *,
    paper_root: Path,
    item: dict[str, Any],
    shell_payload: dict[str, Any],
) -> list[Path]:
    candidate_values: list[str] = []
    for value in (shell_payload.get("source_contract_path"), item.get("source_contract_path")):
        normalized = str(value or "").strip()
        if normalized:
            candidate_values.append(normalized)

    shell_path = str(item.get("shell_path") or "").strip()
    if shell_path:
        candidate_values.append(_contract_path_from_shell_path(shell_path))

    display_id = str(shell_payload.get("display_id") or item.get("display_id") or "").strip()
    if display_id:
        candidate_values.append(f"paper/figures/{display_id}.contract.json")

    candidates: list[Path] = []
    seen: set[str] = set()
    for value in candidate_values:
        resolved = _resolve_workspace_path(value, paper_root=paper_root)
        key = str(resolved)
        if key in seen:
            continue
        seen.add(key)
        candidates.append(resolved)
    return candidates


def _resolve_contract_backed_figure_contract_path(
    *,
    paper_root: Path,
    item: dict[str, Any],
    shell_payload: dict[str, Any],
) -> Path | None:
    for candidate_path in _contract_backed_figure_contract_candidates(
        paper_root=paper_root,
        item=item,
        shell_payload=shell_payload,
    ):
        if not candidate_path.exists():
            continue
        candidate_payload = load_json(candidate_path)
        if str(candidate_payload.get("renderer_script_path") or "").strip():
            return candidate_path
    return None


def _resolve_requirement_key_from_shell(
    *,
    requirement_key: str,
    shell_payload: dict[str, Any] | None,
) -> str:
    if _is_known_requirement_key(requirement_key):
        return requirement_key
    if not shell_payload:
        return requirement_key
    shell_requirement_key = str(shell_payload.get("requirement_key") or "").strip()
    if shell_requirement_key and _is_known_requirement_key(shell_requirement_key):
        return shell_requirement_key
    shell_template_id = str(shell_payload.get("template_id") or "").strip()
    if shell_template_id and display_registry.is_evidence_figure_template(shell_template_id):
        return shell_template_id
    shell_id = str(shell_payload.get("shell_id") or "").strip()
    if shell_id and display_registry.is_illustration_shell(shell_id):
        return shell_id
    return requirement_key


__all__ = [
    "_active_generated_illustration_paths_from_catalog",
    "_as_string_list",
    "_claim_ids_for_table",
    "_is_known_requirement_key",
    "_load_display_shell_payload",
    "_purpose_first_renderer_fields",
    "_resolve_contract_backed_figure_contract_path",
    "_resolve_requirement_key_from_shell",
    "_resolve_workspace_path",
]
