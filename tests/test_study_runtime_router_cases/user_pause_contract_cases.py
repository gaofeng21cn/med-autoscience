from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import _clear_readiness_report, make_profile, write_study, write_text


def _managed_runtime_transport(module: object):
    transport = module.managed_runtime_transport
    assert transport is module.med_deepscientist_transport
    return transport


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


def test_pause_study_runtime_replaces_auto_continuation_with_user_pause_contract(
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
    assert runtime_state["stop_reason"] == "user_pause"
    assert runtime_state["continuation_policy"] == "wait_for_user_or_resume"
    assert runtime_state["continuation_anchor"] == "user_pause"
    assert runtime_state["continuation_reason"] == "user_pause"
    assert runtime_state["user_pause_contract"]["source"] == "test-human-takeover"
    assert result["user_pause_contract"]["status"] == "recorded"
