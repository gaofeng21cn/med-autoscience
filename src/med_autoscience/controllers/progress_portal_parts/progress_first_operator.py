from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


def build_progress_first_operator_projection(progress: Mapping[str, Any] | None) -> dict[str, Any]:
    payload = _mapping(progress)
    monitoring = _mapping(payload.get("progress_first_monitoring_summary"))
    sprint_state = _mapping(payload.get("progress_first_sprint_state"))
    next_forced_delta = _mapping(monitoring.get("next_forced_delta")) or _mapping(payload.get("next_forced_delta"))
    deliverable_delta = _mapping(
        payload.get("deliverable_progress_delta")
        or sprint_state.get("deliverable_progress_delta")
        or payload.get("paper_progress_delta")
        or sprint_state.get("paper_progress_delta")
    )
    paper_delta = _mapping(
        payload.get("paper_progress_delta")
        or sprint_state.get("paper_progress_delta")
        or deliverable_delta
    )
    platform_delta = _mapping(payload.get("platform_repair_delta") or sprint_state.get("platform_repair_delta"))
    classification = (
        _non_empty_text(monitoring.get("progress_delta_classification"))
        or _non_empty_text(payload.get("progress_delta_classification"))
        or _non_empty_text(sprint_state.get("classification"))
    )
    status = "available" if next_forced_delta or classification or deliverable_delta or paper_delta or platform_delta else "pending"
    return {
        "surface_kind": "mas_progress_first_operator_projection",
        "schema_version": 1,
        "status": status,
        "progress_delta_classification": classification,
        "paper_progress_delta_counted": _bool_from_any(
            monitoring.get("paper_progress_delta_counted"),
            sprint_state.get("paper_progress_delta_counted"),
            default=_delta_count(paper_delta) > 0,
        ),
        "platform_repair_delta_counted": _bool_from_any(
            monitoring.get("platform_repair_delta_counted"),
            sprint_state.get("platform_repair_delta_counted"),
            default=_delta_count(platform_delta) > 0,
        ),
        "deliverable_progress_delta": deliverable_delta,
        "paper_progress_delta": paper_delta,
        "platform_repair_delta": platform_delta,
        "platform_repair_is_deliverable_progress": False,
        "next_forced_delta": _compact_mapping(
            next_forced_delta,
            (
                "required_delta_kind",
                "reason",
                "work_unit_id",
                "eval_id",
                "next_owner",
                "allowed_outcomes",
                "target_surface",
                "target_surface_specificity",
                "missing_explicit_target_surface",
                "target_surface_fallback_reason",
                "target_surface_diagnostic",
                "acceptance_refs",
                "owner_action",
            ),
        ),
        "source_refs": _dedupe_refs(
            [
                *_string_list(monitoring.get("source_refs")),
                *_string_list(payload.get("source_refs")),
                *_string_list(sprint_state.get("source_refs")),
            ]
        ),
        "authority": {
            "writes_authority_surface": False,
            "display_and_drilldown_only": True,
            "can_authorize_publication_readiness": False,
            "can_authorize_quality_verdict": False,
        },
    }


def render_progress_first_operator_section(projection: Mapping[str, Any]) -> str:
    from .rendering import list_html, status_chip
    from .status_display import display_text

    next_forced_delta = _mapping(projection.get("next_forced_delta"))
    target_surface = _mapping(next_forced_delta.get("target_surface"))
    owner_action = _mapping(next_forced_delta.get("owner_action"))
    items = [
        f"classification={display_text(projection.get('progress_delta_classification'), empty_text='missing', preserve_known_token=True)}",
        f"paper_progress_delta={_delta_count(_mapping(projection.get('paper_progress_delta')))}",
        f"deliverable_progress_delta={_delta_count(_mapping(projection.get('deliverable_progress_delta')))}",
        f"platform_repair_delta={_delta_count(_mapping(projection.get('platform_repair_delta')))}",
        f"required_delta_kind={display_text(next_forced_delta.get('required_delta_kind'), empty_text='missing', preserve_known_token=True)}",
        f"target_surface={display_text(target_surface.get('surface_ref'), empty_text='missing', preserve_known_token=True)}",
        f"next_owner={display_text(owner_action.get('next_owner'), empty_text='missing', preserve_known_token=True)}",
    ]
    return (
        '<section class="panel wide"><h2>Progress-First '
        + status_chip(projection.get("status") or "pending")
        + "</h2>"
        + list_html(items, empty_text="缺少 Progress-First operator projection。")
        + "</section>"
    )


def _compact_mapping(value: Mapping[str, Any], keys: Iterable[str]) -> dict[str, Any]:
    return {key: value[key] for key in keys if key in value and value[key] not in (None, "", [], {})}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_list(value: object) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _dedupe_refs(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = _non_empty_text(value)
        if text is not None and text not in result:
            result.append(text)
    return result


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _delta_count(value: Mapping[str, Any]) -> int:
    try:
        return int(value.get("count") or 0)
    except (TypeError, ValueError):
        return 0


def _bool_from_any(*values: object, default: bool) -> bool:
    for value in values:
        if isinstance(value, bool):
            return value
    return default


__all__ = [
    "build_progress_first_operator_projection",
    "render_progress_first_operator_section",
]
