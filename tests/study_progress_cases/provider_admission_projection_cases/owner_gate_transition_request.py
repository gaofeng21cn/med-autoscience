from __future__ import annotations

import importlib
import json

from tests.study_runtime_test_helpers import make_profile, write_study
from tests.study_progress_cases.shared import _write_json
from tests.study_progress_cases.provider_admission_projection import (
    _accepted_owner_gate_stage_packet_payload,
    _opl_transition_result,
    _quality_repair_current_work_unit,
    _quality_repair_handoff,
    _write_ready_quality_repair_dispatch,
)


def test_provider_admission_projection_clears_candidates_under_typed_blocker(tmp_path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_quality_repair_dispatch(study_root, study_id=study_id, fingerprint=fingerprint)

    fields = module.provider_admission_projection_fields(
        payload={
            "study_id": study_id,
            "current_work_unit": _quality_repair_current_work_unit(
                study_id=study_id,
                fingerprint=fingerprint,
                status="typed_blocker",
            ),
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "write",
                "typed_blocker": {
                    "blocker_type": "medical_publication_surface_blocked",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": fingerprint,
                },
            },
        },
        handoff=_quality_repair_handoff(study_id=study_id, fingerprint=fingerprint),
        study_root=study_root,
    )

    assert fields == {
        "provider_admission_pending_count": 0,
        "provider_admission_candidates": [],
        "transition_request_pending_count": 0,
        "transition_request_candidates": [],
    }


def test_provider_admission_projection_preserves_complete_opl_readback_under_typed_blocker(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    readback = _opl_transition_result(
        study_id=study_id,
        work_unit_id=work_unit_id,
        fingerprint=fingerprint,
    )

    fields = module.provider_admission_projection_fields(
        payload={
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": _quality_repair_current_work_unit(
                study_id=study_id,
                fingerprint=fingerprint,
                status="typed_blocker",
            ),
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "write",
                "typed_blocker": {
                    "blocker_type": "medical_publication_surface_blocked",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                },
            },
        },
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "source_path": "/tmp/opl_current_control_state/latest.json",
            "running_provider_attempt": False,
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [
                {
                    "source": "opl_current_control_state.provider_admission_candidates",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "status": "provider_admission_pending",
                    "next_executable_owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "provider_attempt_or_lease_required": True,
                    "opl_domain_progress_transition_runtime_live_readback": readback,
                }
            ],
            "action_queue": [],
        },
        study_root=study_root,
    )

    assert fields["provider_admission_pending_count"] == 1
    assert fields["transition_request_pending_count"] == 0
    candidate = fields["provider_admission_candidates"][0]
    assert candidate["status"] == "provider_admission_pending"
    assert candidate["provider_admission_requires_opl_runtime_result"] is False
    assert candidate["opl_transition_readback_source"] == (
        "opl_domain_progress_transition_runtime_live_readback"
    )
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["work_unit_fingerprint"] == fingerprint


def test_provider_admission_projection_materializes_accepted_owner_gate_transition_request(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    stage_packet_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/"
        "immutable/run_quality_repair_batch/33abc53e0c18295f5fa03738.json"
    )
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_quality_repair_dispatch(study_root, study_id=study_id, fingerprint=fingerprint)
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    dispatch_payload = json.loads(dispatch_path.read_text(encoding="utf-8"))
    for key in (
        "opl_domain_progress_transition_result",
        "opl_domain_progress_transition_runtime_live_readback",
        "opl_transition_readback_source",
    ):
        dispatch_payload.pop(key, None)
    _write_json(dispatch_path, dispatch_payload)

    fields = module.provider_admission_projection_fields(
        payload=_accepted_owner_gate_stage_packet_payload(
            study_id=study_id,
            work_unit_id=work_unit_id,
            fingerprint=fingerprint,
            stage_packet_ref=stage_packet_ref,
        ),
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "source_path": "/tmp/opl_current_control_state/latest.json",
            "running_provider_attempt": False,
            "action_queue": [],
        },
        study_root=study_root,
    )

    assert fields["provider_admission_pending_count"] == 0
    assert fields["provider_admission_candidates"] == []
    assert fields["transition_request_pending_count"] == 1
    candidate = fields["transition_request_candidates"][0]
    assert candidate["source"] == "opl_current_control_state.study_current_executable_owner_action"
    assert candidate["status"] == "transition_request_pending"
    assert candidate["provider_admission_pending"] is False
    assert candidate["provider_admission_requires_opl_runtime_result"] is True
    assert candidate["mas_owner_action_source"] == "paper_recovery_state.accepted_owner_gate_decision"
    assert candidate["action_type"] == "run_quality_repair_batch"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["work_unit_fingerprint"] == fingerprint
    assert candidate["currentness_basis"]["source"] == "paper_recovery_state.accepted_owner_gate_decision"


