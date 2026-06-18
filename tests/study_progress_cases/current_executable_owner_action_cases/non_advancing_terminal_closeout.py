from __future__ import annotations

from .. import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


STUDY_ID = "003-dpcc-primary-care-phenotype-treatment-gap"
WRITE_WORK_UNIT = "medical_prose_write_repair"
WRITE_FINGERPRINT = "publication-blockers::0915410f804b3697"


def test_current_owner_action_blocks_same_identity_non_advancing_current_work_unit() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )
    payload = _payload(current_work_unit=_non_advancing_current_work_unit())

    assert module.build_current_executable_owner_action(payload) is None


def test_current_owner_action_blocks_same_identity_record_only_terminal_closeout() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )
    payload = _payload(
        progress_first_monitoring_summary={"latest_terminal_stage": _record_only_terminal_closeout()}
    )

    assert module.build_current_executable_owner_action(payload) is None


def _payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "study_id": STUDY_ID,
        "quest_id": STUDY_ID,
        "current_stage": "publication_supervision",
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "phase": "owner_action_ready",
            "current_authority": {
                "owner": "write",
                "authority": "med-autoscience",
                "obligation": {
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": WRITE_WORK_UNIT,
                    "work_unit_fingerprint": WRITE_FINGERPRINT,
                },
            },
            "next_safe_action": {
                "kind": "materialize_successor_owner_action",
                "owner": "write",
                "provider_admission_allowed": False,
                "successor_owner_action": {
                    "action_type": "run_quality_repair_batch",
                    "owner": "write",
                    "work_unit_id": WRITE_WORK_UNIT,
                    "work_unit_fingerprint": WRITE_FINGERPRINT,
                    "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                    "source_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                },
            },
            "supervisor_decision": {
                "decision": "materialize_recovery_action",
                "identity_match": True,
            },
        },
    }
    payload.update(overrides)
    return payload


def _non_advancing_current_work_unit() -> dict[str, object]:
    return {
        "surface_kind": "current_work_unit",
        "schema_version": 1,
        "status": "typed_blocker",
        "owner": "one-person-lab",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": WRITE_WORK_UNIT,
        "work_unit_fingerprint": WRITE_FINGERPRINT,
        "action_fingerprint": WRITE_FINGERPRINT,
        "state": {
            "state_kind": "typed_blocker",
            "source": "terminal_closeout_typed_blocker",
            "blocker_type": "non_advancing_apply",
            "typed_blocker": {
                "blocker_type": "non_advancing_apply",
                "blocked_reason": "fresh_readback_did_not_advance_same_aggregate",
                "non_advancing_apply": True,
                "provider_completion_is_domain_completion": False,
                "owner": "one-person-lab",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": WRITE_WORK_UNIT,
                "work_unit_fingerprint": WRITE_FINGERPRINT,
                "action_fingerprint": WRITE_FINGERPRINT,
                "terminal_closeout_status": "closed",
                "progress_delta_classification": "platform_repair",
            },
        },
    }


def _record_only_terminal_closeout() -> dict[str, object]:
    return {
        "stage_attempt_id": "sat_f22f2e9d25d336fa2a2a4306",
        "stage_id": "domain_owner/default-executor-dispatch",
        "status": "closed",
        "stage_name": WRITE_WORK_UNIT,
        "outcome": (
            "closed_with_existing_mas_owner_receipt_ref; "
            "provider_completion_is_not_domain_completion"
        ),
        "action_type": "run_quality_repair_batch",
        "next_forced_delta": {
            "required_delta_kind": "consume_existing_owner_receipt_or_route_to_publication_gate_or_ai_reviewer_owner",
            "work_unit_id": WRITE_WORK_UNIT,
            "owner_action": {
                "next_owner": "MedAutoScience",
                "action_type": "consume_owner_receipt",
                "work_unit_id": WRITE_WORK_UNIT,
            },
        },
        "paper_stage_log": {
            "progress_delta_classification": "platform_repair",
            "paper_progress_delta": {"count": 0, "refs": []},
            "deliverable_progress_delta": {"count": 0, "refs": []},
            "remaining_blockers": [
                "provider_completion_is_not_domain_completion",
            ],
        },
    }
