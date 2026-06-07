from __future__ import annotations

import json
from pathlib import Path


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def opl_execution_authorization(*, study_id: str, action_type: str) -> dict[str, str]:
    return {
        "owner": "one-person-lab",
        "provider_attempt_ref": f"opl://stage-attempts/{study_id}/{action_type}",
        "stage_attempt_id": f"stage-attempt::{study_id}::{action_type}",
        "attempt_lease_ref": f"opl://stage-attempts/{study_id}/{action_type}/leases/current",
        "attempt_lease_status": "active",
        "execution_authorization_decision_ref": (
            f"opl://stage-attempts/{study_id}/{action_type}/execution-authorizations/current"
        ),
    }


def owner_route(*, study_id: str, action_type: str, owner: str) -> dict[str, object]:
    return {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": f"quest-{study_id}",
        "truth_epoch": f"truth-epoch::{study_id}::{action_type}",
        "runtime_health_epoch": f"runtime-health-epoch::{study_id}::{action_type}",
        "work_unit_fingerprint": f"work-unit::{study_id}::{action_type}",
        "failure_signature": action_type,
        "trace_id": f"owner-route-trace::{study_id}::{action_type}",
        "route_epoch": f"truth-epoch::{study_id}::{action_type}",
        "source_fingerprint": f"truth-source::{study_id}::{action_type}",
        "current_owner": "mas_controller",
        "next_owner": owner,
        "owner_reason": action_type,
        "active_run_id": None,
        "allowed_actions": [action_type],
        "blocked_actions": [
            item
            for item in (
                "publication_gate_specificity_required",
                "current_package_freshness_required",
                "artifact_display_surface_materialization_required",
                "return_to_ai_reviewer_workflow",
                "canonical_paper_inputs_rehydrate_required",
            )
            if item != action_type
        ],
        "idempotency_key": f"owner-route::{study_id}::{action_type}::{owner}",
    }


def dispatch(
    *,
    study_id: str,
    action_type: str,
    owner: str,
    required_output_surface: str,
    owner_route: dict[str, object] | None = None,
) -> dict[str, object]:
    route = owner_route or globals()["owner_route"](
        study_id=study_id,
        action_type=action_type,
        owner=owner,
    )
    authorization = opl_execution_authorization(study_id=study_id, action_type=action_type)
    return {
        "surface": "default_executor_dispatch_request",
        "schema_version": 1,
        "executor_kind": "codex_cli_default",
        "executor_name": "Codex CLI",
        "executor_mode": "autonomous_agent_loop",
        "chat_completion_only_executor_forbidden": True,
        "dispatch_status": "ready",
        "study_id": study_id,
        "quest_id": f"quest-{study_id}",
        "action_type": action_type,
        "action_id": f"dispatch::{study_id}::{action_type}",
        "next_executable_owner": owner,
        "required_output_surface": required_output_surface,
        "owner_route": route,
        "opl_execution_authorization": dict(authorization),
        "prompt_contract": {
            "study_id": study_id,
            "quest_id": f"quest-{study_id}",
            "action_type": action_type,
            "next_executable_owner": owner,
            "required_output_surface": required_output_surface,
            "owner_route": route,
            "opl_execution_authorization": dict(authorization),
            "idempotency_key": route["idempotency_key"],
            "prompt_budget": {"max_prompt_tokens": 6000},
            "compact_evidence_packet_ref": f"artifacts/supervision/compact_evidence_packets/{action_type}.json",
            "do_not_repeat": True,
            "repeat_suppression_key": route["work_unit_fingerprint"],
            "forbidden_surfaces": [
                "paper/**",
                "manuscript/**",
                "current_package/**",
                "paper/current_package/**",
                "manuscript/current_package/**",
                "src/med_autoscience/platform/**",
                "src/med_autoscience/runtime_transport/**",
            ],
            "allowed_write_surfaces": ["artifacts/supervision/**"],
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "manual_study_patch_allowed": False,
            "medical_claim_authoring_allowed": False,
        },
    }


def write_scan_latest(profile, study_id: str, owner_route: dict[str, object]) -> None:
    write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "owner_route": owner_route}],
        },
    )


def write_current_dispatch(path: Path, profile, dispatch: dict[str, object]) -> None:
    write_json(path, dispatch)
    write_scan_latest(profile, str(dispatch["study_id"]), dict(dispatch["owner_route"]))
    write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatches": [
                {
                    **dispatch,
                    "refs": {"dispatch_path": str(path)},
                }
            ],
        },
    )
