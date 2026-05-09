from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_auto_runtime_parked_truth_suppresses_stale_external_supervisor_lifecycle(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-dm-cvd-mortality-risk", quest_id="quest-dm001")
    status_payload = _parked_status(
        study_root=study_root,
        quest_id="quest-dm001",
        parked_state="external_metadata_pending",
        reason="quest_waiting_for_submission_metadata",
    )
    progress_payload = {
        "study_id": "001-dm-cvd-mortality-risk",
        "quest_id": "quest-dm001",
        "current_stage": "auto_runtime_parked",
        "paper_stage": "bundle_stage_blocked",
        "auto_runtime_parked": status_payload["auto_runtime_parked"],
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "ai_repair_lifecycle": {
            "state": "blocked",
            "blocked_reason": "abnormal_stopped_runtime_resume_required",
            "next_owner": "external_supervisor",
            "external_supervisor_required": True,
        },
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (
            status_payload,
            progress_payload,
            "quest-dm001",
            _ai_reviewer_eval(required=False),
        ),
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=["001-dm-cvd-mortality-risk"],
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["action_queue"] == []
    assert study["why_not_applied"] is None
    assert study["blocked_reason"] is None
    assert study["next_owner"] is None
    assert study["external_supervisor_required"] is False
    assert study["owner_route"]["current_owner"] == "controller_stop"
    assert study["owner_route"]["allowed_actions"] == []


@pytest.mark.parametrize(
    ("study_id", "parked_state", "reason", "paper_stage"),
    [
        (
            "004-dpcc-longitudinal-care-inertia-intensification-gap",
            "manual_hold",
            "quest_waiting_for_explicit_wakeup_after_manual_hold",
            "manual_hold",
        ),
        ("001-lineage-pfs", "publishability_stop_loss", "publishability_stop_loss_recommended", "stop_loss"),
    ],
)
def test_terminal_parked_truth_does_not_reopen_ai_reviewer_queue(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    study_id: str,
    parked_state: str,
    reason: str,
    paper_stage: str,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    status_payload = _parked_status(
        study_root=study_root,
        quest_id=f"quest-{study_id}",
        parked_state=parked_state,
        reason=reason,
    )
    progress_payload = {
        "study_id": study_id,
        "quest_id": f"quest-{study_id}",
        "current_stage": "auto_runtime_parked",
        "paper_stage": paper_stage,
        "auto_runtime_parked": status_payload["auto_runtime_parked"],
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "quality_review_loop": {"closure_state": "review_required"},
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (
            status_payload,
            progress_payload,
            f"quest-{study_id}",
            _ai_reviewer_eval(required=True),
        ),
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["action_queue"] == []
    assert study["why_not_applied"] is None
    assert study["blocked_reason"] is None
    assert study["next_owner"] is None
    assert study["external_supervisor_required"] is False
    assert study["owner_route"]["current_owner"] == "controller_stop"
    assert study["owner_route"]["next_owner"] is None


def test_ai_reviewer_pending_parked_truth_routes_to_ai_reviewer_workflow(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    quest_id = "quest-dm001"
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    status_payload = _parked_status(
        study_root=study_root,
        quest_id=quest_id,
        parked_state="ai_reviewer_pending",
        reason="quest_waiting_for_user",
    )
    status_payload["auto_runtime_parked"]["awaiting_explicit_wakeup"] = False
    status_payload["auto_runtime_parked"]["auto_execution_complete"] = False
    status_payload["auto_runtime_parked"]["parked_owner"] = "ai_reviewer"
    status_payload["interaction_arbitration"] = {
        "classification": "blocked_closeout_owner_wait",
        "reason_code": "blocked_turn_closeout_waiting_for_owner",
        "next_owner": "ai_reviewer",
    }
    status_payload["runtime_health_snapshot"]["canonical_runtime_action"] = "continue_supervising_runtime"
    status_payload["runtime_health_snapshot"]["blocking_reasons"] = []
    publication_eval = {
        "assessment_provenance": {
            "owner": "mechanical_projection",
            "ai_reviewer_required": True,
        },
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::specificity",
                "action_type": "return_to_controller",
                "next_work_unit": {"unit_id": "gate_needs_specificity"},
                "work_unit_fingerprint": "publication-blockers::same",
                "specificity_targets": _complete_specificity_targets(study_root),
            }
        ],
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "current_stage": "auto_runtime_parked",
        "paper_stage": "scientific_anchor_missing",
        "auto_runtime_parked": status_payload["auto_runtime_parked"],
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "quality_review_loop": {"closure_state": "review_required"},
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-ai-reviewer",
            "source_signature": "truth-source-ai-reviewer",
        },
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (
            status_payload,
            progress_payload,
            quest_id,
            publication_eval,
        ),
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["return_to_ai_reviewer_workflow"]
    assert [item["action_type"] for item in result["action_queue"]] == ["return_to_ai_reviewer_workflow"]
    assert study["why_not_applied"] == "ai_reviewer_assessment_required"
    assert study["blocked_reason"] == "ai_reviewer_assessment_required"
    assert study["next_owner"] == "ai_reviewer"
    assert study["owner_route"]["current_owner"] == "controller_stop"
    assert study["owner_route"]["next_owner"] == "ai_reviewer"
    assert study["owner_route"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]


def test_targets_resolved_auto_runtime_parked_routes_to_mas_controller_redrive(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "obesity_multicenter_phenotype_atlas"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::obesity::targets-resolved",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::return-to-controller::targets-resolved",
                "action_type": "return_to_controller",
                "work_unit_fingerprint": "publication-blockers::obesity-anchor",
                "next_work_unit": {
                    "unit_id": "gate_needs_specificity",
                    "lane": "controller",
                    "summary": "Ask the publication gate to identify concrete blocker targets.",
                },
                "specificity_targets": _complete_specificity_targets(study_root),
            }
        ],
    }
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "current-quality-repair-targets-resolved",
            "study_id": study_id,
            "quest_id": quest_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "run_quality_repair_batch"}],
            "route_target": "controller",
            "work_unit_fingerprint": "publication-blockers::obesity-anchor",
            "next_work_unit": {
                "unit_id": "gate_needs_specificity",
                "lane": "controller",
                "summary": "Ask the publication gate to identify concrete blocker targets.",
            },
        },
    )
    status_payload = _parked_status(
        study_root=study_root,
        quest_id=quest_id,
        parked_state="publication_gate_closeout_wait",
        reason="quest_waiting_for_user",
    )
    status_payload.update(
        {
            "quest_status": "waiting_for_user",
            "quest_root": str(quest_root),
            "publication_eval": publication_eval,
            "auto_runtime_parked": {
                "parked": True,
                "parked_state": "publication_gate_closeout_wait",
                "awaiting_explicit_wakeup": True,
                "auto_execution_complete": False,
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "continue_supervising_runtime",
                "attempt_state": "idle",
                "retry_budget_remaining": 3,
                "blocking_reasons": [],
            },
            "continuation_state": {
                "quest_status": "waiting_for_user",
                "active_run_id": None,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "turn_closeout",
                "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
                "pending_user_message_count": 0,
                "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
            },
            "blocked_turn_closeout": {
                "run_id": "mas-run-obesity-stale",
                "blocked_reason": "publication gate targets are now concrete",
                "next_owner": "publication_gate",
            },
            "interaction_arbitration": {
                "classification": "blocked_closeout_owner_wait",
                "action": "block",
                "reason_code": "blocked_turn_closeout_waiting_for_owner",
                "next_owner": "publication_gate",
            },
            "study_truth_snapshot": {
                "truth_epoch": "truth-epoch-obesity-targets",
                "source_signature": "truth-source-obesity-targets",
            },
        }
    )
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "auto_runtime_parked",
        "paper_stage": "scientific_anchor_missing",
        "auto_runtime_parked": status_payload["auto_runtime_parked"],
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["runtime_platform_repair"]
    assert study["action_queue"][0]["reason"] == "runtime_controller_redrive_required"
    assert study["action_queue"][0]["owner"] == "mas_controller"
    assert study["blocked_reason"] == "runtime_controller_redrive_required"
    assert study["next_owner"] == "mas_controller"
    assert study["owner_route"]["current_owner"] == "controller_stop"
    assert study["owner_route"]["allowed_actions"] == ["runtime_platform_repair"]


