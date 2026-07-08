from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from collections.abc import Mapping
from datetime import datetime

from med_autoscience.controllers import opl_runtime_refs, work_unit_ledger

from .shared import _display_text, _mapping_copy, _non_empty_text, _read_json_object


def _int_value(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _float_value(value: object) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _status_active_run_id(status: dict[str, Any]) -> str | None:
    return opl_runtime_refs.active_run_id(status)


def _compact_evidence_items(evidence_index: dict[str, Any] | None) -> list[dict[str, Any]]:
    compact_items: list[dict[str, Any]] = []
    raw_items = (evidence_index or {}).get("items") if isinstance(evidence_index, dict) else []
    for item in [value for value in (raw_items or []) if isinstance(value, dict)][-5:]:
        raw_blockers = item.get("key_blockers")
        key_blockers = raw_blockers if isinstance(raw_blockers, list) else []
        compact_items.append(
            {
                "tool_name": _non_empty_text(item.get("tool_name")),
                "detail": _non_empty_text(item.get("detail")),
                "summary": _non_empty_text(item.get("summary")),
                "payload_bytes": int(item.get("payload_bytes") or 0),
                "sidecar_path": _non_empty_text(item.get("sidecar_path")),
                "payload_sha256": _non_empty_text(item.get("payload_sha256")),
                "key_blockers": [str(value) for value in key_blockers[:5] if str(value).strip()],
            }
        )
    return compact_items


def _gate_cache_surfaces(quest_root: Path) -> list[dict[str, Any]]:
    cache_root = quest_root / ".ds" / "gate_cache"
    if not cache_root.exists():
        return []
    surfaces: list[dict[str, Any]] = []
    for path in sorted(cache_root.glob("*.json")):
        payload = _read_json_object(path)
        if payload is None:
            continue
        surface_id = _non_empty_text(payload.get("surface_id")) or path.stem
        surfaces.append(
            {
                "surface_id": surface_id,
                "path": str(path),
                "input_fingerprint": _non_empty_text(payload.get("input_fingerprint")),
                "generated_at": _non_empty_text(payload.get("generated_at")),
            }
        )
    return surfaces


def _latest_evidence_index_path(
    *,
    quest_root: Path,
    run_id: str | None,
) -> Path | None:
    evidence_root = quest_root / ".ds" / "evidence_packets"
    if run_id is not None:
        candidate = evidence_root / run_id / "index.json"
        if candidate.exists():
            return candidate
    if not evidence_root.exists():
        return None
    candidates = sorted(
        evidence_root.glob("*/index.json"),
        key=lambda item: item.stat().st_mtime if item.exists() else 0,
    )
    return candidates[-1] if candidates else None


def _batch_gate_replay_hit(path: Path) -> dict[str, Any] | None:
    payload = _read_json_object(path)
    if payload is None:
        return None
    nested_batch = _mapping_copy(payload.get("gate_clearing_batch"))
    source = nested_batch or payload
    gate_replay = _mapping_copy(source.get("gate_replay"))
    gate_replay_step = _mapping_copy(source.get("gate_replay_step"))
    status = _non_empty_text(gate_replay_step.get("status")) or _non_empty_text(gate_replay.get("status"))
    if not gate_replay and not gate_replay_step:
        return None
    return {
        "status": status or "unknown",
        "path": str(path),
        "recorded_at": (
            _non_empty_text(gate_replay_step.get("finished_at"))
            or _non_empty_text(source.get("finished_at"))
            or _non_empty_text(source.get("generated_at"))
            or _non_empty_text(source.get("emitted_at"))
            or _non_empty_text(source.get("recorded_at"))
        ),
    }


def _gate_replay_telemetry(study_root: Path | None) -> dict[str, Any]:
    if study_root is None:
        return {}
    try:
        lifecycle = work_unit_ledger.lifecycle_summary(study_root=study_root)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        lifecycle = {}
    totals = _mapping_copy(lifecycle.get("totals"))
    replay_count = _int_value(totals.get("replay_count"))
    latest_replayed_at = None
    for unit in lifecycle.get("units") or []:
        if not isinstance(unit, dict):
            continue
        candidate = _non_empty_text(unit.get("latest_gate_replayed_at"))
        if candidate is not None and (latest_replayed_at is None or candidate > latest_replayed_at):
            latest_replayed_at = candidate
    if replay_count > 0:
        return {
            "gate_replay_hit_count": replay_count,
            "latest_gate_replay_at": latest_replayed_at,
            "gate_replay_status": "observed",
            "gate_replay_ref": _non_empty_text(lifecycle.get("ledger_path")),
        }
    batch_hits = [
        hit
        for hit in (
            _batch_gate_replay_hit(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"),
            _batch_gate_replay_hit(study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"),
        )
        if hit is not None
    ]
    if not batch_hits:
        return {}
    latest_hit = max(batch_hits, key=lambda item: _non_empty_text(item.get("recorded_at")) or "")
    return {
        "gate_replay_hit_count": len(batch_hits),
        "latest_gate_replay_at": _non_empty_text(latest_hit.get("recorded_at")),
        "gate_replay_status": _non_empty_text(latest_hit.get("status")),
        "gate_replay_ref": _non_empty_text(latest_hit.get("path")),
    }


def _token_usage_surface(
    telemetry: dict[str, Any] | None,
    *,
    stage_execution_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    raw = telemetry.get("token_usage") if isinstance(telemetry, dict) else None
    if isinstance(raw, dict) and raw:
        result = dict(raw)
        result.setdefault("status", "present")
        if "total_tokens" not in result:
            result["total_tokens"] = _token_usage_total(result)
        return result
    stage_usage = _token_usage_from_stage_records(stage_execution_records or [])
    if stage_usage is not None:
        return stage_usage
    return {
        "status": "missing",
        "total_tokens": None,
        "missing_token_usage_reason": "no_completed_runner_telemetry_token_usage_observed",
    }


def _token_usage_total(token_usage: Mapping[str, Any]) -> int | None:
    total = _first_number(
        token_usage.get("total_tokens"),
        token_usage.get("total"),
        token_usage.get("token_total"),
        token_usage.get("totalTokens"),
        token_usage.get("tokenTotal"),
    )
    if total is not None:
        return total
    parts = [
        _first_number(token_usage.get("input_tokens"), token_usage.get("inputTokens"), token_usage.get("prompt_tokens"), token_usage.get("promptTokens")),
        _first_number(token_usage.get("cached_input_tokens"), token_usage.get("cachedInputTokens")),
        _first_number(token_usage.get("output_tokens"), token_usage.get("outputTokens"), token_usage.get("completion_tokens"), token_usage.get("completionTokens")),
        _first_number(token_usage.get("reasoning_tokens"), token_usage.get("reasoningTokens")),
    ]
    present = [value for value in parts if value is not None]
    return sum(present) if present else None


def _number(value: object) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return int(float(text))
        except ValueError:
            return None
    return None


def _first_number(*values: object) -> int | None:
    for value in values:
        number = _number(value)
        if number is not None:
            return number
    return None


def _token_usage_from_mapping(value: Mapping[str, Any]) -> dict[str, Any] | None:
    total = _token_usage_total(value)
    input_tokens = _first_number(value.get("input_tokens"), value.get("inputTokens"), value.get("prompt_tokens"), value.get("promptTokens"))
    output_tokens = _first_number(value.get("output_tokens"), value.get("outputTokens"), value.get("completion_tokens"), value.get("completionTokens"))
    if total is None and input_tokens is None and output_tokens is None:
        return None
    result = dict(value)
    result["status"] = _non_empty_text(result.get("status")) or "present"
    result["total_tokens"] = total
    if input_tokens is not None:
        result["input_tokens"] = input_tokens
    if output_tokens is not None:
        result["output_tokens"] = output_tokens
    return result


def _token_usage_from_stage_records(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    missing_with_source: dict[str, Any] | None = None
    for record in records:
        token_usage = _mapping_copy(record.get("token_usage"))
        if not token_usage:
            continue
        if _token_usage_total(token_usage) is not None:
            result = dict(token_usage)
            result.setdefault("status", "present")
            result.setdefault("source", "stage_execution_records")
            result.setdefault("stage_record_source", _non_empty_text(record.get("source")))
            return result
        if missing_with_source is None and _non_empty_text(token_usage.get("source")):
            missing_with_source = dict(token_usage)
    if missing_with_source is None:
        return None
    missing_with_source.setdefault("status", "missing")
    missing_with_source["total_tokens"] = None
    missing_with_source.setdefault("source", "stage_execution_records")
    return missing_with_source


def _stage_log_token_usage(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    for container in _token_usage_containers(payload):
        for key in ("token_usage", "usage", "tokenUsage"):
            token_usage = _mapping_copy(container.get(key))
            if usage := _token_usage_from_mapping(token_usage):
                return usage
    return None


def _token_usage_containers(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    containers: list[Mapping[str, Any]] = [payload]
    for key in (
        "paper_stage_log",
        "user_stage_log",
        "stage_log_summary",
        "domain_execution",
        "owner_result",
        "execution",
        "provider_attempt",
        "runtime_telemetry",
    ):
        container = _mapping_copy(payload.get(key))
        if container:
            containers.append(container)
    return containers


def _closeout_ref_path(*, study_root: Path, ref: str) -> Path | None:
    text = ref.strip()
    if not text:
        return None
    path = Path(text).expanduser()
    if path.is_absolute():
        return path if path.is_file() else None
    candidates = [
        study_root / path,
        study_root.parent.parent / path,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _token_usage_from_closeout_refs(*, study_root: Path, refs: list[str]) -> dict[str, Any] | None:
    missing_reasons: list[str] = []
    inspected_refs: list[str] = []
    for ref in refs:
        path = _closeout_ref_path(study_root=study_root, ref=ref)
        if path is None:
            continue
        inspected_refs.append(str(path))
        payload = _read_json_object(path)
        if payload is None:
            continue
        token_usage = _stage_log_token_usage(payload)
        if token_usage is not None:
            token_usage.setdefault("source", "stage_closeout_user_stage_log")
            token_usage.setdefault("source_ref", str(path))
            return token_usage
        for key in ("paper_stage_log", "user_stage_log", "stage_log_summary"):
            stage_log = _mapping_copy(payload.get(key))
            usage = _mapping_copy(stage_log.get("token_usage"))
            if reason := _non_empty_text(usage.get("missing_token_usage_reason")):
                missing_reasons.append(reason)
    if inspected_refs:
        return {
            "status": "missing",
            "total_tokens": None,
            "missing_token_usage_reason": (
                missing_reasons[0] if missing_reasons else "stage_closeout_has_no_token_usage"
            ),
            "source": "stage_closeout_user_stage_log",
            "inspected_closeout_refs": inspected_refs[:5],
        }
    return None


def _float_number(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None
    return None


def _stage_execution_records(
    *,
    study_root: Path | None,
    telemetry_status: str,
) -> list[dict[str, Any]]:
    if study_root is None:
        return []
    controller_records: list[dict[str, Any]] = []
    for record in (
        _controller_stage_record(
            study_root=study_root,
            controller_name="quality_repair_batch",
            action_type="run_quality_repair_batch",
        ),
        _controller_stage_record(
            study_root=study_root,
            controller_name="gate_clearing_batch",
            action_type="run_gate_clearing_batch",
        ),
    ):
        if record is not None:
            controller_records.append(record)
    lifecycle_records = _work_unit_stage_records(study_root=study_root)
    result = _select_stage_records(
        controller_records=controller_records,
        lifecycle_records=lifecycle_records,
        limit=12,
    )
    for record in result:
        record["token_usage"] = _stage_token_usage(
            record,
            telemetry_status=telemetry_status,
            study_root=study_root,
        )
        record["duration"] = _stage_duration(record)
    return result


def _controller_stage_record(
    *,
    study_root: Path,
    controller_name: str,
    action_type: str,
) -> dict[str, Any] | None:
    path = study_root / "artifacts" / "controller" / controller_name / "latest.json"
    payload = _read_json_object(path)
    if payload is None:
        return None
    step = _mapping_copy(payload.get("gate_replay_step"))
    repair = _mapping_copy(payload.get("repair_execution_evidence"))
    work_unit = _mapping_copy(payload.get("selected_publication_work_unit"))
    repair_work_unit = _mapping_copy(repair.get("repair_work_unit"))
    changed_artifact_refs = _changed_artifact_paths(repair) or _changed_artifact_paths(payload)
    gate_replay = _mapping_copy(payload.get("gate_replay"))
    status = (
        _non_empty_text(step.get("status"))
        or _non_empty_text(repair.get("status"))
        or _non_empty_text(payload.get("status"))
        or "unknown"
    )
    finished_at = (
        _non_empty_text(step.get("finished_at"))
        or _non_empty_text(payload.get("finished_at"))
        or _non_empty_text(payload.get("generated_at"))
        or _non_empty_text(payload.get("emitted_at"))
    )
    return {
        "record_kind": "controller_stage_execution",
        "source": f"study_controller.{controller_name}.latest",
        "source_ref": str(path),
        "stage_id": "publication_supervision",
        "controller_name": controller_name,
        "action_type": action_type,
        "work_unit_id": (
            _non_empty_text(payload.get("work_unit_id"))
            or _non_empty_text(work_unit.get("unit_id"))
            or _non_empty_text(repair_work_unit.get("unit_id"))
        ),
        "work_unit_fingerprint": (
            _non_empty_text(payload.get("work_unit_fingerprint"))
            or _non_empty_text(payload.get("source_work_unit_fingerprint"))
        ),
        "status": status,
        "started_at": _non_empty_text(step.get("started_at")),
        "finished_at": finished_at,
        "duration_seconds": _float_number(step.get("duration_seconds")),
        "work_done": _controller_work_done(
            controller_name=controller_name,
            status=status,
            changed_artifact_count=len(changed_artifact_refs),
            gate_replay_status=_non_empty_text(gate_replay.get("status")),
        ),
        "changed_artifact_refs": changed_artifact_refs[:12],
        "remaining_blockers": _text_list(gate_replay.get("blockers")) or _text_list(repair.get("blockers")),
        "evidence_refs": _controller_evidence_refs(payload=payload, repair=repair, gate_replay=gate_replay),
    }


def _controller_work_done(
    *,
    controller_name: str,
    status: str,
    changed_artifact_count: int,
    gate_replay_status: str | None,
) -> list[str]:
    if controller_name == "quality_repair_batch":
        result = ["Ran the quality repair batch for the selected paper work unit."]
        if changed_artifact_count:
            result.append(f"Recorded {changed_artifact_count} changed artifact ref(s).")
        if gate_replay_status is not None:
            result.append(f"Requested or observed publication gate replay: {gate_replay_status}.")
        return result
    if controller_name == "gate_clearing_batch":
        return [f"Replayed the publication gate for the selected work unit; result: {status}."]
    return [f"Observed controller stage execution: {status}."]


def _changed_artifact_paths(payload: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for item in payload.get("changed_artifact_refs") or []:
        if isinstance(item, Mapping) and (text := _non_empty_text(item.get("path"))):
            refs.append(text)
    canonical = _mapping_copy(payload.get("canonical_artifact_delta"))
    for item in canonical.get("artifact_refs") or []:
        if isinstance(item, Mapping) and (text := _non_empty_text(item.get("path"))):
            refs.append(text)
    return list(dict.fromkeys(refs))


def _controller_evidence_refs(
    *,
    payload: Mapping[str, Any],
    repair: Mapping[str, Any],
    gate_replay: Mapping[str, Any],
) -> list[str]:
    refs: list[str] = []
    refs.extend(_text_list(repair.get("source_refs")))
    refs.extend(_text_list(repair.get("gate_replay_refs")))
    for key in ("repair_execution_evidence_path", "source_eval_artifact_path", "source_summary_artifact_path"):
        if text := _non_empty_text(payload.get(key)):
            refs.append(text)
    for key in ("report_json", "report_markdown"):
        if text := _non_empty_text(gate_replay.get(key)):
            refs.append(text)
    return list(dict.fromkeys(refs))[:12]


def _work_unit_stage_records(*, study_root: Path) -> list[dict[str, Any]]:
    try:
        lifecycle = work_unit_ledger.lifecycle_summary(study_root=study_root)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return []
    records: list[dict[str, Any]] = []
    for unit in lifecycle.get("units") or []:
        if not isinstance(unit, Mapping):
            continue
        records.append(
            {
                "record_kind": "work_unit_lifecycle",
                "source": "work_unit_ledger.lifecycle_summary",
                "source_ref": _non_empty_text(lifecycle.get("ledger_path")),
                "stage_id": "publication_supervision",
                "controller_name": _non_empty_text(unit.get("lane")),
                "action_type": _non_empty_text(unit.get("action_type")),
                "work_unit_id": _non_empty_text(unit.get("unit_id")),
                "work_unit_fingerprint": _non_empty_text(unit.get("dispatch_key")),
                "status": _non_empty_text(unit.get("lifecycle_state")) or "unknown",
                "started_at": _non_empty_text(unit.get("first_recorded_at")),
                "finished_at": _non_empty_text(unit.get("latest_recorded_at")),
                "duration_seconds": None,
                "event_count": _int_value(unit.get("event_count")),
                "work_done": [f"Recorded lifecycle events: {', '.join(_text_list(unit.get('event_types')))}."],
                "changed_artifact_refs": [],
                "remaining_blockers": [],
                "evidence_refs": [_non_empty_text(lifecycle.get("ledger_path"))]
                if _non_empty_text(lifecycle.get("ledger_path"))
                else [],
                "closeout_refs": _text_list(unit.get("closeout_refs")),
            }
        )
    return records


def _dedupe_stage_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[tuple[str | None, str | None, str | None]] = set()
    for record in sorted(records, key=lambda item: _non_empty_text(item.get("finished_at")) or ""):
        key = (
            _non_empty_text(record.get("source_ref")),
            _non_empty_text(record.get("action_type")),
            _non_empty_text(record.get("work_unit_id")),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(record)
    return result


def _select_stage_records(
    *,
    controller_records: list[dict[str, Any]],
    lifecycle_records: list[dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    controllers = _dedupe_stage_records(controller_records)
    controller_keys = {
        (
            _non_empty_text(record.get("source_ref")),
            _non_empty_text(record.get("action_type")),
            _non_empty_text(record.get("work_unit_id")),
        )
        for record in controllers
    }
    lifecycle = [
        record
        for record in _dedupe_stage_records(lifecycle_records)
        if (
            _non_empty_text(record.get("source_ref")),
            _non_empty_text(record.get("action_type")),
            _non_empty_text(record.get("work_unit_id")),
        )
        not in controller_keys
    ]
    remaining_slots = max(limit - len(controllers), 0)
    selected = lifecycle[-remaining_slots:] if remaining_slots else []
    selected.extend(controllers[-limit:])
    return _dedupe_stage_records_preserving_order(selected)[-limit:]


def _dedupe_stage_records_preserving_order(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[tuple[str | None, str | None, str | None]] = set()
    for record in records:
        key = (
            _non_empty_text(record.get("source_ref")),
            _non_empty_text(record.get("action_type")),
            _non_empty_text(record.get("work_unit_id")),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(record)
    return result


def _stage_token_usage(
    record: Mapping[str, Any],
    *,
    telemetry_status: str,
    study_root: Path,
) -> dict[str, Any]:
    token_usage = _mapping_copy(record.get("token_usage"))
    if token_usage:
        return token_usage
    closeout_refs = _text_list(record.get("closeout_refs"))
    if closeout_refs and (closeout_usage := _token_usage_from_closeout_refs(study_root=study_root, refs=closeout_refs)):
        return closeout_usage
    return {
        "status": "missing" if telemetry_status == "missing" else "not_available",
        "total_tokens": None,
        "missing_token_usage_reason": "stage_record_has_no_token_usage",
    }


def _stage_duration(record: Mapping[str, Any]) -> dict[str, Any]:
    seconds = _float_number(record.get("duration_seconds"))
    if seconds is not None:
        return {"status": "present", "seconds": seconds}
    started_at = _parse_datetime(record.get("started_at"))
    finished_at = _parse_datetime(record.get("finished_at"))
    if started_at is not None and finished_at is not None:
        if record.get("record_kind") == "work_unit_lifecycle":
            return {
                "status": "elapsed_window_only",
                "seconds": max((finished_at - started_at).total_seconds(), 0.0),
                "source": "lifecycle_first_latest_recorded_at",
                "not_execution_duration": True,
                "event_count": _int_value(record.get("event_count")),
            }
        return {
            "status": "present",
            "seconds": max((finished_at - started_at).total_seconds(), 0.0),
            "source": "started_at_finished_at",
        }
    return {
        "status": "missing",
        "seconds": None,
        "missing_duration_reason": "stage_record_has_no_duration",
    }


def _parse_datetime(value: object) -> datetime | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    return [text for item in value if (text := _non_empty_text(item)) is not None]


def _latest_run_telemetry_surface(
    *,
    quest_root: Path | None,
    status: dict[str, Any],
    study_root: Path | None = None,
) -> dict[str, Any] | None:
    if quest_root is None:
        return None
    runs_root = quest_root / ".ds" / "runs"
    active_run_id = _status_active_run_id(status)
    telemetry_path: Path | None = None
    if active_run_id and runs_root.exists():
        candidate = runs_root / active_run_id / "telemetry.json"
        if candidate.exists():
            telemetry_path = candidate
    if telemetry_path is None and runs_root.exists():
        candidates = sorted(
            runs_root.glob("*/telemetry.json"),
            key=lambda item: item.stat().st_mtime if item.exists() else 0,
        )
        telemetry_path = candidates[-1] if candidates else None
    telemetry = _read_json_object(telemetry_path) if telemetry_path is not None else None
    run_id = (
        _non_empty_text((telemetry or {}).get("run_id"))
        or (telemetry_path.parent.name if telemetry_path is not None else None)
        or active_run_id
    )
    evidence_index_path = _latest_evidence_index_path(quest_root=quest_root, run_id=run_id)
    if telemetry is None and evidence_index_path is not None:
        run_id = evidence_index_path.parent.name
    evidence_index = (
        _read_json_object(evidence_index_path)
        if evidence_index_path is not None and evidence_index_path.exists()
        else None
    )
    compacted_count = _int_value((telemetry or {}).get("compacted_tool_result_count"))
    full_detail_count = _int_value((telemetry or {}).get("full_detail_tool_call_count"))
    tool_result_bytes = _int_value((telemetry or {}).get("tool_result_bytes_total"))
    tool_result_bytes_after_compaction = _int_value((telemetry or {}).get("tool_result_bytes_after_compaction_total"))
    tool_result_bytes_saved = _int_value((telemetry or {}).get("tool_result_bytes_saved_total"))
    prompt_bytes = _int_value((telemetry or {}).get("prompt_bytes"))
    gate_cache_path = quest_root / ".ds" / "gate_cache" / "paper_contract_health.json"
    gate_cache = _read_json_object(gate_cache_path) if gate_cache_path.exists() else None
    gate_cache_surface = None
    if isinstance(gate_cache, dict):
        gate_cache_surface = {
            "path": str(gate_cache_path),
            "input_fingerprint": _non_empty_text(gate_cache.get("input_fingerprint")),
            "generated_at": _non_empty_text(gate_cache.get("generated_at")),
        }
    gate_cache_surfaces = _gate_cache_surfaces(quest_root)
    gate_replay_telemetry = _gate_replay_telemetry(study_root)
    stage_execution_records = _stage_execution_records(
        study_root=study_root,
        telemetry_status="present" if telemetry is not None else "missing",
    )
    token_usage = _token_usage_surface(telemetry, stage_execution_records=stage_execution_records)
    if (
        telemetry is None
        and evidence_index is None
        and gate_cache_surface is None
        and not gate_cache_surfaces
        and not gate_replay_telemetry
        and not stage_execution_records
    ):
        return None
    return {
        "run_id": run_id or "unknown",
        "telemetry_path": str(telemetry_path) if telemetry_path is not None else None,
        "telemetry_status": "present" if telemetry is not None else "missing",
        "telemetry_missing_reason": None
        if telemetry is not None
        else "no completed runner telemetry found for the selected or latest run",
        "prompt_bytes": prompt_bytes,
        "stdout_bytes": _int_value((telemetry or {}).get("stdout_bytes")),
        "tool_result_bytes_total": tool_result_bytes,
        "tool_result_bytes_after_compaction_total": tool_result_bytes_after_compaction,
        "tool_result_bytes_saved_total": tool_result_bytes_saved,
        "compacted_tool_result_count": compacted_count,
        "full_detail_tool_call_count": full_detail_count,
        "mcp_tool_call_count": _int_value((telemetry or {}).get("mcp_tool_call_count")),
        "tool_call_budget": _int_value((telemetry or {}).get("tool_call_budget")),
        "tool_call_count": _int_value((telemetry or {}).get("tool_call_count")),
        "tool_call_budget_remaining": _int_value((telemetry or {}).get("tool_call_budget_remaining")),
        "tool_call_budget_exceeded": bool((telemetry or {}).get("tool_call_budget_exceeded")),
        "unique_command_count": _int_value((telemetry or {}).get("unique_command_count")),
        "read_tool_call_count": _int_value((telemetry or {}).get("read_tool_call_count")),
        "repeated_read_result_count": _int_value((telemetry or {}).get("repeated_read_result_count")),
        "repeated_read_ratio": _float_value((telemetry or {}).get("repeated_read_ratio")),
        "read_churn_ratio": _float_value((telemetry or {}).get("read_churn_ratio")),
        "same_result_reinjection_count": _int_value((telemetry or {}).get("same_result_reinjection_count")),
        "meaningful_artifact_delta_at": _non_empty_text((telemetry or {}).get("meaningful_artifact_delta_at")),
        "meaningful_artifact_delta_kind": _non_empty_text(
            (telemetry or {}).get("meaningful_artifact_delta_kind")
        ),
        "meaningful_artifact_delta_source_signature": _non_empty_text(
            (telemetry or {}).get("meaningful_artifact_delta_source_signature")
        ),
        "turn_progress_kind": _non_empty_text((telemetry or {}).get("turn_progress_kind")),
        "stage_intent": _non_empty_text((telemetry or {}).get("stage_intent")),
        "full_detail_count": _int_value((telemetry or {}).get("full_detail_count")),
        "model_inherited": bool((telemetry or {}).get("model_inherited")),
        "runner_profile": _non_empty_text((telemetry or {}).get("runner_profile")),
        "token_usage": dict(token_usage),
        "evidence_packet_index_path": (
            str(evidence_index_path) if evidence_index_path is not None and evidence_index_path.exists() else None
        ),
        "evidence_packet_count": len((evidence_index or {}).get("items") or []) if isinstance(evidence_index, dict) else 0,
        "latest_evidence_packets": _compact_evidence_items(evidence_index),
        "gate_cache": gate_cache_surface,
        "gate_cache_surfaces": gate_cache_surfaces,
        "stage_execution_records": stage_execution_records,
        "stage_execution_record_count": len(stage_execution_records),
        **gate_replay_telemetry,
        "summary": (
            f"run `{run_id}` prompt {prompt_bytes} bytes; compacted tool results {compacted_count}; "
            f"full-detail calls {full_detail_count}; direct tool-result bytes {tool_result_bytes}; "
            f"saved tool-result bytes {tool_result_bytes_saved}; "
            f"repeated reads {_int_value((telemetry or {}).get('repeated_read_result_count'))}/"
            f"{_int_value((telemetry or {}).get('read_tool_call_count'))}; "
            f"unique commands {_int_value((telemetry or {}).get('unique_command_count'))}; "
            f"gate replay hits {gate_replay_telemetry.get('gate_replay_hit_count') or 0}; "
            f"stage records {len(stage_execution_records)}; "
            f"token usage {token_usage.get('status') or 'unknown'}."
        ),
    }


def _runtime_efficiency_markdown_lines(runtime_efficiency: dict[str, Any]) -> list[str]:
    if not runtime_efficiency:
        return []
    lines = [
        "- 上下文效率: "
        f"compacted tool results {runtime_efficiency.get('compacted_tool_result_count') or 0}; "
        f"full-detail calls {runtime_efficiency.get('full_detail_tool_call_count') or 0}; "
        f"prompt bytes {runtime_efficiency.get('prompt_bytes') or 0}; "
        f"direct tool-result bytes {runtime_efficiency.get('tool_result_bytes_total') or 0}; "
        f"saved bytes {runtime_efficiency.get('tool_result_bytes_saved_total') or 0}; "
        f"unique commands {runtime_efficiency.get('unique_command_count') or 0}; "
        f"repeated reads {runtime_efficiency.get('repeated_read_result_count') or 0}/"
        f"{runtime_efficiency.get('read_tool_call_count') or 0}; "
        f"gate replay hits {runtime_efficiency.get('gate_replay_hit_count') or 0}"
    ]
    if runtime_efficiency.get("evidence_packet_count"):
        evidence_index_ref = _non_empty_text(runtime_efficiency.get("evidence_packet_index_path")) or "none"
        lines.append(f"- 紧凑证据包: {runtime_efficiency.get('evidence_packet_count')} 个；index: `{evidence_index_ref}`")
    latest_packets = [
        dict(item)
        for item in (runtime_efficiency.get("latest_evidence_packets") or [])
        if isinstance(item, dict)
    ]
    if latest_packets:
        latest_packet = latest_packets[-1]
        packet_summary = _display_text(latest_packet.get("summary")) or _non_empty_text(latest_packet.get("summary"))
        packet_path = _non_empty_text(latest_packet.get("sidecar_path")) or "none"
        if packet_summary:
            lines.append(f"- 最新证据包摘要: {packet_summary} ref: `{packet_path}`")
    gate_cache = _mapping_copy(runtime_efficiency.get("gate_cache"))
    if gate_cache:
        fingerprint = _non_empty_text(gate_cache.get("input_fingerprint")) or "unknown"
        lines.append(f"- Gate cache fingerprint: `{fingerprint}`")
    gate_cache_surfaces = [
        dict(item)
        for item in (runtime_efficiency.get("gate_cache_surfaces") or [])
        if isinstance(item, dict)
    ]
    if gate_cache_surfaces:
        surface_ids = [
            _non_empty_text(item.get("surface_id"))
            for item in gate_cache_surfaces[:8]
            if _non_empty_text(item.get("surface_id"))
        ]
        lines.append(f"- Gate cache surfaces: `{', '.join(surface_ids)}`")
    if runtime_efficiency.get("gate_replay_hit_count"):
        lines.append(
            "- Gate replay telemetry: "
            f"{runtime_efficiency.get('gate_replay_hit_count')} hit(s); "
            f"latest: `{runtime_efficiency.get('latest_gate_replay_at') or 'unknown'}`; "
            f"ref: `{runtime_efficiency.get('gate_replay_ref') or 'none'}`"
        )
    if runtime_efficiency.get("stage_execution_record_count"):
        token_usage = _mapping_copy(runtime_efficiency.get("token_usage"))
        lines.append(
            "- Stage execution records: "
            f"{runtime_efficiency.get('stage_execution_record_count')} record(s); "
            f"token_usage_status: `{token_usage.get('status') or 'unknown'}`"
        )
    return lines


def _runtime_efficiency_refs(runtime_efficiency: dict[str, Any] | None) -> dict[str, str | None]:
    return {
        "runtime_telemetry_path": runtime_efficiency.get("telemetry_path") if runtime_efficiency is not None else None,
        "evidence_packet_index_path": (
            runtime_efficiency.get("evidence_packet_index_path") if runtime_efficiency is not None else None
        ),
        "gate_replay_ref": runtime_efficiency.get("gate_replay_ref") if runtime_efficiency is not None else None,
    }


__all__ = [
    "_latest_run_telemetry_surface",
    "_runtime_efficiency_markdown_lines",
    "_runtime_efficiency_refs",
]
