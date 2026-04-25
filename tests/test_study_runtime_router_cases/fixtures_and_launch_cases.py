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
    write_auditable_current_package,
    write_synced_submission_delivery,
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


def _write_execution_overrides(study_root: Path, **overrides: object) -> None:
    study_payload = yaml.safe_load(study_root.joinpath("study.yaml").read_text(encoding="utf-8"))
    if not isinstance(study_payload, dict):
        raise TypeError("study payload must be a mapping")
    execution = study_payload.get("execution")
    if not isinstance(execution, dict):
        raise TypeError("study execution payload must be a mapping")
    execution.update(overrides)
    write_text(
        study_root / "study.yaml",
        yaml.safe_dump(study_payload, allow_unicode=True, sort_keys=False),
    )


def _write_manual_finish_contract(study_root: Path, manual_finish: dict[str, object] | None) -> None:
    study_payload = yaml.safe_load(study_root.joinpath("study.yaml").read_text(encoding="utf-8"))
    if not isinstance(study_payload, dict):
        raise TypeError("study payload must be a mapping")
    if manual_finish is None:
        study_payload.pop("manual_finish", None)
    else:
        study_payload["manual_finish"] = dict(manual_finish)
    write_text(
        study_root / "study.yaml",
        yaml.safe_dump(study_payload, allow_unicode=True, sort_keys=False),
    )


def _managed_runtime_transport(module: object):
    transport = module.managed_runtime_transport
    assert transport is module.med_deepscientist_transport
    return transport


