from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers.domain_route_scan_parts import current_truth_owner


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_runtime_platform_repair_lifecycle(
    *,
    study_root: Path,
    supervision_latest_relative_path: Path,
    study_id: str,
    quest_id: str | None,
    apply_result: Mapping[str, Any],
    allowed_write_surfaces: Sequence[str],
    forbidden_actions: Sequence[str],
) -> dict[str, Any]:
    dispatch_status = _text(apply_result.get("dispatch_status")) or "blocked"
    if dispatch_status == "applied":
        state = "applied"
    elif dispatch_status == "owner_route_required":
        state = "owner_route_required"
    else:
        state = "blocked"
    repair_kind = _text(apply_result.get("repair_kind")) or "stale_specificity_terminal_gate_redrive"
    blocked_reason = None if state == "applied" else _text(apply_result.get("reason"))
    next_owner = (
        "one-person-lab"
        if state == "owner_route_required"
        else current_truth_owner.next_owner_for_reason(blocked_reason)
        or (
            "publication_gate"
            if blocked_reason == "publication_gate_specificity_required"
            else "artifact_os"
            if blocked_reason == "current_package_freshness_required"
            else "external_supervisor"
        )
    )
    payload = {
        "surface": "ai_repair_lifecycle",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "state": state,
        "authority": (
            "observability_only"
            if next_owner in {"publication_gate", "artifact_os", "one-person-lab"}
            else "external_supervisor"
        ),
        "allowed_write_surfaces": list(allowed_write_surfaces),
        "forbidden_actions": list(forbidden_actions),
        "top_action": {
            "action_type": "runtime_platform_repair",
            "repair_kind": repair_kind,
            "owner": "mas_controller",
            "auto_apply_allowed": True,
            "paper_package_mutation_allowed": False,
            "manual_study_patch_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "medical_claim_authoring_allowed": False,
        },
        "auto_apply_allowed": True,
        "last_apply_attempt_at": _utc_now(),
        "applied_at": _utc_now() if state == "applied" else None,
        "blocked_reason": blocked_reason,
        "next_owner": None if state == "applied" else next_owner,
        "external_supervisor_required": state != "applied" and next_owner == "external_supervisor",
        "opl_runtime_owner_route_required": state == "owner_route_required",
        "quality_gate_relaxation_allowed": False,
        "dispatch_status": dispatch_status,
        "last_apply_attempt": dict(apply_result),
        "refs": {
            "supervision_scan": str(study_root / supervision_latest_relative_path),
        },
    }
    _write_json(study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json", payload)
    return payload


__all__ = ["write_runtime_platform_repair_lifecycle"]
