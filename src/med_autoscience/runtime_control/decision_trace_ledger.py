from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


DECISION_TRACE_KEYS = (
    "decision_trace",
    "decision_trace_ledger",
    "route_decision_trace",
    "route_trace",
)
FAILED_PATH_KEYS = (
    "failed_path_ledger",
    "failed_paths",
    "negative_result_ledger",
    "negative_results",
    "failed_attempts",
)
DECISION_TRACE_REF_KEYS = (
    "decision_trace_refs",
    "decision_refs",
    "route_decision_refs",
    "controller_decision_refs",
)
FAILED_PATH_REF_KEYS = (
    "failed_path_refs",
    "negative_result_refs",
    "failed_attempt_refs",
)
CONSUMED_FAILED_PATH_REF_KEYS = (
    "consumed_failed_path_refs",
    "consumed_refs",
)


def decision_trace_projection(*payloads: Mapping[str, Any]) -> dict[str, Any]:
    decision_refs: list[str] = []
    failed_refs: list[str] = []
    consumed_refs: list[str] = []
    decision_summary: str | None = None
    failed_summary: str | None = None
    repeated_failed_path_suppressed = False

    for payload in payloads:
        if not isinstance(payload, Mapping):
            continue
        decision_summary = decision_summary or _summary(payload)
        decision_refs.extend(_refs_for_keys(payload, DECISION_TRACE_REF_KEYS))
        failed_refs.extend(_refs_for_keys(payload, FAILED_PATH_REF_KEYS))
        consumed_refs.extend(_refs_for_keys(payload, CONSUMED_FAILED_PATH_REF_KEYS))

        source_refs = _mapping(payload.get("source_refs"))
        if source_refs:
            decision_refs.extend(_refs_for_keys(source_refs, DECISION_TRACE_REF_KEYS))
            failed_refs.extend(_refs_for_keys(source_refs, FAILED_PATH_REF_KEYS))
            consumed_refs.extend(_refs_for_keys(source_refs, CONSUMED_FAILED_PATH_REF_KEYS))

        for key in DECISION_TRACE_KEYS:
            surface = _mapping(payload.get(key))
            if not surface:
                continue
            decision_summary = decision_summary or _summary(surface)
            refs = _refs_from_field(surface.get("refs") or surface.get("source_refs") or surface.get("receipt_refs"))
            for ref, role in refs:
                if role == "failed_path" or _looks_like_failed_path_ref(ref):
                    failed_refs.append(ref)
                else:
                    decision_refs.append(ref)
            decision_refs.extend(_refs_for_keys(surface, DECISION_TRACE_REF_KEYS))
            failed_refs.extend(_refs_for_keys(surface, FAILED_PATH_REF_KEYS))
            consumed_refs.extend(_refs_for_keys(surface, CONSUMED_FAILED_PATH_REF_KEYS))
            repeated_failed_path_suppressed = repeated_failed_path_suppressed or bool(
                surface.get("repeated_failed_path_suppressed")
            )

        for key in FAILED_PATH_KEYS:
            surface = _mapping(payload.get(key))
            if not surface:
                continue
            failed_summary = failed_summary or _summary(surface)
            failed_refs.extend(ref for ref, _role in _refs_from_field(surface.get("refs") or surface.get("source_refs")))
            failed_refs.extend(_refs_for_keys(surface, FAILED_PATH_REF_KEYS))
            consumed_refs.extend(_refs_for_keys(surface, CONSUMED_FAILED_PATH_REF_KEYS))
            repeated_failed_path_suppressed = repeated_failed_path_suppressed or bool(
                surface.get("repeated_failed_path_suppressed")
            )

    decision_refs = _unique_texts(decision_refs)
    failed_refs = _unique_texts(failed_refs)
    consumed_refs = _unique_texts(consumed_refs)
    projection: dict[str, Any] = {}
    if decision_summary or decision_refs:
        projection["decision_trace"] = {
            "surface_kind": "mas_decision_trace_refs_projection",
            "summary": decision_summary,
            "refs": decision_refs,
            "body_included": False,
            "route_authority": False,
        }
        projection["decision_trace_refs"] = decision_refs
    if failed_summary or failed_refs or consumed_refs:
        projection["failed_path_ledger"] = {
            "surface_kind": "mas_failed_path_refs_projection",
            "summary": failed_summary,
            "refs": failed_refs,
            "consumed_refs": consumed_refs,
            "body_included": False,
            "route_authority": False,
        }
        projection["failed_path_refs"] = failed_refs
        projection["consumed_failed_path_refs"] = consumed_refs
    if repeated_failed_path_suppressed:
        projection["repeated_failed_path_suppressed"] = True
    return projection


