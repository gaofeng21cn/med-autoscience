from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


SURFACE = "ai_first_action_dispatch_ledger"
SCHEMA_VERSION = 1
AUTHORITY = "operations_governance_only"
VALID_STATUSES = frozenset({"open", "accepted", "in_progress", "closed", "blocked"})
ACTIVE_STATUSES = frozenset({"open", "accepted", "in_progress", "blocked"})
LIFECYCLE_ORDER = ("blocked", "in_progress", "accepted", "open", "closed")
LOW_LEVEL_FIELD_HINTS = ("raw_terminal_log", "full_prompt", "prompt", "secret", "token", "log_path")


def _text(value: object, default: str | None = None) -> str | None:
    text = str(value or "").strip()
    return text or default


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _safe_key(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in value.strip())
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_")[:96] or "action"


def _redacted_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in value.items():
        key_text = str(key)
        if any(hint in key_text.lower() for hint in LOW_LEVEL_FIELD_HINTS):
            continue
        if isinstance(item, Mapping):
            result[key_text] = _redacted_mapping(item)
        elif isinstance(item, list):
            result[key_text] = [
                _redacted_mapping(entry) if isinstance(entry, Mapping) else entry
                for entry in item
            ]
        else:
            result[key_text] = item
    return result


def stable_action_dispatch_ledger_path(*, study_root: str | Path) -> Path:
    return (
        Path(study_root).expanduser().resolve()
        / "artifacts"
        / "runtime"
        / "ai_first_action_dispatch_ledger"
        / "latest.json"
    )


def read_action_dispatch_ledger(*, study_root: str | Path) -> dict[str, Any] | None:
    path = stable_action_dispatch_ledger_path(study_root=study_root)
    if not path.exists() or not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _dispatch_key(*, source_feedback_key: str, action_id: str, target_surface: str) -> str:
    return f"{_safe_key(source_feedback_key)}::{_safe_key(action_id)}::{_safe_key(target_surface)}"


def _event_action(feedback_event: Mapping[str, Any]) -> Mapping[str, Any]:
    return _mapping(feedback_event.get("action_recommendation"))


def _build_dispatch_record(
    *,
    feedback_event: Mapping[str, Any],
    owner: str,
    status: str,
    observed_at: str,
    closure_evidence: list[str] | None,
) -> dict[str, Any]:
    action = _event_action(feedback_event)
    action_id = _text(action.get("action_id"), "inspect_feedback_signal") or "inspect_feedback_signal"
    target_surface = _text(action.get("target_surface"), "ai_first_feedback_state") or "ai_first_feedback_state"
    source_feedback_key = _text(feedback_event.get("event_key")) or _text(feedback_event.get("category"), "feedback")
    source_feedback_key = source_feedback_key or "feedback"
    record = {
        "dispatch_key": _dispatch_key(
            source_feedback_key=source_feedback_key,
            action_id=action_id,
            target_surface=target_surface,
        ),
        "action_category": _text(feedback_event.get("category"), "unknown") or "unknown",
        "source_feedback_key": source_feedback_key,
        "source_surface": _text(feedback_event.get("source_surface"), "ai_first_feedback_state")
        or "ai_first_feedback_state",
        "target_surface": target_surface,
        "action_id": action_id,
        "summary": _text(action.get("summary")) or _text(feedback_event.get("next_action")),
        "dispatch_owner": owner,
        "status": status,
        "created_at": observed_at,
        "updated_at": observed_at,
        "closure_evidence": closure_evidence or [],
        "authority": AUTHORITY,
        "authority_contract": _authority_contract(),
    }
    return _redacted_mapping(record)


def _authority_contract() -> dict[str, bool]:
    return {
        "dispatch_can_authorize_quality": False,
        "dispatch_can_authorize_finalize": False,
        "dispatch_can_authorize_submission": False,
        "dispatch_can_mutate_runtime": False,
        "dispatch_records_manuscript_content": False,
    }


