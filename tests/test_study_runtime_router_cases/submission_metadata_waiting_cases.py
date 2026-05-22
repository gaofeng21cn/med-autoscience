from .shared import *  # noqa: F403
from .submission_metadata_waiting_cases_cases.test_failed_reviewer_revision_explicit_relaunch import *  # noqa: F403,F401
from .submission_metadata_waiting_cases_cases.test_stopped_domain_transition_relaunch import *  # noqa: F403,F401


def test_stopped_submission_metadata_package_resumes_current_controller_work_unit(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
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
    write_submission_metadata_only_bundle(
        quest_root,
        blocking_item_ids=["author_metadata", "ethics_statement"],
    )
    write_synced_submission_delivery(study_root, quest_root)
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

    result = module.study_runtime_status(
        profile=profile,
        study_id=study_id,
        include_progress_projection=False,
    )

    assert result["quest_status"] == "stopped"
    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_waiting_opl_runtime_owner_route"
    assert result["interaction_arbitration"]["classification"] == "controller_work_unit_pending_redrive"


def test_stopped_submission_metadata_package_resumes_current_domain_transition_routeback(
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
    write_submission_metadata_only_bundle(
        quest_root,
        blocking_item_ids=["author_metadata", "ethics_statement"],
    )
    write_synced_submission_delivery(study_root, quest_root)
    write_text(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        json.dumps(
            {
                "schema_version": 1,
                "decision_id": "study-decision::dm002::route-back-analysis",
                "study_id": study_id,
                "quest_id": study_id,
                "emitted_at": "2099-01-01T00:00:01+00:00",
                "decision_type": "route_back_same_line",
                "route_target": "analysis-campaign",
                "requires_human_confirmation": False,
                "controller_actions": [
                    {
                        "action_type": "ensure_study_runtime",
                        "payload_ref": str(
                            study_root / "artifacts" / "controller_decisions" / "latest.json"
                        ),
                    }
                ],
                "next_work_unit": {
                    "unit_id": "unit_harmonized_validation_uncertainty_and_grouped_calibration",
                    "lane": "analysis-campaign",
                    "summary": (
                        "Add uncertainty intervals, grouped calibration evidence, and reproducibility "
                        "details to the unit-harmonized external validation."
                    ),
                },
                "work_unit_fingerprint": (
                    "domain-transition::route_back_same_line::"
                    "unit_harmonized_validation_uncertainty_and_grouped_calibration"
                ),
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
            "guard_boundary": {
                "runner_boundary": "mas_domain_read_model_only",
                "can_write_domain_truth": False,
                "can_execute_generic_state_machine": False,
                "opl_generic_runner_may_resume": False,
                "mas_owner_apply_receipt_required": False,
                "required_owner_surface": "artifacts/publication_eval/latest.json",
            },
            "source_refs": [
                "artifacts/publication_eval/latest.json",
                "artifacts/controller_decisions/latest.json",
                "study_runtime_status",
                "study_macro_state",
            ],
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

    result = module.study_runtime_status(
        profile=profile,
        study_id=study_id,
        include_progress_projection=False,
    )

    assert result["quest_status"] == "stopped"
    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_waiting_opl_runtime_owner_route"
    assert result["interaction_arbitration"]["classification"] == "domain_transition_runtime_redrive"


def test_study_runtime_status_treats_submission_metadata_only_waiting_quest_as_resumable(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"waiting_for_user"}\n')
    write_submission_metadata_only_bundle(
        quest_root,
        blocking_item_ids=[
            "author_metadata",
            "ethics_statement",
            "human_subjects_consent_statement",
            "ai_declaration",
        ],
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_waiting_for_submission_metadata"
    assert result["quest_status"] == "waiting_for_user"

def test_study_runtime_status_treats_submission_metadata_only_waiting_quest_as_resumable_when_checklist_uses_key(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"waiting_for_user"}\n')
    paper_root = quest_root / ".ds" / "worktrees" / "paper-main" / "paper"
    write_text(
        paper_root / "paper_bundle_manifest.json",
        json.dumps(
            {
                "schema_version": 1,
                "paper_branch": "paper/main",
                "compile_report_path": str(paper_root / "build" / "compile_report.json"),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(
        paper_root / "build" / "compile_report.json",
        json.dumps(
            {
                "schema_version": 1,
                "status": "compiled_with_open_submission_items",
                "author_metadata_status": "placeholder_external_input_required",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(
        paper_root / "review" / "submission_checklist.json",
        json.dumps(
            {
                "schema_version": 1,
                "status": "proof_ready_with_author_metadata_and_submission_declarations_pending",
                "blocking_items": [
                    {
                        "key": "author_metadata",
                        "status": "external_input_required",
                        "detail": "author metadata pending",
                    },
                    {
                        "key": "ethics_statement",
                        "status": "external_input_required",
                        "detail": "ethics statement pending",
                    },
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_waiting_for_submission_metadata"
    assert result["quest_status"] == "waiting_for_user"

def test_study_runtime_status_treats_external_metadata_gap_status_as_submission_metadata_only(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"waiting_for_user"}\n')
    paper_root = quest_root / ".ds" / "worktrees" / "paper-main" / "paper"
    write_text(
        paper_root / "paper_bundle_manifest.json",
        json.dumps(
            {
                "schema_version": 1,
                "paper_branch": "paper/main",
                "compile_report_path": str(paper_root / "build" / "compile_report.json"),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(
        paper_root / "build" / "compile_report.json",
        json.dumps(
            {
                "schema_version": 1,
                "status": "success",
                "author_metadata_status": "placeholder_external_input_required",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(
        paper_root / "review" / "submission_checklist.json",
        json.dumps(
            {
                "schema_version": 1,
                "overall_status": "pituitary_target_package_rebuilt_with_external_metadata_gap",
                "package_status": "auditable_package_ready_with_external_metadata_blocker",
                "blocking_items": [
                    "The title-page packet still needs externally confirmed final author order."
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_waiting_for_submission_metadata"
    assert result["quest_status"] == "waiting_for_user"

def test_study_runtime_status_parks_submission_metadata_only_waiting_quest_after_auditable_package_delivery(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"waiting_for_user"}\n')
    write_submission_metadata_only_bundle(
        quest_root,
        blocking_item_ids=[
            "author_metadata",
            "ethics_statement",
            "human_subjects_consent_statement",
            "ai_declaration",
        ],
    )
    write_synced_submission_delivery(study_root, quest_root)
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_waiting_for_submission_metadata"
    assert result["quest_status"] == "waiting_for_user"

def test_ensure_study_runtime_keeps_submission_metadata_only_waiting_quest_parked_after_auditable_package_delivery(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"waiting_for_user"}\n')
    write_submission_metadata_only_bundle(
        quest_root,
        blocking_item_ids=[
            "author_metadata",
            "ethics_statement",
            "human_subjects_consent_statement",
            "ai_declaration",
        ],
    )
    write_synced_submission_delivery(study_root, quest_root)
    calls: list[str] = []
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module,
        "_prepare_runtime_overlay",
        lambda *, profile, quest_root: calls.append("prepare_overlay") or make_runtime_overlay_result(),
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "update_quest_startup_context",
        lambda *, runtime_root, quest_id, startup_contract, requested_baseline_ref=None: calls.append("sync_context")
        or {"ok": True, "snapshot": {"quest_id": quest_id, "startup_contract": startup_contract}},
        raising=False,
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "resume_quest",
        lambda *, runtime_root, quest_id, source: calls.append("resume") or {"ok": True, "status": "active"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="runtime_watch")

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_waiting_for_submission_metadata"
    assert result["quest_status"] == "waiting_for_user"
    assert calls == ["prepare_overlay"]

def test_ensure_study_runtime_pauses_live_delivered_submission_package_milestone(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
    from tests.test_runtime_watch_cases.event_scan_helpers import ready_reviewer_operating_system

    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "running",
                "active_run_id": "run-live-package",
                "pending_user_message_count": 0,
            }
        )
        + "\n",
    )
    write_synced_submission_delivery(study_root, quest_root)
    write_text(study_root / "manuscript" / "current_package" / "figures" / "Figure1.png", "figure placeholder")
    write_text(study_root / "manuscript" / "current_package" / "tables" / "Table1.md", "table placeholder")
    write_text(
        study_root / "manuscript" / "current_package" / "audit" / "submission_manifest.json",
        json.dumps(
            {
                "schema_version": 1,
                "manuscript": {"surface_qc": {"status": "pass", "failures": []}},
                "figures": [{"id": "Figure1"}],
                "tables": [{"id": "Table1"}],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(
        study_root / "manuscript" / "current_package" / "SUBMISSION_TODO.md",
        "# Submission TODO\n\n- author affiliations\n- ethics approval number\n- conflict of interest\n",
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(decision_module.publication_gate_controller, "build_gate_state", lambda quest_root: object())
    monkeypatch.setattr(
        decision_module.publication_gate_controller,
        "build_gate_report",
        lambda state: {
            "schema_version": 1,
            "gate_kind": "publishability_control",
            "generated_at": "2026-04-17T02:04:11+00:00",
            "quest_id": "001-risk",
            "status": "clear",
            "allow_write": True,
            "blockers": [],
            "current_required_action": "continue_bundle_stage",
            "supervisor_phase": "bundle_stage_ready",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": False,
            "deferred_downstream_actions": [],
            "medical_prose_review_status": "ready",
            "controller_stage_note": "bundle-stage package is ready for human submission metadata handoff",
        },
    )
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    publication_eval_id = "publication-eval::001-risk::001-risk::ai-reviewer-current"
    write_text(
        publication_eval_path,
        json.dumps(
            {
                "schema_version": 1,
                "eval_id": publication_eval_id,
                "study_id": "001-risk",
                "quest_id": "001-risk",
                "emitted_at": "2026-04-17T02:04:12+00:00",
                "assessment_provenance": {
                    "owner": "ai_reviewer",
                    "source_kind": "publication_eval_ai_reviewer",
                    "policy_id": "medical_publication_critique_v1",
                    "ai_reviewer_required": False,
                },
                "quality_assessment": {
                    "medical_journal_prose_quality": {"status": "ready"},
                },
                "reviewer_operating_system": ready_reviewer_operating_system(
                    study_root,
                    publication_eval_path,
                    publication_eval_id,
                ),
                "verdict": {"overall_verdict": "promising"},
                "recommended_actions": [
                    {
                        "action_id": "publication-eval-action::continue_same_line::bundle-ready",
                        "action_type": "continue_same_line",
                        "work_unit_fingerprint": "bundle-ready",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "live",
            "source": "daemon_turn_worker",
            "active_run_id": "run-live-package",
            "runner_live": True,
            "bash_live": True,
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "daemon_turn_worker",
                "active_run_id": "run-live-package",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {"ok": True, "status": "none"},
        },
    )
    calls: list[tuple[str, str]] = []

    def fake_pause_quest(*, runtime_root: Path, quest_id: str, source: str, runtime_backend) -> dict[str, object]:
        calls.append(("pause", quest_id))
        return {"ok": True, "status": "paused"}

    monkeypatch.setattr(module, "_pause_quest", fake_pause_quest)

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "pause"
    assert result["reason"] == "quest_waiting_for_submission_metadata"
    assert result["quest_status"] == "paused"
    assert calls == [("pause", "001-risk")]


def test_study_runtime_status_parks_waiting_user_after_revision_intake_consumed_by_current_package(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
    task_intake_module = importlib.import_module("med_autoscience.study_task_intake")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "002-attribution",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical epidemiology framing is fixed around diabetes mortality attribution.",
        paper_urls=["https://example.org/paper-2"],
        journal_shortlist=["Diabetes Research and Clinical Practice", "BMJ Open Diabetes Research & Care"],
        minimum_sci_ready_evidence_package=["attribution_model", "cross_cohort_comparison"],
    )
    quest_root = profile.runtime_root / "002-attribution"
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "waiting_for_user",
                "active_run_id": None,
                "worker_running": False,
                "pending_user_message_count": 0,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "turn_closeout",
                "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
                "blocked_turn_closeout": {
                    "run_id": "run-stale-revision-closeout",
                    "blocked_reason": "controller_duplicate_eval_no_new_work_unit_artifact_delta",
                    "next_owner": "MAS/controller",
                    "closeout_path": str(
                        quest_root
                        / "artifacts"
                        / "runtime"
                        / "turn_closeouts"
                        / "run-stale-revision-closeout.json"
                    ),
                },
                "last_controller_decision_authorization": {
                    "source": "domain_route_scan_platform_repair",
                    "work_unit_id": "submission_authority_sync_closure",
                    "work_unit_fingerprint": "domain-transition::bundle_stage_finalize::submission_authority_sync_closure",
                    "route_target": "finalize",
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    task_intake_module.write_task_intake(
        profile=profile,
        study_id="002-attribution",
        study_root=study_root,
        entry_mode="full_research",
        task_intent="用户已对糖尿病002投稿包给出明确审稿式反馈，必须作为 reviewer_revision 重新激活同一论文线。",
        constraints=("完成前维持 audit preview only / not submission-ready 判断。",),
        first_cycle_outputs=("paper/rebuttal/review_matrix.md and action_plan.md covering all feedback items.",),
    )
    write_synced_submission_delivery(study_root, quest_root, include_submission_checklist=False)
    current_package_root = study_root / "manuscript" / "current_package"
    write_text(current_package_root / "figures" / "Figure1.png", "figure placeholder")
    write_text(current_package_root / "tables" / "Table1.md", "table placeholder")
    write_text(
        current_package_root / "audit" / "submission_manifest.json",
        json.dumps(
            {
                "schema_version": 1,
                "manuscript": {"surface_qc": {"status": "pass", "failures": []}},
                "figures": [{"figure_id": "Figure1"}],
                "tables": [{"table_id": "Table1"}],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(
        current_package_root / "SUBMISSION_TODO.md",
        "# Submission TODO\n\n- author affiliations\n- ethics approval number\n- conflict of interest\n",
    )
    delivery_manifest_path = study_root / "manuscript" / "delivery_manifest.json"
    delivery_manifest = json.loads(delivery_manifest_path.read_text(encoding="utf-8"))
    delivery_manifest["generated_at"] = "2099-01-01T00:00:00+00:00"
    delivery_manifest_path.write_text(json.dumps(delivery_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_text(
        study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json",
        json.dumps(
            {
                "emitted_at": "2099-01-01T00:01:00+00:00",
                "promotion_gate_status": {
                    "generated_at": "2099-01-01T00:00:30+00:00",
                    "status": "clear",
                    "allow_write": True,
                    "blockers": [],
                    "current_required_action": "continue_bundle_stage",
                    "supervisor_phase": "bundle_stage_ready",
                },
                "quality_closure_truth": {
                    "state": "bundle_only_remaining",
                    "current_required_action": "continue_bundle_stage",
                },
                "quality_review_loop": {"closure_state": "bundle_only_remaining"},
                "quality_assessment": {"human_review_readiness": {"status": "ready"}},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "002-attribution"),
    )
    monkeypatch.setattr(decision_module.publication_gate_controller, "build_gate_state", lambda quest_root: object())
    monkeypatch.setattr(
        decision_module.publication_gate_controller,
        "build_gate_report",
        lambda state: {
            "generated_at": "2099-01-01T00:00:30+00:00",
            "status": "clear",
            "allow_write": True,
            "blockers": [],
            "current_required_action": "continue_bundle_stage",
            "supervisor_phase": "bundle_stage_ready",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": False,
            "deferred_downstream_actions": [],
            "controller_stage_note": "bundle-stage work is unlocked and can proceed on the critical path",
        },
    )
    monkeypatch.setattr(
        module.study_runtime_protocol,
        "validate_startup_contract_resolution",
        lambda *, startup_contract: module.study_runtime_protocol.StartupContractValidation(
            status="clear",
            blockers=(),
            medical_analysis_contract_status="resolved",
            medical_reporting_contract_status="resolved",
            medical_analysis_reason_code=None,
            medical_reporting_reason_code=None,
        ),
    )

    result = module.study_runtime_status(
        profile=profile,
        study_id="002-attribution",
        include_progress_projection=False,
    )

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_waiting_for_submission_metadata"
    assert result["auto_runtime_parked"]["parked"] is True
    assert result["interaction_arbitration"]["classification"] == "domain_transition_terminal_or_handoff"
    assert result["interaction_arbitration"]["reason_code"] == "domain_transition_delivered_package_handoff"
    assert result["interaction_arbitration"]["domain_transition_decision_type"] == "delivered_package_handoff"
    assert result["interaction_arbitration"]["next_work_unit_id"] == "package_review_handoff"
