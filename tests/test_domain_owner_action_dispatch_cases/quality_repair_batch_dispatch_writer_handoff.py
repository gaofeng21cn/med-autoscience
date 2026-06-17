from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def _opl_transition_readback(study_id: str, action_type: str = "run_quality_repair_batch") -> dict[str, object]:
    fingerprint = f"domain-transition::{study_id}::{action_type}"
    work_unit_id = action_type
    route_key = f"provider-admission::{study_id}::{fingerprint}"
    return {
        "surface_kind": "opl_domain_progress_transition_result",
        "runtime_owner": "one-person-lab",
        "runtime_kind": "DomainProgressTransitionRuntime",
        "transition_kind": "StartProviderAttempt",
        "outcome_kind": "provider_admission_pending",
        "event_id": f"dpte::{study_id}::{action_type}",
        "outbox_item_id": f"dpto::{study_id}::{action_type}",
        "stage_run_identity": {
            "stage_run_id": f"stage-run::{study_id}::{action_type}",
            "stage_run_identity_ref": f"stage-run-identity::{study_id}::{action_type}",
            "observed_generation": fingerprint,
        },
        "identity": {
            "study_id": study_id,
            "quest_id": study_id,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "route_identity_key": route_key,
            "attempt_idempotency_key": route_key,
        },
        "causality": {
            "mas_transition_request_idempotency_key": route_key,
            "source_generation": fingerprint,
            "expected_version": fingerprint,
            "derived_from_request": True,
        },
        "authority_boundary": {
            "runtime_owner": "one-person-lab",
            "domain_state_owner": "med-autoscience",
            "mas_can_authorize_provider_admission": False,
            "mas_can_create_opl_outbox_record": False,
            "mas_can_create_opl_event": False,
            "mas_can_create_opl_stage_run": False,
            "provider_completion_is_domain_completion": False,
        },
        "exactly_one_outcome": {
            "selected": "provider_admission_pending",
            "allowed": [
                "provider_admission_pending",
                "running_provider_attempt",
                "owner_receipt_ref",
                "typed_blocker_ref",
                "human_gate_ref",
                "route_back_evidence_ref",
            ],
        },
        "projection_metadata": {
            "authority": False,
            "projection_owner": "one-person-lab",
            "consumer": "med-autoscience",
            "observed_generation": fingerprint,
        },
    }


