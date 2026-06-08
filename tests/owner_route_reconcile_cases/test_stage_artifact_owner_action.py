from __future__ import annotations

import importlib
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _terminal_stage_artifact_index(study_root: Path) -> dict[str, object]:
    stage_root = study_root / "artifacts" / "stage_outputs" / "08-publication_package_handoff"
    return {
        "surface_kind": "stage_artifact_index",
        "schema_version": 1,
        "current_stage": {
            "stage_id": "08-publication_package_handoff",
            "artifact_status": "artifact_delta_present",
            "stage_progress_status": "artifact_delta_present",
            "next_missing_surface": None,
        },
        "next_owner_action": {
            "owner": "08-publication_package_handoff",
            "next_owner": "publication_gate_owner",
            "action_type": "publication_handoff_owner_gate",
            "allowed_actions": ["publication_handoff_owner_gate"],
            "required_delta_kind": "publication_handoff_owner_receipt_or_typed_blocker",
            "work_unit_id": "publication_handoff_owner_gate",
            "required_output_surface": None,
            "manifest_ref": str(stage_root / "stage_manifest.json"),
            "receipt_ref": str(stage_root / "receipts" / "owner_receipt.json"),
            "authority_boundary": {
                "refs_only": True,
                "can_write_runtime_owned_surfaces": False,
                "can_write_paper_or_package": False,
                "can_authorize_quality_verdict": False,
                "can_authorize_publication_readiness": False,
                "can_authorize_submission_readiness": False,
            },
            "artifact_first_authority": True,
            "terminal_publication_handoff": True,
            "owner_receipt_required": True,
            "can_authorize_quality_verdict": False,
            "can_authorize_publication_readiness": False,
            "can_authorize_submission_readiness": False,
        },
        "stages": [
            {
                "stage_id": "08-publication_package_handoff",
                "artifact_status": "Delta",
                "stage_progress_status": "awaiting_owner_receipt",
            }
        ],
    }


def test_scan_domain_routes_promotes_stage_artifact_publication_handoff_action(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm002")
    quest_root = profile.runtime_root / "quest-dm002"
    stage_artifact_index = _terminal_stage_artifact_index(study_root)

    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": "quest-dm002",
        "quest_root": str(quest_root),
        "quest_status": "running",
        "current_execution_envelope": {
            "state_kind": "typed_blocker",
            "typed_blocker": {
                "blocker_type": "current_execution_unresolved",
                "owner": "med-autoscience",
            },
        },
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-epoch-dm002-stage-handoff",
            "canonical_runtime_action": "observe_runtime",
            "attempt_state": "parked",
            "retry_budget_remaining": 0,
        },
        "publication_eval": {
            "eval_id": "publication-eval::dm002::terminal-handoff",
            "recommended_actions": [
                {
                    "action_type": "return_to_controller",
                    "work_unit_fingerprint": "stale-default-dispatch",
                    "next_work_unit": {"unit_id": "manuscript_story_repair"},
                }
            ],
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm002-terminal-handoff",
            "source_signature": "truth-source-dm002-terminal-handoff",
        },
        "domain_transition": {
            "decision_type": "route_back_same_line",
            "controller_action": "request_opl_stage_attempt",
            "next_work_unit": {"unit_id": "manuscript_story_repair"},
        },
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": "quest-dm002",
        "current_stage": "publication_supervision",
        "paper_stage": "bundle_stage_blocked",
        "stage_artifact_index": stage_artifact_index,
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "stage_artifact_index.next_owner_action",
            "next_owner": "publication_gate_owner",
            "work_unit_id": "publication_handoff_owner_gate",
            "allowed_actions": ["publication_handoff_owner_gate"],
            "required_delta_kind": "publication_handoff_owner_receipt_or_typed_blocker",
        },
    }

    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, "quest-dm002", status_payload["publication_eval"]),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["stage_artifact_index"] == stage_artifact_index
    assert study["current_executable_owner_action"]["source"] == "stage_artifact_index.next_owner_action"
    assert [action["action_type"] for action in study["action_queue"]] == ["publication_handoff_owner_gate"]
    action = study["action_queue"][0]
    assert action["owner"] == "publication_gate_owner"
    assert action["required_output_surface"] == (
        "artifacts/stage_outputs/08-publication_package_handoff/handoff_owner_receipt.json "
        "or artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
    )
    assert study["owner_route"]["next_owner"] == "publication_gate_owner"
    assert study["owner_route"]["allowed_actions"] == ["publication_handoff_owner_gate"]
    assert study["owner_route"]["source_refs"]["work_unit_id"] == "publication_handoff_owner_gate"
    assert study["owner_route"]["source_refs"]["work_unit_fingerprint"] == (
        "stage-artifact-index::08-publication_package_handoff::publication_handoff_owner_gate"
    )
    assert study["why_not_applied"] == "publication_handoff_owner_gate"
    assert study["blocked_reason"] == "publication_handoff_owner_gate"
    assert study["next_owner"] == "publication_gate_owner"
    assert result["action_queue"][0]["action_type"] == "publication_handoff_owner_gate"