def _materialize_bundle_only_remaining_evaluation_summary(*, study_root: Path, quest_root: Path) -> None:
    summary_module = importlib.import_module("med_autoscience.evaluation_summary")
    study_id = study_root.name
    quest_id = quest_root.name
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    runtime_escalation_path = quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
    gate_report_path = quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"
    publication_objective = "risk stratification external validation"

    write_text(
        charter_path,
        json.dumps(
            {
                "schema_version": 1,
                "charter_id": f"charter::{study_id}::v1",
                "study_id": study_id,
                "publication_objective": publication_objective,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(
        publication_eval_path,
        json.dumps(
            {
                "schema_version": 1,
                "eval_id": f"publication-eval::{study_id}::{quest_id}::2026-04-05T06:00:00+00:00",
                "study_id": study_id,
                "quest_id": quest_id,
                "emitted_at": "2026-04-05T06:00:00+00:00",
                "evaluation_scope": "publication",
                "charter_context_ref": {
                    "ref": str(charter_path),
                    "charter_id": f"charter::{study_id}::v1",
                    "publication_objective": publication_objective,
                },
                "runtime_context_refs": {
                    "runtime_escalation_ref": str(runtime_escalation_path),
                    "main_result_ref": str(quest_root / "artifacts" / "results" / "main_result.json"),
                },
                "delivery_context_refs": {
                    "paper_root_ref": str(study_root / "paper"),
                    "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
                },
                "verdict": {
                    "overall_verdict": "blocked",
                    "primary_claim_status": "supported",
                    "summary": "Core science is closed; remaining work is finalize-stage package hardening.",
                    "stop_loss_pressure": "none",
                },
                "quality_assessment": {
                    "clinical_significance": {
                        "status": "ready",
                        "summary": "Clinical framing and result surface are already reviewable.",
                        "evidence_refs": [str(gate_report_path)],
                    },
                    "evidence_strength": {
                        "status": "ready",
                        "summary": "Core evidence is already closed; remaining issues are downstream-only.",
                        "evidence_refs": [str(gate_report_path)],
                    },
                    "novelty_positioning": {
                        "status": "ready",
                        "summary": "Contribution boundaries are already frozen in the charter and manuscript lane.",
                        "evidence_refs": [str(charter_path)],
                    },
                    "human_review_readiness": {
                        "status": "partial",
                        "summary": "Current package still needs one more finalize pass before human audit.",
                        "evidence_refs": [str(gate_report_path)],
                    },
                },
                "gaps": [
                    {
                        "gap_id": "gap-001",
                        "gap_type": "delivery",
                        "severity": "optional",
                        "summary": "Only submission bundle alignment remains.",
                        "evidence_refs": [str(gate_report_path)],
                    }
                ],
                "recommended_actions": [
                    {
                        "action_id": "action-003",
                        "action_type": "route_back_same_line",
                        "priority": "now",
                        "reason": "Return to finalize for last-mile bundle stabilization.",
                        "route_target": "finalize",
                        "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                        "route_rationale": (
                            "The paper itself is ready for human review and only finalize-level cleanup remains."
                        ),
                        "evidence_refs": [str(gate_report_path)],
                        "requires_controller_decision": True,
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(
        runtime_escalation_path,
        json.dumps(
            {
                "schema_version": 1,
                "record_id": (
                    f"runtime-escalation::{study_id}::{quest_id}::"
                    "publishability_gate_blocked::2026-04-05T05:58:00+00:00"
                ),
                "study_id": study_id,
                "quest_id": quest_id,
                "emitted_at": "2026-04-05T05:58:00+00:00",
                "trigger": {"trigger_id": "publishability_gate_blocked", "source": "publication_gate"},
                "scope": "quest",
                "severity": "study",
                "reason": "publishability_gate_blocked",
                "recommended_actions": ["return_to_controller", "review_publishability_gate"],
                "evidence_refs": [str(gate_report_path)],
                "runtime_context_refs": {
                    "launch_report_path": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
                },
                "summary_ref": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
                "artifact_path": str(runtime_escalation_path),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(
        gate_report_path,
        json.dumps(
            {
                "schema_version": 1,
                "gate_kind": "publishability_control",
                "generated_at": "2026-04-05T06:05:00+00:00",
                "quest_id": quest_id,
                "status": "blocked",
                "allow_write": False,
                "recommended_action": "complete_bundle_stage",
                "latest_gate_path": str(gate_report_path),
                "supervisor_phase": "bundle_stage_blocked",
                "current_required_action": "complete_bundle_stage",
                "controller_stage_note": "bundle-stage blockers are now on the critical path for this paper line",
                "blockers": ["missing_submission_minimal"],
                "medical_publication_surface_named_blockers": ["submission_hardening_incomplete"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )

    summary_module.materialize_evaluation_summary_artifacts(
        study_root=study_root,
        runtime_escalation_ref=str(runtime_escalation_path),
        publishability_gate_report_ref=gate_report_path,
    )


@pytest.fixture(autouse=True)
def _patch_runtime_sidecars(monkeypatch):
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    transport = _managed_runtime_transport(module)
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
        transport,
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
        transport,
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
        transport,
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


def test_prepare_runtime_overlay_passes_profile_repo_root_to_overlay_installer(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "001-risk"
    calls: dict[str, dict[str, object]] = {}

    monkeypatch.setattr(
        module.overlay_installer,
        "ensure_medical_overlay",
        lambda **kwargs: calls.setdefault("ensure", kwargs)
        or {"selected_action": "noop", "post_status": {"all_targets_ready": True}},
    )
    monkeypatch.setattr(
        module.overlay_installer,
        "materialize_runtime_medical_overlay",
        lambda **kwargs: calls.setdefault("materialize", kwargs)
        or {"materialized_surface_count": 1, "surfaces": []},
    )
    monkeypatch.setattr(
        module.overlay_installer,
        "audit_runtime_medical_overlay",
        lambda **kwargs: calls.setdefault("audit", kwargs) or {"all_roots_ready": True, "surface_count": 1, "surfaces": []},
    )

    module._prepare_runtime_overlay(profile=profile, quest_root=quest_root)

    assert calls["ensure"]["med_deepscientist_repo_root"] == profile.med_deepscientist_repo_root
    assert calls["materialize"]["med_deepscientist_repo_root"] == profile.med_deepscientist_repo_root
    assert calls["audit"]["med_deepscientist_repo_root"] == profile.med_deepscientist_repo_root


def test_ensure_study_runtime_creates_and_starts_new_quest(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    transport = _managed_runtime_transport(module)
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

    monkeypatch.setattr(transport, "create_quest", fake_create_quest)
    monkeypatch.setattr(
        transport,
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
    transport = _managed_runtime_transport(module)
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
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
    monkeypatch.setattr(decision_module.publication_gate_controller, "build_gate_state", lambda quest_root: object())
    monkeypatch.setattr(
        decision_module.publication_gate_controller,
        "build_gate_report",
        lambda state: {
            "status": "clear",
            "supervisor_phase": "bundle_stage_ready",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": False,
            "current_required_action": "continue_bundle_stage",
            "deferred_downstream_actions": [],
            "controller_stage_note": "bundle-stage work is unlocked and can proceed on the critical path",
        },
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

    monkeypatch.setattr(transport, "create_quest", fake_create_quest)
    monkeypatch.setattr(transport, "resume_quest", fake_resume_quest)

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "create_and_start"
    assert seen["create_runtime_root"] == protocol_runtime_root
    assert seen["resume_runtime_root"] == protocol_runtime_root


def test_ensure_study_runtime_resume_flow_uses_protocol_quest_root_not_status_string(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    transport = _managed_runtime_transport(module)
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
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
        transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: {"ok": True, "status": "running"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "resume", result
    assert seen["overlay_quest_root"] == protocol_quest_root
    assert "hydration_quest_root" not in seen

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


def test_study_runtime_status_resumes_stopped_user_stop_auto_continuation_with_pending_messages(
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
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "stopped",
                "continuation_policy": "auto",
                "continuation_anchor": "write",
                "continuation_reason": "decision:decision-continue-001",
                "stop_reason": "user_stop",
                "active_interaction_id": "progress-001",
                "pending_user_message_count": 9,
            },
            ensure_ascii=False,
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

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_waiting_on_invalid_blocking"
    assert result["quest_status"] == "stopped"
    assert result["continuation_state"]["continuation_policy"] == "auto"
    assert result["continuation_state"]["continuation_reason"] == "decision:decision-continue-001"


def test_ensure_study_runtime_auto_resumes_stopped_user_stop_auto_continuation_with_pending_messages(
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
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "stopped",
                "continuation_policy": "auto",
                "continuation_anchor": "write",
                "continuation_reason": "decision:decision-continue-001",
                "stop_reason": "user_stop",
                "active_interaction_id": "progress-001",
                "pending_user_message_count": 9,
            },
            ensure_ascii=False,
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
    resumed: dict[str, object] = {}
    monkeypatch.setattr(
        module,
        "_resume_quest",
        lambda **kwargs: resumed.update(kwargs) or {"ok": True, "status": "running"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_waiting_on_invalid_blocking"
    assert result["quest_status"] == "running"
    assert resumed["source"] == "medautosci-test"
    assert resumed["runtime_root"] == profile.med_deepscientist_runtime_root
    assert resumed["quest_id"] == "001-risk"


def test_study_runtime_status_auto_resumes_controller_stopped_submission_hardening_with_pending_message(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
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
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "stopped",
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "decision:decision-hardening-001",
                "stop_reason": "controller_stop:codex-medical-publication-surface",
                "active_interaction_id": "progress-hardening-001",
                "pending_user_message_count": 1,
            },
            ensure_ascii=False,
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
    monkeypatch.setattr(decision_module.publication_gate_controller, "build_gate_state", lambda quest_root: object())
    monkeypatch.setattr(
        decision_module.publication_gate_controller,
        "build_gate_report",
        lambda state: {
            "status": "blocked",
            "supervisor_phase": "bundle_stage_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "current_required_action": "complete_bundle_stage",
            "bundle_tasks_downstream_only": False,
            "deferred_downstream_actions": [],
            "controller_stage_note": "submission hardening is on the critical path",
            "blockers": ["medical_publication_surface_blocked", "submission_hardening_incomplete"],
            "medical_publication_surface_named_blockers": ["submission_hardening_incomplete"],
            "medical_publication_surface_route_back_recommendation": "return_to_finalize",
        },
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "resume", result
    assert result["reason"] == "quest_waiting_on_invalid_blocking"
    assert result["quest_status"] == "stopped"
