from __future__ import annotations

import importlib


def _invalid_blocking_payload() -> dict[str, object]:
    return {
        "interaction_id": "progress-standby-001",
        "kind": "progress",
        "reply_mode": "blocking",
        "expects_reply": True,
        "allow_free_text": True,
        "reply_schema": {"type": "free_text"},
        "decision_type": None,
        "options_count": 0,
        "guidance_requires_user_decision": False,
        "source_artifact_path": "/tmp/runtime/quests/quest-001/.ds/worktrees/paper-main/artifacts/progress/progress-standby-001.json",
    }


def test_arbitrate_waiting_for_user_rejects_invalid_blocking_progress_under_autonomous_policy() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_interaction_arbitration")

    result = module.arbitrate_waiting_for_user(
        pending_interaction=_invalid_blocking_payload(),
        decision_policy="autonomous",
        submission_metadata_only=False,
    )

    assert result == {
        "classification": "invalid_blocking",
        "action": "resume",
        "reason_code": "blocking_requires_structured_decision_request",
        "requires_user_input": False,
        "valid_blocking": False,
        "kind": "progress",
        "decision_type": None,
        "source_artifact_path": "/tmp/runtime/quests/quest-001/.ds/worktrees/paper-main/artifacts/progress/progress-standby-001.json",
        "controller_stage_note": (
            "MAS-managed waiting_for_user is a controller-owned arbitration surface; "
            "runtime blocking is rejected unless it is a valid structured decision request."
        ),
    }


def test_arbitrate_waiting_for_user_rejects_program_decision_requests_inside_mas_managed_mode() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_interaction_arbitration")

    result = module.arbitrate_waiting_for_user(
        pending_interaction={
            "interaction_id": "decision-001",
            "kind": "decision_request",
            "reply_mode": "blocking",
            "expects_reply": True,
            "allow_free_text": False,
            "reply_schema": {"decision_type": "program_routing_choice"},
            "decision_type": "program_routing_choice",
            "options_count": 2,
            "guidance_requires_user_decision": True,
            "source_artifact_path": "/tmp/runtime/quests/quest-001/artifacts/interactions/decision-001.json",
        },
        decision_policy="user_gated",
        submission_metadata_only=False,
    )

    assert result == {
        "classification": "invalid_blocking",
        "action": "resume",
        "reason_code": "mas_managed_policy_rejects_runtime_user_gate",
        "requires_user_input": False,
        "valid_blocking": False,
        "kind": "decision_request",
        "decision_type": "program_routing_choice",
        "source_artifact_path": "/tmp/runtime/quests/quest-001/artifacts/interactions/decision-001.json",
        "controller_stage_note": (
            "MAS-managed studies must keep routing, finalize, adequacy, publishability, and completion decisions "
            "inside the MAS outer loop; runtime blocking may only ask for external secrets or credentials."
        ),
    }


def test_arbitrate_waiting_for_user_rejects_completion_request_before_publication_gate_clears() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_interaction_arbitration")

    result = module.arbitrate_waiting_for_user(
        pending_interaction={
            "interaction_id": "decision-completion-001",
            "kind": "decision",
            "reply_mode": "blocking",
            "expects_reply": True,
            "allow_free_text": False,
            "reply_schema": {"decision_type": "quest_completion_approval"},
            "decision_type": "quest_completion_approval",
            "options_count": 0,
            "guidance_requires_user_decision": True,
            "source_artifact_path": "/tmp/runtime/quests/quest-001/artifacts/decisions/decision-completion-001.json",
        },
        decision_policy="autonomous",
        submission_metadata_only=False,
        publication_gate_report={
            "status": "blocked",
            "blockers": ["forbidden_manuscript_terminology"],
            "current_required_action": "complete_bundle_stage",
        },
    )

    assert result == {
        "classification": "premature_completion_request",
        "action": "resume",
        "reason_code": "completion_requested_before_publication_gate_clear",
        "requires_user_input": False,
        "valid_blocking": False,
        "kind": "decision",
        "decision_type": "quest_completion_approval",
        "source_artifact_path": "/tmp/runtime/quests/quest-001/artifacts/decisions/decision-completion-001.json",
        "publication_gate_status": "blocked",
        "publication_gate_blockers": ["forbidden_manuscript_terminology"],
        "publication_gate_required_action": "complete_bundle_stage",
        "controller_stage_note": (
            "Runtime completion approval was requested before the MAS publication gate cleared; "
            "resume the managed runtime so it fixes publication blockers instead of asking the user."
        ),
    }


