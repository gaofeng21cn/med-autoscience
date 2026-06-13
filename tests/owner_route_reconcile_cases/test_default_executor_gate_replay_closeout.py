from __future__ import annotations

from pathlib import Path

from med_autoscience.controllers.study_transition_receipt_consumption import (
    default_executor_execution_nonconsumable_closeout,
    default_executor_execution_receipt_consumption,
)
from med_autoscience.controllers.study_transition_receipt_consumption_parts.default_executor_candidates import (
    default_executor_execution_candidates,
)
from tests.owner_route_reconcile_cases.test_default_executor_receipt_consumption import _write_json


def test_default_executor_consumes_executed_gate_replay_typed_blocker_closeout(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = tmp_path / "studies" / study_id
    work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    fingerprint = (
        "current-ai-reviewer-gate-replay::003-dpcc-primary-care-phenotype-treatment-gap::"
        "dpcc_publication_gate_replay_after_current_ai_reviewer_record::"
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260610T215426Z::sat_55f14ca934dd33c5287aecff"
    )
    owner_route = {
        "idempotency_key": f"owner-route::{study_id}::gate-replay",
        "route_epoch": "truth-event-000032-097fe584ce2a78fb",
        "truth_epoch": "truth-event-000032-097fe584ce2a78fb",
        "runtime_health_epoch": "runtime-health-event-006596-c5963ea7240e495b",
        "source_eval_id": (
            "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
            "ai-reviewer-record::20260610T215426Z::sat_55f14ca934dd33c5287aecff"
        ),
        "work_unit_fingerprint": fingerprint,
        "next_owner": "gate_clearing_batch",
        "allowed_actions": ["run_gate_clearing_batch"],
        "source_refs": {
            "source_eval_id": (
                "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
                "ai-reviewer-record::20260610T215426Z::sat_55f14ca934dd33c5287aecff"
            ),
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "owner_route_currentness_basis": {
                "truth_epoch": "truth-event-000032-097fe584ce2a78fb",
                "runtime_health_epoch": "runtime-health-event-006596-c5963ea7240e495b",
                "source_eval_id": (
                    "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
                    "ai-reviewer-record::20260610T215426Z::sat_55f14ca934dd33c5287aecff"
                ),
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
            },
        },
    }
    mutable_dispatch_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/"
        "default_executor_dispatches/run_gate_clearing_batch.json"
    )
    immutable_dispatch_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/"
        "immutable/run_gate_clearing_batch/0e70d2aa1641c65aba1e6925.json"
    )
    dispatch_payload = {
        "surface": "default_executor_dispatch_request",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_gate_clearing_batch",
        "dispatch_status": "ready",
        "executor_kind": "codex_cli_default",
        "owner_route": owner_route,
        "prompt_contract": {"owner_route": owner_route},
    }
    _write_json(
        tmp_path / mutable_dispatch_ref,
        {
            **dispatch_payload,
            "refs": {
                "dispatch_path": str(tmp_path / mutable_dispatch_ref),
                "immutable_dispatch_path": str(tmp_path / immutable_dispatch_ref),
                "stage_packet_path": str(tmp_path / immutable_dispatch_ref),
            },
        },
    )
    _write_json(tmp_path / immutable_dispatch_ref, dispatch_payload)
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "sat_efe4fb48feb300595e5aade7.closeout.json",
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "stage_id": "domain_owner/default-executor-dispatch",
            "stage_attempt_id": "sat_efe4fb48feb300595e5aade7",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "stage_packet_ref": mutable_dispatch_ref,
            "domain_owner": "gate_clearing_batch",
            "owner_receipt_ref": (
                f"studies/{study_id}/artifacts/supervision/consumer/default_executor_execution/"
                "sat_efe4fb48feb300595e5aade7.closeout.json#owner_receipt"
            ),
            "owner_receipt": {
                "owner": "gate_clearing_batch",
                "status": "executed",
                "gate_replay_status": "blocked",
                "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
                "publication_eval_latest_write_authorized": False,
                "quality_authorized": False,
                "submission_authorized": False,
                "current_package_write_authorized": False,
            },
            "domain_execution": {
                "action_type": "run_gate_clearing_batch",
                "domain_owner": "gate_clearing_batch",
                "execution_status": "executed",
                "gate_replay_status": "blocked",
                "gate_blockers": [
                    "medical_publication_surface_blocked",
                    "reviewer_first_concerns_unresolved",
                    "submission_hardening_incomplete",
                ],
                "publication_gate_report_json": (
                    f"runtime/quests/{study_id}/artifacts/reports/publishability_gate/"
                    "2026-06-10T233125Z.json"
                ),
                "publication_work_unit_lifecycle_status": "blocked",
            },
            "closeout_refs": [
                f"studies/{study_id}/artifacts/supervision/consumer/default_executor_execution/"
                "sat_efe4fb48feb300595e5aade7.closeout.json",
                f"studies/{study_id}/artifacts/controller/gate_clearing_batch/latest.json",
                immutable_dispatch_ref,
                f"runtime/quests/{study_id}/artifacts/reports/publishability_gate/"
                "2026-06-10T233125Z.json",
            ],
        },
    )

    receipt = default_executor_execution_receipt_consumption(
        study_root=study_root,
        owner_route=owner_route,
        actions=[{"action_type": "run_gate_clearing_batch"}],
    )
    redrive = default_executor_execution_nonconsumable_closeout(
        study_root=study_root,
        owner_route=owner_route,
        actions=[{"action_type": "run_gate_clearing_batch"}],
    )

    assert receipt["status"] == "consumed"
    assert receipt["action_type"] == "run_gate_clearing_batch"
    assert receipt["execution_status"] == "executed"
    assert receipt["outcome"] == "typed_blocker"
    assert receipt["blocked_reason"] == "publication_gate_replay_blocked"
    assert receipt["typed_blocker_ref"].endswith("2026-06-10T233125Z.json")
    assert receipt["work_unit_id"] == work_unit_id
    assert receipt["work_unit_fingerprint"] == fingerprint
    assert receipt["next_action"] == "honor_typed_blocker_without_redrive"
    assert redrive == {}


