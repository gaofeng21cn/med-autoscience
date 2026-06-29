from __future__ import annotations

import importlib


def test_current_execution_envelope_default_selector_is_retired_fail_closed() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    result = module.build_current_execution_envelope(
        actions=[
            {
                "action_type": "run_gate_clearing_batch",
                "owner": "gate_clearing_batch",
                "work_unit_id": "legacy-gate-replay",
                "work_unit_fingerprint": "sha256:legacy-gate-replay",
            }
        ],
        live_provider_attempt={"status": "running", "work_unit_id": "legacy-provider-attempt"},
        blocked_reason="legacy_provider_attempt_running",
        next_owner="gate_clearing_batch",
    )

    assert result == {}


def test_current_execution_evidence_is_diagnostic_only() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    result = module.build_current_execution_evidence(
        action_queue=[{"action_type": "run_gate_clearing_batch"}],
        runtime_health={"status": "running"},
        no_op={"reason": "queue_empty"},
        extra={"operator_note": "diagnostic"},
    )

    assert result["surface_kind"] == "legacy_current_execution_evidence"
    assert result["diagnostic_only"] is True
    assert result["authority_boundary"]["status"] == "retired"
    assert result["authority_boundary"]["can_select_next_action"] is False
    assert result["authority_boundary"]["can_start_provider_attempt"] is False
    assert result["action_queue"] == [{"action_type": "run_gate_clearing_batch"}]
    assert result["runtime_health"] == {"status": "running"}
    assert result["no_op"] == [{"reason": "queue_empty"}]
    assert result["operator_note"] == "diagnostic"


def test_current_execution_envelope_retirement_boundary_is_explicit() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    boundary = module.retired_authority_boundary()

    assert boundary["status"] == "retired"
    assert boundary["replacement_authority"] == "StageOutcome -> NextActionEnvelope -> OPL TransitionReceipt"
    assert boundary["can_select_next_action"] is False
    assert boundary["can_authorize_dispatch"] is False
    assert boundary["can_authorize_provider_admission"] is False
    assert boundary["can_start_provider_attempt"] is False
