from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.domain_action_request_materializer_cases.shared import owner_route as _owner_route
from tests.domain_action_request_materializer_cases.shared import (
    disable_progress_projection as _disable_progress_projection,
)
from tests.domain_action_request_materializer_cases.shared import (
    unsupported_domain_action as _unsupported_domain_action,
)
from tests.domain_action_request_materializer_cases.shared import write_json as _write_json
from tests.study_runtime_test_helpers import make_profile, write_study


def test_materialize_domain_action_requests_writes_request_handoff_for_publication_gate_and_ai_reviewer_actions(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    _disable_progress_projection(monkeypatch)
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm")
    latest_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    gate_route = _owner_route(
        study_id=study_id,
        quest_id="quest-dm",
        next_owner="publication_gate",
        owner_reason="publication_gate_specificity_required",
        allowed_actions=["publication_gate_specificity_required"],
    )
    ai_route = _owner_route(
        study_id=study_id,
        quest_id="quest-dm",
        next_owner="ai_reviewer",
        owner_reason="ai_reviewer_assessment_required",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )
    artifact_route = _owner_route(
        study_id=study_id,
        quest_id="quest-dm",
        next_owner="artifact_os",
        owner_reason="artifact_work_required",
        allowed_actions=[
            "current_package_freshness_required",
            "artifact_display_surface_materialization_required",
        ],
    )
    _write_json(
        latest_path,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": "quest-dm",
                    "action_type": "publication_gate_specificity_required",
                    "authority": "observability_only",
                    "owner": "publication_gate",
                    "recommended_owner": "publication_gate",
                    "reason": "publication_gate_specificity_required",
                    "owner_route": gate_route,
                    "handoff_packet": {
                        "request_kind": "publication_gate_specificity_required",
                        "authority": "observability_only",
                        "request_owner": "publication_gate",
                        "owner_route": gate_route,
                        "paper_package_mutation_allowed": False,
                        "quality_gate_relaxation_allowed": False,
                    },
                },
                {
                    "study_id": study_id,
                    "quest_id": "quest-dm",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "authority": "observability_only",
                    "owner": "ai_reviewer",
                    "recommended_owner": "ai_reviewer",
                    "reason": "ai_reviewer_assessment_required",
                    "required_output_surface": "artifacts/publication_eval/latest.json",
                    "owner_route": ai_route,
                    "handoff_packet": {
                        "request_kind": "return_to_ai_reviewer_workflow",
                        "authority": "observability_only",
                        "request_owner": "ai_reviewer",
                        "owner_route": ai_route,
                        "paper_package_mutation_allowed": False,
                        "quality_gate_relaxation_allowed": False,
                    },
                },
                {
                    "study_id": study_id,
                    "quest_id": "quest-dm",
                    "action_type": "current_package_freshness_required",
                    "authority": "observability_only",
                    "owner": "artifact_os",
                    "recommended_owner": "artifact_os",
                    "reason": "current_package_freshness_required",
                    "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
                    "owner_route": artifact_route,
                    "handoff_packet": {
                        "request_kind": "current_package_freshness_required",
                        "authority": "observability_only",
                        "request_owner": "artifact_os",
                        "owner_route": artifact_route,
                        "paper_package_mutation_allowed": False,
                        "quality_gate_relaxation_allowed": False,
                    },
                },
                {
                    "study_id": study_id,
                    "quest_id": "quest-dm",
                    "action_type": "artifact_display_surface_materialization_required",
                    "authority": "observability_only",
                    "owner": "artifact_os",
                    "recommended_owner": "artifact_os",
                    "reason": "display_surface_materialization_failed",
                    "required_output_surface": "paper/display_registry.json",
                    "owner_route": artifact_route,
                    "handoff_packet": {
                        "request_kind": "artifact_display_surface_materialization_required",
                        "authority": "observability_only",
                        "request_owner": "artifact_os",
                        "owner_route": artifact_route,
                        "paper_package_mutation_allowed": False,
                        "quality_gate_relaxation_allowed": False,
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

    gate_packet_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "requests"
        / "publication_gate_specificity"
        / "latest.json"
    )
    ai_packet_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "requests"
        / "ai_reviewer"
        / "latest.json"
    )
    freshness_packet_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "requests"
        / "current_package_freshness"
        / "latest.json"
    )
    display_packet_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "requests"
        / "artifact_display_materialization"
        / "latest.json"
    )
    assert result["runtime_control_owner"] == "one-person-lab"
    assert result["request_tasks"][0]["action_type"] == "publication_gate_specificity_required"
    assert result["request_tasks"][1]["action_type"] == "return_to_ai_reviewer_workflow"
    assert result["request_tasks"][2]["action_type"] == "current_package_freshness_required"
    assert result["request_tasks"][3]["action_type"] == "artifact_display_surface_materialization_required"
    assert result["request_tasks"][0]["request_owner"] == "publication_gate"
    assert result["request_tasks"][1]["request_owner"] == "ai_reviewer"
    assert result["request_tasks"][2]["request_owner"] == "artifact_os"
    assert result["request_tasks"][3]["request_owner"] == "artifact_os"
    assert result["request_tasks"][0]["expected_owner"] == "publication_gate"
    assert result["request_tasks"][1]["expected_owner"] == "ai_reviewer"
    assert result["request_tasks"][2]["expected_owner"] == "artifact_os"
    assert result["request_tasks"][3]["expected_owner"] == "artifact_os"
    assert result["request_tasks"][0]["owner_pickup"]["owner"] == "publication_gate"
    assert result["request_tasks"][1]["owner_pickup"]["owner"] == "ai_reviewer"
    assert result["request_tasks"][2]["owner_pickup"]["owner"] == "artifact_os"
    assert result["request_tasks"][3]["owner_pickup"]["owner"] == "artifact_os"
    assert result["request_tasks"][1]["required_output_surface"] == "artifacts/publication_eval/latest.json"
    assert result["request_tasks"][2]["required_output_surface"] == "artifacts/controller/gate_clearing_batch/latest.json"
    assert result["request_tasks"][3]["required_output_surface"] == "paper/display_registry.json"
    assert result["request_tasks"][0]["refs"]["request_packet_path"] == str(gate_packet_path)
    assert result["request_tasks"][1]["refs"]["request_packet_path"] == str(ai_packet_path)
    assert result["request_tasks"][2]["refs"]["request_packet_path"] == str(freshness_packet_path)
    assert result["request_tasks"][3]["refs"]["request_packet_path"] == str(display_packet_path)
    assert result["ignored_actions"] == []
    assert {task["dispatch_status"] for task in result["request_tasks"]} == {"transition_request_pending"}
    assert {task["provider_admission_pending"] for task in result["request_tasks"]} == {False}
    assert {task["provider_admission_requires_opl_runtime_result"] for task in result["request_tasks"]} == {True}
    assert {task["mas_local_request_packet_persistence"] for task in result["request_tasks"]} == {"forbidden"}
    assert not gate_packet_path.exists()
    assert not ai_packet_path.exists()
    assert not freshness_packet_path.exists()
    assert not display_packet_path.exists()
    gate_packet = result["request_tasks"][0]["handoff_packet"]
    ai_packet = result["request_tasks"][1]["handoff_packet"]
    freshness_packet = result["request_tasks"][2]["handoff_packet"]
    display_packet = result["request_tasks"][3]["handoff_packet"]
    assert gate_packet["authority"] == "observability_only"
    assert ai_packet["authority"] == "observability_only"
    assert freshness_packet["authority"] == "observability_only"
    assert display_packet["authority"] == "observability_only"
    assert gate_packet["request_owner"] == "publication_gate"
    assert ai_packet["request_owner"] == "ai_reviewer"
    assert freshness_packet["request_owner"] == "artifact_os"
    assert display_packet["request_owner"] == "artifact_os"
    assert gate_packet["next_executable_owner"] == "publication_gate"
    assert ai_packet["next_executable_owner"] == "ai_reviewer"
    assert freshness_packet["next_executable_owner"] == "artifact_os"
    assert display_packet["next_executable_owner"] == "artifact_os"
    assert gate_packet["owner_pickup"]["owner"] == "publication_gate"
    assert ai_packet["owner_pickup"]["owner"] == "ai_reviewer"
    assert freshness_packet["owner_pickup"]["owner"] == "artifact_os"
    assert display_packet["owner_pickup"]["owner"] == "artifact_os"
    assert ai_packet["required_output_surface"] == "artifacts/publication_eval/latest.json"
    assert freshness_packet["required_output_surface"] == "artifacts/controller/gate_clearing_batch/latest.json"
    assert display_packet["required_output_surface"] == "paper/display_registry.json"
    assert gate_packet["supervisor_authority_boundary"] == "request_only"
    assert ai_packet["supervisor_authority_boundary"] == "request_only"
    assert freshness_packet["supervisor_authority_boundary"] == "request_only"
    assert display_packet["supervisor_authority_boundary"] == "request_only"
    assert "publication_eval" in ai_packet["consumer_does_not_mutate"]
    assert gate_packet["paper_package_mutation_allowed"] is False
    assert ai_packet["quality_gate_relaxation_allowed"] is False
    assert not (
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json"
    ).exists()


