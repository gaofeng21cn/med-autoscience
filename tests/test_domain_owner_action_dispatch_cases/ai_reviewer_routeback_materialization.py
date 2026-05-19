from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

from tests.domain_owner_action_dispatch_helpers import write_json as _write_json
from tests.study_runtime_test_helpers import make_profile, write_study


def _ai_reviewer_refs(study_root: Path) -> dict[str, str]:
    return {
        "manuscript": str(study_root / "paper" / "draft.md"),
        "evidence_ledger": str(study_root / "paper" / "evidence_ledger.json"),
        "review_ledger": str(study_root / "paper" / "review" / "review_ledger.json"),
        "study_charter": str(study_root / "artifacts" / "controller" / "study_charter.json"),
        "medical_manuscript_blueprint": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
        "claim_evidence_map": str(study_root / "paper" / "claim_evidence_map.json"),
        "medical_prose_review": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
        "publication_gate_projection": str(study_root / "artifacts" / "publication_gate" / "latest.json"),
    }


def _full_quality_assessment(refs: dict[str, str]) -> dict[str, Any]:
    return {
        "clinical_significance": {
            "status": "ready",
            "summary": "The clinical framing is relevant and bounded.",
            "evidence_refs": [refs["study_charter"], refs["manuscript"]],
        },
        "evidence_strength": {
            "status": "ready",
            "summary": "The evidence ledger supports the restrained transportability claims.",
            "evidence_refs": [refs["evidence_ledger"]],
        },
        "novelty_positioning": {
            "status": "ready",
            "summary": "The novelty claim is positioned as external validation and transportability.",
            "evidence_refs": [refs["study_charter"]],
        },
        "medical_journal_prose_quality": {
            "status": "partial",
            "summary": "The prose remains too conceptual for a medical original research article.",
            "evidence_refs": [refs["medical_prose_review"], refs["manuscript"]],
            "reviewer_reason": "Methods and Results must become result-driven and reproducible before readiness.",
        },
        "human_review_readiness": {
            "status": "ready",
            "summary": "The review ledger is sufficient for same-line repair.",
            "evidence_refs": [refs["review_ledger"]],
        },
    }


def _full_ai_reviewer_record(study_root: Path, *, study_id: str, quest_id: str, eval_id: str) -> dict[str, Any]:
    refs = _ai_reviewer_refs(study_root)
    return {
        "schema_version": 1,
        "eval_id": eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "emitted_at": "2026-05-17T07:48:44+00:00",
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": refs["study_charter"],
            "charter_id": f"charter::{study_id}::v1",
            "publication_objective": "External validation and transportability analysis for diabetes mortality.",
        },
        "runtime_context_refs": {
            "runtime_escalation_ref": str(study_root / "runtime" / "runtime_escalation_record.json"),
            "main_result_ref": str(study_root / "artifacts" / "results" / "main_result.json"),
        },
        "delivery_context_refs": {
            "paper_root_ref": str(study_root / "paper"),
            "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
        },
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "source_refs": [refs["manuscript"], refs["medical_prose_review"]],
            "ai_reviewer_required": False,
        },
        "verdict": {
            "overall_verdict": "mixed",
            "primary_claim_status": "partial",
            "summary": "The current manuscript requires same-line write repair before readiness.",
            "stop_loss_pressure": "watch",
        },
        "quality_assessment": _full_quality_assessment(refs),
        "gaps": [
            {
                "gap_id": "medical-prose-write-repair",
                "gap_type": "reporting",
                "severity": "must_fix",
                "summary": "The manuscript is not yet reproducible, result-driven, or transparent enough.",
                "evidence_refs": [refs["medical_prose_review"], refs["manuscript"]],
            }
        ],
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::route-back-write::medical-prose",
                "action_type": "route_back_same_line",
                "priority": "now",
                "reason": "Route the same paper line back to write for medical-journal prose repair.",
                "route_target": "write",
                "route_key_question": (
                    "What is the narrowest manuscript repair needed to make the current evidence read as "
                    "a medical original research article?"
                ),
                "route_rationale": "The reviewer judgment is current and evidence-bound.",
                "evidence_refs": [refs["medical_prose_review"], refs["manuscript"]],
                "requires_controller_decision": True,
                "work_unit_fingerprint": "medical-prose-route-back::write",
                "next_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                    "summary": "Repair the manuscript body against current AI reviewer prose findings.",
                },
            }
        ],
        "future_facing_limitations_plan": [
            {
                "limitation": "Shared covariates constrain cross-country transportability claims.",
                "impact_on_claim": "Absolute-risk and case-mix interpretations must remain restrained.",
                "required_future_analysis_data_or_design": "Use harmonized cohort variables and richer calibration data.",
                "current_manuscript_wording_must_be_restrained": True,
            }
        ],
    }


