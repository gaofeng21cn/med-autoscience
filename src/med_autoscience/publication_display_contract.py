from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


_REQUIRED_STYLE_ROLES_BY_TEMPLATE: dict[str, tuple[str, ...]] = {
    "binary_calibration_decision_curve_panel": ("model_curve", "comparator_curve", "reference_line"),
    "model_complexity_audit_panel": ("model_curve", "comparator_curve", "reference_line"),
    "risk_layering_monotonic_bars": ("model_curve", "comparator_curve"),
    "time_dependent_roc_comparison_panel": ("model_curve", "comparator_curve", "reference_line"),
    "time_to_event_discrimination_calibration_panel": ("model_curve", "comparator_curve", "reference_line"),
    "time_to_event_risk_group_summary": ("model_curve", "comparator_curve", "reference_line"),
    "time_to_event_stratified_cumulative_incidence_panel": ("model_curve", "comparator_curve", "reference_line"),
    "time_to_event_decision_curve": ("model_curve", "comparator_curve", "reference_line"),
    "cohort_flow_figure": (
        "flow_main_fill",
        "flow_main_edge",
        "flow_exclusion_fill",
        "flow_exclusion_edge",
        "flow_primary_fill",
        "flow_primary_edge",
        "flow_secondary_fill",
        "flow_secondary_edge",
        "flow_context_fill",
        "flow_context_edge",
        "flow_audit_fill",
        "flow_audit_edge",
        "flow_title_text",
        "flow_body_text",
        "flow_panel_label",
        "flow_connector",
    ),
}


@dataclass(frozen=True)
class PublicationStyleProfile:
    schema_version: int
    style_profile_id: str
    journal_palette_ref: str
    palette: dict[str, str]
    semantic_roles: dict[str, str]
    typography: dict[str, Any]
    stroke: dict[str, float]
    grid: dict[str, Any]


@dataclass(frozen=True)
class DisplayOverride:
    display_id: str
    template_id: str
    layout_override: dict[str, Any]
    readability_override: dict[str, Any]


_DEFAULT_STYLE_PROFILE_PAYLOAD: dict[str, Any] = {
    "schema_version": 1,
    "style_profile_id": "paper_neutral_clinical_v1",
    "journal_palette_ref": "nature_informed_clinical_publication_v1",
    "palette": {
        "primary": "#0B4F6C",
        "secondary": "#2A9D8F",
        "contrast": "#2F5D8A",
        "tertiary": "#B84A3A",
        "quaternary": "#D99A2B",
        "violet": "#6F63B6",
        "neutral": "#4D4D4D",
        "neutral_mid": "#767676",
        "neutral_light": "#D8D8D8",
        "light": "#F2F5F7",
        "primary_soft": "#D9EAF0",
        "secondary_soft": "#D8F0EB",
        "contrast_soft": "#E6EDF5",
        "tertiary_soft": "#F1D1CB",
        "quaternary_soft": "#F4E3C2",
        "violet_soft": "#E5E1F1",
        "audit": "#B64342",
        "audit_soft": "#F6CFCB",
        "text": "#272727",
        "axis": "#272727",
        "grid": "#ECEFF2",
        "background": "#FFFFFF",
        "heatmap_seq_low": "#F4F8FA",
        "heatmap_seq_mid": "#9DD2D3",
        "heatmap_seq_high": "#0B4F6C",
        "heatmap_low": "#2B6CB0",
        "heatmap_mid": "#F7F7F7",
        "heatmap_high": "#B64342",
        "volcano_up": "#B64342",
        "volcano_down": "#2B6CB0",
        "volcano_background": "#B8B8B8",
    },
    "semantic_roles": {
        "model_curve": "primary",
        "comparator_curve": "secondary",
        "reference_line": "neutral_mid",
        "highlight_band": "light",
        "text": "text",
        "axis_line": "axis",
        "grid_line": "grid",
        "figure_background": "background",
        "series_1": "primary",
        "series_2": "secondary",
        "series_3": "tertiary",
        "series_4": "quaternary",
        "series_5": "violet",
        "series_6": "neutral_mid",
        "heatmap_low": "heatmap_low",
        "heatmap_mid": "heatmap_mid",
        "heatmap_high": "heatmap_high",
        "heatmap_seq_low": "heatmap_seq_low",
        "heatmap_seq_mid": "heatmap_seq_mid",
        "heatmap_seq_high": "heatmap_seq_high",
        "volcano_up": "volcano_up",
        "volcano_down": "volcano_down",
        "volcano_background": "volcano_background",
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
        "font_family": "sans",
        "base_size": 9.0,
        "title_size": 10.0,
        "axis_title_size": 9.0,
        "tick_size": 8.0,
        "legend_size": 6.8,
        "panel_label_size": 9.2,
        "legend_key_width": 20.0,
        "legend_key_height": 7.0,
        "legend_key_spacing_x": 7.0,
        "legend_key_spacing_y": 3.5,
        "colorbar_width": 5.0,
        "colorbar_height": 42.0,
        "colorbar_horizontal_width": 96.0,
        "colorbar_horizontal_height": 5.0,
    },
    "stroke": {
        "axis_linewidth": 0.35,
        "primary_linewidth": 2.0,
        "secondary_linewidth": 1.55,
        "reference_linewidth": 0.9,
        "grid_linewidth": 0.18,
        "marker_size": 3.4,
    },
    "grid": {
        "major": True,
        "minor": False,
        "major_axis": "y",
        "minor_axis": "none",
        "color": "#ECEFF2",
        "linetype": "solid",
    },
}
_DEFAULT_DISPLAY_OVERRIDES_PAYLOAD: dict[str, Any] = {"schema_version": 1, "displays": []}
_DEFAULT_GRID_PAYLOAD: dict[str, Any] = dict(_DEFAULT_STYLE_PROFILE_PAYLOAD["grid"])


