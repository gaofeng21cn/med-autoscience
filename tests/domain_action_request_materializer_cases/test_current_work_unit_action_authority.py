from __future__ import annotations

import importlib
import importlib.util


def _selection_module():
    return importlib.import_module(
        "med_autoscience.controllers.domain_action_request_materializer_parts.current_action_selection"
    )


def _next_action_envelope(*, study_id: str, action_type: str) -> dict[str, object]:
    return {
        "surface_kind": "mas_next_action_envelope",
        "action_id": f"next-action::{study_id}::{action_type}",
        "idempotency_key": f"next-action::{study_id}::{action_type}",
        "action_family": "runtime.opl_route",
        "expected_output_contract": {"output_kind": "opl_transition_receipt"},
    }


def test_fresh_progress_current_action_reads_without_live_provider_probe(monkeypatch) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_action_request_materializer_parts.fresh_progress_current_action"
    )
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    observed: dict[str, object] = {}

    def read_study_progress(**kwargs):
        observed.update(kwargs)
        return {"study_id": kwargs["study_id"]}

    monkeypatch.setattr(study_progress, "read_study_progress", read_study_progress)

    payload = module._read_fresh_study_progress(profile=object(), study_id="001-risk")

    assert payload == {"study_id": "001-risk"}
    assert observed["sync_runtime_summary"] is False
    assert observed["materialize_read_model_artifacts"] is False
    assert observed["enable_opl_live_provider_attempt_probe"] is False


def test_current_action_selection_retires_legacy_next_action_without_canonical_envelope() -> None:
    selection = _selection_module()

    actions, ignored = selection.current_actions_for_studies(
        profile=None,
        study_ids=(),
        scan_payload={
            "action_queue": [
                {
                    "study_id": "002-dm-china-us-mortality-attribution",
                    "action_id": "legacy-stage-native-write",
                    "action_type": "run_quality_repair_batch",
                    "authority": "stage_native_workspace_next_action",
                    "next_action": {
                        "surface_kind": "mas_next_action_envelope",
                        "action_id": "incomplete-next-action",
                    },
                }
            ]
        },
    )

    assert actions == []
    assert ignored == [
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "action_type": "run_quality_repair_batch",
            "action_id": "legacy-stage-native-write",
            "reason": selection.LEGACY_NEXT_ACTION_AUTHORITY_RETIRED_REASON,
        }
    ]


def test_current_action_selection_keeps_complete_next_action_envelope() -> None:
    selection = _selection_module()
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action = {
        "study_id": study_id,
        "action_id": "canonical-runtime-route",
        "action_type": "run_gate_clearing_batch",
        "authority": "stage_native_workspace_next_action",
        "next_action": _next_action_envelope(study_id=study_id, action_type="run_gate_clearing_batch"),
    }

    actions, ignored = selection.current_actions_for_studies(
        profile=None,
        study_ids=(),
        scan_payload={"action_queue": [action]},
    )

    assert actions == [action]
    assert ignored == []


def test_current_work_unit_action_producer_is_physically_retired() -> None:
    assert (
        importlib.util.find_spec(
            "med_autoscience.controllers.domain_action_request_materializer_parts.current_work_unit_action"
        )
        is None
    )


def test_current_action_selection_does_not_let_typed_blocker_barrier_preempt_identity_different_action(
    monkeypatch,
) -> None:
    selection = importlib.import_module(
        "med_autoscience.controllers.domain_action_request_materializer_parts.current_action_selection"
    )
    monkeypatch.setattr(
        selection.fresh_progress_current_action,
        "current_actions",
        lambda **_: [],
    )

    actions, ignored = selection.current_actions_for_studies(
        profile=None,
        study_ids=("002-dm-china-us-mortality-attribution",),
        scan_payload={
            "studies": [
                {
                    "study_id": "002-dm-china-us-mortality-attribution",
                    "quest_id": "002-dm-china-us-mortality-attribution",
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "status": "typed_blocker",
                        "owner": "one-person-lab",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": (
                            "domain-transition::route_back_same_line::"
                            "ai_reviewer_record_gate_consumption"
                        ),
                        "state": {
                            "state_kind": "typed_blocker",
                            "typed_blocker": {
                                "blocker_id": "stage_packet_not_current_selected_dispatch",
                                "owner": "one-person-lab",
                                "work_unit_id": "publication_gate_replay",
                            },
                        },
                    },
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "status": "ready",
                        "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                        "next_owner": "analysis-campaign",
                        "action_type": "run_quality_repair_batch",
                        "allowed_actions": ["run_quality_repair_batch"],
                        "work_unit_id": "analysis_claim_evidence_repair",
                        "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                        "target_surface": {
                            "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json"
                        },
                    },
                    "action_queue": [
                        {
                            "study_id": "002-dm-china-us-mortality-attribution",
                            "action_type": "run_gate_clearing_batch",
                            "action_id": "stale-gate-replay",
                            "owner": "one-person-lab",
                            "work_unit_id": "publication_gate_replay",
                            "work_unit_fingerprint": (
                                "domain-transition::route_back_same_line::"
                                "ai_reviewer_record_gate_consumption"
                            ),
                        }
                    ],
                }
            ],
        },
    )

    assert actions is not None
    assert [action["action_type"] for action in actions] == ["current_execution_envelope_typed_blocker"]
    assert actions[0]["reason"] == "stage_packet_not_current_selected_dispatch"
    assert actions[0]["owner"] == "one-person-lab"


def test_current_action_selection_does_not_let_stale_fresh_paper_recovery_callable_preempt_current_work_unit(
    monkeypatch,
) -> None:
    selection = importlib.import_module(
        "med_autoscience.controllers.domain_action_request_materializer_parts.current_action_selection"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    monkeypatch.setattr(
        selection.fresh_progress_current_action,
        "current_actions",
        lambda **_: [],
    )
    monkeypatch.setattr(
        selection.paper_recovery_owner_callable,
        "current_actions",
        lambda **_: {
            study_id: {
                "study_id": study_id,
                "quest_id": study_id,
                "action_type": "run_gate_clearing_batch",
                "action_id": f"paper-recovery-owner-callable::{study_id}::run_gate_clearing_batch",
                "reason": "publication_gate_replay",
                "owner": "gate_clearing_batch",
                "request_owner": "gate_clearing_batch",
                "recommended_owner": "gate_clearing_batch",
                "authority": "paper_recovery_state",
                "source_surface": "paper_recovery_state",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": "sha256:stale-gate",
                "action_fingerprint": "sha256:stale-gate",
            }
        },
    )

    actions, ignored = selection.current_actions_for_studies(
        profile=None,
        study_ids=(study_id,),
        scan_payload={
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "status": "executable_owner_action",
                        "owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                        "action_fingerprint": "publication-blockers::0915410f804b3697",
                        "state": {
                            "state_kind": "executable_owner_action",
                            "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                        },
                    },
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "status": "ready",
                        "source": "canonical_current_work_unit",
                        "next_owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "allowed_actions": ["run_quality_repair_batch"],
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                        "target_surface": {
                            "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json"
                        },
                    },
                    "action_queue": [],
                }
            ],
            "action_queue": [],
        },
    )

    assert actions is not None
    assert [action["action_type"] for action in actions] == ["run_gate_clearing_batch"]
    assert actions[0]["authority"] == "paper_recovery_state"
    assert actions[0]["work_unit_id"] == "publication_gate_replay"
    assert ignored == []
