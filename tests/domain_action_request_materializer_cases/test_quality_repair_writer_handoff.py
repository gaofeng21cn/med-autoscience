from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _assert_transition_request_projection(dispatch: dict[str, object]) -> dict[str, object]:
    transition_request = dispatch["opl_domain_progress_transition_request"]
    assert isinstance(transition_request, dict)
    assert dispatch["dispatch_status"] == "transition_request_pending"
    assert dispatch["provider_admission_pending"] is False
    assert dispatch["provider_admission_requires_opl_runtime_result"] is True
    assert dispatch["mas_local_dispatch_carrier_persistence"] == "forbidden"
    assert dispatch["opl_transition_runtime_required_for_durable_carrier"] is True
    assert transition_request["surface_kind"] == "mas_domain_progress_transition_request"
    assert transition_request["target_runtime_owner"] == "one-person-lab"
    assert transition_request["target_runtime_kind"] == "DomainProgressTransitionRuntime"
    assert transition_request["recommended_transition_kind"] == "MaterializeOwnerAction"
    assert transition_request["mas_can_create_opl_outbox_record"] is False
    return transition_request


def _assert_request_task_projection(task: dict[str, object]) -> None:
    assert task["dispatch_status"] == "transition_request_pending"
    assert task["provider_admission_pending"] is False
    assert task["provider_admission_requires_opl_runtime_result"] is True
    assert task["mas_local_request_packet_persistence"] == "forbidden"
    assert task["opl_transition_runtime_required_for_durable_carrier"] is True


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
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": quest_id,
        "truth_epoch": "truth-epoch::dm002::writer-handoff",
        "runtime_health_epoch": "runtime-health::dm002::writer-handoff",
        "work_unit_fingerprint": "dm002_same_line_methods_display_package_repair",
        "failure_signature": owner_reason,
        "trace_id": "owner-route-trace::dm002::writer-handoff",
        "route_epoch": "truth-epoch::dm002::writer-handoff",
        "source_fingerprint": "truth-source::dm002::writer-handoff",
        "current_owner": "mas_controller",
        "next_owner": next_owner,
        "owner_reason": owner_reason,
        "active_run_id": None,
        "allowed_actions": allowed_actions,
        "blocked_actions": [],
        "idempotency_key": "owner-route::dm002::writer-handoff",
    }


