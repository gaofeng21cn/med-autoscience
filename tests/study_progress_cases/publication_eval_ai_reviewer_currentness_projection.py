from __future__ import annotations

from .shared import (
    Path,
    datetime,
    importlib,
    json,
    make_profile,
    timezone,
    write_study,
    _write_bash_summary,
    _write_domain_health_diagnostic,
    _write_json,
    _write_publication_eval,
    _write_publishability_gate_report,
    _write_runtime_escalation,
    _write_study_charter_and_controller_summary,
)


_AI_REVIEWER_DIMENSIONS = (
    "clinical_significance",
    "evidence_strength",
    "novelty_positioning",
    "medical_journal_prose_quality",
    "human_review_readiness",
)


def _valid_reviewer_operating_system(study_root: Path, quest_root: Path, *, eval_id: str) -> dict[str, object]:
    manuscript_ref = str(study_root / "paper" / "draft.md")
    evidence_ref = str(study_root / "paper" / "evidence_ledger.json")
    review_ref = str(study_root / "paper" / "review" / "review_ledger.json")
    medical_prose_ref = str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json")
    return {
        "contract_id": "medical_publication_ai_reviewer_os_v1",
        "input_bundle": {
            "manuscript": manuscript_ref,
            "study_charter": str(study_root / "artifacts" / "controller" / "study_charter.json"),
            "evidence_ledger": evidence_ref,
            "review_ledger": review_ref,
            "medical_manuscript_blueprint": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
            "claim_evidence_map": str(study_root / "paper" / "claim_evidence_map.json"),
            "medical_prose_review": medical_prose_ref,
            "publication_gate_projection": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        },
        "rubric_scores": {
            dimension: {
                "status": "ready",
                "rationale": f"{dimension} is current.",
                "evidence_refs": [manuscript_ref, evidence_ref],
            }
            for dimension in _AI_REVIEWER_DIMENSIONS
        },
        "decision_matrix": [
            {
                "dimension": dimension,
                "status": "ready",
                "rationale": f"{dimension} is current.",
            }
            for dimension in _AI_REVIEWER_DIMENSIONS
        ],
        "currentness_checks": {
            "medical_prose_review": {
                "status": "current",
                "request_digest": "sha256:" + "a" * 64,
                "manuscript_ref": manuscript_ref,
                "manuscript_digest": "sha256:" + "c" * 64,
            },
            "current_package_freshness": {
                "status": "fresh",
                "source_eval_id": eval_id,
            },
        },
        "future_facing_limitations_plan": [
            {
                "limitation": "Review authorization is scoped to the current manuscript snapshot.",
                "impact_on_claim": "No claim may exceed the reviewed manuscript evidence.",
                "required_future_analysis_data_or_design": "Repeat AI reviewer evaluation after substantive manuscript changes.",
                "current_manuscript_wording_must_be_restrained": True,
            }
        ],
        "provenance_checks": {
            "assessment_owner": "ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "ai_reviewer_required": False,
            "mechanical_projection_used_as_quality_authority": False,
        },
        "route_back_decision": {
            "recommended_action": "continue_same_line",
            "rationale": "AI reviewer-backed publication quality is current.",
        },
    }


