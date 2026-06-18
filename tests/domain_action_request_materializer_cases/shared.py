from __future__ import annotations

import importlib
import json
from pathlib import Path

from med_autoscience.controllers import stage_native_next_action_admission


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def disable_progress_projection(monkeypatch) -> None:
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setattr(progress_module, "read_study_progress", lambda **_: {})


def legacy_request_task_refs(result: dict[str, object]) -> list[dict[str, object]]:
    diagnostics = result["legacy_request_task_diagnostics"]
    assert isinstance(diagnostics, dict)
    assert diagnostics["surface"] == "legacy_request_task_diagnostics"
    assert diagnostics["canonical_transition_request_surface"] == "domain_progress_transition_requests"
    assert diagnostics["diagnostic_only"] is True
    assert diagnostics["diagnostic_ref_only"] is True
    assert diagnostics["counts_authority"] is False
    assert diagnostics["readiness_authority"] is False
    assert diagnostics["can_create_success_outcome"] is False
    assert diagnostics["body_authority"] is False
    assert diagnostics["legacy_payload_scope"] == "identity_refs_only"
    assert "request_tasks" not in result
    assert result["request_tasks_alias_retired"] is True
    assert result["request_tasks_replacement"] == (
        "legacy_request_task_diagnostics.legacy_request_task_refs"
    )
    return diagnostics["legacy_request_task_refs"]


def stage_native_admission_fields(
    *,
    action_type: str = "run_quality_repair_batch",
    current_stage_id: str = "08-publication_package_handoff",
    source_surface: str = "artifacts/reports/medical_publication_surface/latest.json",
) -> dict[str, object]:
    return {
        "stage_transition_authority_boundary": (
            stage_native_next_action_admission.stage_transition_authority_boundary()
        ),
        "current_work_unit_binding": (
            stage_native_next_action_admission.build_current_work_unit_binding(
                action_type=action_type,
                current_stage_id=current_stage_id,
                source_surface=source_surface,
            )
        ),
    }


def owner_route(
    *,
    study_id: str,
    quest_id: str,
    next_owner: str,
    owner_reason: str,
    allowed_actions: list[str],
) -> dict[str, object]:
    source_fingerprint = f"truth-source::{study_id}::{owner_reason}"
    truth_epoch = f"truth-epoch::{study_id}"
    runtime_health_epoch = f"runtime-health::{study_id}::{owner_reason}"
    return {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": quest_id,
        "truth_epoch": truth_epoch,
        "route_epoch": truth_epoch,
        "runtime_health_epoch": runtime_health_epoch,
        "work_unit_fingerprint": source_fingerprint,
        "source_fingerprint": source_fingerprint,
        "current_owner": "mas_controller",
        "next_owner": next_owner,
        "owner_reason": owner_reason,
        "active_run_id": None,
        "allowed_actions": allowed_actions,
        "blocked_actions": [],
        "idempotency_key": f"owner-route::{study_id}::{owner_reason}",
        "source_refs": {
            "study_truth_epoch": truth_epoch,
            "runtime_health_epoch": runtime_health_epoch,
            "work_unit_id": owner_reason,
            "work_unit_fingerprint": source_fingerprint,
            "owner_route_currentness_basis": {
                "runtime_health_epoch": runtime_health_epoch,
                "truth_epoch": truth_epoch,
                "work_unit_fingerprint": source_fingerprint,
                "work_unit_id": owner_reason,
            },
        },
    }


def unsupported_domain_action(study_id: str, quest_id: str) -> dict[str, object]:
    action_type = "unsupported_supervisor_action"
    route = owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="external_observer",
        owner_reason=action_type,
        allowed_actions=[action_type],
    )
    return {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": action_type,
        "authority": "observability_only",
        "reason": action_type,
        "action_id": f"supervisor-action::{study_id}::{action_type}",
        "owner_route": route,
        "handoff_packet": {
            "packet_type": "external_supervisor_handoff",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": quest_id,
            "action_type": action_type,
            "reason": action_type,
            "authority": "observability_only",
            "recommended_owner": "external_observer",
            "owner_route": route,
        },
    }
