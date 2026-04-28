from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_watch_runtime_suppresses_repeated_work_unit_dispatch(
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

    assert calls == ["runtime_watch_outer_loop_wakeup"]
    assert len(first["managed_study_outer_loop_dispatches"]) == 1
    assert second["managed_study_outer_loop_dispatches"] == []
    assert second["managed_study_no_op_suppressions"] == [
        {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "outcome": "skipped_matching_work_unit",
            "reason": "outer-loop work unit already dispatched for the same blocker fingerprint",
            "dedupe_scope": "controller_decision_blocker_authority",
            "work_unit_fingerprint": "publication-blockers::same",
            "next_work_unit": {
                "unit_id": "analysis_claim_evidence_repair",
                "lane": "analysis-campaign",
                "summary": "Repair claim-evidence blockers.",
            },
            "operator_summary": "同一 blocker fingerprint 已执行过同一 controller work unit；继续空转不会增加论文证据。",
        }
    ]
    assert [event["event_type"] for event in ledger_events] == ["dispatched", "skipped_duplicate"]
    assert wakeup_latest["outcome"] == "skipped_matching_work_unit"
    assert wakeup_latest["no_op_acknowledged"] is True
    assert wakeup_latest["dedupe_scope"] == "controller_decision_blocker_authority"
    assert wakeup_latest["operator_summary"] == (
        "同一 blocker fingerprint 已执行过同一 controller work unit；继续空转不会增加论文证据。"
    )
    assert wakeup_latest["work_unit_dispatch_key"] == (
        "publication-blockers::same::analysis_claim_evidence_repair::run_gate_clearing_batch"
    )


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


def test_work_unit_dedupe_reuses_prior_upstream_unit_when_blocker_fingerprint_churns(tmp_path: Path) -> None:
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

    assert already_executed is True
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

    assert already_executed is True
    assert dispatch_key == "publication-blockers::same::analysis_claim_evidence_repair::run_gate_clearing_batch"


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


def test_work_unit_dedupe_uses_ledger_for_prior_upstream_unit_when_fingerprint_churns(tmp_path: Path) -> None:
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

    assert already_executed is True
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