def test_execute_dispatch_wraps_materialized_story_surface_bridge_as_controller_context(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    quest_root = profile.runtime_root / f"quest-{study_id}"
    original_work_unit_id = "repair_current_manuscript_publication_surface_after_ai_reviewer_recheck"
    materialized_work_unit_id = "dm002_current_publication_hardening_after_current_ai_reviewer_eval"
    runtime_route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    runtime_route.update(
        {
            "truth_epoch": "truth-event-000022",
            "route_epoch": "truth-event-000022",
            "runtime_health_epoch": "runtime-health-event-006239",
            "source_fingerprint": "truth-snapshot::dm002-current",
            "failure_signature": "quest_waiting_opl_runtime_owner_route",
            "owner_reason": "quest_waiting_opl_runtime_owner_route",
            "work_unit_fingerprint": f"domain-transition::route_back_same_line::{original_work_unit_id}",
            "idempotency_key": "owner-route::dm002::runtime-handoff",
            "source_refs": {
                "study_truth_epoch": "truth-event-000022",
                "runtime_health_epoch": "runtime-health-event-006239",
                "work_unit_id": original_work_unit_id,
                "work_unit_fingerprint": f"domain-transition::route_back_same_line::{original_work_unit_id}",
                "blocked_reason": "quest_waiting_opl_runtime_owner_route",
            },
        }
    )
    route = dict(runtime_route)
    route.update(
        {
            "failure_signature": "manuscript_story_surface_delta_missing",
            "owner_reason": "manuscript_story_surface_delta_missing",
            "idempotency_key": "owner-route::dm002::story-surface-materialized",
            "source_refs": {
                **runtime_route["source_refs"],
                "materialized_work_unit_id": materialized_work_unit_id,
                "bridge_authority": "domain_action_request_materializer_story_surface_bridge",
                "bridged_from_owner_reason": "quest_waiting_opl_runtime_owner_route",
                "bridged_from_idempotency_key": runtime_route["idempotency_key"],
                "blocked_reason": "manuscript_story_surface_delta_missing",
                "source_eval_id": "publication-eval::dm002::current",
            },
        }
    )
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface=(
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        owner_route=route,
    )
    dispatch_payload["dispatch_authority"] = "quality_repair_batch_writer_handoff"
    dispatch_payload["source_action"] = {
        "surface": "quality_repair_batch",
        "blocked_reason": "manuscript_story_surface_delta_missing",
        "source_eval_id": "publication-eval::dm002::current",
        "repair_execution_evidence_ref": str(
            study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
        ),
    }
    dispatch_payload["medical_claim_authoring_allowed"] = True
    dispatch_payload["prompt_contract"].update(
        {
            "medical_claim_authoring_allowed": True,
            "allowed_write_surfaces": [
                "paper/draft.md",
                "paper/build/review_manuscript.md",
                "paper/claim_evidence_map.json",
                "paper/evidence_ledger.json",
                "paper/review/**",
            ],
            "forbidden_surfaces": [
                "manuscript/**",
                "current_package/**",
                "paper/current_package/**",
                "manuscript/current_package/**",
                "src/med_autoscience/platform/**",
                "artifacts/publication_eval/latest.json",
                "artifacts/controller_decisions/latest.json",
            ],
        }
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    _write_json(dispatch_path, dispatch_payload)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": f"quest-{study_id}",
                    "owner_route": runtime_route,
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "quest_id": f"quest-{study_id}",
                            "action_type": "run_quality_repair_batch",
                            "owner": "write",
                            "request_owner": "write",
                            "reason": "quest_waiting_opl_runtime_owner_route",
                            "next_work_unit": original_work_unit_id,
                            "controller_work_unit_id": original_work_unit_id,
                            "owner_route": runtime_route,
                        }
                    ],
                }
            ],
        },
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "owner_callable_adapters": [{**dispatch_payload, "refs": {"dispatch_path": str(dispatch_path)}}],
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "quest_id": f"quest-{study_id}",
            "quest_root": str(quest_root),
        },
    )
    called: dict[str, object] = {}

    def fake_run_quality_repair_batch(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        return {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"),
        }

    monkeypatch.setattr(
        module.action_execution.quality_repair.quality_repair_batch,
        "run_quality_repair_batch",
        fake_run_quality_repair_batch,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 0, result
    assert result["handoff_ready_count"] == 0
    assert result["blocked_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "opl_execution_authorization_required"
    assert execution["typed_blocker"]["blocker_id"] == "opl_execution_authorization_required"
    assert execution["will_start_llm"] is False
    assert execution["owner_callable_surface"] is None
    assert execution["provider_attempt_or_lease_required"] is False
    assert execution["provider_admission_requires_opl_runtime_result"] is True
    handoff_route = execution["writer_worker_handoff"]["owner_route"]
    assert handoff_route["source_refs"]["work_unit_id"] == original_work_unit_id
    assert handoff_route["source_refs"]["materialized_work_unit_id"] == materialized_work_unit_id
    assert handoff_route["source_refs"]["source_eval_id"] == "publication-eval::dm002::current"
    assert called == {}


def test_execute_dispatch_picks_quality_repair_writer_handoff_without_request_packet(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    quest_root = profile.runtime_root / f"quest-{study_id}"
    quest_root.mkdir(parents=True, exist_ok=True)
    route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    route["failure_signature"] = "manuscript_story_surface_delta_missing"
    route["owner_reason"] = "manuscript_story_surface_delta_missing"
    route["work_unit_fingerprint"] = "medical-prose-routeback::write::sha256-dm003"
    route["idempotency_key"] = "owner-route::dm003::write::story-surface"
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface=(
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        owner_route=route,
    )
    dispatch_payload["dispatch_authority"] = "quality_repair_batch_writer_handoff"
    dispatch_payload["source_action"] = {
        "surface": "quality_repair_batch",
        "blocked_reason": "manuscript_story_surface_delta_missing",
        "source_eval_id": "publication-eval::dm003::medical-prose-routeback",
        "repair_execution_evidence_ref": str(
            study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
        ),
    }
    dispatch_payload["source_action"]["next_work_unit"] = {
        "unit_id": "medical_prose_write_repair",
        "lane": "write",
    }
    dispatch_payload["prompt_contract"]["next_work_unit"] = {
        "unit_id": "medical_prose_write_repair",
        "lane": "write",
    }
    dispatch_payload["medical_claim_authoring_allowed"] = True
    dispatch_payload["prompt_contract"]["medical_claim_authoring_allowed"] = True
    dispatch_payload["prompt_contract"]["allowed_write_surfaces"] = [
        "paper/draft.md",
        "paper/build/review_manuscript.md",
        "paper/claim_evidence_map.json",
        "paper/evidence_ledger.json",
        "paper/review/**",
    ]
    dispatch_payload["prompt_contract"]["forbidden_surfaces"] = [
        "manuscript/**",
        "current_package/**",
        "paper/current_package/**",
        "manuscript/current_package/**",
        "src/med_autoscience/platform/**",
        "artifacts/publication_eval/latest.json",
        "artifacts/controller_decisions/latest.json",
    ]
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    dispatch_payload["refs"] = {"dispatch_path": str(dispatch_path)}
    _write_json(dispatch_path, dispatch_payload)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "owner_route": route}],
        },
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "owner_callable_adapters": [{**dispatch_payload, "refs": {"dispatch_path": str(dispatch_path)}}],
        },
    )
    request_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "requests"
        / "quality_repair_batch"
        / "latest.json"
    )
    assert not request_path.exists()
    monkeypatch.setattr(module.action_execution, "quest_root_from_status", lambda *_: quest_root)
    def fake_run_quality_repair_batch(**kwargs) -> dict[str, object]:
        raise AssertionError("writer handoff dispatch must not re-enter quality_repair_batch owner callable")

    monkeypatch.setattr(
        module.action_execution.quality_repair.quality_repair_batch,
        "run_quality_repair_batch",
        fake_run_quality_repair_batch,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 0
    assert result["handoff_ready_count"] == 0
    assert result["blocked_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "opl_execution_authorization_required"
    assert execution["owner_route_current"] is True
    assert execution["will_start_llm"] is False
    assert execution["owner_callable_surface"] is None
    assert execution["provider_attempt_or_lease_required"] is False
    assert execution["writer_worker_handoff"]["source_action"]["next_work_unit"]["unit_id"] == "medical_prose_write_repair"


def test_default_dispatch_picks_quality_repair_writer_handoff_from_owner_request(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    quest_root.mkdir(parents=True, exist_ok=True)
    current_route = _owner_route(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
    )
    current_route.update(
        {
            "truth_epoch": "truth-event-000035-d649b1535a6bc2aa",
            "route_epoch": "truth-event-000035-d649b1535a6bc2aa",
            "runtime_health_epoch": "runtime-health-event-006487-7e921dd42b7003d0",
            "source_fingerprint": "truth-snapshot::86ef8e2d33582504debb97a2",
            "work_unit_fingerprint": "truth-snapshot::86ef8e2d33582504debb97a2",
            "idempotency_key": (
                "owner-route::002-dm-china-us-mortality-attribution::"
                "truth-event-000035-d649b1535a6bc2aa::ai_reviewer::domain_transition_ai_reviewer_re_eval"
            ),
            "source_refs": {
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_fingerprint": "truth-snapshot::86ef8e2d33582504debb97a2",
                "source_eval_id": (
                    "publication-eval::002-dm-china-us-mortality-attribution::"
                    "ai-reviewer-current-inputs::20260601T130009Z"
                ),
            },
        }
    )
    writer_route = dict(current_route)
    writer_route.update(
        {
            "next_owner": "write",
            "owner_reason": "manuscript_story_surface_delta_missing",
            "failure_signature": "manuscript_story_surface_delta_missing",
            "allowed_actions": ["run_quality_repair_batch"],
            "idempotency_key": (
                "owner-route::002-dm-china-us-mortality-attribution::"
                "truth-snapshot::86ef8e2d33582504debb97a2::write::"
                "manuscript_story_surface_delta_missing::run_quality_repair_batch"
            ),
            "source_refs": {
                **current_route["source_refs"],
                "blocked_reason": "manuscript_story_surface_delta_missing",
                "materialized_from_action_type": "return_to_ai_reviewer_workflow",
                "materialized_work_unit_id": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                "bridge_authority": "domain_action_request_materializer_story_surface_bridge",
                "bridged_from_owner_reason": "domain_transition_ai_reviewer_re_eval",
                "bridged_from_idempotency_key": current_route["idempotency_key"],
            },
        }
    )
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface=(
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        owner_route=writer_route,
    )
    dispatch_payload["dispatch_authority"] = "quality_repair_batch_writer_handoff"
    dispatch_payload["source_action"] = {
        "surface": "quality_repair_batch",
        "blocked_reason": "manuscript_story_surface_delta_missing",
        "next_work_unit": {
            "unit_id": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
            "lane": "write",
        },
    }
    dispatch_payload["prompt_contract"]["next_work_unit"] = {
        "unit_id": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
        "lane": "write",
    }
    dispatch_payload["medical_claim_authoring_allowed"] = True
    dispatch_payload["prompt_contract"]["medical_claim_authoring_allowed"] = True
    dispatch_payload["prompt_contract"]["allowed_write_surfaces"] = [
        "paper/draft.md",
        "paper/build/review_manuscript.md",
        "paper/claim_evidence_map.json",
        "paper/evidence_ledger.json",
        "paper/review/**",
    ]
    dispatch_payload["prompt_contract"]["forbidden_surfaces"] = [
        "manuscript/**",
        "current_package/**",
        "paper/current_package/**",
        "manuscript/current_package/**",
        "src/med_autoscience/platform/**",
        "artifacts/publication_eval/latest.json",
        "artifacts/controller_decisions/latest.json",
    ]
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    dispatch_payload["refs"] = {"dispatch_path": str(dispatch_path)}
    _write_json(dispatch_path, dispatch_payload)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": {
                        **current_route,
                        "idempotency_key": "owner-route::002::stale-scan-route",
                    },
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "quality_repair_batch" / "latest.json",
        {
            "surface": "supervisor_request_handoff_packet",
            "request_kind": "run_quality_repair_batch",
            "action_type": "run_quality_repair_batch",
            "status": "requested",
            "study_id": study_id,
            "request_owner": "write",
            "next_executable_owner": "write",
            "owner_route": writer_route,
        },
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "owner_callable_adapters": [{**dispatch_payload, "refs": {"dispatch_path": str(dispatch_path)}}],
        },
    )
    monkeypatch.setattr(module.action_execution, "quest_root_from_status", lambda *_: quest_root)
    monkeypatch.setattr(
        module.action_execution.quality_repair.quality_repair_batch,
        "run_quality_repair_batch",
        lambda **_: (_ for _ in ()).throw(
            AssertionError("writer handoff dispatch must not re-enter quality_repair_batch owner callable")
        ),
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(),
        mode="developer_apply_safe",
        apply=True,
    )

    summary = result["per_study_execution_summary"][0]
    assert summary["selected_dispatch_count"] == 1
    assert summary["zero_dispatch_reason"] is None
    assert result["executed_count"] == 0
    assert result["handoff_ready_count"] == 0
    assert result["blocked_count"] == 1
    execution = result["executions"][0]
    assert execution["action_type"] == "run_quality_repair_batch"
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "opl_execution_authorization_required"
    assert execution["owner_route_basis"] == "owner_request"
    assert execution["will_start_llm"] is False
    assert execution["owner_callable_surface"] is None
    assert execution["provider_attempt_or_lease_required"] is False


