from __future__ import annotations

from .shared import *  # noqa: F403

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import _clear_readiness_report, make_profile, write_study, write_text


def _managed_runtime_transport(module: object):
    return module.managed_runtime_transport


def _patch_ready_workspace(monkeypatch, module: object, *, study_id: str) -> None:
    monkeypatch.setattr(
        module.analysis_bundle_controller,
        "ensure_study_runtime_analysis_bundle",
        lambda: {"action": "already_ready", "ready": True},
    )
    monkeypatch.setattr(
        module.overlay_installer,
        "ensure_medical_overlay",
        lambda **kwargs: {"selected_action": "noop", "post_status": {"all_targets_ready": True}},
    )
    monkeypatch.setattr(
        module.overlay_installer,
        "materialize_runtime_medical_overlay",
        lambda **kwargs: {"materialized_surface_count": 1, "surfaces": []},
    )
    monkeypatch.setattr(
        module.overlay_installer,
        "audit_runtime_medical_overlay",
        lambda **kwargs: {"all_roots_ready": True, "surface_count": 1, "surfaces": []},
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


def _patch_no_live_worker(monkeypatch, module: object) -> None:
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "none",
            "source": "combined_runner_or_bash_session",
            "active_run_id": None,
            "runner_live": False,
            "bash_live": False,
            "runtime_audit": {
                "ok": True,
                "status": "none",
                "source": "quest_session_runtime_audit",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {
                "ok": True,
                "status": "none",
                "session_count": 0,
                "live_session_count": 0,
                "live_session_ids": [],
            },
        },
    )


def _write_managed_study(profile, study_id: str) -> tuple[Path, Path]:
    study_root = write_study(
        profile.workspace_root,
        study_id,
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation"],
    )
    quest_root = profile.runtime_root / study_id
    write_text(quest_root / "quest.yaml", f"quest_id: {study_id}\n")
    return study_root, quest_root


def test_user_paused_quest_blocks_auto_resume_even_when_auto_resume_is_enabled(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    _, quest_root = _write_managed_study(profile, study_id)
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "paused",
                "active_run_id": None,
                "worker_running": False,
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "controller_work_unit_pending",
                "stop_reason": "user_pause",
            }
        )
        + "\n",
    )
    _patch_ready_workspace(monkeypatch, module, study_id=study_id)
    monkeypatch.setattr(
        module,
        "_resume_quest",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("user pause must not be auto-resumed")),
    )

    result = module.ensure_study_runtime(profile=profile, study_id=study_id, source="runtime_watch")

    assert result["quest_status"] == "paused"
    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_user_paused_requires_explicit_wakeup"
    assert result["auto_runtime_parked"]["parked"] is True
    assert result["auto_runtime_parked"]["parked_state"] == "explicit_resume_pending"
    assert result["auto_runtime_parked"]["awaiting_explicit_wakeup"] is True
    assert result["runtime_health_snapshot"]["canonical_runtime_action"] == "await_explicit_resume"


def test_user_paused_quest_resumes_after_explicit_user_wakeup(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    _, quest_root = _write_managed_study(profile, study_id)
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    write_text(
        runtime_state_path,
        json.dumps(
            {
                "status": "paused",
                "active_run_id": None,
                "worker_running": False,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "user_pause",
                "continuation_reason": "user_pause",
                "stop_reason": "user_pause",
                "user_pause_contract": {
                    "recorded_at": "2026-05-06T05:08:51+00:00",
                    "resume_requires_explicit_wakeup": True,
                    "source": "test-human-takeover",
                },
            }
        )
        + "\n",
    )
    _patch_ready_workspace(monkeypatch, module, study_id=study_id)
    calls: list[str] = []
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "update_quest_startup_context",
        lambda *, runtime_root, quest_id, startup_contract, requested_baseline_ref=None: calls.append("sync_context")
        or {"ok": True, "snapshot": {"quest_id": quest_id, "startup_contract": startup_contract}},
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "_resume_quest",
        lambda *, runtime_root, quest_id, source, runtime_backend: calls.append("resume")
        or {"ok": True, "status": "running", "snapshot": {"status": "running", "active_run_id": "run-explicit"}},
    )

    result = module.ensure_study_runtime(
        profile=profile,
        study_id=study_id,
        explicit_user_wakeup=True,
        source="user_explicit_wakeup",
    )

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_paused"
    assert result["quest_status"] == "running"
    assert calls == ["sync_context", "resume"]
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))
    assert runtime_state["last_explicit_user_wakeup"]["source"] == "user_explicit_wakeup"
    assert runtime_state["last_explicit_user_wakeup"]["cleared_stop_reason"] == "user_pause"
    assert "user_pause_contract" not in runtime_state


