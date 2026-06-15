from __future__ import annotations

import importlib


def _module():
    return importlib.import_module(
        "med_autoscience.controllers.domain_action_request_materializer_parts.current_work_unit_action"
    )


def test_canonical_current_work_unit_action_rejects_readiness_typed_blocker_identity() -> None:
    action = _module().canonical_current_work_unit_action(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "typed_blocker",
                "owner": "MedAutoScience",
                "action_type": "complete_medical_paper_readiness_surface",
                "work_unit_id": "complete_medical_paper_readiness_surface",
                "work_unit_fingerprint": (
                    "current-readiness-typed-blocker::"
                    "003-dpcc-primary-care-phenotype-treatment-gap::current"
                ),
                "currentness_basis": {
                    "source": "stage_owner_answer.typed_blocker",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                    "work_unit_fingerprint": (
                        "current-readiness-typed-blocker::"
                        "003-dpcc-primary-care-phenotype-treatment-gap::current"
                    ),
                },
                "state": {
                    "state_kind": "typed_blocker",
                    "typed_blocker": {
                        "blocker_id": "medical_paper_readiness_missing",
                        "owner": "MedAutoScience",
                        "work_unit_id": "complete_medical_paper_readiness_surface",
                    },
                },
            },
            "current_executable_owner_action": {},
            "owner_route": {
                "schema_version": 2,
                "next_owner": "MedAutoScience",
                "allowed_actions": ["complete_medical_paper_readiness_surface"],
                "source_refs": {
                    "owner_route_currentness_basis": {
                        "work_unit_id": "complete_medical_paper_readiness_surface",
                        "work_unit_fingerprint": (
                            "current-readiness-typed-blocker::"
                            "003-dpcc-primary-care-phenotype-treatment-gap::current"
                        ),
                    }
                },
            },
        }
    )

    assert action is None


def test_canonical_current_work_unit_action_allows_identity_different_explicit_owner_action() -> None:
    action = _module().canonical_current_work_unit_action(
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
                    "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption"
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
        }
    )

    assert action is not None
    assert action["source_surface"] == "current_executable_owner_action"
    assert action["action_type"] == "run_quality_repair_batch"
    assert action["owner"] == "analysis-campaign"
    assert action["work_unit_id"] == "analysis_claim_evidence_repair"
    assert action["work_unit_fingerprint"] == "publication-blockers::497d1260db522f01"


def test_current_action_selection_does_not_let_typed_blocker_barrier_preempt_identity_different_action(
    monkeypatch,
) -> None:
    selection = importlib.import_module(
        "med_autoscience.controllers.domain_action_request_materializer_parts.current_action_selection"
    )
    monkeypatch.setattr(
        selection.stage_native_next_action,
        "stage_native_next_actions",
        lambda **_: [],
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
    assert [action["action_type"] for action in actions] == ["run_quality_repair_batch"]
    assert actions[0]["source_surface"] == "current_executable_owner_action"
    assert actions[0]["work_unit_id"] == "analysis_claim_evidence_repair"


def test_current_action_selection_does_not_let_stale_fresh_paper_recovery_callable_preempt_current_work_unit(
    monkeypatch,
) -> None:
    selection = importlib.import_module(
        "med_autoscience.controllers.domain_action_request_materializer_parts.current_action_selection"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    monkeypatch.setattr(
        selection.stage_native_next_action,
        "stage_native_next_actions",
        lambda **_: [],
    )
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
    assert [action["action_type"] for action in actions] == ["run_quality_repair_batch"]
    assert actions[0]["authority"] == "canonical_current_work_unit"
    assert actions[0]["work_unit_id"] == "medical_prose_write_repair"
    assert any(
        action["action_type"] == "run_gate_clearing_batch"
        and action["reason"] == "superseded_by_canonical_current_work_unit"
        for action in ignored
    )
