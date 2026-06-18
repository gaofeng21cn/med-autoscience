from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    transition_request_consumer_latest,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


PUBLICATION_SURFACE = "artifacts/reports/medical_publication_surface/latest.json"
PUBLICATION_STAGE_ID = "08-publication_package_handoff"


def _stage_native_fingerprint(
    *,
    action_type: str = "run_quality_repair_batch",
    current_stage_id: str = PUBLICATION_STAGE_ID,
    source_surface: str = PUBLICATION_SURFACE,
) -> str:
    return f"stage-native-next-action::{current_stage_id}::{action_type}::{source_surface}"


def _stage_native_current_work_unit_binding(
    *,
    action_type: str = "run_quality_repair_batch",
    current_stage_id: str = PUBLICATION_STAGE_ID,
    source_surface: str = PUBLICATION_SURFACE,
) -> dict[str, str]:
    return {
        "source": "canonical_current_work_unit",
        "work_unit_id": action_type,
        "work_unit_fingerprint": _stage_native_fingerprint(
            action_type=action_type,
            current_stage_id=current_stage_id,
            source_surface=source_surface,
        ),
    }


def _stage_transition_authority_boundary() -> dict[str, object]:
    return {
        "producer_kind": "runtime_provider",
        "intent_kind": "provider_observation",
        "stage_transition_authority": "one-person-lab",
        "intent_can_write_stage_current_pointer": False,
        "intent_can_write_stage_run_terminal_state": False,
        "intent_can_publish_current_owner_delta": False,
        "intent_can_write_domain_truth": False,
        "intent_can_create_owner_receipt": False,
        "intent_can_create_typed_blocker": False,
        "provider_completion_counts_as_stage_transition": False,
    }


def _write_stage_native_next_action(
    study_root: Path,
    *,
    action_type: str = "run_quality_repair_batch",
    source_surface: str = PUBLICATION_SURFACE,
    include_admission_binding: bool = True,
) -> None:
    payload: dict[str, object] = {
        "schema_version": 1,
        "status": "ready_for_owner_action",
        "action_id": action_type,
        "owner": "write",
        "source_surface": source_surface,
        "current_stage_id": PUBLICATION_STAGE_ID,
        "stage_index_ref": "control/stage_index.json",
        "next_work_unit": "medical_publication_surface_blocked_write_repair",
        "required_output_surface": (
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
    }
    if include_admission_binding:
        payload["stage_transition_authority_boundary"] = _stage_transition_authority_boundary()
        payload["current_work_unit_binding"] = _stage_native_current_work_unit_binding(
            action_type=action_type,
            source_surface=source_surface,
        )
    _write_json(study_root / "control" / "next_action.json", payload)


def _stage_native_quality_repair_dispatch(
    *,
    study_id: str,
    source_authority: str = "stage_native_workspace_next_action",
    source_surface: str = PUBLICATION_SURFACE,
) -> dict[str, object]:
    current_stage_id = PUBLICATION_STAGE_ID
    fingerprint = _stage_native_fingerprint(
        action_type="run_quality_repair_batch",
        current_stage_id=current_stage_id,
        source_surface=source_surface,
    )
    epoch = f"stage-native-next-action::{study_id}::{current_stage_id}"
    route = _owner_route(study_id=study_id, action_type="run_quality_repair_batch", owner="write")
    route.update(
        {
            "truth_epoch": epoch,
            "runtime_health_epoch": epoch,
            "work_unit_fingerprint": fingerprint,
            "source_fingerprint": fingerprint,
            "route_epoch": epoch,
            "source_refs": {
                "work_unit_id": "run_quality_repair_batch",
                "work_unit_fingerprint": fingerprint,
                "source_surface": source_surface,
                "stage_index_ref": "control/stage_index.json",
                "current_stage_id": current_stage_id,
                "current_work_unit_binding": _stage_native_current_work_unit_binding(
                    source_surface=source_surface,
                ),
                "owner_route_currentness_basis": {
                    "truth_epoch": epoch,
                    "runtime_health_epoch": epoch,
                    "work_unit_id": "run_quality_repair_batch",
                    "work_unit_fingerprint": fingerprint,
                },
            },
            "idempotency_key": f"owner-route::{study_id}::{epoch}::write::run_quality_repair_batch",
        }
    )
    payload = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface=PUBLICATION_SURFACE,
        owner_route=route,
    )
    payload.pop("opl_execution_authorization", None)
    prompt_contract = payload["prompt_contract"]
    assert isinstance(prompt_contract, dict)
    prompt_contract.pop("opl_execution_authorization", None)
    prompt_contract["owner_route_currentness_basis"] = route["source_refs"][
        "owner_route_currentness_basis"
    ]
    payload["source_action"] = {
        "study_id": study_id,
        "quest_id": f"quest-{study_id}",
        "action_type": "run_quality_repair_batch",
        "action_id": f"stage-native-next-action::{study_id}::run_quality_repair_batch",
        "owner": "write",
        "request_owner": "write",
        "recommended_owner": "write",
        "authority": source_authority,
        "required_output_surface": PUBLICATION_SURFACE,
        "source_surface": source_surface,
        "stage_index_ref": "control/stage_index.json",
        "current_stage_id": current_stage_id,
        "current_work_unit_binding": _stage_native_current_work_unit_binding(
            source_surface=source_surface,
        ),
    }
    return payload


