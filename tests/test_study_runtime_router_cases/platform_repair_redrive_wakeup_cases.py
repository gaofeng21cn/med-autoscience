from __future__ import annotations

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


def test_waiting_platform_repair_redrive_resumes_after_explicit_user_wakeup(
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
                "worker_pending": False,
                "pending_turn_reason": "explicit_resume",
                "pending_turn_source": "product_entry",
                "pending_user_message_count": 1,
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "runtime_platform_repair_redrive",
                "last_runner_start_error": "workspace_python_missing_or_not_executable",
            }
        )
        + "\n",
    )
    _patch_ready_workspace(monkeypatch, module, study_id=study_id)
    monkeypatch.setattr(
        module,
        "_resume_quest",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("OPL runtime owner route handoff must not call resume_quest")
        ),
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
    assert result["explicit_user_wakeup"]["cleared_platform_repair_redrive"] is True
    assert result["interaction_arbitration"]["classification"] == "opl_runtime_owner_route_handoff"
    assert result["opl_runtime_owner_route_handoff"]["queue_owner"] == "one-person-lab"
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))
    assert runtime_state["last_explicit_user_wakeup"]["source"] == "user_explicit_wakeup"
    assert runtime_state["last_explicit_user_wakeup"]["cleared_platform_repair_redrive"] is True
    assert runtime_state["last_explicit_user_wakeup"]["handoff_kind"] == "opl_runtime_owner_route"
    assert runtime_state["last_opl_runtime_owner_route_handoff"]["queue_owner"] == "one-person-lab"
    assert runtime_state["pending_user_message_count"] == 1
    assert runtime_state["continuation_policy"] == "wait_for_opl_runtime_owner"
    assert runtime_state["continuation_anchor"] == "opl_runtime_owner_route"
    assert runtime_state["continuation_reason"] == "quest_waiting_opl_runtime_owner_route"
