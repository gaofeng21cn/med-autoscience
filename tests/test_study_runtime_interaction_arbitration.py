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