def test_materialize_domain_action_requests_preserves_current_quality_repair_writer_handoff(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    monkeypatch.setenv("OPL_STATE_DIR", str(tmp_path / "opl-state"))
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm002")
    route = _owner_route(
        study_id=study_id,
        quest_id="quest-dm002",
        next_owner="write",
        owner_reason="manuscript_story_surface_delta_missing",
        allowed_actions=["run_quality_repair_batch"],
    )
    action = {
        "study_id": study_id,
        "quest_id": "quest-dm002",
        "action_type": "run_quality_repair_batch",
        "authority": "observability_only",
        "owner": "write",
        "reason": "manuscript_story_surface_delta_missing",
        "required_output_surface": (
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        "owner_route": route,
        "next_work_unit": {"unit_id": "dm002_same_line_methods_display_package_repair", "lane": "write"},
        "handoff_packet": {
            "request_kind": "run_quality_repair_batch",
            "authority": "observability_only",
            "request_owner": "write",
            "owner_route": route,
        },
    }
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": "quest-dm002",
                    "owner_route": route,
                    "action_queue": [action],
                }
            ],
            "action_queue": [action],
        },
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / "run_quality_repair_batch.json"
    )
    _write_json(dispatch_path, _writer_handoff(study_id=study_id, dispatch_path=dispatch_path, route=route))
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "quality_repair_batch" / "latest.json",
        {
            "request_kind": "run_quality_repair_batch",
            "status": "requested",
            "study_id": study_id,
            "quest_id": "quest-dm002",
            "request_owner": "write",
            "expected_owner": "write",
            "next_executable_owner": "write",
            "dispatch_authority": "quality_repair_batch_writer_handoff",
            "owner_route": route,
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    dispatch = result["owner_callable_adapters"][0]
    written_dispatch = json.loads(dispatch_path.read_text(encoding="utf-8"))
    transition_request = _assert_transition_request_projection(dispatch)
    assert dispatch["dispatch_authority"] == "quality_repair_batch_writer_handoff"
    assert dispatch["medical_claim_authoring_allowed"] is True
    assert dispatch["prompt_contract"]["medical_claim_authoring_allowed"] is True
    assert dispatch["prompt_contract"]["allowed_write_surfaces"] == [
        "paper/draft.md",
        "paper/build/review_manuscript.md",
        "paper/claim_evidence_map.json",
        "paper/evidence_ledger.json",
        "paper/review/**",
    ]
    assert dispatch["prompt_contract"]["search_boundaries"]["surface"] == "default_executor_search_discipline.v1"
    assert "grep -R" in dispatch["prompt_contract"]["search_boundaries"]["forbidden_command_patterns"]
    assert "runtime/.ds/**" in dispatch["prompt_contract"]["search_boundaries"]["forbidden_path_globs"]
    assert dispatch["source_action"]["surface"] == "quality_repair_batch"
    assert dispatch["source_action"]["blocked_reason"] == "manuscript_story_surface_delta_missing"
    assert transition_request["dispatch_ref"] == str(dispatch_path)
    assert written_dispatch["dispatch_authority"] == "quality_repair_batch_writer_handoff"
    assert written_dispatch["medical_claim_authoring_allowed"] is True
    assert "immutable_dispatch_path" not in written_dispatch.get("refs", {})
    assert result["apply_writes_domain_intent_projection_only"] is True
    assert result["apply_writes_disabled_reason"] == (
        "opl_domain_progress_transition_runtime_owns_durable_carrier"
    )
    assert result["mas_local_dispatch_carrier_persistence"] == "forbidden"
    assert result["mas_local_request_packet_persistence"] == "forbidden"
    assert result["ready_owner_callable_adapter_count"] == 0
    assert result["transition_request_pending_owner_callable_adapter_count"] == 1


def test_materialize_runtime_owner_story_surface_route_to_writer_handoff(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    dispatch_contract = importlib.import_module(
        "med_autoscience.controllers.domain_owner_action_dispatch_parts.dispatch_contract"
    )
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    monkeypatch.setenv("OPL_STATE_DIR", str(tmp_path / "opl-state"))
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    source_eval_id = "publication-eval::003::current-analysis-harmonization"
    route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": quest_id,
        "truth_epoch": source_eval_id,
        "runtime_health_epoch": "runtime-health::003::write-current",
        "work_unit_fingerprint": "sha256:medical-prose-currentness-recheck",
        "failure_signature": "quest_waiting_opl_runtime_owner_route",
        "route_epoch": source_eval_id,
        "source_fingerprint": "truth-source::003::medical-prose-currentness-recheck",
        "current_owner": "mas_controller",
        "next_owner": "write",
        "owner_reason": "quest_waiting_opl_runtime_owner_route",
        "active_run_id": None,
        "allowed_actions": ["run_quality_repair_batch"],
        "blocked_actions": ["return_to_ai_reviewer_workflow", "run_gate_clearing_batch"],
        "idempotency_key": "owner-route::003::medical-prose-currentness-recheck",
        "source_refs": {
            "source_eval_id": source_eval_id,
            "work_unit_id": "medical_prose_currentness_recheck",
            "work_unit_fingerprint": "sha256:medical-prose-currentness-recheck",
            "runtime_health_epoch": "runtime-health::003::write-current",
            "study_truth_epoch": source_eval_id,
            "blocked_reason": "quest_waiting_opl_runtime_owner_route",
        },
    }
    required_output_surface = (
        "canonical manuscript story-surface delta or "
        "typed blocker:manuscript_story_surface_delta_missing"
    )
    action = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": "run_quality_repair_batch",
        "authority": "observability_only",
        "owner": "write",
        "request_owner": "write",
        "recommended_owner": "write",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "required_output_surface": required_output_surface,
        "owner_route": route,
        "next_work_unit": "medical_prose_currentness_recheck",
        "controller_work_unit_id": "medical_prose_currentness_recheck",
        "executable_work_unit": "medical_prose_currentness_recheck",
        "work_unit_fingerprint": "sha256:medical-prose-currentness-recheck",
        "source_eval_id": source_eval_id,
        "handoff_packet": {
            "request_kind": "run_quality_repair_batch",
            "authority": "observability_only",
            "request_owner": "write",
            "owner_route": route,
        },
    }
    _write_json(
        study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json",
        {"status": "blocked", "blockers": ["manuscript_story_surface_delta_missing"]},
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
                    "owner_route": route,
                    "action_queue": [action],
                }
            ],
            "action_queue": [action],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    dispatch = result["owner_callable_adapters"][0]
    prompt_contract = dispatch["prompt_contract"]
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / "run_quality_repair_batch.json"
    )
    transition_request = _assert_transition_request_projection(dispatch)
    assert dispatch["dispatch_authority"] == "quality_repair_batch_writer_handoff"
    assert dispatch["medical_claim_authoring_allowed"] is True
    assert dispatch["source_action"]["blocked_reason"] == "manuscript_story_surface_delta_missing"
    assert dispatch["owner_route"]["owner_reason"] == "manuscript_story_surface_delta_missing"
    assert dispatch["owner_route"]["source_refs"]["work_unit_id"] == "medical_prose_currentness_recheck"
    assert dispatch["owner_route"]["source_refs"]["bridged_from_owner_reason"] == (
        "quest_waiting_opl_runtime_owner_route"
    )
    assert prompt_contract["medical_claim_authoring_allowed"] is True
    assert prompt_contract["allowed_write_surfaces"] == [
        "paper/draft.md",
        "paper/build/review_manuscript.md",
        "paper/claim_evidence_map.json",
        "paper/evidence_ledger.json",
        "paper/review/**",
    ]
    assert "paper/**" not in prompt_contract["forbidden_surfaces"]
    assert "artifacts/publication_eval/latest.json" in prompt_contract["forbidden_surfaces"]
    assert "artifacts/controller_decisions/latest.json" in prompt_contract["forbidden_surfaces"]
    assert dispatch_contract.prompt_contract_error(
        prompt_contract,
        forbidden_surfaces=module.FORBIDDEN_SURFACES,
    ) is None
    assert not dispatch_path.exists()
    assert "dispatch_ref" not in transition_request
    assert result["apply_writes_domain_intent_projection_only"] is True
    assert result["apply_writes_disabled_reason"] == (
        "opl_domain_progress_transition_runtime_owns_durable_carrier"
    )
    assert result["ready_owner_callable_adapter_count"] == 0
    assert result["transition_request_pending_owner_callable_adapter_count"] == 1


