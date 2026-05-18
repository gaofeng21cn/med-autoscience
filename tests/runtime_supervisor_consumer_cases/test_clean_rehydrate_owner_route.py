from __future__ import annotations

import importlib
import json
from pathlib import Path

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
        "surface": "runtime_supervisor_owner_route",
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


def test_supervisor_consume_routes_clean_canonical_rehydrate_to_write_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_consumer")
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
        profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json",
        {
            "surface": "portable_runtime_supervisor_scan",
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

    result = module.supervisor_consume(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    task = result["request_tasks"][0]
    dispatch = result["default_executor_dispatches"][0]
    packet_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "canonical_paper_inputs_rehydrate_required.json"
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "canonical_paper_inputs_rehydrate_required.json"
    )
    assert task["action_type"] == "canonical_paper_inputs_rehydrate_required"
    assert task["request_owner"] == "write"
    assert task["required_output_surface"] == "paper/medical_manuscript_blueprint_source.json"
    assert task["request_packet_ref"] == "artifacts/supervision/requests/canonical_paper_inputs_rehydrate/latest.json"
    assert dispatch["dispatch_status"] == "ready"
    assert dispatch["next_executable_owner"] == "write"
    assert dispatch["required_output_surface"] == "paper/medical_manuscript_blueprint_source.json"
    assert dispatch["prompt_contract"]["request_packet_ref"] == (
        "artifacts/supervision/requests/canonical_paper_inputs_rehydrate/latest.json"
    )
    assert packet_path.is_file()
    assert dispatch_path.is_file()
    assert not (study_root / "paper" / "medical_manuscript_blueprint.json").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_supervisor_consume_routes_hard_methodology_handoff_to_analysis_harmonization_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_consumer")
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
        profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json",
        {
            "surface": "portable_runtime_supervisor_scan",
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

    result = module.supervisor_consume(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    task = result["request_tasks"][0]
    dispatch = result["default_executor_dispatches"][0]
    packet_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "unit_harmonized_external_validation_rerun.json"
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "unit_harmonized_external_validation_rerun.json"
    )
    assert task["dispatch_status"] == "applied"
    assert task["request_owner"] == "analysis_harmonization_owner"
    assert task["request_packet_ref"] == "artifacts/supervision/requests/analysis_harmonization/latest.json"
    assert dispatch["dispatch_status"] == "ready"
    assert dispatch["next_executable_owner"] == "analysis_harmonization_owner"
    assert dispatch["prompt_contract"]["request_packet_ref"] == (
        "artifacts/supervision/requests/analysis_harmonization/latest.json"
    )
    assert dispatch["prompt_contract"]["quality_gate_relaxation_allowed"] is False
    assert packet_path.is_file()
    assert dispatch_path.is_file()
    assert not (study_root / "paper").exists()
    assert not (study_root / "manuscript").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_supervisor_consume_routes_model_provenance_handoff_to_source_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_consumer")
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
        profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json",
        {
            "surface": "portable_runtime_supervisor_scan",
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

    result = module.supervisor_consume(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    task = result["request_tasks"][0]
    dispatch = result["default_executor_dispatches"][0]
    packet_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "recover_transport_model_provenance.json"
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "recover_transport_model_provenance.json"
    )
    assert task["dispatch_status"] == "applied"
    assert task["request_owner"] == "source_provenance_owner"
    assert task["request_packet_ref"] == "artifacts/supervision/requests/source_provenance/latest.json"
    assert dispatch["dispatch_status"] == "ready"
    assert dispatch["next_executable_owner"] == "source_provenance_owner"
    assert dispatch["prompt_contract"]["request_packet_ref"] == (
        "artifacts/supervision/requests/source_provenance/latest.json"
    )
    assert dispatch["prompt_contract"]["quality_gate_relaxation_allowed"] is False
    assert packet_path.is_file()
    assert dispatch_path.is_file()
    assert not (study_root / "paper").exists()
    assert not (study_root / "manuscript").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_supervisor_consume_prefers_current_study_queue_over_stale_top_level_queue(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_consumer")
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
        profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json",
        {
            "surface": "portable_runtime_supervisor_scan",
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

    result = module.supervisor_consume(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    dispatch = result["default_executor_dispatches"][0]
    assert result["default_executor_dispatch_count"] == 1
    assert dispatch["action_type"] == "canonical_paper_inputs_rehydrate_required"
    assert dispatch["next_executable_owner"] == "write"
    assert dispatch["owner_route"]["next_owner"] == "write"
    assert dispatch["owner_route"]["work_unit_fingerprint"] == current_route["source_fingerprint"]
    assert dispatch["required_output_surface"].endswith("paper/medical_manuscript_blueprint_source.json")
    assert not (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    ).exists()
