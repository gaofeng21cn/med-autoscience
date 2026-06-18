from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.domain_action_request_materializer_cases.shared import legacy_request_task_refs as _legacy_request_task_refs

from tests.study_runtime_test_helpers import make_profile, write_study


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
    return {
        "surface": "domain_route_owner_route",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "route_epoch": f"truth-epoch::{study_id}",
        "source_fingerprint": f"truth-source::{study_id}::{owner_reason}",
        "current_owner": "mas_controller",
        "next_owner": next_owner,
        "owner_reason": owner_reason,
        "active_run_id": None,
        "allowed_actions": allowed_actions,
        "blocked_actions": [],
        "idempotency_key": f"owner-route::{study_id}::{owner_reason}",
    }


def test_materialize_domain_action_requests_routes_clean_canonical_rehydrate_to_write_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    monkeypatch.setenv("OPL_STATE_DIR", str(tmp_path / "opl-state"))
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm002")
    route = _owner_route(
        study_id=study_id,
        quest_id="quest-dm002",
        next_owner="write",
        owner_reason="canonical_paper_inputs_rehydrate_required",
        allowed_actions=["canonical_paper_inputs_rehydrate_required"],
    )
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "owner_route": route}],
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": "quest-dm002",
                    "action_type": "canonical_paper_inputs_rehydrate_required",
                    "authority": "observability_only",
                    "owner": "write",
                    "recommended_owner": "write",
                    "reason": "canonical_paper_inputs_rehydrate_required",
                    "required_output_surface": "paper/medical_manuscript_blueprint_source.json",
                    "owner_route": route,
                    "handoff_packet": {
                        "request_kind": "canonical_paper_inputs_rehydrate_required",
                        "authority": "observability_only",
                        "request_owner": "write",
                        "owner_route": route,
                        "paper_package_mutation_allowed": False,
                        "quality_gate_relaxation_allowed": False,
                    },
                    "legacy_artifact_reader_allowed": False,
                    "mechanical_blueprint_as_canonical_allowed": False,
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

    task = _legacy_request_task_refs(result)[0]
    dispatch = result["domain_progress_transition_requests"][0]
    packet_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "requests"
        / "canonical_paper_inputs_rehydrate"
        / "latest.json"
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / "canonical_paper_inputs_rehydrate_required.json"
    )
    assert task["action_type"] == "canonical_paper_inputs_rehydrate_required"
    assert task["request_owner"] == "write"
    assert task["required_output_surface"] == "paper/medical_manuscript_blueprint_source.json"
    assert task["request_packet_ref"] == "artifacts/supervision/requests/canonical_paper_inputs_rehydrate/latest.json"
    assert dispatch["dispatch_status"] == "transition_request_pending"
    assert dispatch["next_executable_owner"] == "write"
    assert dispatch["required_output_surface"] == "paper/medical_manuscript_blueprint_source.json"
    assert dispatch["prompt_contract_ref"]["request_packet_ref"] == (
        "artifacts/supervision/requests/canonical_paper_inputs_rehydrate/latest.json"
    )
    assert not packet_path.exists()
    assert not dispatch_path.exists()
    assert not (study_root / "paper" / "medical_manuscript_blueprint.json").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_materialize_domain_action_requests_routes_hard_methodology_handoff_to_analysis_harmonization_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    monkeypatch.setenv("OPL_STATE_DIR", str(tmp_path / "opl-state"))
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm002")
    route = _owner_route(
        study_id=study_id,
        quest_id="quest-dm002",
        next_owner="analysis_harmonization_owner",
        owner_reason="unit_harmonized_rerun_required",
        allowed_actions=["unit_harmonized_external_validation_rerun"],
    )
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "owner_route": route}],
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": "quest-dm002",
                    "action_type": "unit_harmonized_external_validation_rerun",
                    "authority": "observability_only",
                    "owner": "analysis_harmonization_owner",
                    "recommended_owner": "analysis_harmonization_owner",
                    "reason": "unit_harmonized_rerun_required",
                    "required_output_surface": (
                        "unit-harmonized external-validation rerun evidence or "
                        "typed blocker:unit_harmonized_rerun_required"
                    ),
                    "owner_route": route,
                    "quality_gate_relaxation_allowed": False,
                    "current_package_write_allowed": False,
                    "handoff_packet": {
                        "request_kind": "unit_harmonized_external_validation_rerun",
                        "authority": "observability_only",
                        "request_owner": "analysis_harmonization_owner",
                        "owner_route": route,
                        "paper_package_mutation_allowed": False,
                        "quality_gate_relaxation_allowed": False,
                        "medical_claim_authoring_allowed": False,
                    },
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

    task = _legacy_request_task_refs(result)[0]
    dispatch = result["domain_progress_transition_requests"][0]
    packet_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "requests"
        / "analysis_harmonization"
        / "latest.json"
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / "unit_harmonized_external_validation_rerun.json"
    )
    assert task["dispatch_status"] == "transition_request_pending"
    assert task["request_owner"] == "analysis_harmonization_owner"
    assert task["request_packet_ref"] == "artifacts/supervision/requests/analysis_harmonization/latest.json"
    assert dispatch["dispatch_status"] == "transition_request_pending"
    assert dispatch["next_executable_owner"] == "analysis_harmonization_owner"
    assert dispatch["prompt_contract_ref"]["request_packet_ref"] == (
        "artifacts/supervision/requests/analysis_harmonization/latest.json"
    )
    assert dispatch["prompt_contract_ref"]["quality_gate_relaxation_allowed"] is False
    assert not packet_path.exists()
    assert not dispatch_path.exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "manuscript").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_materialize_domain_action_requests_routes_model_provenance_handoff_to_source_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    monkeypatch.setenv("OPL_STATE_DIR", str(tmp_path / "opl-state"))
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm002")
    route = _owner_route(
        study_id=study_id,
        quest_id="quest-dm002",
        next_owner="source_provenance_owner",
        owner_reason="transport_model_provenance_recovery_required",
        allowed_actions=["recover_transport_model_provenance"],
    )
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "owner_route": route}],
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": "quest-dm002",
                    "action_type": "recover_transport_model_provenance",
                    "authority": "observability_only",
                    "owner": "source_provenance_owner",
                    "recommended_owner": "source_provenance_owner",
                    "reason": "transport_model_provenance_recovery_required",
                    "required_output_surface": (
                        "canonical transport model provenance bundle or "
                        "typed blocker:transport_model_provenance_recovery_required"
                    ),
                    "owner_route": route,
                    "quality_gate_relaxation_allowed": False,
                    "current_package_write_allowed": False,
                    "handoff_packet": {
                        "request_kind": "recover_transport_model_provenance",
                        "authority": "observability_only",
                        "request_owner": "source_provenance_owner",
                        "owner_route": route,
                        "paper_package_mutation_allowed": False,
                        "quality_gate_relaxation_allowed": False,
                        "medical_claim_authoring_allowed": False,
                    },
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

    task = _legacy_request_task_refs(result)[0]
    dispatch = result["domain_progress_transition_requests"][0]
    packet_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "requests"
        / "source_provenance"
        / "latest.json"
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / "recover_transport_model_provenance.json"
    )
    assert task["dispatch_status"] == "transition_request_pending"
    assert task["request_owner"] == "source_provenance_owner"
    assert task["request_packet_ref"] == "artifacts/supervision/requests/source_provenance/latest.json"
    assert dispatch["dispatch_status"] == "transition_request_pending"
    assert dispatch["next_executable_owner"] == "source_provenance_owner"
    assert dispatch["prompt_contract_ref"]["request_packet_ref"] == (
        "artifacts/supervision/requests/source_provenance/latest.json"
    )
    assert dispatch["prompt_contract_ref"]["quality_gate_relaxation_allowed"] is False
    assert not packet_path.exists()
    assert not dispatch_path.exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "manuscript").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_materialize_domain_action_requests_routes_methodology_reframe_to_decision_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    monkeypatch.setenv("OPL_STATE_DIR", str(tmp_path / "opl-state"))
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm002")
    route = _owner_route(
        study_id=study_id,
        quest_id="quest-dm002",
        next_owner="decision",
        owner_reason="methodology_reframe_required",
        allowed_actions=["methodology_reframe_route_decision"],
    )
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "owner_route": route}],
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": "quest-dm002",
                    "action_type": "methodology_reframe_route_decision",
                    "authority": "observability_only",
                    "owner": "decision",
                    "recommended_owner": "decision",
                    "reason": "methodology_reframe_required",
                    "required_output_surface": (
                        "controller route decision for a provenance-limited reframe, reproducible-model restart, "
                        "stop-loss, or human gate"
                    ),
                    "owner_route": route,
                    "terminal_source_blocker": {
                        "blocked_reason": "methodology_reframe_required",
                        "source_blocked_reason": "transport_model_provenance_recovery_required",
                        "next_owner": "decision",
                        "terminal_source_provenance_blocker": True,
                    },
                    "handoff_packet": {
                        "request_kind": "methodology_reframe_route_decision",
                        "authority": "observability_only",
                        "request_owner": "decision",
                        "owner_route": route,
                        "paper_package_mutation_allowed": False,
                        "quality_gate_relaxation_allowed": False,
                        "medical_claim_authoring_allowed": False,
                    },
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

    task = _legacy_request_task_refs(result)[0]
    dispatch = result["domain_progress_transition_requests"][0]
    packet_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "requests"
        / "decision"
        / "latest.json"
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / "methodology_reframe_route_decision.json"
    )
    assert task["dispatch_status"] == "transition_request_pending"
    assert task["request_owner"] == "decision"
    assert task["request_packet_ref"] == "artifacts/supervision/requests/decision/latest.json"
    assert dispatch["dispatch_status"] == "transition_request_pending"
    assert dispatch["next_executable_owner"] == "decision"
    assert dispatch["prompt_contract_ref"]["request_packet_ref"] == "artifacts/supervision/requests/decision/latest.json"
    assert dispatch["prompt_contract_ref"]["quality_gate_relaxation_allowed"] is False
    assert not packet_path.exists()
    assert not dispatch_path.exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "manuscript").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_materialize_domain_action_requests_prefers_current_study_queue_over_stale_top_level_queue(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    monkeypatch.setenv("OPL_STATE_DIR", str(tmp_path / "opl-state"))
    profile = make_profile(tmp_path)
    study_id = "004-dpcc-longitudinal-care-inertia-intensification-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    stale_route = _owner_route(
        study_id=study_id,
        quest_id=study_id,
        next_owner="ai_reviewer",
        owner_reason="paper_authority_clean_migration_required",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )
    current_route = _owner_route(
        study_id=study_id,
        quest_id=study_id,
        next_owner="write",
        owner_reason="canonical_paper_inputs_rehydrate_required",
        allowed_actions=["canonical_paper_inputs_rehydrate_required"],
    )
    current_route["source_fingerprint"] = "truth-source::current-write-rehydrate"
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "authority": "observability_only",
                    "owner": "ai_reviewer",
                    "recommended_owner": "ai_reviewer",
                    "reason": "paper_authority_clean_migration_required",
                    "required_output_surface": "artifacts/publication_eval/latest.json",
                    "owner_route": stale_route,
                }
            ],
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner_route": current_route,
                    "action_queue": [
                        {
                            "action_type": "canonical_paper_inputs_rehydrate_required",
                            "authority": "observability_only",
                            "owner": "write",
                            "recommended_owner": "write",
                            "reason": "canonical_paper_inputs_rehydrate_required",
                            "required_output_surface": str(
                                study_root / "paper" / "medical_manuscript_blueprint_source.json"
                            ),
                            "owner_route": current_route,
                            "legacy_artifact_reader_allowed": False,
                            "mechanical_blueprint_as_canonical_allowed": False,
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

    dispatch = result["domain_progress_transition_requests"][0]
    assert result["domain_progress_transition_request_count"] == 1
    assert dispatch["action_type"] == "canonical_paper_inputs_rehydrate_required"
    assert dispatch["next_executable_owner"] == "write"
    assert dispatch["owner_route_ref"]["next_owner"] == "write"
    assert dispatch["owner_route_ref"]["work_unit_fingerprint"] == current_route["source_fingerprint"]
    assert dispatch["required_output_surface"].endswith("paper/medical_manuscript_blueprint_source.json")
    assert not (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / "return_to_ai_reviewer_workflow.json"
    ).exists()


def test_materialize_domain_action_requests_rejects_stale_top_level_queue_when_executable_envelope_current(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    monkeypatch.setenv("OPL_STATE_DIR", str(tmp_path / "opl-state"))
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = "quest-dm002"
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    stale_route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="decision",
        owner_reason="methodology_reframe_route_decision",
        allowed_actions=["methodology_reframe_route_decision"],
    )
    current_route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="analysis_harmonization_owner",
        owner_reason="unit_harmonized_rerun_required",
        allowed_actions=["unit_harmonized_external_validation_rerun"],
    )
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "action_type": "methodology_reframe_route_decision",
                    "authority": "observability_only",
                    "owner": "decision",
                    "recommended_owner": "decision",
                    "reason": "methodology_reframe_route_decision",
                    "required_output_surface": "controller route decision for a provenance-limited reframe",
                    "owner_route": stale_route,
                }
            ],
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "owner_route": current_route,
                    "current_execution_envelope": {
                        "state_kind": "executable_owner_action",
                        "owner": "analysis_harmonization_owner",
                        "next_work_unit": "unit_harmonized_external_validation_rerun",
                        "typed_blocker": None,
                    },
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

    ignored = result["ignored_actions"]
    assert result["domain_progress_transition_request_count"] == 0
    assert _legacy_request_task_refs(result) == []
    assert ignored[0]["action_type"] == "methodology_reframe_route_decision"
    assert ignored[0]["reason"] == "superseded_by_current_execution_envelope"
    assert not (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / "methodology_reframe_route_decision.json"
    ).exists()
