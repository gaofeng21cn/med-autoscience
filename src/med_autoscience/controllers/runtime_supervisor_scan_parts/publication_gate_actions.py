from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


ACTION_TYPE = "publication_gate_specificity_required"


def action_payload(*, gate_specificity: Mapping[str, Any]) -> dict[str, Any]:
    missing_target_kinds = _string_items(gate_specificity.get("missing_target_kinds")) or [
        "claim",
        "figure",
        "table",
        "metric",
        "source_path",
    ]
    return {
        "action_type": ACTION_TYPE,
        "authority": "observability_only",
        "owner": "publication_gate",
        "request_owner": "publication_gate",
        "recommended_owner": "publication_gate",
        "reason": ACTION_TYPE,
        "summary": "Publication gate must name concrete claim/figure/table/metric/source_path targets.",
        "required_target_kinds": ["claim", "figure", "table", "metric", "source_path"],
        "missing_target_kinds": missing_target_kinds,
        "gate_owner": _text(gate_specificity.get("gate_owner")) or "publication_gate",
        "next_controller_write": _mapping(gate_specificity.get("next_controller_write")),
        "paper_package_mutation_allowed": False,
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _string_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, Iterable) or isinstance(value, Mapping | bytes):
        return []
    return list(dict.fromkeys(text for item in value if (text := _text(item)) is not None))


__all__ = ["ACTION_TYPE", "action_payload"]
