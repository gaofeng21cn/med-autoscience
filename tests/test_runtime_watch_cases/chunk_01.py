from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_applies_new_blocker_once(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[tuple[str, bool]] = []

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append((quest_root.name, apply))
        return {
            "status": "blocked",
            "blockers": ["missing_post_main_publishability_gate"],
            "allow_write": False,
            "missing_non_scalar_deliverables": ["calibration_plot"],
            "submission_minimal_present": False,
            "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
            "intervention_enqueued": apply,
        }

    result = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"publication_gate": fake_runner},
        apply=True,
    )

    assert calls == [("q001", False), ("q001", True)]
    assert result["controllers"]["publication_gate"]["action"] == "applied"
def test_watch_runtime_materializes_outer_loop_decision_for_autonomous_continue_same_line(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation"],
    )
    quest_root = profile.runtime_root / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(quest_root, study_root)
    runtime_event_ref = _write_runtime_event_record(
        quest_root,
        study_root,
        runtime_escalation_ref=runtime_escalation_ref,
    )
    publication_eval_ref = _write_publication_eval(study_root, quest_root)
    _write_charter(study_root)
    status_payload = {
        **make_study_runtime_status_payload(
            study_id="001-risk",
            decision="blocked",
            reason="quest_stopped_requires_explicit_rerun",
        ),
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(quest_root),
        "quest_status": "stopped",
        "execution": {
            "engine": "med-deepscientist",
            "auto_entry": "on_managed_research_intent",
            "quest_id": "quest-001",
            "auto_resume": True,
        },
        "runtime_escalation_ref": runtime_escalation_ref,
        "runtime_event_ref": runtime_event_ref,
        "publication_supervisor_state": {
            "supervisor_phase": "write_stage_ready",
            "phase_owner": "publication_gate",
            "current_required_action": "continue_write_stage",
        },
    }
    ensure_calls: list[tuple[str, bool]] = []

    def fake_ensure(**kwargs):
        ensure_calls.append((str(kwargs.get("source") or "").strip(), bool(kwargs.get("allow_stopped_relaunch"))))
        if kwargs.get("source") == "runtime_watch":
            return status_payload
        if kwargs.get("source") == "runtime_watch_outer_loop_wakeup":
            return {
                "decision": "relaunch_stopped",
                "reason": "quest_stopped_requires_explicit_rerun",
            }
        raise AssertionError(f"unexpected ensure source: {kwargs.get('source')}")

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fake_ensure)
    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    first = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )
    second = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    latest_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    payload = json.loads(latest_path.read_text(encoding="utf-8"))
    watch_latest = json.loads(
        (quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json").read_text(encoding="utf-8")
    )

    assert ensure_calls == [
        ("runtime_watch", False),
        ("runtime_watch_outer_loop_wakeup", True),
        ("runtime_watch", False),
    ]
    assert first["managed_study_actions"][0]["study_id"] == "001-risk"
    assert second["managed_study_actions"][0]["study_id"] == "001-risk"
    assert first["managed_study_outer_loop_dispatches"] == [
        {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "decision_type": "continue_same_line",
            "route_target": "write",
            "route_key_question": "What is the narrowest same-line manuscript repair or continuation step required now?",
            "controller_action_type": "ensure_study_runtime_relaunch_stopped",
            "study_decision_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
            "dispatch_status": "executed",
            "source": "runtime_watch_outer_loop_wakeup",
        }
    ]
    assert second["managed_study_outer_loop_dispatches"] == []
    assert watch_latest["managed_study_outer_loop_dispatch"] == first["managed_study_outer_loop_dispatches"][0]
    assert payload["decision_type"] == "continue_same_line"
    assert payload["requires_human_confirmation"] is False
    assert payload["reason"] == "Controller should continue the same study line."
    assert payload["publication_eval_ref"] == publication_eval_ref
    assert payload["runtime_escalation_ref"] == runtime_escalation_ref
    assert payload["controller_actions"] == [
        {
            "action_type": "ensure_study_runtime_relaunch_stopped",
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]
def test_watch_runtime_autoparks_ready_submission_milestone_without_runtime_escalation_ref(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    (study_root / "artifacts" / "controller" / "study_charter.json").unlink()
    quest_root = profile.runtime_root / "quest-001"
    _write_charter(study_root)
    dump_json(
        study_root / "artifacts" / "runtime" / "last_launch_report.json",
        {
            "recorded_at": "2026-04-05T06:10:00+00:00",
            "decision": "noop",
            "reason": "quest_already_running",
            "quest_status": "running",
        },
    )
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    dump_json(
        publication_eval_path,
        {
            "schema_version": 1,
            "eval_id": "publication-eval::001-risk::quest-001::2026-04-05T05:58:00+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-04-05T05:58:00+00:00",
            "evaluation_scope": "publication",
            "charter_context_ref": {
                "ref": str((study_root / "artifacts" / "controller" / "study_charter.json").resolve()),
                "charter_id": "charter::001-risk::v1",
                "publication_objective": "risk stratification external validation",
            },
            "runtime_context_refs": {
                "runtime_escalation_ref": str(
                    (quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json").resolve()
                ),
                "main_result_ref": str((quest_root / "artifacts" / "results" / "main_result.json").resolve()),
            },
            "delivery_context_refs": {
                "paper_root_ref": str((study_root / "paper").resolve()),
                "submission_minimal_ref": str(
                    (study_root / "paper" / "submission_minimal" / "submission_manifest.json").resolve()
                ),
            },
            "verdict": {
                "overall_verdict": "promising",
                "primary_claim_status": "supported",
                "summary": "Human-review package is ready and only bundle-stage cleanup remains.",
                "stop_loss_pressure": "none",
            },
            "gaps": [
                {
                    "gap_id": "gap-001",
                    "gap_type": "reporting",
                    "severity": "optional",
                    "summary": "Only optional submission-bundle cleanup remains.",
                    "evidence_refs": [str(publication_eval_path)],
                }
            ],
            "quality_assessment": {
                "clinical_significance": {
                    "status": "ready",
                    "summary": "Clinical question is already publication-ready.",
                    "evidence_refs": [str(publication_eval_path)],
                    "reviewer_reason": "Clinical framing is stable.",
                    "reviewer_revision_advice": "Only minor bundle cleanup remains.",
                    "reviewer_next_round_focus": "Keep the clinician-facing framing consistent across surfaces.",
                },
                "evidence_strength": {
                    "status": "ready",
                    "summary": "Evidence chain is already closed.",
                    "evidence_refs": [str(publication_eval_path)],
                    "reviewer_reason": "Evidence posture is stable.",
                    "reviewer_revision_advice": "Only refresh delivery surfaces if needed.",
                    "reviewer_next_round_focus": "Keep evidence references synchronized across package surfaces.",
                },
                "novelty_positioning": {
                    "status": "ready",
                    "summary": "Contribution boundary is already explicit.",
                    "evidence_refs": [str(publication_eval_path)],
                    "reviewer_reason": "Novelty framing is fixed.",
                    "reviewer_revision_advice": "Do not expand the claim boundary.",
                    "reviewer_next_round_focus": "Keep contribution wording aligned with the frozen charter.",
                },
                "human_review_readiness": {
                    "status": "ready",
                    "summary": "The human-facing current package is ready for review.",
                    "evidence_refs": [str(publication_eval_path)],
                    "reviewer_reason": "The review package is synchronized.",
                    "reviewer_revision_advice": "Only keep bundle surfaces aligned.",
                    "reviewer_next_round_focus": "Double-check package surface consistency before submission.",
                },
            },
            "recommended_actions": [
                {
                    "action_id": "action-001",
                    "action_type": "continue_same_line",
                    "priority": "now",
                    "reason": "Only finalize-level bundle cleanup remains on the current paper line.",
                    "route_target": "finalize",
                    "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                    "route_rationale": "The paper itself is ready for human review and only finalize-level cleanup remains.",
                    "evidence_refs": [str(publication_eval_path)],
                    "requires_controller_decision": True,
                }
            ],
        },
    )
    dump_json(
        study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json",
        {
            "schema_version": 1,
            "summary_id": "evaluation-summary::001-risk::2026-04-05T06:00:00+00:00",
            "overall_verdict": "promising",
            "quality_closure_truth": {
                "state": "bundle_only_remaining",
                "summary": "Core scientific quality is already closed and only bundle cleanup remains.",
                "current_required_action": "continue_bundle_stage",
                "route_target": "finalize",
            },
            "quality_assessment": {
                "human_review_readiness": {
                    "status": "ready",
                    "summary": "Human-review package is ready.",
                }
            },
            "quality_execution_lane": {
                "lane_id": "submission_hardening",
                "route_target": "finalize",
                "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                "summary": "Only finalize-level submission hardening remains.",
            },
        },
    )
    initial_status = {
        **make_study_runtime_status_payload(
            study_id="001-risk",
            decision="noop",
            reason="quest_already_running",
        ),
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(quest_root),
        "quest_status": "active",
        "active_run_id": "run-001",
        "runtime_liveness_status": "live",
        "execution": {
            "engine": "med-deepscientist",
            "auto_entry": "on_managed_research_intent",
            "quest_id": "quest-001",
            "auto_resume": True,
        },
        "publication_supervisor_state": {
            "supervisor_phase": "bundle_stage_ready",
            "phase_owner": "publication_gate",
            "current_required_action": "continue_bundle_stage",
        },
    }
    stopped_status = {
        **initial_status,
        "quest_status": "stopped",
        "decision": "blocked",
        "reason": "quest_waiting_for_submission_metadata",
    }
    ensure_calls: list[tuple[str, bool]] = []
    stop_calls: list[dict[str, object]] = []
    stopped = False

    def fake_ensure(**kwargs):
        ensure_calls.append((str(kwargs.get("source") or "").strip(), bool(kwargs.get("allow_stopped_relaunch"))))
        return initial_status

    def fake_status(**kwargs):
        return stopped_status if stopped else initial_status

    def fake_stop_quest(**kwargs):
        nonlocal stopped
        stopped = True
        stop_calls.append(kwargs)
        return {"ok": True, "quest_id": "quest-001", "status": "stopped", "snapshot": {"status": "stopped"}}

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fake_ensure)
    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", fake_status)
    monkeypatch.setattr(module.study_runtime_router.managed_runtime_transport, "stop_quest", fake_stop_quest)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    monkeypatch.setattr(module.study_outer_loop, "_utc_now", lambda: "2026-04-05T05:58:00+00:00")

    first = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )
    second = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    payload = json.loads((study_root / "artifacts" / "controller_decisions" / "latest.json").read_text(encoding="utf-8"))

    assert ensure_calls == [
        ("runtime_watch", False),
        ("runtime_watch", False),
    ]
    assert len(stop_calls) == 1
    assert first["managed_study_outer_loop_dispatches"] == [
        {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "decision_type": "continue_same_line",
            "route_target": "finalize",
            "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
            "controller_action_type": "stop_runtime",
            "study_decision_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
            "dispatch_status": "executed",
            "source": "runtime_watch_outer_loop_wakeup",
        }
    ]
    assert second["managed_study_outer_loop_dispatches"] == []
    assert payload["controller_actions"] == [
        {
            "action_type": "stop_runtime",
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]
    assert payload["reason"] == "Human-review milestone reached; stop the live runtime and wait for explicit resume."
    assert payload["runtime_escalation_ref"]["record_id"] == (
        "runtime-escalation::001-risk::quest-001::quest_already_running::2026-04-05T05:58:00+00:00"
    )
def test_watch_runtime_materializes_outer_loop_decision_for_autonomous_bounded_analysis(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(quest_root, study_root)
    runtime_event_ref = _write_runtime_event_record(
        quest_root,
        study_root,
        runtime_escalation_ref=runtime_escalation_ref,
    )
    _write_charter(study_root)
    _write_publication_eval(
        study_root,
        quest_root,
        action_type="bounded_analysis",
        reason="Run one bounded robustness analysis before the next gate pass.",
    )
    status_payload = {
        **make_study_runtime_status_payload(
            study_id="001-risk",
            decision="blocked",
            reason="quest_stopped_requires_explicit_rerun",
        ),
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(quest_root),
        "quest_status": "stopped",
        "execution": {
            "engine": "med-deepscientist",
            "auto_entry": "on_managed_research_intent",
            "quest_id": "quest-001",
            "auto_resume": True,
        },
        "runtime_escalation_ref": runtime_escalation_ref,
        "runtime_event_ref": runtime_event_ref,
        "publication_supervisor_state": {
            "supervisor_phase": "publishability_gate_blocked",
            "phase_owner": "publication_gate",
            "current_required_action": "return_to_publishability_gate",
        },
    }

    def fake_ensure(**kwargs):
        if kwargs.get("source") == "runtime_watch":
            return status_payload
        if kwargs.get("source") == "runtime_watch_outer_loop_wakeup":
            return {
                "decision": "relaunch_stopped",
                "reason": "quest_stopped_requires_explicit_rerun",
            }
        raise AssertionError(f"unexpected ensure source: {kwargs.get('source')}")

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fake_ensure)
    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    payload = json.loads((study_root / "artifacts" / "controller_decisions" / "latest.json").read_text(encoding="utf-8"))
    watch_latest = json.loads(
        (quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json").read_text(encoding="utf-8")
    )

    assert result["managed_study_actions"][0]["study_id"] == "001-risk"
    assert result["managed_study_outer_loop_dispatches"] == [
        {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "decision_type": "bounded_analysis",
            "route_target": "analysis-campaign",
            "route_key_question": "What is the narrowest supplementary analysis still required before the paper line can continue?",
            "controller_action_type": "ensure_study_runtime_relaunch_stopped",
            "study_decision_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
            "dispatch_status": "executed",
            "source": "runtime_watch_outer_loop_wakeup",
        }
    ]
    assert watch_latest["managed_study_outer_loop_dispatch"] == result["managed_study_outer_loop_dispatches"][0]
    assert payload["decision_type"] == "bounded_analysis"
    assert payload["requires_human_confirmation"] is False
    assert payload["controller_actions"] == [
        {
            "action_type": "ensure_study_runtime_relaunch_stopped",
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]
def test_watch_runtime_materializes_outer_loop_decision_for_quality_re_review(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(quest_root, study_root)
    runtime_event_ref = _write_runtime_event_record(
        quest_root,
        study_root,
        runtime_escalation_ref=runtime_escalation_ref,
    )
    _write_charter(study_root)
    _write_publication_eval(
        study_root,
        quest_root,
        action_type="continue_same_line",
        reason="Older publication eval still points to ordinary write continuation.",
    )
    dump_json(
        study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json",
        {
            "schema_version": 1,
            "summary_id": "evaluation-summary::001-risk::2026-04-05T06:00:00+00:00",
            "overall_verdict": "promising",
            "primary_claim_status": "partial",
            "stop_loss_pressure": "none",
            "verdict_summary": "Revision is complete and MAS should re-review.",
            "requires_controller_decision": True,
            "quality_review_loop": {
                "policy_id": "publication-critique.v1",
                "loop_id": "quality-review-loop::001-risk::2026-04-05T06:00:00+00:00",
                "closure_state": "quality_repair_required",
                "lane_id": "general_quality_repair",
                "current_phase": "re_review_required",
                "current_phase_label": "等待复评",
                "recommended_next_phase": "re_review",
                "recommended_next_phase_label": "发起复评",
                "active_plan_id": "quality-plan::001-risk::v1",
                "active_plan_execution_status": "completed",
                "blocking_issue_count": 1,
                "blocking_issues": ["当前 blocking issues 是否已真正闭环"],
                "next_review_focus": ["当前 blocking issues 是否已真正闭环"],
                "re_review_ready": True,
                "summary": "当前修订计划已完成，下一步应由 MAS 发起 re-review，重新判断 blocking issues 是否真正闭环。",
                "recommended_next_action": "发起下一轮 MAS quality re-review，确认当前 blocking issues 是否已真正闭环。",
            },
        },
    )
    status_payload = {
        **make_study_runtime_status_payload(
            study_id="001-risk",
            decision="blocked",
            reason="quest_stopped_requires_explicit_rerun",
        ),
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(quest_root),
        "quest_status": "stopped",
        "execution": {
            "engine": "med-deepscientist",
            "auto_entry": "on_managed_research_intent",
            "quest_id": "quest-001",
            "auto_resume": True,
        },
        "runtime_escalation_ref": runtime_escalation_ref,
        "runtime_event_ref": runtime_event_ref,
        "publication_supervisor_state": {
            "supervisor_phase": "publishability_gate_blocked",
            "phase_owner": "publication_gate",
            "current_required_action": "return_to_publishability_gate",
        },
    }

    def fake_ensure(**kwargs):
        if kwargs.get("source") == "runtime_watch":
            return status_payload
        if kwargs.get("source") == "runtime_watch_outer_loop_wakeup":
            return {
                "decision": "relaunch_stopped",
                "reason": "quest_stopped_requires_explicit_rerun",
            }
        raise AssertionError(f"unexpected ensure source: {kwargs.get('source')}")

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fake_ensure)
    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    payload = json.loads((study_root / "artifacts" / "controller_decisions" / "latest.json").read_text(encoding="utf-8"))
    watch_latest = json.loads(
        (quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json").read_text(encoding="utf-8")
    )

    assert result["managed_study_outer_loop_dispatches"] == [
        {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "decision_type": "continue_same_line",
            "route_target": "review",
            "route_key_question": "当前 blocking issues 是否已真正闭环",
            "controller_action_type": "ensure_study_runtime_relaunch_stopped",
            "study_decision_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
            "dispatch_status": "executed",
            "source": "runtime_watch_outer_loop_wakeup",
        }
    ]
    assert watch_latest["managed_study_outer_loop_dispatch"] == result["managed_study_outer_loop_dispatches"][0]
    assert payload["decision_type"] == "continue_same_line"
    assert payload["route_target"] == "review"
    assert payload["route_key_question"] == "当前 blocking issues 是否已真正闭环"
    assert payload["reason"] == "发起下一轮 MAS quality re-review，确认当前 blocking issues 是否已真正闭环。"
def test_watch_runtime_fails_closed_when_outer_loop_candidate_lacks_stable_charter(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    (study_root / "artifacts" / "controller" / "study_charter.json").unlink()
    quest_root = profile.runtime_root / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(quest_root, study_root)
    _write_publication_eval(study_root, quest_root)
    status_payload = {
        **make_study_runtime_status_payload(
            study_id="001-risk",
            decision="blocked",
            reason="quest_stopped_requires_explicit_rerun",
        ),
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(quest_root),
        "quest_status": "stopped",
        "runtime_escalation_ref": runtime_escalation_ref,
        "publication_supervisor_state": {
            "current_required_action": "continue_write_stage",
        },
    }

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", lambda **kwargs: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    with pytest.raises(ValueError, match="study charter"):
        module.run_watch_for_runtime(
            runtime_root=profile.runtime_root,
            controller_runners={},
            apply=True,
            profile=profile,
            ensure_study_runtimes=True,
        )

    assert not (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()
@pytest.mark.parametrize(
    ("action_type", "current_required_action"),
    [
        ("continue_same_line", "human_confirmation_required"),
        ("prepare_promotion_review", "continue_write_stage"),
    ],
)
def test_watch_runtime_skips_outer_loop_materialization_when_human_gate_or_action_is_not_autonomous(
    tmp_path: Path,
    monkeypatch,
    action_type: str,
    current_required_action: str,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(quest_root, study_root)
    _write_charter(study_root)
    _write_publication_eval(study_root, quest_root, action_type=action_type)
    status_payload = {
        **make_study_runtime_status_payload(
            study_id="001-risk",
            decision="blocked",
            reason="quest_stopped_requires_explicit_rerun",
        ),
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(quest_root),
        "quest_status": "stopped",
        "runtime_escalation_ref": runtime_escalation_ref,
        "publication_supervisor_state": {
            "current_required_action": current_required_action,
        },
    }
    ensure_calls: list[str] = []

    def fake_ensure(**kwargs):
        ensure_calls.append(str(kwargs.get("source") or "").strip())
        return status_payload

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fake_ensure)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert result["managed_study_actions"][0]["study_id"] == "001-risk"
    assert result["managed_study_outer_loop_dispatches"] == []
    assert ensure_calls == ["runtime_watch"]
    assert not (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()
    watch_latest_path = quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json"
    assert not watch_latest_path.exists()
def test_publication_eval_action_uses_bounded_analysis_for_clear_continue_write_stage() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")

    action = module._publication_eval_action(
        report={
            "status": "clear",
            "current_required_action": "continue_write_stage",
            "controller_stage_note": "Current line is clear and a bounded robustness pass should complete first.",
        },
        generated_at="2026-04-05T06:05:00+00:00",
        evidence_refs=("/tmp/main_result.json",),
    )

    assert action.action_type == "bounded_analysis"
    assert action.priority == "now"
def test_publication_eval_action_uses_same_line_route_back_for_blocked_reviewer_first_surface() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")

    action = module._publication_eval_action(
        report={
            "status": "blocked",
            "current_required_action": "return_to_publishability_gate",
            "controller_stage_note": "稿件书写面还有医学论文表达硬阻塞，需要继续修文。",
            "medical_publication_surface_named_blockers": ["reviewer_first_concerns_unresolved"],
            "medical_publication_surface_route_back_recommendation": "return_to_write",
        },
        generated_at="2026-04-05T06:05:00+00:00",
        evidence_refs=("/tmp/main_result.json",),
    )

    assert action.action_type == "route_back_same_line"
    assert action.reason == "稿件书写面还有医学论文表达硬阻塞，需要继续修文。"
    assert action.route_target == "write"
    assert action.route_key_question == "What is the narrowest same-line manuscript repair or continuation step required now?"
    assert action.route_rationale == "稿件书写面还有医学论文表达硬阻塞，需要继续修文。"
    assert action.priority == "now"
def test_publication_eval_action_uses_bounded_analysis_for_blocked_claim_evidence_route() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")

    action = module._publication_eval_action(
        report={
            "status": "blocked",
            "current_required_action": "return_to_publishability_gate",
            "controller_stage_note": "当前 claim-evidence 对齐还不够，需要补一轮最小补充分析。",
            "medical_publication_surface_named_blockers": ["claim_evidence_consistency_failed"],
            "medical_publication_surface_route_back_recommendation": "return_to_analysis_campaign",
        },
        generated_at="2026-04-05T06:05:00+00:00",
        evidence_refs=("/tmp/main_result.json",),
    )

    assert action.action_type == "bounded_analysis"
    assert action.reason == "当前 claim-evidence 对齐还不够，需要补一轮最小补充分析。"
    assert action.route_target == "analysis-campaign"
    assert action.route_key_question == "What is the narrowest supplementary analysis still required before the paper line can continue?"
def test_publication_eval_action_routes_blocked_bundle_stage_back_to_same_line_finalize() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")

    action = module._publication_eval_action(
        report={
            "status": "blocked",
            "current_required_action": "complete_bundle_stage",
            "controller_stage_note": "bundle-stage blockers are now on the critical path for this paper line",
        },
        generated_at="2026-04-21T03:10:00+00:00",
        evidence_refs=("/tmp/publishability_gate.json",),
    )

    assert action.action_type == "route_back_same_line"
    assert action.priority == "now"
    assert action.route_target == "finalize"
    assert action.route_key_question == (
        "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？"
    )
    assert action.route_rationale == "bundle-stage blockers are now on the critical path for this paper line"
