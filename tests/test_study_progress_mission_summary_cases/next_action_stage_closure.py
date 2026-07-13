from __future__ import annotations

import importlib
import json

import pytest

from med_autoscience.controllers.next_action_envelope import SURFACE_KIND


def test_top_level_next_legal_action_prefers_canonical_runtime_readback_request() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress.mission_summary"
    )

    payload = module.refresh_top_level_stage_closure_projection(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "next_action": {
                "surface_kind": "mas_next_action_envelope",
                "action_id": "next-action::dm002::runtime-route",
                "action_family": "runtime.opl_route",
                "action_kind": "submit_to_opl_runtime",
                "owner": "one-person-lab",
                "executor_target": "opl_domain_progress_transition_runtime",
            },
            "stage_closure_decision": {
                "projection_status": "terminalizer_outcome_observed",
                "decision_ref": "stage-closure::dm002",
                "outcome": {
                    "kind": "typed_blocker",
                    "blocker_type": "route_back_checkpoint_without_semantic_delta",
                    "next_action": "materialize_typed_blocker_or_route_redesign",
                    "known_blockers": ["paper_mission_stage_route_domain_gate_pending"],
                },
                "known_blockers": ["paper_mission_stage_route_domain_gate_pending"],
            },
        }
    )

    assert payload["next_action"]["action_family"] == "runtime.opl_route"
    assert payload["stage_closure"]["next_legal_action"] == (
        "materialize_typed_blocker_or_route_redesign"
    )
    assert payload["next_legal_action"] == "codex_select_any_declared_stage"


def test_single_next_action_projection_does_not_accept_program_domain_transition_override() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress.projection_payload_assembly"
    )

    payload = module._attach_nonbinding_codex_route_context(
        {
            "study_id": "obesity_multicenter_phenotype_atlas",
            "next_action": {
                "surface_kind": SURFACE_KIND,
                "action_id": "next-action::obesity::old-submission-route",
                "action_family": "runtime.opl_route",
                "action_kind": "submit_to_opl_runtime",
                "owner": "one-person-lab",
                "work_unit_id": "submission_milestone_candidate",
            },
            "canonical_next_action_source": "paper_mission_next_action_envelope",
            "domain_transition": {
                "decision_type": "ai_reviewer_re_eval",
                "route_target": "review",
                "owner": "ai_reviewer",
                "next_work_unit": {
                    "unit_id": "ai_reviewer_medical_prose_quality_review",
                    "lane": "review",
                },
                "next_action": {
                    "surface_kind": SURFACE_KIND,
                    "action_id": "next-action::obesity::ai-reviewer",
                    "action_family": "paper.review.ai_reviewer",
                    "action_kind": "owner_review",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "owner": "ai_reviewer",
                    "executor_target": "mas_owner_callable",
                    "work_unit_id": "ai_reviewer_medical_prose_quality_review",
                    "expected_output_contract": {
                        "output_kind": "ai_reviewer_publication_eval_record"
                    },
                },
            },
            "user_visible_projection": {
                "next_owner": "one-person-lab",
                "conditions": [
                    {"type": "next_owner", "status": "true", "message": "one-person-lab"}
                ],
            },
        }
    )

    assert "canonical_next_action_source" not in payload
    assert payload["next_action_projection_role"] == "nonbinding_codex_route_context"
    assert payload["next_action"]["action_family"] == "runtime.opl_route"
    assert payload["next_action"]["owner"] == "one-person-lab"
    assert payload["next_action"]["work_unit_id"] == "submission_milestone_candidate"
    assert payload["user_visible_projection"]["next_owner"] == "one-person-lab"
    assert payload["user_visible_projection"]["conditions"][0]["message"] == "one-person-lab"


