from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers.owner_route_reconcile_parts import current_truth_owner

OPL_OWNER_ROUTE_HANDOFF_SOURCE = "owner_route_reconcile_opl_owner_route_handoff"
OPL_RUNTIME_OWNER_ROUTE_REASON = "quest_waiting_opl_runtime_owner_route"
OWNER_ROUTE_ALLOWED_WRITE_SURFACES = [
    "artifacts/supervision/**",
    "artifacts/autonomy/repair_lifecycle/latest.json",
    "artifacts/autonomy/repair_actions/latest.json",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def text(value: object) -> str | None:
    item = str(value or "").strip()
    return item or None


def mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def owner_route_reason_for_repair(repair_kind: str) -> str:
    if (
        repair_kind
        in {
            "current_controller_owner_handoff_redrive",
            "current_controller_runtime_route_redrive",
            "controller_work_unit_pending_redrive",
            "pending_opl_owner_route_handoff",
            "live_activity_timeout_current_controller_redrive",
        }
        or repair_kind.startswith("domain_transition_")
    ):
        return current_truth_owner.RUNTIME_CONTROLLER_REDRIVE_REASON
    if repair_kind == "stale_specificity_terminal_gate_redrive":
        return "stale_specificity_terminal_gate_cleared"
    return "opl_runtime_owner_route_required"


def owner_route_handoff(
    *,
    runtime_state_path: Path,
    study_id: str,
    quest_id: str | None,
    reason: str,
    repair_kind: str,
    authorization: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    authorization_payload = mapping(authorization)
    return {
        "surface_kind": "mas_runtime_owner_route_handoff",
        "domain_truth_owner": "med-autoscience",
        "queue_owner": "one-person-lab",
        "dispatch_surface": "medautosci domain-handler export -> medautosci domain-handler dispatch",
        "recommended_task_kind": "domain_route/reconcile-apply",
        "study_id": study_id,
        "quest_id": quest_id,
        "runtime_state_path": str(runtime_state_path),
        "source": OPL_OWNER_ROUTE_HANDOFF_SOURCE,
        "reason": reason,
        "repair_kind": repair_kind,
        "recorded_at": utc_now(),
        "decision_id": authorization_payload.get("decision_id"),
        "work_unit_id": authorization_payload.get("work_unit_id"),
        "work_unit_fingerprint": authorization_payload.get("work_unit_fingerprint"),
        "authority_boundary": authority_boundary(),
    }


def authority_boundary() -> dict[str, bool]:
    return {
        "mas_writes_generic_runtime_queue": False,
        "mas_submits_runtime_chat": False,
        "mas_resumes_provider_worker": False,
        "opl_writes_mas_truth": False,
        "mas_owner_receipt_required": True,
    }


def mark_owner_route_handoff(
    *,
    study_root: Path | None = None,
    runtime_state_path: Path,
    study_id: str,
    quest_id: str | None,
    reason: str,
    repair_kind: str,
    authorization: Mapping[str, Any] | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    handoff = owner_route_handoff(
        runtime_state_path=runtime_state_path,
        study_id=study_id,
        quest_id=quest_id,
        reason=reason,
        repair_kind=repair_kind,
        authorization=authorization,
    )
    if extra:
        handoff.update(dict(extra))
    mark = {
        "marked": True,
        "path": str(runtime_state_path),
        "handoff": handoff,
        "runtime_state_mutated": False,
        "artifact_owner": "med-autoscience",
        "artifact_surface": "artifacts/supervision/owner_route_handoff/latest.json",
    }
    if study_root is not None:
        mark["artifact_path"] = str(
            write_owner_route_handoff_record(
                study_root=study_root,
                study_id=study_id,
                quest_id=quest_id,
                handoff=handoff,
                source=OPL_OWNER_ROUTE_HANDOFF_SOURCE,
            )
        )
    return mark


def write_owner_route_handoff_record(
    *,
    study_root: Path,
    study_id: str,
    quest_id: str | None,
    handoff: Mapping[str, Any],
    source: str,
) -> Path:
    handoff_payload = dict(handoff)
    boundary = mapping(handoff_payload.get("authority_boundary")) or authority_boundary()
    record = {
        "surface_kind": "mas_runtime_owner_route_handoff_record",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "recorded_at": text(handoff_payload.get("recorded_at")) or utc_now(),
        "source": source,
        "handoff": handoff_payload,
        "queue_owner": "one-person-lab",
        "domain_truth_owner": "med-autoscience",
        "recommended_task_kind": "domain_route/reconcile-apply",
        "runtime_state_mutated": False,
        "authority_boundary": boundary,
    }
    path = _handoff_record_path(study_root=study_root, study_id=study_id, handoff=handoff_payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _handoff_record_path(*, study_root: Path, study_id: str, handoff: Mapping[str, Any]) -> Path:
    runtime_state_path = text(handoff.get("runtime_state_path"))
    if runtime_state_path is not None:
        runtime_path = Path(runtime_state_path).expanduser().resolve()
        for parent in runtime_path.parents:
            if parent.name == "runtime":
                return parent.parent / "studies" / study_id / "artifacts" / "supervision" / "owner_route_handoff" / "latest.json"
    return Path(study_root).expanduser().resolve() / "artifacts" / "supervision" / "owner_route_handoff" / "latest.json"


def apply_result(
    *,
    base: Mapping[str, Any],
    study_root: Path | None = None,
    study_id: str,
    quest_id: str | None,
    runtime_state_path: Path,
    reason: str,
    repair_kind: str,
    authorization: Mapping[str, Any] | None = None,
    authorization_written: bool | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    extra_payload = mapping(extra)
    handoff_mark = mark_owner_route_handoff(
        study_root=study_root,
        runtime_state_path=runtime_state_path,
        study_id=study_id,
        quest_id=quest_id,
        reason=reason,
        repair_kind=repair_kind,
        authorization=authorization,
        extra=extra_payload,
    )
    payload: dict[str, Any] = {
        **dict(base),
        "allowed_write_surfaces": list(OWNER_ROUTE_ALLOWED_WRITE_SURFACES),
        "dispatch_status": "owner_route_required" if handoff_mark.get("marked") is True else "blocked",
        "reason": reason,
        "repair_kind": repair_kind,
        "queue_owner": "one-person-lab",
        "domain_truth_owner": "med-autoscience",
        "recommended_task_kind": "domain_route/reconcile-apply",
        "opl_runtime_owner_route_handoff": handoff_mark.get("handoff"),
        "opl_runtime_owner_route_mark": handoff_mark,
        "authority_boundary": authority_boundary(),
    }
    if authorization is not None:
        payload["current_controller_authorization"] = authorization
    if authorization_written is not None:
        payload["current_controller_authorization_written"] = authorization_written
    payload.update(extra_payload)
    return payload


__all__ = [
    "OPL_RUNTIME_OWNER_ROUTE_REASON",
    "OPL_OWNER_ROUTE_HANDOFF_SOURCE",
    "apply_result",
    "authority_boundary",
    "mark_owner_route_handoff",
    "owner_route_handoff",
    "owner_route_reason_for_repair",
    "write_owner_route_handoff_record",
]
