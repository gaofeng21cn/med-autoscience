from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_study_progress_projects_gate_specificity_as_controller_lane(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "002-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-002"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "study_id": "002-risk",
            "quest_id": "quest-002",
            "emitted_at": "2026-05-02T12:08:13+00:00",
            "verdict": {
                "overall_verdict": "blocked",
                "summary": (
                    "medical publication surface is blocked; route back to `analysis-campaign` "
                    "to close claim-evidence consistency gaps."
                ),
            },
            "gaps": [
                {
                    "gap_id": "gap-005",
                    "gap_type": "claim",
                    "severity": "must_fix",
                    "summary": "claim_evidence_consistency_failed",
                    "evidence_refs": [str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json")],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "publication-eval-action::return_to_controller::publication-blockers::specificity",
                    "action_type": "return_to_controller",
                    "priority": "now",
                    "reason": "Gate only named generic blocker labels.",
                    "requires_controller_decision": True,
                    "work_unit_fingerprint": "publication-blockers::specificity",
                    "next_work_unit": {
                        "unit_id": "gate_needs_specificity",
                        "lane": "controller",
                        "summary": (
                            "Ask the publication gate to identify concrete claim, display, evidence, "
                            "citation, metric, or package-artifact targets."
                        ),
                    },
                    "blocking_work_units": [
                        {
                            "unit_id": "gate_needs_specificity",
                            "lane": "controller",
                            "summary": "Ask the publication gate to identify concrete blocker targets.",
                        }
                    ],
                }
            ],
        },
    )
    _write_runtime_watch(quest_root)
    _write_bash_summary(quest_root)

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "002-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "quest_id": "quest-002",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "active",
            "decision": "blocked",
            "reason": "needs_specificity",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "controller_stage_note": "publication gate needs concrete blocker objects before dispatch.",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "监管心跳新鲜。",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="002-risk")

    assert result["intervention_lane"]["lane_id"] == "publication_gate_specificity_required"
    assert result["intervention_lane"]["recommended_action_id"] == "request_gate_specificity"
    assert result["intervention_lane"]["route_target"] == "controller"
    assert result["intervention_lane"]["work_unit_id"] == "gate_needs_specificity"
    assert result["intervention_lane"].get("route_target") != "analysis-campaign"
    assert result["operator_status_card"]["handling_state"] == "publication_gate_specificity_required"
    assert "普通分析" in result["operator_status_card"]["user_visible_verdict"]
    assert "claim/figure/table/metric/source path" in result["operator_status_card"]["next_confirmation_signal"]
    assert "current_package_freshness/latest.json" in result["operator_status_card"]["next_confirmation_signal"]


__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