def _write_ai_reviewer_currentness_inputs(study_root: Path, *, eval_id: str) -> None:
    refs = _ai_reviewer_refs(study_root)
    request_digest = "sha256:" + "a" * 64
    manuscript_digest = "sha256:" + "c" * 64
    request_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json"
    _write_json(
        request_path,
        {
            "surface": "medical_prose_review_request",
            "request_digest": request_digest,
            "manuscript": {"path": refs["manuscript"], "digest": manuscript_digest},
        },
    )
    _write_json(
        Path(refs["medical_prose_review"]),
        {
            "surface": "medical_prose_review",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "request_ref": str(request_path),
                "request_digest": request_digest,
                "manuscript_ref": refs["manuscript"],
                "manuscript_digest": manuscript_digest,
            },
            "medical_journal_prose_quality": {
                "status": "partial",
                "overall_style_verdict": "revise",
                "route_back_recommendation": {
                    "required": True,
                    "route_target": "write",
                    "reason": "Rewrite manuscript prose against the current evidence.",
                },
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "current_package_freshness" / "latest.json",
        {
            "schema_version": 1,
            "status": "fresh",
            "source_eval_id": eval_id,
            "current_package_root": str(study_root / "manuscript" / "current_package"),
            "current_package_zip": str(study_root / "manuscript" / "current_package.zip"),
        },
    )


def _write_ai_reviewer_request(study_root: Path, *, study_id: str, quest_id: str, eval_id: str) -> None:
    refs = _ai_reviewer_refs(study_root)
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "input_contract": {
                "required_refs": {
                    surface: {"path": ref, "present": True, "valid": True}
                    for surface, ref in refs.items()
                },
                "all_required_refs_present": True,
                "missing_or_invalid_refs": [],
            },
            "ai_reviewer_record": _full_ai_reviewer_record(
                study_root,
                study_id=study_id,
                quest_id=quest_id,
                eval_id=eval_id,
            ),
        },
    )


class _DeveloperMode:
    def __init__(self, mode: str, *, safe_actions_enabled: bool, blocked_reason: str | None = None) -> None:
        self.mode = mode
        self.safe_actions_enabled = safe_actions_enabled
        self.blocked_reason = blocked_reason

    def to_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "requested_mode": "developer_apply_safe",
            "safe_actions_enabled": self.safe_actions_enabled,
            "blocked_reason": self.blocked_reason,
            "github_user_gate": {"allowed": self.safe_actions_enabled, "reason": self.blocked_reason},
        }


