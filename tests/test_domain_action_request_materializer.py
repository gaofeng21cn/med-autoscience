from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from tests.domain_action_request_materializer_cases.shared import owner_route as _owner_route
from tests.domain_action_request_materializer_cases.shared import (
    disable_progress_projection as _disable_progress_projection,
)
from tests.domain_action_request_materializer_cases.shared import (
    unsupported_domain_action as _unsupported_domain_action,
)
from tests.domain_action_request_materializer_cases.shared import (
    next_action_envelope as _next_action_envelope,
)
from tests.domain_action_request_materializer_cases.shared import write_json as _write_json
from tests.domain_action_request_materializer_cases.request_handoff_dispatch_cases import (
    test_materialize_domain_action_requests_writes_request_handoff_for_publication_gate_and_ai_reviewer_actions,
    test_materialize_domain_action_requests_request_handoff_requires_owner_route_allowed_action,
    test_materialize_domain_action_requests_mixed_queue_writes_owner_callable_adapters,
    test_materialize_domain_action_requests_does_not_repeat_suppress_pending_ai_reviewer_output,
)
from tests.domain_action_request_materializer_cases.unsupported_action_boundary import (
    test_materialize_domain_action_requests_dry_run_ignores_unsupported_action_without_writes,
    test_materialize_domain_action_requests_apply_does_not_write_unsupported_action_surfaces,
    test_materialize_domain_action_requests_does_not_resurrect_existing_unsupported_dispatch,
)
from tests.domain_action_request_materializer_cases.test_evidence_gap_decision import (
    test_materializer_evidence_gap_prompt_defaults_do_not_block_without_gap,
    test_materializer_evidence_tail_continues_but_withholds_readiness_claims,
    test_materializer_hard_evidence_gap_blocks_current_dispatch,
    test_materializer_soft_gap_continues_and_records_ledger,
)
from tests.domain_action_request_materializer_cases.test_progress_currentness_route_cases import (
    test_materialize_domain_action_requests_blocks_readiness_and_stage_native_when_current_action_missing,
    test_materialize_domain_action_requests_blocks_stage_native_write_when_fresh_envelope_is_typed_blocker,
    test_materialize_domain_action_requests_does_not_materialize_fatal_budget_exhausted_successor,
    test_materialize_domain_action_requests_prefers_fresh_domain_transition_over_stage_native_write,
    test_materialize_domain_action_requests_prefers_fresh_progress_ticket_over_stale_readiness_scan,
    test_materialize_domain_action_requests_prefers_fresh_readiness_action_over_stage_native_write,
    test_materialize_domain_action_requests_rejects_currentness_action_when_next_action_identity_mismatches,
    test_materialize_domain_action_requests_retires_nonfatal_budget_exhausted_successor_without_envelope,
    test_materialize_domain_action_requests_routes_consumed_write_closeout_to_ai_reviewer,
)
from tests.study_runtime_test_helpers import make_profile, write_study


