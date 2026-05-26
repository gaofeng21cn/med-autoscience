from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_quality_repair_writer_handoff_bridges_runtime_owner_route_currentness(tmp_path: Path) -> None:
    writer_handoff = importlib.import_module(
        "med_autoscience.controllers.quality_repair_batch_parts.writer_handoff"
    )
    attempt_protocol = importlib.import_module("med_autoscience.runtime_control.owner_route_attempt_protocol")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    source_eval_id = "publication-eval::dm003::medical-prose-routeback"
    current_route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    current_route.update(
        {
            "truth_epoch": source_eval_id,
            "runtime_health_epoch": "runtime-health-dm003-write-route",
            "work_unit_fingerprint": "medical-prose-routeback::write::dm003",
            "source_fingerprint": "truth-source::dm003::medical-prose",
            "failure_signature": "quest_waiting_opl_runtime_owner_route",
            "owner_reason": "quest_waiting_opl_runtime_owner_route",
            "source_refs": {
                "source_eval_id": source_eval_id,
                "work_unit_id": "medical_prose_write_repair",
                "runtime_health_epoch": "runtime-health-dm003-write-route",
                "study_truth_epoch": source_eval_id,
                "blocked_reason": "quest_waiting_opl_runtime_owner_route",
            },
        }
    )

    handoff = writer_handoff.build_writer_worker_handoff(
        profile=profile,
        study_id=study_id,
        quest_id=f"quest-{study_id}",
        schema_version=1,
        source_eval_id=source_eval_id,
        source_eval_artifact_path="artifacts/publication_eval/latest.json",
        source_summary_artifact_path="artifacts/eval_hygiene/evaluation_summary/latest.json",
        repair_execution_evidence_path=(
            profile.studies_root
            / study_id
            / "artifacts/controller/repair_execution_evidence/latest.json"
        ),
        blocked_repair_reason="manuscript_story_surface_delta_missing",
        authority_route_context={
            "current_owner_route": current_route,
            "controller_route_context": {
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "medical-prose-routeback::write::dm003",
            },
        },
    )

    envelope = attempt_protocol.default_executor_attempt_envelope(dispatch=handoff)

    assert envelope["dispatchable"] is True
    assert envelope["owner_reason_contract"]["reason"] == "manuscript_story_surface_delta_missing"
    assert envelope["owner_route_currentness_basis"] == {
        "source_eval_id": source_eval_id,
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "medical-prose-routeback::write::dm003",
        "truth_epoch": source_eval_id,
        "runtime_health_epoch": "runtime-health-dm003-write-route",
        "owner_reason": "manuscript_story_surface_delta_missing",
    }
    assert handoff["owner_route"]["source_refs"]["bridged_from_owner_reason"] == (
        "quest_waiting_opl_runtime_owner_route"
    )
    assert handoff["owner_route"]["source_refs"]["blocked_reason"] == (
        "manuscript_story_surface_delta_missing"
    )


