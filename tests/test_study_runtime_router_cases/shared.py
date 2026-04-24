from __future__ import annotations

from dataclasses import replace
import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from ..study_runtime_test_helpers import (
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


def _write_native_runtime_event_for_status_test(*, quest_root: Path, quest_id: str, quest_status: str) -> dict[str, object]:
    artifact_path = quest_root / "artifacts" / "reports" / "runtime_events" / "latest.json"
    payload = {
        "schema_version": 1,
        "event_id": f"runtime-event::{quest_id}::{quest_status}::2026-04-11T00:00:00+00:00",
        "quest_id": quest_id,
        "emitted_at": "2026-04-11T00:00:00+00:00",
        "event_source": "daemon_app",
        "event_kind": "runtime_control_applied",
        "summary_ref": f"quest:{quest_id}:{quest_status}",
        "status_snapshot": {
            "quest_status": quest_status,
            "display_status": quest_status,
            "active_run_id": "run-native",
            "runtime_liveness_status": "live" if quest_status == "running" else "none",
            "worker_running": quest_status == "running",
            "stop_reason": None,
            "continuation_policy": "resume_allowed",
            "continuation_anchor": "decision",
            "continuation_reason": "native_runtime_truth",
            "pending_user_message_count": 0,
            "interaction_action": None,
            "interaction_requires_user_input": False,
            "active_interaction_id": None,
            "last_transition_at": "2026-04-11T00:00:00+00:00",
        },
        "outer_loop_input": {
            "quest_status": quest_status,
            "display_status": quest_status,
            "active_run_id": "run-native",
            "runtime_liveness_status": "live" if quest_status == "running" else "none",
            "worker_running": quest_status == "running",
            "stop_reason": None,
            "continuation_policy": "resume_allowed",
            "continuation_anchor": "decision",
            "continuation_reason": "native_runtime_truth",
            "pending_user_message_count": 0,
            "interaction_action": None,
            "interaction_requires_user_input": False,
            "active_interaction_id": None,
            "last_transition_at": "2026-04-11T00:00:00+00:00",
        },
        "artifact_path": str(artifact_path),
        "summary": f"native runtime event for {quest_status}",
    }
    write_text(
        artifact_path,
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
    )
    return payload


























































