def _normalize_status(*, status: str, closure_evidence: list[str] | None) -> str:
    normalized = status.strip().lower()
    if normalized not in VALID_STATUSES:
        raise ValueError(f"invalid action dispatch status: {status}")
    if normalized == "closed" and not closure_evidence:
        raise ValueError("closed action dispatch requires closure_evidence")
    return normalized


def _merge_records(
    *,
    existing_records: list[Mapping[str, Any]],
    new_records: list[Mapping[str, Any]],
    observed_at: str,
) -> list[dict[str, Any]]:
    by_key = {
        str(item.get("dispatch_key")): dict(item)
        for item in existing_records
        if _text(item.get("dispatch_key"))
    }
    merged: list[dict[str, Any]] = []
    for record in new_records:
        key = str(record.get("dispatch_key"))
        prior = by_key.pop(key, None)
        item = dict(record)
        if prior:
            item["created_at"] = prior.get("created_at") or item["created_at"]
            prior_status = _text(prior.get("status"))
            if item.get("status") == "open" and prior_status in VALID_STATUSES:
                item["status"] = prior_status
            for preserved_key in ("closure_evidence", "summary"):
                if item.get("status") != "closed" and preserved_key == "closure_evidence":
                    item[preserved_key] = prior.get(preserved_key) or item.get(preserved_key) or []
                elif preserved_key in prior:
                    item[preserved_key] = prior[preserved_key]
        item["updated_at"] = observed_at
        merged.append(item)
    merged.extend(dict(item) for item in by_key.values())
    return sorted(merged, key=lambda item: str(item.get("dispatch_key") or ""))


def build_action_dispatch_projection(
    *,
    feedback_state: Mapping[str, Any],
    existing_ledger: Mapping[str, Any] | None = None,
    dispatch_owner: str = "mas_operator",
    status: str = "open",
    observed_at: str | None = None,
    closure_evidence: list[str] | None = None,
) -> dict[str, Any]:
    observed = observed_at or _utc_now()
    normalized_status = _normalize_status(status=status, closure_evidence=closure_evidence)
    records = [
        _build_dispatch_record(
            feedback_event=event,
            owner=dispatch_owner,
            status=normalized_status,
            observed_at=observed,
            closure_evidence=closure_evidence,
        )
        for event in _list(feedback_state.get("events"))
        if isinstance(event, Mapping) and _event_action(event)
    ]
    existing_records = [
        item
        for item in _list((existing_ledger or {}).get("dispatches"))
        if isinstance(item, Mapping)
    ]
    dispatches = _merge_records(
        existing_records=existing_records,
        new_records=records,
        observed_at=observed,
    )
    counts = {
        "open": sum(1 for item in dispatches if item.get("status") == "open"),
        "accepted": sum(1 for item in dispatches if item.get("status") == "accepted"),
        "in_progress": sum(1 for item in dispatches if item.get("status") == "in_progress"),
        "blocked": sum(1 for item in dispatches if item.get("status") == "blocked"),
        "closed": sum(1 for item in dispatches if item.get("status") == "closed"),
        "total": len(dispatches),
    }
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "authority": AUTHORITY,
        "updated_at": observed,
        "dispatches": dispatches,
        "counts": counts,
        "user_view": {
            "open_action_count": counts["open"]
            + counts["accepted"]
            + counts["in_progress"]
            + counts["blocked"],
            "closed_action_count": counts["closed"],
            "next_action": _text((dispatches[0] if dispatches else {}).get("summary")),
        },
        "maintainer_view": {
            "dispatches": dispatches,
            "dispatch_owner": dispatch_owner,
        },
        "authority_contract": _authority_contract(),
    }


