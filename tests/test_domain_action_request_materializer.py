from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from tests.domain_action_request_materializer_cases.shared import owner_route as _owner_route
from tests.domain_action_request_materializer_cases.shared import (
    disable_progress_projection as _disable_progress_projection,
)
from tests.domain_action_request_materializer_cases.shared import (
    stage_native_admission_fields as _stage_native_admission_fields,
)
from tests.domain_action_request_materializer_cases.shared import (
    unsupported_domain_action as _unsupported_domain_action,
)
from tests.domain_action_request_materializer_cases.shared import write_json as _write_json
from tests.domain_action_request_materializer_cases.request_handoff_dispatch_cases import *  # noqa: F403,F401
from tests.domain_action_request_materializer_cases.unsupported_action_boundary import *
from tests.study_runtime_test_helpers import make_profile, write_study


@pytest.fixture(autouse=True)
def _isolated_opl_state_dir(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OPL_STATE_DIR", str(tmp_path / "opl-state"))


def test_materialize_domain_action_requests_prefers_fresh_progress_ticket_over_stale_readiness_scan(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    write_study(profile.workspace_root, study_id, quest_id="quest-dm003")
    stale_route = _owner_route(
        study_id=study_id,
        quest_id="quest-dm003",
        next_owner="MedAutoScience",
        owner_reason="medical_paper_readiness_missing",
        allowed_actions=["complete_medical_paper_readiness_surface"],
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": "quest-dm003",
                    "owner_route": stale_route,
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "source": "stage_kernel_projection.current_owner_delta",
                        "latest_owner_answer_kind": "typed_blocker",
                        "allowed_actions": ["complete_medical_paper_readiness_surface"],
                        "work_unit_id": "complete_medical_paper_readiness_surface",
                        "next_owner": "MedAutoScience",
                    },
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "quest_id": "quest-dm003",
                            "action_type": "complete_medical_paper_readiness_surface",
                            "authority": "mas_owner_surface",
                            "owner": "MedAutoScience",
                            "request_owner": "MedAutoScience",
                            "recommended_owner": "MedAutoScience",
                            "reason": "medical_paper_readiness_missing",
                            "required_output_surface": "artifacts/medical_paper/<surface_key>.json",
                            "work_unit_id": "complete_medical_paper_readiness_surface",
                            "owner_route": stale_route,
                        }
                    ],
                }
            ],
        },
    )
    fresh_route = _owner_route(
        study_id=study_id,
        quest_id="quest-dm003",
        next_owner="finalize",
        owner_reason="dpcc_publication_gate_replay_after_current_ai_reviewer_record",
        allowed_actions=["run_gate_clearing_batch"],
    )

    def read_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": "quest-dm003",
            "generated_at": "2026-06-07T17:20:00+00:00",
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "finalize",
                "next_work_unit": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "source": "domain_transition",
                "source_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                "next_owner": "finalize",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "allowed_actions": ["run_gate_clearing_batch"],
            },
            "current_owner_ticket": {
                "surface_kind": "mas_current_owner_ticket",
                "owner": "finalize",
                "allowed_action": "run_gate_clearing_batch",
                "work_unit": {
                    "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "summary": "Replay publication gate after the current AI reviewer record.",
                },
                "target_surface": {
                    "ref_kind": "route_obligation",
                    "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                },
            },
            "owner_route": fresh_route,
            "paper_progress_delta": {"count": 1},
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
        }

    monkeypatch.setattr(progress_module, "read_study_progress", read_progress)

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert [item["action_type"] for item in result["default_executor_dispatches"]] == [
        "run_gate_clearing_batch"
    ]
    dispatch = result["default_executor_dispatches"][0]
    assert dispatch["next_executable_owner"] == "finalize"
    assert dispatch["owner_route"]["allowed_actions"] == ["run_gate_clearing_batch"]
    assert dispatch["owner_route"]["source_refs"]["work_unit_id"] == (
        "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    )
    assert {
        item["action_type"]: item["reason"]
        for item in result["ignored_actions"]
        if item["study_id"] == study_id
    } == {
        "complete_medical_paper_readiness_surface": (
            "superseded_by_fresh_study_progress_current_owner_ticket"
        )
    }


def test_materialize_domain_action_requests_prefers_fresh_domain_transition_over_stage_native_write(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm003")
    _write_json(
        study_root / "control" / "next_action.json",
        {
            "status": "ready_for_owner_action",
            "action_id": "run_quality_repair_batch",
            "owner": "write",
            "source_surface": "control/next_action.json",
            "current_stage_id": "08-publication_package_handoff",
        },
    )
    stale_route = _owner_route(
        study_id=study_id,
        quest_id="quest-dm003",
        next_owner="MedAutoScience",
        owner_reason="medical_paper_readiness_missing",
        allowed_actions=["complete_medical_paper_readiness_surface"],
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": "quest-dm003",
                    "owner_route": stale_route,
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "source": "stage_kernel_projection.current_owner_delta",
                        "latest_owner_answer_kind": "typed_blocker",
                        "allowed_actions": ["complete_medical_paper_readiness_surface"],
                        "work_unit_id": "complete_medical_paper_readiness_surface",
                        "next_owner": "MedAutoScience",
                    },
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "quest_id": "quest-dm003",
                            "action_type": "complete_medical_paper_readiness_surface",
                            "authority": "mas_owner_surface",
                            "owner": "MedAutoScience",
                            "request_owner": "MedAutoScience",
                            "recommended_owner": "MedAutoScience",
                            "reason": "medical_paper_readiness_missing",
                            "work_unit_id": "complete_medical_paper_readiness_surface",
                            "owner_route": stale_route,
                        }
                    ],
                }
            ],
        },
    )

    def read_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": "quest-dm003",
            "generated_at": "2026-06-07T19:20:00+00:00",
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "finalize",
                "next_work_unit": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "source": "domain_transition",
                "source_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                "next_owner": "finalize",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "allowed_actions": ["request_opl_stage_attempt"],
                "target_surface": {
                    "surface_key": "publication_gate_replay",
                },
            },
            "current_owner_ticket": {
                "surface_kind": "mas_current_owner_ticket",
                "owner": "MedAutoScience",
                "allowed_action": "complete_medical_paper_readiness_surface",
                "work_unit": {
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                },
            },
            "owner_route": stale_route,
            "paper_progress_delta": {"count": 0},
            "deliverable_progress_delta": {"count": 0},
        }

    monkeypatch.setattr(progress_module, "read_study_progress", read_progress)

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert [item["action_type"] for item in result["default_executor_dispatches"]] == [
        "run_gate_clearing_batch"
    ]
    dispatch = result["default_executor_dispatches"][0]
    assert dispatch["next_executable_owner"] == "gate_clearing_batch"
    assert dispatch["source_action"]["controller_work_unit_id"] == (
        "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    )
    assert dispatch["owner_route"]["allowed_actions"] == ["run_gate_clearing_batch"]
    assert {
        item["action_type"]: item["reason"]
        for item in result["ignored_actions"]
        if item["study_id"] == study_id
        } == {
            "complete_medical_paper_readiness_surface": (
                "superseded_by_fresh_study_progress_current_owner_ticket"
            ),
            "run_quality_repair_batch": "stage_native_workspace_next_action_requires_authority_binding",
        }


def test_materialize_domain_action_requests_blocks_stage_native_write_when_fresh_envelope_is_typed_blocker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm003")
    _write_json(
        study_root / "control" / "next_action.json",
        {
            "status": "ready_for_owner_action",
            "action_id": "run_quality_repair_batch",
            "owner": "write",
            "source_surface": "control/next_action.json",
            "current_stage_id": "08-publication_package_handoff",
        },
    )
    stale_route = _owner_route(
        study_id=study_id,
        quest_id="quest-dm003",
        next_owner="MedAutoScience",
        owner_reason="medical_paper_readiness_missing",
        allowed_actions=["complete_medical_paper_readiness_surface"],
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "quest_id": "quest-dm003", "owner_route": stale_route}],
        },
    )

    def read_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": "quest-dm003",
            "generated_at": "2026-06-07T19:20:00+00:00",
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "typed_blocker": {
                    "blocker_id": "human_gate_required",
                    "owner": "MedAutoScience",
                    "work_unit_id": "human_publication_decision",
                },
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "source": "domain_transition",
                "next_owner": "finalize",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "allowed_actions": ["request_opl_stage_attempt"],
            },
            "current_owner_ticket": {
                "surface_kind": "mas_current_owner_ticket",
                "owner": "MedAutoScience",
                "allowed_action": "complete_medical_paper_readiness_surface",
                "work_unit": {"work_unit_id": "complete_medical_paper_readiness_surface"},
            },
            "owner_route": stale_route,
        }

    monkeypatch.setattr(progress_module, "read_study_progress", read_progress)

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["default_executor_dispatches"] == []
    assert any(
        item["action_type"] == "current_execution_envelope_typed_blocker"
        and item["reason"] == "unsupported_action_type"
        for item in result["ignored_actions"]
    )
    assert any(
        item["action_type"] == "run_quality_repair_batch"
        and item["reason"] == "stage_native_workspace_next_action_requires_authority_binding"
        for item in result["ignored_actions"]
    )