def test_arbitrate_waiting_for_user_blocks_external_secret_request() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_interaction_arbitration")

    result = module.arbitrate_waiting_for_user(
        pending_interaction={
            "interaction_id": "decision-secret-001",
            "kind": "decision_request",
            "reply_mode": "blocking",
            "expects_reply": True,
            "allow_free_text": False,
            "reply_schema": {"decision_type": "external_secret_request"},
            "decision_type": "external_secret_request",
            "options_count": 1,
            "guidance_requires_user_decision": True,
            "source_artifact_path": "/tmp/runtime/quests/quest-001/artifacts/interactions/decision-secret-001.json",
        },
        decision_policy="autonomous",
        submission_metadata_only=False,
    )

    assert result == {
        "classification": "external_input_required",
        "action": "block",
        "reason_code": "external_secret_or_credential_required",
        "requires_user_input": True,
        "valid_blocking": True,
        "kind": "decision_request",
        "decision_type": "external_secret_request",
        "source_artifact_path": "/tmp/runtime/quests/quest-001/artifacts/interactions/decision-secret-001.json",
        "controller_stage_note": (
            "Only explicit external secrets or credentials may stay user-blocking under MAS management."
        ),
    }


def test_arbitrate_waiting_for_user_allows_submission_metadata_only_resume_without_user_decision() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_interaction_arbitration")

    result = module.arbitrate_waiting_for_user(
        pending_interaction=None,
        decision_policy="autonomous",
        submission_metadata_only=True,
    )

    assert result == {
        "classification": "submission_metadata_only",
        "action": "resume",
        "reason_code": "submission_metadata_only",
        "requires_user_input": False,
        "valid_blocking": False,
        "kind": None,
        "decision_type": None,
        "source_artifact_path": None,
        "controller_stage_note": (
            "Submission metadata gaps stay controller-owned and must not block autonomous runtime continuation."
        ),
    }


def test_arbitrate_waiting_for_user_redrives_callable_blocked_closeout_owner_without_pending_interaction() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_interaction_arbitration")

    result = module.arbitrate_waiting_for_user(
        pending_interaction=None,
        decision_policy="autonomous",
        submission_metadata_only=False,
        blocked_closeout={
            "run_id": "run-blocked",
            "closeout_path": "/tmp/runtime/quests/quest-001/artifacts/runtime/turn_closeouts/run-blocked.json",
            "blocked_reason": "publication gate requires AI reviewer provenance",
            "next_owner": "ai_reviewer",
        },
    )

    assert result == {
        "classification": "blocked_closeout_owner_redrive",
        "action": "resume",
        "reason_code": "blocked_turn_closeout_waiting_for_callable_owner",
        "requires_user_input": False,
        "valid_blocking": False,
        "kind": "turn_closeout",
        "decision_type": None,
        "source_artifact_path": "/tmp/runtime/quests/quest-001/artifacts/runtime/turn_closeouts/run-blocked.json",
        "run_id": "run-blocked",
        "next_owner": "ai_reviewer",
        "blocked_reason": "publication gate requires AI reviewer provenance",
        "controller_stage_note": (
            "The latest MAS turn closeout parked execution for a registered callable owner; "
            "resume the managed runtime or controller dispatch instead of projecting a user wait."
        ),
    }


