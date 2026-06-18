from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.profiles import WorkspaceProfile

from med_autoscience.controllers.domain_dispatch_evidence_payload import (
    build_domain_dispatch_evidence_record_payload,
)


_AUTO_CONTINUATION_BLOCKING_DECISIONS = {"stop_loss", "terminal_stop", "completed"}


def controller_decision_route_back_task(
    *,
    study: Mapping[str, Any],
    current_progress: Mapping[str, Any] | None = None,
    profile: WorkspaceProfile,
    profile_ref: Path,
    study_id: str,
) -> dict[str, Any] | None:
    controller = _mapping(study.get("controller_decisions"))
    if not controller:
        return None
    if _hard_human_gate_required(controller) or _terminal_controller_decision(controller):
        return None
    if _text(controller.get("decision_type")) != "route_back_same_line":
        return None
    route_target = _text(controller.get("route_target"))
    next_work_unit = _mapping(controller.get("next_work_unit"))
    work_unit_id = _text(next_work_unit.get("unit_id"))
    if route_target is None or work_unit_id is None:
        return None
    if _owner_receipt_recorded_for_work_unit(
        current_progress or {},
        action_type="run_quality_repair_batch",
        work_unit_id=work_unit_id,
    ):
        return None
    study_root = Path(_text(study.get("study_root")) or profile.studies_root / study_id)
    controller_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    controller_ref = _workspace_relative(controller_path, workspace_root=profile.workspace_root)
    source_fingerprint = _fingerprint(
        {
            "decision_id": _text(controller.get("decision_id")),
            "emitted_at": _text(controller.get("emitted_at")),
            "decision_type": _text(controller.get("decision_type")),
            "route_target": route_target,
            "next_work_unit": dict(next_work_unit),
            "work_unit_fingerprint": _text(controller.get("work_unit_fingerprint")),
            "controller_actions": controller.get("controller_actions"),
        }
    )
    source_refs = [
        {
            "role": "mas_controller_decision_route_back",
            "ref": controller_ref,
            "exists": controller_path.exists(),
        }
    ]
    evidence_record_payload = build_domain_dispatch_evidence_record_payload(
        task_kind="domain_route/reconcile-apply",
        study_id=study_id,
        reason="controller_decision_route_back",
        evidence_refs=source_refs,
        source_fingerprint=source_fingerprint,
        profile_name=profile.name,
    )
    return {
        "domain_id": "medautoscience",
        "task_kind": "domain_route/reconcile-apply",
        "recommended_task_kind": "domain_route/reconcile-apply",
        "priority": 70,
        "source": "mas-controller-decision",
        "requires_approval": False,
        "dedupe_key": f"mas:{profile.name}:{study_id}:controller-decision:{source_fingerprint}",
        "source_fingerprint": source_fingerprint,
        "domain_truth_owner": "med-autoscience",
        "queue_owner": "one-person-lab",
        "reason": "controller_decision_route_back",
        "source_refs": source_refs,
        "dispatch_owner": "med-autoscience",
        "profile_name": profile.name,
        "domain_dispatch_evidence_record_payload": evidence_record_payload,
        "payload": {
            "profile": str(profile_ref),
            "study_id": study_id,
            "source_fingerprint": source_fingerprint,
            "continuation_reason": "controller_decision_route_back",
            "route_target": route_target,
            "route_key_question": _text(controller.get("route_key_question")),
            "route_rationale": _text(controller.get("route_rationale")),
            "next_work_unit": dict(next_work_unit),
            "blocking_work_units": [
                dict(unit)
                for unit in controller.get("blocking_work_units") or []
                if isinstance(unit, Mapping)
            ],
            "work_unit_fingerprint": (
                _text(controller.get("work_unit_fingerprint"))
                or f"controller-decision::{route_target}::{work_unit_id}"
            ),
            "controller_decision_ref": controller_ref,
            "authority_boundary": "mas_owner_reconcile_only",
        },
    }


def _owner_receipt_recorded_for_work_unit(
    progress: Mapping[str, Any],
    *,
    action_type: str,
    work_unit_id: str,
) -> bool:
    current_work_unit = _mapping(progress.get("current_work_unit"))
    current_work_unit_state = _mapping(current_work_unit.get("state"))
    if _text(current_work_unit.get("status")) != "owner_receipt_recorded":
        return False
    if _text(current_work_unit_state.get("state_kind")) not in {None, "owner_receipt_recorded"}:
        return False
    if _text(current_work_unit.get("action_type")) not in {None, action_type}:
        return False
    if _text(current_work_unit.get("work_unit_id")) != work_unit_id:
        return False
    return _owner_receipt_ref(current_work_unit) is not None or _owner_receipt_ref(
        _mapping(progress.get("current_execution_envelope"))
    ) is not None


def _owner_receipt_ref(surface: Mapping[str, Any]) -> str | None:
    state = _mapping(surface.get("state"))
    binding = _mapping(surface.get("owner_answer_binding")) or _mapping(
        state.get("owner_answer_binding")
    )
    return (
        _text(surface.get("owner_receipt_ref"))
        or _text(state.get("owner_receipt_ref"))
        or _text(binding.get("owner_receipt_ref"))
    )


def _hard_human_gate_required(controller: Mapping[str, Any]) -> bool:
    if bool(controller.get("requires_human_confirmation")):
        return True
    gates = controller.get("family_human_gates")
    return isinstance(gates, list) and len(gates) > 0


def _terminal_controller_decision(controller: Mapping[str, Any]) -> bool:
    decision_type = _text(controller.get("decision_type"))
    route_target = _text(controller.get("route_target"))
    return decision_type in _AUTO_CONTINUATION_BLOCKING_DECISIONS or route_target == "stop"


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _workspace_relative(path: Path, *, workspace_root: Path) -> str:
    try:
        return str(path.relative_to(workspace_root))
    except ValueError:
        return str(path)


def _fingerprint(value: object) -> str:
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()[:16]


__all__ = ["controller_decision_route_back_task"]
