from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from tests.reviewer_os_fixture_helpers import current_manuscript_routeback_record
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


@pytest.mark.parametrize(
    "work_unit_id",
    (
        "materialize_current_ai_reviewer_record_through_mas_owner_surface",
        "repair_current_manuscript_publication_surface_after_ai_reviewer_recheck",
    ),
)
def test_ai_reviewer_story_surface_work_unit_bridges_runtime_route_to_story_surface_writer(
    monkeypatch,
    tmp_path: Path,
    work_unit_id: str,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    manuscript_path = study_root / "paper" / "draft.md"
    review_manuscript_path = study_root / "paper" / "build" / "review_manuscript.md"
    manuscript_text = "# Draft\n\nCurrent story still needs a canonical story-surface delta.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    review_manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    review_manuscript_path.write_text(manuscript_text, encoding="utf-8")
    eval_id = "publication-eval::002::quest::2026-05-26T08:30:00+00:00::ai-reviewer"
    record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260526T083000Z_publication_eval_record.json"
    )
    record_payload = current_manuscript_routeback_record(
        study_root=study_root,
        manuscript_path=manuscript_path,
        manuscript_text=manuscript_text,
        study_id=study_id,
        quest_id=quest_id,
        eval_id=eval_id,
        emitted_at="2026-05-26T08:30:00+00:00",
    )
    _write_json(record_path, record_payload)
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "schema_version": 1,
            "request_kind": "return_to_ai_reviewer_workflow",
            "study_id": study_id,
            "quest_id": quest_id,
            "request_owner": "ai_reviewer",
            "request_lifecycle": {"state": "assessment_written", "blocked_reason": None},
            "publication_eval_record_ref": str(record_path.resolve()),
            "ai_reviewer_record": record_payload,
        },
    )
    work_unit_fingerprint = f"domain-transition::route_back_same_line::{work_unit_id}"
    route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="write",
        owner_reason="quest_waiting_opl_runtime_owner_route",
        allowed_actions=["run_quality_repair_batch"],
    )
    route.update(
        {
            "schema_version": 2,
            "truth_epoch": "truth-event-000022",
            "route_epoch": "truth-event-000022",
            "source_fingerprint": "truth-snapshot::dm002-current",
            "runtime_health_epoch": "runtime-health-event-006239",
            "work_unit_fingerprint": work_unit_fingerprint,
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
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "quest_id": quest_id, "owner_route": route}],
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
                    "executable_work_unit": work_unit_id,
                    "work_unit_fingerprint": work_unit_fingerprint,
                    "required_output_surface": (
                        "canonical manuscript story-surface delta or "
                        "typed blocker:manuscript_story_surface_delta_missing"
                    ),
                    "owner_route": route,
                }
            ],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    request = result["request_tasks"][0]
    dispatch = result["default_executor_dispatches"][0]
    source_refs = dispatch["owner_route"]["source_refs"]
    assert request["action_type"] == "run_quality_repair_batch"
    assert request["request_owner"] == "write"
    assert request["reason"] == "manuscript_story_surface_delta_missing"
    assert dispatch["dispatch_status"] == "ready"
    assert dispatch["owner_route"]["owner_reason"] == "manuscript_story_surface_delta_missing"
    assert source_refs["bridge_authority"] == "domain_action_request_materializer_story_surface_bridge"
    assert source_refs["bridged_from_owner_reason"] == "quest_waiting_opl_runtime_owner_route"
    assert source_refs["bridged_from_idempotency_key"] == route["idempotency_key"]
    assert source_refs["work_unit_id"] == work_unit_id
    assert source_refs["materialized_work_unit_id"] == "dm002_current_publication_hardening_after_current_ai_reviewer_eval"
    assert dispatch["source_action"]["materialization_decision"] == "story_surface_delta_or_typed_blocker_required"