def test_managed_runtime_worker_materializes_current_route_back_ai_reviewer_eval(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    run_id = "mas-run-002-current"
    eval_id = "publication-eval::002::current-route-back"
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    _write_ai_reviewer_currentness_inputs(study_root, eval_id=eval_id)
    _write_ai_reviewer_request(study_root, study_id=study_id, quest_id=quest_id, eval_id=eval_id)
    _write_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "status": "running",
            "quest_id": quest_id,
            "active_run_id": run_id,
            "worker_running": True,
            "current_controller_authorization": {
                "decision_id": "fresh-ai-reviewer-medical-prose-decision",
                "authorization_basis": "controller_domain_transition",
                "active_run_id": run_id,
                "controller_actions": ["return_to_ai_reviewer_workflow"],
                "route_target": "review",
                "work_unit_id": "ai_reviewer_medical_prose_quality_review",
                "work_unit_fingerprint": "domain-transition::ai_reviewer_re_eval::medical-prose-review",
                "next_work_unit": {
                    "unit_id": "ai_reviewer_medical_prose_quality_review",
                    "lane": "review",
                },
            },
        },
    )
    monkeypatch.setenv("MED_AUTOSCIENCE_MANAGED_RUNTIME_WORKER", "1")
    monkeypatch.setenv("MED_AUTOSCIENCE_MANAGED_RUNTIME_QUEST_ROOT", str(quest_root))
    monkeypatch.setenv("MED_AUTOSCIENCE_MANAGED_RUNTIME_QUEST_ID", quest_id)
    monkeypatch.setenv("MED_AUTOSCIENCE_MANAGED_RUNTIME_RUN_ID", run_id)
    monkeypatch.setenv("HOME", str(quest_root / ".ds" / "codex_homes" / run_id))
    monkeypatch.setenv("CODEX_HOME", str(quest_root / ".ds" / "codex_homes" / run_id / ".codex"))
    monkeypatch.setattr(
        module,
        "resolve_developer_supervisor_mode",
        lambda **_: _DeveloperMode(
            "external_observe",
            safe_actions_enabled=False,
            blocked_reason="github_user_lookup_failed",
        ),
    )
    monkeypatch.setattr(
        module,
        "_refresh_controller_decision_after_ai_reviewer_eval",
        lambda **_: {"refresh_status": "skipped", "skipped_reason": "unit_test"},
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
        managed_runtime_worker=True,
    )

    latest = json.loads((study_root / "artifacts" / "publication_eval" / "latest.json").read_text(encoding="utf-8"))
    prose_currentness = latest["reviewer_operating_system"]["currentness_checks"]["medical_prose_review"]

    assert result["executed_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "executed"
    assert execution["managed_runtime_authorization"]["status"] == "authorized"
    assert latest["assessment_provenance"]["owner"] == "ai_reviewer"
    assert latest["assessment_provenance"]["source_kind"] == "publication_eval_ai_reviewer"
    assert latest["quality_assessment"]["medical_journal_prose_quality"]["status"] == "partial"
    assert latest["recommended_actions"][0]["action_type"] == "route_back_same_line"
    assert latest["recommended_actions"][0]["route_target"] == "write"
    assert prose_currentness["status"] == "current"
    assert prose_currentness["prose_status"] == "partial"
    assert prose_currentness["overall_style_verdict"] == "revise"
    assert prose_currentness["route_back_required"] is True
    assert prose_currentness["route_target"] == "write"


def test_dispatch_prefers_current_request_record_over_stale_latest_ai_reviewer_record(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    eval_id = "publication-eval::002::current-ai-reviewer-response"
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    refs = _ai_reviewer_refs(study_root)
    _write_ai_reviewer_currentness_inputs(study_root, eval_id=eval_id)
    _write_ai_reviewer_request(study_root, study_id=study_id, quest_id=quest_id, eval_id=eval_id)
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "eval_id": "publication-eval::stale-clean-migration",
            "study_id": study_id,
            "quest_id": quest_id,
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "publication_eval_ai_reviewer",
                "ai_reviewer_required": False,
            },
            "quality_assessment": {"medical_journal_prose_quality": {"status": "underdefined"}},
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
    from tests.domain_owner_action_dispatch_helpers import (
        dispatch as _dispatch,
        write_current_dispatch as _write_current_dispatch,
    )

    _write_current_dispatch(
        dispatch_path,
        profile,
        _dispatch(
            study_id=study_id,
            action_type="return_to_ai_reviewer_workflow",
            owner="ai_reviewer",
            required_output_surface="artifacts/publication_eval/latest.json",
        ),
    )
    monkeypatch.setattr(
        module,
        "_refresh_controller_decision_after_ai_reviewer_eval",
        lambda **_: {"refresh_status": "skipped", "skipped_reason": "unit_test"},
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    latest = json.loads((study_root / "artifacts" / "publication_eval" / "latest.json").read_text(encoding="utf-8"))

    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    assert latest["eval_id"] == eval_id
    assert latest["quality_assessment"]["medical_journal_prose_quality"]["status"] == "partial"
    assert latest["quality_assessment"]["medical_journal_prose_quality"]["evidence_refs"] == [
        refs["medical_prose_review"],
        refs["manuscript"],
    ]
    assert latest["reviewer_operating_system"]["currentness_checks"]["medical_prose_review"][
        "route_back_required"
    ] is True
