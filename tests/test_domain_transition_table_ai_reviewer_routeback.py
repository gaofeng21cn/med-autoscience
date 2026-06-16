from __future__ import annotations

import json
import hashlib
from pathlib import Path

from med_autoscience.controllers import study_domain_transition_table
from med_autoscience.controllers.owner_route_reconcile_parts import current_truth_owner
from med_autoscience.controllers.study_outer_loop_parts.domain_transition_actions import (
    domain_transition_recommended_action,
)
from tests.reviewer_os_fixture_helpers import (
    current_manuscript_routeback_record,
    current_manuscript_routeback_reviewer_os,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _current_ai_reviewer_route_back_eval(study_root: Path) -> dict:
    return {
        "eval_id": "publication-eval::dm002::current-route-back",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "ai_reviewer_required": False,
        },
        "verdict": {"overall_verdict": "blocked"},
        "quality_assessment": {
            "medical_journal_prose_quality": {
                "status": "blocked",
                "summary": "The manuscript needs same-line story repair.",
            }
        },
        "reviewer_operating_system": {
            "currentness_checks": {
                "medical_prose_review": {
                    "status": "current",
                    "request_digest": "sha256:request",
                    "manuscript_ref": str(study_root / "paper" / "manuscript.md"),
                    "manuscript_digest": "sha256:manuscript",
                    "route_back_required": True,
                    "route_target": "write",
                }
            }
        },
        "recommended_actions": [
            {
                "action_id": "ai-reviewer-action::return-to-write",
                "action_type": "route_back_same_line",
                "requires_controller_decision": True,
                "route_target": "write",
                "work_unit_fingerprint": "ai_reviewer_story_clean_external_validation_v3",
                "next_work_unit": {
                    "unit_id": "manuscript_story_repair",
                    "lane": "write",
                    "summary": "Rewrite the manuscript as a clean external-validation paper.",
                },
            }
        ],
    }


