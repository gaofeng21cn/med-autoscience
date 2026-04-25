from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace


def _base_status_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "study_id": "001-risk",
        "study_root": "/tmp/workspace/studies/001-risk",
        "entry_mode": "full_research",
        "execution": {
            "engine": "med-deepscientist",
            "auto_entry": "on_managed_research_intent",
            "quest_id": "quest-001",
            "auto_resume": True,
        },
        "quest_id": "quest-001",
        "quest_root": "/tmp/runtime/quests/quest-001",
        "quest_exists": True,
        "quest_status": "running",
        "runtime_binding_path": "/tmp/workspace/studies/001-risk/runtime_binding.yaml",
        "runtime_binding_exists": True,
        "study_completion_contract": {},
        "decision": "noop",
        "reason": "quest_already_running",
    }


def _patch_router(monkeypatch, module) -> None:
    managed_runtime_backend = SimpleNamespace(resolve_daemon_url=lambda *, runtime_root: "http://127.0.0.1:21999")
    monkeypatch.setattr(
        module,
        "_router_module",
        lambda: SimpleNamespace(
            managed_runtime_backend=managed_runtime_backend,
            managed_runtime_transport=managed_runtime_backend,
            med_deepscientist_transport=managed_runtime_backend,
            _managed_runtime_backend_for_execution=lambda execution: managed_runtime_backend,
        ),
    )


