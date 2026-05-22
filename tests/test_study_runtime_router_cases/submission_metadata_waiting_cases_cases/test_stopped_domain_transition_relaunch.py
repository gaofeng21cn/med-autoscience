from __future__ import annotations

from tests.test_study_runtime_router_cases.shared import *  # noqa: F403


def test_allow_stopped_relaunch_reopens_current_domain_transition_routeback(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision_status_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_decision_parts.domain_status_authority"
    )

    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(
        profile.workspace_root,
        study_id,
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="External validation framing needs unit-harmonized calibration evidence.",
        paper_urls=["https://example.org/paper-2"],
        journal_shortlist=["Diabetes Research and Clinical Practice"],
        minimum_sci_ready_evidence_package=["external_validation", "calibration"],
    )
    quest_root = profile.runtime_root / study_id
    write_text(quest_root / "quest.yaml", f"quest_id: {study_id}\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "stopped",
                "active_run_id": None,
                "worker_running": False,
                "pending_user_message_count": 0,
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "controller_work_unit_pending",
                "last_controller_decision_authorization": {
                    "authorization_basis": "controller_domain_transition",
                    "decision_id": "study-decision::dm002::route-back-analysis",
                    "source": "domain_route_scan_platform_repair",
                    "route_target": "analysis-campaign",
                    "work_unit_id": "unit_harmonized_validation_uncertainty_and_grouped_calibration",
                    "work_unit_fingerprint": (
                        "domain-transition::route_back_same_line::"
                        "unit_harmonized_validation_uncertainty_and_grouped_calibration"
                    ),
                    "controller_actions": ["ensure_study_runtime"],
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )

    def fake_record_domain_transition_if_required(*, status, study_root):
        status.extras["domain_transition"] = {
            "study_id": study_id,
            "decision_type": "route_back_same_line",
            "route_target": "analysis-campaign",
            "next_work_unit": {
                "unit_id": "unit_harmonized_validation_uncertainty_and_grouped_calibration",
                "lane": "analysis-campaign",
                "summary": (
                    "Add uncertainty intervals, grouped calibration evidence, and reproducibility "
                    "details to the unit-harmonized external validation."
                ),
            },
            "controller_action": "ensure_study_runtime",
            "owner": "analysis-campaign",
            "typed_blocker": None,
        }

    monkeypatch.setattr(
        decision_status_module,
        "record_domain_transition_if_required",
        fake_record_domain_transition_if_required,
    )
    monkeypatch.setattr(
        module,
        "inspect_workspace_contracts",
        lambda profile: {
            "overall_ready": True,
            "runtime_contract": {"ready": True},
            "launcher_contract": {"ready": True},
            "behavior_gate": {"ready": True, "phase_25_ready": True},
        },
    )
    monkeypatch.setattr(
        module.startup_data_readiness_controller,
        "startup_data_readiness",
        lambda *, workspace_root: _clear_readiness_report(workspace_root, study_id),
    )
    monkeypatch.setattr(
        module,
        "_resume_quest",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("controller-authorized stopped redrive must not call resume_quest")
        ),
    )
    monkeypatch.setattr(
        module,
        "_relaunch_stopped_quest",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("controller-authorized stopped redrive must be handed to OPL runtime owner")
        ),
    )

    result = module.ensure_study_runtime(
        profile=profile,
        study_id=study_id,
        allow_stopped_relaunch=True,
        source="domain_route_scan_platform_repair",
    )

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_waiting_opl_runtime_owner_route"
    assert result["quest_status"] == "stopped"
    assert result["interaction_arbitration"]["classification"] == "domain_transition_runtime_redrive"