def test_current_ai_reviewer_write_routeback_does_not_project_reviewer_redrive_for_live_run(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    _write_json(
        study_root / study_domain_transition_table.PUBLICATION_EVAL_RELATIVE_PATH,
        _current_ai_reviewer_route_back_eval(study_root),
    )
    _write_json(
        study_root / study_domain_transition_table.CONTROLLER_DECISION_RELATIVE_PATH,
        {
            "decision_type": "continue_same_line",
            "route_target": "review",
            "next_work_unit": {"unit_id": "ai_reviewer_medical_prose_quality_review"},
        },
    )

    transition = study_domain_transition_table.project_domain_transition(
        study_id="dm002",
        study_root=study_root,
        status={},
        macro_state={},
        active_run_id="mas-run-dm002",
    )

    assert transition["decision_type"] == "active_domain_health_diagnostic"
    assert transition["owner"] == "med-autoscience"
    assert transition["controller_action"] == "domain_health_diagnostic"


def test_current_ai_reviewer_write_routeback_projects_same_line_write_handoff_when_not_live(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    _write_json(
        study_root / study_domain_transition_table.PUBLICATION_EVAL_RELATIVE_PATH,
        _current_ai_reviewer_route_back_eval(study_root),
    )

    transition = study_domain_transition_table.project_domain_transition(
        study_id="dm002",
        study_root=study_root,
        status={},
        macro_state={},
        active_run_id=None,
    )

    assert transition["decision_type"] == "route_back_same_line"
    assert transition["route_target"] == "write"
    assert transition["owner"] == "write"
    assert transition["next_work_unit"]["unit_id"] == "manuscript_story_repair"


def test_current_ai_reviewer_write_routeback_owner_route_has_explicit_target_surface(
    tmp_path: Path,
) -> None:
    from med_autoscience.runtime_control import owner_route as owner_route_part

    study_root = tmp_path / "study"
    _write_json(
        study_root / study_domain_transition_table.PUBLICATION_EVAL_RELATIVE_PATH,
        _current_ai_reviewer_route_back_eval(study_root),
    )

    action = domain_transition_recommended_action(
        study_id="dm002",
        study_root=study_root,
        status_payload={"study_id": "dm002", "study_root": str(study_root)},
        active_run_id=None,
    )

    route, actions = owner_route_part.route_and_decorate_actions(
        study_id="dm002",
        quest_id="dm002",
        status={
            "study_id": "dm002",
            "study_root": str(study_root),
            "study_truth_snapshot": {
                "truth_epoch": "truth-event-dm002",
                "source_signature": "truth-snapshot-dm002",
            },
        },
        progress={},
        actions=[action],
        blocked_reason=action["reason"],
        next_owner=action["route_target"],
        active_run_id=None,
    )

    assert route["target_surface"]["surface_ref"] == (
        "canonical manuscript story-surface delta or "
        "typed blocker:manuscript_story_surface_delta_missing"
    )
    assert route["target_surface_source"] == "owner_route.action_target_surface"
    assert actions[0]["owner_route"]["target_surface"] == route["target_surface"]


def test_gate_recheck_only_readiness_preempts_stale_write_routeback(tmp_path: Path) -> None:
    study_root = tmp_path / "study"
    publication_eval = _current_ai_reviewer_route_back_eval(study_root)
    publication_eval["verdict"] = {"overall_verdict": "mixed", "primary_claim_status": "partial"}
    publication_eval["quality_assessment"]["medical_journal_prose_quality"]["status"] = "partial"
    publication_eval["quality_assessment"]["medical_journal_prose_quality"][
        "summary"
    ] = "The manuscript is publication-shaped but gate replay remains required."
    publication_eval["reviewer_operating_system"]["currentness_checks"]["current_manuscript"] = {
        "status": "current",
        "manuscript_ref": str(study_root / "paper" / "manuscript.md"),
        "manuscript_digest": "sha256:manuscript",
    }
    publication_eval["reviewer_operating_system"]["claim_evidence_alignment"] = {
        "surface_kind": "claim_evidence_alignment_gate_v1",
        "status": "ready",
        "claim_count": 1,
        "aligned_claim_count": 1,
        "missing_required_fields": [],
        "blockers": [],
    }
    publication_eval["reviewer_operating_system"]["publication_quality_readiness"] = {
        "surface_kind": "publication_quality_authority_kernel_v1",
        "status": "blocked",
        "current_manuscript_digest": "sha256:manuscript",
        "review_request_digest": "sha256:request",
        "evidence_ledger_digest": "sha256:evidence",
        "claim_evidence_alignment_digest": "sha256:alignment",
        "rubric_version": "medical_publication_critique_v1",
        "owner_attempt_id": "ai-reviewer-publication-eval::current",
        "fail_closed_when_missing": True,
        "missing_required_fields": ["owner_authorized_publication_gate_recheck"],
    }

    _write_json(
        study_root / study_domain_transition_table.PUBLICATION_EVAL_RELATIVE_PATH,
        publication_eval,
    )

    transition = study_domain_transition_table.project_domain_transition(
        study_id="dm003",
        study_root=study_root,
        status={},
        macro_state={},
        active_run_id=None,
    )

    assert transition["decision_type"] == "publication_gate_blocker"
    assert transition["route_target"] == "review"
    assert transition["owner"] == "publication_gate"
    assert transition["controller_action"] == "run_gate_clearing_batch"
    assert transition["next_work_unit"]["unit_id"] == "publication_gate_replay"


def test_stale_current_manuscript_ai_reviewer_request_preempts_old_write_routeback(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    publication_eval = _current_ai_reviewer_route_back_eval(study_root)
    manuscript_path = study_root / "paper" / "draft.md"
    stale_record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260521T213722Z_publication_eval_record.json"
    )
    _write_json(
        study_root / study_domain_transition_table.PUBLICATION_EVAL_RELATIVE_PATH,
        publication_eval,
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "request_lifecycle": {
                "state": "requested",
                "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
                "stale_record_ref": str(stale_record_path),
                "required_currentness_refs": [str(manuscript_path)],
            },
        },
    )

    transition = study_domain_transition_table.project_domain_transition(
        study_id="dm002",
        study_root=study_root,
        status={},
        macro_state={},
        active_run_id=None,
    )

    assert transition["decision_type"] == "ai_reviewer_re_eval"
    assert transition["route_target"] == "review"
    assert transition["owner"] == "ai_reviewer"
    assert transition["controller_action"] == "return_to_ai_reviewer_workflow"
    assert transition["next_work_unit"]["unit_id"] == (
        "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
    )
    assert transition["typed_blocker"] is None
    assert str(stale_record_path) in transition["source_refs"]


def test_current_ai_reviewer_record_consumes_stale_input_request_before_write_routeback(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    manuscript_path = study_root / "paper" / "draft.md"
    evidence_path = study_root / "paper" / "evidence_ledger.json"
    claim_map_path = study_root / "paper" / "claim_evidence_map.json"
    manuscript_text = "# Draft\n\nCurrent manuscript with updated input ledgers.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    _write_json(evidence_path, {"updated": "current"})
    _write_json(claim_map_path, {"updated": "current"})
    old_eval = _current_ai_reviewer_route_back_eval(study_root)
    old_eval["eval_id"] = "publication-eval::dm002::old-inputs::2026-05-31T10:00:00+00:00"
    _write_json(study_root / study_domain_transition_table.PUBLICATION_EVAL_RELATIVE_PATH, old_eval)
    current_record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260601T131804Z_publication_eval_record.json"
    )
    current_record = current_manuscript_routeback_record(
        study_root=study_root,
        manuscript_path=manuscript_path,
        manuscript_text=manuscript_text,
        study_id="dm002",
        quest_id="dm002",
        eval_id="publication-eval::dm002::ai-reviewer-current-inputs::20260601T130009Z",
        emitted_at="2026-06-01T13:18:04+00:00",
    )
    current_record["assessment_provenance"].update(
        {
            "source_kind": "publication_eval_ai_reviewer",
            "source_refs": [
                str(manuscript_path.resolve()),
                str(evidence_path.resolve()),
                str(claim_map_path.resolve()),
            ],
        }
    )
    current_record["reviewer_operating_system"]["currentness_checks"]["evidence_ledger"] = {
        "status": "current",
        "ref": str(evidence_path.resolve()),
        "digest": _sha256_text(evidence_path.read_text(encoding="utf-8")),
    }
    current_record["reviewer_operating_system"]["currentness_checks"]["claim_evidence_map"] = {
        "status": "current",
        "ref": str(claim_map_path.resolve()),
        "digest": _sha256_text(claim_map_path.read_text(encoding="utf-8")),
    }
    current_record["recommended_actions"] = [
        {
            "action_id": "A1_consume_current_ai_reviewer_record_then_gate_replay",
            "action_type": "route_back_same_line",
            "priority": "now",
            "reason": "Consume this current AI reviewer record and route the manuscript back to write.",
            "requires_controller_decision": True,
            "route_target": "write",
            "next_work_unit": {
                "unit_id": "consume_current_ai_reviewer_record_then_prose_gate_package_replay",
                "lane": "write",
                "summary": "Consume the current AI reviewer record, refresh durable medical-prose currentness, replay publication gate logic, and only then evaluate package/readiness surfaces.",
            },
        }
    ]
    _write_json(current_record_path, current_record)
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "request_lifecycle": {
                "state": "requested",
                "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
                "stale_record_ref": str(
                    study_root
                    / "artifacts"
                    / "publication_eval"
                    / "ai_reviewer_responses"
                    / "20260601T121132Z_publication_eval_record.json"
                ),
                "required_currentness_refs": [
                    str(evidence_path.resolve()),
                    str(claim_map_path.resolve()),
                ],
            },
        },
    )

    transition = study_domain_transition_table.project_domain_transition(
        study_id="dm002",
        study_root=study_root,
        status={},
        macro_state={},
        active_run_id=None,
    )

    assert transition["decision_type"] == "route_back_same_line"
    assert transition["route_target"] == "write"
    assert transition["owner"] == "write"
    assert transition["controller_action"] == "request_opl_stage_attempt"
    assert transition["next_work_unit"]["unit_id"] == (
        "consume_current_ai_reviewer_record_then_prose_gate_package_replay"
    )
    assert transition["completion_receipt_consumption"]["receipt_ref"] == str(current_record_path.resolve())
    assert str(current_record_path.resolve()) in transition["source_refs"]


