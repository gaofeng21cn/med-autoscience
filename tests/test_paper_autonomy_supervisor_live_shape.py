from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.paper_autonomy_supervisor import (
    ALLOWED_DECISIONS as SUPERVISOR_ALLOWED_DECISIONS,
    build_paper_autonomy_obligation,
    build_supervisor_decision,
)
from med_autoscience.controllers.paper_recovery_state import build_paper_recovery_state


EXPECTED_STUDY_IDS = {
    "002-dm-china-us-mortality-attribution",
    "003-dpcc-primary-care-phenotype-treatment-gap",
}

ALLOWED_SUPERVISOR_DECISIONS = {
    *SUPERVISOR_ALLOWED_DECISIONS,
}

FORBIDDEN_TERMINAL_DECISIONS = {
    "idle",
    "observe_only",
    "queue_empty",
    "provider_healthy",
    "read_model_refreshed",
    "operator_decision_required",
}


def test_dm002_dm003_zero_queue_live_shape_emits_one_non_idle_supervisor_decision_per_study() -> None:
    decisions = _decisions_by_study(_dm002_dm003_dhd_live_shape())

    assert set(decisions) == EXPECTED_STUDY_IDS
    for decision in decisions.values():
        assert decision["surface_kind"] == "paper_autonomy_supervisor_decision"
        assert decision["decision"] in ALLOWED_SUPERVISOR_DECISIONS
        assert decision["decision"] not in FORBIDDEN_TERMINAL_DECISIONS
        assert decision["identity_match"] is True
        assert "provider_admission_pending_count=0" in decision["forbidden_interpretations"]
        assert "action_queue=[]" in decision["forbidden_interpretations"]
        assert "provider_admission_pending_count=0_is_not_terminal" in decision[
            "forbidden_interpretations"
        ]
        assert "action_queue=[]_is_not_terminal" in decision["forbidden_interpretations"]


def test_dm002_dm003_current_blockers_materialize_recovery_actions_when_owner_callable_is_allowed() -> None:
    decisions = _decisions_by_study(_dm002_dm003_dhd_live_shape())

    dm002 = decisions["002-dm-china-us-mortality-attribution"]
    assert dm002["decision"] == "materialize_recovery_action"
    assert dm002["next_owner"] == "MedAutoScience"
    assert dm002["next_safe_action"]["recovery_kind"] == "mas_control_plane_repair"
    assert dm002["next_safe_action"]["source_next_safe_action"]["kind"] == "run_mas_owner_callable"
    assert dm002["next_safe_action"]["source_next_safe_action"]["owner_callable"][
        "callable_surface"
    ] == "medical_paper_readiness.complete_medical_paper_readiness_surface"
    assert dm002["source_paper_recovery_phase"] == "owner_action_ready"
    assert dm002["paper_progress_classification"] == "none_until_owner_receipt_or_stable_blocker"

    dm003 = decisions["003-dpcc-primary-care-phenotype-treatment-gap"]
    assert dm003["decision"] == "materialize_recovery_action"
    assert dm003["next_owner"] == "publication_gate"
    assert dm003["next_safe_action"]["recovery_kind"] == "mas_control_plane_repair"
    assert dm003["next_safe_action"]["source_next_safe_action"]["kind"] == "run_mas_owner_callable"
    assert dm003["next_safe_action"]["source_next_safe_action"]["owner_callable"][
        "callable_surface"
    ] == "gate_clearing_batch.run_gate_clearing_batch"
    assert dm003["source_paper_recovery_phase"] == "owner_action_ready"
    assert dm003["paper_progress_classification"] == "none_until_owner_receipt_or_stable_blocker"