def test_ai_reviewer_record_production_work_unit_consumes_current_record_before_redrive(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    manuscript_path = study_root / "paper" / "draft.md"
    manuscript_text = "# Draft\n\nCurrent manuscript already has a current AI reviewer record.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    eval_id = "publication-eval::002::quest::2026-05-28T06:26:01+00:00::ai-reviewer"
    record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260528T062601Z_publication_eval_record.json"
    )
    record_payload = current_manuscript_routeback_record(
        study_root=study_root,
        manuscript_path=manuscript_path,
        manuscript_text=manuscript_text,
        study_id=study_id,
        quest_id=quest_id,
        eval_id=eval_id,
        emitted_at="2026-05-28T06:26:01+00:00",
    )
    _write_json(record_path, record_payload)
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "schema_version": 1,
            "request_kind": "return_to_ai_reviewer_workflow",
            "study_id": study_id,
            "quest_id": quest_id,
            "request_owner": "ai_reviewer",
            "request_lifecycle": {"state": "assessment_written", "blocked_reason": None},
            "publication_eval_record_ref": str(record_path.resolve()),
            "ai_reviewer_record": record_payload,
        },
    )
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
    work_unit_fingerprint = f"domain-transition::ai_reviewer_re_eval::{work_unit_id}"
    route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="ai_reviewer",
        owner_reason="domain_transition_ai_reviewer_re_eval",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )
    route.update(
        {
            "schema_version": 2,
            "truth_epoch": "truth-event-000024",
            "route_epoch": "truth-event-000024",
            "source_fingerprint": "truth-snapshot::dm002-ai-reviewer-current",
            "runtime_health_epoch": "runtime-health-event-006362",
            "work_unit_fingerprint": work_unit_fingerprint,
            "idempotency_key": "owner-route::dm002::ai-reviewer-record-production",
            "source_refs": {
                "study_truth_epoch": "truth-event-000024",
                "runtime_health_epoch": "runtime-health-event-006362",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "blocked_reason": "domain_transition_ai_reviewer_re_eval",
                "owner_route_currentness_basis": {
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": work_unit_fingerprint,
                    "truth_epoch": "truth-event-000024",
                    "runtime_health_epoch": "runtime-health-event-006362",
                    "owner_reason": "domain_transition_ai_reviewer_re_eval",
                },
            },
        }
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "quest_id": quest_id, "owner_route": route}],
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "owner": "ai_reviewer",
                    "request_owner": "ai_reviewer",
                    "reason": "domain_transition_ai_reviewer_re_eval",
                    "next_work_unit": work_unit_id,
                    "controller_work_unit_id": work_unit_id,
                    "executable_work_unit": work_unit_id,
                    "work_unit_fingerprint": work_unit_fingerprint,
                    "required_output_surface": "artifacts/publication_eval/latest.json",
                    "owner_route": route,
                }
            ],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    request = result["request_tasks"][0]
    dispatch = result["default_executor_dispatches"][0]
    source_refs = dispatch["owner_route"]["source_refs"]
    assert request["action_type"] == "run_quality_repair_batch"
    assert request["request_owner"] == "write"
    assert request["reason"] == "manuscript_story_surface_delta_missing"
    assert dispatch["action_type"] == "run_quality_repair_batch"
    assert dispatch["source_action"]["reviewer_record_ref"] == str(record_path.resolve())
    assert dispatch["source_action"]["materialization_decision"] == "story_surface_delta_or_typed_blocker_required"
    assert source_refs["bridge_authority"] == "domain_action_request_materializer_story_surface_bridge"
    assert source_refs["materialized_from_action_type"] == "return_to_ai_reviewer_workflow"
    assert source_refs["materialized_work_unit_id"] == "dm002_current_publication_hardening_after_current_ai_reviewer_eval"


