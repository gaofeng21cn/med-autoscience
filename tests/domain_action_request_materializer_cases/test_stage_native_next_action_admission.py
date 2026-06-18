from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from tests.study_runtime_test_helpers import make_profile, write_study


@pytest.fixture(autouse=True)
def _isolated_opl_state_dir(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OPL_STATE_DIR", str(tmp_path / "opl-state"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _owner_route(
    *,
    study_id: str,
    quest_id: str,
    next_owner: str,
    owner_reason: str,
    allowed_actions: list[str],
) -> dict[str, object]:
    source_fingerprint = f"truth-source::{study_id}::{owner_reason}"
    truth_epoch = f"truth-epoch::{study_id}"
    runtime_health_epoch = f"runtime-health::{study_id}::{owner_reason}"
    return {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": quest_id,
        "truth_epoch": truth_epoch,
        "route_epoch": truth_epoch,
        "runtime_health_epoch": runtime_health_epoch,
        "work_unit_fingerprint": source_fingerprint,
        "source_fingerprint": source_fingerprint,
        "current_owner": "mas_controller",
        "next_owner": next_owner,
        "owner_reason": owner_reason,
        "active_run_id": None,
        "allowed_actions": allowed_actions,
        "blocked_actions": [],
        "idempotency_key": f"owner-route::{study_id}::{owner_reason}",
        "source_refs": {
            "study_truth_epoch": truth_epoch,
            "runtime_health_epoch": runtime_health_epoch,
            "work_unit_id": owner_reason,
            "work_unit_fingerprint": source_fingerprint,
            "owner_route_currentness_basis": {
                "runtime_health_epoch": runtime_health_epoch,
                "truth_epoch": truth_epoch,
                "work_unit_fingerprint": source_fingerprint,
                "work_unit_id": owner_reason,
            },
        },
    }


def _write_stage_native_next_action(
    *,
    study_root: Path,
    current_work_unit_binding: dict[str, object] | None = None,
) -> None:
    payload: dict[str, object] = {
        "schema_version": 1,
        "status": "ready_for_owner_action",
        "action_id": "run_quality_repair_batch",
        "owner": "write",
        "source_surface": "artifacts/reports/medical_publication_surface/latest.json",
        "current_stage_id": "08-publication_package_handoff",
        "stage_index_ref": "control/stage_index.json",
        "current_package_status": "not_ready",
        "next_work_unit": "medical_publication_surface_blocked_write_repair",
        "required_output_surface": (
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
    }
    if current_work_unit_binding is not None:
        payload["stage_transition_authority_boundary"] = {
            "stage_transition_authority": "one-person-lab",
            "intent_can_write_stage_current_pointer": False,
            "intent_can_write_stage_run_terminal_state": False,
            "intent_can_publish_current_owner_delta": False,
        }
        payload["current_work_unit_binding"] = current_work_unit_binding
    _write_json(study_root / "control" / "next_action.json", payload)


def _write_readiness_route(*, profile, study_id: str, readiness_route: dict[str, object]) -> None:
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner_route": readiness_route,
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "quest_id": study_id,
                            "action_type": "complete_medical_paper_readiness_surface",
                            "authority": "mas_owner_surface",
                            "owner": "MedAutoScience",
                            "request_owner": "MedAutoScience",
                            "recommended_owner": "MedAutoScience",
                            "reason": "medical_paper_readiness_missing",
                            "work_unit_id": "complete_medical_paper_readiness_surface",
                            "owner_route": readiness_route,
                        }
                    ],
                }
            ],
        },
    )


