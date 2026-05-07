from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = 1
LOW_LEVEL_FIELD_HINTS = ("raw_terminal_log", "full_prompt", "secret", "token_stream")
SURFACE = "ai_first_observability_summary"
OPERATIONS_DASHBOARD_SURFACE = "ai_first_operations_dashboard_summary"
OPERATIONS_DASHBOARD_READ_MODEL = "ai_first_operations_dashboard_read_model"
OPERATIONS_DASHBOARD_CONSUMERS = [
    "product_entry_status",
    "workspace_cockpit",
    "study_progress",
]


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _text(value: object, default: str = "unknown") -> str:
    text = str(value or "").strip()
    return text or default


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _bool_signal(snapshot: Mapping[str, Any], key: str) -> bool | None:
    value = snapshot.get(key)
    return value if isinstance(value, bool) else None


def _runtime_recovery_active(runtime_snapshot: Mapping[str, Any]) -> bool:
    return str(runtime_snapshot.get("canonical_runtime_action") or "").strip() in {
        "recover_runtime",
        "probe_runtime_liveness",
        "escalate_runtime",
    }


def _redacted_fields(*snapshots: Mapping[str, Any]) -> list[str]:
    redacted: set[str] = set()
    for snapshot in snapshots:
        for key in snapshot:
            if any(hint in str(key) for hint in LOW_LEVEL_FIELD_HINTS):
                redacted.add(str(key))
    return sorted(redacted)


def _ai_reviewer_trace_complete(publication_eval: Mapping[str, Any] | None) -> bool:
    if not publication_eval:
        return False
    provenance = _mapping(publication_eval.get("assessment_provenance"))
    return (
        _text(provenance.get("owner")) == "ai_reviewer"
        and provenance.get("ai_reviewer_required") is False
        and bool(_mapping(publication_eval.get("reviewer_operating_system")))
    )


def _route_back_actions(publication_eval: Mapping[str, Any] | None) -> list[Mapping[str, Any]]:
    actions = _list((publication_eval or {}).get("recommended_actions"))
    return [
        item
        for item in actions
        if isinstance(item, Mapping) and _text(item.get("action_type")).startswith("route_back")
    ]


def _quality_toil_items(publication_eval: Mapping[str, Any] | None, *, trace_complete: bool) -> list[str]:
    items: list[str] = []
    if not trace_complete:
        items.append("ai_reviewer_trace_missing")
    for gap in _list((publication_eval or {}).get("gaps")):
        if not isinstance(gap, Mapping):
            continue
        summary = _text(gap.get("summary"), default="")
        if summary:
            items.append(summary)
    return items


def _artifact_snapshot_from_delivery_manifest(delivery_manifest: Mapping[str, Any] | None) -> dict[str, Any]:
    if not delivery_manifest:
        return {
            "stale_artifact_count": 1,
            "current_package_from_canonical_source": False,
        }
    signatures = [
        _text(delivery_manifest.get("source_signature"), default=""),
        _text(delivery_manifest.get("authority_source_signature"), default=""),
        _text(delivery_manifest.get("delivery_source_signature"), default=""),
    ]
    signature_current = bool(signatures[0]) and len(set(signatures)) == 1
    blocking_refs = _list(delivery_manifest.get("blocking_artifact_refs"))
    roles = _mapping(delivery_manifest.get("surface_roles"))
    canonical_source_present = bool(_text(roles.get("controller_authorized_package_source_root"), default=""))
    current = signature_current and canonical_source_present and not blocking_refs
    return {
        "stale_artifact_count": 0 if current else 1 + len(blocking_refs),
        "current_package_from_canonical_source": current,
    }


def _human_review_required(progress_snapshot: Mapping[str, Any]) -> bool:
    explicit = _bool_signal(progress_snapshot, "human_review_required")
    if explicit is not None:
        return explicit
    gate_required = _bool_signal(progress_snapshot, "human_gate_required")
    if gate_required is not None:
        return gate_required
    autonomy_contract = _mapping(progress_snapshot.get("autonomy_contract"))
    restore_point = _mapping(autonomy_contract.get("restore_point"))
    return _bool_signal(restore_point, "human_gate_required") is True