def test_materialize_domain_action_requests_routes_consumed_write_closeout_to_ai_reviewer(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm003")
    _write_json(
        study_root / "control" / "next_action.json",
        {
            "status": "ready_for_owner_action",
            "action_id": "run_quality_repair_batch",
            "owner": "write",
            "source_surface": "control/next_action.json",
            "current_stage_id": "08-publication_package_handoff",
        },
    )
    stale_route = _owner_route(
        study_id=study_id,
        quest_id="quest-dm003",
        next_owner="write",
        owner_reason="medical_prose_write_repair",
        allowed_actions=["run_quality_repair_batch"],
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "quest_id": "quest-dm003", "owner_route": stale_route}],
        },
    )
    consumed_fingerprint = "publication-blockers::0915410f804b3697"
    successor_fingerprint = (
        "domain-transition::ai_reviewer_re_eval::ai_reviewer_medical_prose_quality_review"
    )

    def read_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": "quest-dm003",
            "generated_at": "2026-06-14T02:30:00+00:00",
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "med-autoscience",
                "source": "accepted_closeout_consumed_pending",
                "typed_blocker": {
                    "blocker_type": "provider_completion_is_not_domain_ready",
                    "owner": "med-autoscience",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": consumed_fingerprint,
                },
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "domain_transition",
                "source_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "next_owner": "ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
                "allowed_actions": ["return_to_ai_reviewer_workflow"],
                "work_unit_id": "ai_reviewer_medical_prose_quality_review",
                "work_unit_fingerprint": successor_fingerprint,
                "action_fingerprint": successor_fingerprint,
                "controller_action": "return_to_ai_reviewer_workflow",
                "domain_transition_decision_type": "ai_reviewer_re_eval",
                "next_work_unit": {
                    "unit_id": "ai_reviewer_medical_prose_quality_review",
                    "lane": "review",
                },
                "target_surface": {
                    "surface_key": "publication_eval_latest",
                    "surface_ref": "artifacts/publication_eval/latest.json",
                },
            },
            "domain_transition": {
                "decision_type": "ai_reviewer_re_eval",
                "route_target": "review",
                "owner": "ai_reviewer",
                "controller_action": "return_to_ai_reviewer_workflow",
                "next_work_unit": {
                    "unit_id": "ai_reviewer_medical_prose_quality_review",
                    "lane": "review",
                },
                "completion_receipt_consumption": {
                    "status": "consumed",
                    "action_fingerprint": consumed_fingerprint,
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": consumed_fingerprint,
                },
            },
            "owner_route": stale_route,
        }

    monkeypatch.setattr(progress_module, "read_study_progress", read_progress)

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert [item["action_type"] for item in result["default_executor_dispatches"]] == [
        "return_to_ai_reviewer_workflow"
    ]
    dispatch = result["default_executor_dispatches"][0]
    assert dispatch["next_executable_owner"] == "ai_reviewer"
    assert dispatch["owner_route"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
    assert dispatch["owner_route"]["source_refs"]["work_unit_id"] == (
        "ai_reviewer_medical_prose_quality_review"
    )
    assert not any(
        item["action_type"] == "current_execution_envelope_typed_blocker"
        for item in result["ignored_actions"]
    )


def test_materialize_domain_action_requests_blocks_readiness_and_stage_native_when_current_action_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_json(
        study_root / "control" / "next_action.json",
        {
            "schema_version": 1,
            "status": "ready_for_owner_action",
            "action_id": "stage-native-next-action::run_quality_repair_batch",
            "action_type": "run_quality_repair_batch",
            "owner": "write",
            "source_surface": "artifacts/reports/medical_publication_surface/latest.json",
            "current_stage_id": "08-publication_package_handoff",
            "stage_index_ref": "control/stage_index.json",
            "current_package_status": "not_ready",
            "next_work_unit": "medical_publication_surface_blocked_write_repair",
            **_stage_native_admission_fields(),
            "required_output_surface": (
                "canonical manuscript story-surface delta or "
                "typed blocker:manuscript_story_surface_delta_missing"
            ),
        },
    )
    readiness_route = _owner_route(
        study_id=study_id,
        quest_id=study_id,
        next_owner="MedAutoScience",
        owner_reason="medical_paper_readiness_missing",
        allowed_actions=["complete_medical_paper_readiness_surface"],
    )
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
            "current_executable_owner_action": None,
            "current_owner_ticket": None,
            "owner_route": readiness_route,
            "deliverable_progress_delta": {"count": 0},
        }

    monkeypatch.setattr(progress_module, "read_study_progress", read_progress)

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["request_task_count"] == 0
    assert result["default_executor_dispatch_count"] == 0
    assert any(
        item["action_type"] == "complete_medical_paper_readiness_surface"
        and item["reason"] == "superseded_by_current_work_unit_typed_blocker"
        for item in result["ignored_actions"]
    )
    assert any(
        item["action_type"] == "run_quality_repair_batch"
        and item["reason"]
        == "stage_native_workspace_next_action_requires_current_work_unit_currentness_match"
        for item in result["ignored_actions"]
    )