def _write_controller_decision_authorization(study_root: Path) -> Path:
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    decision_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "decision_id": "decision-analysis-001",
                "study_id": "001-risk",
                "quest_id": "quest-001",
                "emitted_at": "2026-04-25T06:20:00+00:00",
                "decision_type": "bounded_analysis",
                "charter_ref": {
                    "charter_id": "charter::001-risk::v1",
                    "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                },
                "runtime_escalation_ref": {
                    "record_id": "runtime-escalation::001-risk::quest-001::controller-gap",
                    "artifact_path": str(study_root / "artifacts" / "runtime" / "runtime_escalation_record.json"),
                    "summary_ref": str(study_root / "artifacts" / "runtime" / "runtime_escalation_record.json"),
                },
                "publication_eval_ref": {
                    "eval_id": "publication-eval::001-risk::quest-001::latest",
                    "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
                },
                "requires_human_confirmation": False,
                "controller_actions": [
                    {
                        "action_type": "ensure_study_runtime",
                        "payload_ref": str(decision_path),
                    }
                ],
                "reason": "Route bounded revision analysis back into the active runtime.",
                "route_target": "analysis-campaign",
                "route_key_question": (
                    "revision checklist mapping each user comment to manuscript/table/figure/reference changes"
                ),
                "route_rationale": "The revision line needs a bounded quality pass under the same manuscript route.",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return decision_path


def _write_runtime_state(quest_root: Path, payload: dict[str, object]) -> None:
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    runtime_state_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_state_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_runtime_execution_router_patch_exposes_generic_managed_runtime_transport_alias(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    _patch_router(monkeypatch, module)

    router = module._router_module()

    assert router.managed_runtime_transport is router.med_deepscientist_transport


def test_autonomous_runtime_notice_reports_live_runtime_only_when_liveness_is_strictly_live(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")
    _patch_router(monkeypatch, module)
    status = typed_surface.StudyRuntimeStatus.from_payload(_base_status_payload())
    status.record_runtime_liveness_audit(
        {
            "status": "live",
            "active_run_id": "run-live",
            "runtime_audit": {
                "status": "live",
                "active_run_id": "run-live",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
        }
    )

    module._record_autonomous_runtime_notice_if_required(
        status=status,
        runtime_root=Path("/tmp/runtime"),
        launch_report_path=Path("/tmp/workspace/studies/001-risk/artifacts/runtime/last_launch_report.json"),
    )

    assert status.to_dict()["autonomous_runtime_notice"]["notification_reason"] == (
        "detected_existing_live_managed_runtime"
    )


def test_autonomous_runtime_notice_marks_unhealthy_runtime_without_claiming_live(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")
    _patch_router(monkeypatch, module)
    status = typed_surface.StudyRuntimeStatus.from_payload(_base_status_payload())
    status.record_runtime_liveness_audit(
        {
            "status": "unknown",
            "active_run_id": "run-stale",
            "runtime_audit": {
                "status": "live",
                "active_run_id": "run-stale",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
                "stale_progress": True,
            },
            "stale_progress": True,
            "liveness_guard_reason": "stale_progress_watchdog",
        }
    )

    module._record_autonomous_runtime_notice_if_required(
        status=status,
        runtime_root=Path("/tmp/runtime"),
        launch_report_path=Path("/tmp/workspace/studies/001-risk/artifacts/runtime/last_launch_report.json"),
    )

    notice = status.to_dict()["autonomous_runtime_notice"]
    assert notice["required"] is True
    assert notice["active_run_id"] == "run-stale"
    assert notice["notification_reason"] == "managed_runtime_degraded"


def test_autonomous_runtime_notice_does_not_claim_live_without_active_run_id(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")
    _patch_router(monkeypatch, module)
    status = typed_surface.StudyRuntimeStatus.from_payload(_base_status_payload())
    status.record_runtime_liveness_audit(
        {
            "status": "none",
            "active_run_id": None,
            "runtime_audit": {
                "status": "none",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
        }
    )

    module._record_autonomous_runtime_notice_if_required(
        status=status,
        runtime_root=Path("/tmp/runtime"),
        launch_report_path=Path("/tmp/workspace/studies/001-risk/artifacts/runtime/last_launch_report.json"),
    )

    assert "autonomous_runtime_notice" not in status.to_dict()


def test_controller_owned_interaction_reply_message_prompts_write_stage_resume(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")
    _patch_router(monkeypatch, module)
    payload = _base_status_payload()
    payload["reason"] = "quest_stale_decision_after_write_stage_ready"
    status = typed_surface.StudyRuntimeStatus.from_payload(payload)

    message = module._controller_owned_interaction_reply_message(status=status)

    assert message is not None
    assert "publication gate 已放行写作" in message
    assert "继续 write stage" in message


def test_controller_owned_interaction_reply_message_appends_route_context(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")
    _patch_router(monkeypatch, module)
    payload = _base_status_payload()
    payload["reason"] = "quest_stale_decision_after_write_stage_ready"
    status = typed_surface.StudyRuntimeStatus.from_payload(payload)

    message = module._controller_owned_interaction_reply_message(
        status=status,
        route_context={
            "route_target": "write",
            "route_target_label": "当前论文主线写作",
            "route_key_question": "What is the narrowest same-line manuscript repair or continuation step required now?",
            "route_rationale": "The publication gate is clear and the current paper line can continue through same-line manuscript work.",
        },
    )

    assert message is not None
    assert "当前正式 route 是“当前论文主线写作”" in message
    assert "当前关键问题是" in message
    assert "这样推进的理由是" in message


def test_execute_noop_runtime_decision_relays_controller_authorization_to_live_runtime(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "runtime" / "quest-001"
    decision_path = _write_controller_decision_authorization(study_root)
    _write_runtime_state(
        quest_root,
        {
            "status": "running",
            "active_run_id": "run-live-001",
            "pending_user_message_count": 0,
        },
    )
    status_payload = _base_status_payload()
    status_payload["study_root"] = str(study_root)
    status_payload["quest_root"] = str(quest_root)
    status = module.StudyRuntimeStatus.from_payload(status_payload)
    chats: list[dict[str, object]] = []

    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            chats.append(
                {
                    "runtime_root": runtime_root,
                    "quest_id": quest_id,
                    "text": text,
                    "source": source,
                }
            )
            return {"ok": True, "message": {"id": "msg-auth-001"}}

    context = SimpleNamespace(
        study_root=study_root,
        quest_root=quest_root,
        runtime_root=tmp_path / "runtime",
        runtime_backend=FakeBackend(),
        source="medautosci-test",
    )

    outcome = module._execute_runtime_decision(status=status, context=context)

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.NOOP
    assert len(chats) == 1
    assert chats[0]["quest_id"] == "quest-001"
    assert chats[0]["source"] == "medautosci-test"
    assert str(decision_path) in str(chats[0]["text"])
    assert "publication_eval/latest.json" in str(chats[0]["text"])
    assert "requires_controller_decision=true" in str(chats[0]["text"])
    assert "revision checklist mapping each user comment" in str(chats[0]["text"])
    relay = status.to_dict()["controller_decision_authorization_relay"]
    assert relay["delivery_mode"] == "managed_runtime_chat"
    assert relay["message_id"] == "msg-auth-001"
    runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    assert runtime_state["last_controller_decision_authorization"] == {
        "decision_id": "decision-analysis-001",
        "route_target": "analysis-campaign",
        "route_key_question": (
            "revision checklist mapping each user comment to manuscript/table/figure/reference changes"
        ),
        "active_run_id": "run-live-001",
        "delivery_mode": "managed_runtime_chat",
        "message_id": "msg-auth-001",
        "source": "medautosci-test",
    }


def test_execute_noop_runtime_decision_deduplicates_controller_authorization_for_same_run(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "runtime" / "quest-001"
    _write_controller_decision_authorization(study_root)
    _write_runtime_state(
        quest_root,
        {
            "status": "running",
            "active_run_id": "run-live-001",
            "pending_user_message_count": 0,
            "last_controller_decision_authorization": {
                "decision_id": "decision-analysis-001",
                "route_target": "analysis-campaign",
                "route_key_question": (
                    "revision checklist mapping each user comment to manuscript/table/figure/reference changes"
                ),
                "active_run_id": "run-live-001",
                "delivery_mode": "managed_runtime_chat",
                "message_id": "msg-auth-001",
                "source": "medautosci-test",
            },
        },
    )
    status_payload = _base_status_payload()
    status_payload["study_root"] = str(study_root)
    status_payload["quest_root"] = str(quest_root)
    status = module.StudyRuntimeStatus.from_payload(status_payload)

    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            raise AssertionError("controller authorization should be deduplicated for the same active run")

    context = SimpleNamespace(
        study_root=study_root,
        quest_root=quest_root,
        runtime_root=tmp_path / "runtime",
        runtime_backend=FakeBackend(),
        source="medautosci-test",
    )

    outcome = module._execute_runtime_decision(status=status, context=context)

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.NOOP
    assert "controller_decision_authorization_relay" not in status.to_dict()


def test_force_restart_for_live_controller_reroute_supports_write_stage_ready(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")
    _patch_router(monkeypatch, module)
    quest_root = tmp_path / "runtime" / "quest-001"
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    runtime_state_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_state_path.write_text(
        json.dumps(
            {
                "status": "running",
                "active_run_id": "run-live-001",
                "continuation_anchor": "decision",
                "continuation_reason": "decision:decision-live-001",
                "same_fingerprint_auto_turn_count": 3,
                "pending_user_message_count": 0,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    payload = _base_status_payload()
    payload["reason"] = "quest_stale_decision_after_write_stage_ready"
    payload["quest_root"] = str(quest_root)
    status = typed_surface.StudyRuntimeStatus.from_payload(payload)
    status.record_runtime_liveness_audit(
        {
            "status": "live",
            "active_run_id": "run-live-001",
            "runtime_audit": {
                "status": "live",
                "active_run_id": "run-live-001",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
        }
    )
    status.record_publication_supervisor_state(
        {
            "status": "clear",
            "supervisor_phase": "write_stage_ready",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "current_required_action": "continue_write_stage",
            "bundle_tasks_downstream_only": False,
            "deferred_downstream_actions": [],
            "controller_stage_note": "write stage is clear",
        }
    )

    assert module._should_skip_redundant_resume_for_live_controller_reroute(status=status) is True
    assert (
        module._should_force_restart_for_live_controller_reroute(
            status=status,
            context=SimpleNamespace(quest_root=quest_root),
        )
        is True
    )


def test_force_restart_for_live_controller_reroute_supports_write_drift_even_when_runtime_state_stays_write(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")
    _patch_router(monkeypatch, module)
    quest_root = tmp_path / "runtime" / "quest-001"
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    runtime_state_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_state_path.write_text(
        json.dumps(
            {
                "status": "running",
                "active_run_id": "run-live-001",
                "continuation_anchor": "write",
                "continuation_reason": "write:finish_proofing_and_submission_checks",
                "same_fingerprint_auto_turn_count": 3,
                "pending_user_message_count": 0,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    payload = _base_status_payload()
    payload["reason"] = "quest_drifting_into_write_without_gate_approval"
    payload["quest_root"] = str(quest_root)
    status = typed_surface.StudyRuntimeStatus.from_payload(payload)
    status.record_runtime_liveness_audit(
        {
            "status": "live",
            "active_run_id": "run-live-001",
            "runtime_audit": {
                "status": "live",
                "active_run_id": "run-live-001",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
        }
    )
    status.record_publication_supervisor_state(
        {
            "status": "blocked",
            "supervisor_phase": "return_to_publishability_gate",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "current_required_action": "return_to_publishability_gate",
            "bundle_tasks_downstream_only": True,
            "deferred_downstream_actions": [],
            "controller_stage_note": "write stage must yield back to the publication gate",
        }
    )

    assert module._should_skip_redundant_resume_for_live_controller_reroute(status=status) is True
    assert (
        module._should_force_restart_for_live_controller_reroute(
            status=status,
            context=SimpleNamespace(quest_root=quest_root),
        )
        is True
    )


def test_runtime_event_status_snapshot_includes_continuation_anchor(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")
    _patch_router(monkeypatch, module)
    status = typed_surface.StudyRuntimeStatus.from_payload(_base_status_payload())
    status.record_continuation_state(
        {
            "quest_status": "running",
            "active_run_id": "run-live-001",
            "continuation_policy": "auto",
            "continuation_anchor": "decision",
            "continuation_reason": "decision:decision-live-001",
            "runtime_state_path": "/tmp/runtime/quests/quest-001/.ds/runtime_state.json",
        }
    )

    snapshot = module._runtime_event_status_snapshot(status)

    assert snapshot["continuation_anchor"] == "decision"
    assert snapshot["continuation_reason"] == "decision:decision-live-001"