def test_waiting_controller_owner_closeout_resumes_after_explicit_user_wakeup(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    _, quest_root = _write_managed_study(profile, study_id)
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    write_text(
        runtime_state_path,
        json.dumps(
            {
                "status": "waiting_for_user",
                "active_run_id": None,
                "worker_running": False,
                "pending_user_message_count": 2,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "turn_closeout",
                "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
                "blocked_turn_closeout": {
                    "run_id": "run-blocked",
                    "blocked_reason": "control_plane_route_blocked_bundle_build",
                    "next_owner": "MAS/controller",
                    "closeout_path": str(quest_root / "artifacts" / "runtime" / "turn_closeouts" / "run-blocked.json"),
                },
                "last_controller_decision_authorization": {
                    "decision_id": "decision-current-paper-work",
                    "work_unit_id": "analysis_claim_evidence_repair",
                    "work_unit_fingerprint": "publication-blockers::current",
                },
            }
        )
        + "\n",
    )
    write_text(
        quest_root / ".ds" / "user_message_queue.json",
        json.dumps(
            {
                "pending": [
                    {"message_id": "msg-gate", "source": "codex-publication-gate", "content": "gate stop"},
                    {"message_id": "msg-surface", "source": "codex-medical-publication-surface", "content": "surface stop"},
                ],
                "completed": [],
            }
        )
        + "\n",
    )
    _patch_ready_workspace(monkeypatch, module, study_id=study_id)
    calls: list[str] = []
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "update_quest_startup_context",
        lambda *, runtime_root, quest_id, startup_contract, requested_baseline_ref=None: calls.append("sync_context")
        or {"ok": True, "snapshot": {"quest_id": quest_id, "startup_contract": startup_contract}},
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "_resume_quest",
        lambda *, runtime_root, quest_id, source, runtime_backend: calls.append("resume")
        or {"ok": True, "status": "running", "snapshot": {"status": "running", "active_run_id": "run-explicit"}},
    )

    result = module.ensure_study_runtime(
        profile=profile,
        study_id=study_id,
        explicit_user_wakeup=True,
        source="user_explicit_wakeup",
    )

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_waiting_opl_runtime_owner_route"
    assert result["quest_status"] == "waiting_for_user"
    assert result["explicit_user_wakeup"]["status"] == "recorded"
    assert result["interaction_arbitration"]["classification"] == "opl_runtime_owner_route_handoff"
    assert result["opl_runtime_owner_route_handoff"]["queue_owner"] == "one-person-lab"
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))
    assert runtime_state["last_explicit_user_wakeup"]["source"] == "user_explicit_wakeup"
    assert runtime_state["pending_user_message_count"] == 2
    assert runtime_state["last_explicit_user_wakeup"]["handoff_kind"] == "opl_runtime_owner_route"
    assert runtime_state["last_opl_runtime_owner_route_handoff"]["queue_owner"] == "one-person-lab"
    assert runtime_state["continuation_policy"] == "wait_for_opl_runtime_owner"
    assert runtime_state["continuation_anchor"] == "opl_runtime_owner_route"
    assert runtime_state["continuation_reason"] == "quest_waiting_opl_runtime_owner_route"
    assert "blocked_turn_closeout" not in runtime_state