def test_materialize_current_ai_reviewer_record_then_prose_gate_package_replay_to_writer_handoff(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    dispatch_module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    dispatch_contract = importlib.import_module(
        "med_autoscience.controllers.domain_owner_action_dispatch_parts.dispatch_contract"
    )
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    monkeypatch.setenv("OPL_STATE_DIR", str(tmp_path / "opl-state"))
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    manuscript_path = study_root / "paper" / "draft.md"
    review_manuscript_path = study_root / "paper" / "build" / "review_manuscript.md"
    manuscript_text = "# Draft\n\nCurrent DM002 manuscript requires prose hardening after AI review.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    review_manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    review_manuscript_path.write_text(manuscript_text, encoding="utf-8")
    source_eval_id = (
        "publication-eval::002-dm-china-us-mortality-attribution::"
        "ai-reviewer-current-manuscript::20260602T062142Z"
    )
    record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260602T062142Z_publication_eval_record.json"
    )
    from tests.reviewer_os_fixture_helpers import current_manuscript_routeback_record

    record_payload = current_manuscript_routeback_record(
        study_root=study_root,
        manuscript_path=manuscript_path,
        manuscript_text=manuscript_text,
        study_id=study_id,
        quest_id=quest_id,
        eval_id=source_eval_id,
        emitted_at="2026-06-02T06:21:42+00:00",
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
    work_unit_id = "consume_current_ai_reviewer_record_then_prose_gate_package_replay"
    work_unit_fingerprint = "domain-transition::ai_reviewer_re_eval::produce_ai_reviewer_publication_eval_record_against_current_manuscript"
    route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": quest_id,
        "truth_epoch": "truth-event-000035-d649b1535a6bc2aa",
        "route_epoch": "truth-event-000035-d649b1535a6bc2aa",
        "runtime_health_epoch": "runtime-health-event-006513-a0659016cafcf7e2",
        "work_unit_fingerprint": work_unit_fingerprint,
        "failure_signature": "quest_waiting_opl_runtime_owner_route",
        "trace_id": "owner-route-trace::dm002::current-reviewer-record-consumption",
        "source_fingerprint": "truth-snapshot::023fed00f609d4d2ab1283f7",
        "current_owner": "mas_controller",
        "next_owner": "write",
        "owner_reason": "quest_waiting_opl_runtime_owner_route",
        "active_run_id": None,
        "allowed_actions": ["run_quality_repair_batch"],
        "blocked_actions": ["return_to_ai_reviewer_workflow", "run_gate_clearing_batch"],
        "idempotency_key": "owner-route::dm002::current-reviewer-record-consumption",
        "source_refs": {
            "blocked_reason": "quest_waiting_opl_runtime_owner_route",
            "runtime_health_epoch": "runtime-health-event-006513-a0659016cafcf7e2",
            "source_eval_id": source_eval_id,
            "study_truth_epoch": "truth-event-000035-d649b1535a6bc2aa",
            "work_unit_fingerprint": work_unit_fingerprint,
            "work_unit_id": work_unit_id,
            "owner_route_currentness_basis": {
                "runtime_health_epoch": "runtime-health-event-006513-a0659016cafcf7e2",
                "source_eval_id": source_eval_id,
                "truth_epoch": "truth-event-000035-d649b1535a6bc2aa",
                "work_unit_fingerprint": work_unit_fingerprint,
                "work_unit_id": work_unit_id,
            },
        },
    }
    action = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": "run_quality_repair_batch",
        "authority": "observability_only",
        "owner": "write",
        "request_owner": "write",
        "recommended_owner": "write",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "route_target": "write",
        "required_output_surface": (
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        "next_work_unit": work_unit_id,
        "controller_work_unit_id": work_unit_id,
        "executable_work_unit": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "source_eval_id": source_eval_id,
        "owner_route": route,
        "handoff_packet": {
            "request_kind": "run_quality_repair_batch",
            "authority": "observability_only",
            "request_owner": "write",
            "owner_route": route,
        },
    }
    _write_json(
        study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json",
        {"status": "progress_delta_candidate", "blockers": []},
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
                    "owner_route": route,
                    "action_queue": [action],
                }
            ],
            "action_queue": [action],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    request = result["request_tasks"][0]
    dispatch = result["owner_callable_adapters"][0]
    prompt_contract = dispatch["prompt_contract"]
    source_refs = dispatch["owner_route"]["source_refs"]
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / "run_quality_repair_batch.json"
    )
    transition_request = _assert_transition_request_projection(dispatch)
    _assert_request_task_projection(request)
    assert request["reason"] == "manuscript_story_surface_delta_missing"
    assert request["source_action"]["next_work_unit"] == "dm002_current_publication_hardening_after_current_ai_reviewer_eval"
    assert dispatch["dispatch_authority"] == "quality_repair_batch_writer_handoff"
    assert dispatch["medical_claim_authoring_allowed"] is True
    assert dispatch["source_action"]["blocked_reason"] == "manuscript_story_surface_delta_missing"
    assert dispatch["owner_route"]["owner_reason"] == "manuscript_story_surface_delta_missing"
    assert prompt_contract["next_work_unit"]["unit_id"] == "dm002_current_publication_hardening_after_current_ai_reviewer_eval"
    assert source_refs["work_unit_id"] == work_unit_id
    assert source_refs["source_eval_id"] == source_eval_id
    assert source_refs["materialized_work_unit_id"] == "dm002_current_publication_hardening_after_current_ai_reviewer_eval"
    assert source_refs["materialized_from_action_type"] == "run_quality_repair_batch"
    assert source_refs["bridged_from_owner_reason"] == "quest_waiting_opl_runtime_owner_route"
    assert source_refs["bridge_authority"] == "domain_action_request_materializer_story_surface_bridge"
    assert prompt_contract["medical_claim_authoring_allowed"] is True
    assert prompt_contract["allowed_write_surfaces"] == [
        "paper/draft.md",
        "paper/build/review_manuscript.md",
        "paper/claim_evidence_map.json",
        "paper/evidence_ledger.json",
        "paper/review/**",
    ]
    assert dispatch_contract.prompt_contract_error(
        prompt_contract,
        forbidden_surfaces=module.FORBIDDEN_SURFACES,
    ) is None
    assert not dispatch_path.exists()
    assert "dispatch_ref" not in transition_request
    assert result["ready_owner_callable_adapter_count"] == 0
    assert result["transition_request_pending_owner_callable_adapter_count"] == 1
    monkeypatch.setattr(
        dispatch_module.action_execution.quality_repair,
        "execute_quality_repair_batch",
        lambda **_: {
            "execution_status": "handoff_ready",
            "blocked_reason": None,
            "owner_callable_surface": "quality_repair_batch.run_quality_repair_batch",
            "owner_result": {"status": "handoff_ready"},
        },
    )

    dispatch_result = dispatch_module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    summary = dispatch_result["per_study_execution_summary"][0]
    assert summary["selected_dispatch_count"] == 0
    assert summary["zero_dispatch_reason"] == "no_selected_dispatch_for_requested_action_types"
    assert dispatch_result["execution_count"] == 0
    assert dispatch_result["blocked_count"] == 0