def test_materialize_domain_action_requests_prefers_fresh_readiness_action_over_stage_native_write(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_json(
        study_root / "control" / "next_action.json",
        {
            "status": "ready_for_owner_action",
            "action_id": "run_quality_repair_batch",
            "owner": "write",
            "source_surface": "artifacts/reports/medical_publication_surface/latest.json",
            "current_stage_id": "08-publication_package_handoff",
        },
    )
    route = _owner_route(
        study_id=study_id,
        quest_id=study_id,
        next_owner="MedAutoScience",
        owner_reason="medical_paper_readiness_missing",
        allowed_actions=["complete_medical_paper_readiness_surface"],
    )

    def read_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "generated_at": "2026-06-07T19:30:00+00:00",
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "MedAutoScience",
                "next_work_unit": "complete_medical_paper_readiness_surface",
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "source": "stage_kernel_projection.current_owner_delta",
                "source_ref": (
                    "artifacts/stage_outputs/08-publication_package_handoff/"
                    "receipts/typed_blocker.json"
                ),
                "next_owner": "MedAutoScience",
                "work_unit_id": "complete_medical_paper_readiness_surface",
                "allowed_actions": ["complete_medical_paper_readiness_surface"],
                "surface_key": "authoring_runtime_authorization",
                "target_surface": {
                    "surface_key": "authoring_runtime_authorization",
                },
            },
            "current_owner_ticket": {
                "surface_kind": "mas_current_owner_ticket",
                "owner": "MedAutoScience",
                "allowed_action": "complete_medical_paper_readiness_surface",
                "work_unit": {"work_unit_id": "complete_medical_paper_readiness_surface"},
                "target_surface": {
                    "surface_key": "authoring_runtime_authorization",
                },
            },
            "owner_route": route,
        }

    monkeypatch.setattr(progress_module, "read_study_progress", read_progress)

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert [item["action_type"] for item in result["default_executor_dispatches"]] == [
        "complete_medical_paper_readiness_surface"
    ]
    dispatch = result["default_executor_dispatches"][0]
    assert dispatch["next_executable_owner"] == "MedAutoScience"
    assert dispatch["surface_key"] == "authoring_runtime_authorization"
    assert dispatch["owner_route"]["allowed_actions"] == ["complete_medical_paper_readiness_surface"]


