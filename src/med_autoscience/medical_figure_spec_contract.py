from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.publication_figure_quality_contract import VALID_FIGURE_KINDS


MEDICAL_FIGURE_SPEC_BASENAME = "figure_spec.json"
SUPPORTED_MEDICAL_SEMANTIC_FIELDS = frozenset(
    (
        "cohort_ref",
        "endpoint_ref",
        "model_ref",
        "risk_horizon",
        "effect_estimate_ref",
        "claim_role",
    )
)


def _read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must be a JSON object")
    return payload


def _require_schema_version(payload: dict[str, Any], *, contract_name: str) -> None:
    schema_version = payload.get("schema_version")
    if isinstance(schema_version, bool) or not isinstance(schema_version, int):
        raise ValueError(f"{contract_name}.schema_version must be an integer")
    if schema_version != 1:
        raise ValueError(f"{contract_name}.schema_version must equal 1")


def _require_non_empty_string(item: dict[str, Any], field_name: str, *, context: str) -> str:
    value = item.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}.{field_name} must be a non-empty string")
    return value.strip()


def _optional_non_empty_string(item: dict[str, Any], field_name: str, *, context: str) -> str | None:
    value = item.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}.{field_name} must be a non-empty string when provided")
    return value.strip()


def _require_object(item: dict[str, Any], field_name: str, *, context: str) -> dict[str, Any]:
    value = item.get(field_name)
    if not isinstance(value, dict):
        raise ValueError(f"{context}.{field_name} must be a JSON object")
    return dict(value)


def _normalize_medical_semantics(
    semantics: dict[str, Any],
    *,
    figure_kind: str,
    context: str,
) -> dict[str, Any]:
    normalized = dict(semantics)
    normalized["claim_role"] = _require_non_empty_string(semantics, "claim_role", context=context)

    if figure_kind == "evidence_figure":
        normalized["cohort_ref"] = _require_non_empty_string(semantics, "cohort_ref", context=context)
        normalized["endpoint_ref"] = _require_non_empty_string(semantics, "endpoint_ref", context=context)

    for field_name in SUPPORTED_MEDICAL_SEMANTIC_FIELDS - {"cohort_ref", "endpoint_ref", "claim_role"}:
        value = _optional_non_empty_string(semantics, field_name, context=context)
        if value is not None:
            normalized[field_name] = value

    if figure_kind != "evidence_figure":
        for field_name in ("cohort_ref", "endpoint_ref"):
            value = _optional_non_empty_string(semantics, field_name, context=context)
            if value is not None:
                normalized[field_name] = value

    return normalized


def _normalize_panels(payload: dict[str, Any]) -> list[dict[str, Any]]:
    panels = payload.get("panels")
    if panels is None:
        return []
    if not isinstance(panels, list):
        raise ValueError("medical_figure_spec.panels must be a list when provided")

    normalized_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()
    for index, panel in enumerate(panels):
        context = f"medical_figure_spec.panels[{index}]"
        if not isinstance(panel, dict):
            raise ValueError(f"{context} must be a JSON object")
        panel_id = _require_non_empty_string(panel, "panel_id", context=context)
        if panel_id in seen_panel_ids:
            raise ValueError(f"medical_figure_spec.panels[].panel_id contains duplicate value `{panel_id}`")
        seen_panel_ids.add(panel_id)
        normalized_panels.append(
            {
                **panel,
                "panel_id": panel_id,
                "data_role": _require_non_empty_string(panel, "data_role", context=context),
                "mark_role": _require_non_empty_string(panel, "mark_role", context=context),
            }
        )
    return normalized_panels


def load_medical_figure_spec(path: Path) -> dict[str, Any]:
    payload = _read_json_object(path)
    _require_schema_version(payload, contract_name="medical_figure_spec")

    figure_id = _require_non_empty_string(payload, "figure_id", context="medical_figure_spec")
    intent_ref = _require_non_empty_string(payload, "intent_ref", context="medical_figure_spec")
    template_id = _require_non_empty_string(payload, "template_id", context="medical_figure_spec")
    figure_kind = _require_non_empty_string(payload, "figure_kind", context="medical_figure_spec")
    if figure_kind not in VALID_FIGURE_KINDS:
        raise ValueError(f"medical_figure_spec.figure_kind must be one of {sorted(VALID_FIGURE_KINDS)!r}")

    semantics = _require_object(payload, "medical_semantics", context="medical_figure_spec")
    normalized_semantics = _normalize_medical_semantics(
        semantics,
        figure_kind=figure_kind,
        context="medical_figure_spec.medical_semantics",
    )
    normalized_panels = _normalize_panels(payload)

    normalized = {
        **payload,
        "figure_id": figure_id,
        "intent_ref": intent_ref,
        "template_id": template_id,
        "figure_kind": figure_kind,
        "medical_semantics": normalized_semantics,
    }
    if "panels" in payload:
        normalized["panels"] = normalized_panels
    return normalized