def _read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must be a JSON object")
    return payload


def _write_json_if_missing(path: Path, payload: dict[str, Any]) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def seed_publication_display_contracts_if_missing(*, paper_root: Path) -> list[str]:
    written_files: list[str] = []
    style_profile_path = paper_root / "publication_style_profile.json"
    if _write_json_if_missing(style_profile_path, _DEFAULT_STYLE_PROFILE_PAYLOAD):
        written_files.append(str(style_profile_path))
    display_overrides_path = paper_root / "display_overrides.json"
    if _write_json_if_missing(display_overrides_path, _DEFAULT_DISPLAY_OVERRIDES_PAYLOAD):
        written_files.append(str(display_overrides_path))
    return written_files


def _require_schema_version(payload: dict[str, Any], *, contract_name: str) -> int:
    schema_version = payload.get("schema_version")
    if isinstance(schema_version, bool) or not isinstance(schema_version, int):
        raise ValueError(f"{contract_name}.schema_version must be an integer")
    if schema_version != 1:
        raise ValueError(f"{contract_name}.schema_version must equal 1")
    return schema_version


def _normalize_string_map(value: Any, *, field_name: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    normalized: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, str):
            raise ValueError(f"{field_name} keys and values must be non-empty strings")
        normalized_key = key.strip()
        normalized_value = item.strip()
        if not normalized_key or not normalized_value:
            raise ValueError(f"{field_name} keys and values must be non-empty strings")
        normalized[normalized_key] = normalized_value
    return normalized


def _normalize_numeric_map(value: Any, *, field_name: str) -> dict[str, float]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object when provided")
    normalized: dict[str, float] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError(f"{field_name} keys must be non-empty strings")
        normalized_key = key.strip()
        if not normalized_key:
            raise ValueError(f"{field_name} keys must be non-empty strings")
        if isinstance(item, bool) or not isinstance(item, int | float):
            raise ValueError(f"{field_name}.{normalized_key} must be numeric")
        normalized[normalized_key] = float(item)
    return normalized