def test_provider_admission_projection_owner_receipt_consumes_accepted_owner_gate_transition_request(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    receipt_ref = (
        f"studies/{study_id}/artifacts/controller/repair_execution_receipts/latest.json"
    )
    stage_packet_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/"
        "immutable/run_quality_repair_batch/33abc53e0c18295f5fa03738.json"
    )
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_quality_repair_dispatch(study_root, study_id=study_id, fingerprint=fingerprint)
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    dispatch_payload = json.loads(dispatch_path.read_text(encoding="utf-8"))
    for key in (
        "opl_domain_progress_transition_result",
        "opl_domain_progress_transition_runtime_live_readback",
        "opl_transition_readback_source",
    ):
        dispatch_payload.pop(key, None)
    _write_json(dispatch_path, dispatch_payload)
    payload = _accepted_owner_gate_stage_packet_payload(
        study_id=study_id,
        work_unit_id=work_unit_id,
        fingerprint=fingerprint,
        stage_packet_ref=stage_packet_ref,
    )
    payload["paper_recovery_state"]["current_authority"] = {
        "owner": "write",
        "authority": "med-autoscience",
        "obligation": {
            "study_id": study_id,
            "quest_id": study_id,
            "owner": "write",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
        },
    }
    payload["current_work_unit"] = {
        "surface_kind": "current_work_unit",
        "schema_version": 1,
        "status": "owner_receipt_recorded",
        "study_id": study_id,
        "quest_id": study_id,
        "stage_id": "publication_supervision",
        "owner": "write",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "acceptance_refs": [receipt_ref],
        "required_output_contract": {
            "owner_receipt_consumed": True,
            "owner_receipt_ref": receipt_ref,
            "provider_completion_is_domain_completion": False,
            "domain_ready_authorized": False,
        },
        "currentness_basis": {
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "truth_epoch": "truth-event-000035-39f0b8e96689a623",
            "runtime_health_epoch": "runtime-health-event-006980-c004aeb3b04b4dc7",
        },
        "state": {
            "state_kind": "owner_receipt_recorded",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "owner_receipt_ref": receipt_ref,
            "next_safe_action_kind": "consume_owner_receipt",
            "provider_admission_pending": False,
        },
    }
    payload["current_execution_envelope"] = {
        "state_kind": "owner_receipt_recorded",
        "owner": "write",
        "source_refs": [receipt_ref],
    }
    payload["current_executable_owner_action"] = None

    fields = module.provider_admission_projection_fields(
        payload=payload,
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "source_path": "/tmp/opl_current_control_state/latest.json",
            "running_provider_attempt": False,
            "action_queue": [],
        },
        study_root=study_root,
    )

    assert fields["provider_admission_pending_count"] == 0
    assert fields["provider_admission_candidates"] == []
    assert fields["transition_request_pending_count"] == 0
    assert fields["transition_request_candidates"] == []
    consumed = fields["owner_receipt_transition_request_consumed"]
    assert consumed["owner_receipt_ref"] == receipt_ref
    assert consumed["action_type"] == "run_quality_repair_batch"
    assert consumed["work_unit_id"] == work_unit_id
    assert consumed["work_unit_fingerprint"] == fingerprint


