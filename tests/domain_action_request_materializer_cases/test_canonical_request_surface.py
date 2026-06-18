from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _owner_route(
    *,
    study_id: str,
    quest_id: str,
    next_owner: str,
    owner_reason: str,
    allowed_actions: list[str],
) -> dict[str, object]:
    return {
        "surface": "domain_route_owner_route",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "route_epoch": f"truth-epoch::{study_id}",
        "source_fingerprint": f"truth-source::{study_id}::{owner_reason}",
        "current_owner": "mas_controller",
        "next_owner": next_owner,
        "owner_reason": owner_reason,
        "active_run_id": None,
        "allowed_actions": allowed_actions,
        "blocked_actions": [],
        "idempotency_key": f"owner-route::{study_id}::{owner_reason}",
    }


def test_materialize_domain_action_requests_writes_quality_repair_request_to_canonical_requests_surface(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dpcc")
    route = _owner_route(
        study_id=study_id,
        quest_id="quest-dpcc",
        next_owner="write",
        owner_reason="manuscript_story_surface_delta_missing",
        allowed_actions=["run_quality_repair_batch"],
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": "quest-dpcc",
                    "action_type": "run_quality_repair_batch",
                    "authority": "observability_only",
                    "owner": "write",
                    "recommended_owner": "write",
                    "reason": "manuscript_story_surface_delta_missing",
                    "required_output_surface": (
                        "canonical manuscript story-surface delta or "
                        "typed blocker:manuscript_story_surface_delta_missing"
                    ),
                    "owner_route": route,
                    "handoff_packet": {
                        "request_kind": "run_quality_repair_batch",
                        "authority": "observability_only",
                        "request_owner": "write",
                        "owner_route": route,
                    },
                },
            ],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    canonical_request_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "requests"
        / "quality_repair_batch"
        / "latest.json"
    )
    legacy_consumer_request_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "run_quality_repair_batch.json"
    )
    assert "request_tasks" not in result
    assert result["request_tasks_alias_retired"] is True
    assert result["request_tasks_replacement"] == (
        "legacy_request_task_diagnostics.legacy_request_task_refs"
    )
    assert result["request_task_counts_authority"] is False
    assert result["request_task_readiness_authority"] is False
    legacy_request_tasks = result["legacy_request_task_diagnostics"]
    assert legacy_request_tasks["surface"] == "legacy_request_task_diagnostics"
    assert legacy_request_tasks["canonical_transition_request_surface"] == (
        "domain_progress_transition_requests"
    )
    assert legacy_request_tasks["diagnostic_only"] is True
    assert legacy_request_tasks["counts_authority"] is False
    assert legacy_request_tasks["readiness_authority"] is False
    task = legacy_request_tasks["legacy_request_task_refs"][0]
    assert task["dispatch_status"] == "transition_request_pending"
    assert task["blocked_reason"] == "opl_execution_authorization_required"
    assert task["provider_admission_pending"] is False
    assert task["provider_admission_requires_opl_runtime_result"] is True
    assert task["mas_local_request_packet_persistence"] == "forbidden"
    assert task["opl_transition_runtime_required_for_durable_carrier"] is True
    assert task["request_packet_ref"] == "artifacts/supervision/requests/quality_repair_batch/latest.json"
    assert task["refs"]["request_packet_path"] == str(canonical_request_path)
    assert not canonical_request_path.exists()
    assert not legacy_consumer_request_path.exists()
    assert result["apply_writes_domain_intent_projection_only"] is True
    assert result["written_files"] == []


def test_canonical_transition_request_projection_carries_dispatcher_boundary_fields() -> None:
    projection = importlib.import_module(
        "med_autoscience.controllers.domain_action_request_materializer_parts.transition_request_projection"
    )
    dispatch = {
        "surface": "default_executor_dispatch_request",
        "dispatch_status": "ready",
        "study_id": "study-a",
        "quest_id": "quest-a",
        "action_type": "run_quality_repair_batch",
        "executor_kind": "codex_cli_default",
        "refs": {
            "dispatch_path": (
                "studies/study-a/artifacts/supervision/consumer/"
                "default_executor_dispatches/run_quality_repair_batch.json"
            )
        },
        "prompt_contract": {
            "study_id": "study-a",
            "action_type": "run_quality_repair_batch",
            "prompt_budget": {},
            "compact_evidence_packet_ref": "packet://evidence",
            "do_not_repeat": True,
            "repeat_suppression_key": "repeat-key",
            "forbidden_surfaces": ["paper/**"],
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "manual_study_patch_allowed": False,
            "medical_claim_authoring_allowed": False,
        },
    }

    request = projection.domain_progress_transition_request_projection([dispatch])[0]

    assert request["surface"] == "mas_domain_progress_transition_request_projection"
    assert request["legacy_surface"] == "default_executor_dispatch_request"
    assert request["projection_only"] is True
    assert request["owner_callable_carrier_projection_only"] is True
    assert request["owner_callable_adapter_diagnostic_only"] is True
    assert request["owner_callable_adapter_readiness_authority"] is False
    assert request["owner_callable_adapter_can_create_success_outcome"] is False
    assert request["mas_private_attempt_loop_forbidden"] is True
    assert request["prompt_contract"] == dispatch["prompt_contract"]
    assert request["prompt_contract_ref"] == dispatch["prompt_contract"]