def test_waiting_pending_user_message_redrive_resumes_without_explicit_wakeup(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    _, quest_root = _write_managed_study(profile, study_id)
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    write_text(
        runtime_state_path,
        json.dumps(
            {
                "status": "waiting_for_user",
                "active_run_id": None,
                "worker_running": False,
                "pending_user_message_count": 2,
                "continuation_policy": "auto",
                "continuation_anchor": "user_message_queue",
                "continuation_reason": "runtime_platform_repair_resume_existing_pending_user_message",
            }
        )
        + "\n",
    )
    _patch_ready_workspace(monkeypatch, module, study_id=study_id)
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "get_quest_session",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "quest_id": quest_id,
            "snapshot": {"status": "waiting_for_user", "pending_user_message_count": 2},
            "runtime_audit": {
                "ok": True,
                "status": "none",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_resume_quest",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("pending user-message redrive belongs to OPL runtime owner")
        ),
    )

    result = module.ensure_study_runtime(profile=profile, study_id=study_id, source="runtime_platform_repair")

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_waiting_opl_runtime_owner_route"
    assert result["quest_status"] == "waiting_for_user"
    assert result["interaction_arbitration"]["classification"] == "pending_user_message_redrive"
    assert result["interaction_arbitration"]["action"] == "resume"


def test_waiting_platform_repair_decision_redrive_resumes_without_pending_messages(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    _, quest_root = _write_managed_study(profile, study_id)
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "waiting_for_user",
                "active_run_id": None,
                "worker_running": False,
                "pending_user_message_count": 0,
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "runtime_platform_repair_redrive",
            }
        )
        + "\n",
    )
    _patch_ready_workspace(monkeypatch, module, study_id=study_id)
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "get_quest_session",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "quest_id": quest_id,
            "snapshot": {"status": "waiting_for_user", "pending_user_message_count": 0},
            "runtime_audit": {
                "ok": True,
                "status": "none",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_resume_quest",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("platform decision redrive belongs to OPL runtime owner")
        ),
    )

    result = module.ensure_study_runtime(profile=profile, study_id=study_id, source="runtime_platform_repair")

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_waiting_opl_runtime_owner_route"
    assert result["quest_status"] == "waiting_for_user"
    assert result["interaction_arbitration"]["classification"] == "platform_repair_decision_redrive"
    assert result["interaction_arbitration"]["action"] == "resume"


def test_waiting_controller_work_unit_pending_resumes_with_current_authorization(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    _, quest_root = _write_managed_study(profile, study_id)
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "waiting_for_user",
                "active_run_id": None,
                "worker_running": False,
                "pending_user_message_count": 0,
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "controller_work_unit_pending",
                "last_controller_decision_authorization": {
                    "decision_id": "decision-current-paper-work",
                    "work_unit_id": "analysis_claim_evidence_repair",
                    "work_unit_fingerprint": "publication-blockers::current",
                },
            }
        )
        + "\n",
    )
    _patch_ready_workspace(monkeypatch, module, study_id=study_id)
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "get_quest_session",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "quest_id": quest_id,
            "snapshot": {"status": "waiting_for_user", "pending_user_message_count": 0},
            "runtime_audit": {
                "ok": True,
                "status": "none",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_resume_quest",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("controller work-unit pending redrive belongs to OPL runtime owner")
        ),
    )

    result = module.ensure_study_runtime(profile=profile, study_id=study_id, source="runtime_platform_repair")

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_waiting_opl_runtime_owner_route"
    assert result["quest_status"] == "waiting_for_user"
    assert result["interaction_arbitration"]["classification"] == "controller_work_unit_pending_redrive"
    assert result["interaction_arbitration"]["action"] == "resume"


def test_waiting_controller_work_unit_pending_without_authorization_stays_blocked(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    _, quest_root = _write_managed_study(profile, study_id)
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "waiting_for_user",
                "active_run_id": None,
                "worker_running": False,
                "pending_user_message_count": 0,
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "controller_work_unit_pending",
            }
        )
        + "\n",
    )
    _patch_ready_workspace(monkeypatch, module, study_id=study_id)
    monkeypatch.setattr(
        module,
        "_resume_quest",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("missing controller authorization must not resume")),
    )

    result = module.ensure_study_runtime(profile=profile, study_id=study_id, source="runtime_platform_repair")

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_waiting_for_user"
    assert result["interaction_arbitration"]["classification"] == "unclassified_waiting_state"
    assert result["interaction_arbitration"]["action"] == "block"


