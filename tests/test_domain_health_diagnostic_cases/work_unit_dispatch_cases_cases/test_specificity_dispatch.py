from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_watch_runtime_does_not_dispatch_after_platform_repair_required(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    ledger = importlib.import_module("med_autoscience.controllers.work_unit_ledger")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    _write_charter(study_root)
    _write_publication_eval(study_root, quest_root, action_type="bounded_analysis")
    status_payload = {
        **make_progress_projection_payload(
            study_id="001-risk",
            decision="blocked",
            reason="study_completion_publishability_gate_blocked",
        ),
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(quest_root),
        "quest_status": "running",
    }
    tick_request = {
        "study_root": study_root,
        "charter_ref": _write_charter(study_root),
        "publication_eval_ref": _write_publication_eval(study_root, quest_root, action_type="bounded_analysis"),
        "decision_type": "bounded_analysis",
        "route_target": "analysis-campaign",
        "route_key_question": "analysis_claim_evidence_repair: Repair claim-evidence blockers.",
        "route_rationale": "Run bounded claim-evidence repair.",
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "request_opl_stage_attempt",
                "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
            }
        ],
        "reason": "Run bounded claim-evidence repair.",
        "work_unit_fingerprint": "publication-blockers::same",
        "next_work_unit": {
            "unit_id": "analysis_claim_evidence_repair",
            "lane": "analysis-campaign",
            "summary": "Repair claim-evidence blockers.",
        },
    }
    identity = module.domain_health_diagnostic_work_units.identity_from_tick_request(
        study_id="001-risk",
        quest_id="quest-001",
        tick_request=tick_request,
    )
    ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type="platform_repair_required",
        payload={
            "source": "domain_health_diagnostic_outer_loop_wakeup",
            "wakeup_outcome": "platform_repair_required",
            "wakeup_reason": "outer-loop work unit redrive budget exhausted without result evidence",
        },
        recorded_at="2026-05-02T04:45:16+00:00",
    )
    calls: list[str] = []

    def fake_outer_loop_tick(**kwargs):
        calls.append(str(kwargs.get("source") or ""))
        return {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "source": kwargs.get("source"),
            "study_decision_ref": {
                "artifact_path": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve())
            },
            "dispatch_status": "executed",
            "executed_controller_action": {"action_type": "request_opl_stage_attempt", "result": {"status": "executed"}},
        }

    monkeypatch.setattr(module.study_outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: tick_request)
    monkeypatch.setattr(module.domain_status_projection, "study_outer_loop_tick", fake_outer_loop_tick)
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )
    wakeup_latest = json.loads(
        (study_root / "artifacts" / "runtime" / "domain_health_diagnostic_wakeup" / "latest.json").read_text(encoding="utf-8")
    )
    ledger_events = [
        json.loads(line)
        for line in (
            study_root / "artifacts" / "runtime" / "work_unit_ledger" / "events.jsonl"
        ).read_text(encoding="utf-8").splitlines()
    ]

    assert calls == []
    assert result["managed_study_outer_loop_dispatches"] == []
    assert result["managed_study_no_op_suppressions"][0]["outcome"] == "platform_repair_required"
    assert wakeup_latest["outcome"] == "platform_repair_required"
    assert [event["event_type"] for event in ledger_events] == [
        "platform_repair_required",
        "platform_repair_required",
    ]


