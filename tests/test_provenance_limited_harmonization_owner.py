from __future__ import annotations

import importlib
import json
from pathlib import Path
import os

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _set_mtime(path: Path, timestamp: int) -> None:
    os.utime(path, (timestamp, timestamp))


def test_human_gate_rebuild_authorization_routes_to_analysis_harmonization_owner(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.provenance_limited_harmonization_owner")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    _write_json(
        decision_path,
        {
            "schema_version": 1,
            "decision_id": "study-decision::dm002::methodology-reframe",
            "study_id": study_id,
            "quest_id": study_id,
            "decision_type": "bounded_analysis",
            "requires_human_confirmation": False,
            "work_unit_fingerprint": "decision::methodology_reframe_route_decision",
            "next_work_unit": {
                "unit_id": "provenance_limited_harmonization_audit",
                "selected_route_option": "provenance_limited_harmonization_audit",
                "terminal_source_provenance_blocker_consumed": True,
                "current_transport_claim_must_not_be_used_as_medical_conclusion": True,
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "source_provenance" / "latest.json",
        {
            "surface": "source_provenance_owner_result",
            "schema_version": 1,
            "study_id": study_id,
            "owner": "source_provenance_owner",
            "work_unit": "recover_transport_model_provenance",
            "status": "blocked",
            "blocked_reason": "transport_model_provenance_recovery_required",
            "typed_blocker_owner": "source_provenance_owner",
            "typed_blocker": {"blocker_id": "transport_model_provenance_recovery_required"},
            "transport_model_provenance_recovered": False,
            "provenance_search": {
                "searched": True,
                "accepted_bundle_ref": None,
                "result_summary_acceptance_allowed": False,
                "substitute_refit_allowed": False,
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "task_intake" / "latest.json",
        {
            "task_id": "study-task::dm002::rebuild",
            "task_intake_kind": "methodology_rebuild_authorization",
            "emitted_at": "2026-05-19T07:40:54+00:00",
            "task_intent": "Authorize a clean reproducible-model rebuild route after HDL unit failure.",
        },
    )

    result = module.provenance_limited_harmonization_audit_or_typed_blocker(
        profile=profile,
        study_id=study_id,
        dispatch=None,
        request=None,
        apply=True,
    )

    owner_result = result["owner_result"]
    assert owner_result["status"] == "blocked"
    assert owner_result["blocked_reason"] == "unit_harmonized_rerun_required"
    assert owner_result["typed_blocker"]["blocker_id"] == "unit_harmonized_rerun_required"
    assert owner_result["recommended_next_route"] == "rebuild_reproducible_model_route"
    assert owner_result["next_owner"] == "analysis_harmonization_owner"
    assert owner_result["next_work_unit"] == "unit_harmonized_external_validation_rerun"
    assert owner_result["rebuild_authorization_consumed"] is True
    assert owner_result["rebuild_authorization"]["task_intake_kind"] == "methodology_rebuild_authorization"
    assert owner_result["current_transport_claim_must_not_be_used_as_medical_conclusion"] is True
    assert owner_result["paper_package_mutation_allowed"] is False
    assert not (study_root / "paper").exists()
    assert not (study_root / "manuscript").exists()


def test_later_rebuild_authorization_invalidates_prior_human_gate_blocker(
    tmp_path: Path,
) -> None:
    result_module = importlib.import_module(
        "med_autoscience.controllers.provenance_limited_harmonization_owner_result"
    )
    study_root = tmp_path / "studies" / "002-dm"
    _write_json(
        study_root / "artifacts" / "controller" / "provenance_limited_harmonization" / "latest.json",
        {
            "surface": "provenance_limited_harmonization_owner_result",
            "schema_version": 1,
            "generated_at": "2026-05-19T07:30:00+00:00",
            "study_id": "002-dm",
            "owner": "provenance_limited_harmonization_owner",
            "work_unit": "provenance_limited_harmonization_audit",
            "status": "blocked",
            "blocked_reason": "rebuild_reproducible_model_route_required",
            "typed_blocker_owner": "provenance_limited_harmonization_owner",
            "typed_blocker": {"blocker_id": "rebuild_reproducible_model_route_required"},
            "provenance_limited_audit_completed": True,
            "next_owner": "human_gate",
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "task_intake" / "latest.json",
        {
            "task_id": "study-task::dm002::rebuild",
            "task_intake_kind": "methodology_rebuild_authorization",
            "emitted_at": "2026-05-19T07:40:54+00:00",
            "task_intent": "Authorize a clean reproducible-model rebuild route.",
        },
    )

    assert result_module.required_output_satisfied(study_root=study_root) is False
    assert result_module.typed_blocker_state(study_root=study_root) is None


def test_clean_rebuild_authorization_invalidates_current_audit_controller_decision(
    tmp_path: Path,
) -> None:
    result_module = importlib.import_module(
        "med_autoscience.controllers.provenance_limited_harmonization_owner_result"
    )
    study_root = tmp_path / "studies" / "002-dm"
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    _write_json(
        decision_path,
        {
            "schema_version": 1,
            "decision_id": "study-decision::dm002::audit-route",
            "study_id": "002-dm",
            "quest_id": "002-dm",
            "decision_type": "bounded_analysis",
            "work_unit_fingerprint": "decision::methodology_reframe_route_decision",
            "next_work_unit": {
                "unit_id": "provenance_limited_harmonization_audit",
                "selected_route_option": "provenance_limited_harmonization_audit",
                "terminal_source_provenance_blocker_consumed": True,
                "current_transport_claim_must_not_be_used_as_medical_conclusion": True,
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "source_provenance" / "latest.json",
        {
            "surface": "source_provenance_owner_result",
            "schema_version": 1,
            "study_id": "002-dm",
            "owner": "source_provenance_owner",
            "work_unit": "recover_transport_model_provenance",
            "status": "blocked",
            "blocked_reason": "transport_model_provenance_recovery_required",
            "typed_blocker_owner": "source_provenance_owner",
            "typed_blocker": {"blocker_id": "transport_model_provenance_recovery_required"},
            "transport_model_provenance_recovered": False,
            "provenance_search": {
                "searched": True,
                "accepted_bundle_ref": None,
                "result_summary_acceptance_allowed": False,
                "substitute_refit_allowed": False,
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "task_intake" / "latest.json",
        {
            "task_id": "study-task::dm002::rebuild",
            "task_intake_kind": "methodology_rebuild_authorization",
            "emitted_at": "2026-05-19T07:40:54+00:00",
            "task_intent": "Authorize a clean reproducible-model rebuild route.",
        },
    )
    _set_mtime(study_root / "artifacts" / "controller" / "source_provenance" / "latest.json", 2_000)
    _set_mtime(study_root / "artifacts" / "controller" / "task_intake" / "latest.json", 3_000)
    _set_mtime(decision_path, 4_000)

    assert result_module.current_controller_decision_requests_audit(study_root=study_root) is False