def _user_view(
    *,
    runtime_snapshot: Mapping[str, Any],
    quality_snapshot: Mapping[str, Any],
    artifact_snapshot: Mapping[str, Any],
) -> dict[str, str]:
    reasons: list[str] = []
    has_context = bool(runtime_snapshot or quality_snapshot or artifact_snapshot)
    if _bool_signal(quality_snapshot, "ai_reviewer_trace_complete") is False:
        reasons.append("AI reviewer trace incomplete")
    if _bool_signal(quality_snapshot, "publication_eval_fresh") is False:
        reasons.append("publication eval stale")
    if _int(artifact_snapshot.get("stale_artifact_count")) > 0:
        reasons.append("artifact refresh pending")
    if _runtime_recovery_active(runtime_snapshot):
        reasons.append("runtime recovery in progress")
    if not has_context:
        return {
            "status": "informational",
            "reason": "doctor report exposes the observability contract without study-specific runtime traces",
            "next_action": "inspect_study_runtime_status_or_runtime_watch",
        }
    if not reasons:
        return {
            "status": "on_track",
            "reason": "AI-first quality, runtime, and artifact signals are current",
            "next_action": "continue_current_study_route",
        }
    return {
        "status": "attention_required",
        "reason": "; ".join(reasons),
        "next_action": "return_to_ai_reviewer_or_runtime_recovery",
    }


def _operations_user_view(*, progress_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "current_stage": _text(progress_snapshot.get("current_stage")),
        "blockers": _text_list(progress_snapshot.get("current_blockers")),
        "next_step": _text(progress_snapshot.get("next_system_action")),
        "human_review_required": _human_review_required(progress_snapshot),
    }