def test_materialize_domain_action_requests_apply_refreshes_latest_when_current_queue_is_empty(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    _disable_progress_projection(monkeypatch)
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    stale_dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "unsupported_supervisor_action.json"
    )
    consumer_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json"
    latest_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(stale_dispatch_path, {"surface": "default_executor_dispatch_request", "dispatch_status": "ready"})
    _write_json(
        consumer_path,
        {
            "surface": "domain_action_request_materializer",
            "generated_at": "2026-05-07T16:13:16+00:00",
            "default_executor_dispatch_count": 1,
            "default_executor_dispatches": [
                {
                    "study_id": study_id,
                    "action_type": "unsupported_supervisor_action",
                    "dispatch_status": "ready",
                    "refs": {"dispatch_path": str(stale_dispatch_path)},
                }
            ],
        },
    )
    _write_json(
        latest_path,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id}],
            "action_queue": [],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    consumer = json.loads(consumer_path.read_text(encoding="utf-8"))
    assert result["runtime_control_owner"] == "one-person-lab"
    assert result["request_task_count"] == 0
    assert result["default_executor_dispatch_count"] == 0
    assert result["written_files"] == [str(consumer_path)]
    assert consumer["generated_at"] == result["generated_at"]
    assert consumer["default_executor_dispatches"] == []
    assert consumer["written_files"] == [str(consumer_path)]


