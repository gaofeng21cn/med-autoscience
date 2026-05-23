from __future__ import annotations

import json
from pathlib import Path
from typing import Any


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
    assert apply_result["recommended_task_kind"] == "domain_route/owner-handoff"
    assert apply_result["authority_boundary"]["mas_writes_generic_runtime_queue"] is False
    assert apply_result["authority_boundary"]["mas_submits_runtime_chat"] is False
    assert apply_result["authority_boundary"]["mas_resumes_provider_worker"] is False
    assert apply_result["authority_boundary"]["opl_writes_mas_truth"] is False
    assert "quest_root/.ds/runtime_state.json" not in apply_result["allowed_write_surfaces"]
    assert "quest_root/.ds/events.jsonl" not in apply_result["allowed_write_surfaces"]
    handoff = apply_result["opl_runtime_owner_route_handoff"]
    assert handoff["queue_owner"] == "one-person-lab"
    assert handoff["domain_truth_owner"] == "med-autoscience"
    assert handoff["recommended_task_kind"] == "domain_route/owner-handoff"
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
            projected["last_runtime_platform_repair"] = {
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