def test_materialize_domain_action_requests_request_handoff_requires_owner_route_allowed_action(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    _disable_progress_projection(monkeypatch)
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm")
    route = _owner_route(
        study_id=study_id,
        quest_id="quest-dm",
        next_owner="publication_gate",
        owner_reason="publication_gate_specificity_required",
        allowed_actions=[],
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
                    "quest_id": "quest-dm",
                    "action_type": "publication_gate_specificity_required",
                    "authority": "observability_only",
                    "owner": "publication_gate",
                    "recommended_owner": "publication_gate",
                    "reason": "publication_gate_specificity_required",
                    "owner_route": route,
                    "handoff_packet": {
                        "request_kind": "publication_gate_specificity_required",
                        "authority": "observability_only",
                        "request_owner": "publication_gate",
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

    task = result["request_tasks"][0]
    packet_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "publication_gate_specificity_required.json"
    )
    assert task["dispatch_status"] == "blocked"
    assert task["blocked_reason"] == "owner_route_next_owner_mismatch"
    assert task["owner_route_current"] is False
    assert not packet_path.exists()


def test_materialize_domain_action_requests_mixed_queue_writes_default_executor_dispatches(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    _disable_progress_projection(monkeypatch)
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dpcc")
    latest_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        latest_path,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": _owner_route(
                        study_id=study_id,
                        quest_id="quest-dpcc",
                        next_owner="external_engineering_agent",
                        owner_reason="unsupported_supervisor_action",
                        allowed_actions=[
                            "unsupported_supervisor_action",
                            "publication_gate_specificity_required",
                            "return_to_ai_reviewer_workflow",
                        ],
                    ),
                }
            ],
            "action_queue": [
                _unsupported_domain_action(study_id, "quest-dpcc"),
                {
                    "study_id": study_id,
                    "quest_id": "quest-dpcc",
                    "action_type": "publication_gate_specificity_required",
                    "authority": "observability_only",
                    "owner": "publication_gate",
                    "reason": "publication_gate_specificity_required",
                    "handoff_packet": {
                        "request_kind": "publication_gate_specificity_required",
                        "authority": "observability_only",
                        "request_owner": "publication_gate",
                    },
                },
                {
                    "study_id": study_id,
                    "quest_id": "quest-dpcc",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "authority": "observability_only",
                    "owner": "ai_reviewer",
                    "reason": "ai_reviewer_assessment_required",
                    "handoff_packet": {
                        "request_kind": "return_to_ai_reviewer_workflow",
                        "authority": "observability_only",
                        "request_owner": "ai_reviewer",
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
    assert result["runtime_control_owner"] == "one-person-lab"
    assert result["ignored_actions"][0]["action_type"] == "unsupported_supervisor_action"
    assert result["ignored_actions"][0]["reason"] == "unsupported_action_type"
    assert result["default_executor_dispatch_count"] == 2
    assert [dispatch["executor_kind"] for dispatch in dispatches] == [
        "codex_cli_default",
        "codex_cli_default",
    ]
    assert [dispatch["action_type"] for dispatch in dispatches] == [
        "publication_gate_specificity_required",
        "return_to_ai_reviewer_workflow",
    ]
    assert dispatches[0]["next_executable_owner"] == "publication_gate"
    assert dispatches[1]["next_executable_owner"] == "ai_reviewer"
    assert dispatches[0]["default_model_policy"] == "inherit_current_codex_configuration"
    assert set(module.FORBIDDEN_SURFACES).issubset(dispatches[1]["prompt_contract"]["forbidden_surfaces"])
    assert "artifacts/publication_eval/latest.json" in dispatches[1]["prompt_contract"]["forbidden_surfaces"]
    assert "artifacts/controller_decisions/latest.json" in dispatches[1]["prompt_contract"]["forbidden_surfaces"]
    assert "publication_eval/latest.json" in dispatches[1]["prompt_contract"]["required_output_surface"]
    assert dispatches[1]["prompt_contract"]["manual_study_patch_allowed"] is False
    assert dispatches[0]["dispatch_status"] == "blocked"
    assert dispatches[0]["blocked_reason"] == "owner_route_next_owner_mismatch"
    assert dispatches[1]["dispatch_status"] == "blocked"
    assert dispatches[1]["blocked_reason"] == "owner_route_next_owner_mismatch"

    dispatch_dir = study_root / "artifacts" / "supervision" / "consumer" / "default_executor_dispatches"
    written_dispatches = sorted(dispatch_dir.glob("*.json"))
    assert written_dispatches == []

    assert not (study_root / "artifacts" / "supervision" / "consumer" / "unsupported_supervisor_action.json").exists()
    assert not (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "publication_gate_specificity_required.json"
    ).exists()
    assert not (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "return_to_ai_reviewer_workflow.json"
    ).exists()
    blocked_tasks = {
        task["action_type"]: task
        for task in result["request_tasks"]
        if task["action_type"] in {"publication_gate_specificity_required", "return_to_ai_reviewer_workflow"}
    }
    assert blocked_tasks["publication_gate_specificity_required"]["dispatch_status"] == "blocked"
    assert blocked_tasks["publication_gate_specificity_required"]["blocked_reason"] == "owner_route_next_owner_mismatch"
    assert blocked_tasks["return_to_ai_reviewer_workflow"]["dispatch_status"] == "blocked"
    assert blocked_tasks["return_to_ai_reviewer_workflow"]["blocked_reason"] == "owner_route_next_owner_mismatch"
    assert not (
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json"
    ).exists()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "manuscript").exists()


def test_materialize_domain_action_requests_does_not_repeat_suppress_pending_ai_reviewer_output(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    _disable_progress_projection(monkeypatch)
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dpcc")
    route = _owner_route(
        study_id=study_id,
        quest_id="quest-dpcc",
        next_owner="ai_reviewer",
        owner_reason="ai_reviewer_assessment_required",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )
    action = {
        "study_id": study_id,
        "quest_id": "quest-dpcc",
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
    }
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": route,
                    "meaningful_artifact_delta": False,
                    "ai_reviewer_assessment": {"present": False, "missing": True, "owner": "mechanical_projection"},
                }
            ],
            "action_queue": [action],
        },
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    _write_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": "quest-dpcc",
            "action_type": "return_to_ai_reviewer_workflow",
            "dispatch_status": "ready",
            "owner_route": route,
            "idempotency_key": route["idempotency_key"],
            "prompt_contract": {
                "do_not_repeat": True,
                "repeat_suppression_key": route["source_fingerprint"],
            },
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    dispatch = result["default_executor_dispatches"][0]
    assert dispatch["dispatch_status"] == "transition_request_pending"
    assert dispatch["repeat_suppressed"] is False
    assert dispatch["blocked_reason"] == "opl_execution_authorization_required"
    assert dispatch["provider_admission_pending"] is False
    assert dispatch["provider_admission_requires_opl_runtime_result"] is True
    assert dispatch["mas_local_dispatch_carrier_persistence"] == "forbidden"
    assert result["repeat_suppressed_count"] == 0