def test_explicit_resume_pending_with_current_controller_route_queues_ai_reviewer_workflow(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "obesity_multicenter_phenotype_atlas"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    work_unit_fingerprint = "publication-blockers::497d1260db522f01"
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::obesity::claim-evidence-repair",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {
            "owner": "mechanical_projection",
            "ai_reviewer_required": True,
        },
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::route-back-same-line",
                "action_type": "route_back_same_line",
                "work_unit_fingerprint": work_unit_fingerprint,
                "next_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                    "summary": "Repair claim-evidence, story, figure, and results traceability blockers.",
                },
                "specificity_targets": _complete_specificity_targets(study_root),
            }
        ],
    }
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "current-quality-repair-obesity",
            "study_id": study_id,
            "quest_id": quest_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "run_quality_repair_batch"}],
            "route_target": "write",
            "work_unit_fingerprint": work_unit_fingerprint,
            "next_work_unit": {
                "unit_id": "analysis_claim_evidence_repair",
                "lane": "analysis-campaign",
                "summary": "Repair claim-evidence, story, figure, and results traceability blockers.",
            },
        },
    )
    status_payload = _parked_status(
        study_root=study_root,
        quest_id=quest_id,
        parked_state="explicit_resume_pending",
        reason="quest_waiting_for_user",
    )
    status_payload.update(
        {
            "quest_status": "waiting_for_user",
            "quest_root": str(quest_root),
            "publication_eval": {},
            "continuation_state": {
                "quest_status": "waiting_for_user",
                "active_run_id": None,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "turn_closeout",
                "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
                "pending_user_message_count": 0,
                "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
            },
            "blocked_turn_closeout": {
                "run_id": "mas-run-obesity-blocked",
                "blocked_reason": "claim evidence repair still needs AI reviewer provenance",
                "next_owner": "artifact_os",
            },
            "interaction_arbitration": {
                "classification": "blocked_closeout_owner_wait",
                "action": "block",
                "reason_code": "blocked_turn_closeout_waiting_for_owner",
                "next_owner": "artifact_os",
            },
            "study_truth_snapshot": {
                "truth_epoch": "truth-epoch-obesity-ai-reviewer",
                "source_signature": "truth-source-obesity-ai-reviewer",
            },
        }
    )
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "auto_runtime_parked",
        "paper_stage": "publishability_gate_blocked",
        "auto_runtime_parked": status_payload["auto_runtime_parked"],
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "quality_review_loop": {"closure_state": "review_required"},
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["gate_specificity"]["status"] == "specific_targets_present"
    assert [item["action_type"] for item in study["action_queue"]] == ["return_to_ai_reviewer_workflow"]
    assert [item["action_type"] for item in result["action_queue"]] == ["return_to_ai_reviewer_workflow"]
    assert study["why_not_applied"] == "ai_reviewer_assessment_required"
    assert study["blocked_reason"] == "ai_reviewer_assessment_required"
    assert study["next_owner"] == "ai_reviewer"
    assert study["owner_route"]["current_owner"] == "controller_stop"
    assert study["owner_route"]["next_owner"] == "ai_reviewer"
    assert study["owner_route"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]