def test_execute_dispatch_accepts_request_bound_writer_handoff_bridged_from_runtime_route(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    quest_root.mkdir(parents=True)
    work_unit_id = "materialize_current_ai_reviewer_record_through_mas_owner_surface"
    work_unit_fingerprint = f"domain-transition::route_back_same_line::{work_unit_id}"
    runtime_route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    runtime_route.update(
        {
            "truth_epoch": "truth-event-000022",
            "route_epoch": "truth-event-000022",
            "runtime_health_epoch": "runtime-health-event-006244",
            "work_unit_fingerprint": work_unit_fingerprint,
            "source_fingerprint": "truth-snapshot::dm002-current",
            "failure_signature": "quest_waiting_opl_runtime_owner_route",
            "owner_reason": "quest_waiting_opl_runtime_owner_route",
            "idempotency_key": "owner-route::dm002::runtime-handoff",
            "source_refs": {
                "study_truth_epoch": "truth-event-000022",
                "runtime_health_epoch": "runtime-health-event-006244",
                "source_eval_id": "publication-eval::dm002::current",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "blocked_reason": "quest_waiting_opl_runtime_owner_route",
            },
        }
    )
    bridged_route = dict(runtime_route)
    bridged_route.update(
        {
            "current_owner": "quality_repair_batch",
            "failure_signature": "manuscript_story_surface_delta_missing",
            "owner_reason": "manuscript_story_surface_delta_missing",
            "route_epoch": "quality-repair-writer-handoff::dm002::current",
            "idempotency_key": "quality-repair-writer-handoff::dm002::current",
            "source_refs": {
                **runtime_route["source_refs"],
                "blocked_reason": "manuscript_story_surface_delta_missing",
                "bridged_from_owner_reason": "quest_waiting_opl_runtime_owner_route",
                "bridged_from_idempotency_key": runtime_route["idempotency_key"],
                "bridge_authority": "quality_repair_batch_writer_handoff_currentness_bridge",
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
        owner_route=bridged_route,
    )
    dispatch_payload.update(
        {
            "dispatch_authority": "quality_repair_batch_writer_handoff",
            "typed_blocker_if_unresolved": "manuscript_story_surface_delta_missing",
            "medical_claim_authoring_allowed": True,
            "source_action": {
                "surface": "quality_repair_batch",
                "blocked_reason": "manuscript_story_surface_delta_missing",
                "source_eval_id": "publication-eval::dm002::current",
                "repair_execution_evidence_ref": str(
                    study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
                ),
                "next_work_unit": work_unit_id,
            },
        }
    )
    dispatch_payload["prompt_contract"].update(
        {
            "owner_route": bridged_route,
            "idempotency_key": bridged_route["idempotency_key"],
            "repeat_suppression_key": work_unit_fingerprint,
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
            "manual_study_patch_allowed": False,
            "medical_claim_authoring_allowed": True,
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
    stale_request_route = dict(bridged_route)
    stale_request_route.update(
        {
            "truth_epoch": "truth-event-000015",
            "route_epoch": "truth-event-000015",
            "runtime_health_epoch": "runtime-health-event-006238",
            "work_unit_fingerprint": "dm002-old-display-table-package-repair",
            "source_fingerprint": "truth-snapshot::dm002-old",
            "idempotency_key": "owner-route::dm002::old-writer-handoff",
            "source_refs": {
                **bridged_route["source_refs"],
                "study_truth_epoch": "truth-event-000015",
                "runtime_health_epoch": "runtime-health-event-006238",
                "work_unit_id": "dm002_same_line_display_table_package_repair",
                "work_unit_fingerprint": "dm002-old-display-table-package-repair",
            },
        }
    )
    request = {
        "request_kind": "run_quality_repair_batch",
        "status": "requested",
        "study_id": study_id,
        "quest_id": quest_id,
        "request_owner": "write",
        "expected_owner": "write",
        "next_executable_owner": "write",
        "action_type": "run_quality_repair_batch",
        "owner_route": stale_request_route,
        "source_action": dispatch_payload["source_action"],
        "refs": {
            "source_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            "repair_execution_evidence_path": str(
                study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
            ),
        },
        "dispatch_authority": "quality_repair_batch_writer_handoff",
    }
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "quality_repair_batch" / "latest.json",
        request,
    )
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "owner_route": runtime_route,
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "quest_id": quest_id,
                            "action_type": "run_quality_repair_batch",
                            "owner": "write",
                            "request_owner": "write",
                            "reason": "quest_waiting_opl_runtime_owner_route",
                            "next_work_unit": work_unit_id,
                            "controller_work_unit_id": work_unit_id,
                            "owner_route": runtime_route,
                        }
                    ],
                }
            ],
        },
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatches": [{**dispatch_payload, "refs": {"dispatch_path": str(dispatch_path)}}],
        },
    )
    monkeypatch.setattr(
        module.action_execution.quality_repair,
        "execute_quality_repair_batch",
        lambda **_: {
            "execution_status": "handoff_ready",
            "blocked_reason": None,
            "owner_callable_surface": "quality_repair_batch.run_quality_repair_batch",
            "owner_result": {"status": "handoff_ready"},
        },
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["blocked_count"] == 0
    assert execution["execution_status"] == "handoff_ready"
    assert execution["owner_route_current"] is True
    assert execution["owner_route_basis"] == "bridged_writer_handoff"


def test_execute_dispatch_accepts_materialized_story_surface_route_bridged_from_runtime_route(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    quest_root.mkdir(parents=True)
    work_unit_id = "materialize_current_ai_reviewer_record_through_mas_owner_surface"
    work_unit_fingerprint = f"domain-transition::route_back_same_line::{work_unit_id}"
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
            "work_unit_fingerprint": work_unit_fingerprint,
            "source_fingerprint": "truth-snapshot::dm002-current",
            "failure_signature": "quest_waiting_opl_runtime_owner_route",
            "owner_reason": "quest_waiting_opl_runtime_owner_route",
            "idempotency_key": "owner-route::dm002::runtime-handoff",
            "source_refs": {
                "study_truth_epoch": "truth-event-000022",
                "runtime_health_epoch": "runtime-health-event-006239",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "blocked_reason": "quest_waiting_opl_runtime_owner_route",
                "owner_route_currentness_basis": {
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": work_unit_fingerprint,
                    "truth_epoch": "truth-event-000022",
                    "runtime_health_epoch": "runtime-health-event-006239",
                    "owner_reason": "quest_waiting_opl_runtime_owner_route",
                },
            },
        }
    )
    bridged_route = dict(runtime_route)
    bridged_route.update(
        {
            "failure_signature": "manuscript_story_surface_delta_missing",
            "owner_reason": "manuscript_story_surface_delta_missing",
            "idempotency_key": "owner-route::dm002::story-surface-delta",
            "source_refs": {
                **runtime_route["source_refs"],
                "blocked_reason": "manuscript_story_surface_delta_missing",
                "bridged_from_owner_reason": "quest_waiting_opl_runtime_owner_route",
                "bridged_from_idempotency_key": runtime_route["idempotency_key"],
                "bridge_authority": "domain_action_request_materializer_story_surface_bridge",
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
        owner_route=bridged_route,
    )
    dispatch_payload.update(
        {
            "dispatch_authority": "consumer_default_executor_dispatch",
            "source_action": {
                "action_type": "run_quality_repair_batch",
                "reason": "manuscript_story_surface_delta_missing",
                "route_target": "write",
                "next_work_unit": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                "controller_work_unit_id": work_unit_id,
                "executable_work_unit": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
            },
        }
    )
    dispatch_payload["prompt_contract"].update(
        {
            "owner_route": bridged_route,
            "idempotency_key": bridged_route["idempotency_key"],
            "repeat_suppression_key": work_unit_fingerprint,
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
                    "quest_id": quest_id,
                    "owner_route": runtime_route,
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "quest_id": quest_id,
                            "action_type": "run_quality_repair_batch",
                            "owner": "write",
                            "request_owner": "write",
                            "reason": "quest_waiting_opl_runtime_owner_route",
                            "next_work_unit": work_unit_id,
                            "controller_work_unit_id": work_unit_id,
                            "owner_route": runtime_route,
                        }
                    ],
                }
            ],
        },
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatches": [{**dispatch_payload, "refs": {"dispatch_path": str(dispatch_path)}}],
        },
    )
    monkeypatch.setattr(
        module.action_execution.quality_repair,
        "execute_quality_repair_batch",
        lambda **_: {
            "execution_status": "handoff_ready",
            "blocked_reason": None,
            "owner_callable_surface": "quality_repair_batch.run_quality_repair_batch",
            "owner_result": {"status": "handoff_ready"},
        },
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["blocked_count"] == 0
    assert execution["execution_status"] == "handoff_ready"
    assert execution["owner_route_current"] is True
    assert execution["owner_route_basis"] == "bridged_writer_handoff"


def test_execute_dispatch_rejects_materialized_story_surface_route_with_stale_bridge_idempotency(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    (profile.runtime_root / quest_id).mkdir(parents=True)
    work_unit_id = "materialize_current_ai_reviewer_record_through_mas_owner_surface"
    work_unit_fingerprint = f"domain-transition::route_back_same_line::{work_unit_id}"
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
            "work_unit_fingerprint": work_unit_fingerprint,
            "source_fingerprint": "truth-snapshot::dm002-current",
            "failure_signature": "quest_waiting_opl_runtime_owner_route",
            "owner_reason": "quest_waiting_opl_runtime_owner_route",
            "idempotency_key": "owner-route::dm002::runtime-handoff-current",
            "source_refs": {
                "study_truth_epoch": "truth-event-000022",
                "runtime_health_epoch": "runtime-health-event-006239",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "blocked_reason": "quest_waiting_opl_runtime_owner_route",
            },
        }
    )
    bridged_route = dict(runtime_route)
    bridged_route.update(
        {
            "failure_signature": "manuscript_story_surface_delta_missing",
            "owner_reason": "manuscript_story_surface_delta_missing",
            "idempotency_key": "owner-route::dm002::story-surface-delta",
            "source_refs": {
                **runtime_route["source_refs"],
                "blocked_reason": "manuscript_story_surface_delta_missing",
                "bridged_from_owner_reason": "quest_waiting_opl_runtime_owner_route",
                "bridged_from_idempotency_key": "owner-route::dm002::runtime-handoff-stale",
                "bridge_authority": "domain_action_request_materializer_story_surface_bridge",
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
        owner_route=bridged_route,
    )
    dispatch_payload.update(
        {
            "dispatch_authority": "consumer_default_executor_dispatch",
            "source_action": {
                "action_type": "run_quality_repair_batch",
                "reason": "manuscript_story_surface_delta_missing",
                "route_target": "write",
                "next_work_unit": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                "controller_work_unit_id": work_unit_id,
                "executable_work_unit": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
            },
        }
    )
    dispatch_payload["prompt_contract"].update(
        {
            "owner_route": bridged_route,
            "idempotency_key": bridged_route["idempotency_key"],
            "repeat_suppression_key": work_unit_fingerprint,
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
                    "quest_id": quest_id,
                    "owner_route": runtime_route,
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "quest_id": quest_id,
                            "action_type": "run_quality_repair_batch",
                            "owner": "write",
                            "request_owner": "write",
                            "reason": "quest_waiting_opl_runtime_owner_route",
                            "next_work_unit": work_unit_id,
                            "controller_work_unit_id": work_unit_id,
                            "owner_route": runtime_route,
                        }
                    ],
                }
            ],
        },
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatches": [{**dispatch_payload, "refs": {"dispatch_path": str(dispatch_path)}}],
        },
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["blocked_count"] == 1
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "owner_route_stale"
    assert execution["owner_route_basis"] == "scan_latest"


