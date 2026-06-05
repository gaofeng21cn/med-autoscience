from __future__ import annotations

import hashlib

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_watch_runtime_closes_opl_runtime_handoff_when_inputs_show_gate_delta(
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
            include_authority_snapshot=True,
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
        event_type="opl_runtime_handoff_required",
        payload={
            "source": "domain_health_diagnostic_outer_loop_wakeup",
            "wakeup_outcome": "opl_runtime_handoff_required",
            "wakeup_reason": "outer-loop work unit redrive budget exhausted without result evidence",
        },
        recorded_at="2026-05-02T04:45:16+00:00",
    )
    latest_path = study_root / "artifacts" / "runtime" / "domain_health_diagnostic_wakeup" / "latest.json"
    dump_json(
        latest_path,
        {
            "outcome": "opl_runtime_handoff_required",
            "work_unit_dispatch_key": identity.dispatch_key,
            "input_fingerprint": "old-input",
            "watched_inputs": {
                "artifacts": {
                    "publication_eval_latest": {"sha256": "old-eval", "mtime_ns": 1},
                    "publication_gate_latest": {"sha256": "old-gate", "mtime_ns": 1},
                }
            },
        },
    )
    dump_json(
        quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json",
        {
            "schema_version": 1,
            "generated_at": "2026-05-02T05:00:00+00:00",
            "status": "blocked",
            "gate_fingerprint": "publication-gate::new",
        },
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
    wakeup_latest = json.loads(latest_path.read_text(encoding="utf-8"))
    ledger_events = [
        json.loads(line)
        for line in (
            study_root / "artifacts" / "runtime" / "work_unit_ledger" / "events.jsonl"
        ).read_text(encoding="utf-8").splitlines()
    ]

    assert calls == ["domain_health_diagnostic_outer_loop_wakeup"]
    assert len(result["managed_study_outer_loop_dispatches"]) == 1
    assert result["managed_study_no_op_suppressions"] == []
    assert wakeup_latest["outcome"] == "dispatched"
    assert [event["event_type"] for event in ledger_events] == [
        "opl_runtime_handoff_required",
        "closed",
        "dispatched",
    ]
    assert ledger_events[1]["payload"]["gate_fingerprint_before"] == "old-gate"
    assert ledger_events[1]["payload"]["gate_fingerprint_after"] != "old-gate"


def test_watch_runtime_closes_opl_runtime_handoff_when_inputs_show_controller_result_delta(
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
            include_authority_snapshot=True,
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
        "decision_type": "route_back_same_line",
        "route_target": "write",
        "route_key_question": "manuscript_story_repair: Repair story-facing manuscript blockers.",
        "route_rationale": "Run bounded manuscript story repair.",
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "run_quality_repair_batch",
                "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
            }
        ],
        "reason": "Run bounded manuscript story repair.",
        "work_unit_fingerprint": "publication-blockers::story",
        "next_work_unit": {
            "unit_id": "manuscript_story_repair",
            "lane": "write",
            "summary": "Repair story-facing manuscript blockers.",
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
        event_type="opl_runtime_handoff_required",
        payload={
            "source": "domain_health_diagnostic_outer_loop_wakeup",
            "wakeup_outcome": "opl_runtime_handoff_required",
            "wakeup_reason": "outer-loop work unit redrive budget exhausted without result evidence",
        },
        recorded_at="2026-05-02T04:45:16+00:00",
    )
    latest_path = study_root / "artifacts" / "runtime" / "domain_health_diagnostic_wakeup" / "latest.json"
    dump_json(
        latest_path,
        {
            "outcome": "opl_runtime_handoff_required",
            "work_unit_dispatch_key": identity.dispatch_key,
            "input_fingerprint": "old-input",
            "watched_inputs": {
                "artifacts": {
                    "publication_eval_latest": {
                        "sha256": hashlib.sha256(
                            (study_root / "artifacts" / "publication_eval" / "latest.json").read_bytes()
                        ).hexdigest(),
                    },
                    "publication_gate_latest": {"exists": False},
                    "quality_repair_batch_latest": {"sha256": "old-quality"},
                    "gate_clearing_batch_latest": {"sha256": "old-gate-batch"},
                    "repair_execution_evidence_latest": {"sha256": "old-repair-evidence"},
                    "publication_work_unit_lifecycle_latest": {"sha256": "old-lifecycle"},
                }
            },
        },
    )
    dump_json(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json",
        {
            "schema_version": 1,
            "status": "executed",
            "ok": True,
            "gate_clearing_batch": {
                "status": "executed",
                "publication_work_unit_lifecycle": {
                    "status": "blocked",
                    "work_unit": {"unit_id": "manuscript_story_repair"},
                },
            },
        },
    )
    dump_json(
        study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json",
        {
            "schema_version": 1,
            "status": "progress_delta_candidate",
            "repair_work_unit": {"unit_id": "manuscript_story_repair"},
            "changed_artifact_refs": [
                {"path": str((study_root / "paper" / "draft.md").resolve()), "fingerprint": {"sha256": "draft-new"}}
            ],
            "quality_authorized": False,
            "submission_authorized": False,
            "current_package_write_authorized": False,
        },
    )
    dump_json(
        study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json",
        {
            "schema_version": 1,
            "status": "executed",
            "publication_work_unit_lifecycle": {
                "status": "blocked",
                "work_unit": {"unit_id": "manuscript_story_repair"},
            },
        },
    )
    dump_json(
        study_root / "artifacts" / "controller" / "publication_work_unit_lifecycle" / "latest.json",
        {
            "schema_version": 1,
            "status": "blocked",
            "work_unit": {"unit_id": "manuscript_story_repair"},
            "unit_statuses": [{"unit_id": "repair_paper_live_paths", "status": "current"}],
        },
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
            "executed_controller_action": {
                "action_type": "run_quality_repair_batch",
                "result": {"status": "executed"},
            },
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
    ledger_events = [
        json.loads(line)
        for line in (
            study_root / "artifacts" / "runtime" / "work_unit_ledger" / "events.jsonl"
        ).read_text(encoding="utf-8").splitlines()
    ]

    assert calls == ["domain_health_diagnostic_outer_loop_wakeup"]
    assert len(result["managed_study_outer_loop_dispatches"]) == 1
    assert result["managed_study_no_op_suppressions"] == []
    assert [event["event_type"] for event in ledger_events] == [
        "opl_runtime_handoff_required",
        "closed",
        "dispatched",
    ]
    closed_payload = ledger_events[1]["payload"]
    assert closed_payload["closure_reason"] == "meaningful_artifact_delta_after_opl_runtime_handoff"
    assert closed_payload["controller_result_artifact_deltas"]


def test_watch_runtime_closes_opl_runtime_handoff_when_ai_reviewer_request_becomes_executable(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    ledger = importlib.import_module("med_autoscience.controllers.work_unit_ledger")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "003-dpcc")
    quest_root = profile.runtime_root / "quest-003"
    _write_charter(study_root)
    _write_publication_eval(study_root, quest_root, action_type="continue_same_line")
    status_payload = {
        **make_progress_projection_payload(
            study_id="003-dpcc",
            decision="blocked",
            reason="quest_waiting_opl_runtime_owner_route",
            include_authority_snapshot=True,
        ),
        "study_root": str(study_root),
        "quest_id": "quest-003",
        "quest_root": str(quest_root),
        "quest_status": "paused",
    }
    tick_request = {
        "study_root": study_root,
        "charter_ref": _write_charter(study_root),
        "publication_eval_ref": _write_publication_eval(study_root, quest_root, action_type="continue_same_line"),
        "decision_type": "continue_same_line",
        "route_target": "review",
        "route_key_question": "当前稿件是否已经通过 AI reviewer-owned publication evaluation？",
        "route_rationale": "Rebuild AI reviewer quality authority.",
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "return_to_ai_reviewer_workflow",
                "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
            }
        ],
        "reason": "Rebuild AI reviewer quality authority.",
        "work_unit_fingerprint": "domain-transition::ai_reviewer_re_eval::ai_reviewer_recheck",
        "next_work_unit": {
            "unit_id": "ai_reviewer_recheck",
            "lane": "review",
            "summary": "Return the current manuscript and evidence refs to the AI reviewer workflow.",
        },
    }
    identity = module.domain_health_diagnostic_work_units.identity_from_tick_request(
        study_id="003-dpcc",
        quest_id="quest-003",
        tick_request=tick_request,
    )
    assert identity is not None
    ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type="opl_runtime_handoff_required",
        payload={
            "source": "domain_health_diagnostic_outer_loop_wakeup",
            "wakeup_outcome": "opl_runtime_handoff_required",
            "wakeup_reason": "outer-loop work unit redrive budget exhausted without result evidence",
        },
        recorded_at="2026-06-05T00:30:00+00:00",
    )
    latest_path = study_root / "artifacts" / "runtime" / "domain_health_diagnostic_wakeup" / "latest.json"
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    dump_json(
        latest_path,
        {
            "outcome": "opl_runtime_handoff_required",
            "work_unit_dispatch_key": identity.dispatch_key,
            "input_fingerprint": "old-input",
            "watched_inputs": {
                "artifacts": {
                    "ai_reviewer_request_latest": {
                        "path": str(request_path.resolve()),
                        "exists": True,
                        "stable_payload_sha256": "old-request",
                        "stable_payload": {
                            "request_kind": "return_to_ai_reviewer_workflow",
                            "request_owner": "ai_reviewer",
                            "request_lifecycle": {
                                "all_required_refs_present": True,
                                "blocked_reason": "paper_authority_clean_migration_required",
                            },
                            "required_inputs": {},
                            "required_refs": {},
                        },
                    },
                    "publication_eval_latest": {"sha256": "eval-same"},
                    "publication_gate_latest": {"sha256": "gate-same"},
                }
            },
        },
    )
    dump_json(
        request_path,
        {
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "request_lifecycle": {
                "request_packet_materialized": True,
                "all_required_refs_present": True,
                "blocked_reason": None,
            },
            "required_inputs": {
                "manuscript_ref": str((study_root / "paper" / "draft.md").resolve()),
                "evidence_ledger_ref": str((study_root / "paper" / "evidence_ledger.json").resolve()),
                "review_ledger_ref": str((study_root / "paper" / "review" / "review_ledger.json").resolve()),
                "study_charter_ref": str((study_root / "artifacts" / "controller" / "study_charter.json").resolve()),
            },
            "input_contract": {
                "required_refs": {
                    "manuscript": {
                        "path": str((study_root / "paper" / "draft.md").resolve()),
                        "present": True,
                        "valid": True,
                    },
                    "evidence_ledger": {
                        "path": str((study_root / "paper" / "evidence_ledger.json").resolve()),
                        "present": True,
                        "valid": True,
                    },
                    "review_ledger": {
                        "path": str((study_root / "paper" / "review" / "review_ledger.json").resolve()),
                        "present": True,
                        "valid": True,
                    },
                    "study_charter": {
                        "path": str((study_root / "artifacts" / "controller" / "study_charter.json").resolve()),
                        "present": True,
                        "valid": True,
                    },
                }
            },
        },
    )
    calls: list[str] = []

    def fake_outer_loop_tick(**kwargs):
        calls.append(str(kwargs.get("source") or ""))
        return {
            "study_id": "003-dpcc",
            "quest_id": "quest-003",
            "source": kwargs.get("source"),
            "study_decision_ref": {
                "artifact_path": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve())
            },
            "dispatch_status": "executed",
            "executed_controller_action": {
                "action_type": "return_to_ai_reviewer_workflow",
                "result": {"status": "executed"},
            },
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
    wakeup_latest = json.loads(latest_path.read_text(encoding="utf-8"))
    ledger_events = [
        json.loads(line)
        for line in (
            study_root / "artifacts" / "runtime" / "work_unit_ledger" / "events.jsonl"
        ).read_text(encoding="utf-8").splitlines()
    ]

    assert calls == ["domain_health_diagnostic_outer_loop_wakeup"]
    assert len(result["managed_study_outer_loop_dispatches"]) == 1
    assert result["managed_study_no_op_suppressions"] == []
    assert wakeup_latest["outcome"] == "dispatched"
    assert [event["event_type"] for event in ledger_events] == [
        "opl_runtime_handoff_required",
        "closed",
        "dispatched",
    ]
    assert ledger_events[1]["payload"]["ai_reviewer_request_ref"] == str(request_path.resolve())
    assert ledger_events[1]["payload"]["ai_reviewer_request_fingerprint_before"] == "old-request"
    assert ledger_events[1]["payload"]["ai_reviewer_request_fingerprint_after"] != "old-request"
