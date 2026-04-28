from __future__ import annotations

from . import shared_base as _shared_base

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared_base)

def _canonicalize_registry_id(value: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        return normalized
    if display_registry.is_evidence_figure_template(normalized):
        return display_registry.get_evidence_figure_spec(normalized).template_id
    if display_registry.is_illustration_shell(normalized):
        return display_registry.get_illustration_shell_spec(normalized).shell_id
    if display_registry.is_table_shell(normalized):
        return display_registry.get_table_shell_spec(normalized).shell_id
    return normalized

def full_id(value: str) -> str:
    return _canonicalize_registry_id(value)

def _normalize_namespaced_ids(payload: Any) -> Any:
    if isinstance(payload, dict):
        normalized: dict[str, Any] = {}
        for key, value in payload.items():
            normalized_value = _normalize_namespaced_ids(value)
            if key in {"requirement_key", "template_id", "shell_id", "table_shell_id"} and isinstance(
                normalized_value, str
            ):
                normalized_value = _canonicalize_registry_id(normalized_value)
            normalized[key] = normalized_value
        return normalized
    if isinstance(payload, list):
        return [_normalize_namespaced_ids(item) for item in payload]
    return payload

def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized_payload = _normalize_namespaced_ids(payload)
    path.write_text(json.dumps(normalized_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def _ensure_output_parents(*paths: Path | None) -> None:
    for path in paths:
        if path is None:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)

def extract_svg_font_size(svg_text: str, marker: str) -> float:
    match = re.search(rf"font-size: ([0-9.]+)px;[^>]*>{re.escape(marker)}<", svg_text)
    assert match is not None, f"missing svg text marker: {marker}"
    return float(match.group(1))

def write_default_publication_display_contracts(paper_root: Path) -> None:
    dump_json(
        paper_root / "publication_style_profile.json",
        {
            "schema_version": 1,
            "style_profile_id": "paper_neutral_clinical_v1",
            "palette": {
                "primary": "#245A6B",
                "secondary": "#B89A6D",
                "contrast": "#8B3A3A",
                "neutral": "#6B7280",
                "light": "#E7E1D8",
                "primary_soft": "#EAF2F5",
                "secondary_soft": "#F4EEE5",
                "contrast_soft": "#F7EBEB",
                "audit": "#9E5151",
                "audit_soft": "#FAEFED",
            },
            "semantic_roles": {
                "model_curve": "primary",
                "comparator_curve": "secondary",
                "reference_line": "neutral",
                "highlight_band": "light",
                "flow_main_fill": "light",
                "flow_main_edge": "neutral",
                "flow_exclusion_fill": "audit_soft",
                "flow_exclusion_edge": "audit",
                "flow_primary_fill": "primary_soft",
                "flow_primary_edge": "primary",
                "flow_secondary_fill": "light",
                "flow_secondary_edge": "neutral",
                "flow_context_fill": "contrast_soft",
                "flow_context_edge": "contrast",
                "flow_audit_fill": "audit_soft",
                "flow_audit_edge": "audit",
                "flow_title_text": "neutral",
                "flow_body_text": "neutral",
                "flow_panel_label": "neutral",
                "flow_connector": "neutral",
            },
            "typography": {
                "title_size": 12.5,
                "axis_title_size": 11.0,
                "tick_size": 10.0,
                "panel_label_size": 11.0,
            },
            "stroke": {
                "primary_linewidth": 2.4,
                "secondary_linewidth": 1.9,
                "reference_linewidth": 1.0,
                "marker_size": 4.2,
            },
        },
    )
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [],
        },
    )

def restrict_display_registry_to_display_ids(paper_root: Path, *display_ids: str) -> None:
    registry_path = paper_root / "display_registry.json"
    registry_payload = json.loads(registry_path.read_text(encoding="utf-8"))
    allowed_display_ids = {str(value).strip() for value in display_ids if str(value).strip()}
    registry_payload["displays"] = [
        item
        for item in (registry_payload.get("displays") or [])
        if str(item.get("display_id") or "").strip() in allowed_display_ids
    ]
    dump_json(registry_path, registry_payload)