def test_legacy_human_takeover_escalation_not_treated_as_user_pause(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    protocol = importlib.import_module("med_autoscience.runtime_protocol")
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    _, quest_root = _write_managed_study(profile, study_id)
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    write_text(
        runtime_state_path,
        json.dumps(
            {
                "status": "paused",
                "active_run_id": None,
                "worker_running": False,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "user_pause",
                "continuation_reason": "user_pause",
                "stop_reason": "user_pause",
                "updated_at": "2026-05-09T01:02:36+00:00",
                "user_pause_contract": {
                    "recorded_at": "2026-05-09T01:02:36+00:00",
                    "resume_requires_explicit_wakeup": True,
                    "source": "cli",
                },
            }
        )
        + "\n",
    )
    protocol.write_runtime_escalation_record(
        quest_root=quest_root,
        record=protocol.RuntimeEscalationRecord(
            schema_version=1,
            record_id="runtime-escalation::001-risk::001-risk::human_takeover_requested::2026-05-09T01:02:36+00:00",
            study_id=study_id,
            quest_id=study_id,
            emitted_at="2026-05-09T01:02:36+00:00",
            trigger=protocol.RuntimeEscalationTrigger(
                trigger_id="human_takeover_requested",
                source="runtime_supervision",
            ),
            scope="quest",
            severity="quest",
            reason="human_takeover_requested",
            recommended_actions=("manual_runtime_review_required", "controller_review_required"),
            evidence_refs=(str(tmp_path / "runtime_supervision.json"),),
            runtime_context_refs={"runtime_supervision_path": str(tmp_path / "runtime_supervision.json")},
            summary_ref=str(tmp_path / "last_launch_report.json"),
        ),
    )
    _patch_ready_workspace(monkeypatch, module, study_id=study_id)
    calls: list[str] = []
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "update_quest_startup_context",
        lambda *, runtime_root, quest_id, startup_contract, requested_baseline_ref=None: calls.append("sync_context")
        or {"ok": True, "snapshot": {"quest_id": quest_id, "startup_contract": startup_contract}},
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "_resume_quest",
        lambda *, runtime_root, quest_id, source, runtime_backend: calls.append("resume")
        or {"ok": True, "status": "running", "snapshot": {"status": "running", "active_run_id": "run-after-takeover"}},
    )

    result = module.ensure_study_runtime(profile=profile, study_id=study_id, source="runtime_watch")
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_paused"
    assert calls == ["sync_context", "resume"]
    assert "stop_reason" not in runtime_state
    assert "user_pause_contract" not in runtime_state
    assert runtime_state["human_takeover_contract"]["source"] == "legacy_human_takeover_escalation_repair"


def test_relay_repeats_when_existing_authorization_marker_lacks_target_context(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    controller_authorization = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    study_root, quest_root = _write_managed_study(profile, study_id)
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    write_text(
        runtime_state_path,
        json.dumps(
                {
                    "status": "paused",
                    "active_run_id": None,
                    "worker_running": False,
                    "continuation_policy": "auto",
                    "continuation_anchor": "decision",
                    "continuation_reason": "controller_work_unit_pending",
                    "last_controller_decision_authorization": {
                        "decision_id": "decision-1",
                        "route_target": "analysis-campaign",
                    "route_key_question": "analysis_claim_evidence_repair: Repair blockers.",
                    "control_intent_key": "control-intent::same",
                },
            }
        )
        + "\n",
    )
    authorization_context = {
        "decision_id": "decision-1",
        "study_id": study_id,
        "quest_id": study_id,
        "requires_human_confirmation": False,
        "controller_actions": ("run_quality_repair_batch",),
        "route_target": "analysis-campaign",
        "route_key_question": "analysis_claim_evidence_repair: Repair blockers.",
        "route_rationale": "Repair blockers.",
        "work_unit_id": "analysis_claim_evidence_repair",
        "work_unit_fingerprint": "publication-blockers::1",
        "blocker_authority_fingerprint": "publication-blockers::1",
        "next_work_unit": {
            "unit_id": "analysis_claim_evidence_repair",
            "lane": "analysis-campaign",
            "summary": "Repair blockers.",
        },
        "blocking_work_units": [],
        "specificity_targets": [
            {
                "target_kind": "claim",
                "target_id": "claim_evidence_map",
                "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
                "blocking_reason": "claim_evidence_consistency_failed",
            }
        ],
        "decision_path": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
        "control_intent_key": "control-intent::same",
        "control_intent_identity": {
            "business_key": "control-intent::same",
            "dedupe_key": "control-intent::same",
        },
    }
    monkeypatch.setattr(
        controller_authorization,
        "_load_controller_decision_authorization_context",
        lambda *, study_root: authorization_context,
    )
    monkeypatch.setattr(
        controller_authorization.control_intent,
        "lifecycle_state",
        lambda **kwargs: {
            "lifecycle_state": "delivered",
            "latest_event_type": "delivered",
            "delivery_blocked": True,
            "block_reason": "same_fingerprint_no_artifact_delta",
        },
    )
    monkeypatch.setattr(controller_authorization.control_intent, "append_event", lambda **kwargs: None)
    _patch_ready_workspace(monkeypatch, module, study_id=study_id)
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "chat_quest",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("controller authorization target context must be handed off as owner_route_ref")
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "_resume_quest",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("controller authorization handoff must not call resume_quest")
        ),
    )

    result = module.ensure_study_runtime(profile=profile, study_id=study_id, source="runtime_watch")

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_waiting_opl_runtime_owner_route"
    owner_route_ref = result["controller_decision_authorization_owner_route_ref"]
    assert owner_route_ref["queue_owner"] == "one-person-lab"
    assert owner_route_ref["specificity_targets"] == authorization_context["specificity_targets"]
    assert owner_route_ref["authority_boundary"]["mas_submits_runtime_chat"] is False


