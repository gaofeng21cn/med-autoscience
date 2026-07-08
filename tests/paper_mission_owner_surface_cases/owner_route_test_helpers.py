from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_AI_REPAIR_LIFECYCLE: dict[str, Any] = {
    "state": "blocked",
    "blocked_reason": "domain_transition_ai_reviewer_re_eval",
    "next_owner": "external_supervisor",
    "external_supervisor_required": True,
}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parked_owner_surface_payloads(
    *,
    study_root: Path,
    quest_id: str,
    quest_root: Path,
    publication_eval: dict[str, Any] | None = None,
    truth_epoch: str,
    source_signature: str,
    paper_stage: str,
    quest_status: str = "paused",
    decision: str = "blocked",
    reason: str = "quest_waiting_for_user",
    current_stage: str = "auto_runtime_parked",
    status_updates: dict[str, Any] | None = None,
    progress_updates: dict[str, Any] | None = None,
    ai_repair_lifecycle: dict[str, Any] | None = DEFAULT_AI_REPAIR_LIFECYCLE,
    include_runtime_health: bool = False,
    parked_state: str = "explicit_resume_pending",
) -> tuple[dict[str, Any], dict[str, Any]]:
    truth_snapshot = {
        "truth_epoch": truth_epoch,
        "source_signature": source_signature,
    }
    status_payload: dict[str, Any] = {
        "study_id": study_root.name,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": quest_status,
        "decision": decision,
        "reason": reason,
        "active_run_id": None,
        "study_truth_snapshot": truth_snapshot,
    }
    if publication_eval is not None:
        status_payload["publication_eval"] = publication_eval
    if include_runtime_health:
        status_payload.update(
            {
                "auto_runtime_parked": {
                    "parked": True,
                    "parked_state": parked_state,
                    "awaiting_explicit_wakeup": True,
                    "auto_execution_complete": False,
                },
                "runtime_liveness_audit": {
                    "active_run_id": None,
                    "runtime_audit": {"worker_running": False, "active_run_id": None},
                },
                "runtime_health_snapshot": {
                    "runtime_health_epoch": "runtime-health-epoch-dm002-hard",
                    "canonical_runtime_action": "external_supervisor_required",
                    "attempt_state": "escalated",
                    "retry_budget_remaining": 0,
                    "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
                },
            }
        )
    if status_updates:
        status_payload.update(status_updates)

    progress_payload = parked_progress_payload(
        study_root=study_root,
        quest_id=quest_id,
        quest_root=quest_root,
        status_payload=status_payload,
        paper_stage=paper_stage,
        current_stage=current_stage,
        ai_repair_lifecycle=ai_repair_lifecycle,
    )
    if progress_updates:
        progress_payload.update(progress_updates)
    return status_payload, progress_payload


def parked_progress_payload(
    *,
    study_root: Path,
    quest_id: str,
    quest_root: Path,
    status_payload: dict[str, Any],
    paper_stage: str,
    current_stage: str = "auto_runtime_parked",
    ai_repair_lifecycle: dict[str, Any] | None = DEFAULT_AI_REPAIR_LIFECYCLE,
    include_refs: bool = True,
    include_quality_review_loop: bool = True,
) -> dict[str, Any]:
    progress_payload: dict[str, Any] = {
        "study_id": study_root.name,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": current_stage,
        "paper_stage": paper_stage,
        "supervision": {"active_run_id": None, "health_status": "parked"},
    }
    if include_refs:
        progress_payload["refs"] = {
            "publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")
        }
    if include_quality_review_loop:
        progress_payload["quality_review_loop"] = {"closure_state": "review_required"}
    if "study_truth_snapshot" in status_payload:
        progress_payload["study_truth_snapshot"] = status_payload["study_truth_snapshot"]
    if "auto_runtime_parked" in status_payload:
        progress_payload["auto_runtime_parked"] = status_payload["auto_runtime_parked"]
    if ai_repair_lifecycle is not None:
        progress_payload["ai_repair_lifecycle"] = dict(ai_repair_lifecycle)
    return progress_payload