def test_scan_domain_routes_promotes_handoff_typed_blocker_followup_action(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm002")
    quest_root = profile.runtime_root / "quest-dm002"
    typed_blocker_ref = (
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
    )
    stage_artifact_index = _terminal_stage_artifact_index(study_root)

    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": "quest-dm002",
        "quest_root": str(quest_root),
        "quest_status": "running",
        "current_execution_envelope": {
            "state_kind": "typed_blocker",
            "typed_blocker": {
                "blocker_type": "medical_paper_readiness_not_ready",
                "owner": "MedAutoScience",
            },
        },
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-epoch-dm002-readiness-followup",
            "canonical_runtime_action": "observe_runtime",
        },
        "publication_eval": {},
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm002-readiness-followup",
            "source_signature": "truth-source-dm002-readiness-followup",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": "quest-dm002",
        "current_stage": "publication_supervision",
        "paper_stage": "bundle_stage_blocked",
        "medical_paper_readiness": {
            "overall_status": "blocked",
            "next_action": {
                "action_id": "complete_medical_paper_readiness_surface",
                "surface_key": "literature_provider_runtime",
                "summary": "运行联网 literature provider runtime 并写入可审计来源后再继续。",
            },
        },
        "stage_artifact_index": stage_artifact_index,
        "stage_kernel_projection": {
            "current_owner_delta": {
                "owner": "MedAutoScience",
                "action": "complete_medical_paper_readiness_surface",
                "reason": "medical_paper_readiness_not_ready",
                "required_input": "complete_medical_paper_readiness_surface",
                "blocked_surface": "publication_handoff_owner_gate",
                "source_ref": typed_blocker_ref,
                "source_kind": "typed_blocker",
            }
        },
    }

    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, "quest-dm002", status_payload["publication_eval"]),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["current_executable_owner_action"]["source"] == "stage_kernel_projection.current_owner_delta"
    assert study["current_executable_owner_action"]["allowed_actions"] == [
        "complete_medical_paper_readiness_surface"
    ]
    assert study["current_executable_owner_action"]["blocked_surface"] == "publication_handoff_owner_gate"
    assert study["current_executable_owner_action"]["surface_key"] == "literature_provider_runtime"
    assert study["current_executable_owner_action"]["target_surface"]["surface_key"] == (
        "literature_provider_runtime"
    )
    assert [action["action_type"] for action in study["action_queue"]] == [
        "complete_medical_paper_readiness_surface"
    ]
    action = study["action_queue"][0]
    assert action["owner"] == "MedAutoScience"
    assert action["source_surface"] == "stage_kernel_projection.current_owner_delta"
    assert action["source_ref"] == typed_blocker_ref
    assert action["surface_key"] == "literature_provider_runtime"
    assert action["next_action"]["surface_key"] == "literature_provider_runtime"
    assert action["work_unit_fingerprint"] == (
        "stage-current-owner-delta::complete_medical_paper_readiness_surface::"
        "literature_provider_runtime::"
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
    )
    assert study["owner_route"]["next_owner"] == "MedAutoScience"
    assert study["owner_route"]["allowed_actions"] == ["complete_medical_paper_readiness_surface"]
    assert study["owner_route"]["source_refs"]["work_unit_fingerprint"] == action["work_unit_fingerprint"]
    assert study["why_not_applied"] == "medical_paper_readiness_not_ready"
    assert study["blocked_reason"] == "medical_paper_readiness_not_ready"
    assert result["action_queue"][0]["action_type"] == "complete_medical_paper_readiness_surface"
    queued_action = result["action_queue"][0]
    assert queued_action["action_fingerprint"] == action["work_unit_fingerprint"]
    assert queued_action["handoff_packet"]["action_fingerprint"] == action["work_unit_fingerprint"]
    assert queued_action["paper_progress_stall_action_fingerprint"].startswith("paper_progress_stall:")
    assert queued_action["handoff_packet"]["paper_progress_stall_action_fingerprint"].startswith(
        "paper_progress_stall:"
    )


def test_stage_kernel_typed_blocker_answer_without_next_action_suppresses_requeue() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.stage_artifact_owner_actions"
    )
    typed_blocker_ref = (
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
    )
    stale_controller_actions = [
        {
            "action_type": "return_to_ai_reviewer_workflow",
            "controller_route": {"decision_path": "artifacts/controller_decisions/latest.json"},
        }
    ]
    progress_payload = {
        "medical_paper_readiness": {"overall_status": "blocked"},
        "stage_kernel_projection": {
            "current_owner_delta": {
                "owner": "MedAutoScience",
                "action": "complete_medical_paper_readiness_surface",
                "reason": "medical_paper_readiness_missing",
                "required_input": "complete_medical_paper_readiness_surface",
                "blocked_surface": "publication_handoff_owner_gate",
                "source_ref": typed_blocker_ref,
                "source_kind": "typed_blocker",
                "latest_owner_answer_kind": "typed_blocker",
                "hard_gate": {
                    "state": "domain_owner_answer_recorded",
                    "owner_answer_ref": typed_blocker_ref,
                },
            }
        },
    }

    actions = module.action_queue_with_terminal_publication_handoff(
        actions=stale_controller_actions,
        progress=progress_payload,
        study_id="002-dm-china-us-mortality-attribution",
        quest_id="quest-dm002",
        decorate_action=lambda *, study_id, quest_id, action: {
            **action,
            "study_id": study_id,
            "quest_id": quest_id,
        },
    )

    assert actions == []
    assert module.projection_fields(progress_payload, stale_controller_actions) == {}