def test_gate_replay_closeout_uses_closeout_bound_immutable_dispatch_not_current_mutable_slot(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = tmp_path / "studies" / study_id
    work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    old_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260610T215426Z::sat_old"
    )
    current_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260611T003412Z::sat_current"
    )
    old_fingerprint = (
        "current-ai-reviewer-gate-replay::003-dpcc-primary-care-phenotype-treatment-gap::"
        f"{work_unit_id}::{old_eval_id}"
    )
    current_fingerprint = (
        "current-ai-reviewer-gate-replay::003-dpcc-primary-care-phenotype-treatment-gap::"
        f"{work_unit_id}::{current_eval_id}"
    )

    def owner_route(eval_id: str, fingerprint: str) -> dict:
        return {
            "idempotency_key": f"owner-route::{study_id}::gate-replay::{eval_id}",
            "route_epoch": "truth-event-000032-097fe584ce2a78fb",
            "truth_epoch": "truth-event-000032-097fe584ce2a78fb",
            "runtime_health_epoch": "runtime-health-event-006596-c5963ea7240e495b",
            "source_eval_id": eval_id,
            "work_unit_fingerprint": fingerprint,
            "next_owner": "gate_clearing_batch",
            "allowed_actions": ["run_gate_clearing_batch"],
            "source_refs": {
                "source_eval_id": eval_id,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "owner_route_currentness_basis": {
                    "truth_epoch": "truth-event-000032-097fe584ce2a78fb",
                    "runtime_health_epoch": "runtime-health-event-006596-c5963ea7240e495b",
                    "source_eval_id": eval_id,
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                },
            },
        }

    old_route = owner_route(old_eval_id, old_fingerprint)
    current_route = owner_route(current_eval_id, current_fingerprint)
    mutable_dispatch_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/"
        "default_executor_dispatches/run_gate_clearing_batch.json"
    )
    old_immutable_dispatch_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/"
        "immutable/run_gate_clearing_batch/old.json"
    )
    current_immutable_dispatch_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/"
        "immutable/run_gate_clearing_batch/current.json"
    )

    def dispatch_payload(route: dict) -> dict:
        return {
            "surface": "default_executor_dispatch_request",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "dispatch_status": "ready",
            "executor_kind": "codex_cli_default",
            "owner_route": route,
            "prompt_contract": {"owner_route": route},
        }

    _write_json(
        tmp_path / mutable_dispatch_ref,
        {
            **dispatch_payload(current_route),
            "refs": {
                "dispatch_path": str(tmp_path / mutable_dispatch_ref),
                "immutable_dispatch_path": str(tmp_path / current_immutable_dispatch_ref),
                "stage_packet_path": str(tmp_path / current_immutable_dispatch_ref),
            },
        },
    )
    _write_json(tmp_path / old_immutable_dispatch_ref, dispatch_payload(old_route))
    _write_json(tmp_path / current_immutable_dispatch_ref, dispatch_payload(current_route))
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "sat_old.closeout.json",
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "stage_id": "domain_owner/default-executor-dispatch",
            "stage_attempt_id": "sat_old",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "stage_packet_ref": mutable_dispatch_ref,
            "domain_execution": {
                "action_type": "run_gate_clearing_batch",
                "domain_owner": "gate_clearing_batch",
                "execution_status": "executed",
                "gate_replay_status": "blocked",
                "publication_gate_report_json": (
                    f"runtime/quests/{study_id}/artifacts/reports/publishability_gate/"
                    "2026-06-10T233125Z.json"
                ),
                "publication_work_unit_lifecycle_status": "blocked",
            },
            "owner_receipt": {
                "owner": "gate_clearing_batch",
                "status": "executed",
                "publication_eval_latest_write_authorized": False,
                "quality_authorized": False,
                "submission_authorized": False,
                "current_package_write_authorized": False,
            },
            "status": "executed",
            "closeout_refs": [
                f"studies/{study_id}/artifacts/supervision/consumer/default_executor_execution/"
                "sat_old.closeout.json",
                old_immutable_dispatch_ref,
                f"runtime/quests/{study_id}/artifacts/reports/publishability_gate/"
                "2026-06-10T233125Z.json",
            ],
        },
    )

    candidates = [
        execution
        for execution, _receipt_ref in default_executor_execution_candidates(study_root=study_root)
        if execution.get("execution_id") == "sat_old"
    ]
    assert len(candidates) == 1
    assert candidates[0]["owner_route_currentness_source"] == "stage_packet_ref_recovered"
    assert (
        candidates[0]["current_owner_route"]["source_refs"]["owner_route_currentness_basis"]["source_eval_id"]
        == old_eval_id
    )

    assert (
        default_executor_execution_receipt_consumption(
            study_root=study_root,
            owner_route=current_route,
            actions=[{"action_type": "run_gate_clearing_batch"}],
        )
        == {}
    )
    assert (
        default_executor_execution_nonconsumable_closeout(
            study_root=study_root,
            owner_route=current_route,
            actions=[{"action_type": "run_gate_clearing_batch"}],
        )
        == {}
    )


