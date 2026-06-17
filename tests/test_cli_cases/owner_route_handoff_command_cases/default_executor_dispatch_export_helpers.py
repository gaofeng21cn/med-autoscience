from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_TRANSITION_REQUEST_CARRIER_FIELDS = {
    "transition_request_status": "transition_request_pending",
    "carrier_status": "transition_request_pending",
    "carrier_kind": "opl_domain_progress_transition_request_carrier",
    "legacy_surface": "default_executor_dispatch_request",
    "legacy_carrier_projection": True,
    "provider_admission_pending": False,
    "provider_admission_requires_opl_runtime_result": True,
    "provider_attempt_or_lease_required": False,
    "mas_private_attempt_loop_forbidden": True,
    "mas_dispatch_authority": False,
    "mas_creates_owner_callable_carrier": False,
    "mas_creates_opl_outbox": False,
    "mas_creates_opl_event": False,
    "mas_creates_opl_stage_run": False,
    "opl_transition_runtime_required": True,
}

_TRANSITION_REQUEST_PAYLOAD_FIELDS = {
    key: value
    for key, value in _TRANSITION_REQUEST_CARRIER_FIELDS.items()
    if key
    not in {
        "transition_request_status",
        "carrier_status",
        "carrier_kind",
        "legacy_surface",
    }
}


def _assert_fields(actual: dict[str, Any], expected: dict[str, Any]) -> None:
    assert {key: actual[key] for key in expected} == expected


def assert_transition_request_carrier(task: dict[str, Any]) -> None:
    payload = task["payload"]
    assert isinstance(payload, dict)
    assert "status" not in task
    assert "dispatch_status" not in task
    _assert_fields(task, _TRANSITION_REQUEST_CARRIER_FIELDS)
    _assert_fields(payload, _TRANSITION_REQUEST_PAYLOAD_FIELDS)
    assert payload["authority_boundary"]["target_runtime_kind"] == "DomainProgressTransitionRuntime"
    assert payload["authority_boundary"]["mas_can_authorize_provider_admission"] is False
    transition_request = payload["opl_domain_progress_transition_request"]
    assert transition_request["surface_kind"] == "mas_domain_progress_transition_request"
    assert transition_request["target_runtime_owner"] == "one-person-lab"
    assert transition_request["mas_can_create_opl_outbox_record"] is False
    assert transition_request["mas_can_create_opl_stage_run"] is False
    assert "provider_admission_identity" not in payload


def assert_dispatch_requests_opl_transition_runtime_intake(
    cli: Any,
    tmp_path: Path,
    capsys: Any,
    task: dict[str, Any],
    write_json: Any,
) -> None:
    task_path = tmp_path / "exported-default-executor-transition-request.json"
    write_json(task_path, task)
    dispatch_exit_code = cli.main(["domain-handler", "dispatch", "--task", str(task_path), "--format", "json"])
    dispatch_payload = json.loads(capsys.readouterr().out)
    assert dispatch_exit_code == 0
    assert dispatch_payload["accepted"] is True
    assert dispatch_payload["opl_attempt_admission_requested"] is False
    assert dispatch_payload["opl_attempt_admission_status"] == "not_requested"
    assert dispatch_payload["opl_domain_progress_transition_runtime_intake_requested"] is True
    assert dispatch_payload["dispatch"]["execution_policy"] == (
        "opl_domain_progress_transition_runtime_intake_required"
    )
    dispatch_result = dispatch_payload["dispatch"]["result"]
    assert dispatch_result["surface"] == "default_executor_transition_request_intake"
    assert dispatch_result["authority_boundary"] == "mas_domain_progress_transition_request_only"
    assert dispatch_result["provider_admission_requires_opl_runtime_result"] is True
    assert dispatch_result["mas_can_authorize_provider_admission"] is False
    assert dispatch_result["mas_can_create_opl_event"] is False
    assert dispatch_result["mas_can_create_opl_outbox_record"] is False
    assert dispatch_result["mas_can_create_opl_stage_run"] is False