def _normalize_typography_map(value: Any, *, field_name: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object when provided")
    normalized: dict[str, Any] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError(f"{field_name} keys must be non-empty strings")
        normalized_key = key.strip()
        if not normalized_key:
            raise ValueError(f"{field_name} keys must be non-empty strings")
        if normalized_key == "font_family":
            if not isinstance(item, str) or not item.strip():
                raise ValueError(f"{field_name}.font_family must be a non-empty string")
            normalized[normalized_key] = item.strip()
            continue
        if isinstance(item, bool) or not isinstance(item, int | float):
            raise ValueError(f"{field_name}.{normalized_key} must be numeric")
        normalized[normalized_key] = float(item)
    return normalized


def _normalize_grid_map(value: Any, *, field_name: str) -> dict[str, Any]:
    if value is None:
        return dict(_DEFAULT_GRID_PAYLOAD)
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object when provided")
    normalized: dict[str, Any] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError(f"{field_name} keys must be non-empty strings")
        normalized_key = key.strip()
        if not normalized_key:
            raise ValueError(f"{field_name} keys must be non-empty strings")
        if isinstance(item, bool):
            normalized[normalized_key] = item
        elif isinstance(item, int | float):
            normalized[normalized_key] = float(item)
        elif isinstance(item, str) and item.strip():
            normalized[normalized_key] = item.strip()
        else:
            raise ValueError(f"{field_name}.{normalized_key} must be a string, number, or boolean")
    for required_key in ("major", "minor"):
        if required_key in normalized and not isinstance(normalized[required_key], bool):
            raise ValueError(f"{field_name}.{required_key} must be boolean")
    return {**_DEFAULT_GRID_PAYLOAD, **normalized}


def load_publication_style_profile(path: Path) -> PublicationStyleProfile:
    payload = _read_json_object(path)
    schema_version = _require_schema_version(payload, contract_name="publication_style_profile")

    style_profile_id_value = payload.get("style_profile_id")
    if not isinstance(style_profile_id_value, str) or not style_profile_id_value.strip():
        raise ValueError("publication_style_profile.style_profile_id must be a non-empty string")
    style_profile_id = style_profile_id_value.strip()

    journal_palette_ref_value = payload.get("journal_palette_ref")
    if journal_palette_ref_value is None:
        journal_palette_ref = ""
    elif isinstance(journal_palette_ref_value, str) and journal_palette_ref_value.strip():
        journal_palette_ref = journal_palette_ref_value.strip()
    else:
        raise ValueError("publication_style_profile.journal_palette_ref must be a non-empty string when provided")

    palette = _normalize_string_map(payload.get("palette"), field_name="publication_style_profile.palette")
    semantic_roles = _normalize_string_map(
        payload.get("semantic_roles"),
        field_name="publication_style_profile.semantic_roles",
    )
    if not semantic_roles:
        raise ValueError("publication_style_profile.semantic_roles must be a non-empty object")

    required_palette_keys = {"primary", "secondary", "neutral"}
    if not required_palette_keys.issubset(palette):
        raise ValueError("publication_style_profile.palette must define primary, secondary, and neutral")
    unknown_palette_keys = {palette_key for palette_key in semantic_roles.values() if palette_key not in palette}
    if unknown_palette_keys:
        unknown = ", ".join(sorted(unknown_palette_keys))
        raise ValueError(f"publication_style_profile.semantic_roles reference undefined palette keys: {unknown}")

    typography = _normalize_typography_map(payload.get("typography"), field_name="publication_style_profile.typography")
    stroke = _normalize_numeric_map(payload.get("stroke"), field_name="publication_style_profile.stroke")
    grid = _normalize_grid_map(payload.get("grid"), field_name="publication_style_profile.grid")

    return PublicationStyleProfile(
        schema_version=schema_version,
        style_profile_id=style_profile_id,
        journal_palette_ref=journal_palette_ref,
        palette=palette,
        semantic_roles=semantic_roles,
        typography=typography,
        stroke=stroke,
        grid=grid,
    )


def publication_style_profile_payload(style_profile: PublicationStyleProfile) -> dict[str, Any]:
    return {
        "schema_version": style_profile.schema_version,
        "style_profile_id": style_profile.style_profile_id,
        "journal_palette_ref": style_profile.journal_palette_ref,
        "palette": dict(style_profile.palette),
        "semantic_roles": dict(style_profile.semantic_roles),
        "typography": dict(style_profile.typography),
        "stroke": dict(style_profile.stroke),
        "grid": dict(style_profile.grid),
    }


def load_display_overrides(path: Path) -> dict[tuple[str, str], DisplayOverride]:
    payload = _read_json_object(path)
    _require_schema_version(payload, contract_name="display_overrides")
    displays = payload.get("displays")
    if not isinstance(displays, list):
        raise ValueError("display_overrides.displays must be a list")

    overrides: dict[tuple[str, str], DisplayOverride] = {}
    for item in displays:
        if not isinstance(item, dict):
            raise ValueError("display_overrides.displays entries must be JSON objects")
        display_id_value = item.get("display_id")
        template_id_value = item.get("template_id")
        if not isinstance(display_id_value, str) or not display_id_value.strip():
            raise ValueError("display_overrides.displays[].display_id must be a non-empty string")
        if not isinstance(template_id_value, str) or not template_id_value.strip():
            raise ValueError("display_overrides.displays[].template_id must be a non-empty string")
        display_id = display_id_value.strip()
        template_id = template_id_value.strip()

        layout_override = item.get("layout_override")
        readability_override = item.get("readability_override")
        if layout_override is None:
            layout_override = {}
        if readability_override is None:
            readability_override = {}
        if not isinstance(layout_override, dict):
            raise ValueError("display_overrides.displays[].layout_override must be an object")
        if not isinstance(readability_override, dict):
            raise ValueError("display_overrides.displays[].readability_override must be an object")

        key = (display_id, template_id)
        if key in overrides:
            raise ValueError(f"display_overrides.displays contains duplicate override for {display_id}/{template_id}")
        overrides[key] = DisplayOverride(
            display_id=display_id,
            template_id=template_id,
            layout_override=dict(layout_override),
            readability_override=dict(readability_override),
        )

    return overrides


def resolve_style_roles(
    *,
    style_profile: PublicationStyleProfile,
    template_id: str,
) -> dict[str, str]:
    resolved: dict[str, str] = {}
    for role, palette_key in style_profile.semantic_roles.items():
        if palette_key not in style_profile.palette:
            raise ValueError(
                f"publication_style_profile.semantic_roles[{role}] references undefined palette key `{palette_key}`"
            )
        resolved[role] = style_profile.palette[palette_key]
    required_roles = _REQUIRED_STYLE_ROLES_BY_TEMPLATE.get(template_id, ())
    missing_roles = [role for role in required_roles if role not in resolved]
    if missing_roles:
        missing = ", ".join(missing_roles)
        raise ValueError(f"{template_id} requires publication style roles: {missing}")
    return resolved
