from __future__ import annotations

from med_autoscience.controllers.study_progress_parts.paper_autonomy_supervisor_decision import (
    provider_admission_supervisor_gate,
)
from tests.provider_admission_current_control_helpers import opl_transition_readback


def test_readback_required_projection_accepts_runtime_live_readback_alias() -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    obligation_identity = {
        "study_id": study_id,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
    }
    supervisor_decision = {
        "decision": "opl_supervisor_decision_readback_required",
        "paper_autonomy_obligation_identity": dict(obligation_identity),
    }
    recovery = {
        "surface_kind": "paper_recovery_state",
        "phase": "admission_pending",
        "study_id": study_id,
        "current_authority": {"owner": "write", "obligation": dict(obligation_identity)},
        "supervisor_decision": dict(supervisor_decision),
    }
    readback = opl_transition_readback(
        study_id,
        action_fingerprint=fingerprint,
        work_unit_id=work_unit_id,
        route_identity_key="paper-policy-request:1a379264039c75d0e9cfd8f5",
        attempt_idempotency_key="paper-policy-request:1a379264039c75d0e9cfd8f5",
    )
    candidate = {
        "study_id": study_id,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "route_identity_key": "paper-policy-request:1a379264039c75d0e9cfd8f5",
        "attempt_idempotency_key": "paper-policy-request:1a379264039c75d0e9cfd8f5",
        "opl_transition_readback_source": "opl_domain_progress_transition_runtime_live_readback",
        "opl_domain_progress_transition_runtime_live_readback": readback,
    }

    gate = provider_admission_supervisor_gate(
        {"study_id": study_id, "provider_admission_candidates": [candidate]},
        paper_recovery_state=recovery,
    )

    assert "opl_domain_progress_transition_result" not in candidate
    assert gate == {
        "blocked": False,
        "admission_allowed": True,
        "supervisor_decision": supervisor_decision,
    }