def test_arbitrate_waiting_for_user_blocks_unknown_blocked_closeout_owner_without_pending_interaction() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_interaction_arbitration")

    result = module.arbitrate_waiting_for_user(
        pending_interaction=None,
        decision_policy="autonomous",
        submission_metadata_only=False,
        blocked_closeout={
            "run_id": "run-blocked",
            "closeout_path": "/tmp/runtime/quests/quest-001/artifacts/runtime/turn_closeouts/run-blocked.json",
            "blocked_reason": "external owner handoff",
            "next_owner": "unknown_external_owner",
        },
    )

    assert result["classification"] == "blocked_closeout_owner_wait"
    assert result["action"] == "block"
    assert result["requires_user_input"] is False
    assert result["valid_blocking"] is True
    assert result["next_owner"] == "unknown_external_owner"


def test_arbitrate_waiting_for_user_redrives_mas_controller_route_authorization_owner() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_interaction_arbitration")

    result = module.arbitrate_waiting_for_user(
        pending_interaction=None,
        decision_policy="autonomous",
        submission_metadata_only=False,
        blocked_closeout={
            "run_id": "run-blocked",
            "closeout_path": "/tmp/runtime/quests/quest-001/artifacts/runtime/turn_closeouts/run-blocked.json",
            "blocked_reason": "control_plane_route_blocked_bundle_build",
            "next_owner": "MAS/controller route authorization owner for bundle_build_allowed",
        },
    )

    assert result["classification"] == "blocked_closeout_owner_redrive"
    assert result["action"] == "resume"
    assert result["requires_user_input"] is False
    assert result["valid_blocking"] is False
    assert result["next_owner"] == "MAS/controller route authorization owner for bundle_build_allowed"


def test_arbitrate_waiting_for_user_redrives_mas_controller_colon_owner() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_interaction_arbitration")

    result = module.arbitrate_waiting_for_user(
        pending_interaction=None,
        decision_policy="autonomous",
        submission_metadata_only=False,
        blocked_closeout={
            "run_id": "run-blocked",
            "closeout_path": "/tmp/runtime/quests/quest-001/artifacts/runtime/turn_closeouts/run-blocked.json",
            "blocked_reason": "canonical_artifact_delta_missing",
            "next_owner": (
                "MAS/controller: redrive submission_minimal_refresh with a controller-owned "
                "paper-facing artifact delta"
            ),
        },
    )

    assert result["classification"] == "blocked_closeout_owner_redrive"
    assert result["action"] == "resume"
    assert result["requires_user_input"] is False
    assert result["valid_blocking"] is False


def test_arbitrate_waiting_for_user_respects_delivered_package_oracle_over_blocked_closeout_redrive() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_interaction_arbitration")

    result = module.arbitrate_waiting_for_user(
        pending_interaction=None,
        decision_policy="autonomous",
        submission_metadata_only=False,
        blocked_closeout={
            "run_id": "run-old",
            "closeout_path": "/tmp/runtime/quests/quest-001/artifacts/runtime/turn_closeouts/run-old.json",
            "blocked_reason": "old owner_handoff",
            "next_owner": "MAS/controller",
        },
        domain_transition={
            "decision_type": "delivered_package_handoff",
            "route_target": "human_gate",
            "controller_action": "wait_for_human_gate",
            "next_work_unit": {"unit_id": "package_review_handoff"},
            "guard_boundary": {"opl_generic_runner_may_resume": False},
            "typed_blocker": {"blocker_id": "package_delivered_not_publication_authority"},
        },
    )

    assert result["classification"] == "domain_transition_terminal_or_handoff"
    assert result["action"] == "block"
    assert result["reason_code"] == "domain_transition_delivered_package_handoff"
    assert result["requires_user_input"] is False
    assert result["valid_blocking"] is True
    assert result["domain_transition_decision_type"] == "delivered_package_handoff"
    assert result["next_work_unit_id"] == "package_review_handoff"