def assert_owner_route_required(
    *,
    apply_result: dict[str, Any],
    quest_root: Path | None = None,
    ensure_calls: list[dict[str, object]] | None = None,
    pause_calls: list[dict[str, object]] | None = None,
    expected_reason: str | None = None,
) -> dict[str, Any] | None:
    if ensure_calls is not None:
        assert ensure_calls == []
    if pause_calls is not None:
        assert pause_calls == []
    assert "resume_result" not in apply_result
    assert apply_result["dispatch_status"] == "owner_route_required"
    if expected_reason is not None:
        assert apply_result["reason"] == expected_reason
    assert apply_result["queue_owner"] == "one-person-lab"
    assert apply_result["domain_truth_owner"] == "med-autoscience"
    assert apply_result["recommended_task_kind"] == "stage_outcome/opl-handoff"
    assert apply_result["authority_boundary"]["mas_writes_generic_runtime_queue"] is False
    assert apply_result["authority_boundary"]["mas_submits_runtime_chat"] is False
    assert apply_result["authority_boundary"]["mas_resumes_provider_worker"] is False
    assert apply_result["authority_boundary"]["opl_writes_mas_truth"] is False
    assert "quest_root/.ds/runtime_state.json" not in apply_result["allowed_write_surfaces"]
    assert "quest_root/.ds/events.jsonl" not in apply_result["allowed_write_surfaces"]
    handoff = apply_result["opl_runtime_owner_route_handoff"]
    assert handoff["queue_owner"] == "one-person-lab"
    assert handoff["domain_truth_owner"] == "med-autoscience"
    assert handoff["recommended_task_kind"] == "stage_outcome/opl-handoff"
    assert handoff["authority_boundary"]["mas_writes_generic_runtime_queue"] is False
    assert handoff["authority_boundary"]["mas_submits_runtime_chat"] is False
    assert handoff["authority_boundary"]["mas_resumes_provider_worker"] is False
    assert handoff["authority_boundary"]["opl_writes_mas_truth"] is False
    assert handoff["authority_boundary"]["mas_owner_receipt_required"] is True
    if expected_reason is not None:
        assert handoff["reason"] == expected_reason
    if quest_root is None:
        return None
    runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    actual_runtime_state = dict(runtime_state)
    assert "last_opl_runtime_owner_route_handoff" not in actual_runtime_state
    mark = apply_result["opl_runtime_owner_route_mark"]
    handoff_record_path = Path(mark["artifact_path"])
    handoff_record = json.loads(handoff_record_path.read_text(encoding="utf-8"))
    assert handoff_record["runtime_state_mutated"] is False
    assert handoff_record["handoff"]["queue_owner"] == "one-person-lab"
    assert handoff_record["handoff"]["authority_boundary"]["mas_resumes_provider_worker"] is False
    return project_owner_route_runtime_state(actual_runtime_state, apply_result)


def assert_controller_authorization_handoff(
    apply_result: dict[str, Any],
    *,
    expected_decision_id: str | None = None,
    expected_work_unit_id: str | None = None,
) -> dict[str, Any]:
    assert apply_result["current_controller_authorization_written"] is False
    authorization = apply_result["current_controller_authorization"]
    assert authorization["written"] is False
    assert authorization["runtime_state_mutated"] is False
    assert authorization["delegated_runtime_owner"] == "one-person-lab"
    if expected_decision_id is not None:
        assert authorization["decision_id"] == expected_decision_id
    if expected_work_unit_id is not None:
        assert authorization["work_unit_id"] == expected_work_unit_id
    return authorization


def project_owner_route_runtime_state(runtime_state: dict[str, Any], apply_result: dict[str, Any]) -> dict[str, Any]:
    projected = dict(runtime_state)
    for key in (
        "stale_specificity_clear",
        "stale_controller_terminal_clear",
        "owner_handoff_clear",
        "existing_pending_user_message_resume",
    ):
        clear_result = apply_result.get(key)
        if not isinstance(clear_result, dict):
            continue
        if clear_result.get("runtime_state_mutated") is False:
            for cleared_key in clear_result.get("cleared_keys") or []:
                assert cleared_key in runtime_state
        for cleared_key in clear_result.get("cleared_keys") or []:
            projected.pop(cleared_key, None)
        proposed = clear_result.get("proposed_runtime_state")
        if isinstance(proposed, dict):
            projected.update(proposed)
        if clear_result.get("clear_reason"):
            projected["last_owner_route_cleanup"] = {
                "clear_reason": clear_result.get("clear_reason"),
                "cleared_keys": list(clear_result.get("cleared_keys") or []),
                "runtime_state_mutated": False,
                "delegated_runtime_owner": clear_result.get("delegated_runtime_owner"),
            }
    authorization = apply_result.get("current_controller_authorization")
    if isinstance(authorization, dict):
        for cleared_key in authorization.get("cleared_keys") or []:
            projected.pop(cleared_key, None)
        proposed = authorization.get("proposed_runtime_state")
        if isinstance(proposed, dict):
            projected.update(proposed)
    return projected