def test_user_paused_stopped_quest_surfaces_explicit_wakeup_not_generic_rerun(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    _, quest_root = _write_managed_study(profile, study_id)
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "stopped",
                "active_run_id": None,
                "worker_running": False,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "user_pause",
                "continuation_reason": "user_pause",
                "stop_reason": "user_pause",
                "user_pause_contract": {
                    "recorded_at": "2026-05-06T05:08:51+00:00",
                    "resume_requires_explicit_wakeup": True,
                    "source": "test-human-takeover",
                },
            }
        )
        + "\n",
    )
    _patch_ready_workspace(monkeypatch, module, study_id=study_id)
    monkeypatch.setattr(
        module,
        "_resume_quest",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("stopped user pause must not be auto-resumed")),
    )

    result = module.ensure_study_runtime(profile=profile, study_id=study_id, source="runtime_watch")

    assert result["quest_status"] == "stopped"
    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_user_paused_requires_explicit_wakeup"
    assert result["auto_runtime_parked"]["parked_state"] == "explicit_resume_pending"
    assert result["auto_runtime_parked"]["awaiting_explicit_wakeup"] is True
    assert result["runtime_health_snapshot"]["canonical_runtime_action"] == "await_explicit_resume"


def test_user_paused_active_no_worker_drift_blocks_watch_runtime_recovery(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    _, quest_root = _write_managed_study(profile, study_id)
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "active",
                "active_run_id": None,
                "worker_running": False,
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "controller_work_unit_pending",
                "stop_reason": "user_pause",
            }
        )
        + "\n",
    )
    _patch_ready_workspace(monkeypatch, module, study_id=study_id)
    _patch_no_live_worker(monkeypatch, module)
    monkeypatch.setattr(
        module,
        "_resume_quest",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("user pause drift must not be auto-resumed")),
    )

    result = module.ensure_study_runtime(profile=profile, study_id=study_id, source="runtime_watch")

    assert result["quest_status"] == "active"
    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_user_paused_requires_explicit_wakeup"
    assert result["runtime_health_snapshot"]["attempt_state"] == "awaiting_explicit_resume"
    assert result["runtime_health_snapshot"]["canonical_runtime_action"] == "await_explicit_resume"