def test_execute_dispatch_accepts_materialized_story_surface_route_bridged_from_current_ai_reviewer_route(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    (profile.runtime_root / quest_id).mkdir(parents=True)
    work_unit_id = "materialize_current_ai_reviewer_record_through_mas_owner_surface"
    materialized_work_unit_id = "dm002_current_publication_hardening_after_current_ai_reviewer_eval"
    work_unit_fingerprint = "truth-snapshot::dm002-current-ai-reviewer"
    current_route = _owner_route(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
    )
    current_route.update(
        {
            "truth_epoch": "truth-event-000022",
            "route_epoch": "truth-event-000022",
            "runtime_health_epoch": "runtime-health-event-006244",
            "work_unit_fingerprint": work_unit_fingerprint,
            "source_fingerprint": "truth-snapshot::dm002-current",
            "failure_signature": "ai_reviewer_assessment_required",
            "owner_reason": "ai_reviewer_assessment_required",
            "idempotency_key": "owner-route::dm002::current-ai-reviewer",
            "source_refs": {
                "study_truth_epoch": "truth-event-000022",
                "runtime_health_epoch": "runtime-health-event-006244",
                "source_eval_id": "publication-eval::dm002::current",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "blocked_reason": "ai_reviewer_assessment_required",
            },
        }
    )
    bridged_route = dict(current_route)
    bridged_route.update(
        {
            "failure_signature": "manuscript_story_surface_delta_missing",
            "owner_reason": "manuscript_story_surface_delta_missing",
            "next_owner": "write",
            "allowed_actions": ["run_quality_repair_batch"],
            "blocked_actions": ["return_to_ai_reviewer_workflow"],
            "idempotency_key": "owner-route::dm002::story-surface-after-ai-reviewer",
            "source_refs": {
                **current_route["source_refs"],
                "blocked_reason": "manuscript_story_surface_delta_missing",
                "materialized_work_unit_id": materialized_work_unit_id,
                "materialized_from_action_type": "return_to_ai_reviewer_workflow",
                "bridged_from_owner_reason": "ai_reviewer_assessment_required",
                "bridged_from_idempotency_key": current_route["idempotency_key"],
                "bridge_authority": "domain_action_request_materializer_story_surface_bridge",
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
        owner_route=bridged_route,
    )
    dispatch_payload.update(
        {
            "dispatch_authority": "consumer_default_executor_dispatch",
            "source_action": {
                "action_type": "run_quality_repair_batch",
                "reason": "manuscript_story_surface_delta_missing",
                "route_target": "write",
                "next_work_unit": materialized_work_unit_id,
                "controller_work_unit_id": work_unit_id,
                "executable_work_unit": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "materialization_decision": "story_surface_delta_or_typed_blocker_required",
            },
        }
    )
    dispatch_payload["prompt_contract"].update(
        {
            "owner_route": bridged_route,
            "idempotency_key": bridged_route["idempotency_key"],
            "repeat_suppression_key": work_unit_fingerprint,
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
                    "quest_id": quest_id,
                    "owner_route": current_route,
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "quest_id": quest_id,
                            "action_type": "return_to_ai_reviewer_workflow",
                            "owner": "ai_reviewer",
                            "request_owner": "ai_reviewer",
                            "reason": "ai_reviewer_assessment_required",
                            "next_work_unit": work_unit_id,
                            "controller_work_unit_id": work_unit_id,
                            "owner_route": current_route,
                        }
                    ],
                }
            ],
        },
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatches": [{**dispatch_payload, "refs": {"dispatch_path": str(dispatch_path)}}],
        },
    )
    monkeypatch.setattr(
        module.action_execution.quality_repair,
        "execute_quality_repair_batch",
        lambda **_: {
            "execution_status": "handoff_ready",
            "blocked_reason": None,
            "owner_callable_surface": "quality_repair_batch.run_quality_repair_batch",
            "owner_result": {"status": "handoff_ready"},
        },
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["blocked_count"] == 0
    assert execution["execution_status"] == "handoff_ready"
    assert execution["owner_route_current"] is True
    assert execution["owner_route_basis"] == "bridged_writer_handoff"