def test_provider_admission_projection_owner_gate_admission_supersedes_terminal_closeout(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    stage_attempt_id = "sat_08da46bea43329723d2fbbea"
    stage_packet_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/"
        "immutable/run_quality_repair_batch/33abc53e0c18295f5fa03738.json"
    )
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_quality_repair_dispatch(study_root, study_id=study_id, fingerprint=fingerprint)
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    dispatch_payload = json.loads(dispatch_path.read_text(encoding="utf-8"))
    for key in (
        "opl_domain_progress_transition_result",
        "opl_domain_progress_transition_runtime_live_readback",
        "opl_transition_readback_source",
    ):
        dispatch_payload.pop(key, None)
    _write_json(dispatch_path, dispatch_payload)
    typed_blocker = {
        "surface_kind": "mas_domain_typed_blocker",
        "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
        "blocked_reason": "no_selected_dispatch_for_authorized_stage_packet",
        "stage_attempt_id": stage_attempt_id,
        "owner": "one-person-lab",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
    }
    payload = _accepted_owner_gate_stage_packet_payload(
        study_id=study_id,
        work_unit_id=work_unit_id,
        fingerprint=fingerprint,
        stage_packet_ref=stage_packet_ref,
    )
    current_work_unit = payload["current_work_unit"]
    assert isinstance(current_work_unit, dict)
    current_work_unit["currentness_basis"] = {
        "source": "study_intervention_event.owner_gate_decision",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "truth_epoch": "truth-event-000035-39f0b8e96689a623",
        "runtime_health_epoch": "runtime-health-event-006980-82d8638211349896",
        "stage_attempt_id": stage_attempt_id,
    }
    current_work_unit["state"] = {
        "state_kind": "typed_blocker",
        "source": "terminal_closeout_typed_blocker",
        "typed_blocker": typed_blocker,
    }
    payload["current_execution_envelope"] = {
        "state_kind": "typed_blocker",
        "owner": "one-person-lab",
        "typed_blocker": typed_blocker,
    }

    fields = module.provider_admission_projection_fields(
        payload=payload,
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "source_path": "/tmp/opl_current_control_state/latest.json",
            "running_provider_attempt": False,
            "action_queue": [],
            "provider_admission_terminal_closeout_consumed": {
                "surface_kind": "provider_admission_terminal_closeout_consumed",
                "source": "opl_current_control_state_handoff.latest_terminal_stage_log",
                "stage_attempt_id": stage_attempt_id,
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "typed_blocker": typed_blocker,
            },
            "typed_blocker": typed_blocker,
            "latest_terminal_stage_log": {
                "stage_attempt_id": stage_attempt_id,
                "typed_blocker": typed_blocker,
            },
        },
        study_root=study_root,
    )

    assert "provider_admission_terminal_closeout_consumed" not in fields
    assert fields["provider_admission_pending_count"] == 0
    assert fields["provider_admission_candidates"] == []
    assert fields["transition_request_pending_count"] == 1
    candidate = fields["transition_request_candidates"][0]
    assert candidate["status"] == "transition_request_pending"
    assert candidate["provider_admission_requires_opl_runtime_result"] is True
    assert candidate["action_type"] == "run_quality_repair_batch"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["work_unit_fingerprint"] == fingerprint
    assert candidate["mas_owner_action_source"] == "paper_recovery_state.accepted_owner_gate_decision"


def test_provider_admission_projection_rejects_owner_gate_admission_without_condition(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    stage_packet_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/"
        "immutable/run_quality_repair_batch/33abc53e0c18295f5fa03738.json"
    )
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_quality_repair_dispatch(study_root, study_id=study_id, fingerprint=fingerprint)

    fields = module.provider_admission_projection_fields(
        payload=_accepted_owner_gate_stage_packet_payload(
            study_id=study_id,
            work_unit_id=work_unit_id,
            fingerprint=fingerprint,
            stage_packet_ref=stage_packet_ref,
            include_owner_gate_condition=False,
        ),
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "source_path": "/tmp/opl_current_control_state/latest.json",
            "running_provider_attempt": False,
            "action_queue": [],
        },
        study_root=study_root,
    )

    assert fields == {
        "provider_admission_pending_count": 0,
        "provider_admission_candidates": [],
        "transition_request_pending_count": 0,
        "transition_request_candidates": [],
    }


def test_provider_admission_projection_rejects_owner_gate_admission_without_stage_packet_ref(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    stage_packet_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/"
        "immutable/run_quality_repair_batch/33abc53e0c18295f5fa03738.json"
    )
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_quality_repair_dispatch(study_root, study_id=study_id, fingerprint=fingerprint)

    fields = module.provider_admission_projection_fields(
        payload=_accepted_owner_gate_stage_packet_payload(
            study_id=study_id,
            work_unit_id=work_unit_id,
            fingerprint=fingerprint,
            stage_packet_ref=stage_packet_ref,
            include_stage_packet_ref=False,
        ),
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "source_path": "/tmp/opl_current_control_state/latest.json",
            "running_provider_attempt": False,
            "action_queue": [],
        },
        study_root=study_root,
    )

    assert fields == {
        "provider_admission_pending_count": 0,
        "provider_admission_candidates": [],
        "transition_request_pending_count": 0,
        "transition_request_candidates": [],
    }
