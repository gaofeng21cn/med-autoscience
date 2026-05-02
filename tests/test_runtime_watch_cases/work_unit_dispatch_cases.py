from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_watch_runtime_redrives_repeated_work_unit_until_attempt_closes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    _write_charter(study_root)
    _write_publication_eval(study_root, quest_root, action_type="bounded_analysis")
    status_payload = {
        **make_study_runtime_status_payload(
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
        "route_key_question": "What is the narrowest supplementary analysis still required before the paper line can continue?",
        "route_rationale": "Run deterministic gate-clearing batch first.",
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "run_gate_clearing_batch",
                "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
            }
        ],
        "reason": "Run deterministic gate-clearing batch first.",
        "work_unit_fingerprint": "publication-blockers::same",
        "next_work_unit": {
            "unit_id": "analysis_claim_evidence_repair",
            "lane": "analysis-campaign",
            "summary": "Repair claim-evidence blockers.",
        },
    }
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
            "executed_controller_action": {"action_type": "run_gate_clearing_batch", "result": {"status": "executed"}},
        }

    monkeypatch.setattr(module.study_outer_loop, "build_runtime_watch_outer_loop_tick_request", lambda **_: tick_request)
    monkeypatch.setattr(module.study_runtime_router, "study_outer_loop_tick", fake_outer_loop_tick)
    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", lambda **_: status_payload)
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
    wakeup_latest = json.loads(
        (study_root / "artifacts" / "runtime" / "runtime_watch_wakeup" / "latest.json").read_text(encoding="utf-8")
    )
    ledger_events = [
        json.loads(line)
        for line in (
            study_root / "artifacts" / "runtime" / "work_unit_ledger" / "events.jsonl"
        ).read_text(encoding="utf-8").splitlines()
    ]

    assert calls == ["runtime_watch_outer_loop_wakeup", "runtime_watch_outer_loop_wakeup"]
    assert len(first["managed_study_outer_loop_dispatches"]) == 1
    assert len(second["managed_study_outer_loop_dispatches"]) == 1
    assert second["managed_study_no_op_suppressions"] == []
    assert [event["event_type"] for event in ledger_events] == ["dispatched", "dispatched"]
    assert wakeup_latest["outcome"] == "dispatched"
    assert "no_op_acknowledged" not in wakeup_latest
    assert wakeup_latest["work_unit_dispatch_key"] == (
        "publication-blockers::same::analysis_claim_evidence_repair::run_gate_clearing_batch"
    )


