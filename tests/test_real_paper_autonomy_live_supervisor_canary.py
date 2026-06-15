from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pytest

from med_autoscience.controllers.real_paper_autonomy_live_supervisor_canary import (
    DEFAULT_TARGET_STUDIES,
    FORBIDDEN_PROGRESS_AUTHORITIES,
    FORBIDDEN_TERMINAL_DECISIONS,
    READ_ONLY_CONTRACT,
    build_live_supervisor_canary,
)


DM002 = "002-dm-china-us-mortality-attribution"
DM003 = "003-dpcc-primary-care-phenotype-treatment-gap"
REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = REPO_ROOT / "contracts" / "paper_autonomy_live_supervisor_canary_contract.json"


class FakeProfile:
    name = "dm-cvd-mortality-risk"
    workspace_root = Path("/tmp/yang/DM-CVD-Mortality-Risk")
    runtime_root = Path("/tmp/yang/DM-CVD-Mortality-Risk/runtime")
    profile_ref = Path("/tmp/yang/DM-CVD-Mortality-Risk/profile.toml")


def test_live_supervisor_canary_requires_one_identity_bound_decision_per_study() -> None:
    payload = build_live_supervisor_canary(
        profile=FakeProfile(),  # type: ignore[arg-type]
        profile_ref=str(FakeProfile.profile_ref),
        study_ids=(DM002, DM003),
        progress_reader=_progress_reader(_progress_payloads()),
        dhd_reader=_dhd_reader(_progress_payloads()),
    )

    assert payload["surface_kind"] == "real_paper_autonomy_live_supervisor_canary"
    assert payload["read_only_contract"] == READ_ONLY_CONTRACT
    assert payload["summary"]["status"] == "pass"
    assert payload["summary"]["writes_performed"] is False
    assert payload["summary"]["exactly_one_supervisor_decision_per_study"] is True
    assert payload["summary"]["forbidden_progress_authorities_rejected"] is True
    assert payload["dhd_dry_run_summary"] == {
        "action_class": "observe_only",
        "will_start_llm": False,
        "codex_dispatch_count": 0,
        "provider_admission_pending_count": 0,
        "progress_currentness_count": 2,
        "provider_admission_candidate_count": 0,
    }

    by_study = {item["study_id"]: item for item in payload["study_results"]}
    assert set(by_study) == {DM002, DM003}
    for item in by_study.values():
        decision = item["supervisor_decision"]
        assert item["supervisor_decision_count"] == 1
        assert item["identity_match"] is True
        assert item["progress_dhd_identity_match"] is True
        assert item["classification"] == "recovery_action_required"
        assert item["provider_admission"]["pending_count"] == 0
        assert item["provider_admission"]["candidate_count"] == 0
        assert item["strict_running_proof"]["running_provider_attempt"] is False
        assert item["paper_progress_authority"]["paper_progress_credit"] is False
        assert item["paper_progress_authority"]["control_outcome_credit"] is False
        assert "provider_admission_pending_count=0" in item["forbidden_progress_authorities"]
        assert decision["decision"] == "materialize_recovery_action"
        assert "provider_admission_pending_count=0" in decision["forbidden_interpretations"]
        assert "action_queue=[]" in decision["forbidden_interpretations"]