def test_materialize_domain_action_requests_only_writes_current_owner_dispatch_for_route_epoch(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    _disable_progress_projection(monkeypatch)
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm002")
    route = _owner_route(
        study_id=study_id,
        quest_id="quest-dm002",
        next_owner="artifact_os",
        owner_reason="current_package_freshness_required",
        allowed_actions=["current_package_freshness_required", "return_to_ai_reviewer_workflow"],
    )
    latest_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        latest_path,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": "quest-dm002",
                    "action_type": "current_package_freshness_required",
                    "authority": "observability_only",
                    "owner": "artifact_os",
                    "reason": "current_package_freshness_required",
                    "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
                    "owner_route": route,
                    "handoff_packet": {
                        "request_kind": "current_package_freshness_required",
                        "authority": "observability_only",
                        "request_owner": "artifact_os",
                        "owner_route": route,
                    },
                },
                {
                    "study_id": study_id,
                    "quest_id": "quest-dm002",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "authority": "observability_only",
                    "owner": "ai_reviewer",
                    "reason": "ai_reviewer_assessment_required",
                    "required_output_surface": "artifacts/publication_eval/latest.json",
                    "owner_route": route,
                    "handoff_packet": {
                        "request_kind": "return_to_ai_reviewer_workflow",
                        "authority": "observability_only",
                        "request_owner": "ai_reviewer",
                        "owner_route": route,
                    },
                },
            ],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    dispatches = result["default_executor_dispatches"]
    assert [item["action_type"] for item in dispatches] == [
        "current_package_freshness_required",
        "return_to_ai_reviewer_workflow",
    ]
    assert dispatches[0]["dispatch_status"] == "ready"
    assert dispatches[1]["dispatch_status"] == "blocked"
    assert dispatches[1]["blocked_reason"] == "owner_route_next_owner_mismatch"
    dispatch_dir = study_root / "artifacts" / "supervision" / "consumer" / "default_executor_dispatches"
    assert (dispatch_dir / "current_package_freshness_required.json").is_file()
    assert not (dispatch_dir / "return_to_ai_reviewer_workflow.json").exists()
