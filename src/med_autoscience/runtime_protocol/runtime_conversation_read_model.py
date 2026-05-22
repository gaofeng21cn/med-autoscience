from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol import live_console_read_model_io as io
from med_autoscience.runtime_protocol.runtime_live_console_read_model import (
    build_live_console_session_read_model,
)


SCHEMA_VERSION = 1
SURFACE_KIND = "mas_runtime_conversation_read_model"
OWNER = "MedAutoScience"
CONVERSATION_READ_MODEL_REF = "artifacts/runtime/conversation_read_model/latest.json"
CONVERSATION_READ_MODEL_HISTORY_REF = "artifacts/runtime/conversation_read_model/history.jsonl"
JSONL_TAIL_READ_BYTES = 1_048_576
JSONL_MAX_ITEMS = 200


def build_conversation_read_model(
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    study_id: str | None = None,
    study_root: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated = io.text(generated_at) or _utc_now()
    selected_study_id, selected_study_root = _resolve_selection(profile=profile, study_id=study_id, study_root=study_root)
    contexts = _study_contexts(
        profile=profile,
        selected_study_id=selected_study_id,
        selected_study_root=selected_study_root,
    )
    live_console = _live_console_session_model(
        profile=profile,
        profile_ref=profile_ref,
        selected_study_id=selected_study_id,
        selected_study_root=selected_study_root,
        generated_at=generated,
    )
    timeline = _timeline(contexts=contexts, live_console=live_console)
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": SURFACE_KIND,
        "owner": OWNER,
        "generated_at": generated,
        "read_only": True,
        "authority": _authority(),
        "workspace": {
            "profile_name": profile.name,
            "workspace_root": str(profile.workspace_root),
            "profile_ref": str(profile_ref) if profile_ref is not None else None,
        },
        "selected_study_id": selected_study_id,
        "studies": [_study_projection(context) for context in contexts],
        "timeline": timeline,
        "timeline_summary": _timeline_summary(timeline),
        "source_refs": _source_refs(contexts=contexts, live_console=live_console),
    }