def repeated_failed_path_suppressed(
    *,
    actions: Iterable[Mapping[str, Any]],
    trace_projection: Mapping[str, Any],
) -> bool:
    recorded_refs = set(_text_items(trace_projection.get("failed_path_refs")))
    recorded_refs.update(_text_items(trace_projection.get("consumed_failed_path_refs")))
    if not recorded_refs:
        return False
    return any(
        bool(recorded_refs.intersection(_refs_consumed_by_action(action)))
        for action in actions
        if isinstance(action, Mapping)
    )


def filter_actions_consuming_recorded_failed_paths(
    *,
    actions: Iterable[Mapping[str, Any]],
    trace_projection: Mapping[str, Any],
) -> list[dict[str, Any]]:
    recorded_refs = set(_text_items(trace_projection.get("failed_path_refs")))
    recorded_refs.update(_text_items(trace_projection.get("consumed_failed_path_refs")))
    filtered: list[dict[str, Any]] = []
    for action in actions:
        payload = dict(action)
        consumed = _refs_consumed_by_action(payload)
        if consumed and recorded_refs.intersection(consumed):
            continue
        filtered.append(payload)
    return filtered


def _refs_consumed_by_action(action: Mapping[str, Any]) -> set[str]:
    refs: set[str] = set()
    for key in (
        "consumes_failed_path_refs",
        "consumed_failed_path_refs",
        "failed_path_refs",
    ):
        refs.update(_text_items(action.get(key)))
    return refs


def _refs_for_keys(payload: Mapping[str, Any], keys: Iterable[str]) -> list[str]:
    refs: list[str] = []
    for key in keys:
        refs.extend(ref for ref, _role in _refs_from_field(payload.get(key)))
    return refs


def _refs_from_field(value: object) -> list[tuple[str, str | None]]:
    refs: list[tuple[str, str | None]] = []
    if isinstance(value, str):
        text = _text(value)
        return [(text, None)] if text else []
    if isinstance(value, Mapping):
        ref = _text(value.get("ref")) or _text(value.get("path")) or _text(value.get("artifact_path"))
        role = _text(value.get("role")) or _text(value.get("ref_role"))
        if ref:
            refs.append((ref, role))
        for key, item in value.items():
            if key in {"body", "content", "payload", "entries", "ref", "path", "artifact_path", "role", "ref_role"}:
                continue
            if str(key).endswith("refs") or str(key).endswith("ref") or str(key).endswith("path"):
                refs.extend(_refs_from_field(item))
        return refs
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes, Mapping)):
        for item in value:
            refs.extend(_refs_from_field(item))
    return refs


def _summary(payload: Mapping[str, Any]) -> str | None:
    for key in (
        "summary",
        "decision_summary",
        "route_summary",
        "failed_path_summary",
        "reason",
    ):
        if text := _text(payload.get(key)):
            return text
    return None


def _looks_like_failed_path_ref(ref: str) -> bool:
    return "failed_path" in ref or "failed-path" in ref


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text_items(value: object) -> list[str]:
    return [ref for ref, _role in _refs_from_field(value)]


def _unique_texts(values: Iterable[object]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = _text(value)
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "decision_trace_projection",
    "filter_actions_consuming_recorded_failed_paths",
    "repeated_failed_path_suppressed",
]