def test_arbitrate_waiting_for_user_respects_human_gate_oracle_over_auto_resume() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_interaction_arbitration")

    result = module.arbitrate_waiting_for_user(
        pending_interaction=None,
        decision_policy="autonomous",
        submission_metadata_only=False,
        continuation_state={
            "continuation_policy": "auto",
            "continuation_anchor": "decision",
            "continuation_reason": "controller_work_unit_pending",
            "pending_user_message_count": 0,
        },
        controller_authorization={
            "decision_id": "decision-human-gate",
            "work_unit_id": "submission_authority_sync_closure",
            "work_unit_fingerprint": "fingerprint-human-gate",
        },
        domain_transition={
            "decision_type": "human_gate",
            "route_target": "human_gate",
            "controller_action": "wait_for_human_gate",
            "next_work_unit": {"unit_id": "human_gate_resume"},
            "guard_boundary": {"opl_generic_runner_may_resume": False},
            "typed_blocker": {"blocker_id": "human_gate_required"},
        },
    )

    assert result["classification"] == "domain_transition_terminal_or_handoff"
    assert result["action"] == "block"
    assert result["reason_code"] == "domain_transition_human_gate"
    assert result["domain_transition_decision_type"] == "human_gate"


def test_arbitrate_waiting_for_user_respects_stop_loss_oracle_over_platform_redrive() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_interaction_arbitration")

    result = module.arbitrate_waiting_for_user(
        pending_interaction=None,
        decision_policy="autonomous",
        submission_metadata_only=False,
        continuation_state={
            "continuation_policy": "auto",
            "continuation_anchor": "decision",
            "continuation_reason": "runtime_platform_repair_redrive",
            "pending_user_message_count": 0,
        },
        domain_transition={
            "decision_type": "stop_loss",
            "route_target": "stop",
            "controller_action": "stop_runtime",
            "next_work_unit": {"unit_id": "stop_loss_handoff"},
            "guard_boundary": {"opl_generic_runner_may_resume": False},
            "typed_blocker": {"blocker_id": "stop_loss_active"},
        },
    )

    assert result["classification"] == "domain_transition_terminal_or_handoff"
    assert result["action"] == "block"
    assert result["reason_code"] == "domain_transition_stop_loss"
    assert result["domain_transition_decision_type"] == "stop_loss"


def test_arbitrate_waiting_for_user_routes_publication_blocker_as_oracle_blocker_not_user_wait() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_interaction_arbitration")

    result = module.arbitrate_waiting_for_user(
        pending_interaction={
            "interaction_id": "decision-completion-001",
            "kind": "decision",
            "reply_mode": "blocking",
            "expects_reply": True,
            "allow_free_text": False,
            "reply_schema": {"decision_type": "quest_completion_approval"},
            "decision_type": "quest_completion_approval",
            "options_count": 0,
            "guidance_requires_user_decision": True,
            "source_artifact_path": "/tmp/runtime/quests/quest-001/artifacts/decisions/decision-completion-001.json",
        },
        decision_policy="autonomous",
        submission_metadata_only=False,
        publication_gate_report={
            "status": "blocked",
            "blockers": ["claim_specificity_gap"],
            "current_required_action": "complete_bundle_stage",
        },
        domain_transition={
            "decision_type": "publication_gate_blocker",
            "route_target": "review",
            "controller_action": "run_gate_clearing_batch",
            "next_work_unit": {"unit_id": "publication_gate_replay"},
            "guard_boundary": {
                "required_owner_surface": "artifacts/publication_eval/latest.json",
                "opl_generic_runner_may_resume": False,
            },
            "typed_blocker": {"blocker_id": "publication_gate_blocked"},
        },
    )

    assert result["classification"] == "domain_transition_publication_blocker"
    assert result["action"] == "resume"
    assert result["reason_code"] == "domain_transition_publication_gate_blocker"
    assert result["valid_blocking"] is False
    assert result["domain_transition_decision_type"] == "publication_gate_blocker"
    assert result["next_work_unit_id"] == "publication_gate_replay"