def materialize_conversation_read_model(
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    study_id: str | None = None,
    study_root: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    payload = build_conversation_read_model(
        profile,
        profile_ref=profile_ref,
        study_id=study_id,
        study_root=study_root,
        generated_at=generated_at,
    )
    latest_path = (profile.workspace_root / CONVERSATION_READ_MODEL_REF).resolve()
    history_path = (profile.workspace_root / CONVERSATION_READ_MODEL_HISTORY_REF).resolve()
    io.write_json(latest_path, payload)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    return {
        "status": "materialized",
        "surface_kind": SURFACE_KIND,
        "read_only": True,
        "payload_path": str(latest_path),
        "read_model_ref": str(latest_path),
        "history_path": str(history_path),
        "conversation_read_model": payload,
        "generated_at": payload["generated_at"],
    }


def _authority() -> dict[str, Any]:
    return {
        "kind": "read_only_runtime_conversation_projection",
        "mode": "read_only",
        "writes_authority_surface": False,
        "can_write_paper_or_package": False,
        "can_write_publication_eval": False,
        "can_write_controller_decisions": False,
        "can_write_runtime_sqlite_authority": False,
        "can_execute_controller_actions": False,
        "authority_surfaces_not_written": [
            "paper",
            "package",
            "publication_eval/latest.json",
            "controller_decisions/latest.json",
            "runtime_lifecycle.sqlite",
            "runtime_lifecycle refs indexes",
        ],
    }


def _resolve_selection(
    *,
    profile: WorkspaceProfile,
    study_id: str | None,
    study_root: str | Path | None,
) -> tuple[str | None, Path | None]:
    if io.text(study_id) and study_root is not None:
        raise ValueError("Specify only one of study_id or study_root")
    if study_root is not None:
        root = Path(study_root).expanduser().resolve()
        return root.name, root
    selected = io.text(study_id) or None
    return selected, (profile.studies_root / selected).expanduser().resolve() if selected else None


def _study_contexts(
    *,
    profile: WorkspaceProfile,
    selected_study_id: str | None,
    selected_study_root: Path | None,
) -> list[dict[str, Any]]:
    roots = _discover_study_roots(profile)
    if selected_study_root is not None and selected_study_root not in roots:
        roots.append(selected_study_root)
    contexts = [_study_context(profile=profile, study_root=root) for root in sorted(set(roots))]
    if selected_study_id is None:
        return contexts
    selected = [context for context in contexts if context["study_id"] == selected_study_id]
    others = [context for context in contexts if context["study_id"] != selected_study_id]
    return [*selected, *others] if selected else contexts


def _discover_study_roots(profile: WorkspaceProfile) -> list[Path]:
    studies_root = profile.studies_root.expanduser().resolve()
    if not studies_root.exists():
        return []
    return [path.resolve() for path in studies_root.iterdir() if path.is_dir() and (path / "study.yaml").exists()]


def _study_context(*, profile: WorkspaceProfile, study_root: Path) -> dict[str, Any]:
    progress_projection_path, progress_projection = io.read_first_json(
        (
            study_root / "artifacts" / "runtime" / "progress_projection" / "latest.json",
            study_root / "artifacts" / "runtime" / "status" / "latest.json",
            study_root / "artifacts" / "runtime" / "status.json",
        )
    )
    summary_path, summary = io.read_first_json((study_root / "artifacts" / "runtime" / "runtime_status_summary.json",))
    health_path, health = io.read_first_json((study_root / "artifacts" / "runtime" / "health" / "latest.json",))
    supervision_path, supervision = io.read_first_json(
        (study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",)
    )
    quest_root = _quest_root(profile=profile, progress_projection=progress_projection, summary=summary, study_root=study_root)
    quest_sources = _quest_sources(quest_root)
    return {
        "study_id": io.first_text(
            progress_projection.get("study_id"),
            summary.get("study_id"),
            health.get("study_id"),
            supervision.get("study_id"),
            study_root.name,
        ),
        "study_root": study_root.resolve(),
        "quest_root": quest_root,
        "surfaces": {
            "progress_projection": {"path": progress_projection_path, "payload": progress_projection},
            "runtime_status_summary": {"path": summary_path, "payload": summary},
            "runtime_health": {"path": health_path, "payload": health},
            "runtime_supervision": {"path": supervision_path, "payload": supervision},
            **quest_sources,
        },
    }


def _quest_root(
    *,
    profile: WorkspaceProfile,
    progress_projection: Mapping[str, Any],
    summary: Mapping[str, Any],
    study_root: Path,
) -> Path | None:
    for value in (progress_projection.get("quest_root"), summary.get("quest_root")):
        candidate_text = io.text(value)
        if candidate_text:
            return Path(candidate_text).expanduser().resolve()
    quest_id = io.first_text(progress_projection.get("quest_id"), summary.get("quest_id"))
    if quest_id:
        return (profile.runtime_root / quest_id).expanduser().resolve()
    candidate = (profile.runtime_root / study_root.name).expanduser().resolve()
    return candidate if candidate.exists() else None


def _quest_sources(quest_root: Path | None) -> dict[str, dict[str, Any]]:
    if quest_root is None:
        return {}
    return {
        "runtime_state": _read_json_source(quest_root / ".ds" / "runtime_state.json"),
        "user_message_queue": _read_json_source(quest_root / "artifacts" / "runtime" / "user_message_queue.json"),
        "user_messages_jsonl": _read_jsonl_source(quest_root / "artifacts" / "runtime" / "user_messages.jsonl"),
        "turn_receipts_jsonl": _read_jsonl_source(quest_root / "artifacts" / "runtime" / "turn_receipts.jsonl"),
        "latest_turn_receipt": _read_json_source(quest_root / "artifacts" / "runtime" / "latest_turn_receipt.json"),
        "runtime_events_jsonl": _read_jsonl_source(quest_root / "artifacts" / "runtime" / "mas_runtime_events.jsonl"),
    }


def _read_json_source(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"path": None, "payload": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"path": path.resolve(), "payload": {}, "parse_error": f"{type(exc).__name__}: {exc}"}
    return {"path": path.resolve(), "payload": dict(payload) if isinstance(payload, Mapping) else {}}


def _read_jsonl_source(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"path": None, "items": []}
    items: list[dict[str, Any]] = []
    parse_errors: list[dict[str, Any]] = []
    lines, metadata = _read_jsonl_tail(path)
    total_lines = metadata.pop("line_count", None)
    start_line_number = int(total_lines or 0) - len(lines) + 1 if total_lines is not None else 1
    for offset, line in enumerate(lines):
        line_number = start_line_number + offset
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            parse_errors.append({"line_number": line_number, "error": f"JSONDecodeError: {exc}"})
            continue
        if isinstance(payload, Mapping):
            items.append(dict(payload))
        else:
            parse_errors.append({"line_number": line_number, "error": "jsonl line is not an object"})
    if len(items) > JSONL_MAX_ITEMS:
        items = items[-JSONL_MAX_ITEMS:]
        metadata["items_truncated"] = True
        metadata["max_items"] = JSONL_MAX_ITEMS
    result: dict[str, Any] = {"path": path.resolve(), "items": items, **metadata}
    if parse_errors:
        result["parse_errors"] = parse_errors
    return result


def _read_jsonl_tail(path: Path) -> tuple[list[str], dict[str, Any]]:
    size_bytes = path.stat().st_size
    if size_bytes <= JSONL_TAIL_READ_BYTES:
        return path.read_text(encoding="utf-8", errors="replace").splitlines(), {
            "truncated": False,
            "size_bytes": size_bytes,
            "bytes_read": size_bytes,
        }
    with path.open("rb") as handle:
        handle.seek(-JSONL_TAIL_READ_BYTES, 2)
        data = handle.read(JSONL_TAIL_READ_BYTES)
    text = data.decode("utf-8", errors="replace")
    lines = text.splitlines()
    if lines:
        lines = lines[1:]
    return lines, {
        "truncated": True,
        "size_bytes": size_bytes,
        "bytes_read": len(data),
        "tail_bytes_read": len(data),
    }


def _live_console_session_model(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
    selected_study_id: str | None,
    selected_study_root: Path | None,
    generated_at: str,
) -> dict[str, Any]:
    latest_path, latest_payload = io.read_first_json(
        (profile.workspace_root / "artifacts" / "runtime" / "live_console" / "session_read_model" / "latest.json",)
    )
    if latest_payload:
        return {"path": latest_path, "payload": latest_payload}
    selection_kwargs: dict[str, Any] = {}
    if selected_study_root is not None and selected_study_id is not None and selected_study_root.name != selected_study_id:
        selection_kwargs["study_root"] = selected_study_root
    elif selected_study_id is not None:
        selection_kwargs["study_id"] = selected_study_id
    elif selected_study_root is not None:
        selection_kwargs["study_root"] = selected_study_root
    payload = build_live_console_session_read_model(
        profile,
        profile_ref=profile_ref,
        generated_at=generated_at,
        **selection_kwargs,
    )
    return {"path": None, "payload": payload}


def _study_projection(context: Mapping[str, Any]) -> dict[str, Any]:
    status = _surface_payload(context, "progress_projection")
    state = _surface_payload(context, "runtime_state")
    health = _surface_payload(context, "runtime_health")
    return {
        "study_id": context["study_id"],
        "study_root": str(context["study_root"]),
        "quest_id": io.first_text(status.get("quest_id"), state.get("quest_id"), _quest_root_name(context)),
        "quest_root": str(context["quest_root"]) if context.get("quest_root") is not None else None,
        "active_run_id": io.first_text(status.get("active_run_id"), state.get("active_run_id"), health.get("active_run_id")),
        "runtime_status": io.first_text(status.get("quest_status"), state.get("status"), health.get("health_status"), "missing"),
        "pending_user_message_count": _optional_int(state.get("pending_user_message_count")),
        "read_only": True,
    }


def _timeline(*, contexts: Iterable[Mapping[str, Any]], live_console: Mapping[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for context in contexts:
        items.extend(_user_message_items(context))
        items.extend(_turn_receipt_items(context))
        items.extend(_runtime_event_items(context))
        items.extend(_state_blocker_items(context))
        items.extend(_health_action_blocker_items(context))
    items.extend(_live_console_items(live_console))
    return [_with_sequence(item, sequence=index) for index, item in enumerate(_sort_timeline(items), start=1)]


def _user_message_items(context: Mapping[str, Any]) -> list[dict[str, Any]]:
    queue_source = _surface(context, "user_message_queue")
    jsonl_source = _surface(context, "user_messages_jsonl")
    items: list[dict[str, Any]] = []
    for queue_name in ("completed", "pending"):
        queue_items = _list(_mapping(queue_source.get("payload")).get(queue_name))
        for message in queue_items:
            if not isinstance(message, Mapping):
                continue
            items.append(
                _base_item(context, item_kind="user_message", source_ref=_source_path(queue_source))
                | {
                    "message_id": io.first_text(message.get("message_id"), message.get("id")),
                    "message_status": io.first_text(message.get("status"), queue_name),
                    "occurred_at": io.first_text(message.get("recorded_at"), message.get("claimed_at")),
                    "run_id": io.text(message.get("claimed_by_run_id")) or None,
                    "content_ref": "content_present" if io.text(message.get("content")) else "missing",
                    "reply_to_interaction_id": io.text(message.get("reply_to_interaction_id")) or None,
                    "missing_fields": _missing(message, ("message_id", "content", "recorded_at")),
                }
            )
    for message in _mapping_items(jsonl_source):
        items.append(
            _base_item(context, item_kind="user_message", source_ref=_source_path(jsonl_source))
            | {
                "message_id": io.first_text(message.get("message_id"), message.get("id")),
                "message_status": io.first_text(message.get("status"), "recorded"),
                "occurred_at": io.first_text(message.get("recorded_at"), message.get("created_at")),
                "run_id": io.text(message.get("claimed_by_run_id")) or None,
                "content_ref": "content_present" if io.text(message.get("content")) else "missing",
                "reply_to_interaction_id": io.text(message.get("reply_to_interaction_id")) or None,
                "missing_fields": _missing(message, ("message_id", "content", "recorded_at")),
            }
        )
    return items


def _turn_receipt_items(context: Mapping[str, Any]) -> list[dict[str, Any]]:
    source = _surface(context, "turn_receipts_jsonl")
    items: list[dict[str, Any]] = []
    for receipt in _mapping_items(source):
        items.append(_turn_receipt_item(context=context, receipt=receipt, source_ref=_source_path(source)))
    latest = _surface_payload(context, "latest_turn_receipt")
    if latest:
        latest_item = _turn_receipt_item(context=context, receipt=latest, source_ref=_source_path(_surface(context, "latest_turn_receipt")))
        latest_item["item_kind"] = "latest_turn_receipt_ref"
        items.append(latest_item)
    return items


def _turn_receipt_item(*, context: Mapping[str, Any], receipt: Mapping[str, Any], source_ref: str | None) -> dict[str, Any]:
    runner_receipt = _mapping(receipt.get("runner_receipt"))
    return _base_item(context, item_kind="turn_receipt", source_ref=source_ref) | {
        "run_id": io.text(receipt.get("run_id")) or None,
        "turn_reason": io.text(receipt.get("reason")) or None,
        "turn_status": io.text(receipt.get("status")) or "missing",
        "occurred_at": io.text(receipt.get("recorded_at")) or None,
        "started": receipt.get("started") if isinstance(receipt.get("started"), bool) else None,
        "queued": receipt.get("queued") if isinstance(receipt.get("queued"), bool) else None,
        "idempotency_key": io.text(receipt.get("idempotency_key")) or None,
        "runner_kind": io.text(runner_receipt.get("runner_kind")) or None,
        "tool_refs": _tool_refs(runner_receipt),
        "assistant_refs": _assistant_refs(runner_receipt),
        "claimed_user_message_refs": _claimed_user_message_refs(receipt),
        "missing_fields": _missing(receipt, ("run_id", "reason", "status", "recorded_at")),
    }


def _runtime_event_items(context: Mapping[str, Any]) -> list[dict[str, Any]]:
    source = _surface(context, "runtime_events_jsonl")
    items: list[dict[str, Any]] = []
    for event in _mapping_items(source):
        snapshot = _mapping(event.get("snapshot"))
        items.append(
            _base_item(context, item_kind="runtime_lifecycle_event", source_ref=_source_path(source))
            | {
                "event_name": io.text(event.get("event")) or "missing",
                "occurred_at": io.text(event.get("recorded_at")) or io.text(snapshot.get("updated_at")) or None,
                "run_id": io.first_text(snapshot.get("active_run_id"), snapshot.get("last_completed_run_id")),
                "runtime_status": io.text(snapshot.get("status")) or None,
                "turn_reason": io.first_text(snapshot.get("turn_reason"), snapshot.get("pending_turn_reason")),
                "stop_requested": snapshot.get("stop_requested") if isinstance(snapshot.get("stop_requested"), bool) else None,
                "blocker_refs": _blocker_refs(snapshot),
                "missing_fields": _missing(event, ("event", "recorded_at")),
            }
        )
    return items


def _state_blocker_items(context: Mapping[str, Any]) -> list[dict[str, Any]]:
    source = _surface(context, "runtime_state")
    state = _surface_payload(context, "runtime_state")
    if not state:
        return []
    items: list[dict[str, Any]] = []
    if state.get("stop_requested") is True:
        items.append(_control_item(context, source=source, event_name="stop_requested", state=state))
    if io.text(state.get("pending_turn_reason")):
        items.append(_control_item(context, source=source, event_name="replan_or_pending_turn", state=state))
    if state.get("blocking_decision_request") or io.text(state.get("waiting_interaction_id")):
        items.append(_control_item(context, source=source, event_name="blocked_waiting_for_user", state=state))
    if state.get("control_intent_lifecycle"):
        items.append(_control_item(context, source=source, event_name="control_intent_lifecycle", state=state))
    return items


def _control_item(
    context: Mapping[str, Any],
    *,
    source: Mapping[str, Any],
    event_name: str,
    state: Mapping[str, Any],
) -> dict[str, Any]:
    return _base_item(context, item_kind="runtime_control_ref", source_ref=_source_path(source)) | {
        "event_name": event_name,
        "occurred_at": io.text(state.get("updated_at")) or None,
        "run_id": io.first_text(state.get("active_run_id"), state.get("last_completed_run_id")),
        "runtime_status": io.text(state.get("status")) or "missing",
        "turn_reason": io.first_text(state.get("turn_reason"), state.get("pending_turn_reason")),
        "stop_requested": state.get("stop_requested") if isinstance(state.get("stop_requested"), bool) else None,
        "blocker_refs": _blocker_refs(state),
        "missing_fields": _missing(state, ("status", "updated_at")),
    }


def _health_action_blocker_items(context: Mapping[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for surface_name in ("runtime_health", "runtime_supervision", "progress_projection"):
        source = _surface(context, surface_name)
        payload = _mapping(source.get("payload"))
        if not payload:
            continue
        refs = _action_refs(payload) + _blocker_refs(payload)
        if not refs:
            continue
        items.append(
            _base_item(context, item_kind="action_or_blocker_ref", source_ref=_source_path(source))
            | {
                "surface": surface_name,
                "occurred_at": io.first_text(payload.get("last_seen_at"), payload.get("updated_at"), payload.get("recorded_at")),
                "run_id": io.first_text(payload.get("active_run_id"), payload.get("last_completed_run_id")),
                "runtime_status": io.first_text(payload.get("health_status"), payload.get("quest_status"), payload.get("status"), "missing"),
                "action_refs": _action_refs(payload),
                "blocker_refs": _blocker_refs(payload),
                "missing_fields": [],
            }
        )
    return items


def _live_console_items(live_console: Mapping[str, Any]) -> list[dict[str, Any]]:
    payload = _mapping(live_console.get("payload"))
    source_ref = str(live_console.get("path")) if live_console.get("path") is not None else "generated_live_console_session_read_model"
    items: list[dict[str, Any]] = []
    for run in _list(payload.get("runs")):
        if not isinstance(run, Mapping):
            continue
        items.append(
            {
                "item_kind": "live_console_run_ref",
                "study_id": io.text(run.get("study_id")) or None,
                "quest_id": io.text(run.get("quest_id")) or None,
                "run_id": io.text(run.get("active_run_id")) or None,
                "runtime_status": io.text(run.get("status")) or "missing",
                "occurred_at": None,
                "source_ref": source_ref,
                "read_only": True,
                "missing_fields": _missing(run, ("study_id", "quest_id", "active_run_id", "status")),
            }
        )
    for event in _list(payload.get("events")):
        if not isinstance(event, Mapping):
            continue
        items.append(
            {
                "item_kind": "live_console_event_ref",
                "study_id": io.text(event.get("study_id")) or None,
                "quest_id": None,
                "run_id": None,
                "event_name": io.text(event.get("topic")) or "missing",
                "runtime_status": io.text(event.get("status")) or "missing",
                "occurred_at": io.text(event.get("observed_at")) or None,
                "source_ref": source_ref if live_console.get("path") is not None else io.text(event.get("source_ref")) or source_ref,
                "read_only": True,
                "missing_fields": _missing(event, ("topic", "status", "observed_at")),
            }
        )
    for action in _list(payload.get("controller_action_intents")):
        if not isinstance(action, Mapping):
            continue
        items.append(
            {
                "item_kind": "controller_action_intent_ref",
                "study_id": payload.get("selected_study_id"),
                "quest_id": None,
                "run_id": None,
                "action_refs": [_action_ref(action)],
                "occurred_at": io.text(payload.get("generated_at")) or None,
                "source_ref": source_ref,
                "read_only": True,
                "direct_execution_allowed": action.get("executes_directly") is True,
                "missing_fields": _missing(action, ("intent", "command")),
            }
        )
    return items


def _base_item(context: Mapping[str, Any], *, item_kind: str, source_ref: str | None) -> dict[str, Any]:
    return {
        "item_kind": item_kind,
        "study_id": context["study_id"],
        "quest_id": io.first_text(_surface_payload(context, "runtime_state").get("quest_id"), _quest_root_name(context)),
        "source_ref": source_ref,
        "read_only": True,
    }


def _sort_timeline(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        items,
        key=lambda item: (
            io.text(item.get("occurred_at")) or "9999-12-31T23:59:59+00:00",
            io.text(item.get("item_kind")),
            io.text(item.get("run_id")),
            io.text(item.get("message_id")),
        ),
    )


def _with_sequence(item: dict[str, Any], *, sequence: int) -> dict[str, Any]:
    return {"sequence": sequence, **item}


def _timeline_summary(timeline: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    missing_field_items = 0
    for item in timeline:
        kind = io.text(item.get("item_kind")) or "unknown"
        counts[kind] = counts.get(kind, 0) + 1
        if item.get("missing_fields"):
            missing_field_items += 1
    return {
        "item_count": len(timeline),
        "counts_by_kind": counts,
        "missing_field_item_count": missing_field_items,
    }


def _source_refs(*, contexts: Iterable[Mapping[str, Any]], live_console: Mapping[str, Any]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    seen: set[str] = set()
    for context in contexts:
        for surface_kind, surface in _mapping(context.get("surfaces")).items():
            if not isinstance(surface, Mapping):
                continue
            path = surface.get("path")
            if path is None:
                continue
            ref = str(path)
            if ref in seen:
                continue
            source_ref = {
                "surface_kind": surface_kind,
                "study_id": context["study_id"],
                "source_ref": ref,
                "read_only": True,
            }
            if "truncated" in surface:
                source_ref["truncated"] = surface.get("truncated") is True
                source_ref["size_bytes"] = _optional_int(surface.get("size_bytes"))
                source_ref["bytes_read"] = _optional_int(surface.get("bytes_read"))
            if "items_truncated" in surface:
                source_ref["items_truncated"] = surface.get("items_truncated") is True
                source_ref["max_items"] = _optional_int(surface.get("max_items"))
            refs.append(source_ref)
            seen.add(ref)
    live_path = live_console.get("path")
    if live_path is not None and str(live_path) not in seen:
        refs.append(
            {
                "surface_kind": "live_console_session_read_model",
                "study_id": None,
                "source_ref": str(live_path),
                "read_only": True,
            }
        )
    return refs


def _tool_refs(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for key in ("command", "stdout_path", "stderr_path", "prompt_path"):
        value = payload.get(key)
        if isinstance(value, list):
            refs.append({"kind": key, "value": [str(item) for item in value]})
        elif io.text(value):
            refs.append({"kind": key, "value": io.text(value)})
    return refs


def _assistant_refs(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for key in ("stdout_path", "prompt_path"):
        value = io.text(payload.get(key))
        if value:
            refs.append({"kind": key, "source_ref": value})
    return refs


def _claimed_user_message_refs(receipt: Mapping[str, Any]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for message in _list(receipt.get("claimed_user_messages")):
        if not isinstance(message, Mapping):
            continue
        refs.append(
            {
                "message_id": io.first_text(message.get("message_id"), message.get("id")),
                "status": io.text(message.get("status")) or "missing",
                "claimed_at": io.text(message.get("claimed_at")) or None,
            }
        )
    return refs


def _action_refs(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for key in ("canonical_runtime_action", "next_action", "next_action_summary", "pending_turn_reason"):
        value = io.text(payload.get(key))
        if value:
            refs.append({"kind": key, "value": value})
    for action in _list(payload.get("allowed_controller_actions")):
        if isinstance(action, str) and action.strip():
            refs.append({"kind": "allowed_controller_action", "value": action.strip()})
        elif isinstance(action, Mapping):
            refs.append(_action_ref(action))
    for action in _list(payload.get("controller_action_intents")):
        if isinstance(action, Mapping):
            refs.append(_action_ref(action))
    return refs


def _action_ref(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "kind": io.first_text(payload.get("kind"), payload.get("intent"), payload.get("action_type"), payload.get("action_id"), "action"),
        "value": io.first_text(payload.get("command"), payload.get("summary"), payload.get("reason"), payload.get("intent"), "missing"),
        "direct_execution_allowed": payload.get("executes_directly") is True,
    }


def _blocker_refs(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for key in ("blocking_reasons", "blockers", "gate_blockers"):
        for blocker in _list(payload.get(key)):
            if isinstance(blocker, str) and blocker.strip():
                refs.append({"kind": key, "value": blocker.strip()})
            elif isinstance(blocker, Mapping):
                refs.append({"kind": key, "value": io.first_text(blocker.get("reason"), blocker.get("blocker"), "missing")})
    blocking_request = _mapping(payload.get("blocking_decision_request"))
    if blocking_request:
        refs.append(
            {
                "kind": "blocking_decision_request",
                "interaction_id": io.text(blocking_request.get("interaction_id")) or io.text(payload.get("waiting_interaction_id")) or None,
                "value": io.first_text(blocking_request.get("prompt"), blocking_request.get("reason"), "waiting_for_user"),
            }
        )
    lifecycle = _mapping(payload.get("control_intent_lifecycle"))
    if lifecycle:
        refs.append(
            {
                "kind": "control_intent_lifecycle",
                "value": io.first_text(lifecycle.get("block_reason"), lifecycle.get("state"), "missing"),
            }
        )
    return refs


def _missing(payload: Mapping[str, Any], required_fields: tuple[str, ...]) -> list[str]:
    return [field for field in required_fields if not _has_value(payload.get(field))]


def _has_value(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict)):
        return bool(value)
    return True


def _surface(context: Mapping[str, Any], name: str) -> dict[str, Any]:
    surface = _mapping(context.get("surfaces")).get(name)
    return dict(surface) if isinstance(surface, Mapping) else {}


def _surface_payload(context: Mapping[str, Any], name: str) -> dict[str, Any]:
    return _mapping(_surface(context, name).get("payload"))


def _mapping_items(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [dict(item) for item in _list(source.get("items")) if isinstance(item, Mapping)]


def _source_path(source: Mapping[str, Any]) -> str | None:
    path = source.get("path")
    return str(path) if path is not None else None


def _quest_root_name(context: Mapping[str, Any]) -> str | None:
    quest_root = context.get("quest_root")
    return quest_root.name if isinstance(quest_root, Path) else None


def _optional_int(value: object) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


__all__ = [
    "CONVERSATION_READ_MODEL_HISTORY_REF",
    "CONVERSATION_READ_MODEL_REF",
    "SURFACE_KIND",
    "build_conversation_read_model",
    "materialize_conversation_read_model",
]