def _patch_readiness_blocker_progress(monkeypatch, *, study_id: str, readiness_route: dict[str, object]) -> None:
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")

    def read_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "generated_at": "2026-06-08T00:04:57+00:00",
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "typed_blocker": {
                    "blocker_id": "medical_paper_readiness_missing",
                    "owner": "MedAutoScience",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                    "source_ref": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "receipts/typed_blocker.json"
                    ),
                },
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "typed_blocker",
                "owner": "MedAutoScience",
                "action_type": "complete_medical_paper_readiness_surface",
                "work_unit_id": "complete_medical_paper_readiness_surface",
                "work_unit_fingerprint": f"readiness-typed-blocker::{study_id}",
                "state": {
                    "state_kind": "typed_blocker",
                    "typed_blocker": {
                        "blocker_id": "medical_paper_readiness_missing",
                        "owner": "MedAutoScience",
                        "work_unit_id": "complete_medical_paper_readiness_surface",
                        "source_ref": (
                            "artifacts/stage_outputs/08-publication_package_handoff/"
                            "receipts/typed_blocker.json"
                        ),
                    },
                    "stale_queue_or_handoff_can_override": False,
                },
            },
            "current_executable_owner_action": None,
            "current_owner_ticket": None,
            "owner_route": readiness_route,
            "deliverable_progress_delta": {"count": 0},
        }

    monkeypatch.setattr(progress_module, "read_study_progress", read_progress)


def test_materialize_domain_action_requests_blocks_unbound_stage_native_write_and_readiness_blocker_only(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_stage_native_next_action(study_root=study_root)
    readiness_route = _owner_route(
        study_id=study_id,
        quest_id=study_id,
        next_owner="MedAutoScience",
        owner_reason="medical_paper_readiness_missing",
        allowed_actions=["complete_medical_paper_readiness_surface"],
    )
    _write_readiness_route(profile=profile, study_id=study_id, readiness_route=readiness_route)
    _patch_readiness_blocker_progress(monkeypatch, study_id=study_id, readiness_route=readiness_route)

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["request_task_count"] == 0
    assert result["domain_progress_transition_request_count"] == 0
    assert any(
        item["action_type"] == "complete_medical_paper_readiness_surface"
        and item["reason"] == "superseded_by_current_work_unit_typed_blocker"
        for item in result["ignored_actions"]
    )
    assert any(
        item["action_type"] == "run_quality_repair_batch"
        and item["reason"] == "stage_native_workspace_next_action_requires_authority_binding"
        for item in result["ignored_actions"]
    )


def test_materialize_domain_action_requests_routes_bound_stage_native_write_after_readiness_blocker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    repair_work_unit_fingerprint = (
        "canonical-current-work-unit::08-publication_package_handoff::"
        "medical_publication_surface_blocked_write_repair"
    )
    _write_stage_native_next_action(
        study_root=study_root,
        current_work_unit_binding={
            "source": "canonical_current_work_unit",
            "work_unit_id": "medical_publication_surface_blocked_write_repair",
            "work_unit_fingerprint": repair_work_unit_fingerprint,
        },
    )
    readiness_route = _owner_route(
        study_id=study_id,
        quest_id=study_id,
        next_owner="MedAutoScience",
        owner_reason="medical_paper_readiness_missing",
        allowed_actions=["complete_medical_paper_readiness_surface"],
    )
    _write_readiness_route(profile=profile, study_id=study_id, readiness_route=readiness_route)
    _patch_readiness_blocker_progress(monkeypatch, study_id=study_id, readiness_route=readiness_route)

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["request_task_count"] == 1
    assert result["domain_progress_transition_request_count"] == 1
    dispatch = result["domain_progress_transition_requests"][0]
    assert dispatch["action_type"] == "run_quality_repair_batch"
    assert dispatch["next_executable_owner"] == "write"
    source_action = dispatch["source_action_ref"]
    assert source_action["authority"] == "stage_native_workspace_next_action"
    assert source_action["stage_native_next_action_admission"]["default_dispatch_allowed"] is True
    assert source_action["current_work_unit_binding"]["work_unit_fingerprint"] == repair_work_unit_fingerprint
    assert dispatch["owner_route_ref"]["source_refs"]["work_unit_id"] == "medical_publication_surface_blocked_write_repair"
    assert dispatch["owner_route_ref"]["work_unit_fingerprint"] == repair_work_unit_fingerprint
    assert any(
        item["action_type"] == "complete_medical_paper_readiness_surface"
        and item["reason"] == "superseded_by_readiness_blocker_derived_repair"
        for item in result["ignored_actions"]
    )


def test_materialize_domain_action_requests_routes_stage_native_write_when_current_work_unit_matches_binding(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    monkeypatch.setattr(progress_module, "read_study_progress", lambda **_: {})
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    current_stage_id = "08-publication_package_handoff"
    source_surface = "artifacts/reports/medical_publication_surface/latest.json"
    work_unit_id = "medical_publication_surface_blocked_write_repair"
    repair_work_unit_fingerprint = (
        "canonical-current-work-unit::08-publication_package_handoff::"
        "medical_publication_surface_blocked_write_repair"
    )
    current_work_unit_binding = {
        "source": "canonical_current_work_unit",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": repair_work_unit_fingerprint,
    }
    _write_stage_native_next_action(
        study_root=study_root,
        current_work_unit_binding=current_work_unit_binding,
    )
    epoch = f"stage-native-next-action::{study_id}::{current_stage_id}"
    stage_native_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": study_id,
        "truth_epoch": epoch,
        "runtime_health_epoch": epoch,
        "work_unit_fingerprint": repair_work_unit_fingerprint,
        "failure_signature": "run_quality_repair_batch",
        "trace_id": f"owner-route-trace::{study_id}::run_quality_repair_batch",
        "route_epoch": epoch,
        "source_fingerprint": repair_work_unit_fingerprint,
        "current_owner": "mas_controller",
        "next_owner": "write",
        "owner_reason": "run_quality_repair_batch",
        "active_run_id": None,
        "allowed_actions": ["run_quality_repair_batch"],
        "blocked_actions": [],
        "source_refs": {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": repair_work_unit_fingerprint,
            "source_surface": source_surface,
            "stage_index_ref": "control/stage_index.json",
            "current_stage_id": current_stage_id,
            "current_work_unit_binding": current_work_unit_binding,
            "owner_route_currentness_basis": {
                "truth_epoch": epoch,
                "runtime_health_epoch": epoch,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": repair_work_unit_fingerprint,
            },
        },
        "idempotency_key": f"owner-route::{study_id}::{epoch}::write::run_quality_repair_batch",
    }
    _write_json(
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner_route": stage_native_route,
                    "action_queue": [],
                }
            ],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert [item["action_type"] for item in result["domain_progress_transition_requests"]] == [
        "run_quality_repair_batch"
    ]
    dispatch = result["domain_progress_transition_requests"][0]
    assert dispatch["next_executable_owner"] == "write"
    source_action = dispatch["source_action_ref"]
    assert source_action["authority"] == "stage_native_workspace_next_action"
    assert source_action["stage_native_next_action_admission"]["default_dispatch_allowed"] is True
    assert source_action["current_work_unit_binding"]["work_unit_fingerprint"] == repair_work_unit_fingerprint
    assert dispatch["owner_route_ref"]["source_refs"]["work_unit_id"] == work_unit_id
    assert dispatch["owner_route_ref"]["work_unit_fingerprint"] == repair_work_unit_fingerprint