def test_watch_runtime_records_specificity_request_without_outer_loop_dispatch(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    _write_charter(study_root)
    status_payload = {
        **make_progress_projection_payload(
            study_id="001-risk",
            decision="blocked",
            reason="study_completion_publishability_gate_blocked",
        ),
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(quest_root),
        "quest_status": "running",
    }
    next_work_unit = {
        "unit_id": "gate_needs_specificity",
        "lane": "controller",
        "summary": "Ask the publication gate to identify concrete blocker targets.",
    }
    publication_eval_ref = _write_publication_eval(
        study_root,
        quest_root,
        action_type="return_to_controller",
        work_unit_fingerprint="publication-blockers::vague",
        next_work_unit=next_work_unit,
    )
    tick_request = {
        "study_root": study_root,
        "charter_ref": _write_charter(study_root),
        "publication_eval_ref": publication_eval_ref,
        "decision_type": "return_to_controller",
        "route_target": None,
        "route_key_question": None,
        "route_rationale": "Publication gate needs concrete blocker targets before dispatch.",
        "requires_human_confirmation": False,
        "controller_actions": [],
        "reason": "Publication gate needs concrete blocker targets before dispatch.",
        "work_unit_fingerprint": "publication-blockers::vague",
        "next_work_unit": {
            "unit_id": "gate_needs_specificity",
            "lane": "controller",
            "summary": "Ask the publication gate to identify concrete blocker targets.",
        },
        "specificity_questions": [
            "Which exact claim, figure, table, metric, citation, evidence row, or package artifact is blocking the gate?",
        ],
    }
    calls: list[str] = []
    dump_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "quest_id": "quest-001",
            "status": "paused",
            "active_run_id": None,
            "pending_user_message_count": 2,
            "last_controller_decision_authorization": {
                "decision_id": "old-analysis-decision",
                "route_target": "analysis-campaign",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": "publication-blockers::old",
                "controller_work_unit_lifecycle": {"lifecycle_state": "new"},
            },
        },
    )
    dump_json(
        quest_root / ".ds" / "user_message_queue.json",
        {
            "version": 1,
            "pending": [
                {
                    "message_id": "msg-controller-old",
                    "content": "MAS controller authorization. old analysis request",
                    "dedupe_key": "control-intent::old",
                    "status": "queued",
                },
                {
                    "message_id": "msg-human-real",
                    "content": "请等我确认目标期刊。",
                    "status": "queued",
                },
            ],
            "completed": [],
        },
    )

    def fake_outer_loop_tick(**kwargs):
        calls.append(str(kwargs.get("source") or ""))
        return {"dispatch_status": "executed"}

    monkeypatch.setattr(module.study_outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: tick_request)
    monkeypatch.setattr(module.domain_status_projection, "study_outer_loop_tick", fake_outer_loop_tick)
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )
    wakeup_latest = json.loads(
        (study_root / "artifacts" / "runtime" / "domain_health_diagnostic_wakeup" / "latest.json").read_text(encoding="utf-8")
    )
    controller_decision = json.loads(
        (study_root / "artifacts" / "controller_decisions" / "latest.json").read_text(encoding="utf-8")
    )
    runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    message_queue = json.loads((quest_root / ".ds" / "user_message_queue.json").read_text(encoding="utf-8"))
    ledger_events = [
        json.loads(line)
        for line in (
            study_root / "artifacts" / "runtime" / "work_unit_ledger" / "events.jsonl"
        ).read_text(encoding="utf-8").splitlines()
    ]

    assert calls == []
    assert result["managed_study_outer_loop_dispatches"] == []
    assert result["managed_study_no_op_suppressions"][0]["outcome"] == "needs_specificity"
    assert wakeup_latest["outcome"] == "needs_specificity"
    assert wakeup_latest["no_op_acknowledged"] is True
    assert wakeup_latest["next_work_unit"]["unit_id"] == "gate_needs_specificity"
    assert wakeup_latest["specificity_questions"] == tick_request["specificity_questions"]
    assert controller_decision["decision_type"] == "return_to_controller"
    assert controller_decision["controller_actions"][0]["action_type"] == "request_gate_specificity"
    assert controller_decision["next_work_unit"]["unit_id"] == "gate_needs_specificity"
    assert controller_decision["work_unit_fingerprint"] == "publication-blockers::vague"
    assert runtime_state["last_controller_decision_authorization"]["work_unit_id"] == "gate_needs_specificity"
    assert runtime_state["last_controller_decision_authorization"]["work_unit_fingerprint"] == "publication-blockers::vague"
    assert runtime_state["last_controller_decision_authorization"]["controller_work_unit_executable"] is False
    assert (
        runtime_state["last_controller_decision_authorization"]["non_executable_reason"]
        == "gate_needs_specificity_without_targets"
    )
    assert runtime_state["last_controller_decision_authorization"]["required_target_kinds"] == [
        "claim",
        "display",
        "evidence_source",
        "citation",
        "metric",
        "package_artifact",
        "authorization_provenance",
    ]
    assert runtime_state["last_controller_decision_authorization"]["controller_work_unit_lifecycle"] == {
        "lifecycle_state": "needs_specificity",
        "latest_event_type": "needs_specificity",
        "delivery_blocked": True,
        "block_reason": "needs_specificity",
        "terminal_consumed": True,
    }
    assert runtime_state["pending_user_message_count"] == 1
    assert [item["message_id"] for item in message_queue["pending"]] == ["msg-human-real"]
    assert [item["message_id"] for item in message_queue["completed"]] == ["msg-controller-old"]
    assert message_queue["completed"][0]["status"] == "superseded_by_gate_specificity"
    assert [event["event_type"] for event in ledger_events] == ["needs_specificity"]


