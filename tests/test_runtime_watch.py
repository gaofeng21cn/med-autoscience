from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_quest(tmp_path: Path, name: str, status: str = "running") -> Path:
    quest_root = tmp_path / "runtime" / "quests" / name
    dump_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "quest_id": name,
            "status": status,
            "active_run_id": "run-1" if status in {"running", "active"} else None,
        },
    )
    return quest_root


def make_study_runtime_status_payload(
    *,
    study_id: str = "001-risk",
    decision: str = "create_and_start",
    reason: str = "quest_missing",
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "study_id": study_id,
        "study_root": f"/tmp/studies/{study_id}",
        "entry_mode": "full_research",
        "execution": {"quest_id": study_id, "auto_resume": True},
        "quest_id": study_id,
        "quest_root": f"/tmp/runtime/quests/{study_id}",
        "quest_exists": True,
        "quest_status": "created",
        "runtime_binding_path": f"/tmp/studies/{study_id}/runtime_binding.yaml",
        "runtime_binding_exists": True,
        "study_completion_contract": {},
        "decision": decision,
        "reason": reason,
    }


def _write_runtime_escalation_record(quest_root: Path, study_root: Path) -> dict[str, str]:
    protocol = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    dump_json(
        study_root / "artifacts" / "runtime" / "last_launch_report.json",
        {
            "recorded_at": "2026-04-05T05:54:00+00:00",
            "decision": "blocked",
            "reason": "quest_stopped_requires_explicit_rerun",
        },
    )
    record = protocol.RuntimeEscalationRecord(
        schema_version=1,
        record_id="runtime-escalation::001-risk::quest-001::quest_stopped_requires_explicit_rerun::2026-04-05T05:55:00+00:00",
        study_id="001-risk",
        quest_id="quest-001",
        emitted_at="2026-04-05T05:55:00+00:00",
        trigger=protocol.RuntimeEscalationTrigger(
            trigger_id="quest_stopped_requires_explicit_rerun",
            source="runtime_watch",
        ),
        scope="quest",
        severity="quest",
        reason="quest_stopped_requires_explicit_rerun",
        recommended_actions=("controller_review_required",),
        evidence_refs=(str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),),
        runtime_context_refs={"launch_report_path": str(study_root / "artifacts" / "runtime" / "last_launch_report.json")},
        summary_ref=str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
    )
    return protocol.write_runtime_escalation_record(quest_root=quest_root, record=record).ref().to_dict()


def _write_runtime_event_record(
    quest_root: Path,
    study_root: Path,
    *,
    runtime_escalation_ref: dict[str, str],
) -> dict[str, str]:
    protocol = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    record = protocol.RuntimeEventRecord(
        schema_version=1,
        event_id="runtime-event::001-risk::quest-001::status_observed::2026-04-05T05:56:00+00:00",
        study_id="001-risk",
        quest_id="quest-001",
        emitted_at="2026-04-05T05:56:00+00:00",
        event_source="study_runtime_status",
        event_kind="status_observed",
        summary_ref=str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
        status_snapshot={
            "quest_status": "stopped",
            "decision": "blocked",
            "reason": "quest_stopped_requires_explicit_rerun",
            "active_run_id": None,
            "runtime_liveness_status": "none",
            "worker_running": False,
            "continuation_policy": None,
            "continuation_reason": None,
            "supervisor_tick_status": "fresh",
            "controller_owned_finalize_parking": False,
            "runtime_escalation_ref": runtime_escalation_ref,
        },
        outer_loop_input={
            "quest_status": "stopped",
            "decision": "blocked",
            "reason": "quest_stopped_requires_explicit_rerun",
            "active_run_id": None,
            "runtime_liveness_status": "none",
            "worker_running": False,
            "supervisor_tick_status": "fresh",
            "controller_owned_finalize_parking": False,
            "interaction_action": None,
            "interaction_requires_user_input": False,
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )
    return protocol.write_runtime_event_record(quest_root=quest_root, record=record).ref().to_dict()


def _write_charter(study_root: Path) -> dict[str, str]:
    payload = {
        "schema_version": 1,
        "charter_id": "charter::001-risk::v1",
        "study_id": "001-risk",
        "publication_objective": "risk stratification external validation",
    }
    dump_json(study_root / "artifacts" / "controller" / "study_charter.json", payload)
    return {
        "charter_id": payload["charter_id"],
        "artifact_path": str((study_root / "artifacts" / "controller" / "study_charter.json").resolve()),
    }


def _write_publication_eval(
    study_root: Path,
    quest_root: Path,
    *,
    action_type: str = "continue_same_line",
    reason: str = "Controller should continue the same study line.",
) -> dict[str, str]:
    if action_type == "bounded_analysis":
        route_target = "analysis-campaign"
        route_key_question = "What is the narrowest supplementary analysis still required before the paper line can continue?"
        route_rationale = "The current line is clear enough to continue after one bounded supplementary analysis pass."
    elif action_type == "continue_same_line":
        route_target = "write"
        route_key_question = "What is the narrowest same-line manuscript repair or continuation step required now?"
        route_rationale = "The publication gate is clear and the current paper line can continue through same-line manuscript work."
    else:
        route_target = None
        route_key_question = None
        route_rationale = None
    payload = {
        "schema_version": 1,
        "eval_id": f"publication-eval::001-risk::quest-001::{action_type}::2026-04-05T05:58:00+00:00",
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
            "submission_minimal_ref": str((study_root / "paper" / "submission_minimal" / "submission_manifest.json").resolve()),
        },
        "verdict": {
            "overall_verdict": "promising",
            "primary_claim_status": "supported",
            "summary": "Primary claim is ready to continue on the same line.",
            "stop_loss_pressure": "none",
        },
        "gaps": [
            {
                "gap_id": "gap-001",
                "gap_type": "evidence",
                "severity": "important",
                "summary": "External validation can still improve robustness.",
                "evidence_refs": [str((quest_root / "artifacts" / "results" / "main_result.json").resolve())],
            }
        ],
        "recommended_actions": [
            {
                "action_id": f"action::{action_type}",
                "action_type": action_type,
                "priority": "now",
                "reason": reason,
                **(
                    {
                        "route_target": route_target,
                        "route_key_question": route_key_question,
                        "route_rationale": route_rationale,
                    }
                    if route_target is not None
                    else {}
                ),
                "evidence_refs": [str((study_root / "artifacts" / "publication_eval" / "latest.json").resolve())],
                "requires_controller_decision": True,
            }
        ],
    }
    dump_json(study_root / "artifacts" / "publication_eval" / "latest.json", payload)
    return {
        "eval_id": payload["eval_id"],
        "artifact_path": str((study_root / "artifacts" / "publication_eval" / "latest.json").resolve()),
    }


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
                    "route_key_question": "What is the narrowest finalize or submission-bundle step still required on the current paper line?",
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
                "route_key_question": "What is the narrowest finalize or submission-bundle step still required on the current paper line?",
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
            "route_key_question": "What is the narrowest finalize or submission-bundle step still required on the current paper line?",
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
        "What is the narrowest finalize or submission-bundle step still required on the current paper line?"
    )
    assert action.route_rationale == "bundle-stage blockers are now on the critical path for this paper line"

def test_runtime_watch_uses_runtime_watch_protocol_helpers(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")
    seen: dict[str, object] = {}

    def fake_load_watch_state(path: Path) -> object:
        seen["loaded"] = str(path)
        return module.runtime_watch_protocol.RuntimeWatchState(
            schema_version=1,
            updated_at=None,
            controllers={},
        )

    def fake_plan_controller_intervention(**kwargs) -> object:
        seen.setdefault("planned", []).append(kwargs)
        return module.runtime_watch_protocol.RuntimeWatchInterventionPlan(
            action=module.runtime_watch_protocol.RuntimeWatchControllerAction.APPLIED,
            should_apply=True,
            suppression_reason=None,
            controller_state=module.runtime_watch_protocol.RuntimeWatchControllerState(
                last_seen_fingerprint="fp-1",
                last_applied_fingerprint="fp-1",
                last_applied_at="2026-04-02T12:00:00+00:00",
                last_status="blocked",
                last_suppression_reason=None,
            ),
        )

    monkeypatch.setattr(
        module.runtime_watch_protocol,
        "load_watch_state",
        fake_load_watch_state,
    )
    monkeypatch.setattr(
        module.runtime_watch_protocol,
        "plan_controller_intervention",
        fake_plan_controller_intervention,
    )
    monkeypatch.setattr(
        module.runtime_watch_protocol,
        "save_watch_state",
        lambda quest_root, payload: seen.setdefault("saved", []).append((str(quest_root), payload)),
    )
    monkeypatch.setattr(
        module.runtime_watch_protocol,
        "write_watch_report",
        lambda *, quest_root, report, markdown: seen.setdefault("reported", []).append((str(quest_root), report))
        or (quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json", quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.md"),
    )

    result = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={
            "publication_gate": lambda *, quest_root, apply: {
                "status": "blocked",
                "blockers": ["missing_post_main_publishability_gate"],
                "allow_write": False,
                "missing_non_scalar_deliverables": ["calibration_plot"],
                "submission_minimal_present": False,
                "report_json": "dry.json",
                "report_markdown": "dry.md",
            }
        },
        apply=True,
    )

    assert seen["loaded"] == str(quest_root)
    assert len(seen["planned"]) == 1
    assert len(seen["saved"]) == 1
    assert len(seen["reported"]) == 1
    saved_state = seen["saved"][0][1]
    assert saved_state.controllers["publication_gate"].last_applied_fingerprint is not None
    assert result["controllers"]["publication_gate"]["action"] == "applied"