def test_study_progress_does_not_overwrite_ai_reviewer_publication_eval_with_gate_projection(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    _write_study_charter_and_controller_summary(study_root)
    publication_eval_path = _write_publication_eval(
        study_root,
        quest_root,
        assessment_provenance={
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "source_refs": [str(study_root / "paper" / "draft.md")],
            "ai_reviewer_required": False,
        },
        recommended_actions=[
            {
                "action_id": "publication-eval-action::continue_same_line::publication-blockers::finalize",
                "action_type": "continue_same_line",
                "priority": "now",
                "reason": "AI reviewer already closed publication-facing quality.",
                "evidence_refs": [str(study_root / "paper" / "draft.md")],
                "route_target": "finalize",
                "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                "route_rationale": "AI reviewer-backed bundle-stage closure is current.",
                "requires_controller_decision": True,
                "next_work_unit": {
                    "unit_id": "submission_authority_sync_closure",
                    "lane": "controller",
                    "summary": "Synchronize submission authority and package closure for the bundle-stage.",
                },
                "work_unit_fingerprint": "domain-transition::bundle_stage_finalize::submission_authority_sync_closure",
            }
        ],
        quality_assessment={
            "clinical_significance": {
                "status": "ready",
                "summary": "Clinical question is reviewer-ready.",
                "evidence_refs": [str(study_root / "paper" / "draft.md")],
            },
            "evidence_strength": {
                "status": "ready",
                "summary": "Evidence is reviewer-ready.",
                "evidence_refs": [str(study_root / "paper" / "evidence_ledger.json")],
            },
            "novelty_positioning": {
                "status": "ready",
                "summary": "Novelty boundary is reviewer-ready.",
                "evidence_refs": [str(study_root / "artifacts" / "controller" / "study_charter.json")],
            },
            "medical_journal_prose_quality": {
                "status": "ready",
                "summary": "Medical prose is reviewer-ready.",
                "evidence_refs": [str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json")],
            },
            "human_review_readiness": {
                "status": "ready",
                "summary": "Human review package is reviewer-ready.",
                "evidence_refs": [str(study_root / "paper" / "review" / "review_ledger.json")],
            },
        },
    )
    ai_reviewer_eval = json.loads(publication_eval_path.read_text(encoding="utf-8"))
    eval_id = "publication-eval::001-risk::quest-001::2026-04-12T09:45:00+00:00"
    ai_reviewer_eval.update(
        {
            "eval_id": eval_id,
            "emitted_at": "2026-04-12T09:45:00+00:00",
            "verdict": {
                "overall_verdict": "promising",
                "primary_claim_status": "supported",
                "summary": "AI reviewer-backed publication quality is current.",
                "stop_loss_pressure": "none",
            },
            "gaps": [
                {
                    "gap_id": "gap-optional",
                    "gap_type": "delivery",
                    "severity": "optional",
                    "summary": "Package closure remains a controller-stage task.",
                    "evidence_refs": [str(study_root / "paper")],
                }
            ],
            "reviewer_operating_system": _valid_reviewer_operating_system(study_root, quest_root, eval_id=eval_id),
        }
    )
    _write_json(publication_eval_path, ai_reviewer_eval)
    _write_runtime_escalation(quest_root, study_root)
    _write_domain_health_diagnostic(quest_root)
    gate_report_path = _write_publishability_gate_report(quest_root)
    gate_report = json.loads(gate_report_path.read_text(encoding="utf-8"))
    gate_report.update(
        {
            "generated_at": "2026-04-12T09:50:00+00:00",
            "status": "clear",
            "allow_write": True,
            "recommended_action": "continue_per_gate",
            "blockers": [],
            "study_delivery_status": "current",
            "study_delivery_stale_reason": None,
            "current_required_action": "continue_bundle_stage",
            "controller_stage_note": "bundle-stage work is unlocked and can proceed on the critical path",
        }
    )
    _write_json(gate_report_path, gate_report)
    _write_bash_summary(quest_root)

    monkeypatch.setattr(
        module,
        "_progress_freshness_now",
        lambda: datetime(2026, 4, 12, 10, 0, tzinfo=timezone.utc),
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "study_completion_contract": {},
            "decision": "noop",
            "reason": "quest_already_running",
            "publication_supervisor_state": {
                "supervisor_phase": "bundle_stage_ready",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": False,
                "current_required_action": "continue_bundle_stage",
                "controller_stage_note": "bundle-stage work is unlocked and can proceed on the critical path",
            },
            "execution_owner_guard": {
                "owner": "managed_runtime",
                "supervisor_only": True,
                "active_run_id": "run-001",
                "current_required_action": "supervise_runtime_only",
                "publication_gate_allows_direct_write": True,
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "MAS 外环监管心跳新鲜。",
                "latest_recorded_at": "2026-04-12T09:59:00+00:00",
            },
        },
    )

    module.read_study_progress(profile=profile, study_id="001-risk")
    refreshed_publication_eval = json.loads(publication_eval_path.read_text(encoding="utf-8"))

    assert refreshed_publication_eval["assessment_provenance"]["owner"] == "ai_reviewer"
    assert refreshed_publication_eval["assessment_provenance"]["source_kind"] == "publication_eval_ai_reviewer"
    assert refreshed_publication_eval["assessment_provenance"]["ai_reviewer_required"] is False
    assert refreshed_publication_eval["reviewer_operating_system"]["contract_id"] == "medical_publication_ai_reviewer_os_v1"
    assert refreshed_publication_eval["emitted_at"] == "2026-04-12T09:45:00+00:00"
    assert refreshed_publication_eval["recommended_actions"][0]["next_work_unit"]["unit_id"] == "submission_authority_sync_closure"


def test_publication_runtime_refresh_does_not_demote_ai_reviewer_eval_to_mechanical_projection(
    monkeypatch,
    tmp_path: Path,
) -> None:
    publication_runtime = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.publication_runtime"
    )
    study_root = tmp_path / "study"
    quest_root = tmp_path / "runtime" / "quests" / "quest-001"
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    gate_report_path = quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"
    _write_json(
        publication_eval_path,
        {
            "schema_version": 1,
            "eval_id": "publication-eval::001-risk::quest-001::2026-04-12T09:45:00+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-04-12T09:45:00+00:00",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "publication_eval_ai_reviewer",
                "policy_id": "medical_publication_critique_v1",
                "source_refs": [str(study_root / "paper" / "draft.md")],
                "ai_reviewer_required": False,
            },
            "verdict": {
                "overall_verdict": "promising",
                "primary_claim_status": "supported",
                "summary": "AI reviewer-backed publication quality is current.",
                "stop_loss_pressure": "none",
            },
            "quality_assessment": {},
            "gaps": [],
            "recommended_actions": [],
            "quality_assessment": {
                "medical_journal_prose_quality": {
                    "status": "ready",
                    "summary": "Medical prose is reviewer-current.",
                    "evidence_refs": [
                        str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json")
                    ],
                }
            },
            "reviewer_operating_system": _valid_reviewer_operating_system(
                study_root,
                quest_root,
                eval_id="publication-eval::001-risk::quest-001::2026-04-12T09:45:00+00:00",
            ),
        },
    )
    _write_json(
        gate_report_path,
        {
            "schema_version": 1,
            "gate_kind": "publishability_control",
            "generated_at": "2026-04-12T09:50:00+00:00",
            "status": "clear",
            "allow_write": True,
            "blockers": [],
            "current_required_action": "continue_bundle_stage",
            "controller_stage_note": "bundle-stage work is unlocked and can proceed on the critical path",
        },
    )

    class MechanicalDecisionModule:
        @staticmethod
        def _materialize_publication_eval_from_gate_report(**_: object) -> None:
            _write_json(
                publication_eval_path,
                {
                    "schema_version": 1,
                    "eval_id": "publication-eval::001-risk::quest-001::2026-04-12T09:50:00+00:00",
                    "study_id": "001-risk",
                    "quest_id": "quest-001",
                    "emitted_at": "2026-04-12T09:50:00+00:00",
                    "assessment_provenance": {
                        "owner": "mechanical_projection",
                        "source_kind": "publication_gate_report",
                        "ai_reviewer_required": True,
                    },
                    "verdict": {"overall_verdict": "promising"},
                    "quality_assessment": {},
                    "gaps": [],
                    "recommended_actions": [],
                },
            )

    real_import_module = publication_runtime.import_module

    def fake_import_module(name: str):
        if name == "med_autoscience.controllers.study_runtime_decision":
            return MechanicalDecisionModule
        return real_import_module(name)

    monkeypatch.setattr(publication_runtime, "import_module", fake_import_module)

    publication_runtime._refresh_publication_surfaces_from_gate_report(
        study_root=study_root,
        study_id="001-risk",
        quest_root=quest_root,
        quest_id="quest-001",
        publication_eval_path=publication_eval_path,
        runtime_escalation_path=None,
        domain_health_diagnostic_payload=None,
    )
    refreshed_publication_eval = json.loads(publication_eval_path.read_text(encoding="utf-8"))

    assert refreshed_publication_eval["assessment_provenance"]["owner"] == "ai_reviewer"
    assert refreshed_publication_eval["assessment_provenance"]["ai_reviewer_required"] is False
    assert refreshed_publication_eval["reviewer_operating_system"]["contract_id"] == "medical_publication_ai_reviewer_os_v1"
    assert refreshed_publication_eval["emitted_at"] == "2026-04-12T09:45:00+00:00"


__all__ = [name for name in globals() if name.startswith("test_")]