def test_materialize_domain_action_requests_persists_ai_reviewer_handoff_packet_authority_boundary(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    write_study(profile.workspace_root, study_id, quest_id=study_id)
    work_unit_id = "ai_reviewer_medical_prose_quality_review"
    work_unit_fingerprint = (
        "domain-transition::ai_reviewer_re_eval::"
        "ai_reviewer_medical_prose_quality_review"
    )
    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": study_id,
        "truth_epoch": "truth-event-current",
        "runtime_health_epoch": "runtime-health-current",
        "work_unit_fingerprint": work_unit_fingerprint,
        "source_fingerprint": work_unit_fingerprint,
        "route_epoch": work_unit_fingerprint,
        "current_owner": "med-autoscience",
        "next_owner": "ai_reviewer",
        "owner_reason": work_unit_id,
        "allowed_actions": ["return_to_ai_reviewer_workflow"],
        "blocked_actions": [],
        "source_refs": {
            "runtime_health_epoch": "runtime-health-current",
            "study_truth_epoch": "truth-event-current",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "owner_route_currentness_basis": {
                "runtime_health_epoch": "runtime-health-current",
                "truth_epoch": "truth-event-current",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
            },
        },
        "idempotency_key": f"owner-route::{study_id}::{work_unit_fingerprint}",
    }
    _write_json(
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner_route": owner_route,
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "quest_id": study_id,
                            "action_id": (
                                "supervisor-action::003::return_to_ai_reviewer_workflow::"
                                "domain_transition_ai_reviewer_re_eval"
                            ),
                            "action_type": "return_to_ai_reviewer_workflow",
                            "authority": "observability_only",
                            "owner": "ai_reviewer",
                            "request_owner": "ai_reviewer",
                            "recommended_owner": "ai_reviewer",
                            "route_target": "ai_reviewer",
                            "reason": "domain_transition_ai_reviewer_re_eval",
                            "required_output_surface": "artifacts/publication_eval/latest.json",
                            "work_unit_fingerprint": work_unit_fingerprint,
                            "controller_work_unit_id": work_unit_id,
                            "executable_work_unit": work_unit_id,
                            "source_eval_id": "publication-eval::current-record",
                            "owner_route": owner_route,
                            "handoff_packet": {
                                "authority": "observability_only",
                                "owner": "ai_reviewer",
                                "request_owner": "ai_reviewer",
                                "recommended_owner": "ai_reviewer",
                                "next_executable_owner": "ai_reviewer",
                            },
                        }
                    ],
                }
            ],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["ready_domain_progress_transition_request_count"] == 0
    assert result["transition_request_pending_domain_progress_transition_request_count"] == 1
    assert result["written_files"] == []
    assert result["apply_writes_domain_intent_projection_only"] is True
    assert result["apply_writes_disabled_reason"] == (
        "opl_domain_progress_transition_runtime_owns_durable_carrier"
    )
    dispatch = result["domain_progress_transition_requests"][0]
    persisted_dispatch_path = (
        profile.workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / "return_to_ai_reviewer_workflow.json"
    )
    assert not persisted_dispatch_path.exists()
    consumer_latest = Path(result["refs"]["latest_path"])
    assert not consumer_latest.exists()
    assert dispatch["dispatch_status"] == "transition_request_pending"
    assert dispatch["blocked_reason"] == "opl_execution_authorization_required"
    assert dispatch["action_type"] == "return_to_ai_reviewer_workflow"
    assert dispatch["mas_local_dispatch_carrier_persistence"] == "forbidden"
    assert dispatch["opl_transition_runtime_required_for_durable_carrier"] is True
    assert dispatch["dispatch_ready_for_execution_authority"] is False
    assert dispatch["mas_dispatch_authority"] is False
    assert dispatch["provider_completion_is_domain_completion"] is False
    assert dispatch["provider_admission_pending"] is False
    assert dispatch["provider_admission_requires_opl_runtime_result"] is True
    assert dispatch["authority_boundary"]["authority"] == "med_autoscience.paper_progress_policy_adapter"
    assert dispatch["authority_boundary"]["mas_can_authorize_provider_admission"] is False
    assert dispatch["authority_boundary"]["mas_can_create_opl_outbox_record"] is False
    assert (
        dispatch["stage_transition_authority_boundary_ref"]["stage_transition_authority"]
        == "one-person-lab"
    )
    assert (
        dispatch["stage_transition_authority_boundary_ref"][
            "provider_completion_counts_as_stage_transition"
        ]
        is False
    )
    assert "provider_admission_identity" not in dispatch
    transition_request = dispatch["opl_domain_progress_transition_request"]
    assert transition_request["surface_kind"] == "mas_domain_progress_transition_request"
    assert transition_request["target_runtime_kind"] == "DomainProgressTransitionRuntime"
    assert transition_request["target_runtime_owner"] == "one-person-lab"
    assert transition_request["action_type"] == "return_to_ai_reviewer_workflow"
    assert transition_request["work_unit_id"] == work_unit_id
    assert transition_request["work_unit_fingerprint"] == work_unit_fingerprint
    assert transition_request["mas_can_create_opl_outbox_record"] is False
    assert transition_request["required_postcondition"]["kind"] == "owner_action_ref"