def test_current_ai_reviewer_write_action_preempts_stale_prose_review_route_target_when_not_live(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    publication_eval = _current_ai_reviewer_route_back_eval(study_root)
    publication_eval["reviewer_operating_system"]["currentness_checks"]["medical_prose_review"][
        "route_target"
    ] = "analysis"
    publication_eval["reviewer_operating_system"]["route_back_decision"] = {
        "recommended_action": "route_back_same_line",
        "rationale": "The current AI reviewer action routes same-line paper repair to write.",
    }
    _write_json(
        study_root / study_domain_transition_table.PUBLICATION_EVAL_RELATIVE_PATH,
        publication_eval,
    )

    transition = study_domain_transition_table.project_domain_transition(
        study_id="dm002",
        study_root=study_root,
        status={},
        macro_state={},
        active_run_id=None,
    )

    assert transition["decision_type"] == "route_back_same_line"
    assert transition["route_target"] == "write"
    assert transition["owner"] == "write"
    assert transition["next_work_unit"]["unit_id"] == "manuscript_story_repair"


def test_current_ai_reviewer_analysis_routeback_projects_analysis_campaign_handoff_when_not_live(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    publication_eval = _current_ai_reviewer_route_back_eval(study_root)
    prose_check = publication_eval["reviewer_operating_system"]["currentness_checks"]["medical_prose_review"]
    prose_check["route_target"] = "analysis-campaign"
    publication_eval["recommended_actions"] = [
        {
            "action_id": "ai-reviewer-action::return-to-analysis-campaign",
            "action_type": "route_back_same_line",
            "requires_controller_decision": True,
            "route_target": "analysis-campaign",
            "work_unit_fingerprint": "unit_harmonized_validation_uncertainty_and_grouped_calibration",
            "next_work_unit": {
                "unit_id": "unit_harmonized_validation_uncertainty_and_grouped_calibration",
                "lane": "analysis-campaign",
                "summary": "Close uncertainty intervals and grouped calibration for the unit-harmonized validation.",
            },
        }
    ]
    _write_json(
        study_root / study_domain_transition_table.PUBLICATION_EVAL_RELATIVE_PATH,
        publication_eval,
    )

    transition = study_domain_transition_table.project_domain_transition(
        study_id="dm002",
        study_root=study_root,
        status={},
        macro_state={},
        active_run_id=None,
    )

    assert transition["decision_type"] == "route_back_same_line"
    assert transition["route_target"] == "analysis-campaign"
    assert transition["owner"] == "analysis-campaign"
    assert transition["next_work_unit"]["unit_id"] == "unit_harmonized_validation_uncertainty_and_grouped_calibration"


def test_current_ai_reviewer_bounded_analysis_routeback_accepts_analysis_alias_when_not_live(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    publication_eval = _current_ai_reviewer_route_back_eval(study_root)
    publication_eval["quality_assessment"]["medical_journal_prose_quality"]["status"] = "partial"
    prose_check = publication_eval["reviewer_operating_system"]["currentness_checks"]["medical_prose_review"]
    prose_check["route_target"] = "analysis"
    publication_eval["recommended_actions"] = [
        {
            "action_id": "route-back-analysis-validation-uncertainty-20260520",
            "action_type": "bounded_analysis",
            "requires_controller_decision": True,
            "route_target": "analysis-campaign",
            "work_unit_fingerprint": "unit_harmonized_validation_uncertainty_and_grouped_calibration",
            "next_work_unit": {
                "unit_id": "unit_harmonized_validation_uncertainty_and_grouped_calibration",
                "lane": "analysis-campaign",
                "summary": "Add uncertainty intervals and grouped calibration evidence.",
            },
        }
    ]
    _write_json(
        study_root / study_domain_transition_table.PUBLICATION_EVAL_RELATIVE_PATH,
        publication_eval,
    )

    transition = study_domain_transition_table.project_domain_transition(
        study_id="dm002",
        study_root=study_root,
        status={},
        macro_state={},
        active_run_id=None,
    )

    assert transition["decision_type"] == "route_back_same_line"
    assert transition["route_target"] == "analysis-campaign"
    assert transition["owner"] == "analysis-campaign"
    assert transition["next_work_unit"]["unit_id"] == "unit_harmonized_validation_uncertainty_and_grouped_calibration"


def test_current_ai_reviewer_record_transition_refs_are_json_serializable(tmp_path: Path) -> None:
    study_root = tmp_path / "study"
    manuscript_path = study_root / "paper" / "draft.md"
    manuscript_text = "# Draft\n\nCurrent manuscript with updated 95% CIs.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    old_eval = _current_ai_reviewer_route_back_eval(study_root)
    old_eval["eval_id"] = "publication-eval::dm002::old::2026-05-22T20:30:41+00:00::ai-reviewer"
    old_eval["emitted_at"] = "2026-05-22T20:30:41+00:00"
    _write_json(study_root / study_domain_transition_table.PUBLICATION_EVAL_RELATIVE_PATH, old_eval)
    current_record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260524T175827Z_publication_eval_record.json"
    )
    current_record = _current_ai_reviewer_route_back_eval(study_root)
    current_record.update(
        {
            "eval_id": "publication-eval::dm002::new::2026-05-24T17:58:27+00:00::ai-reviewer",
            "emitted_at": "2026-05-24T17:58:27+00:00",
            "future_facing_limitations_plan": [
                {
                    "limitation": "External validation remains observational.",
                    "impact_on_claim": "Use restrained validation wording.",
                    "required_future_analysis_data_or_design": "Independent implementation validation.",
                    "current_manuscript_wording_must_be_restrained": True,
                }
            ],
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
            "reviewer_operating_system": current_manuscript_routeback_reviewer_os(
                study_root=study_root,
                manuscript_path=manuscript_path,
                manuscript_text=manuscript_text,
                eval_id="publication-eval::dm002::new::2026-05-24T17:58:27+00:00::ai-reviewer",
            ),
            "recommended_actions": [
                {
                    "action_id": "route-back-same-line-current-publication-hardening-dm002-20260524T175827Z",
                    "action_type": "route_back_same_line",
                    "requires_controller_decision": True,
                    "route_target": "write",
                    "work_unit_fingerprint": (
                        "dm002_current_ai_reviewer_publication_eval_live_draft_"
                        "2dcd51592c6a_20260524T175827Z"
                    ),
                    "next_work_unit": {
                        "unit_id": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                        "lane": "write",
                        "summary": "Harden the current manuscript against the current AI reviewer record.",
                    },
                }
            ],
        }
    )
    current_record["assessment_provenance"]["source_kind"] = "publication_eval_ai_reviewer"
    _write_json(current_record_path, current_record)

    transition = study_domain_transition_table.project_domain_transition(
        study_id="dm002",
        study_root=study_root,
        status={},
        macro_state={},
        active_run_id=None,
    )

    json.dumps(transition, ensure_ascii=False, sort_keys=True)
    assert str(current_record_path.resolve()) in transition["source_refs"]
    assert all(isinstance(ref, str) for ref in transition["source_refs"])
    expected_consumption = {
        "status": "consumed",
        "receipt_kind": "ai_reviewer_publication_eval",
        "receipt_ref": str(current_record_path.resolve()),
        "eval_id": current_record["eval_id"],
        "reviewer_trace_ref": f"{current_record_path.resolve()}#reviewer_operating_system",
        "next_action": "honor_ai_reviewer_publication_eval_authority",
    }
    for key, value in expected_consumption.items():
        assert transition["completion_receipt_consumption"][key] == value
    assert transition["completion_receipt_consumption"]["owner_route_currentness_basis"][
        "work_unit_fingerprint"
    ] == "dm002_current_ai_reviewer_publication_eval_live_draft_2dcd51592c6a_20260524T175827Z"


def test_current_ai_reviewer_routeback_materializes_outer_loop_controller_action(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    publication_eval = _current_ai_reviewer_route_back_eval(study_root)
    publication_eval["quality_assessment"]["medical_journal_prose_quality"]["status"] = "partial"
    prose_check = publication_eval["reviewer_operating_system"]["currentness_checks"]["medical_prose_review"]
    prose_check["route_target"] = "analysis"
    publication_eval["recommended_actions"] = [
        {
            "action_id": "route-back-analysis-validation-uncertainty-20260520",
            "action_type": "bounded_analysis",
            "requires_controller_decision": True,
            "route_target": "analysis-campaign",
            "work_unit_fingerprint": "unit_harmonized_validation_uncertainty_and_grouped_calibration",
            "next_work_unit": {
                "unit_id": "unit_harmonized_validation_uncertainty_and_grouped_calibration",
                "lane": "analysis-campaign",
                "summary": "Add uncertainty intervals and grouped calibration evidence.",
            },
        }
    ]
    _write_json(
        study_root / study_domain_transition_table.PUBLICATION_EVAL_RELATIVE_PATH,
        publication_eval,
    )

    action = domain_transition_recommended_action(
        study_id="dm002",
        study_root=study_root,
        status_payload={"study_id": "dm002", "quest_id": "dm002"},
        active_run_id=None,
    )

    assert action is not None
    assert action["action_type"] == "route_back_same_line"
    assert action["controller_action_type"] == "run_quality_repair_batch"
    assert action["route_target"] == "analysis-campaign"
    assert (
        action["work_unit_fingerprint"]
        == "domain-transition::route_back_same_line::unit_harmonized_validation_uncertainty_and_grouped_calibration"
    )
    assert action["next_work_unit"]["unit_id"] == "unit_harmonized_validation_uncertainty_and_grouped_calibration"


def test_current_ai_reviewer_routeback_controller_route_accepts_domain_transition_fingerprint(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    publication_eval = _current_ai_reviewer_route_back_eval(study_root)
    publication_eval["quality_assessment"]["medical_journal_prose_quality"]["status"] = "partial"
    prose_check = publication_eval["reviewer_operating_system"]["currentness_checks"]["medical_prose_review"]
    prose_check["route_target"] = "analysis"
    publication_eval["recommended_actions"] = [
        {
            "action_id": "route-back-analysis-validation-uncertainty-20260520",
            "action_type": "bounded_analysis",
            "requires_controller_decision": True,
            "route_target": "analysis-campaign",
            "work_unit_fingerprint": "unit_harmonized_validation_uncertainty_and_grouped_calibration",
            "next_work_unit": {
                "unit_id": "unit_harmonized_validation_uncertainty_and_grouped_calibration",
                "lane": "analysis-campaign",
                "summary": "Add uncertainty intervals and grouped calibration evidence.",
            },
        }
    ]
    _write_json(
        study_root / study_domain_transition_table.PUBLICATION_EVAL_RELATIVE_PATH,
        publication_eval,
    )
    decision_path = study_root / study_domain_transition_table.CONTROLLER_DECISION_RELATIVE_PATH
    _write_json(
        decision_path,
        {
            "decision_id": "study-decision::dm002::route-back",
            "decision_type": "route_back_same_line",
            "route_target": "analysis-campaign",
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "run_quality_repair_batch", "payload_ref": str(decision_path)}],
            "work_unit_fingerprint": (
                "domain-transition::route_back_same_line::"
                "unit_harmonized_validation_uncertainty_and_grouped_calibration"
            ),
            "next_work_unit": {
                "unit_id": "unit_harmonized_validation_uncertainty_and_grouped_calibration",
                "lane": "analysis-campaign",
                "summary": "Add uncertainty intervals and grouped calibration evidence.",
            },
        },
    )

    route = current_truth_owner.current_controller_runtime_route(
        study_root=study_root,
        publication_eval_payload=publication_eval,
    )

    assert route is not None
    assert route["route_target"] == "analysis-campaign"
    assert route["work_unit_id"] == "unit_harmonized_validation_uncertainty_and_grouped_calibration"


def test_materialized_controller_write_route_preempts_stale_ai_reviewer_projection(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    manuscript_path = study_root / "paper" / "draft.md"
    manuscript_text = "# Draft\n\nCurrent manuscript still needs medical prose repair.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    old_eval = _current_ai_reviewer_route_back_eval(study_root)
    old_eval["eval_id"] = "publication-eval::dm003::old-readiness-blocker"
    _write_json(study_root / study_domain_transition_table.PUBLICATION_EVAL_RELATIVE_PATH, old_eval)
    current_record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260616T015951Z_publication_eval_record.json"
    )
    current_record = current_manuscript_routeback_record(
        study_root=study_root,
        manuscript_path=manuscript_path,
        manuscript_text=manuscript_text,
        study_id="dm003",
        quest_id="dm003",
        eval_id="publication-eval::dm003::current-ai-reviewer-no-routeback-action",
        emitted_at="2026-06-16T01:59:51+00:00",
    )
    current_record["recommended_actions"] = []
    _write_json(current_record_path, current_record)
    _write_json(
        study_root / study_domain_transition_table.CONTROLLER_DECISION_RELATIVE_PATH,
        {
            "schema_version": 1,
            "decision_id": "dm003-controller-route-back-write",
            "decision_type": "route_back_same_line",
            "study_id": "dm003",
            "quest_id": "dm003",
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "run_quality_repair_batch"}],
            "route_target": "write",
            "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
            "next_work_unit": {
                "unit_id": "medical_prose_write_repair",
                "lane": "write",
                "summary": "Repair medical prose against the current AI reviewer record.",
            },
        },
    )

    transition = study_domain_transition_table.project_domain_transition(
        study_id="dm003",
        study_root=study_root,
        status={},
        macro_state={},
        active_run_id=None,
    )

    assert transition["decision_type"] == "route_back_same_line"
    assert transition["route_target"] == "write"
    assert transition["owner"] == "write"
    assert transition["controller_action"] == "request_opl_stage_attempt"
    assert transition["next_work_unit"]["unit_id"] == "medical_prose_write_repair"
    assert str(current_record_path.resolve()) in transition["source_refs"]
    assert str((study_root / study_domain_transition_table.CONTROLLER_DECISION_RELATIVE_PATH).resolve()) in transition[
        "source_refs"
    ]