def test_paper_recovery_state_embeds_same_supervisor_decision_for_dm002_dm003_live_shape() -> None:
    report = _dm002_dm003_dhd_live_shape()

    for study_id, progress in report["progress_currentness"].items():
        state = build_paper_recovery_state(
            progress,
            diagnostic_report={
                "action_class": report["action_class"],
                "will_start_llm": report["will_start_llm"],
                "codex_dispatch_count": report["codex_dispatch_count"],
                "provider_admission_pending_count": report["provider_admission_pending_count"],
            },
        )
        direct_decision = build_supervisor_decision(progress, paper_recovery_state=state)

        assert state["supervisor_decision"] == direct_decision
        assert state["supervisor_decision"]["decision"] == "materialize_recovery_action"
        assert state["supervisor_decision"]["decision"] in ALLOWED_SUPERVISOR_DECISIONS
        assert "provider_admission_pending_count=0" in state["supervisor_decision"][
            "forbidden_interpretations"
        ]
        assert "action_queue=[]" in state["supervisor_decision"]["forbidden_interpretations"]
        assert state["study_id"] == study_id


def test_owner_receipt_recorded_live_shape_is_allowed_terminal_supervisor_decision() -> None:
    progress = _owner_receipt_recorded_progress_payload()
    state = build_paper_recovery_state(progress)
    decision = build_supervisor_decision(progress, paper_recovery_state=state)

    assert state["phase"] == "owner_receipt_recorded"
    assert state["supervisor_decision"] == decision
    assert decision["decision"] == "stop_with_owner_receipt"
    assert decision["decision"] in ALLOWED_SUPERVISOR_DECISIONS
    assert decision["decision"] not in FORBIDDEN_TERMINAL_DECISIONS
    assert decision["next_safe_action"]["kind"] == "consume_owner_receipt"
    assert decision["next_safe_action"]["owner_receipt_ref"] == "owner-receipt:dm003:gate"
    assert decision["paper_progress_classification"] == "mas_owner_receipt_credit"
    assert "owner-receipt:dm003:gate" in decision["evidence_refs"]


def test_live_shape_obligation_preserves_current_identity_not_queue_empty_as_root() -> None:
    report = _dm002_dm003_dhd_live_shape()
    progress = report["progress_currentness"]["003-dpcc-primary-care-phenotype-treatment-gap"]
    state = build_paper_recovery_state(progress)

    obligation = build_paper_autonomy_obligation(progress, paper_recovery_state=state)

    assert obligation["surface_kind"] == "paper_autonomy_obligation"
    assert obligation["study_id"] == "003-dpcc-primary-care-phenotype-treatment-gap"
    assert obligation["action_type"] == "run_gate_clearing_batch"
    assert obligation["work_unit_id"] == "publication_gate_replay"
    assert obligation["work_unit_fingerprint"] == (
        "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f"
    )
    assert obligation["desired_delta"]["owner"] == "publication_gate"
    assert obligation["source_recovery_phase"] == "owner_action_ready"