def test_typed_blocker_successor_does_not_override_domain_transition_reviewer_action(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress.projection_payload_assembly.typed_blocker_resolution_successor"
    )
    monkeypatch.setattr(
        module,
        "latest_typed_blocker_resolution_readback",
        lambda **_: {
            "source_ref": "/tmp/old-typed-blocker-resolution.json",
            "next_owner_action": {
                "study_id": "obesity_multicenter_phenotype_atlas",
                "next_owner": "mas_authority_kernel",
                "action_type": "classify_quality_blockers_or_materialize_degraded_handoff_gate",
                "allowed_actions": [
                    "classify_quality_blockers_or_materialize_degraded_handoff_gate"
                ],
                "work_unit_id": "submission_blocker_degraded_handoff_or_quality_repair",
                "work_unit_fingerprint": "old-submission-blocker",
            },
        },
    )
    profile = type("Profile", (), {"workspace_root": "/tmp/obesity-workspace"})()
    ai_reviewer_next_action = {
        "surface_kind": SURFACE_KIND,
        "action_id": "next-action::obesity::ai-reviewer",
        "action_family": "paper.review.ai_reviewer",
        "action_kind": "owner_review",
        "action_type": "return_to_ai_reviewer_workflow",
        "owner": "ai_reviewer",
        "executor_target": "mas_owner_callable",
        "work_unit_id": "ai_reviewer_medical_prose_quality_review",
    }

    payload = module.attach_typed_blocker_resolution_successor_projection(
        payload={
            "study_id": "obesity_multicenter_phenotype_atlas",
            "next_action": ai_reviewer_next_action,
            "canonical_next_action_source": "domain_transition.next_action",
            "domain_transition": {
                "decision_type": "ai_reviewer_re_eval",
                "owner": "ai_reviewer",
                "next_action": ai_reviewer_next_action,
            },
        },
        profile=profile,
        study_id="obesity_multicenter_phenotype_atlas",
    )

    assert payload["canonical_next_action_source"] == "domain_transition.next_action"
    assert payload["next_action"] == ai_reviewer_next_action
    assert "typed_blocker_resolution_readback" not in payload


def test_new_reviewer_revision_intake_retire_stale_typed_blocker_resolution(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress.projection_payload_assembly.typed_blocker_resolution_successor"
    )
    study_id = "obesity_multicenter_phenotype_atlas"
    workspace_root = tmp_path / "workspace"
    task_root = workspace_root / "studies" / study_id / "artifacts" / "controller" / "task_intake"
    task_root.mkdir(parents=True)
    (task_root / "latest.json").write_text(
        json.dumps(
            {
                "study_id": study_id,
                "task_intake_kind": "reviewer_revision",
                "emitted_at": "2026-07-02T10:38:00+00:00",
                "task_intent": "根据用户反馈继续 manuscript revision。",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        module,
        "latest_typed_blocker_resolution_readback",
        lambda **_: {
            "recorded_at": "2026-07-02T02:36:01Z",
            "source_ref": "/tmp/old-typed-blocker-resolution.json",
            "next_owner_action": {
                "study_id": study_id,
                "next_owner": "mas_authority_kernel",
                "action_type": "await_human_or_mas_authority_decision_for_submission_blocker",
                "allowed_actions": [
                    "await_human_or_mas_authority_decision_for_submission_blocker"
                ],
                "work_unit_id": "submission_blocker_human_gate",
                "work_unit_fingerprint": "old-submission-human-gate",
            },
        },
    )
    profile = type("Profile", (), {"workspace_root": str(workspace_root)})()
    revision_next_action = {
        "surface_kind": SURFACE_KIND,
        "action_id": "next-action::obesity::write-repair",
        "action_family": "paper.write.prose_repair",
        "action_kind": "paper_write",
        "action_type": "request_opl_stage_attempt",
        "owner": "write",
        "work_unit_id": "medical_methods_and_registry_reporting_repair",
    }

    payload = module.attach_typed_blocker_resolution_successor_projection(
        payload={
            "study_id": study_id,
            "next_action": revision_next_action,
            "canonical_next_action_source": "domain_transition.next_action",
        },
        profile=profile,
        study_id=study_id,
    )

    assert payload["canonical_next_action_source"] == "domain_transition.next_action"
    assert payload["next_action"] == revision_next_action
    assert "typed_blocker_resolution_readback" not in payload


def test_top_level_next_legal_action_prefers_receipt_consumption_over_stage_replay() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress.mission_summary"
    )

    payload = module.refresh_top_level_stage_closure_projection(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "mas_receipt_consumption": {
                "surface_kind": "mas_receipt_consumption_projection",
                "status": "requires_mas_owner_consumption",
                "next_legal_action": "consume_opl_stage_attempt_receipt",
            },
            "stage_closure_decision": {
                "projection_status": "terminalizer_outcome_observed",
                "decision_ref": "stage-closure::dm003",
                "outcome": {
                    "kind": "next_stage_transition",
                    "transition_kind": "route_back_candidate_checkpoint",
                    "next_action": "consume_route_back_checkpoint_or_materialize_terminalizer_outcome",
                },
            },
        }
    )

    assert payload["next_legal_action"] == "consume_opl_stage_attempt_receipt"