def test_current_ai_reviewer_write_routeback_preempts_consumed_story_recheck_request(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    publication_eval = _current_ai_reviewer_route_back_eval(study_root)
    publication_eval["eval_id"] = "publication-eval::dm002::current-ai-reviewer-write-repair"
    publication_eval["recommended_actions"] = [
        {
            "action_id": "dm002-current-ai-reviewer-write-repair",
            "action_type": "route_back_same_line",
            "requires_controller_decision": True,
            "route_target": "write",
            "work_unit_fingerprint": "dm002_same_line_publication_paper_repair_20260521",
            "next_work_unit": {
                "unit_id": "dm002_same_line_publication_paper_repair",
                "lane": "write",
                "summary": "Repair current AI reviewer paper-surface findings.",
            },
        }
    ]
    _write_json(
        study_root / study_domain_transition_table.PUBLICATION_EVAL_RELATIVE_PATH,
        publication_eval,
    )
    _write_json(
        study_root / "artifacts" / "controller" / "publication_work_unit_lifecycle" / "latest.json",
        {
            "schema_version": 1,
            "source_eval_id": publication_eval["eval_id"],
            "status": "blocked",
            "work_unit": {"unit_id": "manuscript_story_repair"},
            "unit_statuses": [
                {"unit_id": "repair_paper_live_paths", "status": "current"},
                {"unit_id": "materialize_display_surface", "status": "materialized"},
            ],
            "gate_replay_status": "blocked",
        },
    )
    ai_reviewer_request_path = (
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    )
    _write_json(ai_reviewer_request_path, {"request_id": "ai-reviewer-recheck::dm002"})
    publication_eval["assessment_provenance"]["source_refs"] = [str(ai_reviewer_request_path)]
    _write_json(
        study_root / study_domain_transition_table.PUBLICATION_EVAL_RELATIVE_PATH,
        publication_eval,
    )
    _write_json(
        study_root / study_domain_transition_table.REPAIR_EXECUTION_EVIDENCE_RELATIVE_PATH,
        {
            "schema_version": 1,
            "status": "progress_delta_candidate",
            "review_finding": {"source_eval_id": publication_eval["eval_id"]},
            "repair_work_unit": {"unit_id": "manuscript_story_repair"},
            "ai_reviewer_recheck_required": True,
            "ai_reviewer_recheck_done": True,
            "ai_reviewer_recheck_request_ref": str(ai_reviewer_request_path),
            "manuscript_surface_hygiene": {
                "status": "clear",
                "blockers": [],
                "story_surface_delta_required": True,
                "story_surface_delta_present": True,
                "story_surface_delta_refs": [
                    {
                        "path": str(study_root / "paper" / "draft.md"),
                        "artifact_role": "canonical_manuscript_story_surface",
                    }
                ],
            },
            "blockers": [],
        },
    )

    transition = study_domain_transition_table.project_domain_transition(
        study_id="dm002",
        study_root=study_root,
        status={},
        macro_state={},
        active_run_id=None,
    )

    assert transition["decision_type"] == "route_back_same_line"
    assert transition["route_target"] == "write"
    assert transition["owner"] == "write"
    assert transition["controller_action"] == "request_opl_stage_attempt"
    assert transition["next_work_unit"]["unit_id"] == "dm002_same_line_publication_paper_repair"
