from __future__ import annotations

from dataclasses import replace
import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from .study_runtime_test_helpers import (
    _clear_readiness_report,
    make_profile,
    make_runtime_overlay_result,
    make_startup_hydration_report,
    make_startup_hydration_validation_report,
    write_study,
    write_submission_metadata_only_bundle,
    write_text,
)


def _write_requested_baseline_ref(study_root: Path, requested_baseline_ref: dict[str, object] | None) -> None:
    study_payload = yaml.safe_load(study_root.joinpath("study.yaml").read_text(encoding="utf-8"))
    if not isinstance(study_payload, dict):
        raise TypeError("study payload must be a mapping")
    execution = study_payload.get("execution")
    if not isinstance(execution, dict):
        raise TypeError("study execution payload must be a mapping")
    execution["requested_baseline_ref"] = requested_baseline_ref
    write_text(
        study_root / "study.yaml",
        yaml.safe_dump(study_payload, allow_unicode=True, sort_keys=False),
    )


@pytest.fixture(autouse=True)
def _patch_runtime_sidecars(monkeypatch):
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
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
        module.med_deepscientist_transport,
        "inspect_quest_live_bash_sessions",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "live",
            "session_count": 1,
            "live_session_count": 1,
            "live_session_ids": ["sess-default"],
        },
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "live",
            "source": "combined_runner_or_bash_session",
            "active_run_id": "run-default",
            "runner_live": True,
            "bash_live": True,
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "daemon_turn_worker",
                "active_run_id": "run-default",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {
                "ok": True,
                "status": "live",
                "session_count": 1,
                "live_session_count": 1,
                "live_session_ids": ["sess-default"],
            },
        },
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "update_quest_startup_context",
        lambda *, runtime_root, quest_id, startup_contract, requested_baseline_ref=None: {
            "ok": True,
            "snapshot": {
                "quest_id": quest_id,
                "startup_contract": startup_contract,
                "requested_baseline_ref": requested_baseline_ref,
            },
        },
    )