def test_live_supervisor_canary_fail_closes_dhd_identity_drift() -> None:
    progress_payloads = _progress_payloads()
    dhd_payloads = {
        **progress_payloads,
        DM003: {
            **progress_payloads[DM003],
            "current_work_unit": {
                **progress_payloads[DM003]["current_work_unit"],
                "work_unit_fingerprint": "sha256:stale-dhd-fingerprint",
                "action_fingerprint": "sha256:stale-dhd-fingerprint",
                "currentness_basis": {
                    **progress_payloads[DM003]["current_work_unit"]["currentness_basis"],
                    "work_unit_fingerprint": "sha256:stale-dhd-fingerprint",
                    "action_fingerprint": "sha256:stale-dhd-fingerprint",
                },
            },
        },
    }

    payload = build_live_supervisor_canary(
        profile=FakeProfile(),  # type: ignore[arg-type]
        study_ids=(DM002, DM003),
        progress_reader=_progress_reader(progress_payloads),
        dhd_reader=_dhd_reader(dhd_payloads),
    )

    assert payload["summary"]["status"] == "fail"
    by_study = {item["study_id"]: item for item in payload["study_results"]}
    assert by_study[DM002]["classification"] == "recovery_action_required"
    assert by_study[DM003]["classification"] == "stale_diagnostic"
    assert by_study[DM003]["progress_dhd_identity_match"] is False
    assert f"{DM003}:progress_dhd_identity_mismatch" in payload["summary"]["failures"]


def test_live_supervisor_canary_fail_closes_missing_dhd_progress() -> None:
    payload = build_live_supervisor_canary(
        profile=FakeProfile(),  # type: ignore[arg-type]
        study_ids=(DM002, DM003),
        progress_reader=_progress_reader(_progress_payloads()),
        dhd_reader=_dhd_reader({DM002: _progress_payloads()[DM002]}),
    )

    by_study = {item["study_id"]: item for item in payload["study_results"]}
    assert payload["summary"]["status"] == "fail"
    assert by_study[DM003]["classification"] == "stale_diagnostic"
    assert f"{DM003}:missing_dhd_progress_currentness" in payload["summary"]["failures"]
    assert f"{DM003}:progress_dhd_identity_mismatch" in payload["summary"]["failures"]


def test_live_supervisor_canary_separates_owner_receipt_from_stable_blocker_credit() -> None:
    payloads = {
        DM002: _stable_blocker_progress_payload(),
        DM003: _owner_receipt_recorded_progress_payload(),
    }
    payload = build_live_supervisor_canary(
        profile=FakeProfile(),  # type: ignore[arg-type]
        study_ids=(DM002, DM003),
        progress_reader=_progress_reader(payloads),
        dhd_reader=_dhd_reader(payloads),
    )

    assert payload["summary"]["status"] == "pass"
    by_study = {item["study_id"]: item for item in payload["study_results"]}

    dm002 = by_study[DM002]
    assert dm002["classification"] == "stable_typed_blocker"
    assert dm002["supervisor_decision"]["decision"] == "stop_with_stable_typed_blocker"
    assert dm002["paper_progress_authority"]["paper_progress_credit"] is False
    assert dm002["paper_progress_authority"]["control_outcome_credit"] is True

    dm003 = by_study[DM003]
    assert dm003["classification"] == "owner_receipt_recorded"
    assert dm003["supervisor_decision"]["decision"] == "stop_with_owner_receipt"
    assert dm003["current_work_unit"]["owner_receipt_ref"] == "owner-receipt:dm003:gate"
    assert dm003["paper_progress_authority"]["paper_progress_credit"] is True
    assert dm003["paper_progress_authority"]["control_outcome_credit"] is True


def _progress_reader(payloads: Mapping[str, Mapping[str, Any]]):
    def read_progress(_profile: FakeProfile, study_id: str) -> Mapping[str, Any]:
        return payloads[study_id]

    return read_progress


def _dhd_reader(payloads: Mapping[str, Mapping[str, Any]]):
    def read_dhd(_profile: FakeProfile, _study_ids: Sequence[str]) -> Mapping[str, Any]:
        return {
            "surface_kind": "domain_health_diagnostic_runtime_report",
            "schema_version": 1,
            "action_class": "observe_only",
            "will_start_llm": False,
            "codex_dispatch_count": 0,
            "provider_admission_pending_count": 0,
            "managed_study_opl_provider_admission_candidates": [],
            "action_queue": [],
            "progress_currentness": dict(payloads),
        }

    return read_dhd


