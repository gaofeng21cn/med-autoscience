from __future__ import annotations

from pathlib import Path
from typing import Any

from .shared import _display_text, _mapping_copy, _non_empty_text, _read_json_object


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
        _non_empty_text(execution_owner_guard.get("active_run_id"))
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


def _latest_run_telemetry_surface(
    *,
    quest_root: Path | None,
    status: dict[str, Any],
) -> dict[str, Any] | None:
    if quest_root is None:
        return None
    runs_root = quest_root / ".ds" / "runs"
    if not runs_root.exists():
        return None
    active_run_id = _status_active_run_id(status)
    telemetry_path: Path | None = None
    if active_run_id:
        candidate = runs_root / active_run_id / "telemetry.json"
        if candidate.exists():
            telemetry_path = candidate
    if telemetry_path is None:
        candidates = sorted(
            runs_root.glob("*/telemetry.json"),
            key=lambda item: item.stat().st_mtime if item.exists() else 0,
        )
        telemetry_path = candidates[-1] if candidates else None
    if telemetry_path is None:
        return None
    telemetry = _read_json_object(telemetry_path)
    if telemetry is None:
        return None
    run_id = _non_empty_text(telemetry.get("run_id")) or telemetry_path.parent.name
    evidence_index_path = quest_root / ".ds" / "evidence_packets" / run_id / "index.json"
    evidence_index = _read_json_object(evidence_index_path) if evidence_index_path.exists() else None
    token_usage = telemetry.get("token_usage") if isinstance(telemetry.get("token_usage"), dict) else {}
    compacted_count = int(telemetry.get("compacted_tool_result_count") or 0)
    full_detail_count = int(telemetry.get("full_detail_tool_call_count") or 0)
    tool_result_bytes = int(telemetry.get("tool_result_bytes_total") or 0)
    prompt_bytes = int(telemetry.get("prompt_bytes") or 0)
    gate_cache_path = quest_root / ".ds" / "gate_cache" / "paper_contract_health.json"
    gate_cache = _read_json_object(gate_cache_path) if gate_cache_path.exists() else None
    gate_cache_surface = None
    if isinstance(gate_cache, dict):
        gate_cache_surface = {
            "path": str(gate_cache_path),
            "input_fingerprint": _non_empty_text(gate_cache.get("input_fingerprint")),
            "generated_at": _non_empty_text(gate_cache.get("generated_at")),
        }
    return {
        "run_id": run_id,
        "telemetry_path": str(telemetry_path),
        "prompt_bytes": prompt_bytes,
        "stdout_bytes": int(telemetry.get("stdout_bytes") or 0),
        "tool_result_bytes_total": tool_result_bytes,
        "compacted_tool_result_count": compacted_count,
        "full_detail_tool_call_count": full_detail_count,
        "mcp_tool_call_count": int(telemetry.get("mcp_tool_call_count") or 0),
        "model_inherited": bool(telemetry.get("model_inherited")),
        "runner_profile": _non_empty_text(telemetry.get("runner_profile")),
        "token_usage": dict(token_usage),
        "evidence_packet_index_path": str(evidence_index_path) if evidence_index_path.exists() else None,
        "evidence_packet_count": len((evidence_index or {}).get("items") or []) if isinstance(evidence_index, dict) else 0,
        "latest_evidence_packets": _compact_evidence_items(evidence_index),
        "gate_cache": gate_cache_surface,
        "summary": (
            f"run `{run_id}` prompt {prompt_bytes} bytes; compacted tool results {compacted_count}; "
            f"full-detail calls {full_detail_count}; direct tool-result bytes {tool_result_bytes}."
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
        f"direct tool-result bytes {runtime_efficiency.get('tool_result_bytes_total') or 0}"
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
    return lines


def _runtime_efficiency_refs(runtime_efficiency: dict[str, Any] | None) -> dict[str, str | None]:
    return {
        "runtime_telemetry_path": runtime_efficiency.get("telemetry_path") if runtime_efficiency is not None else None,
        "evidence_packet_index_path": (
            runtime_efficiency.get("evidence_packet_index_path") if runtime_efficiency is not None else None
        ),
    }


__all__ = [
    "_latest_run_telemetry_surface",
    "_runtime_efficiency_markdown_lines",
    "_runtime_efficiency_refs",
]