def test_runtime_watch_preserves_publication_supervisor_summary(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")

    result = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={
            "publication_gate": lambda *, quest_root, apply: {
                "status": "blocked",
                "blockers": ["missing_post_main_publishability_gate"],
                "allow_write": False,
                "missing_non_scalar_deliverables": [],
                "submission_minimal_present": True,
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": [],
                "controller_stage_note": "bundle suggestions are downstream-only until the publication gate allows write",
                "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
                "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
            }
        },
        apply=False,
    )

    controller = result["controllers"]["publication_gate"]
    assert controller["supervisor_phase"] == "publishability_gate_blocked"
    assert controller["phase_owner"] == "publication_gate"
    assert controller["upstream_scientific_anchor_ready"] is True
    assert controller["bundle_tasks_downstream_only"] is True
    assert controller["current_required_action"] == "return_to_publishability_gate"
    assert controller["deferred_downstream_actions"] == []
    assert "downstream-only" in controller["controller_stage_note"]


def test_runtime_watch_applies_publication_gate_when_clear_status_still_needs_draft_handoff_sync(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        return {
            "status": "clear",
            "blockers": [],
            "allow_write": True,
            "missing_non_scalar_deliverables": [],
            "submission_minimal_present": False,
            "draft_handoff_delivery_required": True,
            "draft_handoff_delivery_status": "missing",
            "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
        }

    result = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"publication_gate": fake_runner},
        apply=True,
    )

    assert calls == [False, True]
    assert result["controllers"]["publication_gate"]["action"] == "applied"


def test_runtime_watch_does_not_reapply_after_draft_handoff_sync_stabilizes(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []
    state = {"draft_handoff_synced": False}

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        if apply:
            state["draft_handoff_synced"] = True
        status = "current" if state["draft_handoff_synced"] else "missing"
        return {
            "status": "blocked",
            "blockers": ["medical_publication_surface_blocked"],
            "allow_write": False,
            "missing_non_scalar_deliverables": [],
            "submission_minimal_present": False,
            "draft_handoff_delivery_required": True,
            "draft_handoff_delivery_status": status,
            "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
        }

    first = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"publication_gate": fake_runner},
        apply=True,
    )
    second = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"publication_gate": fake_runner},
        apply=True,
    )

    assert first["controllers"]["publication_gate"]["action"] == "applied"
    assert second["controllers"]["publication_gate"]["action"] == "suppressed"
    assert calls == [False, True, False]


def test_build_default_controller_runners_includes_figure_loop_guard() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    runners = module.build_default_controller_runners()
    assert "figure_loop_guard" in runners


def test_runtime_watch_registers_medical_runtime_audits() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    runners = module.build_default_controller_runners()

    assert "medical_literature_audit" in runners
    assert "medical_reporting_audit" in runners


def test_runtime_watch_orders_publication_surface_before_gate(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[tuple[str, bool]] = []
    state = {"surface_blocked": False}

    def fake_medical_publication_surface(*, quest_root: Path, apply: bool) -> dict:
        calls.append(("medical_publication_surface", apply))
        if apply:
            state["surface_blocked"] = True
        return {
            "status": "blocked",
            "blockers": ["methods_section_structure_missing_or_incomplete"],
            "report_json": str(quest_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.md"),
            "top_hits": [
                {
                    "path": "paper/draft.md",
                    "location": "line 33",
                    "phrase": "Methods",
                }
            ],
            "intervention_enqueued": apply,
        }

    def fake_publication_gate(*, quest_root: Path, apply: bool) -> dict:
        calls.append(("publication_gate", apply))
        blocked = state["surface_blocked"]
        return {
            "status": "blocked" if blocked else "clear",
            "blockers": ["medical_publication_surface_blocked"] if blocked else [],
            "allow_write": not blocked,
            "missing_non_scalar_deliverables": [],
            "submission_minimal_present": True,
            "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
            "intervention_enqueued": apply,
        }

    result = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={
            "publication_gate": fake_publication_gate,
            "medical_publication_surface": fake_medical_publication_surface,
        },
        apply=True,
    )

    assert result["controllers"]["medical_publication_surface"]["status"] == "blocked"
    assert result["controllers"]["publication_gate"]["status"] == "blocked"
    assert result["controllers"]["publication_gate"]["blockers"] == ["medical_publication_surface_blocked"]
    assert calls == [
        ("medical_publication_surface", False),
        ("medical_publication_surface", True),
        ("publication_gate", False),
        ("publication_gate", True),
    ]


def test_suppresses_duplicate_blocker(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        return {
            "status": "blocked",
            "blockers": ["forbidden_manuscript_terms_present"],
            "report_json": str(quest_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.md"),
            "top_hits": [{"path": "paper/draft.md", "location": "line 1", "phrase": "deployment-facing"}],
            "intervention_enqueued": apply,
        }

    first = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"medical_publication_surface": fake_runner},
        apply=True,
    )
    second = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"medical_publication_surface": fake_runner},
        apply=True,
    )

    assert first["controllers"]["medical_publication_surface"]["action"] == "applied"
    assert second["controllers"]["medical_publication_surface"]["action"] == "suppressed"
    assert calls == [False, True, False]


def test_suppresses_duplicate_figure_loop_guard_blocker(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        return {
            "status": "blocked",
            "blockers": ["figure_loop_budget_exceeded"],
            "dominant_figure_id": "F4B",
            "dominant_figure_mentions": 18,
            "reference_count": 7,
            "report_json": str(quest_root / "artifacts" / "reports" / "figure_loop_guard" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "figure_loop_guard" / "latest.md"),
            "intervention_enqueued": apply,
        }

    first = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"figure_loop_guard": fake_runner},
        apply=True,
    )
    second = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"figure_loop_guard": fake_runner},
        apply=True,
    )

    assert first["controllers"]["figure_loop_guard"]["action"] == "applied"
    assert second["controllers"]["figure_loop_guard"]["action"] == "suppressed"
    assert calls == [False, True, False]


def test_runtime_watch_surfaces_deferred_figure_loop_guard_stop(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        return {
            "status": "blocked",
            "blockers": ["figure_loop_budget_exceeded"],
            "dominant_figure_id": "F4B",
            "dominant_figure_mentions": 18,
            "reference_count": 7,
            "report_json": str(quest_root / "artifacts" / "reports" / "figure_loop_guard" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "figure_loop_guard" / "latest.md"),
            "intervention_enqueued": apply,
            "quest_stop_applied": False,
            "quest_stop_deferred": apply,
            "quest_stop_defer_reason": "self_owned_runtime_watch" if apply else None,
        }

    result = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"figure_loop_guard": fake_runner},
        apply=True,
    )

    controller = result["controllers"]["figure_loop_guard"]
    assert controller["action"] == "applied"
    assert controller["quest_stop_applied"] is False
    assert controller["quest_stop_deferred"] is True
    assert controller["quest_stop_defer_reason"] == "self_owned_runtime_watch"


def test_suppresses_duplicate_medical_literature_audit_blocker_even_when_report_paths_change(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []
    state = {"run": 0}

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        state["run"] += 1
        suffix = f"scan-{state['run']}"
        return {
            "status": "blocked",
            "blockers": ["reference_gaps_present"],
            "action": "clear",
            "missing_pmids": ["12345"],
            "report_json": str(quest_root / "artifacts" / "reports" / "medical_literature_audit" / f"{suffix}.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "medical_literature_audit" / f"{suffix}.md"),
        }

    first = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"medical_literature_audit": fake_runner},
        apply=True,
    )
    second = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"medical_literature_audit": fake_runner},
        apply=True,
    )

    assert first["controllers"]["medical_literature_audit"]["action"] == "applied"
    assert second["controllers"]["medical_literature_audit"]["action"] == "suppressed"
    assert calls == [False, True, False]


def test_suppresses_duplicate_medical_reporting_audit_blocker_even_when_report_paths_change(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []
    state = {"run": 0}

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        state["run"] += 1
        suffix = f"scan-{state['run']}"
        return {
            "status": "blocked",
            "blockers": ["missing_reporting_guideline_checklist"],
            "action": "clear",
            "report_json": str(quest_root / "artifacts" / "reports" / "medical_reporting_audit" / f"{suffix}.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "medical_reporting_audit" / f"{suffix}.md"),
        }

    first = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"medical_reporting_audit": fake_runner},
        apply=True,
    )
    second = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"medical_reporting_audit": fake_runner},
        apply=True,
    )

    assert first["controllers"]["medical_reporting_audit"]["action"] == "applied"
    assert second["controllers"]["medical_reporting_audit"]["action"] == "suppressed"
    assert calls == [False, True, False]


def test_blocked_with_apply_disabled_records_suppression_without_second_apply(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        return {
            "status": "blocked",
            "blockers": ["missing_post_main_publishability_gate"],
            "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
        }

    result = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"publication_gate": fake_runner},
        apply=False,
    )

    assert result["controllers"]["publication_gate"]["action"] == "suppressed"
    assert result["controllers"]["publication_gate"]["suppression_reason"] == "apply_disabled"
    assert calls == [False]