def test_watch_runtime_carries_specificity_targets_into_authorization_and_wakeup(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    _write_charter(study_root)
    status_payload = {
        **make_progress_projection_payload(
            study_id="001-risk",
            decision="blocked",
            reason="study_completion_publishability_gate_blocked",
        ),
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(quest_root),
        "quest_status": "running",
    }
    next_work_unit = {
        "unit_id": "gate_needs_specificity",
        "lane": "controller",
        "summary": "Specific gate targets are available.",
    }
    publication_eval_ref = _write_publication_eval(
        study_root,
        quest_root,
        action_type="return_to_controller",
        work_unit_fingerprint="publication-blockers::specific",
        next_work_unit=next_work_unit,
    )
    specificity_targets = [
        {
            "target_kind": "claim",
            "target_id": "primary_claim",
            "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
            "blocking_reason": "Primary claim needs a concrete evidence anchor.",
        },
        {
            "target_kind": "figure",
            "target_id": "figure_2",
            "source_path": str(study_root / "paper" / "figures" / "figure_2.png"),
            "blocking_reason": "Figure 2 needs a concrete blocker reference.",
        },
        {
            "target_kind": "table",
            "target_id": "table_1",
            "source_path": str(study_root / "paper" / "tables" / "table_1.csv"),
            "blocking_reason": "Table 1 needs denominator provenance.",
        },
        {
            "target_kind": "metric",
            "target_id": "c_statistic",
            "source_path": str(study_root / "artifacts" / "results" / "model_performance.json"),
            "blocking_reason": "Metric needs a result source path.",
        },
        {
            "target_kind": "source_path",
            "target_id": "external_validation_dataset",
            "source_path": str(study_root / "artifacts" / "results" / "external_validation.json"),
            "blocking_reason": "External validation source path is missing.",
        },
    ]
    tick_request = {
        "study_root": study_root,
        "charter_ref": _write_charter(study_root),
        "publication_eval_ref": publication_eval_ref,
        "decision_type": "return_to_controller",
        "route_target": "controller",
        "route_key_question": "gate_needs_specificity: concrete targets are available.",
        "route_rationale": "Publication gate provided concrete blocker targets for repair.",
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "request_gate_specificity",
                "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
            }
        ],
        "reason": "Publication gate provided concrete blocker targets for repair.",
        "work_unit_fingerprint": "publication-blockers::specific",
        "next_work_unit": next_work_unit,
        "specificity_targets": specificity_targets,
    }
    dump_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "quest_id": "quest-001",
            "status": "running",
            "active_run_id": "run-1",
            "worker_running": True,
        },
    )

    monkeypatch.setattr(module.study_outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: tick_request)
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )
    wakeup_latest = json.loads(
        (study_root / "artifacts" / "runtime" / "domain_health_diagnostic_wakeup" / "latest.json").read_text(encoding="utf-8")
    )
    runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    authorization = runtime_state["last_controller_decision_authorization"]

    assert result["managed_study_no_op_suppressions"][0]["outcome"] == "needs_specificity"
    assert wakeup_latest["specificity_targets"] == specificity_targets
    assert authorization["specificity_targets"] == specificity_targets
    assert authorization["controller_work_unit_executable"] is True
    assert "non_executable_reason" not in authorization