def test_execute_dispatch_consumes_quality_repair_writer_handoff_as_stage_attempt(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    quest_root = profile.runtime_root / f"quest-{study_id}"
    quest_root.mkdir(parents=True, exist_ok=True)
    route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    route["failure_signature"] = "manuscript_story_surface_delta_missing"
    route["owner_reason"] = "manuscript_story_surface_delta_missing"
    route["work_unit_fingerprint"] = "medical-prose-routeback::write::sha256-dm003"
    route["idempotency_key"] = "owner-route::dm003::write::story-surface"
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface=(
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        owner_route=route,
    )
    dispatch_payload["opl_domain_progress_transition_result"] = _opl_transition_readback(study_id)
    dispatch_payload["dispatch_authority"] = "quality_repair_batch_writer_handoff"
    dispatch_payload["source_action"] = {
        "surface": "quality_repair_batch",
        "blocked_reason": "manuscript_story_surface_delta_missing",
        "source_eval_id": "publication-eval::dm003::medical-prose-routeback",
        "repair_execution_evidence_ref": str(
            study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
        ),
    }
    dispatch_payload["source_action"]["next_work_unit"] = {
        "unit_id": "medical_prose_write_repair",
        "lane": "write",
    }
    dispatch_payload["prompt_contract"]["next_work_unit"] = {
        "unit_id": "medical_prose_write_repair",
        "lane": "write",
    }
    dispatch_payload["medical_claim_authoring_allowed"] = True
    dispatch_payload["prompt_contract"]["medical_claim_authoring_allowed"] = True
    dispatch_payload["prompt_contract"]["allowed_write_surfaces"] = [
        "paper/draft.md",
        "paper/build/review_manuscript.md",
        "paper/claim_evidence_map.json",
        "paper/evidence_ledger.json",
        "paper/review/**",
    ]
    dispatch_payload["prompt_contract"]["forbidden_surfaces"] = [
        "manuscript/**",
        "current_package/**",
        "paper/current_package/**",
        "manuscript/current_package/**",
        "src/med_autoscience/platform/**",
        "artifacts/publication_eval/latest.json",
        "artifacts/controller_decisions/latest.json",
    ]
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    dispatch_payload["refs"] = {"dispatch_path": str(dispatch_path)}
    _write_json(dispatch_path, dispatch_payload)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "owner_route": route}],
        },
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "owner_callable_adapters": [{**dispatch_payload, "refs": {"dispatch_path": str(dispatch_path)}}],
        },
    )
    monkeypatch.setattr(module.action_execution, "quest_root_from_status", lambda *_: quest_root)
    def fake_run_quality_repair_batch(**kwargs) -> dict[str, object]:
        raise AssertionError("writer handoff dispatch must not re-enter quality_repair_batch owner callable")

    monkeypatch.setattr(
        module.action_execution.quality_repair.quality_repair_batch,
        "run_quality_repair_batch",
        fake_run_quality_repair_batch,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 0
    assert result["handoff_ready_count"] == 1
    assert result["blocked_count"] == 0
    assert result["codex_dispatch_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "handoff_ready"
    assert execution["blocked_reason"] is None
    assert execution["owner_route_current"] is True
    assert execution["action_class"] == "codex_worker_dispatch"
    assert execution["will_start_llm"] is True
    assert execution["owner_callable_surface"] == "opl_default_executor.stage_attempt"
    assert execution["writer_worker_handoff"]["dispatch_authority"] == "quality_repair_batch_writer_handoff"
    assert execution["writer_worker_handoff"]["next_executable_owner"] == "write"
    assert execution["required_next_owner"] == "write"
    assert execution["stage_attempt_admission"]["status"] == "requested"
    assert execution["stage_attempt_admission"]["owner"] == "one-person-lab"
    assert execution["stage_attempt_admission"]["domain_completion_authorized"] is False
    assert execution["paper_stage_log"]["surface_kind"] == "mas_paper_facing_stage_log_summary"
    assert execution["paper_stage_log"]["stage_name"] == "medical_prose_write_repair"
    assert execution["paper_stage_log"]["outcome"] == "handoff_ready"
    assert execution["paper_stage_log"]["remaining_blockers"] == []
    assert execution["paper_stage_log"]["paper_work_done"] == [
        "Prepared writer owner handoff for a canonical manuscript story-surface delta or typed blocker."
    ]


def test_quality_repair_writer_handoff_rejects_package_write_surface(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    route["failure_signature"] = "manuscript_story_surface_delta_missing"
    route["owner_reason"] = "manuscript_story_surface_delta_missing"
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface=(
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        owner_route=route,
    )
    dispatch_payload["dispatch_authority"] = "quality_repair_batch_writer_handoff"
    dispatch_payload["source_action"] = {
        "surface": "quality_repair_batch",
        "blocked_reason": "manuscript_story_surface_delta_missing",
    }
    dispatch_payload["medical_claim_authoring_allowed"] = True
    dispatch_payload["prompt_contract"]["medical_claim_authoring_allowed"] = True
    dispatch_payload["prompt_contract"]["allowed_write_surfaces"] = [
        "paper/draft.md",
        "paper/current_package/proof.json",
    ]
    dispatch_payload["prompt_contract"]["forbidden_surfaces"] = [
        "manuscript/**",
        "current_package/**",
        "paper/current_package/**",
        "manuscript/current_package/**",
        "src/med_autoscience/platform/**",
        "artifacts/publication_eval/latest.json",
        "artifacts/controller_decisions/latest.json",
    ]
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    dispatch_payload["refs"] = {"dispatch_path": str(dispatch_path)}
    _write_json(dispatch_path, dispatch_payload)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "owner_route": route}],
        },
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 0
    assert result["blocked_count"] == 0
    assert result["execution_count"] == 0
    summary = result["per_study_execution_summary"][0]
    assert summary["selected_dispatch_count"] == 0
    assert summary["zero_dispatch_reason"] == "no_selected_dispatch_for_requested_action_types"