def test_materialize_prefers_current_writer_handoff_over_consumed_reviewer_transition(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    writer_handoff = importlib.import_module(
        "med_autoscience.controllers.quality_repair_batch_parts.writer_handoff"
    )
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    monkeypatch.setenv("OPL_STATE_DIR", str(tmp_path / "opl-state"))
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    source_eval_id = "publication-eval::003::current-writer-handoff"
    work_unit_id = "dpcc_medical_journal_quality_story_surface_repair"
    stale_reviewer_work_unit = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    current_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": quest_id,
        "truth_epoch": source_eval_id,
        "route_epoch": source_eval_id,
        "runtime_health_epoch": "runtime-health::003::current-writer-handoff",
        "work_unit_fingerprint": "domain-transition::dm003::current-writer-handoff",
        "failure_signature": "manuscript_story_surface_delta_missing",
        "trace_id": "owner-route-trace::003::current-writer-handoff",
        "source_fingerprint": "truth-source::003::current-writer-handoff",
        "current_owner": "quality_repair_batch",
        "next_owner": "write",
        "owner_reason": "manuscript_story_surface_delta_missing",
        "active_run_id": None,
        "allowed_actions": ["run_quality_repair_batch"],
        "blocked_actions": ["return_to_ai_reviewer_workflow", "run_gate_clearing_batch"],
        "idempotency_key": "quality-repair-writer-handoff::003::current",
        "source_refs": {
            "source_eval_id": source_eval_id,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": "domain-transition::dm003::current-writer-handoff",
            "blocked_reason": "manuscript_story_surface_delta_missing",
        },
    }
    handoff = writer_handoff.build_writer_worker_handoff(
        profile=profile,
        study_id=study_id,
        quest_id=quest_id,
        schema_version=1,
        source_eval_id=source_eval_id,
        source_eval_artifact_path=str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        source_summary_artifact_path=None,
        repair_execution_evidence_path=(
            study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
        ),
        blocked_repair_reason="manuscript_story_surface_delta_missing",
        authority_route_context={
            "current_owner_route": current_route,
            "controller_route_context": {
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": "domain-transition::dm003::current-writer-handoff",
                "required_output_surface": (
                    "canonical manuscript story-surface delta or "
                    "typed blocker:manuscript_story_surface_delta_missing"
                ),
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {"eval_id": source_eval_id, "study_id": study_id, "quest_id": quest_id},
    )
    _write_json(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json",
        {
            "schema_version": 1,
            "status": "handoff_ready",
            "source_eval_id": source_eval_id,
            "study_id": study_id,
            "quest_id": quest_id,
            "next_owner": "write",
            "writer_worker_handoff": handoff,
        },
    )
    stale_reviewer_route = dict(current_route)
    stale_reviewer_route.update(
        {
            "current_owner": "mas_controller",
            "next_owner": "ai_reviewer",
            "owner_reason": "ai_reviewer_record_stale_after_current_inputs",
            "failure_signature": "ai_reviewer_record_stale_after_current_inputs",
            "allowed_actions": ["return_to_ai_reviewer_workflow"],
            "blocked_actions": ["run_quality_repair_batch", "run_gate_clearing_batch"],
            "idempotency_key": "owner-route::003::stale-ai-reviewer-receipt",
            "source_refs": {
                **current_route["source_refs"],
                "work_unit_id": stale_reviewer_work_unit,
                "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
            },
        }
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
                    "owner_route": stale_reviewer_route,
                    "domain_transition": {
                        "decision_type": "ai_reviewer_re_eval",
                        "route_target": "review",
                        "controller_action": "return_to_ai_reviewer_workflow",
                        "next_work_unit": {
                            "unit_id": stale_reviewer_work_unit,
                            "lane": "review",
                        },
                        "completion_receipt_consumption": {
                            "status": "consumed",
                            "receipt_kind": "ai_reviewer_publication_eval",
                            "eval_id": source_eval_id,
                        },
                    },
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "quest_id": quest_id,
                            "action_type": "return_to_ai_reviewer_workflow",
                            "owner": "ai_reviewer",
                            "request_owner": "ai_reviewer",
                            "reason": "ai_reviewer_record_stale_after_current_inputs",
                            "owner_route": stale_reviewer_route,
                        }
                    ],
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

    assert [dispatch["action_type"] for dispatch in result["owner_callable_adapters"]] == [
        "run_quality_repair_batch"
    ]
    dispatch = result["owner_callable_adapters"][0]
    assert dispatch["dispatch_authority"] == "quality_repair_batch_writer_handoff"
    assert dispatch["owner_route"]["source_refs"]["source_eval_id"] == source_eval_id
    assert dispatch["owner_route"]["source_refs"]["work_unit_id"] == work_unit_id
    assert dispatch["medical_claim_authoring_allowed"] is True
    assert result["request_tasks"][0]["action_type"] == "run_quality_repair_batch"
    assert result["request_tasks"][0]["reason"] == "manuscript_story_surface_delta_missing"
    assert result["ignored_actions"][0]["reason"] == "superseded_by_current_quality_repair_writer_handoff"


def _writer_handoff(*, study_id: str, dispatch_path: Path, route: dict[str, object]) -> dict[str, object]:
    required_output = (
        "canonical manuscript story-surface delta or "
        "typed blocker:manuscript_story_surface_delta_missing"
    )
    return {
        "surface": "default_executor_dispatch_request",
        "schema_version": 1,
        "executor_kind": "codex_cli_default",
        "chat_completion_only_executor_forbidden": True,
        "dispatch_status": "ready",
        "dispatch_authority": "quality_repair_batch_writer_handoff",
        "study_id": study_id,
        "quest_id": "quest-dm002",
        "action_type": "run_quality_repair_batch",
        "action_id": "quality-repair-writer-handoff::dm002::latest",
        "next_executable_owner": "write",
        "required_output_surface": required_output,
        "owner_route": route,
        "idempotency_key": route["idempotency_key"],
        "repeat_suppression_key": route["work_unit_fingerprint"],
        "medical_claim_authoring_allowed": True,
        "prompt_contract": {
            "study_id": study_id,
            "quest_id": "quest-dm002",
            "action_type": "run_quality_repair_batch",
            "next_executable_owner": "write",
            "required_output_surface": required_output,
            "owner_route": route,
            "idempotency_key": route["idempotency_key"],
            "prompt_budget": {"max_prompt_tokens": 6000},
            "compact_evidence_packet_ref": "artifacts/supervision/compact_evidence_packets/run_quality_repair_batch.json",
            "do_not_repeat": True,
            "repeat_suppression_key": route["work_unit_fingerprint"],
            "request_packet_ref": "artifacts/supervision/requests/quality_repair_batch/latest.json",
            "forbidden_surfaces": [
                "manuscript/**",
                "current_package/**",
                "paper/current_package/**",
                "manuscript/current_package/**",
                "src/med_autoscience/platform/**",
                "artifacts/publication_eval/latest.json",
                "artifacts/controller_decisions/latest.json",
            ],
            "allowed_write_surfaces": [
                "paper/draft.md",
                "paper/build/review_manuscript.md",
                "paper/claim_evidence_map.json",
                "paper/evidence_ledger.json",
                "paper/review/**",
            ],
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "manual_study_patch_allowed": False,
            "medical_claim_authoring_allowed": True,
        },
        "source_action": {
            "surface": "quality_repair_batch",
            "blocked_reason": "manuscript_story_surface_delta_missing",
            "next_work_unit": {"unit_id": "dm002_same_line_methods_display_package_repair", "lane": "write"},
        },
        "refs": {"dispatch_path": str(dispatch_path)},
    }