def test_current_input_ai_reviewer_record_consumption_work_unit_materializes_to_story_surface_writer(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    manuscript_path = study_root / "paper" / "draft.md"
    manuscript_text = "# Draft\n\nCurrent DPCC manuscript requires journal prose repair.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    eval_id = "publication-eval::003::quest::2026-05-28T21:30:23+00:00::ai-reviewer-current-inputs"
    record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260528T213023Z_publication_eval_record.json"
    )
    record_payload = current_manuscript_routeback_record(
        study_root=study_root,
        manuscript_path=manuscript_path,
        manuscript_text=manuscript_text,
        study_id=study_id,
        quest_id=quest_id,
        eval_id=eval_id,
        emitted_at="2026-05-28T21:30:23+00:00",
    )
    record_payload["recommended_actions"][0].update(
        {
            "work_unit_fingerprint": (
                "dm003-current-input-ai-reviewer-record::write-review-consumption-pending::2026-05-28T21:30:23Z"
            ),
            "next_work_unit": {
                "unit_id": "consume_current_input_ai_reviewer_record",
                "lane": "review",
                "summary": "Consume this record-only AI reviewer response before routing write reconciliation.",
            },
            "blocking_work_units": [
                {
                    "unit_id": "consume_current_input_ai_reviewer_record",
                    "lane": "review",
                    "summary": "Consume the current-input record-only AI reviewer response.",
                },
                {
                    "unit_id": "current_manuscript_reporting_reconciliation",
                    "lane": "write",
                    "summary": "Reconcile manuscript reporting with current evidence.",
                },
            ],
        }
    )
    _write_json(record_path, record_payload)
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "schema_version": 1,
            "request_kind": "return_to_ai_reviewer_workflow",
            "study_id": study_id,
            "quest_id": quest_id,
            "request_owner": "ai_reviewer",
            "request_lifecycle": {"state": "assessment_written", "blocked_reason": None},
            "publication_eval_record_ref": str(record_path.resolve()),
            "ai_reviewer_record": record_payload,
        },
    )
    work_unit_id = "consume_current_input_ai_reviewer_record"
    work_unit_fingerprint = f"domain-transition::route_back_same_line::{work_unit_id}"
    route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="write",
        owner_reason="quest_waiting_opl_runtime_owner_route",
        allowed_actions=["run_quality_repair_batch"],
    )
    route.update(
        {
            "schema_version": 2,
            "truth_epoch": "truth-event-dm003-current-input-reviewer-record",
            "route_epoch": "truth-event-dm003-current-input-reviewer-record",
            "source_fingerprint": "truth-snapshot::dm003-current-input-reviewer-record",
            "runtime_health_epoch": "runtime-health-event-dm003-current-input-reviewer-record",
            "work_unit_fingerprint": work_unit_fingerprint,
            "idempotency_key": "owner-route::dm003::consume-current-input-ai-reviewer-record",
            "source_refs": {
                "study_truth_epoch": "truth-event-dm003-current-input-reviewer-record",
                "runtime_health_epoch": "runtime-health-event-dm003-current-input-reviewer-record",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "blocked_reason": "quest_waiting_opl_runtime_owner_route",
                "owner_route_currentness_basis": {
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": work_unit_fingerprint,
                    "truth_epoch": "truth-event-dm003-current-input-reviewer-record",
                    "runtime_health_epoch": "runtime-health-event-dm003-current-input-reviewer-record",
                    "owner_reason": "quest_waiting_opl_runtime_owner_route",
                },
            },
        }
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "quest_id": quest_id, "owner_route": route}],
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
                    "executable_work_unit": work_unit_id,
                    "work_unit_fingerprint": work_unit_fingerprint,
                    "required_output_surface": (
                        "canonical manuscript story-surface delta or "
                        "typed blocker:manuscript_story_surface_delta_missing"
                    ),
                    "owner_route": route,
                }
            ],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    request = result["request_tasks"][0]
    dispatch = result["default_executor_dispatches"][0]
    source_refs = dispatch["owner_route"]["source_refs"]
    assert request["action_type"] == "run_quality_repair_batch"
    assert request["request_owner"] == "write"
    assert request["reason"] == "manuscript_story_surface_delta_missing"
    assert request["source_action"]["next_work_unit"] == "medical_prose_write_repair"
    assert dispatch["action_type"] == "run_quality_repair_batch"
    assert dispatch["next_executable_owner"] == "write"
    assert dispatch["owner_route_attempt_envelope"]["work_unit_id"] == work_unit_id
    assert dispatch["source_action"]["reviewer_record_ref"] == str(record_path.resolve())
    assert dispatch["source_action"]["source_eval_id"] == eval_id
    assert dispatch["source_action"]["materialization_decision"] == "story_surface_delta_or_typed_blocker_required"
    assert source_refs["work_unit_id"] == work_unit_id
    assert source_refs["source_eval_id"] == eval_id
    assert source_refs["materialized_work_unit_id"] == "medical_prose_write_repair"
    assert source_refs["materialized_from_action_type"] == "run_quality_repair_batch"
    assert source_refs["bridged_from_owner_reason"] == "quest_waiting_opl_runtime_owner_route"
    assert source_refs["bridge_authority"] == "domain_action_request_materializer_story_surface_bridge"