def test_pause_study_runtime_records_human_takeover_without_user_pause_contract(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    transport = _managed_runtime_transport(module)
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    study_root, quest_root = _write_managed_study(profile, study_id)
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    write_text(
        runtime_state_path,
        json.dumps(
            {
                "status": "running",
                "active_run_id": "run-user-paused",
                "worker_running": True,
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "controller_work_unit_pending",
            }
        )
        + "\n",
    )
    _patch_ready_workspace(monkeypatch, module, study_id=study_id)

    def pause_quest(*, runtime_root, quest_id, source):
        write_text(
            runtime_state_path,
            json.dumps(
                {
                    "status": "paused",
                    "active_run_id": None,
                    "worker_running": False,
                    "continuation_policy": "auto",
                    "continuation_anchor": "decision",
                    "continuation_reason": "controller_work_unit_pending",
                }
            )
            + "\n",
        )
        return {
            "ok": True,
            "status": "paused",
            "snapshot": {"status": "paused", "active_run_id": None, "worker_running": False},
        }

    monkeypatch.setattr(transport, "pause_quest", pause_quest)

    result = module.pause_study_runtime(
        profile=profile,
        study_root=study_root,
        source="test-human-takeover",
    )
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))

    assert result["decision"] == "pause"
    assert result["reason"] == "human_takeover_requested"
    assert "stop_reason" not in runtime_state
    assert runtime_state["continuation_policy"] == "controller_review"
    assert runtime_state["continuation_anchor"] == "human_takeover"
    assert runtime_state["continuation_reason"] == "human_takeover_requested"
    assert "user_pause_contract" not in runtime_state
    assert runtime_state["human_takeover_contract"]["source"] == "test-human-takeover"
    assert runtime_state["human_takeover_contract"]["resume_requires_explicit_wakeup"] is True
    assert result["human_takeover_contract"]["status"] == "recorded"


def test_pause_study_runtime_records_human_takeover_contract_when_daemon_is_down_but_quest_is_already_paused(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    transport = _managed_runtime_transport(module)
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    study_root, quest_root = _write_managed_study(profile, study_id)
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    write_text(
        runtime_state_path,
        json.dumps(
            {
                "status": "paused",
                "active_run_id": None,
                "worker_running": False,
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "controller_work_unit_pending",
            }
        )
        + "\n",
    )
    _patch_ready_workspace(monkeypatch, module, study_id=study_id)
    monkeypatch.setattr(
        transport,
        "pause_quest",
        lambda *, runtime_root, quest_id, source: (_ for _ in ()).throw(RuntimeError("connection refused")),
    )

    result = module.pause_study_runtime(
        profile=profile,
        study_root=study_root,
        source="test-human-takeover",
    )
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))

    assert result["decision"] == "pause"
    assert result["reason"] == "human_takeover_requested"
    assert result["quest_status"] == "paused"
    assert result["pause_postcondition"]["effective"] is True
    assert "stop_reason" not in runtime_state
    assert runtime_state["continuation_policy"] == "controller_review"
    assert runtime_state["continuation_anchor"] == "human_takeover"
    assert runtime_state["continuation_reason"] == "human_takeover_requested"
    assert runtime_state["human_takeover_contract"]["source"] == "test-human-takeover"
    assert result["human_takeover_contract"]["status"] == "recorded"


def test_pause_study_runtime_records_human_takeover_contract_when_daemon_is_down_but_quest_is_already_stopped(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    transport = _managed_runtime_transport(module)
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    study_root, quest_root = _write_managed_study(profile, study_id)
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    write_text(
        runtime_state_path,
        json.dumps(
            {
                "status": "stopped",
                "active_run_id": None,
                "worker_running": False,
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "controller_work_unit_pending",
                "stop_reason": "controller_stop:signal:sigterm",
            }
        )
        + "\n",
    )
    _patch_ready_workspace(monkeypatch, module, study_id=study_id)
    monkeypatch.setattr(
        transport,
        "pause_quest",
        lambda *, runtime_root, quest_id, source: (_ for _ in ()).throw(RuntimeError("connection refused")),
    )

    result = module.pause_study_runtime(
        profile=profile,
        study_root=study_root,
        source="test-human-takeover",
    )
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))

    assert result["decision"] == "pause"
    assert result["reason"] == "human_takeover_requested"
    assert result["quest_status"] == "stopped"
    assert result["pause_postcondition"]["effective"] is True
    assert "stop_reason" not in runtime_state
    assert runtime_state["continuation_policy"] == "controller_review"
    assert runtime_state["continuation_anchor"] == "human_takeover"
    assert runtime_state["continuation_reason"] == "human_takeover_requested"
    assert runtime_state["human_takeover_contract"]["source"] == "test-human-takeover"
    assert result["human_takeover_contract"]["status"] == "recorded"