def _parked_status(*, study_root: Path, quest_id: str, parked_state: str, reason: str) -> dict:
    return {
        "study_id": study_root.name,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_status": "paused",
        "decision": "blocked",
        "reason": reason,
        "active_run_id": None,
        "auto_runtime_parked": {
            "parked": True,
            "parked_state": parked_state,
            "awaiting_explicit_wakeup": True,
            "auto_execution_complete": parked_state == "external_metadata_pending",
        },
        "runtime_liveness_audit": {
            "active_run_id": None,
            "runtime_audit": {"worker_running": False, "active_run_id": None},
        },
        "runtime_health_snapshot": {
            "canonical_runtime_action": "await_explicit_resume",
            "attempt_state": "parked",
            "blocking_reasons": [reason],
        },
    }


def _ai_reviewer_eval(*, required: bool) -> dict:
    return {
        "assessment_provenance": {
            "owner": "mechanical_projection" if required else "ai_reviewer",
            "ai_reviewer_required": required,
        },
        "recommended_actions": [],
    }


def _complete_specificity_targets(study_root: Path) -> list[dict[str, str]]:
    return [
        {
            "target_kind": "claim",
            "target_id": "claim_evidence_map",
            "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
            "blocking_reason": "missing_publication_anchor",
        },
        {
            "target_kind": "figure",
            "target_id": "figure_catalog",
            "source_path": str(study_root / "paper" / "figures" / "figure_catalog.json"),
            "blocking_reason": "missing_publication_anchor",
        },
        {
            "target_kind": "table",
            "target_id": "submission_table_or_manifest",
            "source_path": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
            "blocking_reason": "missing_publication_anchor",
        },
        {
            "target_kind": "metric",
            "target_id": "main_result_metrics",
            "source_path": str(study_root / "artifacts" / "results" / "main_result.json"),
            "blocking_reason": "missing_publication_anchor",
        },
        {
            "target_kind": "source_path",
            "target_id": "publication_gate_source_path",
            "source_path": str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
            "blocking_reason": "missing_publication_anchor",
        },
    ]
