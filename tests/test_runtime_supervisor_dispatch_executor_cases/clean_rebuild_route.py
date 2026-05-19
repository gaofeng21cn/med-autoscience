from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.runtime_supervisor_dispatch_executor_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_execute_dispatch_routes_authorized_terminal_source_blocker_to_clean_rebuild(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
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
            "task_id": "study-task::dm002::clean-rebuild",
            "task_intake_kind": "methodology_rebuild_authorization",
            "emitted_at": "2026-05-19T08:00:00+00:00",
            "task_intent": "Authorize a clean reproducible-model rebuild route after HDL unit failure.",
        },
    )
    route = _owner_route(
        study_id=study_id,
        action_type="methodology_reframe_route_decision",
        owner="decision",
    )
    route.update(
        {
            "failure_signature": "methodology_reframe_required",
            "owner_reason": "methodology_reframe_required",
            "work_unit_fingerprint": "decision::methodology_reframe_route_decision",
            "source_fingerprint": "truth-snapshot::terminal-source-provenance-blocker",
            "idempotency_key": "owner-route::dm002::decision::methodology-reframe-clean-rebuild",
        }
    )
    dispatch = _dispatch(
        study_id=study_id,
        action_type="methodology_reframe_route_decision",
        owner="decision",
        required_output_surface=(
            "controller route decision for a provenance-limited reframe, "
            "reproducible-model restart, stop-loss, or human gate"
        ),
        owner_route=route,
    )
    dispatch["source_action"] = {
        "action_type": "methodology_reframe_route_decision",
        "source_ref": "artifacts/controller/source_provenance/latest.json",
        "terminal_source_provenance_blocker": True,
        "blocked_reason": "methodology_reframe_required",
    }
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "methodology_reframe_route_decision.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch)

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("methodology_reframe_route_decision",),
        mode="developer_apply_safe",
        apply=True,
    )

    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    execution = result["executions"][0]
    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    assert execution["execution_status"] == "executed"
    assert execution["owner_result"]["selected_route_option"] == "rebuild_reproducible_model_route"
    assert execution["owner_result"]["selected_next_work_unit"]["unit_id"] == (
        "unit_harmonized_external_validation_rerun"
    )
    assert execution["owner_result"]["selected_next_work_unit"]["clean_reproducible_model_rebuild_authorized"] is True
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    assert decision["next_work_unit"]["unit_id"] == "unit_harmonized_external_validation_rerun"
    assert decision["next_work_unit"]["selected_route_option"] == "rebuild_reproducible_model_route"
    assert decision["next_work_unit"]["required_owner"] == "analysis_harmonization_owner"
    assert decision["next_work_unit"]["required_next_work_unit"] == "unit_harmonized_external_validation_rerun"
    assert decision["next_work_unit"]["typed_blocker"] == "unit_harmonized_rerun_required"
    assert decision["next_work_unit"]["terminal_source_provenance_blocker_consumed"] is True
    assert decision["next_work_unit"]["current_transport_claim_must_not_be_used_as_medical_conclusion"] is True
    assert not (study_root / "manuscript").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
