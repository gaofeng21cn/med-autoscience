from __future__ import annotations

from tests.test_study_runtime_router_cases.shared import *  # noqa: F403


def test_execute_runtime_decision_returns_terminal_outcome_for_completed_status(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(profile.workspace_root, "001-risk")

    resolved_study_id, resolved_study_root, study_payload = module._resolve_study(
        profile=profile,
        study_id="001-risk",
        study_root=None,
    )
    status = module._status_state(
        profile=profile,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        study_payload=study_payload,
        entry_mode=None,
    )
    status.set_decision("completed", "quest_already_completed")
    context = module._build_execution_context(
        profile=profile,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        study_payload=study_payload,
        source="test",
    )

    outcome = module._execute_runtime_decision(status=status, context=context)

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.COMPLETED
    assert outcome.daemon_result is None
    assert outcome.startup_payload_path is None


def test_execute_resume_runtime_decision_records_nested_resume_daemon_step(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    transport = _managed_runtime_transport(module)
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
        paper_framing_summary="Prediction framing is fixed.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    status = module.ProgressProjectionStatus.from_payload(
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(profile.workspace_root / "studies" / "001-risk"),
            "entry_mode": "full_research",
            "execution": {"quest_id": "001-risk", "auto_resume": True},
            "quest_id": "001-risk",
            "quest_root": str(profile.runtime_root / "001-risk"),
            "quest_exists": True,
            "quest_status": "paused",
            "runtime_binding_path": str(profile.workspace_root / "studies" / "001-risk" / "runtime_binding.yaml"),
            "runtime_binding_exists": False,
            "workspace_contracts": {"overall_ready": True},
            "startup_data_readiness": {"status": "clear"},
            "startup_boundary_gate": {"allow_compute_stage": True},
            "runtime_reentry_gate": {"allow_runtime_entry": True},
            "study_completion_contract": {"status": "absent", "ready": False},
            "controller_first_policy_summary": "summary",
            "automation_ready_summary": "ready",
            "decision": "resume",
            "reason": "quest_paused",
        }
    )
    context = module._build_execution_context(
        profile=profile,
        study_id="001-risk",
        study_root=profile.workspace_root / "studies" / "001-risk",
        study_payload=yaml.safe_load((profile.workspace_root / "studies" / "001-risk" / "study.yaml").read_text(encoding="utf-8")),
        source="test",
    )

    monkeypatch.setattr(
        module,
        "_sync_existing_quest_startup_context",
        lambda **kwargs: {
            "ok": True,
            "snapshot": {
                "quest_id": kwargs["quest_id"],
                "startup_contract": kwargs["create_payload"]["startup_contract"],
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_run_startup_hydration",
        lambda **kwargs: (
            module.study_runtime_protocol.StartupHydrationReport.from_payload(
                make_startup_hydration_report(kwargs["quest_root"])
            ),
            module.study_runtime_protocol.StartupHydrationValidationReport.from_payload(
                make_startup_hydration_validation_report(kwargs["quest_root"])
            ),
        ),
    )
    monkeypatch.setattr(
        transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: {"ok": True, "status": "running"},
    )

    outcome = module._execute_resume_runtime_decision(status=status, context=context)

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.RESUME
    assert outcome.daemon_result == {"resume": {"ok": True, "status": "running"}}
    assert outcome.daemon_step("resume") == {"ok": True, "status": "running"}
    assert status.quest_status is module.StudyRuntimeQuestStatus.RUNNING


def test_execute_resume_runtime_decision_materializes_fresh_domain_transition_before_resume(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    outer_loop = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    transport = _managed_runtime_transport(module)
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    write_text(quest_root / "quest.yaml", f"quest_id: {study_id}\nstudy_id: {study_id}\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "paused",
                "quest_id": study_id,
                "active_run_id": None,
                "pending_user_message_count": 0,
                "last_controller_decision_authorization": {
                    "decision_id": "stale-publication-gate-recheck",
                    "controller_actions": ["run_gate_clearing_batch"],
                    "route_target": "review",
                    "work_unit_id": "publication_gate_recheck",
                    "work_unit_fingerprint": "publication-gate-recheck::stale",
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    charter_ref = {
        "charter_id": f"charter::{study_id}::v1",
        "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
    }
    write_text(
        study_root / "artifacts" / "controller" / "study_charter.json",
        json.dumps({"charter_id": charter_ref["charter_id"]}, ensure_ascii=False, indent=2) + "\n",
    )
    publication_eval_ref = {
        "eval_id": "publication-eval::003::current",
        "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
    }
    write_text(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        json.dumps(
            {
                "schema_version": 1,
                "eval_id": publication_eval_ref["eval_id"],
                "study_id": study_id,
                "quest_id": study_id,
                "assessment_provenance": {
                    "owner": "mechanical_projection",
                    "ai_reviewer_required": True,
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    runtime_escalation_ref = {
        "record_id": "runtime-escalation::003::current",
        "artifact_path": str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
        "summary_ref": str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
    }
    write_text(
        Path(runtime_escalation_ref["artifact_path"]),
        json.dumps(
            {
                "schema_version": 1,
                "record_id": runtime_escalation_ref["record_id"],
                "study_id": study_id,
                "quest_id": study_id,
                "emitted_at": "2026-05-21T15:28:06+00:00",
                "trigger": {"trigger_id": "domain_transition_ai_reviewer_re_eval", "source": "progress_projection"},
                "scope": "quest",
                "severity": "study",
                "reason": "domain_transition_ai_reviewer_re_eval",
                "recommended_actions": ["return_to_ai_reviewer_workflow"],
                "evidence_refs": [publication_eval_ref["artifact_path"]],
                "runtime_context_refs": {},
                "summary_ref": runtime_escalation_ref["summary_ref"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    controller_decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    write_text(
        controller_decision_path,
        json.dumps(
            {
                "schema_version": 1,
                "decision_id": "stale-publication-gate-recheck",
                "study_id": study_id,
                "quest_id": study_id,
                "emitted_at": "2026-05-20T16:24:17+00:00",
                "decision_type": "route_back_same_line",
                "charter_ref": charter_ref,
                "runtime_escalation_ref": runtime_escalation_ref,
                "publication_eval_ref": publication_eval_ref,
                "requires_human_confirmation": False,
                "controller_actions": [
                    {"action_type": "run_gate_clearing_batch", "payload_ref": str(controller_decision_path)}
                ],
                "reason": "Stale gate recheck must not authorize the next runtime turn.",
                "route_target": "review",
                "route_key_question": "Recheck publication gate.",
                "route_rationale": "Old gate lifecycle route.",
                "work_unit_fingerprint": "publication-gate-recheck::stale",
                "next_work_unit": {
                    "unit_id": "publication_gate_recheck",
                    "lane": "review",
                    "summary": "Replay stale publication gate.",
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    fresh_fingerprint = "domain-transition::ai_reviewer_re_eval::ai_reviewer_medical_prose_quality_review"
    fresh_next_work_unit = {
        "unit_id": "ai_reviewer_medical_prose_quality_review",
        "lane": "review",
        "summary": "Re-run AI reviewer manuscript-quality review after the latest reviewer revision intake.",
    }
    tick_request = {
        "study_root": study_root,
        "charter_ref": charter_ref,
        "publication_eval_ref": publication_eval_ref,
        "decision_type": "continue_same_line",
        "route_target": "review",
        "route_key_question": "当前稿件是否已经通过 AI reviewer-owned publication evaluation？",
        "route_rationale": "Mechanical or stale publication projection cannot authorize quality closure.",
        "source_route_key_question": None,
        "requires_human_confirmation": False,
        "controller_actions": [
            {"action_type": "return_to_ai_reviewer_workflow", "payload_ref": str(controller_decision_path)}
        ],
        "reason": fresh_next_work_unit["summary"],
        "work_unit_fingerprint": fresh_fingerprint,
        "next_work_unit": fresh_next_work_unit,
        "blocking_work_units": [fresh_next_work_unit],
    }
    materialized_calls: list[dict[str, object]] = []

    def fake_materialize_non_dispatching_outer_loop_decision(**kwargs: object) -> dict[str, object]:
        materialized_calls.append(dict(kwargs))
        write_text(
            controller_decision_path,
            json.dumps(
                {
                    "schema_version": 1,
                    "decision_id": "fresh-domain-transition-ai-reviewer",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "emitted_at": "2026-05-21T15:28:06+00:00",
                    "decision_type": "continue_same_line",
                    "charter_ref": charter_ref,
                    "runtime_escalation_ref": runtime_escalation_ref,
                    "publication_eval_ref": publication_eval_ref,
                    "requires_human_confirmation": False,
                    "controller_actions": tick_request["controller_actions"],
                    "reason": tick_request["reason"],
                    "route_target": "review",
                    "route_key_question": tick_request["route_key_question"],
                    "route_rationale": tick_request["route_rationale"],
                    "work_unit_fingerprint": fresh_fingerprint,
                    "next_work_unit": fresh_next_work_unit,
                    "blocking_work_units": [fresh_next_work_unit],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
        )
        return {
            "dispatch_status": "recorded_non_dispatching",
            "study_decision_ref": {"artifact_path": str(controller_decision_path)},
        }

    status = module.ProgressProjectionStatus.from_payload(
        {
            "schema_version": 1,
            "study_id": study_id,
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {"quest_id": study_id, "auto_resume": True},
            "quest_id": study_id,
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "paused",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": False,
            "workspace_contracts": {"overall_ready": True},
            "startup_data_readiness": {"status": "clear"},
            "startup_boundary_gate": {"allow_compute_stage": True},
            "runtime_reentry_gate": {"allow_runtime_entry": True},
            "study_completion_contract": {"status": "absent", "ready": False},
            "controller_first_policy_summary": "summary",
            "automation_ready_summary": "ready",
            "decision": "resume",
            "reason": "domain_transition_ai_reviewer_re_eval",
            "domain_transition": {
                "decision_type": "ai_reviewer_re_eval",
                "route_target": "review",
                "next_work_unit": fresh_next_work_unit,
                "controller_action": "return_to_ai_reviewer_workflow",
                "owner": "ai_reviewer",
            },
            "runtime_escalation_ref": runtime_escalation_ref,
        }
    )
    context = module._build_execution_context(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        study_payload=yaml.safe_load((study_root / "study.yaml").read_text(encoding="utf-8")),
        source="test",
    )

    monkeypatch.setattr(
        module,
        "_sync_existing_quest_startup_context",
        lambda **kwargs: {
            "ok": True,
            "snapshot": {
                "quest_id": kwargs["quest_id"],
                "startup_contract": kwargs["create_payload"]["startup_contract"],
            },
        },
    )
    monkeypatch.setattr(outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: tick_request)
    monkeypatch.setattr(
        outer_loop,
        "materialize_non_dispatching_outer_loop_decision",
        fake_materialize_non_dispatching_outer_loop_decision,
    )

    def fake_resume_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, object]:
        decision = json.loads(controller_decision_path.read_text(encoding="utf-8"))
        assert decision["decision_id"] == "fresh-domain-transition-ai-reviewer"
        assert decision["controller_actions"][0]["action_type"] == "return_to_ai_reviewer_workflow"
        assert decision["next_work_unit"]["unit_id"] == "ai_reviewer_medical_prose_quality_review"
        return {"ok": True, "status": "running"}

    monkeypatch.setattr(transport, "resume_quest", fake_resume_quest)

    outcome = module._execute_resume_runtime_decision(status=status, context=context)

    assert materialized_calls
    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.RESUME
    assert status.to_dict()["controller_decision_currentness"]["status"] == "materialized"
    assert status.quest_status is module.StudyRuntimeQuestStatus.RUNNING


@pytest.mark.parametrize(
    ("resume_reason",),
    [
        ("quest_marked_running_but_no_live_session",),
        ("quest_parked_on_unchanged_finalize_state",),
    ],
)
def test_execute_resume_runtime_decision_skips_startup_hydration_for_managed_runtime_recovery(
    monkeypatch,
    tmp_path: Path,
    resume_reason: str,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    transport = _managed_runtime_transport(module)
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
        paper_framing_summary="Prediction framing is fixed.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    status = module.ProgressProjectionStatus.from_payload(
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(profile.workspace_root / "studies" / "001-risk"),
            "entry_mode": "full_research",
            "execution": {"quest_id": "001-risk", "auto_resume": True},
            "quest_id": "001-risk",
            "quest_root": str(profile.runtime_root / "001-risk"),
            "quest_exists": True,
            "quest_status": "active",
            "runtime_binding_path": str(profile.workspace_root / "studies" / "001-risk" / "runtime_binding.yaml"),
            "runtime_binding_exists": False,
            "workspace_contracts": {"overall_ready": True},
            "startup_data_readiness": {"status": "clear"},
            "startup_boundary_gate": {"allow_compute_stage": True},
            "runtime_reentry_gate": {"allow_runtime_entry": True},
            "study_completion_contract": {"status": "absent", "ready": False},
            "controller_first_policy_summary": "summary",
            "automation_ready_summary": "ready",
            "decision": "resume",
                "reason": resume_reason,
            }
        )
    context = module._build_execution_context(
        profile=profile,
        study_id="001-risk",
        study_root=profile.workspace_root / "studies" / "001-risk",
        study_payload=yaml.safe_load((profile.workspace_root / "studies" / "001-risk" / "study.yaml").read_text(encoding="utf-8")),
        source="test",
    )

    monkeypatch.setattr(
        module,
        "_sync_existing_quest_startup_context",
        lambda **kwargs: {
            "ok": True,
            "snapshot": {
                "quest_id": kwargs["quest_id"],
                "startup_contract": kwargs["create_payload"]["startup_contract"],
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_run_startup_hydration",
        lambda **kwargs: pytest.fail("startup hydration should not run for managed runtime recovery"),
    )
    monkeypatch.setattr(
        transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: {"ok": True, "status": "running"},
    )

    outcome = module._execute_resume_runtime_decision(status=status, context=context)

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.RESUME
    assert outcome.daemon_result == {"resume": {"ok": True, "status": "running"}}
    assert outcome.daemon_step("resume") == {"ok": True, "status": "running"}
    assert status.quest_status is module.StudyRuntimeQuestStatus.RUNNING


def test_execute_resume_runtime_decision_blocks_when_resume_request_has_no_effect(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    transport = _managed_runtime_transport(module)
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    status = module.ProgressProjectionStatus.from_payload(
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(profile.workspace_root / "studies" / "001-risk"),
            "entry_mode": "full_research",
            "execution": {"quest_id": "001-risk", "auto_resume": True},
            "quest_id": "001-risk",
            "quest_root": str(profile.runtime_root / "001-risk"),
            "quest_exists": True,
            "quest_status": "waiting_for_user",
            "runtime_binding_path": str(profile.workspace_root / "studies" / "001-risk" / "runtime_binding.yaml"),
            "runtime_binding_exists": False,
            "workspace_contracts": {"overall_ready": True},
            "startup_data_readiness": {"status": "clear"},
            "startup_boundary_gate": {"allow_compute_stage": True},
            "runtime_reentry_gate": {"allow_runtime_entry": True},
            "study_completion_contract": {"status": "absent", "ready": False},
            "controller_first_policy_summary": "summary",
            "automation_ready_summary": "ready",
            "decision": "resume",
            "reason": "quest_waiting_on_invalid_blocking",
            "interaction_arbitration": {
                "classification": "invalid_blocking",
                "action": "resume",
                "requires_user_input": False,
            },
        }
    )
    context = module._build_execution_context(
        profile=profile,
        study_id="001-risk",
        study_root=profile.workspace_root / "studies" / "001-risk",
        study_payload=yaml.safe_load((profile.workspace_root / "studies" / "001-risk" / "study.yaml").read_text(encoding="utf-8")),
        source="test",
    )

    monkeypatch.setattr(
        module,
        "_sync_existing_quest_startup_context",
        lambda **kwargs: {
            "ok": True,
            "snapshot": {
                "quest_id": kwargs["quest_id"],
                "startup_contract": kwargs["create_payload"]["startup_contract"],
            },
        },
    )
    monkeypatch.setattr(
        transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: {
            "ok": True,
            "quest_id": quest_id,
            "scheduled": False,
            "started": False,
            "queued": False,
            "snapshot": {
                "status": "waiting_for_user",
                "active_run_id": None,
            },
        },
    )

    outcome = module._execute_resume_runtime_decision(status=status, context=context)

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.BLOCKED
    assert status.decision is module.StudyRuntimeDecision.BLOCKED
    assert status.reason is module.StudyRuntimeReason.RESUME_REQUEST_FAILED
    assert status.quest_status is module.StudyRuntimeQuestStatus.WAITING_FOR_USER
    assert status.to_dict()["resume_postcondition"] == {
        "effective": False,
        "failure_mode": "waiting_state_preserved",
        "snapshot_status": "waiting_for_user",
        "active_run_id": None,
        "scheduled": False,
        "started": False,
        "queued": False,
    }