def _progress_payloads() -> dict[str, dict[str, Any]]:
    return {
        DM002: _progress_payload(
            study_id=DM002,
            owner="MedAutoScience",
            action_type="complete_medical_paper_readiness_surface",
            work_unit_id="complete_medical_paper_readiness_surface",
            work_unit_fingerprint=(
                "current-readiness-typed-blocker::"
                "002-dm-china-us-mortality-attribution::e64a9d00f80571fd"
            ),
            blocker_type="medical_paper_readiness_missing",
            source_ref=(
                "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies/"
                "002-dm-china-us-mortality-attribution/artifacts/stage_outputs/"
                "08-publication_package_handoff/receipts/typed_blocker.json"
            ),
        ),
        DM003: _progress_payload(
            study_id=DM003,
            owner="publication_gate",
            action_type="run_gate_clearing_batch",
            work_unit_id="publication_gate_replay",
            work_unit_fingerprint=(
                "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f"
            ),
            blocker_type="publication_gate_replay_blocked",
            source_ref=(
                "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies/"
                "003-dpcc-primary-care-phenotype-treatment-gap/artifacts/controller/"
                "gate_clearing_batch/latest.json"
            ),
        ),
    }


def _stable_blocker_progress_payload() -> dict[str, Any]:
    payload = _progress_payloads()[DM002]
    typed_blocker = payload["current_work_unit"]["state"]["typed_blocker"]
    typed_blocker.update(
        {
            "blocker_type": "anti_loop_budget_exhausted",
            "blocked_reason": "anti_loop_budget_exhausted",
            "stable_outcome_ref": "typed-blocker:dm002:anti-loop",
        }
    )
    payload["current_execution_envelope"]["typed_blocker"] = {
        **payload["current_execution_envelope"]["typed_blocker"],
        "blocker_type": "anti_loop_budget_exhausted",
        "stable_outcome_ref": "typed-blocker:dm002:anti-loop",
    }
    payload["paper_recovery_state"] = {
        "phase": "domain_blocked",
        "supervisor_decision": _stable_blocker_supervisor_decision(payload),
    }
    return payload


def _stable_blocker_supervisor_decision(payload: Mapping[str, Any]) -> dict[str, Any]:
    unit = payload["current_work_unit"]
    fingerprint = unit["work_unit_fingerprint"]
    obligation = {
        "surface_kind": "paper_autonomy_obligation",
        "schema_version": 1,
        "paper_autonomy_obligation_id": (
            f"paper-autonomy::{DM002}::publication_supervision::"
            f"{unit['action_type']}::{unit['work_unit_id']}::{fingerprint}"
        ),
        "study_id": DM002,
        "quest_id": DM002,
        "stage_id": "publication_supervision",
        "action_type": unit["action_type"],
        "work_unit_id": unit["work_unit_id"],
        "work_unit_fingerprint": fingerprint,
        "route_identity_key": f"{DM002}:{unit['action_type']}:{unit['work_unit_id']}:{fingerprint}",
        "attempt_idempotency_key": f"idem::{DM002}",
        "owner_route_currentness_basis": unit["currentness_basis"],
        "desired_delta": {
            "owner": unit["owner"],
            "target_surface": "typed_blocker",
            "required_output_ref_family": "typed_blocker",
        },
        "source_recovery_phase": "domain_blocked",
    }
    return {
        "surface_kind": "paper_autonomy_supervisor_decision",
        "schema_version": 1,
        "decision_id": "decision:dm002:stable-blocker",
        "decision": "stop_with_stable_typed_blocker",
        "identity_match": True,
        "paper_autonomy_obligation": obligation,
        "paper_autonomy_obligation_ref": "paper-autonomy-obligation:dm002:stable-blocker",
        "source_paper_recovery_phase": "domain_blocked",
        "evidence_refs": ["typed-blocker:dm002:anti-loop"],
        "missing_evidence_refs": [],
        "forbidden_interpretations": [
            "provider_admission_pending_count=0",
            "action_queue=[]",
            "provider_admission_pending_count=0_is_not_terminal",
            "action_queue=[]_is_not_terminal",
        ],
        "next_owner": "one-person-lab",
        "next_safe_action": {
            "kind": "publish_stable_blocker_and_stop_same_identity_redrive",
        },
        "paper_progress_classification": "stable_stop_loss_credit",
        "platform_repair_classification": "stop_loss",
    }