def test_controller_missing_artifacts_does_not_crash_runtime_watch(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")

    def missing_artifact_runner(*, quest_root: Path, apply: bool) -> dict:
        raise FileNotFoundError(f"No main RESULT.json found under {quest_root}")

    result = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"publication_gate": missing_artifact_runner},
        apply=True,
    )

    controller = result["controllers"]["publication_gate"]
    assert controller["status"] == "awaiting_artifacts"
    assert controller["action"] == "clear"
    assert controller["suppression_reason"] == "precondition_missing"
    assert "missing_artifact:No main RESULT.json found under" in controller["advisories"][0]


def test_reapplies_when_fingerprint_changes(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    quest_root = make_quest(tmp_path, "q001", status="running")
    state = {"value": "deployment-facing"}
    calls: list[bool] = []

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        return {
            "status": "blocked",
            "blockers": ["forbidden_manuscript_terms_present"],
            "report_json": str(quest_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.md"),
            "top_hits": [{"path": "paper/draft.md", "location": "line 1", "phrase": state["value"]}],
            "intervention_enqueued": apply,
        }

    first = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"medical_publication_surface": fake_runner},
        apply=True,
    )
    state["value"] = "baseline-comparable"
    second = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"medical_publication_surface": fake_runner},
        apply=True,
    )

    assert first["controllers"]["medical_publication_surface"]["action"] == "applied"
    assert second["controllers"]["medical_publication_surface"]["action"] == "applied"
    assert calls == [False, True, False, True]