def test_artifact_first_mission_summary_prefers_current_stage_closure_readback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress.mission_summary"
    )

    monkeypatch.setattr(module, "_latest_materialized_mission", lambda *_: {})
    monkeypatch.setattr(
        module,
        "_current_stage_closure_readback",
        lambda **_: {
            "surface_kind": "mas_stage_closure_decision",
            "decision_ref": "/tmp/current-stage-closure.json",
            "outcome": {
                "kind": "next_stage_transition",
                "transition_kind": "route_back_candidate_checkpoint",
                "route_checkpoint_evidence_ref": (
                    "ops/medautoscience/paper_mission_stage_attempts/"
                    "sat-current/stage_attempt_closeout_packet.json"
                ),
                "next_action": (
                    "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                ),
            },
            "opl_closeout": {
                "status": "opl_runtime_terminal_readback_observed",
                "stage_attempt_id": "sat-current",
                "work_unit_id": "submission_milestone_candidate",
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_study_progress_opl_runtime_readback",
        lambda **_: {
            "opl_stage_attempt_readback_status": "opl_runtime_terminal_readback_observed",
            "opl_stage_attempt_readback": {
                "carrier_status": "opl_runtime_terminal_readback_observed",
                "terminal_closeout": {
                    "stage_attempt_id": "sat-current",
                    "closeout_ref": (
                        "ops/medautoscience/paper_mission_stage_attempts/"
                        "sat-current/stage_attempt_closeout_packet.json"
                    ),
                },
            },
        },
    )

    payload = module.attach_artifact_first_mission_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "study_root": "/tmp/studies/003-dpcc-primary-care-phenotype-treatment-gap",
            "paper_progress_delta": {"count": 0, "token_usage_total": 0, "sources": []},
            "stage_closure_decision": {
                "projection_status": "terminalizer_outcome_observed",
                "decision_ref": "/tmp/stale-stage-closure.json",
                "outcome": {
                    "kind": "next_stage_transition",
                    "transition_kind": "route_back_candidate_checkpoint",
                    "route_checkpoint_evidence_ref": (
                        "ops/medautoscience/paper_mission_stage_attempts/"
                        "sat-stale/stage_attempt_closeout_packet.json"
                    ),
                    "next_action": (
                        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                    ),
                },
                "opl_closeout": {
                    "status": "opl_runtime_terminal_readback_observed",
                    "stage_attempt_id": "sat-stale",
                },
            },
        },
    )

    assert payload["stage_closure_decision"]["decision_ref"] == "/tmp/current-stage-closure.json"
    assert payload["stage_closure"]["decision_ref"] == "/tmp/current-stage-closure.json"
    assert payload["stage_closure"]["outcome"]["route_checkpoint_evidence_ref"].endswith(
        "sat-current/stage_attempt_closeout_packet.json"
    )


def test_paper_mission_run_nested_stage_closure_readback_keeps_terminalizer_fields() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress.mission_summary"
    )

    paper_mission_run = {
        "mission_id": "paper-mission::dm003",
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
    }
    updated = module._paper_mission_run_with_stage_closure_readback(
        paper_mission_run=paper_mission_run,
        stage_closure_decision={
            "projection_status": "terminalizer_outcome_observed",
            "decision_ref": "stage-closure::dm003",
            "outcome": {
                "kind": "typed_blocker",
                "next_action": "materialize_typed_blocker_or_route_redesign",
            },
            "outcome_kind": "typed_blocker",
            "repair_budget": {
                "repair_budget_max": 3,
                "repair_attempt_count": 3,
                "repair_budget_status": "exhausted",
            },
            "package_kind": "degraded_handoff_package",
            "known_blockers": ["claim_evidence_consistency_failed"],
        },
    )

    assert updated["mission_id"] == paper_mission_run["mission_id"]
    assert updated["stage_closure_readback"] == {
        "projection_status": "terminalizer_outcome_observed",
        "decision_ref": "stage-closure::dm003",
        "outcome": {
            "kind": "typed_blocker",
            "next_action": "materialize_typed_blocker_or_route_redesign",
        },
        "outcome_kind": "typed_blocker",
        "repair_budget": {
            "repair_budget_max": 3,
            "repair_attempt_count": 3,
            "repair_budget_status": "exhausted",
        },
        "package_kind": "degraded_handoff_package",
        "known_blockers": ["claim_evidence_consistency_failed"],
    }