def _trusted_opl_execution_authorization() -> dict[str, str]:
    return {
        "owner": "one-person-lab",
        "executor_kind": "codex_cli",
        "provider_attempt_ref": "temporal://attempt/stage-native-proof",
        "attempt_lease_ref": "temporal://lease/stage-native-proof",
        "attempt_lease_status": "active",
        "execution_authorization_decision_ref": "opl://execution-authorizations/stage-native-proof",
    }


def test_stage_native_write_repair_dispatch_requires_opl_authorization_after_current_next_action_selection(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_stage_native_next_action(study_root)
    dispatch_payload = _stage_native_quality_repair_dispatch(study_id=study_id)
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch_payload)
    def fail_if_called(**_: object) -> dict[str, object]:
        raise AssertionError("MAS dispatcher must not execute stage-native owner callable without OPL proof")

    monkeypatch.setattr(module.action_execution.quality_repair, "execute_quality_repair_batch", fail_if_called)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["blocked_count"] == 1
    assert result["executed_count"] == 0
    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "opl_execution_authorization_required"
    assert execution["typed_blocker"]["blocker_id"] == "opl_execution_authorization_required"
    assert execution["owner_route_basis"] == "stage_native_workspace_next_action_blocker_projection"
    assert execution["owner_route_current"] is True


def test_stage_native_write_repair_dispatch_with_opl_proof_keeps_stage_native_route_basis(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_stage_native_next_action(study_root)
    dispatch_payload = _stage_native_quality_repair_dispatch(study_id=study_id)
    dispatch_payload["opl_execution_authorization"] = _trusted_opl_execution_authorization()
    prompt_contract = dispatch_payload["prompt_contract"]
    assert isinstance(prompt_contract, dict)
    prompt_contract["opl_execution_authorization"] = _trusted_opl_execution_authorization()
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch_payload)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["execution_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "dry_run"
    assert execution["owner_route_basis"] == "stage_native_workspace_next_action"
    assert execution["opl_execution_authorization_present"] is True


def test_stage_native_write_repair_owner_request_survives_stale_readiness_scan(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_stage_native_next_action(study_root)
    dispatch_payload = _stage_native_quality_repair_dispatch(study_id=study_id)
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    dispatch_payload["refs"] = {"dispatch_path": str(dispatch_path)}
    _write_json(dispatch_path, dispatch_payload)
    owner_route = dispatch_payload["owner_route"]
    assert isinstance(owner_route, dict)
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "quality_repair_batch" / "latest.json",
        {
            "surface": "supervisor_request_handoff_packet",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": f"quest-{study_id}",
            "action_type": "run_quality_repair_batch",
            "request_kind": "run_quality_repair_batch",
            "authority": "stage_native_workspace_next_action",
            "request_owner": "write",
            "expected_owner": "write",
            "next_executable_owner": "write",
            "owner_route": owner_route,
            "owner_pickup": {
                "state": "pending",
                "owner": "write",
                "owner_route": owner_route,
            },
        },
    )
    readiness_route = _owner_route(
        study_id=study_id,
        action_type="complete_medical_paper_readiness_surface",
        owner="MedAutoScience",
    )
    readiness_route["source_refs"] = {
        "work_unit_id": "complete_medical_paper_readiness_surface",
        "work_unit_fingerprint": (
            "stage-current-owner-delta::complete_medical_paper_readiness_surface::"
            "authoring_runtime_authorization::typed_blocker"
        ),
        "owner_route_currentness_basis": {
            "truth_epoch": readiness_route["truth_epoch"],
            "runtime_health_epoch": readiness_route["runtime_health_epoch"],
            "work_unit_id": "complete_medical_paper_readiness_surface",
            "work_unit_fingerprint": (
                "stage-current-owner-delta::complete_medical_paper_readiness_surface::"
                "authoring_runtime_authorization::typed_blocker"
            ),
        },
    }
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": f"quest-{study_id}",
                    "owner_route": readiness_route,
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "source": "stage_kernel_projection.current_owner_delta",
                        "latest_owner_answer_kind": "typed_blocker",
                        "next_owner": "MedAutoScience",
                        "allowed_actions": ["complete_medical_paper_readiness_surface"],
                        "work_unit_id": "complete_medical_paper_readiness_surface",
                    },
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "action_type": "complete_medical_paper_readiness_surface",
                            "reason": "medical_paper_readiness_missing",
                            "owner": "MedAutoScience",
                            "owner_route": readiness_route,
                        }
                    ],
                }
            ],
        },
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "owner_callable_adapters": [],
        },
    )
    def fail_if_called(**_: object) -> dict[str, object]:
        raise AssertionError("MAS dispatcher must not execute owner-request callable without OPL proof")

    monkeypatch.setattr(module.action_execution.quality_repair, "execute_quality_repair_batch", fail_if_called)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["execution_count"] == 1
    assert result["executed_count"] == 0
    assert result["blocked_count"] == 1
    execution = result["executions"][0]
    assert execution["action_type"] == "run_quality_repair_batch"
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "opl_execution_authorization_required"
    assert execution["owner_route_current"] is True
    assert execution["owner_route_basis"] == "stage_native_workspace_next_action_blocker_projection"