def _owner_receipt_recorded_progress_payload() -> dict[str, Any]:
    work_unit_fingerprint = "sha256:owner-receipt-terminal"
    return {
        "study_id": DM003,
        "quest_id": DM003,
        "provider_admission_pending_count": 0,
        "provider_admission_candidates": [],
        "action_queue": [],
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "owner_receipt_recorded",
            "study_id": DM003,
            "quest_id": DM003,
            "owner": "publication_gate",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": work_unit_fingerprint,
            "currentness_basis": {
                "source": "paper_recovery_state.owner_receipt_recorded",
                "truth_epoch": f"truth::{DM003}",
                "runtime_health_epoch": f"runtime::{DM003}",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": work_unit_fingerprint,
                "action_fingerprint": work_unit_fingerprint,
                "idempotency_key": f"idem::{DM003}::owner-receipt",
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
            "allowed_controller_actions": [
                "record_user_decision",
                "direct_study_execution",
                "direct_paper_line_write",
            ],
        },
    }


@pytest.mark.parametrize(
    "forbidden_flag",
    (
        "may_apply_domain_health_diagnostic",
        "may_hydrate",
        "may_tick",
        "may_redrive",
        "may_start_provider_attempt",
        "may_write_yang_study_or_runtime_artifacts",
    ),
)
def test_live_supervisor_canary_read_only_contract_forbids_mutating_runtime(
    forbidden_flag: str,
) -> None:
    assert READ_ONLY_CONTRACT[forbidden_flag] is False


@pytest.mark.meta
def test_live_supervisor_canary_contract_matches_runtime_constants_and_entrypoint() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    assert contract["surface_kind"] == "paper_autonomy_live_supervisor_canary_contract"
    assert contract["state"] == "active_contract"
    assert contract["command_surface"] == {
        "script_ref": "scripts/real-paper-autonomy-soak-inventory.py",
        "mode": "live-supervisor-canary",
        "example_command": (
            "scripts/run-python-clean.sh scripts/real-paper-autonomy-soak-inventory.py "
            "--mode live-supervisor-canary --profile <profile> "
            "--study 002-dm-china-us-mortality-attribution "
            "--study 003-dpcc-primary-care-phenotype-treatment-gap"
        ),
        "requires_exactly_one_profile": True,
        "default_target_studies": list(DEFAULT_TARGET_STUDIES),
        "output_surface_kind": "real_paper_autonomy_live_supervisor_canary",
    }
    assert contract["read_only_contract"] == READ_ONLY_CONTRACT
    assert contract["allowed_supervisor_decisions"] == [
        "execute_current_owner_delta",
        "consume_terminal_closeout",
        "materialize_recovery_action",
        "wait_for_owner_with_resume_token",
        "stop_with_stable_typed_blocker",
        "stop_with_owner_receipt",
    ]
    assert set(contract["forbidden_terminal_decisions"]) == FORBIDDEN_TERMINAL_DECISIONS
    assert contract["forbidden_progress_authorities"] == list(FORBIDDEN_PROGRESS_AUTHORITIES)
    assert contract["success_criteria"]["writes_performed"] is False
    assert contract["failure_effect"] == {
        "status": "fail",
        "effect": "fail_closed_to_stale_diagnostic_or_identity_split_report",
        "may_generate_domain_authority": False,
        "may_generate_provider_admission": False,
        "may_credit_paper_progress": False,
    }