def _operations_maintainer_view(
    *,
    drift_audit: Mapping[str, Any],
    runtime_snapshot: Mapping[str, Any],
    quality_snapshot: Mapping[str, Any],
    artifact_snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    toil_items = _text_list(quality_snapshot.get("quality_toil_items"))
    return {
        "ai_first_drift": {
            "status": _text(drift_audit.get("status")),
            "fail_count": _int(_mapping(drift_audit.get("summary")).get("fail_count")),
        },
        "runtime": {
            "action": _text(runtime_snapshot.get("canonical_runtime_action")),
            "retry_budget_remaining": _int(runtime_snapshot.get("retry_budget_remaining")),
        },
        "ai_reviewer_trace": {
            "complete": _bool_signal(quality_snapshot, "ai_reviewer_trace_complete"),
        },
        "cache_freshness": {
            "publication_eval_fresh": _bool_signal(quality_snapshot, "publication_eval_fresh"),
            "gate_cache_fresh": _bool_signal(quality_snapshot, "gate_cache_fresh"),
        },
        "route_back": {
            "count": _int(quality_snapshot.get("route_back_count")),
            "target": _text(quality_snapshot.get("route_back_target")),
        },
        "artifact_stale": {
            "stale_artifact_count": _int(artifact_snapshot.get("stale_artifact_count")),
            "current_package_from_canonical_source": _bool_signal(
                artifact_snapshot,
                "current_package_from_canonical_source",
            ),
        },
        "quality_toil": {
            "toil_items": toil_items,
            "toil_count": len(toil_items),
        },
        "redacted_fields": _redacted_fields(runtime_snapshot, quality_snapshot, artifact_snapshot),
    }


def build_ai_first_observability_snapshots_from_study_root(
    *,
    study_root: str | Path,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root)
    publication_eval = _read_json_object(
        resolved_study_root / "artifacts" / "publication_eval" / "latest.json"
    )
    runtime_health = _read_json_object(
        resolved_study_root / "artifacts" / "runtime" / "health" / "latest.json"
    ) or {}
    delivery_manifest = _read_json_object(resolved_study_root / "manuscript" / "delivery_manifest.json")

    route_back_actions = _route_back_actions(publication_eval)
    trace_complete = _ai_reviewer_trace_complete(publication_eval)
    return {
        "surface": "ai_first_runtime_observability_snapshots",
        "schema_version": SCHEMA_VERSION,
        "study_root": str(resolved_study_root),
        "runtime_snapshot": {
            "canonical_runtime_action": _text(runtime_health.get("canonical_runtime_action")),
            "retry_budget_remaining": _int(runtime_health.get("retry_budget_remaining")),
        },
        "quality_snapshot": {
            "ai_reviewer_trace_complete": trace_complete,
            "publication_eval_fresh": publication_eval is not None,
            "gate_cache_fresh": None,
            "route_back_count": len(route_back_actions),
            "route_back_target": _text(route_back_actions[0].get("route_target"))
            if route_back_actions
            else "unknown",
            "quality_toil_items": _quality_toil_items(publication_eval, trace_complete=trace_complete),
        },
        "artifact_snapshot": _artifact_snapshot_from_delivery_manifest(delivery_manifest),
        "refs": {
            "publication_eval_path": str(
                resolved_study_root / "artifacts" / "publication_eval" / "latest.json"
            ),
            "runtime_health_path": str(
                resolved_study_root / "artifacts" / "runtime" / "health" / "latest.json"
            ),
            "delivery_manifest_path": str(resolved_study_root / "manuscript" / "delivery_manifest.json"),
        },
    }


def build_ai_first_observability_summary(
    *,
    drift_audit: Mapping[str, Any],
    runtime_snapshot: Mapping[str, Any],
    quality_snapshot: Mapping[str, Any],
    artifact_snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    drift_summary = _mapping(drift_audit.get("summary"))
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "operator_view": {
            "ai_first_drift_status": str(drift_audit.get("status") or "unknown"),
            "ai_first_drift_fail_count": _int(drift_summary.get("fail_count")),
            "runtime_action": str(runtime_snapshot.get("canonical_runtime_action") or "unknown"),
            "retry_budget_remaining": _int(runtime_snapshot.get("retry_budget_remaining")),
            "ai_reviewer_trace_complete": _bool_signal(quality_snapshot, "ai_reviewer_trace_complete"),
            "route_back_count": _int(quality_snapshot.get("route_back_count")),
            "publication_eval_fresh": _bool_signal(quality_snapshot, "publication_eval_fresh"),
            "stale_artifact_count": _int(artifact_snapshot.get("stale_artifact_count")),
            "current_package_from_canonical_source": _bool_signal(
                artifact_snapshot,
                "current_package_from_canonical_source",
            ),
            "redacted_fields": _redacted_fields(runtime_snapshot, quality_snapshot, artifact_snapshot),
        },
        "user_view": _user_view(
            runtime_snapshot=runtime_snapshot,
            quality_snapshot=quality_snapshot,
            artifact_snapshot=artifact_snapshot,
        ),
        "authority": {
            "observability_can_authorize_quality": False,
            "observability_can_mutate_runtime": False,
            "user_view_excludes_low_level_logs": True,
        },
    }


def build_ai_first_operations_dashboard_summary(
    *,
    drift_audit: Mapping[str, Any],
    progress_snapshot: Mapping[str, Any],
    runtime_snapshot: Mapping[str, Any],
    quality_snapshot: Mapping[str, Any],
    artifact_snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "surface": OPERATIONS_DASHBOARD_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "read_model": OPERATIONS_DASHBOARD_READ_MODEL,
        "contract": {
            "authority": "observability_only",
            "shared_read_model_consumers": list(OPERATIONS_DASHBOARD_CONSUMERS),
            "user_view_fields": [
                "current_stage",
                "blockers",
                "next_step",
                "human_review_required",
            ],
            "maintainer_view_fields": [
                "ai_reviewer_trace",
                "cache_freshness",
                "route_back",
                "artifact_stale",
                "quality_toil",
            ],
        },
        "user_view": _operations_user_view(progress_snapshot=progress_snapshot),
        "maintainer_view": _operations_maintainer_view(
            drift_audit=drift_audit,
            runtime_snapshot=runtime_snapshot,
            quality_snapshot=quality_snapshot,
            artifact_snapshot=artifact_snapshot,
        ),
        "authority": {
            "observability_can_authorize_quality": False,
            "observability_can_mutate_runtime": False,
            "user_view_excludes_low_level_logs": True,
        },
    }


def build_doctor_ai_first_observability_summary(*, drift_audit: Mapping[str, Any]) -> dict[str, Any]:
    summary = build_ai_first_observability_summary(
        drift_audit=drift_audit,
        runtime_snapshot={},
        quality_snapshot={},
        artifact_snapshot={},
    )
    summary["contract"] = {
        "operator_view_includes": [
            "ai_first_drift_status",
            "runtime_action",
            "ai_reviewer_trace_complete",
            "route_back_count",
            "publication_eval_fresh",
            "stale_artifact_count",
        ],
        "user_view_excludes": list(LOW_LEVEL_FIELD_HINTS),
        "authority": "observability_only",
    }
    return summary
