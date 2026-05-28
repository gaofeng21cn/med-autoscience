from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path

from med_autoscience.publication_eval_reviewer_os import (
    validate_ai_reviewer_operating_system_trace,
)
from tests.reviewer_os_fixture_helpers import current_manuscript_routeback_reviewer_os
from tests.study_runtime_test_helpers import make_profile, write_study


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_reviewer_os_requires_currentness_source_eval_package_and_route_target(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    manuscript_path = study_root / "paper" / "draft.md"
    manuscript_text = "# Draft\n\nCurrent manuscript.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    eval_id = "publication-eval::dm002::current::2026-05-28T08:00:00+00:00::ai-reviewer"
    reviewer_os = current_manuscript_routeback_reviewer_os(
        study_root=study_root,
        manuscript_path=manuscript_path,
        manuscript_text=manuscript_text,
        eval_id=eval_id,
    )

    assert validate_ai_reviewer_operating_system_trace(reviewer_os) == []

    missing_source_eval = dict(reviewer_os)
    missing_source_eval["currentness_checks"] = dict(reviewer_os["currentness_checks"])
    missing_source_eval["currentness_checks"].pop("source_eval")
    assert (
        "reviewer_operating_system.currentness_checks.source_eval must be non-empty"
        in validate_ai_reviewer_operating_system_trace(missing_source_eval)
    )

    stale_manuscript = dict(reviewer_os)
    stale_manuscript["currentness_checks"] = dict(reviewer_os["currentness_checks"])
    stale_manuscript["currentness_checks"]["current_manuscript"] = {
        **reviewer_os["currentness_checks"]["current_manuscript"],
        "status": "stale",
    }
    assert (
        "reviewer_operating_system.currentness_checks.current_manuscript.status must be current"
        in validate_ai_reviewer_operating_system_trace(stale_manuscript)
    )

    missing_route_target = dict(reviewer_os)
    missing_route_target["route_back_decision"] = dict(reviewer_os["route_back_decision"])
    missing_route_target["route_back_decision"].pop("route_target")
    assert (
        "reviewer_operating_system.route_back_decision.route_target must name the current route target"
        in validate_ai_reviewer_operating_system_trace(missing_route_target)
    )

    mismatched_package = dict(reviewer_os)
    mismatched_package["currentness_checks"] = dict(reviewer_os["currentness_checks"])
    mismatched_package["currentness_checks"]["current_package_freshness"] = {
        **reviewer_os["currentness_checks"]["current_package_freshness"],
        "source_eval_id": "publication-eval::older",
    }
    assert (
        "reviewer_operating_system.currentness_checks.current_package_freshness.source_eval_id "
        "must match source_eval.eval_id"
        in validate_ai_reviewer_operating_system_trace(mismatched_package)
    )


def test_invalid_current_ai_reviewer_response_record_does_not_supersede_latest_eval(
    tmp_path: Path,
) -> None:
    canonical_inputs = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.canonical_inputs"
    )
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    manuscript_path = study_root / "paper" / "draft.md"
    manuscript_text = "# Draft\n\nCurrent manuscript with updated 95% CIs.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    latest_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::old::2026-05-22T20:30:41+00:00::ai-reviewer",
        "study_id": study_id,
        "quest_id": quest_id,
        "emitted_at": "2026-05-22T20:30:41+00:00",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "quality_assessment": {"medical_journal_prose_quality": {"status": "blocked"}},
        "recommended_actions": [],
    }
    latest_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(latest_path, latest_eval)
    invalid_record = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::new-invalid::2026-05-24T17:58:27+00:00::ai-reviewer",
        "study_id": study_id,
        "quest_id": quest_id,
        "emitted_at": "2026-05-24T17:58:27+00:00",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "quality_assessment": {
            dimension: {"status": "blocked", "summary": f"{dimension} requires hardening."}
            for dimension in (
                "clinical_significance",
                "evidence_strength",
                "novelty_positioning",
                "medical_journal_prose_quality",
                "human_review_readiness",
            )
        },
        "future_facing_limitations_plan": [
            {
                "limitation": "External validation remains observational.",
                "impact_on_claim": "Use restrained validation wording.",
                "required_future_analysis_data_or_design": "Independent implementation validation.",
                "current_manuscript_wording_must_be_restrained": True,
            }
        ],
        "reviewer_operating_system": {
            "currentness_checks": {
                "medical_prose_review": {
                    "status": "stale_for_live_manuscript",
                    "used_as_context_not_clearance": True,
                },
                "current_manuscript": {
                    "status": "current",
                    "manuscript_ref": str(manuscript_path.resolve()),
                    "manuscript_digest": _sha256_text(manuscript_text),
                    "reviewed_at": "2026-05-24T17:58:27+00:00",
                },
            }
        },
        "recommended_actions": [
            {
                "action_id": "route-back-same-line-current-publication-hardening-dm002-20260524T175827Z",
                "action_type": "route_back_same_line",
                "requires_controller_decision": True,
                "route_target": "write",
                "work_unit_fingerprint": "dm002-invalid-record-should-not-route",
                "next_work_unit": {
                    "unit_id": "dm002_invalid_record_should_not_route",
                    "lane": "write",
                    "summary": "This invalid record must not drive owner routing.",
                },
            }
        ],
    }
    invalid_record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260524T175827Z_publication_eval_record.json"
    )
    _write_json(invalid_record_path, invalid_record)

    selected = canonical_inputs.publication_eval_payload(
        {"study_id": study_id, "study_root": str(study_root), "publication_eval": latest_eval},
        {
            "study_id": study_id,
            "study_root": str(study_root),
            "refs": {"publication_eval_path": str(latest_path)},
        },
    )

    assert selected["eval_id"] == latest_eval["eval_id"]
    assert selected.get("_projection_source_kind") is None