def test_ai_reviewer_record_stale_after_current_inputs_keeps_ai_reviewer_production_route(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    manuscript_path = study_root / "paper" / "draft.md"
    evidence_path = study_root / "paper" / "evidence_ledger.json"
    claim_map_path = study_root / "paper" / "claim_evidence_map.json"
    manuscript_text = "# Draft\n\nCurrent manuscript has updated evidence inputs.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    _write_json(evidence_path, {"schema_version": 1, "updated": "current"})
    _write_json(claim_map_path, {"schema_version": 1, "updated": "current"})
    record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260528T153941Z_publication_eval_record.json"
    )
    record_payload = current_manuscript_routeback_record(
        study_root=study_root,
        manuscript_path=manuscript_path,
        manuscript_text=manuscript_text,
        study_id=study_id,
        quest_id=quest_id,
        eval_id="publication-eval::003::quest::2026-05-28T15:39:41+00:00::ai-reviewer",
        emitted_at="2026-05-28T15:39:41+00:00",
    )
    _write_json(record_path, record_payload)
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    required_currentness_refs = [str(evidence_path.resolve()), str(claim_map_path.resolve())]
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "schema_version": 1,
            "request_kind": "return_to_ai_reviewer_workflow",
            "study_id": study_id,
            "quest_id": quest_id,
            "request_owner": "ai_reviewer",
            "request_lifecycle": {
                "state": "requested",
                "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
                "stale_record_ref": str(record_path.resolve()),
                "required_currentness_refs": required_currentness_refs,
            },
            "input_contract": {
                "required_refs": {
                    "manuscript": {"path": str(manuscript_path.resolve()), "present": True, "valid": True},
                    "evidence_ledger": {"path": str(evidence_path.resolve()), "present": True, "valid": True},
                    "claim_evidence_map": {"path": str(claim_map_path.resolve()), "present": True, "valid": True},
                }
            },
            "publication_eval_record_ref": str(record_path.resolve()),
            "ai_reviewer_record": record_payload,
        },
    )
    route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="ai_reviewer",
        owner_reason="ai_reviewer_record_stale_after_current_inputs",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )
    route.update(
        {
            "schema_version": 2,
            "truth_epoch": "truth-event-000008",
            "route_epoch": "truth-event-000008",
            "source_fingerprint": "truth-snapshot::dm003-current-inputs",
            "runtime_health_epoch": "runtime-health-event-006160",
            "work_unit_fingerprint": f"domain-transition::ai_reviewer_re_eval::{work_unit_id}",
            "idempotency_key": "owner-route::dm003::ai-reviewer-record-stale-after-current-inputs",
            "source_refs": {
                "study_truth_epoch": "truth-event-000008",
                "runtime_health_epoch": "runtime-health-event-006160",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": f"domain-transition::ai_reviewer_re_eval::{work_unit_id}",
                "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
                "owner_route_currentness_basis": {
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": f"domain-transition::ai_reviewer_re_eval::{work_unit_id}",
                    "truth_epoch": "truth-event-000008",
                    "runtime_health_epoch": "runtime-health-event-006160",
                    "owner_reason": "ai_reviewer_record_stale_after_current_inputs",
                },
            },
        }
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "quest_id": quest_id, "owner_route": route}],
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "owner": "ai_reviewer",
                    "request_owner": "ai_reviewer",
                    "reason": "ai_reviewer_record_stale_after_current_inputs",
                    "next_work_unit": work_unit_id,
                    "controller_work_unit_id": work_unit_id,
                    "executable_work_unit": work_unit_id,
                    "work_unit_fingerprint": f"domain-transition::ai_reviewer_re_eval::{work_unit_id}",
                    "required_output_surface": "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
                    "required_currentness_refs": required_currentness_refs,
                    "stale_record_ref": str(record_path.resolve()),
                    "record_only_surface": True,
                    "publication_eval_latest_write_allowed": False,
                    "controller_decision_write_allowed": False,
                    "owner_route": route,
                }
            ],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    request = result["request_tasks"][0]
    dispatch = result["default_executor_dispatches"][0]
    source_refs = dispatch["owner_route"]["source_refs"]
    assert request["action_type"] == "return_to_ai_reviewer_workflow"
    assert request["request_owner"] == "ai_reviewer"
    assert request["reason"] == "ai_reviewer_record_stale_after_current_inputs"
    assert dispatch["action_type"] == "return_to_ai_reviewer_workflow"
    assert dispatch["next_executable_owner"] == "ai_reviewer"
    assert dispatch["source_action"]["next_work_unit"] == work_unit_id
    assert source_refs["work_unit_id"] == work_unit_id
    assert "materialized_work_unit_id" not in source_refs


