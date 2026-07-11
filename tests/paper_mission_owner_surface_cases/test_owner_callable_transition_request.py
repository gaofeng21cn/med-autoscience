from __future__ import annotations

import importlib


def _profile(tmp_path):
    profiles = importlib.import_module("med_autoscience.profiles")
    workspace_root = tmp_path / "workspace"
    return profiles.WorkspaceProfile(
        name="test",
        workspace_root=workspace_root,
        runtime_root=workspace_root / "runtime",
        studies_root=workspace_root / "studies",
        portfolio_root=workspace_root / "portfolio",
        med_deepscientist_runtime_root=workspace_root / "legacy-runtime",
        med_deepscientist_repo_root=None,
        default_publication_profile="default",
        default_citation_style="vancouver",
        research_route_bias_policy="none",
        preferred_study_archetypes=(),
        default_submission_targets=(),
    )


def test_ai_reviewer_handoff_exposes_only_opl_transition_request_for_runtime(tmp_path) -> None:
    production = importlib.import_module(
        "med_autoscience.controllers.stage_outcome_authority.action_execution.ai_reviewer_record_production"
    )

    handoff = production.build_ai_reviewer_record_worker_handoff(
        profile=_profile(tmp_path),
        study_id="study-1",
        request={"study_id": "study-1", "quest_id": "quest-1"},
        dispatch={
            "owner_route": {
                "study_id": "study-1",
                "quest_id": "quest-1",
                "truth_epoch": "truth-1",
                "runtime_health_epoch": "runtime-1",
                "source_fingerprint": "source-1",
                "work_unit_fingerprint": "work-unit-1",
                "next_owner": "ai_reviewer",
                "owner_reason": "ai_reviewer_request_pending",
                "allowed_actions": ["return_to_ai_reviewer_workflow"],
                "idempotency_key": "owner-route-1",
                "source_refs": {
                    "source_eval_id": "eval-1",
                    "work_unit_id": "review-current-record",
                    "work_unit_fingerprint": "work-unit-1",
                    "study_truth_epoch": "truth-1",
                    "runtime_health_epoch": "runtime-1",
                },
            }
        },
        production_request={"request_kind": "refresh_current_record"},
    )

    transition_request = handoff["opl_domain_progress_transition_request"]
    assert transition_request["surface_kind"] == "mas_domain_progress_transition_request"
    assert transition_request["target_runtime_kind"] == "DomainProgressTransitionRuntime"
    assert transition_request["target_runtime_owner"] == "one-person-lab"
    assert handoff["provider_admission_requires_opl_runtime_result"] is True
    assert "owner_route_attempt_envelope" not in handoff
