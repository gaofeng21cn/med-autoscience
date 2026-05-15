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


def test_bare_paused_quest_without_live_worker_requires_explicit_wakeup(
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
                "worker_pending": False,
                "turn_reason": "explicit_resume",
            }
        )
        + "\n",
    )
    _patch_ready_workspace(monkeypatch, module, study_id=study_id)
    monkeypatch.setattr(
        module,
        "_resume_quest",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("bare paused quest must not auto-resume")),
    )

    result = module.ensure_study_runtime(profile=profile, study_id=study_id, source="runtime_status_read")

    assert result["quest_status"] == "paused"
    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_user_paused_requires_explicit_wakeup"
    assert result["auto_runtime_parked"]["parked_state"] == "explicit_resume_pending"
    assert result["auto_runtime_parked"]["awaiting_explicit_wakeup"] is True


def test_bare_paused_quest_resumes_after_explicit_user_wakeup(
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
                "worker_pending": False,
                "turn_reason": "explicit_resume",
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
    assert result["explicit_user_wakeup"]["cleared_bare_paused"] is True
    assert calls == ["sync_context", "resume"]
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))
    assert runtime_state["last_explicit_user_wakeup"]["source"] == "user_explicit_wakeup"
    assert runtime_state["last_explicit_user_wakeup"]["cleared_bare_paused"] is True