@pytest.fixture(autouse=True)
def _isolated_opl_state_dir(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OPL_STATE_DIR", str(tmp_path / "opl-state"))




def test_materialize_domain_action_requests_routes_publication_eval_recommended_repair_without_ticket(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress.projection")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_json(
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "quest_id": study_id,
                            "action_type": "run_quality_repair_batch",
                            "authority": "stage_native_workspace_next_action",
                            "reason": "stale_stage_native_write_repair",
                            "owner": "write",
                            "work_unit_id": "medical_prose_write_repair",
                        }
                    ],
                }
            ],
        },
    )
    publication_eval_id = f"publication-eval::{study_id}::2026-06-14T08:02:57+00:00"
    fingerprint = "publication-blockers::0915410f804b3697"
    route_identity_key = f"provider-admission::{study_id}::{fingerprint}"
    attempt_idempotency_key = f"attempt::{study_id}::{fingerprint}"

    def read_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "generated_at": "2026-06-14T08:03:00+00:00",
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "currentness_basis": {
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": fingerprint,
                    "truth_epoch": "truth-event-000035-39f0b8e96689a623",
                    "runtime_health_epoch": "runtime-health-event-006839-87fcfd5b5277d89f",
                    "route_identity_key": route_identity_key,
                    "attempt_idempotency_key": attempt_idempotency_key,
                },
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "medical_prose_write_repair",
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "publication_eval.recommended_actions.readiness_blocker_repair",
                "source_ref": "runtime/quests/003/artifacts/reports/publishability_gate/latest.json",
                "next_owner": "write",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "publication_eval_id": publication_eval_id,
                "target_surface": {
                    "ref_kind": "publication_eval_recommended_action",
                    "publication_eval_id": publication_eval_id,
                    "next_work_unit": {
                        "unit_id": "medical_prose_write_repair",
                        "lane": "write",
                    },
                },
            },
            "next_action": _next_action_envelope(
                study_id=study_id,
                action_type="run_quality_repair_batch",
                work_unit_id="medical_prose_write_repair",
            ),
            "current_owner_ticket": None,
            "owner_route": None,
        }

    monkeypatch.setattr(progress_module, "read_study_progress", read_progress)

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert [item["action_type"] for item in result["domain_progress_transition_requests"]] == [
        "run_quality_repair_batch"
    ]
    dispatch = result["domain_progress_transition_requests"][0]
    assert dispatch["study_id"] == study_id
    assert dispatch["next_executable_owner"] == "write"
    assert dispatch["route_identity_key"] == route_identity_key
    assert dispatch["attempt_idempotency_key"] == attempt_idempotency_key
    assert dispatch["currentness_basis"]["route_identity_key"] == route_identity_key
    assert dispatch["currentness_basis"]["attempt_idempotency_key"] == attempt_idempotency_key
    assert dispatch["owner_route_ref"]["work_unit_fingerprint"] == fingerprint
    assert dispatch["owner_route_ref"]["source_fingerprint"] == publication_eval_id
    assert dispatch["owner_route_ref"]["source_refs"]["owner_route_currentness_basis"] == {
        "truth_epoch": "truth-event-000035-39f0b8e96689a623",
        "runtime_health_epoch": "runtime-health-event-006839-87fcfd5b5277d89f",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": fingerprint,
        "source_eval_id": publication_eval_id,
        "source_fingerprint": publication_eval_id,
    }
    assert any(
        item["reason"] == "superseded_by_fresh_study_progress_current_owner_ticket"
        and item["action_type"] == "run_quality_repair_batch"
        for item in result["ignored_actions"]
    )


