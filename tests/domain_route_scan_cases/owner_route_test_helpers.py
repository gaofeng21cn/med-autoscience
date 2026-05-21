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
    assert apply_result["recommended_task_kind"] == "domain_route/reconcile-apply"
    assert apply_result["authority_boundary"]["mas_writes_generic_runtime_queue"] is False
    assert apply_result["authority_boundary"]["mas_submits_runtime_chat"] is False
    assert apply_result["authority_boundary"]["mas_resumes_provider_worker"] is False
    assert apply_result["authority_boundary"]["opl_writes_mas_truth"] is False
    assert "quest_root/.ds/runtime_state.json" not in apply_result["allowed_write_surfaces"]
    assert "quest_root/.ds/events.jsonl" not in apply_result["allowed_write_surfaces"]
    handoff = apply_result["opl_runtime_owner_route_handoff"]
    assert handoff["queue_owner"] == "one-person-lab"
    assert handoff["domain_truth_owner"] == "med-autoscience"
    assert handoff["recommended_task_kind"] == "domain_route/reconcile-apply"
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
    assert "last_opl_runtime_owner_route_handoff" not in runtime_state
    handoff_record_path = (
        quest_root.parents[2]
        / "studies"
        / apply_result["opl_runtime_owner_route_handoff"]["study_id"]
        / "artifacts"
        / "supervision"
        / "owner_route_handoff"
        / "latest.json"
    )
    handoff_record = json.loads(handoff_record_path.read_text(encoding="utf-8"))
    assert handoff_record["runtime_state_mutated"] is False
    assert handoff_record["handoff"]["queue_owner"] == "one-person-lab"
    assert handoff_record["handoff"]["authority_boundary"]["mas_resumes_provider_worker"] is False
    return runtime_state
