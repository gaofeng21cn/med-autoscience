from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def runtime_controller_event_refs(*, root: Path) -> list[str]:
    refs: list[str] = []
    paths = (
        root / "artifacts" / "controller" / "latest.json",
        root / "artifacts" / "controller_decisions" / "latest.json",
        root / "artifacts" / "publication_eval" / "latest.json",
        root / "artifacts" / "supervision" / "hourly" / "latest.json",
    )
    for path in paths:
        payload = read_json_object(path)
        refs.extend(
            refs_for_keys(
                payloads=[payload],
                keys=(
                    "runtime_event_refs",
                    "event_refs",
                    "controller_event_refs",
                    "supervision_event_refs",
                    "receipt_refs",
                ),
            )
        )
    return unique_refs(refs)


def analysis_queue_items(
    *,
    payloads: list[dict[str, Any]],
    study_id: str,
    manifest_refs: list[str],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for payload in payloads:
        for key in ("items", "queue_items", "analysis_items"):
            values = payload.get(key)
            if not isinstance(values, list):
                continue
            for item in values:
                normalized = _analysis_queue_item(item, default_state=text(payload.get("state")))
                if normalized:
                    items.append(normalized)
    if items:
        return _unique_items(items)
    return [
        {
            "ref": f"analysis-queue-item:mas/{study_id}/medical-manuscript-quality-blocked",
            "state": "blocked",
            "retry_count": 0,
            "budget_cost": 0,
            "source_refs": manifest_refs
            or [f"analysis-queue-missing:mas/{study_id}/medical-manuscript-quality"],
        }
    ]


def refs_from_value(values: object) -> list[str]:
    if isinstance(values, Mapping):
        ref = _item_ref(values)
        refs = [ref] if ref else []
        for key in ("refs", "items", "events", "claims", "evidence"):
            refs.extend(refs_from_value(values.get(key)))
        return unique_refs(refs)
    if not isinstance(values, list):
        ref = text(values)
        return [ref] if ref and ":" in ref else []
    refs: list[str] = []
    for item in values:
        if isinstance(item, Mapping):
            ref = _item_ref(item)
            if ref:
                refs.append(ref)
            for key in ("refs", "source_refs", "evidence_refs", "review_refs", "display_refs"):
                refs.extend(refs_from_value(item.get(key)))
        else:
            ref = text(item)
            if ref:
                refs.append(ref)
    return refs


def refs_for_keys(*, payloads: list[dict[str, Any]], keys: tuple[str, ...]) -> list[str]:
    refs: list[str] = []
    for payload in payloads:
        for key in keys:
            refs.extend(refs_from_value(payload.get(key)))
    return unique_refs(refs)


def first_text(payloads: list[dict[str, Any]], *keys: str) -> str:
    for payload in payloads:
        for key in keys:
            value = text(payload.get(key))
            if value:
                return value
    return ""


def first_mapping(payloads: list[dict[str, Any]], key: str) -> dict[str, Any]:
    for payload in payloads:
        value = payload.get(key)
        if isinstance(value, Mapping):
            return dict(value)
        value_text = text(value)
        if value_text:
            return {"policy_ref": value_text} if key == "retry_policy" else {"ref": value_text}
    return {}


def unique_refs(refs: list[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for ref in refs:
        if not ref or ref in seen:
            continue
        seen.add(ref)
        unique.append(ref)
    return unique


def quality_dimension(publication_eval: Mapping[str, Any], dimension: str) -> dict[str, Any]:
    quality = publication_eval.get("quality_assessment")
    if not isinstance(quality, Mapping):
        return {}
    item = quality.get(dimension)
    return dict(item) if isinstance(item, Mapping) else {}


def existing_refs(*paths: Path) -> list[str]:
    refs: list[str] = []
    seen: set[str] = set()
    for path in paths:
        if not path.exists():
            continue
        ref = str(path)
        if ref in seen:
            continue
        seen.add(ref)
        refs.append(ref)
    return refs


def read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def jsonl_count(path: Path) -> int:
    try:
        with path.open(encoding="utf-8") as handle:
            return sum(1 for line in handle if line.strip())
    except OSError:
        return 0


def jsonl_event_types(paths: tuple[Path, ...]) -> list[str]:
    event_types: list[str] = []
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(payload, Mapping):
                continue
            event_type = text(
                payload.get("event_type")
                or payload.get("type")
                or payload.get("kind")
                or payload.get("event_kind")
            )
            if event_type:
                event_types.append(event_type)
    return unique_refs(event_types)


def text(value: object) -> str:
    return str(value or "").strip()


def _analysis_queue_item(item: object, *, default_state: str) -> dict[str, Any] | None:
    if isinstance(item, Mapping):
        ref = _item_ref(item)
        if not ref:
            return None
        return {
            "ref": ref,
            "state": text(item.get("state") or item.get("status")) or default_state or "blocked",
            "retry_count": _int(item.get("retry_count"), default=0),
            "budget_cost": item.get("budget_cost", item.get("cost", 0)),
            "source_refs": refs_from_value(item.get("source_refs")),
        }
    ref = text(item)
    if not ref:
        return None
    return {
        "ref": ref,
        "state": default_state or "blocked",
        "retry_count": 0,
        "budget_cost": 0,
        "source_refs": [],
    }


def _item_ref(item: Mapping[str, Any]) -> str:
    for key in (
        "ref",
        "id",
        "route_ref",
        "paper_ref",
        "claim_ref",
        "experiment_ref",
        "idea_ref",
        "failed_idea_ref",
        "negative_result_ref",
        "rationale_ref",
        "queue_ref",
        "event_ref",
        "provider_ref",
        "executor_ref",
        "context_ref",
        "evidence_ref",
        "review_ref",
        "display_ref",
        "table_ref",
        "figure_ref",
    ):
        ref = text(item.get(key))
        if ref:
            return ref
    return ""


def _unique_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        ref = text(item.get("ref"))
        if not ref or ref in seen:
            continue
        seen.add(ref)
        unique.append(item)
    return unique


def _int(value: object, *, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default