def test_current_ai_reviewer_write_routeback_preempts_stale_package_freshness_followthrough(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    manuscript_path = study_root / "paper" / "draft.md"
    review_manuscript_path = study_root / "paper" / "build" / "review_manuscript.md"
    manuscript_text = (
        "# Draft\n\n"
        "Current manuscript still omits the required confidence intervals and must return to write.\n"
    )
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    review_manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    review_manuscript_path.write_text(manuscript_text, encoding="utf-8")
    eval_id = "publication-eval::003::quest::2026-05-28T16:44:29+00:00::ai-reviewer"
    record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260528T164429Z_publication_eval_record.json"
    )
    record_payload = current_manuscript_routeback_record(
        study_root=study_root,
        manuscript_path=manuscript_path,
        manuscript_text=manuscript_text,
        study_id=study_id,
        quest_id=quest_id,
        eval_id=eval_id,
        emitted_at="2026-05-28T16:44:29+00:00",
    )
    _write_json(record_path, record_payload)
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "schema_version": 1,
            "request_kind": "return_to_ai_reviewer_workflow",
            "study_id": study_id,
            "quest_id": quest_id,
            "request_owner": "ai_reviewer",
            "request_lifecycle": {"state": "assessment_written", "blocked_reason": None},
            "publication_eval_record_ref": str(record_path.resolve()),
            "ai_reviewer_record": record_payload,
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json",
        {
            "surface": "quality_repair_execution_evidence",
            "schema_version": 1,
            "canonical_artifact_delta": {"meaningful_artifact_delta": True},
            "manuscript_surface_hygiene": {
                "story_surface_delta_required": True,
                "story_surface_delta_present": True,
                "story_surface_delta_refs": [
                    str(manuscript_path.resolve()),
                    str(review_manuscript_path.resolve()),
                ],
            },
        },
    )
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="ai_reviewer",
        owner_reason="ai_reviewer_record_stale_after_current_inputs",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )
    route.update(
        {
            "schema_version": 2,
            "truth_epoch": "truth-event-000008",
            "route_epoch": "truth-event-000008",
            "source_fingerprint": "truth-snapshot::dm003-current-inputs",
            "runtime_health_epoch": "runtime-health-event-006160",
            "work_unit_fingerprint": f"domain-transition::ai_reviewer_re_eval::{work_unit_id}",
            "idempotency_key": "owner-route::dm003::ai-reviewer-current-routeback",
            "source_refs": {
                "study_truth_epoch": "truth-event-000008",
                "runtime_health_epoch": "runtime-health-event-006160",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": f"domain-transition::ai_reviewer_re_eval::{work_unit_id}",
                "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
                "owner_route_currentness_basis": {
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": f"domain-transition::ai_reviewer_re_eval::{work_unit_id}",
                    "truth_epoch": "truth-event-000008",
                    "runtime_health_epoch": "runtime-health-event-006160",
                    "owner_reason": "ai_reviewer_record_stale_after_current_inputs",
                },
            },
        }
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "quest_id": quest_id, "owner_route": route}],
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "owner": "ai_reviewer",
                    "request_owner": "ai_reviewer",
                    "reason": "ai_reviewer_record_stale_after_current_inputs",
                    "next_work_unit": work_unit_id,
                    "controller_work_unit_id": work_unit_id,
                    "executable_work_unit": work_unit_id,
                    "work_unit_fingerprint": f"domain-transition::ai_reviewer_re_eval::{work_unit_id}",
                    "required_output_surface": "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
                    "record_only_surface": True,
                    "publication_eval_latest_write_allowed": False,
                    "controller_decision_write_allowed": False,
                    "owner_route": route,
                }
            ],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    request = result["request_tasks"][0]
    dispatch = result["default_executor_dispatches"][0]
    source_refs = dispatch["owner_route"]["source_refs"]
    assert request["action_type"] == "run_quality_repair_batch"
    assert request["request_owner"] == "write"
    assert request["reason"] == "manuscript_story_surface_delta_missing"
    assert dispatch["action_type"] == "run_quality_repair_batch"
    assert source_refs["work_unit_id"] == work_unit_id
    assert source_refs["materialized_work_unit_id"] == "medical_prose_write_repair"
    assert source_refs["materialized_from_action_type"] == "return_to_ai_reviewer_workflow"
    assert source_refs["bridged_from_owner_reason"] == "ai_reviewer_record_stale_after_current_inputs"
    assert source_refs["bridge_authority"] == "domain_action_request_materializer_story_surface_bridge"