def test_materialize_domain_action_requests_apply_refreshes_latest_when_current_queue_is_empty(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    _disable_progress_projection(monkeypatch)
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    stale_dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / "unsupported_supervisor_action.json"
    )
    consumer_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json"
    latest_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(stale_dispatch_path, {"surface": "owner_callable_dispatch_request", "dispatch_status": "ready"})
    _write_json(
        consumer_path,
        {
            "surface": "domain_action_request_materializer",
            "generated_at": "2026-05-07T16:13:16+00:00",
            "owner_callable_adapter_count": 1,
            "owner_callable_adapters": [
                {
                    "study_id": study_id,
                    "action_type": "unsupported_supervisor_action",
                    "dispatch_status": "ready",
                    "refs": {"dispatch_path": str(stale_dispatch_path)},
                }
            ],
        },
    )
    _write_json(
        latest_path,
        {
            "surface": "portable_paper_mission_owner_surface",
            "schema_version": 1,
            "studies": [{"study_id": study_id}],
            "action_queue": [],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["runtime_control_owner"] == "one-person-lab"
    assert result["request_task_count"] == 0
    assert result["domain_progress_transition_request_count"] == 0
    assert result["written_files"] == []
    assert json.loads(consumer_path.read_text(encoding="utf-8"))["owner_callable_adapter_count"] == 1


def test_materialize_domain_action_requests_only_writes_current_owner_dispatch_for_route_epoch(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    _disable_progress_projection(monkeypatch)
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm002")
    route = _owner_route(
        study_id=study_id,
        quest_id="quest-dm002",
        next_owner="artifact_os",
        owner_reason="current_package_freshness_required",
        allowed_actions=["current_package_freshness_required", "return_to_ai_reviewer_workflow"],
    )
    latest_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        latest_path,
        {
            "surface": "portable_paper_mission_owner_surface",
            "schema_version": 1,
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": "quest-dm002",
                    "action_type": "current_package_freshness_required",
                    "authority": "observability_only",
                    "owner": "artifact_os",
                    "reason": "current_package_freshness_required",
                    "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
                    "next_action": _next_action_envelope(
                        study_id=study_id,
                        action_type="current_package_freshness_required",
                        work_unit_id="current_package_freshness_required",
                    ),
                    "owner_route": route,
                    "handoff_packet": {
                        "request_kind": "current_package_freshness_required",
                        "authority": "observability_only",
                        "request_owner": "artifact_os",
                        "owner_route": route,
                    },
                },
                {
                    "study_id": study_id,
                    "quest_id": "quest-dm002",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "authority": "observability_only",
                    "owner": "ai_reviewer",
                    "reason": "ai_reviewer_assessment_required",
                    "required_output_surface": "artifacts/publication_eval/latest.json",
                    "next_action": _next_action_envelope(
                        study_id=study_id,
                        action_type="return_to_ai_reviewer_workflow",
                        work_unit_id="return_to_ai_reviewer_workflow",
                    ),
                    "owner_route": route,
                    "handoff_packet": {
                        "request_kind": "return_to_ai_reviewer_workflow",
                        "authority": "observability_only",
                        "request_owner": "ai_reviewer",
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

    assert result["target_runtime_owner"] == "one-person-lab"
    assert result["canonical_transition_request_surface"] == "domain_progress_transition_requests"
    assert "owner_callable_adapter_list_deprecated" not in result
    assert "owner_callable_adapter_count" not in result
    assert "owner_callable_adapters" not in result
    assert result["domain_progress_transition_request_count"] == 2
    legacy_diagnostics = result["legacy_owner_callable_adapter_diagnostics"]
    assert legacy_diagnostics["surface"] == "legacy_owner_callable_adapter_diagnostics"
    assert legacy_diagnostics["canonical_transition_request_surface"] == "domain_progress_transition_requests"
    assert legacy_diagnostics["diagnostic_only"] is True
    assert legacy_diagnostics["counts_authority"] is False
    assert legacy_diagnostics["readiness_authority"] is False
    assert legacy_diagnostics["can_create_success_outcome"] is False
    assert legacy_diagnostics["body_authority"] is False
    assert legacy_diagnostics["body_projection"] is False
    assert legacy_diagnostics["legacy_payload_scope"] == "identity_refs_only"
    assert legacy_diagnostics["legacy_dispatch_count"] == 2
    assert legacy_diagnostics["legacy_ready_count"] == 0
    assert legacy_diagnostics["legacy_blocked_count"] == 1
    assert legacy_diagnostics["legacy_transition_request_pending_count"] == 1
    assert legacy_diagnostics["legacy_dispatch_body_omitted"] is True
    assert len(legacy_diagnostics["legacy_dispatch_refs"]) == 2
    assert legacy_diagnostics["legacy_dispatches"] == legacy_diagnostics["legacy_dispatch_refs"]
    assert "source_action" not in legacy_diagnostics["legacy_dispatches"][0]
    assert "owner_route" not in legacy_diagnostics["legacy_dispatches"][0]
    assert "prompt_contract" not in legacy_diagnostics["legacy_dispatches"][0]
    transition_requests = result["domain_progress_transition_requests"]
    assert [item["action_type"] for item in transition_requests] == [
        "current_package_freshness_required",
        "return_to_ai_reviewer_workflow",
    ]
    assert transition_requests[0]["dispatch_status"] == "transition_request_pending"
    assert transition_requests[0]["legacy_owner_callable_adapter_readback"] is False
    assert transition_requests[0]["durable_carrier_owner"] == "one-person-lab"
    assert transition_requests[0]["mas_creates_owner_callable_carrier"] is False
    assert transition_requests[0]["mas_creates_opl_outbox"] is False
    assert transition_requests[0]["mas_creates_opl_event"] is False
    assert transition_requests[0]["mas_creates_opl_stage_run"] is False
    assert transition_requests[0]["provider_admission_pending"] is False
    assert transition_requests[0]["provider_admission_requires_opl_runtime_result"] is True
    transition_postcondition = transition_requests[0]["opl_transition_runtime_postcondition"]
    assert transition_postcondition["surface_kind"] == "opl_domain_progress_transition_runtime_postcondition"
    assert transition_postcondition["required_owner_surface"] == "one-person-lab DomainProgressTransitionRuntime"
    assert transition_postcondition["runtime_contract_ref"] == (
        "contracts/opl_domain_progress_transition_runtime_contract.json"
    )
    assert transition_postcondition["mas_surface_role"] == "domain_intent_and_policy_request_projection"
    assert transition_postcondition["mas_can_satisfy_readback"] is False
    assert transition_postcondition["request_projection_only"] is True
    assert transition_postcondition["required_readback_shape"] == {
        "identity": True,
        "causality": True,
        "authority_boundary": True,
        "exactly_one_outcome": True,
        "projection_metadata": True,
        "event_id": True,
        "outbox_item_id": True,
        "stage_run_identity": True,
    }
    assert transition_postcondition["mas_projection_cannot_replace"] == [
        "opl_command",
        "opl_event",
        "opl_transactional_outbox",
        "opl_stage_run",
        "opl_provider_admission",
        "opl_fixed_point_reconcile",
    ]
    assert transition_requests[0]["opl_domain_progress_transition_request"]["surface_kind"] == (
        "mas_domain_progress_transition_request"
    )
    assert result["mas_dispatch_authority"] is False
    assert result["mas_creates_opl_outbox"] is False
    assert result["mas_creates_opl_event"] is False
    assert result["mas_creates_opl_stage_run"] is False
    assert result["authority_boundary"]["mas_dispatch_authority"] is False
    assert result["authority_boundary"]["can_select_next_action"] is False
    assert result["opl_transition_runtime_postcondition"] == transition_postcondition
    assert result["apply_writes_domain_intent_projection_only"] is True
    assert result["apply_writes_disabled_reason"] == (
        "opl_domain_progress_transition_runtime_owns_durable_carrier"
    )
    assert transition_requests[0]["owner_callable_adapter_diagnostic_only"] is True
    assert transition_requests[0]["owner_callable_adapter_readiness_authority"] is False
    assert transition_requests[0]["owner_callable_adapter_can_create_success_outcome"] is False
    assert transition_requests[0]["target_runtime_owner"] == "one-person-lab"
    assert transition_requests[0]["mas_dispatch_authority"] is False
    assert transition_requests[0]["mas_creates_opl_outbox"] is False
    assert transition_requests[0]["mas_creates_opl_event"] is False
    assert transition_requests[0]["mas_creates_opl_stage_run"] is False
    assert transition_requests[0]["dispatch_ready_for_execution_authority"] is False
    assert transition_requests[0]["provider_admission_pending"] is False
    assert transition_requests[0]["provider_admission_requires_opl_runtime_result"] is True
    assert transition_requests[0]["opl_transition_runtime_postcondition"] == transition_postcondition
    assert transition_requests[0]["authority_boundary"]["can_create_success_outcome"] is False
    assert transition_requests[0]["authority_boundary"]["can_select_next_action"] is False
    assert transition_requests[0]["mas_local_dispatch_carrier_persistence"] == "forbidden"
    assert transition_requests[0]["blocked_reason"] == "opl_execution_authorization_required"
    assert "domain_intent" not in transition_requests[0]
    assert transition_requests[0]["domain_intent_body_omitted"] is True
    assert transition_requests[0]["domain_intent_ref"]["action_type"] == "current_package_freshness_required"
    assert transition_requests[0]["owner_callable_adapter_contract"]["execution_authority_owner"] == "one-person-lab"
    assert transition_requests[1]["dispatch_status"] == "blocked"
    assert transition_requests[1]["blocked_reason"] == "owner_route_next_owner_mismatch"
    dispatch_dir = study_root / "artifacts" / "supervision" / "consumer" / "owner_callable_adapters"
    assert not (dispatch_dir / "current_package_freshness_required.json").exists()
    assert not (dispatch_dir / "return_to_ai_reviewer_workflow.json").exists()