def test_ensure_study_runtime_creates_and_starts_new_quest(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    _write_requested_baseline_ref(study_root, {"baseline_id": "demo-baseline"})
    created: dict[str, object] = {}
    resumed: dict[str, object] = {}

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    def fake_create_quest(*, runtime_root: Path, payload: dict[str, object]) -> dict[str, object]:
        created["runtime_root"] = runtime_root
        created["payload"] = payload
        return {
            "ok": True,
            "snapshot": {
                "quest_id": "001-risk",
                "quest_root": str(runtime_root / "001-risk"),
                "status": "created",
            },
            "startup": {"queued": True},
        }

    monkeypatch.setattr(module.med_deepscientist_transport, "create_quest", fake_create_quest)
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: resumed.update(
            {"runtime_root": runtime_root, "quest_id": quest_id, "source": source}
        )
        or {"ok": True, "status": "running"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "create_and_start"
    assert created["runtime_root"] == profile.med_deepscientist_runtime_root
    payload = created["payload"]
    assert payload["quest_id"] == "001-risk"
    assert payload["auto_start"] is False
    assert payload["title"] == "Diabetes mortality risk paper"
    assert "requested_baseline_ref" not in payload
    assert payload["startup_contract"]["custom_profile"] == "freeform"
    assert payload["startup_contract"]["scope"] == "full_research"
    assert payload["startup_contract"]["baseline_mode"] == "reuse_existing_only"
    assert payload["startup_contract"]["baseline_execution_policy"] == "reuse_existing_only"
    assert "resolve-journal-shortlist" in payload["startup_contract"]["controller_first_policy_summary"]
    assert payload["startup_contract"]["submission_targets"] == []
    assert payload["startup_contract"]["journal_shortlist"]["status"] == "resolved"
    assert "resolve-submission-targets" in payload["startup_contract"]["controller_first_policy_summary"]
    assert "apply-data-asset-update" in payload["startup_contract"]["controller_first_policy_summary"]
    assert "continue until durable outputs requiring human selection are produced" in payload["startup_contract"]["automation_ready_summary"]
    assert result["startup_boundary_gate"]["allow_compute_stage"] is True
    assert result["startup_boundary_gate"]["required_first_anchor"] == "scout"
    assert result["startup_hydration"]["status"] == "hydrated"
    assert result["startup_hydration_validation"]["status"] == "clear"
    assert resumed == {
        "runtime_root": profile.med_deepscientist_runtime_root,
        "quest_id": "001-risk",
        "source": "medautosci-test",
    }
    assert Path(result["startup_payload_path"]).is_file()
    assert Path(result["runtime_binding_path"]).is_file()
    assert Path(result["launch_report_path"]).is_file()
    binding = yaml.safe_load(Path(result["runtime_binding_path"]).read_text(encoding="utf-8"))
    assert binding["last_action"] == "create_and_start"
    assert binding["quest_id"] == "001-risk"
    report = json.loads(Path(result["launch_report_path"]).read_text(encoding="utf-8"))
    assert report["decision"] == "create_and_start"
    assert report["study_id"] == "001-risk"
    assert report["study_root"] == str(study_root)


def test_ensure_study_runtime_uses_protocol_runtime_root_for_transport_calls(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    seen: dict[str, object] = {}
    protocol_runtime_root = tmp_path / "protocol-runtime"
    protocol_quest_root = protocol_runtime_root / "quests" / "001-risk"

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module.study_runtime_protocol,
        "resolve_study_runtime_context",
        lambda *, profile, study_root, study_id, quest_id: SimpleNamespace(
            runtime_root=protocol_runtime_root,
            quest_root=protocol_quest_root,
            runtime_binding_path=study_root / "runtime_binding.yaml",
            startup_payload_root=tmp_path / "protocol-startup-payloads" / study_id,
            launch_report_path=study_root / "artifacts" / "runtime" / "last_launch_report.json",
        ),
    )
    monkeypatch.setattr(
        module.quest_state,
        "inspect_quest_runtime",
        lambda quest_root: module.quest_state.QuestRuntimeSnapshot(
            quest_exists=False,
            quest_status=None,
            bash_session_audit=None,
        ),
    )

    def fake_create_quest(*, runtime_root: Path, payload: dict[str, object]) -> dict[str, object]:
        seen["create_runtime_root"] = runtime_root
        return {
            "ok": True,
            "snapshot": {
                "quest_id": "001-risk",
                "quest_root": str(runtime_root / "quests" / "001-risk"),
                "status": "created",
            },
        }

    def fake_resume_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, object]:
        seen["resume_runtime_root"] = runtime_root
        return {"ok": True, "status": "running"}

    monkeypatch.setattr(module.med_deepscientist_transport, "create_quest", fake_create_quest)
    monkeypatch.setattr(module.med_deepscientist_transport, "resume_quest", fake_resume_quest)

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "create_and_start"
    assert seen["create_runtime_root"] == protocol_runtime_root
    assert seen["resume_runtime_root"] == protocol_runtime_root


def test_ensure_study_runtime_resume_flow_uses_protocol_quest_root_not_status_string(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    protocol_runtime_root = tmp_path / "protocol-runtime"
    protocol_quest_root = protocol_runtime_root / "quests" / "001-risk"
    seen: dict[str, Path] = {}

    monkeypatch.setattr(
        module,
        "_status_state",
        lambda **kwargs: module.StudyRuntimeStatus.from_payload(
            {
                "schema_version": 1,
                "study_id": "001-risk",
                "study_root": str(study_root),
                "entry_mode": "full_research",
                "execution": {"quest_id": "001-risk", "auto_resume": True},
                "quest_id": "001-risk",
                "quest_root": str(tmp_path / "wrong-status-quest-root"),
                "quest_exists": True,
                "quest_status": "paused",
                "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
                "runtime_binding_exists": True,
                "runtime_reentry_gate": {},
                "study_completion_contract": {},
                "decision": "resume",
                "reason": "quest_paused",
            }
        ),
    )
    monkeypatch.setattr(
        module.study_runtime_protocol,
        "resolve_study_runtime_context",
        lambda *, profile, study_root, study_id, quest_id: SimpleNamespace(
            runtime_root=protocol_runtime_root,
            quest_root=protocol_quest_root,
            runtime_binding_path=study_root / "runtime_binding.yaml",
            startup_payload_root=tmp_path / "protocol-startup-payloads" / study_id,
            launch_report_path=study_root / "artifacts" / "runtime" / "last_launch_report.json",
        ),
    )
    monkeypatch.setattr(
        module,
        "_prepare_runtime_overlay",
        lambda *, profile, quest_root: (
            seen.__setitem__("overlay_quest_root", quest_root) or {"audit": {"all_roots_ready": True}}
        ),
    )
    monkeypatch.setattr(
        module,
        "quest_hydration_controller",
        SimpleNamespace(
            run_hydration=lambda *, quest_root, hydration_payload: (
                seen.__setitem__("hydration_quest_root", quest_root) or make_startup_hydration_report(quest_root)
            )
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(run_validation=lambda *, quest_root: make_startup_hydration_validation_report(quest_root)),
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: {"ok": True, "status": "running"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "resume"
    assert seen["overlay_quest_root"] == protocol_quest_root
    assert seen["hydration_quest_root"] == protocol_quest_root

def test_study_runtime_status_blocks_stopped_quest_pending_explicit_rerun(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"stopped"}\n')
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_stopped_requires_explicit_rerun"
    assert result["quest_status"] == "stopped"


def test_ensure_study_runtime_does_not_auto_resume_stopped_quest(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"stopped"}\n')
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module,
        "_resume_quest",
        lambda **kwargs: pytest.fail("_resume_quest should not run for stopped quests under P1 rerun policy"),
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_stopped_requires_explicit_rerun"
    assert result["quest_status"] == "stopped"


def test_execute_runtime_decision_returns_terminal_outcome_for_completed_status(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(profile.workspace_root, "001-risk")

    resolved_study_id, resolved_study_root, study_payload = module._resolve_study(
        profile=profile,
        study_id="001-risk",
        study_root=None,
    )
    status = module._status_state(
        profile=profile,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        study_payload=study_payload,
        entry_mode=None,
    )
    status.set_decision("completed", "quest_already_completed")
    context = module._build_execution_context(
        profile=profile,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        study_payload=study_payload,
        source="test",
    )

    outcome = module._execute_runtime_decision(status=status, context=context)

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.COMPLETED
    assert outcome.daemon_result is None
    assert outcome.startup_payload_path is None


def test_execute_resume_runtime_decision_records_nested_resume_daemon_step(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
        paper_framing_summary="Prediction framing is fixed.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    status = module.StudyRuntimeStatus.from_payload(
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(profile.workspace_root / "studies" / "001-risk"),
            "entry_mode": "full_research",
            "execution": {"quest_id": "001-risk", "auto_resume": True},
            "quest_id": "001-risk",
            "quest_root": str(profile.runtime_root / "001-risk"),
            "quest_exists": True,
            "quest_status": "paused",
            "runtime_binding_path": str(profile.workspace_root / "studies" / "001-risk" / "runtime_binding.yaml"),
            "runtime_binding_exists": False,
            "workspace_contracts": {"overall_ready": True},
            "startup_data_readiness": {"status": "clear"},
            "startup_boundary_gate": {"allow_compute_stage": True},
            "runtime_reentry_gate": {"allow_runtime_entry": True},
            "study_completion_contract": {"status": "absent", "ready": False},
            "controller_first_policy_summary": "summary",
            "automation_ready_summary": "ready",
            "decision": "resume",
            "reason": "quest_paused",
        }
    )
    context = module._build_execution_context(
        profile=profile,
        study_id="001-risk",
        study_root=profile.workspace_root / "studies" / "001-risk",
        study_payload=yaml.safe_load((profile.workspace_root / "studies" / "001-risk" / "study.yaml").read_text(encoding="utf-8")),
        source="test",
    )

    monkeypatch.setattr(
        module,
        "_sync_existing_quest_startup_context",
        lambda **kwargs: {
            "ok": True,
            "snapshot": {
                "quest_id": kwargs["quest_id"],
                "startup_contract": kwargs["create_payload"]["startup_contract"],
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_run_startup_hydration",
        lambda **kwargs: (
            module.study_runtime_protocol.StartupHydrationReport.from_payload(
                make_startup_hydration_report(kwargs["quest_root"])
            ),
            module.study_runtime_protocol.StartupHydrationValidationReport.from_payload(
                make_startup_hydration_validation_report(kwargs["quest_root"])
            ),
        ),
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: {"ok": True, "status": "running"},
    )

    outcome = module._execute_resume_runtime_decision(status=status, context=context)

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.RESUME
    assert outcome.daemon_result == {"resume": {"ok": True, "status": "running"}}
    assert outcome.daemon_step("resume") == {"ok": True, "status": "running"}
    assert status.quest_status is module.StudyRuntimeQuestStatus.RUNNING


def test_execute_pause_runtime_decision_records_nested_pause_daemon_step(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(profile.workspace_root, "001-risk")
    status = module.StudyRuntimeStatus.from_payload(
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(profile.workspace_root / "studies" / "001-risk"),
            "entry_mode": "full_research",
            "execution": {"quest_id": "001-risk", "auto_resume": True},
            "quest_id": "001-risk",
            "quest_root": str(profile.runtime_root / "001-risk"),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(profile.workspace_root / "studies" / "001-risk" / "runtime_binding.yaml"),
            "runtime_binding_exists": False,
            "workspace_contracts": {"overall_ready": True},
            "startup_data_readiness": {"status": "clear"},
            "startup_boundary_gate": {"allow_compute_stage": True},
            "runtime_reentry_gate": {"allow_runtime_entry": True},
            "study_completion_contract": {"status": "absent", "ready": False},
            "controller_first_policy_summary": "summary",
            "automation_ready_summary": "ready",
            "decision": "pause",
            "reason": "runtime_reentry_not_ready_for_running_quest",
        }
    )
    context = module._build_execution_context(
        profile=profile,
        study_id="001-risk",
        study_root=profile.workspace_root / "studies" / "001-risk",
        study_payload=yaml.safe_load((profile.workspace_root / "studies" / "001-risk" / "study.yaml").read_text(encoding="utf-8")),
        source="test",
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "pause_quest",
        lambda *, runtime_root, quest_id, source: {"ok": True, "status": "paused"},
    )

    outcome = module._execute_pause_runtime_decision(status=status, context=context)

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.PAUSE
    assert outcome.daemon_result == {"pause": {"ok": True, "status": "paused"}}
    assert outcome.daemon_step("pause") == {"ok": True, "status": "paused"}
    assert status.quest_status is module.StudyRuntimeQuestStatus.PAUSED

def test_ensure_study_runtime_persists_legacy_resume_daemon_result_shape(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"paused"}\n')
    seen: dict[str, object] = {}

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module,
        "quest_hydration_controller",
        SimpleNamespace(
            run_hydration=lambda **kwargs: make_startup_hydration_report(kwargs["quest_root"])
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(
            run_validation=lambda **kwargs: make_startup_hydration_validation_report(kwargs["quest_root"])
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: {"ok": True, "status": "active"},
    )
    monkeypatch.setattr(
        module.study_runtime_protocol,
        "persist_runtime_artifacts",
        lambda **kwargs: seen.setdefault("persist_calls", []).append(kwargs)
        or module.study_runtime_protocol.StudyRuntimeArtifacts(
            runtime_binding_path=kwargs["runtime_binding_path"],
            launch_report_path=kwargs["launch_report_path"],
            startup_payload_path=kwargs["startup_payload_path"],
        ),
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "resume"
    assert len(seen["persist_calls"]) == 1
    assert seen["persist_calls"][0]["last_action"] == "resume"
    assert seen["persist_calls"][0]["daemon_result"] == {"ok": True, "status": "active"}


def test_execute_runtime_decision_rejects_unknown_decision(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(profile.workspace_root, "001-risk")

    resolved_study_id, resolved_study_root, study_payload = module._resolve_study(
        profile=profile,
        study_id="001-risk",
        study_root=None,
    )
    status = module._status_state(
        profile=profile,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        study_payload=study_payload,
        entry_mode=None,
    )
    status.decision = "unexpected_action"
    status.reason = module.StudyRuntimeReason.QUEST_ALREADY_COMPLETED
    context = module._build_execution_context(
        profile=profile,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        study_payload=study_payload,
        source="test",
    )

    with pytest.raises(ValueError, match="unsupported study runtime decision"):
        module._execute_runtime_decision(status=status, context=context)


def test_ensure_study_runtime_uses_study_runtime_protocol_persistence_helpers(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    seen: dict[str, object] = {}

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "create_quest",
        lambda *, runtime_root, payload: {
            "ok": True,
            "snapshot": {
                "quest_id": "001-risk",
                "quest_root": str(runtime_root / "quests" / "001-risk"),
                "status": "created",
            },
        },
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: {"ok": True, "status": "running"},
    )
    monkeypatch.setattr(
        module.study_runtime_protocol,
        "write_startup_payload",
        lambda *, startup_payload_root, create_payload, slug: seen.setdefault(
            "startup_payload_calls",
            [],
        ).append(
            {
                "startup_payload_root": startup_payload_root,
                "create_payload": create_payload,
                "slug": slug,
            }
        )
        or (tmp_path / "protocol-startup-payload.json"),
    )
    monkeypatch.setattr(
        module.study_runtime_protocol,
        "persist_runtime_artifacts",
        lambda **kwargs: seen.setdefault("persist_calls", []).append(kwargs)
        or module.study_runtime_protocol.StudyRuntimeArtifacts(
            runtime_binding_path=kwargs["runtime_binding_path"],
            launch_report_path=kwargs["launch_report_path"],
            startup_payload_path=kwargs["startup_payload_path"],
        ),
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert isinstance(result, dict)
    assert result["decision"] == "create_and_start"
    assert len(seen["startup_payload_calls"]) == 1
    assert seen["startup_payload_calls"][0]["create_payload"]["quest_id"] == "001-risk"
    assert len(seen["persist_calls"]) == 1
    assert seen["persist_calls"][0]["last_action"] == "create_and_start"
    assert seen["persist_calls"][0]["source"] == "medautosci-test"


def test_run_startup_hydration_returns_typed_protocol_reports(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    create_payload = {"quest_id": "001-risk", "startup_contract": {"schema_version": 4}}

    monkeypatch.setattr(
        module.study_runtime_protocol,
        "build_hydration_payload",
        lambda *, create_payload: {"quest_id": create_payload["quest_id"]},
    )

    monkeypatch.setattr(
        module,
        "quest_hydration_controller",
        SimpleNamespace(
            run_hydration=lambda **kwargs: make_startup_hydration_report(kwargs["quest_root"])
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(
            run_validation=lambda **kwargs: make_startup_hydration_validation_report(kwargs["quest_root"])
        ),
        raising=False,
    )

    hydration_report, validation_report = module._run_startup_hydration(
        quest_root=quest_root,
        create_payload=create_payload,
    )

    assert isinstance(hydration_report, module.study_runtime_protocol.StartupHydrationReport)
    assert isinstance(validation_report, module.study_runtime_protocol.StartupHydrationValidationReport)
    assert hydration_report.status is module.study_runtime_protocol.StartupHydrationStatus.HYDRATED
    assert validation_report.status is module.study_runtime_protocol.StartupHydrationValidationStatus.CLEAR


def test_study_runtime_status_prefers_study_completion_contract_over_boundary_gate(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_status="completed",
        study_completion={
            "status": "completed",
            "summary": "Study-level finalized delivery is complete.",
            "user_approval_text": "同意",
            "evidence_paths": [
                "notes/revision_status.md",
                "manuscript/submission_manifest.json",
            ],
        },
    )
    write_text(study_root / "notes" / "revision_status.md", "# Revision\n")
    write_text(study_root / "manuscript" / "submission_manifest.json", "{}\n")

    monkeypatch.setattr(
        module.quest_state,
        "inspect_quest_runtime",
        lambda quest_root: module.quest_state.QuestRuntimeSnapshot(
            quest_exists=True,
            quest_status="paused",
            bash_session_audit=None,
        ),
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "sync_completion"
    assert result["reason"] == "study_completion_ready"
    assert result["study_completion_contract"]["status"] == "resolved"
    assert result["study_completion_contract"]["ready"] is True


def test_ensure_study_runtime_syncs_study_completion_into_managed_quest(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_status="completed",
        quest_id="001-risk-managed",
        study_completion={
            "status": "completed",
            "summary": "Study-level finalized delivery is complete.",
            "user_approval_text": "同意",
            "evidence_paths": [
                "notes/revision_status.md",
                "manuscript/submission_manifest.json",
            ],
        },
    )
    write_text(study_root / "notes" / "revision_status.md", "# Revision\n")
    write_text(study_root / "manuscript" / "submission_manifest.json", "{}\n")

    monkeypatch.setattr(
        module.quest_state,
        "inspect_quest_runtime",
        lambda quest_root: module.quest_state.QuestRuntimeSnapshot(
            quest_exists=True,
            quest_status="paused",
            bash_session_audit=None,
        ),
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "sync_completion_with_approval",
        lambda *, runtime_root, quest_id, decision_request_payload, approval_text, summary, source: {
            "completion_request": {
                "status": "ok",
                "interaction_id": "decision-001",
                "payload": decision_request_payload,
            },
            "approval_message": {
                "ok": True,
                "message": {
                    "id": "msg-approval",
                    "content": approval_text,
                },
            },
            "completion": {
                "ok": True,
                "status": "completed",
                "snapshot": {"quest_id": quest_id, "status": "completed"},
                "message": summary,
            },
        },
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")
    runtime_binding = yaml.safe_load((study_root / "runtime_binding.yaml").read_text(encoding="utf-8"))
    launch_report = json.loads((study_root / "artifacts" / "runtime" / "last_launch_report.json").read_text(encoding="utf-8"))

    assert result["decision"] == "completed"
    assert result["reason"] == "study_completion_synced"
    assert result["quest_status"] == "completed"
    assert result["completion_sync"]["completion"]["status"] == "completed"
    assert runtime_binding["last_action"] == "completed"
    assert launch_report["decision"] == "completed"
    assert launch_report["reason"] == "study_completion_synced"


def test_build_study_completion_request_message_accepts_typed_completion_state(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    completion_module = importlib.import_module("med_autoscience.study_completion")
    study_root = tmp_path / "study"
    completion_state = completion_module.StudyCompletionState(
        status=completion_module.StudyCompletionStateStatus.RESOLVED,
        contract=completion_module.StudyCompletionContract(
            study_root=study_root,
            status=completion_module.StudyCompletionContractStatus.COMPLETED,
            summary="Study-level finalized delivery is complete.",
            user_approval_text="同意",
            completed_at="2026-04-03T00:00:00+00:00",
            evidence_paths=(
                "notes/revision_status.md",
                "manuscript/submission_manifest.json",
            ),
            missing_evidence_paths=(),
        ),
        errors=(),
    )

    message = module._build_study_completion_request_message(
        study_id="001-risk",
        study_root=study_root,
        completion_state=completion_state,
    )

    assert "Completion summary: Study-level finalized delivery is complete." in message
    assert "- `notes/revision_status.md`" in message
    assert "Please record explicit quest-completion approval" in message


def test_ensure_study_runtime_prefers_runtime_reentry_anchor_when_configured(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
        runtime_reentry_required_paths=[],
        runtime_reentry_first_unit="00_entry_validation",
    )
    write_text(study_root / "analysis" / "clean_room_execution" / "00_entry_validation" / "README.md", "# entry\n")
    created: dict[str, object] = {}

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "create_quest",
        lambda *, runtime_root, payload: created.update({"runtime_root": runtime_root, "payload": payload})
        or {
            "ok": True,
            "snapshot": {
                "quest_id": "001-risk",
                "quest_root": str(runtime_root / "001-risk"),
                "status": "created",
            },
        },
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: {"ok": True, "status": "running"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    contract = created["payload"]["startup_contract"]
    assert result["decision"] == "create_and_start"
    assert result["startup_boundary_gate"]["required_first_anchor"] == "00_entry_validation"
    assert result["startup_boundary_gate"]["effective_custom_profile"] == "continue_existing_state"
    assert contract["required_first_anchor"] == "00_entry_validation"
    assert contract["custom_profile"] == "continue_existing_state"


def test_ensure_study_runtime_creates_quest_before_runtime_overlay_materialization(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    call_order: list[str] = []

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module,
        "_prepare_runtime_overlay",
        lambda *, profile, quest_root: call_order.append("prepare")
        or {"authority": {"selected_action": "noop"}, "materialization": {}, "audit": {"all_roots_ready": True}},
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "create_quest",
        lambda *, runtime_root, payload: call_order.append("create")
        or {
            "ok": True,
            "snapshot": {
                "quest_id": "001-risk",
                "quest_root": str(runtime_root / "001-risk"),
                "status": "created",
            },
        },
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: {"ok": True, "status": "running"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "create_and_start"
    assert call_order[:2] == ["create", "prepare"]


def test_ensure_study_runtime_includes_medical_runtime_contracts(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    created: dict[str, object] = {}
    write_study(
        profile.workspace_root,
        "001-risk",
        paper_framing_summary="Prediction framing is fixed.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
        endpoint_type="binary",
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    def fake_create_quest(*, runtime_root: Path, payload: dict[str, object]) -> dict[str, object]:
        created["runtime_root"] = runtime_root
        created["payload"] = payload
        return {
            "ok": True,
            "snapshot": {
                "quest_id": "001-risk",
                "quest_root": str(runtime_root / "001-risk"),
                "status": "running",
            },
            "startup": {"queued": True},
        }

    monkeypatch.setattr(module.med_deepscientist_transport, "create_quest", fake_create_quest)
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: {"ok": True, "status": "running"},
    )

    module.ensure_study_runtime(profile=profile, study_id="001-risk", source="test")
    startup_contract = created["payload"]["startup_contract"]

    assert startup_contract["schema_version"] == 4
    assert startup_contract["medical_analysis_contract_summary"]["status"] == "resolved"
    assert startup_contract["medical_analysis_contract_summary"]["study_archetype"] == "clinical_classifier"
    assert startup_contract["medical_analysis_contract_summary"]["endpoint_type"] == "binary"
    assert startup_contract["medical_reporting_contract_summary"]["reporting_guideline_family"] == "TRIPOD"
    assert startup_contract["reporting_guideline_family"] == "TRIPOD"


def test_ensure_study_runtime_blocks_before_create_when_reporting_contract_is_unresolved(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profiles = importlib.import_module("med_autoscience.profiles")
    profile = profiles.WorkspaceProfile(
        **{
            **make_profile(tmp_path).__dict__,
            "default_submission_targets": (
                {
                    "publication_profile": "unsupported_profile",
                    "primary": True,
                    "package_required": True,
                    "story_surface": "general_medical_journal",
                },
            ),
        }
    )
    created: dict[str, object] = {}
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        paper_framing_summary="Prediction framing is fixed.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
        endpoint_type="binary",
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )

    def fake_create_quest(*, runtime_root: Path, payload: dict[str, object]) -> dict[str, object]:
        created["payload"] = payload
        return {
            "ok": True,
            "snapshot": {
                "quest_id": "001-risk",
                "quest_root": str(runtime_root / "001-risk"),
                "status": "running",
            },
            "startup": {"queued": True},
        }

    monkeypatch.setattr(module.med_deepscientist_transport, "create_quest", fake_create_quest)
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: {"ok": True, "status": "running"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "startup_contract_resolution_failed"
    assert result["startup_contract_validation"]["blockers"] == [
        "unsupported_medical_analysis_contract",
        "unsupported_medical_reporting_contract",
    ]
    assert "payload" not in created


def test_ensure_study_runtime_hydrates_before_resume(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
        paper_framing_summary="Prediction framing is fixed.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    calls: list[tuple[str, object]] = []

    def fake_create_quest(*, runtime_root: Path, payload: dict[str, object]) -> dict[str, object]:
        calls.append(("create", payload["auto_start"]))
        return {
            "ok": True,
            "snapshot": {
                "quest_id": "001-risk",
                "quest_root": str(runtime_root / "001-risk"),
                "status": "created",
            },
        }

    monkeypatch.setattr(module.med_deepscientist_transport, "create_quest", fake_create_quest)
    monkeypatch.setattr(
        module,
        "quest_hydration_controller",
        SimpleNamespace(
            run_hydration=lambda **kwargs: calls.append(("hydrate", kwargs["quest_root"]))
            or make_startup_hydration_report(kwargs["quest_root"])
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(
            run_validation=lambda **kwargs: calls.append(("validate", kwargs["quest_root"]))
            or make_startup_hydration_validation_report(kwargs["quest_root"])
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: calls.append(("resume", quest_id)) or {"ok": True, "status": "running"},
    )

    module.ensure_study_runtime(profile=profile, study_id="001-risk", source="test")

    assert calls == [
        ("create", False),
        ("hydrate", profile.runtime_root / "001-risk"),
        ("validate", profile.runtime_root / "001-risk"),
        ("resume", "001-risk"),
    ]


def test_ensure_study_runtime_blocks_when_hydration_validation_fails(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
        paper_framing_summary="Prediction framing is fixed.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    calls: list[tuple[str, object]] = []

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "create_quest",
        lambda *, runtime_root, payload: calls.append(("create", payload["auto_start"]))
        or {"ok": True, "snapshot": {"quest_id": "001-risk", "status": "created"}},
    )
    monkeypatch.setattr(
        module,
        "quest_hydration_controller",
        SimpleNamespace(
            run_hydration=lambda **kwargs: calls.append(("hydrate", kwargs["quest_root"]))
            or make_startup_hydration_report(kwargs["quest_root"])
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(
            run_validation=lambda **kwargs: calls.append(("validate", kwargs["quest_root"]))
            or make_startup_hydration_validation_report(
                kwargs["quest_root"],
                status="blocked",
                blockers=["missing_medical_reporting_contract"],
            )
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: calls.append(("resume", quest_id)) or {"ok": True, "status": "running"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "hydration_validation_failed"
    assert result["startup_hydration_validation"]["status"] == "blocked"
    assert calls == [
        ("create", False),
        ("hydrate", profile.runtime_root / "001-risk"),
        ("validate", profile.runtime_root / "001-risk"),
    ]


def test_ensure_study_runtime_blocks_before_create_when_startup_contract_is_unresolved(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = replace(make_profile(tmp_path), preferred_study_archetypes=("clinical_classifier", "gray_zone_triage"))
    write_study(
        profile.workspace_root,
        "001-risk",
        endpoint_type="binary",
        manuscript_family="prediction_model",
    )
    created: dict[str, object] = {}

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "create_quest",
        lambda *, runtime_root, payload: created.setdefault("payload", payload)
        or {"ok": True, "snapshot": {"quest_id": "001-risk", "status": "created"}},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "startup_contract_resolution_failed"
    assert result["startup_contract_validation"]["status"] == "blocked"
    assert result["startup_contract_validation"]["blockers"] == [
        "unsupported_medical_analysis_contract",
        "unsupported_medical_reporting_contract",
    ]
    assert "payload" not in created


def test_ensure_study_runtime_archives_invalid_partial_quest_root_before_create(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
    )
    invalid_quest_root = profile.runtime_root / "001-risk"
    write_text(invalid_quest_root / "paper" / "medical_analysis_contract.json", '{"status":"unsupported"}\n')
    created: dict[str, object] = {}

    monkeypatch.setattr(module, "_timestamp_slug", lambda: "20260402T010203Z")
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )

    def fake_create_quest(*, runtime_root: Path, payload: dict[str, object]) -> dict[str, object]:
        created["payload"] = payload
        assert not invalid_quest_root.exists()
        write_text(invalid_quest_root / "quest.yaml", "quest_id: 001-risk\n")
        return {
            "ok": True,
            "snapshot": {
                "quest_id": "001-risk",
                "quest_root": str(invalid_quest_root),
                "status": "created",
            },
        }

    monkeypatch.setattr(module.med_deepscientist_transport, "create_quest", fake_create_quest)
    monkeypatch.setattr(
        module,
        "quest_hydration_controller",
        SimpleNamespace(run_hydration=lambda **kwargs: make_startup_hydration_report(kwargs["quest_root"])),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(run_validation=lambda **kwargs: make_startup_hydration_validation_report(kwargs["quest_root"])),
        raising=False,
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="test")

    archived_root = (
        profile.med_deepscientist_runtime_root
        / "recovery"
        / "invalid_partial_quest_roots"
        / "001-risk-20260402T010203Z"
    )
    assert result["partial_quest_recovery"]["status"] == "archived_invalid_partial_quest_root"
    assert result["partial_quest_recovery"]["archived_root"] == str(archived_root)
    assert archived_root.joinpath("paper", "medical_analysis_contract.json").exists()
    assert created["payload"]["quest_id"] == "001-risk"


def test_ensure_study_runtime_refreshes_startup_hydration_for_existing_created_quest_when_resume_is_blocked(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
    )
    _write_requested_baseline_ref(study_root, {"baseline_id": "demo-baseline"})
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"created"}\n')
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(module, "_utc_now", lambda: "2026-04-05T06:00:00+00:00")
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module,
        "_prepare_runtime_overlay",
        lambda *, profile, quest_root: calls.append(("prepare_overlay", quest_root)) or make_runtime_overlay_result(),
    )
    monkeypatch.setattr(
        module,
        "quest_hydration_controller",
        SimpleNamespace(
            run_hydration=lambda **kwargs: calls.append(("hydrate", kwargs["quest_root"]))
            or make_startup_hydration_report(kwargs["quest_root"])
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(
            run_validation=lambda **kwargs: calls.append(("validate", kwargs["quest_root"]))
            or make_startup_hydration_validation_report(kwargs["quest_root"])
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "update_quest_startup_context",
        lambda *, runtime_root, quest_id, startup_contract, requested_baseline_ref=None: calls.append(
            ("sync_startup_context", quest_id, startup_contract.get("scope"), requested_baseline_ref)
        )
        or {
            "ok": True,
            "snapshot": {
                "quest_id": quest_id,
                "startup_contract": startup_contract,
                "requested_baseline_ref": requested_baseline_ref,
            },
        },
        raising=False,
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="test")

    escalation_path = quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
    escalation_payload = json.loads(escalation_path.read_text(encoding="utf-8"))
    launch_report = json.loads(Path(result["launch_report_path"]).read_text(encoding="utf-8"))

    assert result["decision"] == "blocked"
    assert result["reason"] == "startup_boundary_not_ready_for_resume"
    assert result["startup_hydration_validation"]["status"] == "clear"
    assert result["runtime_overlay"]["audit"]["all_roots_ready"] is True
    assert result["runtime_escalation_ref"] == {
        "record_id": escalation_payload["record_id"],
        "artifact_path": str(escalation_path),
        "summary_ref": result["launch_report_path"],
    }
    assert escalation_payload["schema_version"] == 1
    assert escalation_payload["study_id"] == "001-risk"
    assert escalation_payload["quest_id"] == "001-risk"
    assert escalation_payload["emitted_at"] == "2026-04-05T06:00:00+00:00"
    assert escalation_payload["trigger"] == {
        "trigger_id": "startup_boundary_not_ready_for_resume",
        "source": "startup_boundary_gate",
    }
    assert escalation_payload["scope"] == "quest"
    assert escalation_payload["severity"] == "quest"
    assert escalation_payload["reason"] == "startup_boundary_not_ready_for_resume"
    assert escalation_payload["recommended_actions"] == ["refresh_startup_hydration", "controller_review_required"]
    assert escalation_payload["summary_ref"] == result["launch_report_path"]
    assert escalation_payload["artifact_path"] == str(escalation_path)
    assert set(escalation_payload["evidence_refs"]) == {
        str(quest_root / "artifacts" / "reports" / "startup" / "hydration_report.json"),
        str(quest_root / "artifacts" / "reports" / "startup" / "hydration_validation_report.json"),
    }
    assert escalation_payload["runtime_context_refs"] == {"launch_report_path": result["launch_report_path"]}
    assert "runtime_escalation_record" not in result
    assert "runtime_escalation_record" not in launch_report
    assert result["startup_context_sync"]["ok"] is True
    assert result["startup_context_sync"]["quest_id"] == "001-risk"
    assert result["startup_context_sync"]["snapshot"]["requested_baseline_ref"] == {
        "baseline_id": "demo-baseline"
    }
    synced_contract = result["startup_context_sync"]["snapshot"]["startup_contract"]
    assert "runtime_escalation_record" not in synced_contract
    assert "runtime_escalation_ref" not in synced_contract
    assert calls == [
        ("prepare_overlay", quest_root),
        ("sync_startup_context", "001-risk", "full_research", {"baseline_id": "demo-baseline"}),
        ("hydrate", quest_root),
        ("validate", quest_root),
    ]


def test_ensure_study_runtime_blocks_when_existing_created_quest_overlay_refresh_still_fails(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"created"}\n')
    calls: list[str] = []

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module,
        "_prepare_runtime_overlay",
        lambda *, profile, quest_root: calls.append("prepare_overlay")
        or make_runtime_overlay_result(all_roots_ready=False),
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "update_quest_startup_context",
        lambda **kwargs: pytest.fail("update_quest_startup_context should not run when overlay refresh stays broken"),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "quest_hydration_controller",
        SimpleNamespace(
            run_hydration=lambda **kwargs: pytest.fail("hydration should not run when overlay refresh stays broken")
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(
            run_validation=lambda **kwargs: pytest.fail("validation should not run when overlay refresh stays broken")
        ),
        raising=False,
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "runtime_overlay_not_ready"
    assert result["runtime_overlay"]["audit"]["all_roots_ready"] is False
    assert calls == ["prepare_overlay"]


def test_ensure_study_runtime_uses_protocol_refresh_gate_for_blocked_existing_quest(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"created"}\n')
    calls: list[str] = []

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module.StudyRuntimeStatus,
        "should_refresh_startup_hydration_while_blocked",
        lambda self: False,
    )
    monkeypatch.setattr(
        module,
        "quest_hydration_controller",
        SimpleNamespace(
            run_hydration=lambda **kwargs: calls.append("hydrate")
            or make_startup_hydration_report(kwargs["quest_root"])
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(
            run_validation=lambda **kwargs: calls.append("validate")
            or make_startup_hydration_validation_report(kwargs["quest_root"])
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "_prepare_runtime_overlay",
        lambda *, profile, quest_root: calls.append("prepare_overlay") or make_runtime_overlay_result(),
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "startup_boundary_not_ready_for_resume"
    assert result["runtime_overlay"]["audit"]["all_roots_ready"] is True
    assert calls == ["prepare_overlay"]


def test_ensure_study_runtime_materializes_overlay_for_non_resumable_existing_quest(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"completed"}\n')
    calls: list[str] = []

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module,
        "_prepare_runtime_overlay",
        lambda *, profile, quest_root: calls.append("prepare_overlay") or make_runtime_overlay_result(),
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "update_quest_startup_context",
        lambda **kwargs: pytest.fail("startup context sync should not run for non-resumable completed quest"),
        raising=False,
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_exists_with_non_resumable_state"
    assert result["runtime_overlay"]["audit"]["all_roots_ready"] is True
    assert calls == ["prepare_overlay"]


def test_ensure_study_runtime_resumes_paused_quest(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    study_root = profile.workspace_root / "studies" / "001-risk"
    write_text(study_root / "analysis" / "clean_room_execution" / "00_entry_validation" / "README.md", "# entry\n")
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"paused"}\n')
    calls: list[tuple[str, object]] = []

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module,
        "quest_hydration_controller",
        SimpleNamespace(
            run_hydration=lambda **kwargs: calls.append(("hydrate", kwargs["quest_root"]))
            or make_startup_hydration_report(kwargs["quest_root"])
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(
            run_validation=lambda **kwargs: calls.append(("validate", kwargs["quest_root"]))
            or make_startup_hydration_validation_report(kwargs["quest_root"])
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: calls.append(("resume", quest_id)) or {"ok": True, "status": "running"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "resume"
    assert calls == [
        ("hydrate", profile.runtime_root / "001-risk"),
        ("validate", profile.runtime_root / "001-risk"),
        ("resume", "001-risk"),
    ]


def test_ensure_study_runtime_resume_rehydrates_when_runtime_reentry_requires_startup_hydration(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
        runtime_reentry_required_paths=[],
        runtime_reentry_require_startup_hydration=True,
    )
    study_root = profile.workspace_root / "studies" / "001-risk"
    write_text(study_root / "analysis" / "clean_room_execution" / "00_entry_validation" / "README.md", "# entry\n")
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"paused"}\n')
    calls: list[tuple[str, object]] = []

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module,
        "quest_hydration_controller",
        SimpleNamespace(
            run_hydration=lambda **kwargs: calls.append(("hydrate", kwargs["quest_root"]))
            or make_startup_hydration_report(kwargs["quest_root"])
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(
            run_validation=lambda **kwargs: calls.append(("validate", kwargs["quest_root"]))
            or make_startup_hydration_validation_report(kwargs["quest_root"])
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: calls.append(("resume", quest_id)) or {"ok": True, "status": "running"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "resume"
    assert calls == [
        ("hydrate", profile.runtime_root / "001-risk"),
        ("validate", profile.runtime_root / "001-risk"),
        ("resume", "001-risk"),
    ]


def test_ensure_study_runtime_blocks_resume_when_runtime_reentry_hydration_validation_fails(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
        runtime_reentry_required_paths=[],
        runtime_reentry_require_startup_hydration=True,
    )
    study_root = profile.workspace_root / "studies" / "001-risk"
    write_text(study_root / "analysis" / "clean_room_execution" / "00_entry_validation" / "README.md", "# entry\n")
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"paused"}\n')
    calls: list[tuple[str, object]] = []

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module,
        "quest_hydration_controller",
        SimpleNamespace(
            run_hydration=lambda **kwargs: calls.append(("hydrate", kwargs["quest_root"]))
            or make_startup_hydration_report(kwargs["quest_root"])
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(
            run_validation=lambda **kwargs: calls.append(("validate", kwargs["quest_root"]))
            or make_startup_hydration_validation_report(
                kwargs["quest_root"],
                status="blocked",
                blockers=["unsupported_medical_analysis_contract"],
            )
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: calls.append(("resume", quest_id)) or {"ok": True, "status": "running"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "hydration_validation_failed"
    assert calls == [
        ("hydrate", profile.runtime_root / "001-risk"),
        ("validate", profile.runtime_root / "001-risk"),
    ]


def test_ensure_study_runtime_blocks_when_managed_skill_audit_is_required_but_overlay_is_disabled(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = replace(make_profile(tmp_path), enable_medical_overlay=False)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
        runtime_reentry_required_paths=[],
        runtime_reentry_require_managed_skill_audit=True,
    )
    study_root = profile.workspace_root / "studies" / "001-risk"
    write_text(study_root / "analysis" / "clean_room_execution" / "00_entry_validation" / "README.md", "# entry\n")
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"paused"}\n')

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "managed_skill_audit_not_available"


def test_ensure_study_runtime_pauses_running_quest_when_required_startup_hydration_is_blocked(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
        runtime_reentry_required_paths=[],
        runtime_reentry_require_startup_hydration=True,
    )
    write_text(study_root / "analysis" / "clean_room_execution" / "00_entry_validation" / "README.md", "# entry\n")
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"running"}\n')
    write_text(quest_root / "paper" / "medical_analysis_contract.json", '{\"status\":\"unsupported\"}\n')
    write_text(quest_root / "paper" / "medical_reporting_contract.json", '{\"status\":\"resolved\"}\n')

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "pause_quest",
        lambda *, runtime_root, quest_id, source: {"ok": True, "status": "paused"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "pause"
    assert result["reason"] == "runtime_reentry_not_ready_for_running_quest"
    assert "unsupported_medical_analysis_contract" in result["runtime_reentry_gate"]["blockers"]


def test_ensure_study_runtime_noops_when_quest_is_already_running(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"running"}\n')

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "live",
            "source": "combined_runner_or_bash_session",
            "active_run_id": "run-live",
            "runner_live": True,
            "bash_live": True,
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "daemon_turn_worker",
                "active_run_id": "run-live",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {
                "ok": True,
                "status": "live",
                "session_count": 1,
                "live_session_count": 1,
                "live_session_ids": ["sess-1"],
            },
        },
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resolve_daemon_url",
        lambda *, runtime_root: "http://127.0.0.1:21999",
    )
    result = module.ensure_study_runtime(profile=profile, study_id="001-risk")

    assert result["decision"] == "noop"
    assert result["reason"] == "quest_already_running"
    assert result["runtime_liveness_audit"]["status"] == "live"
    assert result["bash_session_audit"]["status"] == "live"
    assert result["autonomous_runtime_notice"] == {
        "required": True,
        "notice_key": "quest:001-risk:run-live",
        "notification_reason": "detected_existing_live_managed_runtime",
        "quest_id": "001-risk",
        "quest_status": "running",
        "active_run_id": "run-live",
        "browser_url": "http://127.0.0.1:21999",
        "quest_api_url": "http://127.0.0.1:21999/api/quests/001-risk",
        "quest_session_api_url": "http://127.0.0.1:21999/api/quests/001-risk/session",
        "monitoring_available": True,
        "monitoring_error": None,
        "launch_report_path": str(
            profile.workspace_root / "studies" / "001-risk" / "artifacts" / "runtime" / "last_launch_report.json"
        ),
    }
    assert result["execution_owner_guard"] == {
        "owner": "managed_runtime",
        "supervisor_only": True,
        "guard_reason": "live_managed_runtime",
        "active_run_id": "run-live",
        "current_required_action": "supervise_managed_runtime",
        "allowed_actions": [
            "read_runtime_status",
            "notify_user_runtime_is_live",
            "open_monitoring_entry",
            "pause_runtime",
            "resume_runtime",
            "stop_runtime",
            "record_user_decision",
        ],
        "forbidden_actions": [
            "direct_study_execution",
            "direct_runtime_owned_write",
            "direct_paper_line_write",
            "direct_bundle_build",
            "direct_compiled_bundle_proofing",
        ],
        "runtime_owned_roots": [
            str(quest_root),
            str(quest_root / ".ds"),
            str(quest_root / "paper"),
            str(quest_root / "release"),
            str(quest_root / "artifacts"),
        ],
        "takeover_required": True,
        "takeover_action": "pause_runtime_then_explicit_human_takeover",
        "publication_gate_allows_direct_write": False,
        "controller_stage_note": (
            "live managed runtime owns study-local execution; the foreground agent must stay supervisor-only "
            "until explicit takeover"
        ),
    }


def test_ensure_study_runtime_resumes_running_quest_when_daemon_has_no_live_session(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    study_root = profile.workspace_root / "studies" / "001-risk"
    write_text(study_root / "analysis" / "clean_room_execution" / "00_entry_validation" / "README.md", "# entry\n")
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"running"}\n')
    calls: list[tuple[str, object]] = []

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "none",
            "source": "combined_runner_or_bash_session",
            "active_run_id": "run-stale",
            "runner_live": False,
            "bash_live": False,
            "runtime_audit": {
                "ok": True,
                "status": "none",
                "source": "daemon_turn_worker",
                "active_run_id": "run-stale",
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {
                "ok": True,
                "status": "none",
                "session_count": 1,
                "live_session_count": 0,
                "live_session_ids": [],
            },
        },
    )
    monkeypatch.setattr(
        module,
        "quest_hydration_controller",
        SimpleNamespace(
            run_hydration=lambda **kwargs: calls.append(("hydrate", kwargs["quest_root"]))
            or make_startup_hydration_report(kwargs["quest_root"])
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(
            run_validation=lambda **kwargs: calls.append(("validate", kwargs["quest_root"]))
            or make_startup_hydration_validation_report(kwargs["quest_root"])
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: calls.append(("resume", quest_id)) or {"ok": True, "status": "running"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_marked_running_but_no_live_session"
    assert result["runtime_liveness_audit"]["status"] == "none"
    assert result["bash_session_audit"]["status"] == "none"
    assert calls == [
        ("hydrate", profile.runtime_root / "001-risk"),
        ("validate", profile.runtime_root / "001-risk"),
        ("resume", "001-risk"),
    ]


def test_ensure_study_runtime_blocks_running_quest_when_live_session_audit_fails(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"running"}\n')

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": False,
            "status": "unknown",
            "source": "combined_runner_or_bash_session",
            "active_run_id": None,
            "runner_live": False,
            "bash_live": False,
            "runtime_audit": {
                "ok": False,
                "status": "unknown",
                "source": "quest_session_runtime_audit",
                "active_run_id": None,
                "worker_running": None,
                "worker_pending": None,
                "stop_requested": None,
                "error": "daemon unavailable",
            },
            "bash_session_audit": {
                "ok": False,
                "status": "unknown",
                "session_count": None,
                "live_session_count": None,
                "live_session_ids": [],
                "error": "daemon unavailable",
            },
            "error": "daemon unavailable | daemon unavailable",
        },
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk")

    assert result["decision"] == "blocked"
    assert result["reason"] == "running_quest_live_session_audit_failed"
    assert result["runtime_liveness_audit"]["status"] == "unknown"
    assert result["bash_session_audit"]["status"] == "unknown"


def test_ensure_study_runtime_keeps_supervisor_only_guard_when_live_runtime_progress_is_stale(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"running","active_run_id":"run-live-stale"}\n')

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resolve_daemon_url",
        lambda *, runtime_root: "http://127.0.0.1:21999",
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": False,
            "status": "unknown",
            "source": "combined_runner_or_bash_session",
            "active_run_id": "run-live-stale",
            "runner_live": True,
            "bash_live": False,
            "stale_progress": True,
            "liveness_guard_reason": "stale_progress_watchdog",
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "daemon_turn_worker",
                "active_run_id": "run-live-stale",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
                "interaction_watchdog": {
                    "last_artifact_interact_at": "2026-04-08T10:05:03+00:00",
                    "seconds_since_last_artifact_interact": 3600,
                    "tool_calls_since_last_artifact_interact": 0,
                    "active_execution_window": True,
                    "stale_visibility_gap": True,
                    "inspection_due": True,
                    "user_update_due": False,
                },
                "stale_progress": True,
                "liveness_guard_reason": "stale_progress_watchdog",
            },
            "bash_session_audit": {
                "ok": True,
                "status": "none",
                "session_count": 0,
                "live_session_count": 0,
                "live_session_ids": [],
            },
            "error": "Live managed runtime exceeded the artifact interaction silence threshold.",
        },
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk")

    assert result["decision"] == "blocked"
    assert result["reason"] == "running_quest_live_session_audit_failed"
    assert result["runtime_liveness_audit"]["status"] == "unknown"
    assert result["runtime_liveness_audit"]["stale_progress"] is True
    assert result["autonomous_runtime_notice"]["required"] is True
    assert result["autonomous_runtime_notice"]["active_run_id"] == "run-live-stale"
    assert result["execution_owner_guard"] == {
        "owner": "managed_runtime",
        "supervisor_only": True,
        "guard_reason": "managed_runtime_audit_unhealthy",
        "active_run_id": "run-live-stale",
        "current_required_action": "inspect_runtime_health_and_decide_intervention",
        "allowed_actions": [
            "read_runtime_status",
            "notify_user_runtime_is_live",
            "open_monitoring_entry",
            "pause_runtime",
            "resume_runtime",
            "stop_runtime",
            "record_user_decision",
        ],
        "forbidden_actions": [
            "direct_study_execution",
            "direct_runtime_owned_write",
            "direct_paper_line_write",
            "direct_bundle_build",
            "direct_compiled_bundle_proofing",
        ],
        "runtime_owned_roots": [
            str(quest_root),
            str(quest_root / ".ds"),
            str(quest_root / "paper"),
            str(quest_root / "release"),
            str(quest_root / "artifacts"),
        ],
        "takeover_required": True,
        "takeover_action": "pause_runtime_then_explicit_human_takeover",
        "publication_gate_allows_direct_write": False,
        "controller_stage_note": (
            "managed runtime still owns study-local execution, but the liveness audit is unhealthy; "
            "stay supervisor-only until the runtime is inspected and explicitly paused or resumed"
        ),
    }


def test_ensure_study_runtime_blocks_when_resume_request_fails_after_active_quest_is_parked(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"active"}\n')
    calls: list[tuple[str, object]] = []

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "none",
            "source": "local_runtime_state_contract",
            "active_run_id": None,
            "runner_live": False,
            "bash_live": False,
            "runtime_audit": {"ok": False, "status": "unknown", "error": "daemon unavailable"},
            "bash_session_audit": {"ok": False, "status": "unknown", "error": "daemon unavailable"},
            "local_runtime_state": {"status": "active", "active_run_id": None},
            "probe_error": "daemon unavailable | daemon unavailable",
        },
    )
    monkeypatch.setattr(
        module,
        "quest_hydration_controller",
        SimpleNamespace(
            run_hydration=lambda **kwargs: calls.append(("hydrate", kwargs["quest_root"]))
            or make_startup_hydration_report(kwargs["quest_root"])
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(
            run_validation=lambda **kwargs: calls.append(("validate", kwargs["quest_root"]))
            or make_startup_hydration_validation_report(kwargs["quest_root"])
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "update_quest_startup_context",
        lambda *, runtime_root, quest_id, startup_contract, requested_baseline_ref=None: calls.append(
            ("sync_startup_context", quest_id, startup_contract.get("scope"))
        )
        or {"ok": True, "snapshot": {"quest_id": quest_id, "startup_contract": startup_contract}},
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: (_ for _ in ()).throw(RuntimeError("daemon unavailable")),
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "resume_request_failed"
    assert result["runtime_liveness_audit"]["status"] == "none"
    launch_report = json.loads(
        (profile.workspace_root / "studies" / "001-risk" / "artifacts" / "runtime" / "last_launch_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert launch_report["daemon_result"]["resume"]["status"] == "unavailable"
    assert "daemon unavailable" in launch_report["daemon_result"]["resume"]["error"]
    assert calls == [
        ("sync_startup_context", "001-risk", "full_research"),
        ("hydrate", profile.runtime_root / "001-risk"),
        ("validate", profile.runtime_root / "001-risk"),
    ]


def test_ensure_study_runtime_blocks_when_create_request_fails(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "create_quest",
        lambda *, runtime_root, payload: (_ for _ in ()).throw(RuntimeError("daemon unavailable")),
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: pytest.fail("resume_quest should not run after create failure"),
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "create_request_failed"
    assert result["quest_exists"] is False
    launch_report = json.loads(
        (profile.workspace_root / "studies" / "001-risk" / "artifacts" / "runtime" / "last_launch_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert launch_report["daemon_result"]["create"]["status"] == "unavailable"
    assert "daemon unavailable" in launch_report["daemon_result"]["create"]["error"]


def test_ensure_study_runtime_stays_lightweight_for_non_managed_entry_mode(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", entry_mode="literature_scout")

    assert result["decision"] == "lightweight"
    assert result["reason"] == "entry_mode_not_managed"


def test_ensure_study_runtime_blocks_when_study_has_unresolved_data_contract(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
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
        lambda *, workspace_root: {
            "status": "attention_needed",
            "study_summary": {
                "study_count": 1,
                "review_needed_count": 1,
                "clear_count": 0,
                "review_needed_study_ids": ["001-risk"],
                "clear_study_ids": [],
                "outdated_private_release_study_ids": [],
                "unresolved_contract_study_ids": ["001-risk"],
                "public_extension_study_ids": [],
            },
        },
    )
    result = module.ensure_study_runtime(profile=profile, study_id="001-risk")

    assert result["decision"] == "blocked"
    assert result["reason"] == "study_data_readiness_blocked"


def test_ensure_study_runtime_creates_without_starting_when_startup_boundary_is_incomplete(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    created: dict[str, object] = {}

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )

    def fake_create_quest(*, runtime_root: Path, payload: dict[str, object]) -> dict[str, object]:
        created["runtime_root"] = runtime_root
        created["payload"] = payload
        return {
            "ok": True,
            "snapshot": {
                "quest_id": "001-risk",
                "quest_root": str(runtime_root / "001-risk"),
                "status": "created",
            },
        }

    monkeypatch.setattr(module.med_deepscientist_transport, "create_quest", fake_create_quest)

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    payload = created["payload"]
    contract = payload["startup_contract"]
    assert result["decision"] == "create_only"
    assert result["reason"] == "startup_boundary_not_ready_for_auto_start"
    assert payload["auto_start"] is False
    assert result["startup_boundary_gate"]["allow_compute_stage"] is False
    assert result["startup_boundary_gate"]["required_first_anchor"] == "scout"
    assert result["startup_boundary_gate"]["missing_requirements"] == [
        "paper_framing",
        "journal_shortlist",
        "evidence_package",
    ]
    assert contract["custom_profile"] == "freeform"
    assert contract["scope"] == "full_research"
    assert contract["baseline_mode"] == "stop_if_insufficient"
    assert contract["baseline_execution_policy"] == "skip_unless_blocking"
    assert contract["required_first_anchor"] == "scout"
    assert contract["legacy_code_execution_allowed"] is False
    assert contract["startup_boundary_gate"]["allow_compute_stage"] is False
    assert "resolve-reference-papers" in contract["controller_first_policy_summary"]
    assert "Only when the platform does not already provide a stable controller" in contract["controller_first_policy_summary"]
    assert "when a study boundary is explicit and startup-ready" in contract["automation_ready_summary"]
    assert "Do not enter baseline, experiment, or analysis-campaign" in contract["custom_brief"]
    assert "Check `portfolio/data_assets/public/registry.json` before route lock" in contract["custom_brief"]
    assert "Do not execute legacy implementation code" in contract["custom_brief"]
    assert "prefer mature MedAutoScience controllers before freeform external execution" in contract["custom_brief"]


def test_ensure_study_runtime_blocks_when_runtime_reentry_gate_is_incomplete(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
        runtime_reentry_required_paths=["analysis/paper_facing_evidence_contract.md"],
        runtime_reentry_first_unit="10_china_primary_endpoint",
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "runtime_reentry_not_ready_for_auto_start"
    assert result["runtime_reentry_gate"]["allow_runtime_entry"] is False
    assert "missing_required_path:analysis/paper_facing_evidence_contract.md" in result["runtime_reentry_gate"]["blockers"]


def test_ensure_study_runtime_applies_startup_boundary_to_non_continue_launch_profiles(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        launch_profile="review_audit",
    )
    created: dict[str, object] = {}

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )

    def fake_create_quest(*, runtime_root: Path, payload: dict[str, object]) -> dict[str, object]:
        created["runtime_root"] = runtime_root
        created["payload"] = payload
        return {
            "ok": True,
            "snapshot": {
                "quest_id": "001-risk",
                "quest_root": str(runtime_root / "001-risk"),
                "status": "created",
            },
        }

    monkeypatch.setattr(module.med_deepscientist_transport, "create_quest", fake_create_quest)

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    payload = created["payload"]
    contract = payload["startup_contract"]
    assert result["decision"] == "create_only"
    assert payload["auto_start"] is False
    assert contract["scope"] == "full_research"
    assert contract["baseline_mode"] == "stop_if_insufficient"
    assert contract["baseline_execution_policy"] == "skip_unless_blocking"
    assert contract["required_first_anchor"] == "scout"
    assert contract["startup_boundary_gate"]["status"] == "scout_first_required"


def test_ensure_study_runtime_pauses_running_quest_when_startup_boundary_disallows_compute(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"running"}\n')
    paused: dict[str, object] = {}

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )

    def fake_pause_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, object]:
        paused["runtime_root"] = runtime_root
        paused["quest_id"] = quest_id
        paused["source"] = source
        return {"ok": True, "status": "paused"}

    monkeypatch.setattr(module.med_deepscientist_transport, "pause_quest", fake_pause_quest)

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "pause"
    assert result["reason"] == "startup_boundary_not_ready_for_running_quest"
    assert result["quest_status"] == "paused"
    assert paused == {
        "runtime_root": profile.med_deepscientist_runtime_root,
        "quest_id": "001-risk",
        "source": "medautosci-test",
    }


def test_ensure_study_runtime_blocks_resume_when_startup_boundary_disallows_compute(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"paused"}\n')

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk")

    assert result["decision"] == "blocked"
    assert result["reason"] == "startup_boundary_not_ready_for_resume"
    assert result["startup_boundary_gate"]["allow_compute_stage"] is False


def test_study_runtime_status_requires_evidence_backed_journal_shortlist(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["Heart"],
        journal_shortlist_evidence=[],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )

    result = module.study_runtime_status(
        profile=profile,
        study_root=study_root,
    )

    assert result["startup_boundary_gate"]["allow_compute_stage"] is False
    assert result["startup_boundary_gate"]["journal_shortlist_ready"] is False
    assert result["startup_boundary_gate"]["journal_shortlist_contract_status"] == "absent"


def test_ensure_study_runtime_uses_protocol_hydration_payload_builder(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
        paper_framing_summary="Prediction framing is fixed.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    seen: dict[str, object] = {}

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "create_quest",
        lambda *, runtime_root, payload: {
            "ok": True,
            "snapshot": {"quest_id": "001-risk", "quest_root": str(runtime_root / "001-risk"), "status": "created"},
        },
    )
    monkeypatch.setattr(
        module.study_runtime_protocol,
        "build_hydration_payload",
        lambda *, create_payload: seen.setdefault("hydration_payload", {"sentinel": True}),
    )
    monkeypatch.setattr(
        module,
        "quest_hydration_controller",
        SimpleNamespace(
            run_hydration=lambda *, quest_root, hydration_payload: (
                seen.__setitem__("run_hydration", hydration_payload) or make_startup_hydration_report(quest_root)
            )
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(run_validation=lambda *, quest_root: make_startup_hydration_validation_report(quest_root)),
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: {"ok": True, "status": "running"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="test")

    assert result["decision"] == "create_and_start"
    assert seen["hydration_payload"] == {"sentinel": True}
    assert seen["run_hydration"] == {"sentinel": True}


def test_ensure_study_runtime_uses_protocol_startup_contract_validation(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
    )
    called: dict[str, object] = {"create_called": False}

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module.study_runtime_protocol,
        "validate_startup_contract_resolution",
        lambda *, startup_contract: module.study_runtime_protocol.StartupContractValidation(
            status="blocked",
            blockers=("forced_blocker",),
            medical_analysis_contract_status=None,
            medical_reporting_contract_status=None,
            medical_analysis_reason_code=None,
            medical_reporting_reason_code=None,
        ),
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "create_quest",
        lambda **kwargs: called.__setitem__("create_called", True) or {},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="test")

    assert result["decision"] == "blocked"
    assert result["startup_contract_validation"]["blockers"] == ["forced_blocker"]
    assert called["create_called"] is False


def test_ensure_study_runtime_resumes_idle_quest_after_startup_boundary_clears(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    study_root = profile.workspace_root / "studies" / "001-risk"
    write_text(study_root / "analysis" / "clean_room_execution" / "00_entry_validation" / "README.md", "# entry\n")
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"idle"}\n')
    calls: list[tuple[str, object]] = []

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module,
        "quest_hydration_controller",
        SimpleNamespace(
            run_hydration=lambda **kwargs: calls.append(("hydrate", kwargs["quest_root"]))
            or make_startup_hydration_report(kwargs["quest_root"])
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(
            run_validation=lambda **kwargs: calls.append(("validate", kwargs["quest_root"]))
            or make_startup_hydration_validation_report(kwargs["quest_root"])
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "update_quest_startup_context",
        lambda *, runtime_root, quest_id, startup_contract, requested_baseline_ref=None: calls.append(
            ("sync_startup_context", quest_id, startup_contract.get("scope"))
        )
        or {"ok": True, "snapshot": {"quest_id": quest_id, "startup_contract": startup_contract}},
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: calls.append(("resume", quest_id)) or {"ok": True, "status": "active"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_initialized_waiting_to_start"
    assert result["quest_status"] == "active"
    assert calls == [
        ("sync_startup_context", "001-risk", "full_research"),
        ("hydrate", profile.runtime_root / "001-risk"),
        ("validate", profile.runtime_root / "001-risk"),
        ("resume", "001-risk"),
    ]


def test_ensure_study_runtime_forwards_requested_baseline_ref_when_syncing_existing_quest(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    _write_requested_baseline_ref(study_root, {"baseline_id": "demo-baseline"})
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"idle"}\n')
    seen: dict[str, object] = {}

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module,
        "quest_hydration_controller",
        SimpleNamespace(
            run_hydration=lambda **kwargs: make_startup_hydration_report(kwargs["quest_root"])
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(
            run_validation=lambda **kwargs: make_startup_hydration_validation_report(kwargs["quest_root"])
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "update_quest_startup_context",
        lambda *, runtime_root, quest_id, startup_contract, requested_baseline_ref=None: (
            seen.__setitem__("requested_baseline_ref", requested_baseline_ref)
            or {
                "ok": True,
                "snapshot": {
                    "quest_id": quest_id,
                    "startup_contract": startup_contract,
                    "requested_baseline_ref": requested_baseline_ref,
                },
            }
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: {"ok": True, "status": "active"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "resume"
    assert seen["requested_baseline_ref"] == {"baseline_id": "demo-baseline"}
    assert result["startup_context_sync"]["snapshot"]["requested_baseline_ref"] == {"baseline_id": "demo-baseline"}


def _write_runtime_escalation_record_for_status_test(
    *,
    protocol,
    quest_root: Path,
    launch_report_path: Path,
):
    return protocol.write_runtime_escalation_record(
        quest_root=quest_root,
        record=protocol.RuntimeEscalationRecord(
            schema_version=1,
            record_id="runtime-escalation::001-risk::001-risk::startup_boundary_not_ready_for_resume::2026-04-05T06:00:00+00:00",
            study_id="001-risk",
            quest_id="001-risk",
            emitted_at="2026-04-05T06:00:00+00:00",
            trigger=protocol.RuntimeEscalationTrigger(
                trigger_id="startup_boundary_not_ready_for_resume",
                source="startup_boundary_gate",
            ),
            scope="quest",
            severity="quest",
            reason="startup_boundary_not_ready_for_resume",
            recommended_actions=("refresh_startup_hydration", "controller_review_required"),
            evidence_refs=(
                str(quest_root / "artifacts" / "reports" / "startup" / "hydration_report.json"),
                str(quest_root / "artifacts" / "reports" / "startup" / "hydration_validation_report.json"),
            ),
            runtime_context_refs={"launch_report_path": str(launch_report_path)},
            summary_ref=str(launch_report_path),
            artifact_path=None,
        ),
    )


def test_study_runtime_status_reads_only_runtime_escalation_ref_from_quest_artifact_when_blocked_refresh_is_active(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    protocol = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    study_root = profile.workspace_root / "studies" / "001-risk"
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"created"}\n')
    study_yaml_path = study_root / "study.yaml"
    study_yaml_path.write_text(
        study_yaml_path.read_text(encoding="utf-8").replace("  auto_resume: true\n", "  auto_resume: false\n"),
        encoding="utf-8",
    )
    launch_report_path = study_root / "artifacts" / "runtime" / "last_launch_report.json"
    written_record = _write_runtime_escalation_record_for_status_test(
        protocol=protocol,
        quest_root=quest_root,
        launch_report_path=launch_report_path,
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_initialized_but_auto_resume_disabled"
    assert result["runtime_escalation_ref"] == written_record.ref().to_dict()
    assert "runtime_escalation_record" not in result
    assert "runtime_escalation_ref" not in result["execution"]
    serialized_result = json.dumps(result, ensure_ascii=False)
    assert "runtime_context_refs" not in serialized_result
    assert "recommended_actions" not in serialized_result


def test_study_runtime_status_does_not_expose_runtime_escalation_ref_for_non_med_deepscientist_execution(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    protocol = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    study_root = profile.workspace_root / "studies" / "001-risk"
    study_yaml_path = study_root / "study.yaml"
    study_yaml_path.write_text(
        study_yaml_path.read_text(encoding="utf-8").replace(
            "  engine: med-deepscientist\n",
            "  engine: lightweight-runtime\n",
        ),
        encoding="utf-8",
    )
    quest_root = profile.runtime_root / "001-risk"
    launch_report_path = study_root / "artifacts" / "runtime" / "last_launch_report.json"
    _write_runtime_escalation_record_for_status_test(
        protocol=protocol,
        quest_root=quest_root,
        launch_report_path=launch_report_path,
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "lightweight"
    assert result["reason"] == "study_execution_not_med_deepscientist"
    assert "runtime_escalation_ref" not in result


def test_study_runtime_status_does_not_echo_stale_runtime_escalation_ref_after_block_clears(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    protocol = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    study_root = profile.workspace_root / "studies" / "001-risk"
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"created"}\n')
    launch_report_path = study_root / "artifacts" / "runtime" / "last_launch_report.json"
    _write_runtime_escalation_record_for_status_test(
        protocol=protocol,
        quest_root=quest_root,
        launch_report_path=launch_report_path,
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_initialized_waiting_to_start"
    assert "runtime_escalation_ref" not in result


def test_ensure_study_runtime_uses_custom_quest_id_for_existing_runtime(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        quest_id="001-risk-reentry",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    study_root = profile.workspace_root / "studies" / "001-risk"
    _write_requested_baseline_ref(study_root, {"baseline_id": "demo-baseline"})
    write_text(study_root / "analysis" / "clean_room_execution" / "00_entry_validation" / "README.md", "# entry\n")
    quest_root = profile.runtime_root / "001-risk-reentry"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk-reentry\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"idle"}\n')
    calls: list[tuple[str, object]] = []

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module,
        "quest_hydration_controller",
        SimpleNamespace(
            run_hydration=lambda **kwargs: calls.append(("hydrate", kwargs["quest_root"]))
            or make_startup_hydration_report(kwargs["quest_root"])
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(
            run_validation=lambda **kwargs: calls.append(("validate", kwargs["quest_root"]))
            or make_startup_hydration_validation_report(kwargs["quest_root"])
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "update_quest_startup_context",
        lambda *, runtime_root, quest_id, startup_contract, requested_baseline_ref=None: calls.append(
            ("sync_startup_context", quest_id, startup_contract.get("scope"), requested_baseline_ref)
        )
        or {
            "ok": True,
            "snapshot": {
                "quest_id": quest_id,
                "startup_contract": startup_contract,
                "requested_baseline_ref": requested_baseline_ref,
            },
        },
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: calls.append(("resume", quest_id)) or {"ok": True, "status": "active"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "resume"
    assert result["quest_id"] == "001-risk-reentry"
    assert result["quest_root"] == str(profile.runtime_root / "001-risk-reentry")
    assert result["quest_status"] == "active"
    assert result["startup_context_sync"]["ok"] is True
    assert result["startup_context_sync"]["quest_id"] == "001-risk-reentry"
    assert result["startup_context_sync"]["snapshot"]["requested_baseline_ref"] == {
        "baseline_id": "demo-baseline"
    }
    assert calls == [
        ("sync_startup_context", "001-risk-reentry", "full_research", {"baseline_id": "demo-baseline"}),
        ("hydrate", profile.runtime_root / "001-risk-reentry"),
        ("validate", profile.runtime_root / "001-risk-reentry"),
        ("resume", "001-risk-reentry"),
    ]


def test_ensure_study_runtime_blocks_when_analysis_bundle_is_not_ready(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation"],
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module.analysis_bundle_controller,
        "ensure_study_runtime_analysis_bundle",
        lambda: {"action": "ensure_bundle", "ready": False},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "study_runtime_analysis_bundle_not_ready"
    assert result["analysis_bundle"]["ready"] is False


def test_ensure_study_runtime_pauses_running_quest_when_runtime_overlay_audit_fails(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"running"}\n')
    paused: dict[str, object] = {}

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "live",
            "source": "combined_runner_or_bash_session",
            "active_run_id": "run-001",
            "runner_live": True,
            "bash_live": False,
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "quest_session_runtime_audit",
                "active_run_id": "run-001",
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
    monkeypatch.setattr(
        module.overlay_installer,
        "audit_runtime_medical_overlay",
        lambda **kwargs: {
            "all_roots_ready": False,
            "surface_count": 2,
            "surfaces": [{"surface": "quest"}, {"surface": "worktree"}],
        },
    )

    def fake_pause_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, object]:
        paused["runtime_root"] = runtime_root
        paused["quest_id"] = quest_id
        paused["source"] = source
        return {"ok": True, "status": "paused"}

    monkeypatch.setattr(module.med_deepscientist_transport, "pause_quest", fake_pause_quest)

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "pause"
    assert result["reason"] == "runtime_overlay_audit_failed_for_running_quest"
    assert result["quest_status"] == "paused"
    assert paused == {
        "runtime_root": profile.med_deepscientist_runtime_root,
        "quest_id": "001-risk",
        "source": "medautosci-test",
    }


def test_build_startup_contract_separates_runtime_owned_subset_from_controller_extensions(tmp_path: Path) -> None:
    router = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    ownership = importlib.import_module("med_autoscience.startup_contract")
    profile = make_profile(tmp_path)
    study_root = write_study(
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
    study_payload = yaml.safe_load((study_root / "study.yaml").read_text(encoding="utf-8"))
    execution = router._execution_payload(study_payload)

    startup_contract = router._build_startup_contract(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        study_payload=study_payload,
        execution=execution,
    )

    runtime_owned = ownership.runtime_owned_startup_contract(startup_contract)
    controller_extensions = ownership.controller_owned_startup_contract_extensions(startup_contract)

    assert runtime_owned == {
        "schema_version": 4,
        "user_language": "zh",
        "need_research_paper": True,
        "decision_policy": "autonomous",
        "launch_mode": "custom",
        "custom_profile": startup_contract["custom_profile"],
        "baseline_execution_policy": startup_contract["baseline_execution_policy"],
    }
    assert controller_extensions["scope"] == startup_contract["scope"]
    assert controller_extensions["entry_state_summary"] == startup_contract["entry_state_summary"]
    assert controller_extensions["startup_boundary_gate"] == startup_contract["startup_boundary_gate"]
    assert controller_extensions["runtime_reentry_gate"] == startup_contract["runtime_reentry_gate"]
    assert controller_extensions["medical_analysis_contract_summary"] == startup_contract["medical_analysis_contract_summary"]
    assert controller_extensions["medical_reporting_contract_summary"] == startup_contract["medical_reporting_contract_summary"]
    assert controller_extensions["submission_targets"] == startup_contract["submission_targets"]
    assert "custom_brief" in controller_extensions


def test_compose_startup_contract_rejects_runtime_owned_and_extension_overlap() -> None:
    ownership = importlib.import_module("med_autoscience.startup_contract")

    with pytest.raises(ValueError, match="startup contract ownership overlap"):
        ownership.compose_startup_contract(
            runtime_owned={"launch_mode": "custom"},
            controller_extensions={"launch_mode": "should-not-overlap"},
        )


def test_ensure_study_runtime_keeps_live_audit_blocked_even_if_overlay_audit_fails(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"running"}\n')

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": False,
            "status": "unknown",
            "source": "combined_runner_or_bash_session",
            "active_run_id": None,
            "runner_live": False,
            "bash_live": False,
            "runtime_audit": {
                "ok": False,
                "status": "unknown",
                "source": "quest_session_runtime_audit",
                "active_run_id": None,
                "worker_running": None,
                "worker_pending": None,
                "stop_requested": None,
                "error": "daemon unavailable",
            },
            "bash_session_audit": {
                "ok": False,
                "status": "unknown",
                "session_count": None,
                "live_session_count": None,
                "live_session_ids": [],
                "error": "daemon unavailable",
            },
            "error": "daemon unavailable | daemon unavailable",
        },
    )
    monkeypatch.setattr(
        module.overlay_installer,
        "audit_runtime_medical_overlay",
        lambda **kwargs: {
            "all_roots_ready": False,
            "surface_count": 2,
            "surfaces": [{"surface": "quest"}, {"surface": "worktree"}],
        },
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "pause_quest",
        lambda **kwargs: pytest.fail("pause_quest should not run when live-session audit is unknown"),
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "running_quest_live_session_audit_failed"
    assert result["runtime_liveness_audit"]["status"] == "unknown"
    assert result["runtime_overlay"]["audit"]["all_roots_ready"] is False


def test_study_runtime_status_reports_waiting_for_user_quest_as_blocked(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"waiting_for_user"}\n')
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_waiting_for_user"
    assert result["quest_status"] == "waiting_for_user"


def test_study_runtime_status_surfaces_pending_user_interaction_for_waiting_quest(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"waiting_for_user"}\n')
    write_text(
        quest_root / ".ds" / "worktrees" / "paper-main" / "artifacts" / "progress" / "progress-standby-001.json",
        json.dumps(
            {
                "kind": "progress",
                "schema_version": 1,
                "artifact_id": "progress-standby-001",
                "id": "progress-standby-001",
                "quest_id": "001-risk",
                "created_at": "2026-04-09T01:24:52+00:00",
                "updated_at": "2026-04-09T01:24:52+00:00",
                "status": "active",
                "message": "[等待决策] 这一步已经处理完，等待 Gateway 接管并转发给用户。",
                "summary": "等待 Gateway 侧转发新的用户指令。",
                "interaction_phase": "ack",
                "importance": "info",
                "interaction_id": "progress-standby-001",
                "expects_reply": True,
                "reply_mode": "blocking",
                "surface_actions": [],
                "options": [],
                "allow_free_text": True,
                "reply_schema": {"type": "free_text"},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "get_quest_session",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "quest_id": quest_id,
            "snapshot": {
                "status": "waiting_for_user",
                "waiting_interaction_id": "progress-standby-001",
                "default_reply_interaction_id": "progress-standby-001",
                "pending_decisions": ["progress-standby-001"],
                "active_interaction_id": "progress-standby-001",
            },
            "runtime_audit": {
                "ok": True,
                "status": "none",
                "source": "quest_session_runtime_audit",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_waiting_for_user"
    assert result["quest_status"] == "waiting_for_user"
    assert result["pending_user_interaction"] == {
        "interaction_id": "progress-standby-001",
        "waiting_interaction_id": "progress-standby-001",
        "default_reply_interaction_id": "progress-standby-001",
        "pending_decisions": ["progress-standby-001"],
        "blocking": True,
        "reply_mode": "blocking",
        "expects_reply": True,
        "allow_free_text": True,
        "message": "[等待决策] 这一步已经处理完，等待 Gateway 接管并转发给用户。",
        "summary": "等待 Gateway 侧转发新的用户指令。",
        "reply_schema": {"type": "free_text"},
        "source_artifact_path": str(
            quest_root / ".ds" / "worktrees" / "paper-main" / "artifacts" / "progress" / "progress-standby-001.json"
        ),
        "relay_required": True,
    }


def test_study_runtime_status_treats_submission_metadata_only_waiting_quest_as_resumable(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"waiting_for_user"}\n')
    write_submission_metadata_only_bundle(
        quest_root,
        blocking_item_ids=[
            "author_metadata",
            "ethics_statement",
            "human_subjects_consent_statement",
            "ai_declaration",
        ],
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_waiting_for_submission_metadata"
    assert result["quest_status"] == "waiting_for_user"


def test_ensure_study_runtime_resumes_submission_metadata_only_waiting_quest(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"waiting_for_user"}\n')
    write_submission_metadata_only_bundle(
        quest_root,
        blocking_item_ids=[
            "author_metadata",
            "ethics_statement",
            "human_subjects_consent_statement",
            "ai_declaration",
        ],
    )
    calls: list[str] = []

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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module,
        "_prepare_runtime_overlay",
        lambda *, profile, quest_root: calls.append("prepare_overlay") or make_runtime_overlay_result(),
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "update_quest_startup_context",
        lambda *, runtime_root, quest_id, startup_contract, requested_baseline_ref=None: calls.append("sync_context")
        or {"ok": True, "snapshot": {"quest_id": quest_id, "startup_contract": startup_contract}},
        raising=False,
    )
    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: calls.append("resume") or {"ok": True, "status": "active"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_waiting_for_submission_metadata"
    assert result["quest_status"] == "active"
    assert calls == [
        "prepare_overlay",
        "sync_context",
        "resume",
    ]
