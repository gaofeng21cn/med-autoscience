from __future__ import annotations

import importlib
from pathlib import Path

from tests.runtime_supervisor_dispatch_executor_helpers import (
    dispatch as _dispatch,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_refresh_controller_decisions_for_current_publication_eval_materializes_non_dispatching_decision(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    outer_loop = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "eval_id": "publication-eval::current",
            "study_id": study_id,
            "quest_id": study_id,
            "assessment_provenance": {"owner": "ai_reviewer"},
            "verdict": {"overall_verdict": "blocked"},
        },
    )
    status_payload = {
        "study_id": study_id,
        "quest_id": study_id,
        "decision": "resume",
        "reason": "quest_drifting_into_write_without_gate_approval",
        "quest_status": "running",
        "control_plane_snapshot": {
            "dispatch_gate": {
                "state": "blocked",
                "dispatch_allowed": False,
                "blocking_reasons": ["execution_owner_guard.supervisor_only"],
            }
        },
    }
    tick_request = {
        "study_root": study_root,
        "charter_ref": {
            "charter_id": f"charter::{study_id}::v1",
            "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
        },
        "publication_eval_ref": {
            "eval_id": "publication-eval::current",
            "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        },
        "decision_type": "bounded_analysis",
        "route_target": "analysis-campaign",
        "route_key_question": "Which claim-evidence repair is still blocking the paper?",
        "route_rationale": "AI reviewer current eval blocks on claim-evidence consistency.",
        "source_route_key_question": None,
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "ensure_study_runtime",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        "reason": "AI reviewer current eval blocks on claim-evidence consistency.",
        "work_unit_fingerprint": "publication-blockers::current",
        "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        "blocking_work_units": [{"unit_id": "analysis_claim_evidence_repair"}],
    }
    calls: dict[str, object] = {}

    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", lambda **_: status_payload)
    monkeypatch.setattr(
        outer_loop,
        "build_runtime_watch_outer_loop_tick_request",
        lambda **kwargs: (calls.setdefault("tick_request_kwargs", kwargs), tick_request)[1],
    )

    def fake_materialize_non_dispatching_outer_loop_decision(**kwargs) -> dict[str, object]:
        calls["materialize_kwargs"] = kwargs
        return {
            "dispatch_status": "recorded_non_dispatching",
            "study_decision_ref": {
                "artifact_path": str(study_root / "artifacts" / "controller_decisions" / "latest.json")
            },
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

    assert result["surface"] == "runtime_supervisor_controller_decision_refresh"
    assert result["refresh_count"] == 1
    assert result["materialized_count"] == 1
    refresh = result["refreshes"][0]
    assert refresh["refresh_status"] == "materialized"
    assert refresh["dispatch_status"] == "recorded_non_dispatching"
    assert calls["tick_request_kwargs"] == {
        "study_root": study_root,
        "status_payload": status_payload,
    }
    assert calls["materialize_kwargs"]["profile"] == profile
    assert calls["materialize_kwargs"]["study_id"] == study_id
    assert calls["materialize_kwargs"]["study_root"] == study_root
    assert calls["materialize_kwargs"]["publication_eval_ref"] == tick_request["publication_eval_ref"]
    assert calls["materialize_kwargs"]["source"] == "runtime_supervisor_controller_decision_refresh"


def test_refresh_controller_decisions_for_current_publication_eval_dry_run_does_not_materialize(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    outer_loop = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    status_payload = {"study_id": study_id, "quest_id": study_id, "quest_status": "running"}
    tick_request = {
        "publication_eval_ref": {
            "eval_id": "publication-eval::current",
            "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        },
        "decision_type": "bounded_analysis",
        "reason": "AI reviewer current eval blocks on claim-evidence consistency.",
    }

    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", lambda **_: status_payload)
    monkeypatch.setattr(outer_loop, "build_runtime_watch_outer_loop_tick_request", lambda **_: tick_request)
    monkeypatch.setattr(
        outer_loop,
        "materialize_non_dispatching_outer_loop_decision",
        lambda **_: (_ for _ in ()).throw(AssertionError("dry run must not materialize controller decision")),
    )

    result = module.refresh_controller_decisions_for_current_publication_eval(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["dry_run"] is True
    assert result["materialized_count"] == 0
    assert result["refreshes"][0]["refresh_status"] == "dry_run"
    assert result["refreshes"][0]["publication_eval_ref"]["eval_id"] == "publication-eval::current"


def test_execute_dispatch_refreshes_controller_decision_after_ai_reviewer_materializes_eval(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    outer_loop = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    input_refs = {
        "manuscript": {"path": str(study_root / "paper" / "draft.md"), "present": True, "valid": True},
        "evidence_ledger": {"path": str(study_root / "paper" / "evidence_ledger.json"), "present": True, "valid": True},
        "review_ledger": {
            "path": str(study_root / "paper" / "review" / "review_ledger.json"),
            "present": True,
            "valid": True,
        },
        "study_charter": {
            "path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
            "present": True,
            "valid": True,
        },
        "medical_manuscript_blueprint": {
            "path": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
            "present": True,
            "valid": True,
        },
        "claim_evidence_map": {
            "path": str(study_root / "paper" / "claim_evidence_map.json"),
            "present": True,
            "valid": True,
        },
        "medical_prose_review": {
            "path": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
            "present": True,
            "valid": True,
        },
        "publication_gate_projection": {
            "path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            "present": True,
            "valid": True,
        },
    }
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "supervisor_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "input_contract": {
                "required_refs": input_refs,
                "all_required_refs_present": True,
                "missing_or_invalid_refs": [],
            },
            "ai_reviewer_record": {
                "eval_id": "publication-eval::stale",
                "study_id": study_id,
                "quest_id": f"quest-{study_id}",
            },
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
    dispatch = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
    )
    _write_current_dispatch(dispatch_path, profile, dispatch)

    def fake_run_ai_reviewer_publication_eval_workflow(**_: object) -> dict[str, object]:
        _write_json(
            study_root / "artifacts" / "publication_eval" / "latest.json",
            {
                "eval_id": "publication-eval::current",
                "study_id": study_id,
                "quest_id": f"quest-{study_id}",
                "assessment_provenance": {"owner": "ai_reviewer"},
            },
        )
        return {
            "surface": "ai_reviewer_publication_eval_workflow",
            "status": "materialized",
            "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            "eval_id": "publication-eval::current",
        }

    status_payload = {
        "study_id": study_id,
        "quest_id": f"quest-{study_id}",
        "decision": "resume",
        "reason": "runtime_active",
        "quest_status": "running",
    }
    tick_request = {
        "study_root": study_root,
        "charter_ref": {
            "charter_id": f"charter::{study_id}::v1",
            "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
        },
        "publication_eval_ref": {
            "eval_id": "publication-eval::current",
            "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        },
        "decision_type": "continue_same_line",
        "route_target": "write",
        "route_key_question": "What manuscript repair should run next?",
        "route_rationale": "AI reviewer refreshed the current publication blockers.",
        "source_route_key_question": None,
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "ensure_study_runtime",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        "reason": "AI reviewer refreshed the current publication blockers.",
        "work_unit_fingerprint": "work-unit::current",
        "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        "blocking_work_units": [{"unit_id": "analysis_claim_evidence_repair"}],
    }
    refresh_called: dict[str, object] = {}

    monkeypatch.setattr(
        module.ai_reviewer_publication_eval_workflow,
        "run_ai_reviewer_publication_eval_workflow",
        fake_run_ai_reviewer_publication_eval_workflow,
    )
    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", lambda **_: status_payload)
    monkeypatch.setattr(
        outer_loop,
        "build_runtime_watch_outer_loop_tick_request",
        lambda **kwargs: (refresh_called.setdefault("tick_request_kwargs", kwargs), tick_request)[1],
    )

    def fake_materialize_non_dispatching_outer_loop_decision(**kwargs) -> dict[str, object]:
        refresh_called["materialize_kwargs"] = kwargs
        return {
            "dispatch_status": "recorded_non_dispatching",
            "study_decision_ref": {
                "artifact_path": str(study_root / "artifacts" / "controller_decisions" / "latest.json")
            },
        }

    monkeypatch.setattr(
        outer_loop,
        "materialize_non_dispatching_outer_loop_decision",
        fake_materialize_non_dispatching_outer_loop_decision,
    )

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "executed"
    refresh = execution["owner_result"]["controller_decision_refresh"]
    assert refresh["refresh_status"] == "materialized"
    assert refresh["dispatch_status"] == "recorded_non_dispatching"
    assert refresh_called["tick_request_kwargs"] == {
        "study_root": study_root,
        "status_payload": status_payload,
    }
    assert refresh_called["materialize_kwargs"]["profile"] == profile
    assert refresh_called["materialize_kwargs"]["study_id"] == study_id
    assert refresh_called["materialize_kwargs"]["study_root"] == study_root
    assert refresh_called["materialize_kwargs"]["status_payload"] == status_payload
    assert refresh_called["materialize_kwargs"]["publication_eval_ref"] == tick_request["publication_eval_ref"]
    assert refresh_called["materialize_kwargs"]["next_work_unit"] == tick_request["next_work_unit"]
    assert refresh_called["materialize_kwargs"]["blocking_work_units"] == tick_request["blocking_work_units"]
    assert refresh_called["materialize_kwargs"]["source"] == "ai_reviewer_publication_eval_workflow"