def test_stage_closeout_candidate_preserves_stage_packet_identity_for_current_control(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = tmp_path / "studies" / study_id
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    mutable_dispatch_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/"
        "default_executor_dispatches/run_quality_repair_batch.json"
    )
    old_immutable_dispatch_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/"
        "immutable/run_quality_repair_batch/old.json"
    )
    current_immutable_dispatch_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/"
        "immutable/run_quality_repair_batch/current.json"
    )
    owner_route = {
        "idempotency_key": f"provider-admission::{study_id}::{fingerprint}",
        "truth_epoch": "truth-event-old",
        "runtime_health_epoch": "runtime-health-old",
        "source_eval_id": "publication-eval::old",
        "work_unit_fingerprint": fingerprint,
        "next_owner": "write",
        "allowed_actions": ["run_quality_repair_batch"],
        "source_refs": {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "owner_route_currentness_basis": {
                "truth_epoch": "truth-event-old",
                "runtime_health_epoch": "runtime-health-old",
                "source_eval_id": "publication-eval::old",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
            },
        },
    }
    _write_json(
        tmp_path / mutable_dispatch_ref,
        {
            "surface": "default_executor_dispatch_request",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "dispatch_status": "ready",
            "executor_kind": "codex_cli_default",
            "owner_route": owner_route,
            "refs": {
                "dispatch_path": str(tmp_path / mutable_dispatch_ref),
                "immutable_dispatch_path": str(tmp_path / current_immutable_dispatch_ref),
                "stage_packet_path": str(tmp_path / current_immutable_dispatch_ref),
            },
        },
    )
    _write_json(
        tmp_path / old_immutable_dispatch_ref,
        {
            "surface": "default_executor_dispatch_request",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "dispatch_status": "ready",
            "executor_kind": "codex_cli_default",
            "owner_route": owner_route,
        },
    )
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "sat_old.closeout.json",
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "stage_id": "domain_owner/default-executor-dispatch",
            "stage_attempt_id": "sat_old",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "source_eval_id": "publication-eval::old",
            "stage_packet_ref": mutable_dispatch_ref,
            "status": "closed_with_domain_owner_refs",
            "execution_status": "executed",
            "owner_receipt_ref": (
                f"studies/{study_id}/artifacts/controller/repair_execution_evidence/latest.json"
            ),
            "owner_receipt": {
                "owner": "write",
                "status": "executed",
                "quality_authorized": False,
                "submission_authorized": False,
                "current_package_write_authorized": False,
            },
            "domain_execution": {
                "action_type": "run_quality_repair_batch",
                "domain_owner": "write",
                "execution_status": "executed",
            },
            "closeout_refs": [
                f"studies/{study_id}/artifacts/supervision/consumer/default_executor_execution/"
                "sat_old.closeout.json",
                old_immutable_dispatch_ref,
            ],
        },
    )

    candidates = [
        execution
        for execution, _receipt_ref in default_executor_execution_candidates(study_root=study_root)
        if execution.get("execution_id") == "sat_old"
    ]

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate["stage_packet_ref"] == mutable_dispatch_ref
    assert old_immutable_dispatch_ref in candidate["stage_packet_refs"]
    assert current_immutable_dispatch_ref not in candidate["stage_packet_refs"]