def test_watch_runtime_escalates_after_bounded_work_unit_redrives(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    _write_charter(study_root)
    _write_publication_eval(study_root, quest_root, action_type="bounded_analysis")
    status_payload = {
        **make_study_runtime_status_payload(
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
                "action_type": "ensure_study_runtime",
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
            "executed_controller_action": {"action_type": "ensure_study_runtime", "result": {"status": "executed"}},
        }

    monkeypatch.setattr(module.study_outer_loop, "build_runtime_watch_outer_loop_tick_request", lambda **_: tick_request)
    monkeypatch.setattr(module.study_runtime_router, "study_outer_loop_tick", fake_outer_loop_tick)
    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", lambda **_: status_payload)
    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    results = [
        module.run_watch_for_runtime(
            runtime_root=profile.runtime_root,
            controller_runners={},
            apply=True,
            profile=profile,
            ensure_study_runtimes=True,
        )
        for _ in range(4)
    ]
    wakeup_latest = json.loads(
        (study_root / "artifacts" / "runtime" / "runtime_watch_wakeup" / "latest.json").read_text(encoding="utf-8")
    )
    ledger_events = [
        json.loads(line)
        for line in (
            study_root / "artifacts" / "runtime" / "work_unit_ledger" / "events.jsonl"
        ).read_text(encoding="utf-8").splitlines()
    ]

    assert calls == [
        "runtime_watch_outer_loop_wakeup",
        "runtime_watch_outer_loop_wakeup",
        "runtime_watch_outer_loop_wakeup",
    ]
    assert [len(item["managed_study_outer_loop_dispatches"]) for item in results] == [1, 1, 1, 0]
    assert results[-1]["managed_study_no_op_suppressions"][0]["outcome"] == "platform_repair_required"
    assert results[-1]["managed_study_no_op_suppressions"][0]["redrive_attempt_count"] == 3
    assert wakeup_latest["outcome"] == "platform_repair_required"
    assert wakeup_latest["platform_repair_kind"] == "work_unit_redrive_exhausted_without_attempt_result"
    assert [event["event_type"] for event in ledger_events] == [
        "dispatched",
        "dispatched",
        "dispatched",
        "platform_repair_required",
    ]


def test_watch_runtime_records_specificity_request_without_outer_loop_dispatch(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    _write_charter(study_root)
    status_payload = {
        **make_study_runtime_status_payload(
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
        "publication_eval_ref": _write_publication_eval(study_root, quest_root, action_type="return_to_controller"),
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

    def fake_outer_loop_tick(**kwargs):
        calls.append(str(kwargs.get("source") or ""))
        return {"dispatch_status": "executed"}

    monkeypatch.setattr(module.study_outer_loop, "build_runtime_watch_outer_loop_tick_request", lambda **_: tick_request)
    monkeypatch.setattr(module.study_runtime_router, "study_outer_loop_tick", fake_outer_loop_tick)
    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", lambda **_: status_payload)
    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )
    wakeup_latest = json.loads(
        (study_root / "artifacts" / "runtime" / "runtime_watch_wakeup" / "latest.json").read_text(encoding="utf-8")
    )
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
    assert [event["event_type"] for event in ledger_events] == ["needs_specificity"]


def test_outer_loop_tick_request_carries_publication_work_unit_context(tmp_path: Path) -> None:
    outer_loop = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "quest-001"
    _write_charter(study_root)
    _write_publication_eval(
        study_root,
        quest_root,
        action_type="bounded_analysis",
        work_unit_fingerprint="publication-blockers::same",
        next_work_unit={
            "unit_id": "analysis_claim_evidence_repair",
            "lane": "analysis-campaign",
            "summary": "Repair claim-evidence blockers.",
        },
    )

    request = outer_loop.build_runtime_watch_outer_loop_tick_request(
        study_root=study_root,
        status_payload={
            **make_study_runtime_status_payload(
                study_id="001-risk",
                decision="blocked",
                reason="study_completion_publishability_gate_blocked",
            ),
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_status": "running",
        },
    )

    assert request is not None
    assert request["work_unit_fingerprint"] == "publication-blockers::same"
    assert request["next_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"
    assert request["blocking_work_units"][0]["unit_id"] == "analysis_claim_evidence_repair"


def test_matching_controller_decision_requires_same_work_unit_context(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch_parts.managed_wakeup")
    study_root = tmp_path / "studies" / "001-risk"
    charter_ref = {
        "charter_id": "charter::001-risk::v1",
        "artifact_path": "/tmp/workspace/studies/001-risk/artifacts/controller/study_charter.json",
    }
    publication_eval_ref = {
        "eval_id": "publication-eval::001-risk::quest-001::2026-04-05T05:58:00+00:00",
        "artifact_path": "/tmp/workspace/studies/001-risk/artifacts/publication_eval/latest.json",
    }
    controller_actions = [
        {
            "action_type": "ensure_study_runtime",
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]
    next_work_unit = {
        "unit_id": "analysis_claim_evidence_repair",
        "lane": "analysis-campaign",
        "summary": "Repair claim-evidence blockers.",
    }
    base_payload = {
        "schema_version": 1,
        "decision_id": "study-decision::001-risk::quest-001::bounded_analysis::2026-04-05T06:00:00+00:00",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "emitted_at": "2026-04-05T06:00:00+00:00",
        "decision_type": "bounded_analysis",
        "charter_ref": charter_ref,
        "runtime_escalation_ref": {
            "record_id": "runtime-escalation::001-risk::quest-001::startup_boundary_not_ready_for_resume::2026-04-05T05:55:00+00:00",
            "artifact_path": "/tmp/runtime/quests/quest-001/artifacts/reports/escalation/runtime_escalation_record.json",
            "summary_ref": "/tmp/workspace/studies/001-risk/artifacts/runtime/last_launch_report.json",
        },
        "publication_eval_ref": publication_eval_ref,
        "requires_human_confirmation": False,
        "controller_actions": controller_actions,
        "reason": "Run deterministic gate repair.",
        "route_target": "analysis-campaign",
        "route_key_question": "analysis_claim_evidence_repair: Repair claim-evidence blockers.",
        "route_rationale": (
            "Publication gate selected controller-owned work unit `analysis_claim_evidence_repair`."
        ),
    }
    tick_request = {
        "decision_type": "bounded_analysis",
        "charter_ref": charter_ref,
        "publication_eval_ref": publication_eval_ref,
        "requires_human_confirmation": False,
        "controller_actions": controller_actions,
        "reason": "Run deterministic gate repair.",
        "route_target": "analysis-campaign",
        "route_key_question": "analysis_claim_evidence_repair: Repair claim-evidence blockers.",
        "route_rationale": (
            "Publication gate selected controller-owned work unit `analysis_claim_evidence_repair`."
        ),
        "source_route_key_question": "Broad reviewer revision checklist.",
        "work_unit_fingerprint": "publication-blockers::same",
        "next_work_unit": next_work_unit,
        "blocking_work_units": [next_work_unit],
    }
    latest_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    dump_json(latest_path, base_payload)

    assert module._controller_decision_latest_matches_outer_loop_request(
        study_root=study_root,
        status_payload={},
        tick_request=tick_request,
    ) is False

    dump_json(
        latest_path,
        {
            **base_payload,
            "source_route_key_question": "Broad reviewer revision checklist.",
            "work_unit_fingerprint": "publication-blockers::same",
            "next_work_unit": next_work_unit,
            "blocking_work_units": [next_work_unit],
        },
    )

    assert module._controller_decision_latest_matches_outer_loop_request(
        study_root=study_root,
        status_payload={},
        tick_request=tick_request,
    ) is True


def test_work_unit_dedupe_does_not_reuse_prior_upstream_unit_when_blocker_fingerprint_churns(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch_work_units")
    study_root = tmp_path / "studies" / "001-risk"
    latest_path = study_root / "artifacts" / "runtime" / "runtime_watch_wakeup" / "latest.json"
    latest_path.parent.mkdir(parents=True)
    latest_path.write_text(
        json.dumps(
            {
                "outcome": "dispatched",
                "work_unit_dispatch_key": "publication-blockers::old::analysis_claim_evidence_repair::run_gate_clearing_batch",
            }
        ),
        encoding="utf-8",
    )
    tick_request = {
        "work_unit_fingerprint": "publication-blockers::new",
        "next_work_unit": {"unit_id": "analysis_claim_evidence_repair"},
        "controller_actions": [{"action_type": "run_gate_clearing_batch"}],
    }

    already_executed, dispatch_key = module.dispatch_already_executed(
        study_root=study_root,
        tick_request=tick_request,
    )

    assert already_executed is False
    assert dispatch_key == "publication-blockers::new::analysis_claim_evidence_repair::run_gate_clearing_batch"


def test_work_unit_dedupe_uses_ledger_when_latest_wakeup_was_overwritten_by_noop(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch_work_units")
    ledger = importlib.import_module("med_autoscience.controllers.work_unit_ledger")
    study_root = tmp_path / "studies" / "001-risk"
    latest_path = study_root / "artifacts" / "runtime" / "runtime_watch_wakeup" / "latest.json"
    latest_path.parent.mkdir(parents=True)
    latest_path.write_text(
        json.dumps({"outcome": "no_request"}),
        encoding="utf-8",
    )
    tick_request = {
        "work_unit_fingerprint": "publication-blockers::same",
        "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        "controller_actions": [{"action_type": "run_gate_clearing_batch"}],
    }
    identity = module.identity_from_tick_request(
        study_id="001-risk",
        quest_id="quest-001",
        tick_request=tick_request,
    )
    ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type="dispatched",
        payload={"source": "runtime_watch"},
        recorded_at="2026-04-28T00:00:00+00:00",
    )

    already_executed, dispatch_key = module.dispatch_already_executed(
        study_root=study_root,
        tick_request=tick_request,
    )

    assert already_executed is False
    assert dispatch_key == "publication-blockers::same::analysis_claim_evidence_repair::run_gate_clearing_batch"


def test_work_unit_dedupe_requires_attempt_result_not_bare_dispatch(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch_work_units")
    study_root = tmp_path / "studies" / "001-risk"
    latest_path = study_root / "artifacts" / "runtime" / "runtime_watch_wakeup" / "latest.json"
    latest_path.parent.mkdir(parents=True)
    latest_path.write_text(
        json.dumps(
            {
                "outcome": "dispatched",
                "work_unit_dispatch_key": "publication-blockers::same::analysis_claim_evidence_repair::run_gate_clearing_batch",
            }
        ),
        encoding="utf-8",
    )
    tick_request = {
        "work_unit_fingerprint": "publication-blockers::same",
        "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        "controller_actions": [{"action_type": "run_gate_clearing_batch"}],
    }

    already_executed, dispatch_key = module.dispatch_already_executed(
        study_root=study_root,
        tick_request=tick_request,
    )

    assert already_executed is False
    assert dispatch_key == "publication-blockers::same::analysis_claim_evidence_repair::run_gate_clearing_batch"


def test_work_unit_dedupe_accepts_closed_attempt_result(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch_work_units")
    ledger = importlib.import_module("med_autoscience.controllers.work_unit_ledger")
    study_root = tmp_path / "studies" / "001-risk"
    tick_request = {
        "work_unit_fingerprint": "publication-blockers::same",
        "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        "controller_actions": [{"action_type": "run_gate_clearing_batch"}],
    }
    identity = module.identity_from_tick_request(
        study_id="001-risk",
        quest_id="quest-001",
        tick_request=tick_request,
    )
    ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type="closed",
        payload={"gate_replay_status": "clear"},
        recorded_at="2026-04-28T00:00:00+00:00",
    )

    already_executed, dispatch_key = module.dispatch_already_executed(
        study_root=study_root,
        tick_request=tick_request,
    )

    assert already_executed is True
    assert dispatch_key == "publication-blockers::same::analysis_claim_evidence_repair::run_gate_clearing_batch"


def test_work_unit_dedupe_rejects_closed_event_without_attempt_delta_or_gate_change(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch_work_units")
    ledger = importlib.import_module("med_autoscience.controllers.work_unit_ledger")
    study_root = tmp_path / "studies" / "001-risk"
    tick_request = {
        "work_unit_fingerprint": "publication-blockers::same",
        "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        "controller_actions": [{"action_type": "run_gate_clearing_batch"}],
    }
    identity = module.identity_from_tick_request(
        study_id="001-risk",
        quest_id="quest-001",
        tick_request=tick_request,
    )
    ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type="closed",
        payload={"dispatch_status": "executed"},
        recorded_at="2026-04-28T00:00:00+00:00",
    )

    already_executed, dispatch_key = module.dispatch_already_executed(
        study_root=study_root,
        tick_request=tick_request,
    )

    assert already_executed is False
    assert dispatch_key == "publication-blockers::same::analysis_claim_evidence_repair::run_gate_clearing_batch"


def test_work_unit_dedupe_accepts_closed_event_with_attempt_record(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch_work_units")
    ledger = importlib.import_module("med_autoscience.controllers.work_unit_ledger")
    study_root = tmp_path / "studies" / "001-risk"
    tick_request = {
        "work_unit_fingerprint": "publication-blockers::same",
        "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        "controller_actions": [{"action_type": "run_gate_clearing_batch"}],
    }
    identity = module.identity_from_tick_request(
        study_id="001-risk",
        quest_id="quest-001",
        tick_request=tick_request,
    )
    ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type="closed",
        payload={
            "dispatch_status": "executed",
            "attempt_record": {
                "attempt_state": "released",
                "attempt_count": 1,
                "work_unit_id": "analysis_claim_evidence_repair",
            },
        },
        recorded_at="2026-04-28T00:00:00+00:00",
    )

    already_executed, dispatch_key = module.dispatch_already_executed(
        study_root=study_root,
        tick_request=tick_request,
    )

    assert already_executed is True
    assert dispatch_key == "publication-blockers::same::analysis_claim_evidence_repair::run_gate_clearing_batch"


def test_work_unit_redrive_budget_resets_after_evidenced_close(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch_work_units")
    ledger = importlib.import_module("med_autoscience.controllers.work_unit_ledger")
    study_root = tmp_path / "studies" / "001-risk"
    tick_request = {
        "work_unit_fingerprint": "publication-blockers::same",
        "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        "controller_actions": [{"action_type": "run_gate_clearing_batch"}],
    }
    identity = module.identity_from_tick_request(
        study_id="001-risk",
        quest_id="quest-001",
        tick_request=tick_request,
    )
    for index in range(3):
        ledger.append_event(
            study_root=study_root,
            identity=identity,
            event_type="dispatched",
            payload={"source": "runtime_watch", "attempt": index + 1},
            recorded_at=f"2026-04-28T00:0{index}:00+00:00",
        )
    exhausted, dispatch_key, attempt_count = module.redrive_budget_exhausted(
        study_root=study_root,
        tick_request=tick_request,
    )
    assert exhausted is True
    assert dispatch_key == "publication-blockers::same::analysis_claim_evidence_repair::run_gate_clearing_batch"
    assert attempt_count == 3

    ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type="closed",
        payload={"artifact_delta_ref": "artifacts/delta.json"},
        recorded_at="2026-04-28T00:03:00+00:00",
    )

    exhausted, _, attempt_count = module.redrive_budget_exhausted(
        study_root=study_root,
        tick_request=tick_request,
    )
    assert exhausted is False
    assert attempt_count == 0


def test_work_unit_dedupe_does_not_use_ledger_when_latest_inputs_changed(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch_work_units")
    ledger = importlib.import_module("med_autoscience.controllers.work_unit_ledger")
    study_root = tmp_path / "studies" / "001-risk"
    latest_path = study_root / "artifacts" / "runtime" / "runtime_watch_wakeup" / "latest.json"
    latest_path.parent.mkdir(parents=True)
    latest_path.write_text(
        json.dumps({"outcome": "no_request", "dispatch_cause": "input_changed"}),
        encoding="utf-8",
    )
    tick_request = {
        "work_unit_fingerprint": "publication-blockers::same",
        "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        "controller_actions": [{"action_type": "run_gate_clearing_batch"}],
    }
    identity = module.identity_from_tick_request(
        study_id="001-risk",
        quest_id="quest-001",
        tick_request=tick_request,
    )
    ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type="dispatched",
        payload={"source": "runtime_watch"},
        recorded_at="2026-04-28T00:00:00+00:00",
    )

    already_executed, dispatch_key = module.dispatch_already_executed(
        study_root=study_root,
        tick_request=tick_request,
    )

    assert already_executed is False
    assert dispatch_key == "publication-blockers::same::analysis_claim_evidence_repair::run_gate_clearing_batch"


def test_work_unit_dedupe_does_not_use_ledger_for_prior_upstream_unit_when_fingerprint_churns(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch_work_units")
    ledger = importlib.import_module("med_autoscience.controllers.work_unit_ledger")
    study_root = tmp_path / "studies" / "001-risk"
    previous_request = {
        "work_unit_fingerprint": "publication-blockers::old",
        "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        "controller_actions": [{"action_type": "run_gate_clearing_batch"}],
    }
    previous_identity = module.identity_from_tick_request(
        study_id="001-risk",
        quest_id="quest-001",
        tick_request=previous_request,
    )
    ledger.append_event(
        study_root=study_root,
        identity=previous_identity,
        event_type="dispatched",
        payload={"source": "runtime_watch"},
        recorded_at="2026-04-28T00:00:00+00:00",
    )
    tick_request = {
        "work_unit_fingerprint": "publication-blockers::new",
        "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        "controller_actions": [{"action_type": "run_gate_clearing_batch"}],
    }

    already_executed, dispatch_key = module.dispatch_already_executed(
        study_root=study_root,
        tick_request=tick_request,
    )

    assert already_executed is False
    assert dispatch_key == "publication-blockers::new::analysis_claim_evidence_repair::run_gate_clearing_batch"


def test_work_unit_dedupe_does_not_reuse_prior_delivery_unit_when_fingerprint_changes(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch_work_units")
    study_root = tmp_path / "studies" / "001-risk"
    latest_path = study_root / "artifacts" / "runtime" / "runtime_watch_wakeup" / "latest.json"
    latest_path.parent.mkdir(parents=True)
    latest_path.write_text(
        json.dumps(
            {
                "outcome": "dispatched",
                "work_unit_dispatch_key": "publication-blockers::old::submission_minimal_refresh::run_gate_clearing_batch",
            }
        ),
        encoding="utf-8",
    )
    tick_request = {
        "work_unit_fingerprint": "publication-blockers::new",
        "next_work_unit": {"unit_id": "submission_minimal_refresh"},
        "controller_actions": [{"action_type": "run_gate_clearing_batch"}],
    }

    already_executed, dispatch_key = module.dispatch_already_executed(
        study_root=study_root,
        tick_request=tick_request,
    )

    assert already_executed is False
    assert dispatch_key == "publication-blockers::new::submission_minimal_refresh::run_gate_clearing_batch"