def materialize_action_dispatch_ledger(
    *,
    study_root: str | Path,
    feedback_state: Mapping[str, Any],
    dispatch_owner: str = "mas_operator",
    status: str = "open",
    observed_at: str | None = None,
    closure_evidence: list[str] | None = None,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    path = stable_action_dispatch_ledger_path(study_root=resolved_study_root)
    existing = read_action_dispatch_ledger(study_root=resolved_study_root)
    projection = build_action_dispatch_projection(
        feedback_state=feedback_state,
        existing_ledger=existing,
        dispatch_owner=dispatch_owner,
        status=status,
        observed_at=observed_at,
        closure_evidence=closure_evidence,
    )
    payload = {
        **projection,
        "study_root": str(resolved_study_root),
        "path": str(path),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def _lifecycle_counts(dispatches: list[Mapping[str, Any]]) -> dict[str, int]:
    counts = {status: 0 for status in (*LIFECYCLE_ORDER, "total", "active")}
    counts["total"] = len(dispatches)
    for item in dispatches:
        status = _text(item.get("status"), "open") or "open"
        if status not in VALID_STATUSES:
            status = "open"
        counts[status] += 1
        if status in ACTIVE_STATUSES:
            counts["active"] += 1
    return counts


def _primary_dispatch(dispatches: list[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    for status in LIFECYCLE_ORDER:
        for item in dispatches:
            if item.get("status") == status:
                return item
    return None


def _restore_existing_lifecycle(
    *,
    dispatches: list[Mapping[str, Any]],
    existing_ledger: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    existing_by_key = {
        str(item.get("dispatch_key")): item
        for item in _list((existing_ledger or {}).get("dispatches"))
        if isinstance(item, Mapping) and _text(item.get("dispatch_key"))
    }
    restored: list[dict[str, Any]] = []
    for item in dispatches:
        updated = dict(item)
        prior = existing_by_key.get(str(item.get("dispatch_key")))
        if prior:
            status = _text(prior.get("status"))
            if status in VALID_STATUSES:
                updated["status"] = status
            for key in ("created_at", "updated_at", "closure_evidence", "summary"):
                if key in prior:
                    updated[key] = prior[key]
        restored.append(_redacted_mapping(updated))
    return restored


def build_operator_action_lifecycle(
    *,
    feedback_state: Mapping[str, Any],
    existing_ledger: Mapping[str, Any] | None = None,
    dispatch_owner: str = "mas_operator",
    observed_at: str | None = None,
) -> dict[str, Any]:
    projection = build_action_dispatch_projection(
        feedback_state=feedback_state,
        existing_ledger=existing_ledger,
        dispatch_owner=dispatch_owner,
        status="open",
        observed_at=observed_at,
    )
    dispatches = [
        dict(item)
        for item in _list(projection.get("dispatches"))
        if isinstance(item, Mapping)
    ]
    dispatches = _restore_existing_lifecycle(
        dispatches=dispatches,
        existing_ledger=existing_ledger,
    )
    counts = _lifecycle_counts(dispatches)
    primary = dict(_primary_dispatch(dispatches) or {})
    primary_status = _text(primary.get("status"), "open") or "open"
    next_step = _text(primary.get("summary")) or _text(
        (_mapping(feedback_state.get("user_view"))).get("next_action")
    )
    blocked = primary_status == "blocked" or counts["blocked"] > 0
    return {
        "surface": "ai_first_action_dispatch_lifecycle",
        "schema_version": 1,
        "authority": AUTHORITY,
        "read_model": "operator_action_lifecycle_read_model",
        "updated_at": projection.get("updated_at"),
        "status": "blocked" if blocked else ("open" if counts["active"] else "closed"),
        "counts": counts,
        "primary_action": {
            "dispatch_key": primary.get("dispatch_key"),
            "action_id": primary.get("action_id"),
            "summary": next_step,
            "target_surface": primary.get("target_surface"),
            "status": primary_status if primary else None,
            "source_feedback_key": primary.get("source_feedback_key"),
        }
        if primary
        else None,
        "user_view": {
            "current_blocker": next_step if blocked else None,
            "next_step": next_step,
            "human_review_required": bool(
                _mapping(feedback_state.get("user_view")).get("human_review_required")
            ),
            "primary_action_status": primary_status if primary else None,
            "active_action_count": counts["active"],
        },
        "maintainer_view": {
            "dispatches": dispatches,
            "source_ledger_surface": (existing_ledger or {}).get("surface"),
        },
        "authority_contract": _authority_contract(),
    }
