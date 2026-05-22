from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import write_json as _write_json
from tests.study_runtime_test_helpers import make_profile, write_study


def test_refresh_controller_decision_uses_status_domain_transition_when_outer_tick_is_stale(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    outer_loop = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    publication_eval_ref = {
        "eval_id": "publication-eval::dm003::stale-write-route",
        "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
    }
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "eval_id": publication_eval_ref["eval_id"],
            "study_id": study_id,
            "quest_id": study_id,
            "assessment_provenance": {"owner": "ai_reviewer"},
        },
    )
    controller_decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    status_payload = {
        "study_id": study_id,
        "quest_id": study_id,
        "decision": "resume",
        "reason": "domain_transition_ai_reviewer_re_eval",
        "quest_status": "active",
        "domain_transition": {
            "decision_type": "ai_reviewer_re_eval",
            "controller_action": "return_to_ai_reviewer_workflow",
            "route_target": "review",
            "owner": "ai_reviewer",
            "next_work_unit": {
                "unit_id": "ai_reviewer_medical_prose_quality_review",
                "lane": "review",
                "summary": "Re-run AI reviewer manuscript-quality review after the canonical manuscript story repair.",
            },
        },
    }
    stale_tick_request = {
        "study_root": study_root,
        "charter_ref": {
            "charter_id": f"charter::{study_id}::v1",
            "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
        },
        "publication_eval_ref": publication_eval_ref,
        "decision_type": "route_back_same_line",
        "route_target": "write",
        "route_key_question": "Repair medical manuscript prose quality.",
        "route_rationale": "Old write route from the previous quality-repair batch.",
        "source_route_key_question": None,
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "run_quality_repair_batch",
                "payload_ref": str(controller_decision_path),
            }
        ],
        "reason": "Old write route from the previous quality-repair batch.",
        "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
        "next_work_unit": {"unit_id": "medical_prose_write_repair", "lane": "write"},
        "blocking_work_units": [{"unit_id": "medical_prose_write_repair", "lane": "write"}],
    }
    calls: dict[str, object] = {}

    monkeypatch.setattr(module.study_runtime_router, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: stale_tick_request)

    def fake_materialize_non_dispatching_outer_loop_decision(**kwargs: object) -> dict[str, object]:
        calls["materialize_kwargs"] = dict(kwargs)
        return {
            "dispatch_status": "recorded_non_dispatching",
            "study_decision_ref": {"artifact_path": str(controller_decision_path)},
        }

    monkeypatch.setattr(
        outer_loop,
        "materialize_non_dispatching_outer_loop_decision",
        fake_materialize_non_dispatching_outer_loop_decision,
    )

    result = module.refresh_controller_decisions_for_current_publication_eval(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    refresh = result["refreshes"][0]
    materialize_kwargs = calls["materialize_kwargs"]
    assert refresh["refresh_status"] == "materialized"
    assert materialize_kwargs["decision_type"] == "continue_same_line"
    assert materialize_kwargs["route_target"] == "review"
    assert materialize_kwargs["work_unit_fingerprint"] == (
        "domain-transition::ai_reviewer_re_eval::ai_reviewer_medical_prose_quality_review"
    )
    assert materialize_kwargs["next_work_unit"]["unit_id"] == "ai_reviewer_medical_prose_quality_review"
    assert materialize_kwargs["controller_actions"][0]["action_type"] == "return_to_ai_reviewer_workflow"


def test_refresh_controller_decision_does_not_bypass_human_gate_with_status_domain_transition(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    outer_loop = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    publication_eval_ref = {
        "eval_id": "publication-eval::dm003::human-gate",
        "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
    }
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "eval_id": publication_eval_ref["eval_id"],
            "study_id": study_id,
            "quest_id": study_id,
        },
    )
    controller_decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    status_payload = {
        "study_id": study_id,
        "quest_id": study_id,
        "decision": "blocked",
        "reason": "human_confirmation_required",
        "quest_status": "waiting_for_user",
        "publication_supervisor_state": {"current_required_action": "human_confirmation_required"},
        "domain_transition": {
            "decision_type": "ai_reviewer_re_eval",
            "controller_action": "return_to_ai_reviewer_workflow",
            "route_target": "review",
            "next_work_unit": {
                "unit_id": "ai_reviewer_medical_prose_quality_review",
                "lane": "review",
            },
        },
    }
    stale_tick_request = {
        "study_root": study_root,
        "charter_ref": {
            "charter_id": f"charter::{study_id}::v1",
            "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
        },
        "publication_eval_ref": publication_eval_ref,
        "decision_type": "route_back_same_line",
        "route_target": "write",
        "route_key_question": "Repair medical manuscript prose quality.",
        "route_rationale": "Old write route from the previous quality-repair batch.",
        "source_route_key_question": None,
        "requires_human_confirmation": False,
        "controller_actions": [{"action_type": "run_quality_repair_batch", "payload_ref": str(controller_decision_path)}],
        "reason": "Old write route from the previous quality-repair batch.",
        "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
        "next_work_unit": {"unit_id": "medical_prose_write_repair", "lane": "write"},
        "blocking_work_units": [{"unit_id": "medical_prose_write_repair", "lane": "write"}],
    }
    calls: dict[str, object] = {}

    monkeypatch.setattr(module.study_runtime_router, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: stale_tick_request)

    def fake_materialize_non_dispatching_outer_loop_decision(**kwargs: object) -> dict[str, object]:
        calls["materialize_kwargs"] = dict(kwargs)
        return {
            "dispatch_status": "recorded_non_dispatching",
            "study_decision_ref": {"artifact_path": str(controller_decision_path)},
        }

    monkeypatch.setattr(
        outer_loop,
        "materialize_non_dispatching_outer_loop_decision",
        fake_materialize_non_dispatching_outer_loop_decision,
    )

    result = module.refresh_controller_decisions_for_current_publication_eval(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["refreshes"][0]["refresh_status"] == "materialized"
    assert calls["materialize_kwargs"]["work_unit_fingerprint"] == (
        "domain-transition::route_back_same_line::medical_prose_write_repair"
    )
    assert calls["materialize_kwargs"]["controller_actions"][0]["action_type"] == "run_quality_repair_batch"