def _decisions_by_study(report: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    decisions: dict[str, Mapping[str, Any]] = {}
    for study_id, progress in report["progress_currentness"].items():
        state = build_paper_recovery_state(
            progress,
            diagnostic_report={
                "action_class": report["action_class"],
                "will_start_llm": report["will_start_llm"],
                "codex_dispatch_count": report["codex_dispatch_count"],
                "provider_admission_pending_count": report["provider_admission_pending_count"],
            },
        )
        assert state["supervisor_decision"] == build_supervisor_decision(
            progress,
            paper_recovery_state=state,
        )
        assert study_id not in decisions
        decisions[study_id] = state["supervisor_decision"]
    return decisions


def _dm002_dm003_dhd_live_shape() -> dict[str, Any]:
    return {
        "surface_kind": "domain_health_diagnostic_runtime_report",
        "schema_version": 1,
        "action_class": "observe_only",
        "will_start_llm": False,
        "codex_dispatch_count": 0,
        "provider_admission_pending_count": 0,
        "managed_study_opl_provider_admission_candidates": [],
        "action_queue": [],
        "progress_currentness": {
            "002-dm-china-us-mortality-attribution": _progress_payload(
                study_id="002-dm-china-us-mortality-attribution",
                owner="MedAutoScience",
                action_type="complete_medical_paper_readiness_surface",
                work_unit_id="complete_medical_paper_readiness_surface",
                work_unit_fingerprint="current-readiness-typed-blocker::002-dm-china-us-mortality-attribution::e64a9d00f80571fd",
                blocker_type="medical_paper_readiness_missing",
                callable_allowed_actions=[
                    "record_user_decision",
                    "direct_study_execution",
                    "direct_paper_line_write",
                ],
                source_ref="/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies/002-dm-china-us-mortality-attribution/artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
            ),
            "003-dpcc-primary-care-phenotype-treatment-gap": _progress_payload(
                study_id="003-dpcc-primary-care-phenotype-treatment-gap",
                owner="publication_gate",
                action_type="run_gate_clearing_batch",
                work_unit_id="publication_gate_replay",
                work_unit_fingerprint="sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f",
                blocker_type="publication_gate_replay_blocked",
                callable_allowed_actions=[
                    "record_user_decision",
                    "direct_study_execution",
                    "direct_paper_line_write",
                ],
                source_ref="/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/controller/gate_clearing_batch/latest.json",
            ),
        },
    }


def _owner_receipt_recorded_progress_payload() -> dict[str, Any]:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_fingerprint = "sha256:owner-receipt-terminal"
    return {
        "study_id": study_id,
        "quest_id": study_id,
        "provider_admission_pending_count": 0,
        "provider_admission_candidates": [],
        "action_queue": [],
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "owner_receipt_recorded",
            "study_id": study_id,
            "quest_id": study_id,
            "owner": "publication_gate",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": work_unit_fingerprint,
            "currentness_basis": {
                "source": "paper_recovery_state.owner_receipt_recorded",
                "truth_epoch": f"truth::{study_id}",
                "runtime_health_epoch": f"runtime::{study_id}",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": work_unit_fingerprint,
                "action_fingerprint": work_unit_fingerprint,
                "idempotency_key": f"idem::{study_id}::owner-receipt",
            },
            "state": {
                "state_kind": "owner_receipt_recorded",
                "owner_receipt_ref": "owner-receipt:dm003:gate",
            },
        },
        "current_execution_envelope": {
            "state_kind": "owner_receipt_recorded",
            "owner": "publication_gate",
            "owner_receipt_ref": "owner-receipt:dm003:gate",
        },
    }


def _progress_payload(
    *,
    study_id: str,
    owner: str,
    action_type: str,
    work_unit_id: str,
    work_unit_fingerprint: str,
    blocker_type: str,
    callable_allowed_actions: list[str],
    source_ref: str,
) -> dict[str, Any]:
    return {
        "study_id": study_id,
        "quest_id": study_id,
        "provider_admission_pending_count": 0,
        "provider_admission_candidates": [],
        "action_queue": [],
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "typed_blocker",
            "study_id": study_id,
            "quest_id": study_id,
            "owner": owner,
            "action_type": action_type,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": work_unit_fingerprint,
            "currentness_basis": {
                "source": "stage_owner_answer.typed_blocker",
                "truth_epoch": f"truth::{study_id}",
                "runtime_health_epoch": f"runtime::{study_id}",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "action_fingerprint": work_unit_fingerprint,
                "source_ref": source_ref,
                "idempotency_key": f"idem::{study_id}",
            },
            "state": {
                "state_kind": "typed_blocker",
                "typed_blocker": {
                    "blocker_type": blocker_type,
                    "blocked_reason": blocker_type,
                    "owner": owner,
                    "action_type": action_type,
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": work_unit_fingerprint,
                    "source_ref": source_ref,
                },
            },
        },
        "current_execution_envelope": {
            "state_kind": "typed_blocker",
            "owner": owner,
            "typed_blocker": {
                "blocker_type": blocker_type,
                "owner": owner,
                "action_type": action_type,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
            },
        },
        "study_truth_snapshot": {
            "allowed_controller_actions": callable_allowed_actions,
        },
    }
