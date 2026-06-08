from __future__ import annotations

from pathlib import Path

from .shared import _write_json


def _owner_route(
    *,
    study_id: str,
    next_owner: str,
    owner_reason: str,
    action_type: str,
    work_unit_id: str,
    work_unit_fingerprint: str,
    runtime_health_epoch: str,
    blocked_actions: list[str],
) -> dict[str, object]:
    return {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": study_id,
        "truth_epoch": "truth-event-000024-daa5883571a64a07",
        "runtime_health_epoch": runtime_health_epoch,
        "work_unit_fingerprint": work_unit_fingerprint,
        "source_fingerprint": work_unit_fingerprint,
        "route_epoch": "truth-event-000024-daa5883571a64a07",
        "current_owner": "mas_controller",
        "next_owner": next_owner,
        "owner_reason": owner_reason,
        "allowed_actions": [action_type],
        "blocked_actions": blocked_actions,
        "source_refs": {
            "runtime_health_epoch": runtime_health_epoch,
            "study_truth_epoch": "truth-event-000024-daa5883571a64a07",
            "work_unit_id": work_unit_id,
            "blocked_reason": owner_reason,
        },
        "idempotency_key": f"owner-route::{study_id}::{work_unit_fingerprint}",
    }


def _write_dispatch(
    *,
    workspace_root: Path,
    study_id: str,
    filename: str,
    action_type: str,
    next_owner: str,
    dispatch_authority: str,
    owner_route: dict[str, object],
    generated_at: str,
    allowed_write_surfaces: list[str] | None = None,
) -> None:
    dispatch_path = (
        workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / filename
    )
    _write_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": action_type,
            "dispatch_status": "ready",
            "dispatch_authority": dispatch_authority,
            "next_executable_owner": next_owner,
            "executor_kind": "codex_cli_default",
            "consumer_mutation_scope": "executor_dispatch_request_only",
            "owner_route": owner_route,
            "prompt_contract": {
                "study_id": study_id,
                "quest_id": study_id,
                "action_type": action_type,
                "next_executable_owner": next_owner,
                "owner_route": owner_route,
                "allowed_write_surfaces": allowed_write_surfaces or ["paper/draft.md"],
                "forbidden_surfaces": [
                    "paper/current_package/**",
                    "manuscript/current_package/**",
                    "artifacts/publication_eval/latest.json",
                    "artifacts/controller_decisions/latest.json",
                ],
                "paper_package_mutation_allowed": False,
                "quality_gate_relaxation_allowed": False,
                "manual_study_patch_allowed": False,
                "medical_claim_authoring_allowed": False,
            },
            "refs": {
                "dispatch_path": str(dispatch_path),
                "source_eval_path": str(
                    workspace_root
                    / "studies"
                    / study_id
                    / "artifacts"
                    / "publication_eval"
                    / "latest.json"
                ),
            },
            "generated_at": generated_at,
        },
    )