def test_quality_repair_writer_handoff_retries_after_guard_block(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    quest_root = profile.runtime_root / f"quest-{study_id}"
    quest_root.mkdir(parents=True, exist_ok=True)
    route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    route["failure_signature"] = "manuscript_story_surface_delta_missing"
    route["owner_reason"] = "manuscript_story_surface_delta_missing"
    route["work_unit_fingerprint"] = "medical-prose-routeback::write::sha256-dm003"
    route["idempotency_key"] = "owner-route::dm003::write::story-surface"
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface=(
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        owner_route=route,
    )
    dispatch_payload["dispatch_authority"] = "quality_repair_batch_writer_handoff"
    dispatch_payload["source_action"] = {
        "surface": "quality_repair_batch",
        "blocked_reason": "manuscript_story_surface_delta_missing",
    }
    dispatch_payload["medical_claim_authoring_allowed"] = True
    dispatch_payload["prompt_contract"]["medical_claim_authoring_allowed"] = True
    dispatch_payload["prompt_contract"]["allowed_write_surfaces"] = [
        "paper/draft.md",
        "paper/build/review_manuscript.md",
        "paper/claim_evidence_map.json",
        "paper/evidence_ledger.json",
        "paper/review/**",
    ]
    dispatch_payload["prompt_contract"]["forbidden_surfaces"] = [
        "manuscript/**",
        "current_package/**",
        "paper/current_package/**",
        "manuscript/current_package/**",
        "src/med_autoscience/platform/**",
        "artifacts/publication_eval/latest.json",
        "artifacts/controller_decisions/latest.json",
    ]
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    dispatch_payload["refs"] = {"dispatch_path": str(dispatch_path)}
    _write_json(dispatch_path, dispatch_payload)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "owner_route": route}],
        },
    )
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "study_id": study_id,
                    "quest_id": f"quest-{study_id}",
                    "action_type": "run_quality_repair_batch",
                    "execution_status": "blocked",
                    "blocked_reason": "medical_claim_authoring_allowed_guard_missing",
                    "dispatch_contract_valid": False,
                    "dispatch_contract_blocked_reason": "medical_claim_authoring_allowed_guard_missing",
                    "owner_route": route,
                    "prompt_contract": dispatch_payload["prompt_contract"],
                    "repeat_suppression_key": "medical-prose-routeback::write::sha256-dm003",
                }
            ],
        },
    )
    monkeypatch.setattr(module.action_execution, "quest_root_from_status", lambda *_: quest_root)
    monkeypatch.setattr(
        module.action_execution.quality_repair.quality_repair_batch,
        "run_quality_repair_batch",
        lambda **_: (_ for _ in ()).throw(
            AssertionError("writer handoff dispatch must not re-enter quality_repair_batch owner callable")
        ),
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 0
    assert result["handoff_ready_count"] == 0
    assert result["repeat_suppressed_count"] == 0
    assert result["execution_count"] == 0
    summary = result["per_study_execution_summary"][0]
    assert summary["selected_dispatch_count"] == 0
    assert summary["zero_dispatch_reason"] == "no_selected_dispatch_for_requested_action_types"
