from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def authorization_dispatches(
    *,
    study_id: str,
    action_types: Iterable[str],
    supported_action_types: Iterable[str],
    forbidden_surfaces: Iterable[str],
    schema_version: int,
) -> list[dict[str, Any]]:
    supported = tuple(supported_action_types)
    forbidden = list(forbidden_surfaces)
    dispatches: list[dict[str, Any]] = []
    for action_type in action_types:
        if action_type not in supported:
            continue
        dispatches.append(
            {
                "surface": "default_executor_dispatch_request",
                "schema_version": schema_version,
                "executor_kind": "codex_cli_default",
                "executor_name": "Codex CLI",
                "executor_mode": "autonomous_agent_loop",
                "chat_completion_only_executor_forbidden": True,
                "dispatch_status": "ready",
                "study_id": study_id,
                "quest_id": study_id,
                "action_type": action_type,
                "action_id": f"managed-runtime::{study_id}::{action_type}",
                "next_executable_owner": "managed_runtime",
                "required_output_surface": _required_output_surface_for_action(action_type),
                "refs": {"dispatch_path": "<managed-runtime-controller-authorization>"},
                "owner_route": _placeholder_owner_route(
                    study_id=study_id,
                    action_type=action_type,
                    supported_action_types=supported,
                ),
                "prompt_contract": _placeholder_prompt_contract(
                    study_id=study_id,
                    action_type=action_type,
                    supported_action_types=supported,
                    forbidden_surfaces=forbidden,
                ),
            }
        )
    return dispatches


def _placeholder_owner_route(
    *,
    study_id: str,
    action_type: str,
    supported_action_types: Iterable[str],
) -> dict[str, Any]:
    return {
        "surface": "runtime_supervisor_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": study_id,
        "truth_epoch": f"managed-runtime::{study_id}::{action_type}",
        "runtime_health_epoch": None,
        "work_unit_fingerprint": f"managed-runtime::{study_id}::{action_type}",
        "failure_signature": action_type,
        "route_epoch": f"managed-runtime::{study_id}::{action_type}",
        "source_fingerprint": f"managed-runtime::{study_id}::{action_type}",
        "current_owner": "managed_runtime",
        "next_owner": "managed_runtime",
        "owner_reason": action_type,
        "allowed_actions": [action_type],
        "blocked_actions": [item for item in supported_action_types if item != action_type],
        "idempotency_key": f"managed-runtime::{study_id}::{action_type}",
    }


def _placeholder_prompt_contract(
    *,
    study_id: str,
    action_type: str,
    supported_action_types: Iterable[str],
    forbidden_surfaces: Iterable[str],
) -> dict[str, Any]:
    route = _placeholder_owner_route(
        study_id=study_id,
        action_type=action_type,
        supported_action_types=supported_action_types,
    )
    return {
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": action_type,
        "next_executable_owner": "managed_runtime",
        "required_output_surface": _required_output_surface_for_action(action_type),
        "owner_route": route,
        "idempotency_key": route["idempotency_key"],
        "prompt_budget": {"max_prompt_tokens": 6000},
        "compact_evidence_packet_ref": f"artifacts/supervision/compact_evidence_packets/{action_type}.json",
        "do_not_repeat": True,
        "repeat_suppression_key": route["work_unit_fingerprint"],
        "forbidden_surfaces": list(forbidden_surfaces),
        "allowed_write_surfaces": ["artifacts/supervision/**"],
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
    }


def _required_output_surface_for_action(action_type: str) -> str | None:
    return {
        "runtime_platform_repair": "artifacts/supervision/consumer/default_executor_execution/latest.json",
        "publication_gate_specificity_required": "artifacts/controller/publication_gate_specificity/latest.json",
        "current_package_freshness_required": "artifacts/controller/current_package_freshness/latest.json",
        "artifact_display_surface_materialization_required": "paper/display_registry.json",
        "return_to_ai_reviewer_workflow": "artifacts/publication_eval/latest.json",
        "canonical_paper_inputs_rehydrate_required": "paper/medical_manuscript_blueprint_source.json",
    }.get(action_type)


__all__ = ["authorization_dispatches"]