def test_stage_native_write_repair_dispatch_survives_readiness_missing_typed_blocker_envelope(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_stage_native_next_action(study_root)
    dispatch_payload = _stage_native_quality_repair_dispatch(study_id=study_id)
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch_payload)
    monkeypatch.setattr(
        progress_module,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "quest_id": f"quest-{study_id}",
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
            "current_executable_owner_action": None,
            "current_owner_ticket": None,
        },
    )
    def fail_if_called(**_: object) -> dict[str, object]:
        raise AssertionError("MAS dispatcher must not execute typed-blocker-envelope callable without OPL proof")

    monkeypatch.setattr(module.action_execution.quality_repair, "execute_quality_repair_batch", fail_if_called)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["execution_count"] == 1
    assert result["executed_count"] == 0
    assert result["blocked_count"] == 1
    execution = result["executions"][0]
    assert execution["action_type"] == "run_quality_repair_batch"
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "opl_execution_authorization_required"
    assert execution["owner_route_current"] is True


def test_stage_native_write_repair_next_action_filters_stale_readiness_and_reviewer_dispatches(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_stage_native_next_action(study_root)
    stage_native_dispatch = _stage_native_quality_repair_dispatch(study_id=study_id)
    stage_native_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    stage_native_dispatch["refs"] = {"dispatch_path": str(stage_native_path)}
    _write_json(stage_native_path, stage_native_dispatch)
    readiness_route = _owner_route(
        study_id=study_id,
        action_type="complete_medical_paper_readiness_surface",
        owner="MedAutoScience",
    )
    readiness_dispatch = _dispatch(
        study_id=study_id,
        action_type="complete_medical_paper_readiness_surface",
        owner="MedAutoScience",
        required_output_surface=(
            "artifacts/medical_paper/<surface_key>.json or "
            "typed blocker:medical_paper_readiness_surface_input_required"
        ),
        owner_route=readiness_route,
    )
    readiness_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "complete_medical_paper_readiness_surface.json"
    )
    readiness_dispatch["refs"] = {"dispatch_path": str(readiness_path)}
    _write_json(readiness_path, readiness_dispatch)
    reviewer_route = _owner_route(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
    )
    reviewer_dispatch = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
        owner_route=reviewer_route,
    )
    reviewer_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    reviewer_dispatch["refs"] = {"dispatch_path": str(reviewer_path)}
    _write_json(reviewer_path, reviewer_dispatch)
    _write_json(
        profile.workspace_root / module.CONSUMER_LATEST_RELATIVE_PATH,
        transition_request_consumer_latest(
            readiness_dispatch,
            reviewer_dispatch,
            stage_native_dispatch,
        ),
    )
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": f"quest-{study_id}",
                    "owner_route": readiness_route,
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "source": "stage_kernel_projection.current_owner_delta",
                        "latest_owner_answer_kind": "typed_blocker",
                        "next_owner": "MedAutoScience",
                        "allowed_actions": ["complete_medical_paper_readiness_surface"],
                        "work_unit_id": "complete_medical_paper_readiness_surface",
                    },
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "action_type": "complete_medical_paper_readiness_surface",
                            "reason": "medical_paper_readiness_missing",
                            "owner": "MedAutoScience",
                            "owner_route": readiness_route,
                        }
                    ],
                }
            ],
        },
    )
    monkeypatch.setattr(
        progress_module,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "quest_id": f"quest-{study_id}",
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "typed_blocker": {
                    "blocker_id": "medical_paper_readiness_missing",
                    "owner": "MedAutoScience",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                },
            },
            "current_executable_owner_action": None,
            "current_owner_ticket": None,
        },
    )
    monkeypatch.setattr(
        module.action_execution.quality_repair,
        "execute_quality_repair_batch",
        lambda **_: {
            "execution_status": "executed",
            "blocked_reason": None,
            "owner_callable_surface": "quality_repair_batch.run_quality_repair_batch",
            "owner_result": {"status": "executed"},
        },
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["execution_count"] == 1
    assert result["executed_count"] == 0
    assert result["blocked_count"] == 1
    execution = result["executions"][0]
    assert execution["action_type"] == "complete_medical_paper_readiness_surface"
    assert execution["dispatch_path"] == str(readiness_path)
    assert execution["owner_route_basis"] == "scan_latest"
    assert execution["dispatch_path"] != str(stage_native_path)


def test_quality_repair_dispatch_without_stage_native_authority_still_requires_opl_authorization(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    dispatch_payload = _stage_native_quality_repair_dispatch(
        study_id=study_id,
        source_authority="mas_owner_surface",
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch_payload)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["blocked_count"] == 1
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "opl_execution_authorization_required"


def test_stage_native_next_action_preempts_older_current_writer_handoff(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_stage_native_next_action(study_root)
    stage_native_dispatch = _stage_native_quality_repair_dispatch(study_id=study_id)
    stage_native_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    stage_native_dispatch["refs"] = {"dispatch_path": str(stage_native_path)}
    _write_json(stage_native_path, stage_native_dispatch)
    old_route = _owner_route(study_id=study_id, action_type="run_quality_repair_batch", owner="write")
    old_route.update(
        {
            "failure_signature": "manuscript_story_surface_delta_missing",
            "owner_reason": "manuscript_story_surface_delta_missing",
            "work_unit_fingerprint": "publication-blockers::old-writer-handoff",
            "source_refs": {
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::old-writer-handoff",
                "blocked_reason": "manuscript_story_surface_delta_missing",
            },
        }
    )
    old_writer_handoff = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface=(
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        owner_route=old_route,
    )
    old_writer_handoff["dispatch_authority"] = "quality_repair_batch_writer_handoff"
    old_writer_handoff["source_action"] = {
        "surface": "quality_repair_batch",
        "blocked_reason": "manuscript_story_surface_delta_missing",
    }
    old_writer_handoff["medical_claim_authoring_allowed"] = True
    prompt_contract = old_writer_handoff["prompt_contract"]
    assert isinstance(prompt_contract, dict)
    prompt_contract["medical_claim_authoring_allowed"] = True
    prompt_contract["allowed_write_surfaces"] = [
        "paper/draft.md",
        "paper/build/review_manuscript.md",
        "paper/claim_evidence_map.json",
        "paper/evidence_ledger.json",
        "paper/review/**",
    ]
    old_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "old_writer_handoff.json"
    )
    old_writer_handoff["refs"] = {"dispatch_path": str(old_path)}
    _write_json(old_path, old_writer_handoff)
    _write_json(
        profile.workspace_root / module.CONSUMER_LATEST_RELATIVE_PATH,
        transition_request_consumer_latest(old_writer_handoff, stage_native_dispatch),
    )
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": old_route,
                    "bridged_writer_handoff": {
                        "owner_route": old_route,
                    },
                }
            ],
        },
    )
    monkeypatch.setattr(
        progress_module,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "typed_blocker": {"blocker_id": "medical_paper_readiness_missing"},
            },
        },
    )
    monkeypatch.setattr(
        module.action_execution.quality_repair,
        "execute_quality_repair_batch",
        lambda **_: {
            "execution_status": "handoff_ready",
            "blocked_reason": None,
            "owner_callable_surface": "quality_repair_batch.run_quality_repair_batch",
            "writer_worker_handoff": {},
            "provider_attempt_or_lease_required": True,
        },
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["execution_count"] == 1
    assert result["executed_count"] == 0
    assert result["blocked_count"] == 1
    assert execution["dispatch_path"] == str(old_path)
    assert execution["dispatch_path"] != str(stage_native_path)
    assert execution["owner_route_basis"] != "stage_native_workspace_next_action"


def test_stage_native_next_action_without_authority_binding_does_not_preempt_current_writer_handoff(
    monkeypatch,
    tmp_path: Path,
) -> None:
    materializer = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    dispatch_module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_stage_native_next_action(study_root, include_admission_binding=False)
    stage_native_dispatch = _stage_native_quality_repair_dispatch(study_id=study_id)
    stage_native_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    stage_native_dispatch["refs"] = {"dispatch_path": str(stage_native_path)}
    _write_json(stage_native_path, stage_native_dispatch)
    old_route = _owner_route(study_id=study_id, action_type="run_quality_repair_batch", owner="write")
    old_route.update(
        {
            "failure_signature": "manuscript_story_surface_delta_missing",
            "owner_reason": "manuscript_story_surface_delta_missing",
            "work_unit_fingerprint": "publication-blockers::old-writer-handoff",
            "source_refs": {
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::old-writer-handoff",
                "blocked_reason": "manuscript_story_surface_delta_missing",
            },
        }
    )
    old_writer_handoff = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface=(
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        owner_route=old_route,
    )
    old_writer_handoff["dispatch_authority"] = "quality_repair_batch_writer_handoff"
    old_writer_handoff["source_action"] = {
        "surface": "quality_repair_batch",
        "blocked_reason": "manuscript_story_surface_delta_missing",
    }
    old_writer_handoff["medical_claim_authoring_allowed"] = True
    prompt_contract = old_writer_handoff["prompt_contract"]
    assert isinstance(prompt_contract, dict)
    prompt_contract["medical_claim_authoring_allowed"] = True
    prompt_contract["allowed_write_surfaces"] = [
        "paper/draft.md",
        "paper/build/review_manuscript.md",
        "paper/claim_evidence_map.json",
        "paper/evidence_ledger.json",
        "paper/review/**",
    ]
    old_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    old_writer_handoff["refs"] = {"dispatch_path": str(old_path)}
    _write_json(old_path, old_writer_handoff)
    _write_json(
        profile.workspace_root / materializer.CONSUMER_LATEST_RELATIVE_PATH,
        transition_request_consumer_latest(old_writer_handoff, stage_native_dispatch),
    )
    _write_json(
        profile.workspace_root / materializer.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": old_route,
                    "bridged_writer_handoff": {
                        "owner_route": old_route,
                    },
                }
            ],
        },
    )
    monkeypatch.setattr(
        progress_module,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "typed_blocker": {"blocker_id": "medical_paper_readiness_missing"},
            },
        },
    )
    monkeypatch.setattr(
        dispatch_module.action_execution.quality_repair,
        "execute_quality_repair_batch",
        lambda **_: {
            "execution_status": "handoff_ready",
            "blocked_reason": None,
            "owner_callable_surface": "quality_repair_batch.run_quality_repair_batch",
            "writer_worker_handoff": {},
            "provider_attempt_or_lease_required": True,
        },
    )

    materialized = materializer.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )
    assert "owner_callable_adapters" not in materialized
    assert materialized["canonical_transition_request_surface"] == "domain_progress_transition_requests"
    assert materialized["legacy_owner_callable_adapter_diagnostics"]["diagnostic_only"] is True
    assert materialized["legacy_owner_callable_adapter_diagnostics"]["readiness_authority"] is False
    assert materialized["domain_progress_transition_requests"] == []
    assert any(
        item["action_type"] == "run_quality_repair_batch"
        and item["reason"] == "stage_native_workspace_next_action_requires_authority_binding"
        for item in materialized["ignored_actions"]
    )

    result = dispatch_module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["execution_count"] == 1
    assert execution["dispatch_path"] == str(old_path)
    assert execution["owner_route_basis"] != "stage_native_workspace_next_action"
