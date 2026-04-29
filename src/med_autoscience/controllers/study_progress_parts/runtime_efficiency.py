from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers import work_unit_ledger

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
    autonomous_runtime_notice = (
        dict(status.get("autonomous_runtime_notice") or {})
        if isinstance(status.get("autonomous_runtime_notice"), dict)
        else {}
    )
    execution_owner_guard = (
        dict(status.get("execution_owner_guard") or {})
        if isinstance(status.get("execution_owner_guard"), dict)
        else {}
    )
    continuation_state = (
        dict(status.get("continuation_state") or {})
        if isinstance(status.get("continuation_state"), dict)
        else {}
    )
    execution = dict(status.get("execution") or {}) if isinstance(status.get("execution"), dict) else {}
    return (
        _non_empty_text(status.get("active_run_id"))
        or _non_empty_text(execution_owner_guard.get("active_run_id"))
        or _non_empty_text(autonomous_runtime_notice.get("active_run_id"))
        or _non_empty_text(continuation_state.get("active_run_id"))
        or _non_empty_text(execution.get("active_run_id"))
    )


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
    token_usage = (telemetry or {}).get("token_usage") if isinstance((telemetry or {}).get("token_usage"), dict) else {}
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
    if (
        telemetry is None
        and evidence_index is None
        and gate_cache_surface is None
        and not gate_cache_surfaces
        and not gate_replay_telemetry
    ):
        return None
    return {
        "run_id": run_id or "unknown",
        "telemetry_path": str(telemetry_path) if telemetry_path is not None else None,
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
        **gate_replay_telemetry,
        "summary": (
            f"run `{run_id}` prompt {prompt_bytes} bytes; compacted tool results {compacted_count}; "
            f"full-detail calls {full_detail_count}; direct tool-result bytes {tool_result_bytes}; "
            f"saved tool-result bytes {tool_result_bytes_saved}; "
            f"repeated reads {_int_value((telemetry or {}).get('repeated_read_result_count'))}/"
            f"{_int_value((telemetry or {}).get('read_tool_call_count'))}; "
            f"unique commands {_int_value((telemetry or {}).get('unique_command_count'))}; "
            f"gate replay hits {gate_replay_telemetry.get('gate_replay_hit_count') or 0}."
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