def test_scan_runtime_processes_managed_quests_including_non_live_states(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    runtime_root = tmp_path / "runtime" / "quests"
    make_quest(tmp_path, "q-created", status="created")
    make_quest(tmp_path, "q-idle", status="idle")
    make_quest(tmp_path, "q-paused", status="paused")
    make_quest(tmp_path, "q-running", status="running")
    make_quest(tmp_path, "q-active", status="active")
    make_quest(tmp_path, "q-waiting", status="waiting_for_user")
    make_quest(tmp_path, "q-stopped", status="stopped")
    make_quest(tmp_path, "q-completed", status="completed")
    seen: list[str] = []

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        seen.append(quest_root.name)
        return {
            "status": "clear",
            "blockers": [],
            "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
            "intervention_enqueued": False,
        }

    result = module.run_watch_for_runtime(
        runtime_root=runtime_root,
        controller_runners={"publication_gate": fake_runner},
        apply=False,
    )

    assert sorted(seen) == ["q-active", "q-created", "q-idle", "q-paused", "q-running", "q-stopped", "q-waiting"]
    assert sorted(result["scanned_quests"]) == [
        "q-active",
        "q-created",
        "q-idle",
        "q-paused",
        "q-running",
        "q-stopped",
        "q-waiting",
    ]


def test_watch_runtime_can_ensure_managed_studies_before_scanning(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    profiles = importlib.import_module("med_autoscience.profiles")
    workspace_root = tmp_path / "workspace"
    profile = profiles.WorkspaceProfile(
        name="diabetes",
        workspace_root=workspace_root,
        runtime_root=workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests",
        studies_root=workspace_root / "studies",
        portfolio_root=workspace_root / "portfolio",
        med_deepscientist_runtime_root=workspace_root / "ops" / "med-deepscientist" / "runtime",
        med_deepscientist_repo_root=tmp_path / "med-deepscientist",
        default_publication_profile="general_medical_journal",
        default_citation_style="AMA",
        enable_medical_overlay=True,
        medical_overlay_scope="workspace",
        medical_overlay_skills=("intake-audit", "baseline"),
        research_route_bias_policy="high_plasticity_medical",
        preferred_study_archetypes=("clinical_classifier",),
        default_submission_targets=(),
    )
    study_root = profile.studies_root / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")

    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda *, profile, study_root, source: make_study_runtime_status_payload(
            study_id=Path(study_root).name,
            decision="create_and_start",
            reason="quest_missing",
        ),
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert result["managed_study_actions"] == [
        {"study_id": "001-risk", "decision": "create_and_start", "reason": "quest_missing"}
    ]


def test_watch_runtime_uses_typed_surface_attributes_for_managed_study_actions(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")
    profiles = importlib.import_module("med_autoscience.profiles")
    workspace_root = tmp_path / "workspace"
    profile = profiles.WorkspaceProfile(
        name="diabetes",
        workspace_root=workspace_root,
        runtime_root=workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests",
        studies_root=workspace_root / "studies",
        portfolio_root=workspace_root / "portfolio",
        med_deepscientist_runtime_root=workspace_root / "ops" / "med-deepscientist" / "runtime",
        med_deepscientist_repo_root=tmp_path / "med-deepscientist",
        default_publication_profile="general_medical_journal",
        default_citation_style="AMA",
        enable_medical_overlay=True,
        medical_overlay_scope="workspace",
        medical_overlay_skills=("intake-audit", "baseline"),
        research_route_bias_policy="high_plasticity_medical",
        preferred_study_archetypes=("clinical_classifier",),
        default_submission_targets=(),
    )
    study_root = profile.studies_root / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")

    class AttributeOnlyStudyRuntimeStatus(typed_surface.StudyRuntimeStatus):
        def __getitem__(self, key: str) -> object:
            raise AssertionError("runtime_watch should not use mapping access for typed study runtime status")

        def get(self, key: str, default: object | None = None) -> object | None:
            raise AssertionError("runtime_watch should not use mapping access for typed study runtime status")

    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda *, profile, study_root, source: AttributeOnlyStudyRuntimeStatus.from_payload(
            make_study_runtime_status_payload()
        ),
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert result["managed_study_actions"] == [
        {"study_id": "001-risk", "decision": "create_and_start", "reason": "quest_missing"}
    ]


def test_watch_runtime_uses_typed_surface_attributes_for_read_only_managed_study_actions(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")
    profiles = importlib.import_module("med_autoscience.profiles")
    workspace_root = tmp_path / "workspace"
    profile = profiles.WorkspaceProfile(
        name="diabetes",
        workspace_root=workspace_root,
        runtime_root=workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests",
        studies_root=workspace_root / "studies",
        portfolio_root=workspace_root / "portfolio",
        med_deepscientist_runtime_root=workspace_root / "ops" / "med-deepscientist" / "runtime",
        med_deepscientist_repo_root=tmp_path / "med-deepscientist",
        default_publication_profile="general_medical_journal",
        default_citation_style="AMA",
        enable_medical_overlay=True,
        medical_overlay_scope="workspace",
        medical_overlay_skills=("intake-audit", "baseline"),
        research_route_bias_policy="high_plasticity_medical",
        preferred_study_archetypes=("clinical_classifier",),
        default_submission_targets=(),
    )
    study_root = profile.studies_root / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")

    class AttributeOnlyStudyRuntimeStatus(typed_surface.StudyRuntimeStatus):
        def __getitem__(self, key: str) -> object:
            raise AssertionError("runtime_watch should not use mapping access for typed study runtime status")

        def get(self, key: str, default: object | None = None) -> object | None:
            raise AssertionError("runtime_watch should not use mapping access for typed study runtime status")

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda *, profile, study_root: AttributeOnlyStudyRuntimeStatus.from_payload(
            make_study_runtime_status_payload(decision="noop")
        ),
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert result["managed_study_actions"] == [
        {"study_id": "001-risk", "decision": "noop", "reason": "quest_missing"}
    ]


def test_watch_runtime_hard_recovers_active_no_live_resume_even_without_apply(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    profiles = importlib.import_module("med_autoscience.profiles")
    workspace_root = tmp_path / "workspace"
    profile = profiles.WorkspaceProfile(
        name="diabetes",
        workspace_root=workspace_root,
        runtime_root=workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests",
        studies_root=workspace_root / "studies",
        portfolio_root=workspace_root / "portfolio",
        med_deepscientist_runtime_root=workspace_root / "ops" / "med-deepscientist" / "runtime",
        med_deepscientist_repo_root=tmp_path / "med-deepscientist",
        default_publication_profile="general_medical_journal",
        default_citation_style="AMA",
        enable_medical_overlay=True,
        medical_overlay_scope="workspace",
        medical_overlay_skills=("intake-audit", "baseline"),
        research_route_bias_policy="high_plasticity_medical",
        preferred_study_archetypes=("clinical_classifier",),
        default_submission_targets=(),
    )
    study_root = profile.studies_root / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")
    quest_root = profile.runtime_root / "001-risk"
    calls: list[tuple[str, str]] = []

    def parked_status() -> dict[str, object]:
        return {
            **make_study_runtime_status_payload(
                study_id="001-risk",
                decision="resume",
                reason="quest_parked_on_unchanged_finalize_state",
            ),
            "study_root": str(study_root),
            "quest_root": str(quest_root),
            "quest_status": "active",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "001-risk",
                "auto_resume": True,
            },
            "continuation_state": {
                "quest_status": "active",
                "active_run_id": None,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "decision",
                "continuation_reason": "unchanged_finalize_state",
            },
            "runtime_liveness_audit": {
                "status": "none",
                "active_run_id": None,
                "runtime_audit": {
                    "status": "none",
                    "active_run_id": None,
                    "worker_running": False,
                    "worker_pending": False,
                    "stop_requested": False,
                },
            },
        }

    def recovered_status(*, source: str) -> dict[str, object]:
        return {
            **parked_status(),
            "decision": "resume",
            "reason": "quest_parked_on_unchanged_finalize_state",
            "quest_status": "running",
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-resumed",
                "runtime_audit": {
                    "status": "live",
                    "active_run_id": "run-resumed",
                    "worker_running": True,
                    "worker_pending": False,
                    "stop_requested": False,
                },
            },
            "autonomous_runtime_notice": {
                "active_run_id": "run-resumed",
            },
            "source": source,
        }

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda *, profile, study_root: calls.append(("status", Path(study_root).name)) or parked_status(),
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda *, profile, study_root, source: calls.append(("ensure", source))
        or recovered_status(source=source),
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert calls == [
        ("status", "001-risk"),
        ("ensure", "runtime_watch_auto_recovery"),
    ]
    assert result["managed_study_actions"] == [
        {
            "study_id": "001-risk",
            "decision": "resume",
            "reason": "quest_parked_on_unchanged_finalize_state",
        }
    ]
    assert result["managed_study_auto_recoveries"] == [
        {
            "study_id": "001-risk",
            "preflight_decision": "resume",
            "preflight_reason": "quest_parked_on_unchanged_finalize_state",
            "applied_decision": "resume",
            "applied_reason": "quest_parked_on_unchanged_finalize_state",
            "source": "runtime_watch_auto_recovery",
        }
    ]
    assert result["managed_study_supervision"][0]["health_status"] == "live"


def test_run_watch_for_runtime_auto_recovers_stopped_controller_guard_quest(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = profile.workspace_root / "studies" / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": "001-risk"})
    calls: list[tuple[str, str]] = []

    stopped_guard_status = {
        **make_study_runtime_status_payload(
            study_id="001-risk",
            decision="resume",
            reason="quest_stopped_by_controller_guard",
        ),
        "quest_status": "stopped",
        "runtime_liveness_audit": {
            "status": "none",
            "active_run_id": None,
            "runtime_audit": {
                "status": "none",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
    }
    recovered_status = {
        **stopped_guard_status,
        "quest_status": "running",
        "runtime_liveness_audit": {
            "status": "live",
            "active_run_id": "run-recovered",
            "runtime_audit": {
                "status": "live",
                "active_run_id": "run-recovered",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
        "autonomous_runtime_notice": {
            "active_run_id": "run-recovered",
        },
    }

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda *, profile, study_root: calls.append(("status", Path(study_root).name)) or stopped_guard_status,
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda *, profile, study_root, source: calls.append(("ensure", source)) or recovered_status,
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert calls == [
        ("status", "001-risk"),
        ("ensure", "runtime_watch_auto_recovery"),
    ]
    assert result["managed_study_auto_recoveries"] == [
        {
            "study_id": "001-risk",
            "preflight_decision": "resume",
            "preflight_reason": "quest_stopped_by_controller_guard",
            "applied_decision": "resume",
            "applied_reason": "quest_stopped_by_controller_guard",
            "source": "runtime_watch_auto_recovery",
        }
    ]


def test_run_watch_for_runtime_rechecks_managed_study_immediately_after_figure_loop_guard_stop(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = profile.workspace_root / "studies" / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": "001-risk"})
    quest_root = profile.runtime_root / "001-risk"
    dump_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "quest_id": "001-risk",
            "status": "running",
            "active_run_id": "run-live",
        },
    )
    calls: list[tuple[str, str]] = []

    live_status = {
        **make_study_runtime_status_payload(
            study_id="001-risk",
            decision="noop",
            reason="quest_already_running",
        ),
        "study_root": str(study_root),
        "quest_root": str(quest_root),
        "quest_status": "running",
        "runtime_liveness_audit": {
            "status": "live",
            "active_run_id": "run-live",
            "runtime_audit": {
                "status": "live",
                "active_run_id": "run-live",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
    }
    reroute_status = {
        **live_status,
        "decision": "resume",
        "reason": "quest_stale_decision_after_write_stage_ready",
        "publication_supervisor_state": {
            "supervisor_phase": "write_stage_ready",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": False,
            "current_required_action": "continue_write_stage",
            "deferred_downstream_actions": ["continue_bundle_stage"],
            "controller_stage_note": "write stage is clear and should continue",
        },
    }

    def fake_ensure(*, profile, study_root, source):
        calls.append(("ensure", source))
        if source == "runtime_watch":
            return live_status
        if source == "runtime_watch_controller_reroute":
            return reroute_status
        raise AssertionError(f"unexpected ensure source: {source}")

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fake_ensure)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [quest_root])
    monkeypatch.setattr(
        module,
        "run_watch_for_quest",
        lambda *, quest_root, controller_runners, apply: {
            "quest_root": str(quest_root),
            "quest_status": "running",
            "controllers": {
                "figure_loop_guard": {
                    "status": "blocked",
                    "action": "applied",
                    "blockers": ["figure_loop_budget_exceeded"],
                    "advisories": [],
                    "report_json": str(quest_root / "artifacts" / "reports" / "figure_loop_guard" / "latest.json"),
                    "report_markdown": str(quest_root / "artifacts" / "reports" / "figure_loop_guard" / "latest.md"),
                    "suppression_reason": None,
                    "quest_stop_applied": True,
                    "quest_stop_status": "stopped",
                    "quest_stop_deferred": False,
                    "quest_stop_defer_reason": None,
                }
            },
        },
    )

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert calls == [
        ("ensure", "runtime_watch"),
        ("ensure", "runtime_watch_controller_reroute"),
    ]
    assert result["managed_study_actions"] == [
        {
            "study_id": "001-risk",
            "decision": "resume",
            "reason": "quest_stale_decision_after_write_stage_ready",
        }
    ]
    assert result["managed_study_auto_recoveries"] == [
        {
            "study_id": "001-risk",
            "preflight_decision": "noop",
            "preflight_reason": "quest_already_running",
            "applied_decision": "resume",
            "applied_reason": "quest_stale_decision_after_write_stage_ready",
            "source": "runtime_watch_controller_reroute",
        }
    ]


def test_run_watch_for_runtime_tracks_stopped_auto_continuation_once_router_returns_resume(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = profile.workspace_root / "studies" / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": "001-risk"})
    calls: list[tuple[str, str]] = []

    resumed_stopped_status = {
        **make_study_runtime_status_payload(
            study_id="001-risk",
            decision="resume",
            reason="quest_waiting_on_invalid_blocking",
        ),
        "quest_status": "stopped",
        "execution": {
            "engine": "med-deepscientist",
            "auto_entry": "on_managed_research_intent",
            "quest_id": "001-risk",
            "auto_resume": True,
        },
        "publication_supervisor_state": {
            "supervisor_phase": "bundle_stage_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": False,
            "current_required_action": "complete_bundle_stage",
            "deferred_downstream_actions": [],
            "controller_stage_note": "bundle-stage blockers are now on the critical path for this paper line",
        },
        "continuation_state": {
            "quest_status": "stopped",
            "active_run_id": None,
            "continuation_policy": "auto",
            "continuation_anchor": "write",
            "continuation_reason": "decision:decision-continue-001",
            "runtime_state_path": str(profile.runtime_root / "001-risk" / ".ds" / "runtime_state.json"),
        },
        "family_checkpoint_lineage": {
            "resume_contract": {
                "resume_mode": "resume_from_checkpoint",
                "resume_handle": "study_runtime_status:001-risk:blocked",
                "human_gate_required": False,
            }
        },
        "runtime_liveness_audit": {
            "status": "none",
            "active_run_id": None,
            "runtime_audit": {
                "status": "none",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
    }

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda *, profile, study_root: calls.append(("status", Path(study_root).name)) or resumed_stopped_status,
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda *, profile, study_root, source: calls.append(("ensure", source)) or resumed_stopped_status,
    )
    monkeypatch.setattr(
        module,
        "_refresh_managed_study_status_after_ensure",
        lambda *, profile, study_root, status_payload: status_payload,
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert calls == [
        ("status", "001-risk"),
        ("ensure", "runtime_watch_auto_recovery"),
    ]
    assert result["managed_study_auto_recoveries"] == [
        {
            "study_id": "001-risk",
            "preflight_decision": "resume",
            "preflight_reason": "quest_waiting_on_invalid_blocking",
            "applied_decision": "resume",
            "applied_reason": "quest_waiting_on_invalid_blocking",
            "source": "runtime_watch_auto_recovery",
        }
    ]
    assert result["managed_study_supervision"][0]["health_status"] == "recovering"


def test_run_watch_for_runtime_does_not_project_blocked_explicit_rerun_as_recovering(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = profile.workspace_root / "studies" / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": "001-risk"})
    quest_root = profile.runtime_root / "001-risk"

    blocked_stopped_status = {
        **make_study_runtime_status_payload(
            study_id="001-risk",
            decision="blocked",
            reason="quest_stopped_requires_explicit_rerun",
        ),
        "study_root": str(study_root),
        "quest_root": str(quest_root),
        "quest_status": "stopped",
        "execution": {
            "engine": "med-deepscientist",
            "auto_entry": "on_managed_research_intent",
            "quest_id": "001-risk",
            "auto_resume": True,
        },
        "continuation_state": {
            "quest_status": "stopped",
            "active_run_id": None,
            "continuation_policy": "auto",
            "continuation_anchor": "write",
            "continuation_reason": "decision:decision-continue-001",
            "runtime_state_path": str(profile.runtime_root / "001-risk" / ".ds" / "runtime_state.json"),
        },
        "family_checkpoint_lineage": {
            "resume_contract": {
                "resume_mode": "resume_from_checkpoint",
                "resume_handle": "study_runtime_status:001-risk:blocked",
                "human_gate_required": False,
            }
        },
        "runtime_liveness_audit": {
            "status": "none",
            "active_run_id": None,
            "runtime_audit": {
                "status": "none",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
    }

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda *, profile, study_root: blocked_stopped_status,
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda **kwargs: pytest.fail("ensure_study_runtime should not run for blocked explicit rerun status"),
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert result["managed_study_actions"] == [
        {
            "study_id": "001-risk",
            "decision": "blocked",
            "reason": "quest_stopped_requires_explicit_rerun",
        }
    ]
    assert result["managed_study_auto_recoveries"] == []
    assert result["managed_study_supervision"][0]["health_status"] == "inactive"


def test_run_watch_for_runtime_does_not_auto_recover_submission_metadata_parking(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = profile.workspace_root / "studies" / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": "001-risk"})
    calls: list[tuple[str, str]] = []

    parked_status = {
        **make_study_runtime_status_payload(
            study_id="001-risk",
            decision="blocked",
            reason="quest_waiting_for_submission_metadata",
        ),
        "quest_status": "waiting_for_user",
        "execution": {
            "engine": "med-deepscientist",
            "auto_entry": "on_managed_research_intent",
            "quest_id": "001-risk",
            "auto_resume": True,
        },
        "continuation_state": {
            "quest_status": "waiting_for_user",
            "active_run_id": None,
            "continuation_policy": "wait_for_user_or_resume",
            "continuation_anchor": "decision",
            "continuation_reason": "paper_bundle_submitted",
            "runtime_state_path": str(profile.runtime_root / "001-risk" / ".ds" / "runtime_state.json"),
        },
        "runtime_liveness_audit": {
            "status": "none",
            "active_run_id": None,
            "runtime_audit": {
                "status": "none",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
    }

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda *, profile, study_root: calls.append(("status", Path(study_root).name)) or parked_status,
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda *, profile, study_root, source: calls.append(("ensure", source)) or parked_status,
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert calls == [("status", "001-risk")]
    assert result["managed_study_actions"] == [
        {
            "study_id": "001-risk",
            "decision": "blocked",
            "reason": "quest_waiting_for_submission_metadata",
        }
    ]
    assert result["managed_study_auto_recoveries"] == []


def test_watch_quest_writes_latest_runtime_watch_alias(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")

    result = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={
            "publication_gate": lambda *, quest_root, apply: {
                "status": "clear",
                "blockers": [],
                "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
                "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
            }
        },
        apply=False,
    )

    latest_json = quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json"
    latest_markdown = quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.md"

    assert result["latest_report_json"] == str(latest_json)
    assert result["latest_report_markdown"] == str(latest_markdown)
    assert latest_json.exists()
    assert latest_markdown.exists()


def test_watch_quest_emits_family_orchestration_companion_fields(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")

    result = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={
            "publication_gate": lambda *, quest_root, apply: {
                "status": "clear",
                "blockers": [],
                "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
                "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
            }
        },
        apply=False,
    )

    assert result["family_event_envelope"]["version"] == "family-event-envelope.v1"
    assert result["family_event_envelope"]["session"]["quest_id"] == "q001"
    assert result["family_event_envelope"]["session"]["active_run_id"] == "run-1"
    assert result["family_checkpoint_lineage"]["version"] == "family-checkpoint-lineage.v1"
    assert result["family_checkpoint_lineage"]["session"]["active_run_id"] == "run-1"
    assert result["family_human_gates"] == []


def test_watch_runtime_emits_family_orchestration_companion_fields(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    runtime_root = tmp_path / "runtime" / "quests"
    make_quest(tmp_path, "q001", status="running")

    result = module.run_watch_for_runtime(
        runtime_root=runtime_root,
        controller_runners={
            "publication_gate": lambda *, quest_root, apply: {
                "status": "clear",
                "blockers": [],
                "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
                "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
            }
        },
        apply=False,
    )

    assert result["family_event_envelope"]["version"] == "family-event-envelope.v1"
    assert result["family_event_envelope"]["payload"]["scanned_quest_count"] == 1
    assert result["family_checkpoint_lineage"]["version"] == "family-checkpoint-lineage.v1"
    assert result["family_human_gates"] == []


def test_watch_runtime_aggregates_publication_gate_human_confirmation_into_family_gates(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    runtime_root = tmp_path / "runtime" / "quests"
    make_quest(tmp_path, "q001", status="running")

    result = module.run_watch_for_runtime(
        runtime_root=runtime_root,
        controller_runners={
            "publication_gate": lambda *, quest_root, apply: {
                "status": "blocked",
                "blockers": ["human_confirmation_required"],
                "current_required_action": "human_confirmation_required",
                "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
                "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
            }
        },
        apply=False,
    )

    quest_report = result["reports"][0]
    quest_gate = quest_report["family_human_gates"][0]
    runtime_gate = result["family_human_gates"][0]

    assert quest_gate["version"] == "family-human-gate.v1"
    assert quest_gate["gate_kind"] == "publication_gate_human_confirmation"
    assert quest_gate["request_surface"]["surface_kind"] == "runtime_watch"
    assert runtime_gate == quest_gate
    assert result["family_event_envelope"]["human_gate_hint"]["gate_id"] == quest_gate["gate_id"]
    assert result["family_checkpoint_lineage"]["resume_contract"]["human_gate_required"] is True


def test_watch_runtime_writes_study_supervision_report_and_escalates_after_consecutive_failures(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    profiles = importlib.import_module("med_autoscience.profiles")
    workspace_root = tmp_path / "workspace"
    profile = profiles.WorkspaceProfile(
        name="diabetes",
        workspace_root=workspace_root,
        runtime_root=workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests",
        studies_root=workspace_root / "studies",
        portfolio_root=workspace_root / "portfolio",
        med_deepscientist_runtime_root=workspace_root / "ops" / "med-deepscientist" / "runtime",
        med_deepscientist_repo_root=tmp_path / "med-deepscientist",
        default_publication_profile="general_medical_journal",
        default_citation_style="AMA",
        enable_medical_overlay=True,
        medical_overlay_scope="workspace",
        medical_overlay_skills=("intake-audit", "baseline"),
        research_route_bias_policy="high_plasticity_medical",
        preferred_study_archetypes=("clinical_classifier",),
        default_submission_targets=(),
    )
    study_root = profile.studies_root / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")
    quest_root = profile.runtime_root / "001-risk"
    launch_report_path = study_root / "artifacts" / "runtime" / "last_launch_report.json"
    dump_json(
        launch_report_path,
        {
            "recorded_at": "2026-04-10T09:05:00+00:00",
            "source": "runtime_watch",
            "decision": "blocked",
            "reason": "resume_request_failed",
        },
    )

    def failing_status() -> dict[str, object]:
        return {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "001-risk",
                "auto_resume": True,
            },
            "quest_id": "001-risk",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "blocked",
            "reason": "resume_request_failed",
            "launch_report_path": str(launch_report_path),
            "runtime_liveness_audit": {
                "status": "none",
                "active_run_id": "run-stale",
                "runtime_audit": {
                    "status": "none",
                    "active_run_id": "run-stale",
                    "worker_running": False,
                    "worker_pending": False,
                    "stop_requested": False,
                },
            },
        }

    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda *, profile, study_root, source: failing_status(),
    )
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

    first_supervision = first["managed_study_supervision"][0]
    second_supervision = second["managed_study_supervision"][0]
    latest_path = study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"
    latest_payload = json.loads(latest_path.read_text(encoding="utf-8"))
    escalation_path = quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"

    assert first_supervision["health_status"] == "degraded"
    assert first_supervision["consecutive_failure_count"] == 1
    assert second_supervision["health_status"] == "escalated"
    assert second_supervision["consecutive_failure_count"] == 2
    assert second_supervision["needs_human_intervention"] is True
    assert latest_payload["health_status"] == "escalated"
    assert latest_payload["next_action_summary"]
    assert escalation_path.exists()
    escalation_payload = json.loads(escalation_path.read_text(encoding="utf-8"))

    assert escalation_payload["reason"] == "resume_request_failed"
    assert "runtime_event_ref" not in latest_payload
    assert not (quest_root / "artifacts" / "reports" / "runtime_events" / "latest.json").exists()


def test_watch_runtime_writes_supervision_changed_event_when_degraded_runtime_recovers_to_live(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    profiles = importlib.import_module("med_autoscience.profiles")
    workspace_root = tmp_path / "workspace"
    profile = profiles.WorkspaceProfile(
        name="diabetes",
        workspace_root=workspace_root,
        runtime_root=workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests",
        studies_root=workspace_root / "studies",
        portfolio_root=workspace_root / "portfolio",
        med_deepscientist_runtime_root=workspace_root / "ops" / "med-deepscientist" / "runtime",
        med_deepscientist_repo_root=tmp_path / "med-deepscientist",
        default_publication_profile="general_medical_journal",
        default_citation_style="AMA",
        enable_medical_overlay=True,
        medical_overlay_scope="workspace",
        medical_overlay_skills=("intake-audit", "baseline"),
        research_route_bias_policy="high_plasticity_medical",
        preferred_study_archetypes=("clinical_classifier",),
        default_submission_targets=(),
    )
    study_root = profile.studies_root / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")
    quest_root = profile.runtime_root / "001-risk"
    launch_report_path = study_root / "artifacts" / "runtime" / "last_launch_report.json"
    dump_json(
        launch_report_path,
        {
            "recorded_at": "2026-04-10T09:05:00+00:00",
            "source": "runtime_watch",
            "decision": "blocked",
            "reason": "resume_request_failed",
        },
    )

    states = [
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "001-risk",
                "auto_resume": True,
            },
            "quest_id": "001-risk",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "blocked",
            "reason": "resume_request_failed",
            "launch_report_path": str(launch_report_path),
            "runtime_liveness_audit": {
                "status": "none",
                "active_run_id": "run-stale",
                "runtime_audit": {
                    "status": "none",
                    "active_run_id": "run-stale",
                    "worker_running": False,
                    "worker_pending": False,
                    "stop_requested": False,
                },
            },
        },
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "001-risk",
                "auto_resume": True,
            },
            "quest_id": "001-risk",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "noop",
            "reason": "quest_already_running",
            "launch_report_path": str(launch_report_path),
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-live",
                "runtime_audit": {
                    "status": "live",
                    "active_run_id": "run-live",
                    "worker_running": True,
                    "worker_pending": False,
                    "stop_requested": False,
                },
            },
        },
    ]
    call_index = {"value": 0}

    def next_status(*, profile, study_root, source):
        index = min(call_index["value"], len(states) - 1)
        call_index["value"] += 1
        return states[index]

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", next_status)
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

    first_supervision = first["managed_study_supervision"][0]
    second_supervision = second["managed_study_supervision"][0]
    latest_payload = json.loads(
        (study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json").read_text(encoding="utf-8")
    )

    assert first_supervision["health_status"] == "degraded"
    assert second_supervision["health_status"] == "live"
    assert second_supervision["last_transition"] == "recovered"
    assert "runtime_event_ref" not in latest_payload
    assert not (quest_root / "artifacts" / "reports" / "runtime_events" / "latest.json").exists()


def test_watch_runtime_refreshes_recovery_requested_status_to_live_within_same_tick(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    profiles = importlib.import_module("med_autoscience.profiles")
    workspace_root = tmp_path / "workspace"
    profile = profiles.WorkspaceProfile(
        name="diabetes",
        workspace_root=workspace_root,
        runtime_root=workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests",
        studies_root=workspace_root / "studies",
        portfolio_root=workspace_root / "portfolio",
        med_deepscientist_runtime_root=workspace_root / "ops" / "med-deepscientist" / "runtime",
        med_deepscientist_repo_root=tmp_path / "med-deepscientist",
        default_publication_profile="general_medical_journal",
        default_citation_style="AMA",
        enable_medical_overlay=True,
        medical_overlay_scope="workspace",
        medical_overlay_skills=("intake-audit", "baseline"),
        research_route_bias_policy="high_plasticity_medical",
        preferred_study_archetypes=("clinical_classifier",),
        default_submission_targets=(),
    )
    study_root = profile.studies_root / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")
    quest_root = profile.runtime_root / "001-risk"
    dump_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "quest_id": "001-risk",
            "status": "running",
            "active_run_id": "run-live",
        },
    )

    calls: list[tuple[str, str]] = []
    recovery_requested = {
        "schema_version": 1,
        "study_id": "001-risk",
        "study_root": str(study_root),
        "entry_mode": "full_research",
        "execution": {
            "engine": "med-deepscientist",
            "auto_entry": "on_managed_research_intent",
            "quest_id": "001-risk",
            "auto_resume": True,
        },
        "quest_id": "001-risk",
        "quest_root": str(quest_root),
        "quest_exists": True,
        "quest_status": "running",
        "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
        "runtime_binding_exists": True,
        "study_completion_contract": {},
        "decision": "resume",
        "reason": "quest_marked_running_but_no_live_session",
        "runtime_liveness_audit": {
            "status": "none",
            "active_run_id": None,
            "runtime_audit": {
                "status": "none",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
    }
    live_status = {
        **recovery_requested,
        "decision": "noop",
        "reason": "quest_already_running",
        "runtime_liveness_audit": {
            "status": "live",
            "active_run_id": "run-live",
            "runtime_audit": {
                "status": "live",
                "active_run_id": "run-live",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
        "autonomous_runtime_notice": {
            "active_run_id": "run-live",
            "browser_url": "http://127.0.0.1:21003",
            "quest_session_api_url": "http://127.0.0.1:21003/api/quests/001-risk/session",
        },
        "execution_owner_guard": {
            "active_run_id": "run-live",
        },
    }

    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda *, profile, study_root, source: calls.append(("ensure", source)) or recovery_requested,
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda *, profile, study_root: calls.append(("status", Path(study_root).name)) or live_status,
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [quest_root])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    supervision = result["managed_study_supervision"][0]
    latest_payload = json.loads(
        (study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json").read_text(encoding="utf-8")
    )

    assert calls == [
        ("ensure", "runtime_watch"),
        ("status", "001-risk"),
    ]
    assert result["managed_study_actions"] == [
        {
            "study_id": "001-risk",
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
        }
    ]
    assert supervision["health_status"] == "live"
    assert supervision["runtime_decision"] == "noop"
    assert supervision["active_run_id"] == "run-live"
    assert latest_payload["health_status"] == "live"
    assert latest_payload["runtime_decision"] == "noop"
    assert latest_payload["active_run_id"] == "run-live"


def test_watch_runtime_relays_recovery_alerts_to_bound_conversations_without_path_leaks(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = profile.studies_root / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")
    quest_root = profile.runtime_root / "001-risk"
    states = [
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "hermes",
                "runtime_backend_id": "hermes",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "001-risk",
                "auto_resume": True,
            },
            "quest_id": "001-risk",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
            "runtime_liveness_audit": {
                "status": "none",
                "active_run_id": None,
                "runtime_audit": {
                    "status": "none",
                    "active_run_id": None,
                    "worker_running": False,
                    "worker_pending": False,
                    "stop_requested": False,
                },
            },
        },
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "hermes",
                "runtime_backend_id": "hermes",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "001-risk",
                "auto_resume": True,
            },
            "quest_id": "001-risk",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
            "runtime_liveness_audit": {
                "status": "none",
                "active_run_id": None,
                "runtime_audit": {
                    "status": "none",
                    "active_run_id": None,
                    "worker_running": False,
                    "worker_pending": False,
                    "stop_requested": False,
                },
            },
        },
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "hermes",
                "runtime_backend_id": "hermes",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "001-risk",
                "auto_resume": True,
            },
            "quest_id": "001-risk",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "noop",
            "reason": "quest_already_running",
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-live",
                "runtime_audit": {
                    "status": "live",
                    "active_run_id": "run-live",
                    "worker_running": True,
                    "worker_pending": False,
                    "stop_requested": False,
                },
            },
            "autonomous_runtime_notice": {
                "active_run_id": "run-live",
            },
            "execution_owner_guard": {
                "active_run_id": "run-live",
            },
        },
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "hermes",
                "runtime_backend_id": "hermes",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "001-risk",
                "auto_resume": True,
            },
            "quest_id": "001-risk",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
            "runtime_liveness_audit": {
                "status": "none",
                "active_run_id": None,
                "runtime_audit": {
                    "status": "none",
                    "active_run_id": None,
                    "worker_running": False,
                    "worker_pending": False,
                    "stop_requested": False,
                },
            },
        },
    ]
    state_index = {"value": 0}
    interaction_calls: list[dict[str, object]] = []

    class FakeBackend:
        def artifact_interact(self, *, runtime_root: Path, quest_id: str, payload: dict[str, object]) -> dict[str, object]:
            interaction_calls.append(
                {
                    "runtime_root": str(runtime_root),
                    "quest_id": quest_id,
                    "payload": dict(payload),
                }
            )
            return {
                "status": "ok",
                "interaction_id": f"interaction-{len(interaction_calls)}",
            }

    def next_status(*, profile, study_root, source):
        index = min(state_index["value"], len(states) - 1)
        state_index["value"] += 1
        return states[index]

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", next_status)
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda *, profile, study_root: states[min(max(state_index["value"] - 1, 0), len(states) - 1)],
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    monkeypatch.setattr(
        module.runtime_backend_contract,
        "resolve_managed_runtime_backend",
        lambda execution: FakeBackend(),
    )

    module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )
    module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )
    module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )
    module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    latest_alert_path = study_root / "artifacts" / "runtime" / "runtime_alert_delivery" / "latest.json"
    latest_alert = json.loads(latest_alert_path.read_text(encoding="utf-8"))

    assert len(interaction_calls) == 3
    assert interaction_calls[0]["quest_id"] == "001-risk"
    assert interaction_calls[0]["payload"]["kind"] == "progress"
    assert interaction_calls[0]["payload"]["deliver_to_bound_conversations"] is True
    assert interaction_calls[0]["payload"]["reply_mode"] == "threaded"
    assert "自动恢复中" in str(interaction_calls[0]["payload"]["message"])
    assert str(study_root) not in str(interaction_calls[0]["payload"]["message"])
    assert str(profile.runtime_root) not in str(interaction_calls[0]["payload"]["message"])
    assert interaction_calls[1]["payload"]["kind"] == "milestone"
    assert "已恢复在线" in str(interaction_calls[1]["payload"]["message"])
    assert interaction_calls[2]["payload"]["kind"] == "progress"
    assert latest_alert["delivery_status"] == "delivered"
    assert latest_alert["health_status"] == "recovering"


def test_watch_runtime_relays_manual_intervention_alert_once_per_escalated_state(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = profile.studies_root / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")
    quest_root = profile.runtime_root / "001-risk"
    interaction_calls: list[dict[str, object]] = []

    failing_status = {
        "schema_version": 1,
        "study_id": "001-risk",
        "study_root": str(study_root),
        "entry_mode": "full_research",
        "execution": {
            "engine": "hermes",
            "runtime_backend_id": "hermes",
            "auto_entry": "on_managed_research_intent",
            "quest_id": "001-risk",
            "auto_resume": True,
        },
        "quest_id": "001-risk",
        "quest_root": str(quest_root),
        "quest_exists": True,
        "quest_status": "running",
        "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
        "runtime_binding_exists": True,
        "study_completion_contract": {},
        "decision": "blocked",
        "reason": "resume_request_failed",
        "runtime_liveness_audit": {
            "status": "none",
            "active_run_id": None,
            "runtime_audit": {
                "status": "none",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
    }

    class FakeBackend:
        def artifact_interact(self, *, runtime_root: Path, quest_id: str, payload: dict[str, object]) -> dict[str, object]:
            interaction_calls.append(dict(payload))
            return {"status": "ok", "interaction_id": f"interaction-{len(interaction_calls)}"}

    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda *, profile, study_root, source: failing_status,
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    monkeypatch.setattr(
        module.runtime_backend_contract,
        "resolve_managed_runtime_backend",
        lambda execution: FakeBackend(),
    )

    module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )
    module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )
    module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    latest_alert = json.loads(
        (study_root / "artifacts" / "runtime" / "runtime_alert_delivery" / "latest.json").read_text(encoding="utf-8")
    )

    assert len(interaction_calls) == 2
    assert interaction_calls[0]["kind"] == "progress"
    assert interaction_calls[1]["kind"] == "milestone"
    assert "人工介入" in str(interaction_calls[1]["message"])
    assert latest_alert["delivery_status"] == "delivered"
    assert latest_alert["health_status"] == "escalated"
    assert latest_alert["needs_human_intervention"] is True


def test_watch_runtime_retries_alert_delivery_after_previous_failure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = profile.studies_root / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")
    quest_root = profile.runtime_root / "001-risk"
    attempts = {"value": 0}

    recovering_status = {
        "schema_version": 1,
        "study_id": "001-risk",
        "study_root": str(study_root),
        "entry_mode": "full_research",
        "execution": {
            "engine": "hermes",
            "runtime_backend_id": "hermes",
            "auto_entry": "on_managed_research_intent",
            "quest_id": "001-risk",
            "auto_resume": True,
        },
        "quest_id": "001-risk",
        "quest_root": str(quest_root),
        "quest_exists": True,
        "quest_status": "running",
        "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
        "runtime_binding_exists": True,
        "study_completion_contract": {},
        "decision": "resume",
        "reason": "quest_marked_running_but_no_live_session",
        "runtime_liveness_audit": {
            "status": "none",
            "active_run_id": None,
            "runtime_audit": {
                "status": "none",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
    }

    class FlakyBackend:
        def artifact_interact(self, *, runtime_root: Path, quest_id: str, payload: dict[str, object]) -> dict[str, object]:
            attempts["value"] += 1
            if attempts["value"] == 1:
                raise RuntimeError("relay transport temporarily unavailable")
            return {"status": "ok", "interaction_id": "interaction-2"}

    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda *, profile, study_root, source: recovering_status,
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda *, profile, study_root: recovering_status,
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    monkeypatch.setattr(
        module.runtime_backend_contract,
        "resolve_managed_runtime_backend",
        lambda execution: FlakyBackend(),
    )

    module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )
    failed_alert = json.loads(
        (study_root / "artifacts" / "runtime" / "runtime_alert_delivery" / "latest.json").read_text(encoding="utf-8")
    )

    module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )
    delivered_alert = json.loads(
        (study_root / "artifacts" / "runtime" / "runtime_alert_delivery" / "latest.json").read_text(encoding="utf-8")
    )

    assert attempts["value"] == 2
    assert failed_alert["delivery_status"] == "failed"
    assert "temporarily unavailable" in failed_alert["error"]
    assert delivered_alert["delivery_status"] == "delivered"
    assert delivered_alert["health_status"] == "recovering"


def test_watch_runtime_routes_alert_delivery_through_controlled_research_backend(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = profile.studies_root / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")
    quest_root = profile.runtime_root / "001-risk"
    calls: list[dict[str, object]] = []

    recovering_status = {
        "schema_version": 1,
        "study_id": "001-risk",
        "study_root": str(study_root),
        "entry_mode": "full_research",
        "execution": {
            "engine": "hermes",
            "runtime_backend_id": "hermes",
            "auto_entry": "on_managed_research_intent",
            "quest_id": "001-risk",
            "auto_resume": True,
        },
        "quest_id": "001-risk",
        "quest_root": str(quest_root),
        "quest_exists": True,
        "quest_status": "running",
        "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
        "runtime_binding_exists": True,
        "study_completion_contract": {},
        "decision": "resume",
        "reason": "quest_marked_running_but_no_live_session",
        "runtime_liveness_audit": {
            "status": "none",
            "active_run_id": None,
            "runtime_audit": {
                "status": "none",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
    }

    class OuterBackend:
        BACKEND_ID = "hermes"

    class ControlledBackend:
        BACKEND_ID = "med_deepscientist"

        def artifact_interact(self, *, runtime_root: Path, quest_id: str, payload: dict[str, object]) -> dict[str, object]:
            calls.append(
                {
                    "runtime_root": str(runtime_root),
                    "quest_id": quest_id,
                    "payload": dict(payload),
                }
            )
            return {"status": "ok", "interaction_id": "interaction-controlled"}

    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda *, profile, study_root, source: recovering_status,
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda *, profile, study_root: recovering_status,
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    monkeypatch.setattr(
        module.runtime_backend_contract,
        "resolve_managed_runtime_backend",
        lambda execution: OuterBackend(),
    )
    monkeypatch.setattr(
        module.runtime_backend_contract,
        "controlled_research_backend_metadata_for_backend_id",
        lambda backend_id: ("med_deepscientist", "med-deepscientist"),
    )
    monkeypatch.setattr(
        module.runtime_backend_contract,
        "get_managed_runtime_backend",
        lambda backend_id: ControlledBackend(),
    )

    module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    latest_alert = json.loads(
        (study_root / "artifacts" / "runtime" / "runtime_alert_delivery" / "latest.json").read_text(encoding="utf-8")
    )

    assert len(calls) == 1
    assert calls[0]["quest_id"] == "001-risk"
    assert calls[0]["runtime_root"] == str(profile.med_deepscientist_runtime_root)
    assert latest_alert["delivery_status"] == "delivered"


def test_watch_runtime_sends_recovery_resolution_after_previous_manual_intervention_alert(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = profile.studies_root / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")
    quest_root = profile.runtime_root / "001-risk"
    interactions: list[dict[str, object]] = []

    previous_alert_path = study_root / "artifacts" / "runtime" / "runtime_alert_delivery" / "latest.json"
    dump_json(
        previous_alert_path,
        {
            "schema_version": 1,
            "delivered_at": "2026-04-18T00:50:00+00:00",
            "study_id": "001-risk",
            "quest_id": "001-risk",
            "health_status": "escalated",
            "notification_state": "manual_intervention_required",
            "delivery_status": "delivered",
            "alert_fingerprint": "prior-alert",
        },
    )

    live_status = {
        "schema_version": 1,
        "study_id": "001-risk",
        "study_root": str(study_root),
        "entry_mode": "full_research",
        "execution": {
            "engine": "hermes",
            "runtime_backend_id": "hermes",
            "auto_entry": "on_managed_research_intent",
            "quest_id": "001-risk",
            "auto_resume": True,
        },
        "quest_id": "001-risk",
        "quest_root": str(quest_root),
        "quest_exists": True,
        "quest_status": "running",
        "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
        "runtime_binding_exists": True,
        "study_completion_contract": {},
        "decision": "noop",
        "reason": "quest_already_running",
        "runtime_liveness_audit": {
            "status": "live",
            "active_run_id": "run-live",
            "runtime_audit": {
                "status": "live",
                "active_run_id": "run-live",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
        "autonomous_runtime_notice": {
            "active_run_id": "run-live",
        },
        "execution_owner_guard": {
            "active_run_id": "run-live",
        },
    }

    class FakeBackend:
        BACKEND_ID = "med_deepscientist"

        def artifact_interact(self, *, runtime_root: Path, quest_id: str, payload: dict[str, object]) -> dict[str, object]:
            interactions.append(
                {
                    "runtime_root": str(runtime_root),
                    "quest_id": quest_id,
                    "payload": dict(payload),
                }
            )
            return {"status": "ok", "interaction_id": "interaction-recovered"}

    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda *, profile, study_root, source: live_status,
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda *, profile, study_root: live_status,
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    monkeypatch.setattr(
        module.runtime_backend_contract,
        "resolve_managed_runtime_backend",
        lambda execution: FakeBackend(),
    )
    monkeypatch.setattr(
        module.runtime_backend_contract,
        "controlled_research_backend_metadata_for_backend_id",
        lambda backend_id: ("med_deepscientist", "med-deepscientist"),
    )
    monkeypatch.setattr(
        module.runtime_backend_contract,
        "get_managed_runtime_backend",
        lambda backend_id: FakeBackend(),
    )

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    latest_alert = json.loads(previous_alert_path.read_text(encoding="utf-8"))

    assert result["managed_study_supervision"][0]["health_status"] == "live"
    assert result["managed_study_supervision"][0]["last_transition"] == "live_confirmed"
    assert len(interactions) == 1
    assert interactions[0]["payload"]["kind"] == "milestone"
    assert "已恢复在线" in str(interactions[0]["payload"]["message"])
    assert latest_alert["notification_state"] == "recovered"
    assert latest_alert["delivery_status"] == "delivered"


def test_suppresses_duplicate_data_asset_gate_blocker(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        return {
            "status": "blocked",
            "blockers": ["outdated_private_release"],
            "study_id": quest_root.name,
            "report_json": str(quest_root / "artifacts" / "reports" / "data_asset_gate" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "data_asset_gate" / "latest.md"),
            "intervention_enqueued": apply,
        }

    first = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"data_asset_gate": fake_runner},
        apply=True,
    )
    second = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"data_asset_gate": fake_runner},
        apply=True,
    )

    assert first["controllers"]["data_asset_gate"]["action"] == "applied"
    assert second["controllers"]["data_asset_gate"]["action"] == "suppressed"
    assert calls == [False, True, False]


def test_applies_data_asset_gate_advisory_once(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        return {
            "status": "advisory",
            "blockers": [],
            "advisories": ["public_data_extension_available"],
            "study_id": quest_root.name,
            "public_support_dataset_ids": ["geo-gse000001"],
            "report_json": str(quest_root / "artifacts" / "reports" / "data_asset_gate" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "data_asset_gate" / "latest.md"),
            "intervention_enqueued": apply,
        }

    first = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"data_asset_gate": fake_runner},
        apply=True,
    )
    second = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"data_asset_gate": fake_runner},
        apply=True,
    )

    assert first["controllers"]["data_asset_gate"]["status"] == "advisory"
    assert first["controllers"]["data_asset_gate"]["action"] == "applied"
    assert second["controllers"]["data_asset_gate"]["action"] == "suppressed"
    assert calls == [False, True, False]


def test_reapplies_data_asset_gate_when_unresolved_dataset_ids_change(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []
    state = {"unresolved_dataset_ids": ["ds_a"]}

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        return {
            "status": "blocked",
            "blockers": ["unresolved_private_data_contract"],
            "advisories": [],
            "study_id": quest_root.name,
            "outdated_dataset_ids": [],
            "unresolved_dataset_ids": list(state["unresolved_dataset_ids"]),
            "public_support_dataset_ids": [],
            "report_json": str(quest_root / "artifacts" / "reports" / "data_asset_gate" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "data_asset_gate" / "latest.md"),
            "intervention_enqueued": apply,
        }

    first = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"data_asset_gate": fake_runner},
        apply=True,
    )
    state["unresolved_dataset_ids"] = ["ds_b"]
    second = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"data_asset_gate": fake_runner},
        apply=True,
    )

    assert first["controllers"]["data_asset_gate"]["action"] == "applied"
    assert second["controllers"]["data_asset_gate"]["action"] == "applied"
    assert calls == [False, True, False, True]


def test_watch_loop_runs_runtime_ticks_on_interval(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    runtime_root = tmp_path / "runtime" / "quests"
    runtime_root.mkdir(parents=True)
    seen: list[tuple[str, object]] = []

    def fake_run_watch_for_runtime(
        *,
        runtime_root: Path,
        controller_runners=None,
        apply: bool,
        profile=None,
        ensure_study_runtimes: bool = False,
    ) -> dict[str, object]:
        seen.append(("tick", runtime_root, apply, ensure_study_runtimes))
        return {
            "runtime_root": str(runtime_root),
            "scanned_quests": [],
        }

    monkeypatch.setattr(module, "run_watch_for_runtime", fake_run_watch_for_runtime)

    def fake_sleep(seconds: float) -> None:
        seen.append(("sleep", seconds))

    result = module.run_watch_loop(
        runtime_root=runtime_root,
        apply=True,
        ensure_study_runtimes=True,
        interval_seconds=12,
        max_ticks=2,
        sleep_fn=fake_sleep,
    )

    assert result["tick_count"] == 2
    assert result["interval_seconds"] == 12
    assert result["last_result"] == {
        "runtime_root": str(runtime_root),
        "scanned_quests": [],
    }
    assert seen == [
        ("tick", runtime_root, True, True),
        ("sleep", 12),
        ("tick", runtime_root, True, True),
    ]


def test_watch_loop_continues_after_single_tick_failure(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    runtime_root = tmp_path / "runtime" / "quests"
    runtime_root.mkdir(parents=True)
    seen: list[tuple[str, object]] = []
    attempts = {"count": 0}

    def fake_run_watch_for_runtime(
        *,
        runtime_root: Path,
        controller_runners=None,
        apply: bool,
        profile=None,
        ensure_study_runtimes: bool = False,
    ) -> dict[str, object]:
        attempts["count"] += 1
        seen.append(("tick", attempts["count"]))
        if attempts["count"] == 1:
            raise RuntimeError("transient daemon read failed")
        return {
            "runtime_root": str(runtime_root),
            "scanned_quests": ["q001"],
        }

    monkeypatch.setattr(module, "run_watch_for_runtime", fake_run_watch_for_runtime)

    def fake_sleep(seconds: float) -> None:
        seen.append(("sleep", seconds))

    result = module.run_watch_loop(
        runtime_root=runtime_root,
        apply=True,
        ensure_study_runtimes=True,
        interval_seconds=12,
        max_ticks=2,
        sleep_fn=fake_sleep,
    )

    assert result["tick_count"] == 2
    assert result["last_result"] == {
        "runtime_root": str(runtime_root),
        "scanned_quests": ["q001"],
    }
    assert result["tick_errors"] == [
        {
            "tick": 1,
            "error_type": "RuntimeError",
            "error": "transient daemon read failed",
        }
    ]
    assert seen == [
        ("tick", 1),
        ("sleep", 12),
        ("tick", 2),
    ]


def test_run_managed_supervisor_tick_uses_profile_runtime_root_and_always_enables_study_runtime_ensure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    profiles = importlib.import_module("med_autoscience.profiles")
    profile = profiles.WorkspaceProfile(
        name="glioma",
        workspace_root=tmp_path / "workspace",
        runtime_root=tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests",
        studies_root=tmp_path / "workspace" / "studies",
        portfolio_root=tmp_path / "workspace" / "portfolio",
        med_deepscientist_runtime_root=tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime",
        med_deepscientist_repo_root=tmp_path / "med-deepscientist",
        default_publication_profile="general_medical_journal",
        default_citation_style="AMA",
        enable_medical_overlay=True,
        medical_overlay_scope="workspace",
        medical_overlay_skills=("intake-audit", "baseline"),
        research_route_bias_policy="high_plasticity_medical",
        preferred_study_archetypes=("clinical_classifier",),
        default_submission_targets=(),
    )
    called: dict[str, object] = {}

    def fake_run_watch_for_runtime(
        *,
        runtime_root: Path,
        controller_runners=None,
        apply: bool,
        profile,
        ensure_study_runtimes: bool = False,
    ) -> dict[str, object]:
        called["runtime_root"] = runtime_root
        called["apply"] = apply
        called["profile"] = profile
        called["ensure_study_runtimes"] = ensure_study_runtimes
        return {"mode": "managed_supervisor_tick"}

    monkeypatch.setattr(module, "run_watch_for_runtime", fake_run_watch_for_runtime)

    result = module.run_managed_supervisor_tick(profile=profile, apply=True)

    assert result == {"mode": "managed_supervisor_tick"}
    assert called == {
        "runtime_root": profile.runtime_root,
        "apply": True,
        "profile": profile,
        "ensure_study_runtimes": True,
    }


def test_run_managed_supervisor_loop_uses_profile_runtime_root_and_always_enables_study_runtime_ensure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    profiles = importlib.import_module("med_autoscience.profiles")
    profile = profiles.WorkspaceProfile(
        name="glioma",
        workspace_root=tmp_path / "workspace",
        runtime_root=tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests",
        studies_root=tmp_path / "workspace" / "studies",
        portfolio_root=tmp_path / "workspace" / "portfolio",
        med_deepscientist_runtime_root=tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime",
        med_deepscientist_repo_root=tmp_path / "med-deepscientist",
        default_publication_profile="general_medical_journal",
        default_citation_style="AMA",
        enable_medical_overlay=True,
        medical_overlay_scope="workspace",
        medical_overlay_skills=("intake-audit", "baseline"),
        research_route_bias_policy="high_plasticity_medical",
        preferred_study_archetypes=("clinical_classifier",),
        default_submission_targets=(),
    )
    called: dict[str, object] = {}

    def fake_run_watch_loop(
        *,
        runtime_root: Path,
        apply: bool,
        profile,
        ensure_study_runtimes: bool = False,
        interval_seconds: int,
        max_ticks: int | None,
        sleep_fn,
    ) -> dict[str, object]:
        called["runtime_root"] = runtime_root
        called["apply"] = apply
        called["profile"] = profile
        called["ensure_study_runtimes"] = ensure_study_runtimes
        called["interval_seconds"] = interval_seconds
        called["max_ticks"] = max_ticks
        called["sleep_fn"] = sleep_fn
        return {"mode": "managed_supervisor_loop"}

    monkeypatch.setattr(module, "run_watch_loop", fake_run_watch_loop)

    result = module.run_managed_supervisor_loop(
        profile=profile,
        apply=True,
        interval_seconds=45,
        max_ticks=3,
        sleep_fn=lambda _: None,
    )

    assert result == {"mode": "managed_supervisor_loop"}
    assert called["runtime_root"] == profile.runtime_root
    assert called["apply"] is True
    assert called["profile"] == profile
    assert called["ensure_study_runtimes"] is True
    assert called["interval_seconds"] == 45
    assert called["max_ticks"] == 3
