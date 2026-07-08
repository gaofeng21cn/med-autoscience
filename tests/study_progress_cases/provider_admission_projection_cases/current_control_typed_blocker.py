from __future__ import annotations

from ..provider_admission_projection import (
    _quality_repair_current_work_unit,
    _write_ready_quality_repair_dispatch,
)


def _quality_repair_consumed_typed_blocker_handoff(
    *,
    study_id: str,
    fingerprint: str,
    source: str = "accepted_closeout_consumed_pending",
) -> dict:
    return {
        "surface_kind": "opl_current_control_state_study_handoff",
        "source_path": "/tmp/opl_current_control_state/latest.json",
        "running_provider_attempt": False,
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "typed_blocker",
            "study_id": study_id,
            "quest_id": study_id,
            "owner": "med-autoscience",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "state": {
                "state_kind": "typed_blocker",
                "source": source,
                "typed_blocker": {
                    "blocker_type": "provider_completion_is_not_domain_ready",
                    "owner": "med-autoscience",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": fingerprint,
                    "typed_blocker_ref": (
                        "artifacts/supervision/consumer/owner_callable_adapter_receipt/"
                        "sat_f8e1cfe49a3aa3cf95d0584d.closeout.json"
                    ),
                },
            },
        },
        "current_execution_envelope": {
            "state_kind": "typed_blocker",
            "owner": "med-autoscience",
            "typed_blocker": {
                "blocker_type": "provider_completion_is_not_domain_ready",
                "owner": "med-autoscience",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
            },
            "source": source,
        },
        "provider_admission_candidates": [],
        "provider_admission_pending_count": 0,
        "action_queue": [],
    }


def _current_executable_quality_repair_payload(*, study_id: str, fingerprint: str) -> dict:
    return {
        "study_id": study_id,
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "publication_eval.recommended_actions.readiness_blocker_repair",
            "next_owner": "write",
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
        },
        "current_work_unit": _quality_repair_current_work_unit(
            study_id=study_id,
            fingerprint=fingerprint,
            status="executable_owner_action",
        ),
        "current_execution_envelope": {
            "state_kind": "executable_owner_action",
            "owner": "write",
            "next_work_unit": "medical_prose_write_repair",
        },
    }


from .current_control_typed_blocker_cases.handoff_blockers import (
    test_provider_admission_projection_honors_handoff_consumed_typed_blocker,
    test_existing_projection_refresh_keeps_current_control_typed_blocker_over_stale_action,
)
from .current_control_typed_blocker_cases.gate_followthrough_successors import (
    test_existing_projection_refresh_promotes_progress_first_gate_followthrough_successor_over_consumed_gate_blocker,
    test_existing_projection_refresh_promotes_selected_gate_successor_over_stale_selector_residue,
    test_existing_projection_refresh_promotes_gate_followthrough_successor_over_opl_authorization_residue,
    test_existing_projection_refresh_keeps_paper_recovery_successor_over_stage_readiness_residue,
)
from .current_control_typed_blocker_cases.repair_progress_successors import (
    test_existing_projection_refresh_materializes_recovery_successor_after_consumed_owner_receipt_with_stale_opl_blocker,
    test_existing_projection_refresh_ignores_current_control_executable_residue_without_opl_readback,
    test_existing_projection_refresh_consumes_current_repair_progress_over_stale_gate_replay,
    test_existing_projection_refresh_consumes_current_repair_successor_over_refs_only_handoff,
    test_existing_projection_refresh_materializes_recovery_successor_over_stale_gate_followup,
    test_existing_projection_refresh_promotes_domain_transition_after_consumed_provider_completion_blocker,
)
from .current_control_typed_blocker_cases.current_handoff_blockers import (
    test_provider_admission_projection_ignores_unconsumed_handoff_typed_blocker,
    test_existing_projection_refresh_honors_current_control_typed_blocker,
    test_current_execution_refresh_keeps_handoff_current_typed_blocker_over_gate_followthrough_residue,
)
