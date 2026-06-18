from __future__ import annotations

import importlib
import json
from pathlib import Path

from med_autoscience.controllers import stage_native_next_action_admission
from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _stage_native_admission_fields(
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


def _write_ready_literature_intelligence(study_root: Path) -> None:
    _write_json(
        study_root / "artifacts" / "medical_paper" / "literature_intelligence_os.json",
        {
            "surface": "literature_intelligence_os",
            "status": "ready",
            "search_strategy": {
                "query": "diabetes mortality prediction",
                "mesh_terms": ["Diabetes Mellitus"],
                "keywords": ["diabetes mortality", "transportability"],
            },
            "search_date": "2026-06-06",
            "why_worth_doing": "Provider-backed evidence supports the current study framing.",
            "provider_provenance": [
                {
                    "provider_name": "pubmed",
                    "query": "diabetes mortality prediction",
                    "retrieved_at": "2026-06-06T08:00:00Z",
                    "response_status": "ok",
                    "source_refs": ["artifacts/medical_paper/provider_responses/pubmed.json"],
                },
                {
                    "provider_name": "crossref",
                    "query": "diabetes mortality guideline review",
                    "retrieved_at": "2026-06-06T08:01:00Z",
                    "response_status": "ok",
                    "source_refs": ["artifacts/medical_paper/provider_responses/crossref.json"],
                },
                {
                    "provider_name": "semantic_scholar",
                    "query": "diabetes mortality clinical neighbor",
                    "retrieved_at": "2026-06-06T08:02:00Z",
                    "response_status": "ok",
                    "source_refs": ["artifacts/medical_paper/provider_responses/semantic-scholar.json"],
                },
            ],
            "anchor_papers": ["pmid:12345"],
            "guidelines": ["guideline:TRIPOD+AI"],
            "systematic_reviews": ["doi:10.1000/systematic-review"],
            "journal_neighbor_refs": ["semantic_scholar:S2PAPER1"],
            "high_score_neighbor_refs": [
                {
                    "ref": "semantic_scholar:S2PAPER1",
                    "score": 0.91,
                    "score_source_ref": "semantic_scholar:query",
                }
            ],
            "citation_ledger_refs": [
                "paper/evidence_ledger.json#pmid-12345",
                "paper/evidence_ledger.json#tripod-ai",
                "paper/evidence_ledger.json#systematic-review",
                "paper/evidence_ledger.json#semantic-S2PAPER1",
            ],
            "screening_decisions": [
                {
                    "ref": "pmid:12345",
                    "decision": "include",
                    "reason": "Study anchor.",
                }
            ],
        },
    )


def test_materialize_domain_action_requests_dispatches_stage_artifact_publication_handoff(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm002")
    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": "quest-dm002",
        "truth_epoch": "truth-epoch-dm002-terminal-handoff",
        "runtime_health_epoch": "runtime-health-epoch-dm002-terminal-handoff",
        "work_unit_fingerprint": "stage-artifact-index::08-publication_package_handoff::publication_handoff_owner_gate",
        "failure_signature": "publication_handoff_owner_gate",
        "trace_id": "owner-route-trace::dm002::publication-handoff",
        "route_epoch": "truth-epoch-dm002-terminal-handoff",
        "source_fingerprint": "truth-source-dm002-terminal-handoff",
        "current_owner": "mas_controller",
        "next_owner": "publication_gate_owner",
        "owner_reason": "publication_handoff_owner_gate",
        "active_run_id": None,
        "allowed_actions": ["publication_handoff_owner_gate"],
        "blocked_actions": [],
        "source_refs": {
            "work_unit_id": "publication_handoff_owner_gate",
            "work_unit_fingerprint": (
                "stage-artifact-index::08-publication_package_handoff::"
                "publication_handoff_owner_gate"
            ),
            "owner_route_currentness_basis": {
                "truth_epoch": "truth-epoch-dm002-terminal-handoff",
                "runtime_health_epoch": "runtime-health-epoch-dm002-terminal-handoff",
                "work_unit_id": "publication_handoff_owner_gate",
                "work_unit_fingerprint": (
                    "stage-artifact-index::08-publication_package_handoff::"
                    "publication_handoff_owner_gate"
                ),
            },
        },
        "idempotency_key": "owner-route::dm002::publication-handoff-owner-gate",
    }
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": "quest-dm002",
                    "owner_route": owner_route,
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "quest_id": "quest-dm002",
                            "action_type": "publication_handoff_owner_gate",
                            "authority": "observability_only",
                            "owner": "publication_gate_owner",
                            "request_owner": "publication_gate_owner",
                            "recommended_owner": "publication_gate_owner",
                            "reason": "publication_handoff_owner_gate",
                            "required_output_surface": (
                                "artifacts/stage_outputs/08-publication_package_handoff/"
                                "handoff_owner_receipt.json or "
                                "artifacts/stage_outputs/08-publication_package_handoff/"
                                "receipts/typed_blocker.json"
                            ),
                            "work_unit_id": "publication_handoff_owner_gate",
                            "work_unit_fingerprint": (
                                "stage-artifact-index::08-publication_package_handoff::"
                                "publication_handoff_owner_gate"
                            ),
                            "owner_route": owner_route,
                            "handoff_packet": {
                                "action_type": "publication_handoff_owner_gate",
                                "request_owner": "publication_gate_owner",
                                "recommended_owner": "publication_gate_owner",
                                "owner_route": owner_route,
                                "idempotency_key": owner_route["idempotency_key"],
                            },
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

    assert [item["action_type"] for item in result["domain_progress_transition_requests"]] == [
        "publication_handoff_owner_gate"
    ]
    dispatch = result["domain_progress_transition_requests"][0]
    assert dispatch["dispatch_status"] == "transition_request_pending"
    assert dispatch["next_executable_owner"] == "publication_gate_owner"
    assert dispatch["owner_route"]["next_owner"] == "publication_gate_owner"
    assert dispatch["owner_route"]["allowed_actions"] == ["publication_handoff_owner_gate"]
    assert dispatch["prompt_contract_ref"]["request_packet_ref"] == (
        "artifacts/supervision/requests/publication_handoff_owner_gate/latest.json"
    )
    request_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "requests"
        / "publication_handoff_owner_gate"
        / "latest.json"
    )
    persisted_dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / "publication_handoff_owner_gate.json"
    )
    assert not request_path.exists()
    assert not persisted_dispatch_path.exists()


def test_materialize_domain_action_requests_dispatches_medical_paper_readiness_payload_ref(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm002")
    _write_ready_literature_intelligence(study_root)
    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": "quest-dm002",
        "truth_epoch": "truth-epoch-dm002-readiness",
        "runtime_health_epoch": "runtime-health-epoch-dm002-readiness",
        "work_unit_fingerprint": "stage-current-owner-delta::complete_medical_paper_readiness_surface::typed-blocker",
        "failure_signature": "medical_paper_readiness_not_ready",
        "trace_id": "owner-route-trace::dm002::medical-paper-readiness",
        "route_epoch": "truth-epoch-dm002-readiness",
        "source_fingerprint": "truth-source-dm002-readiness",
        "current_owner": "mas_controller",
        "next_owner": "MedAutoScience",
        "owner_reason": "medical_paper_readiness_not_ready",
        "active_run_id": None,
        "allowed_actions": ["complete_medical_paper_readiness_surface"],
        "blocked_actions": [],
        "source_refs": {
            "work_unit_id": "complete_medical_paper_readiness_surface",
            "work_unit_fingerprint": "stage-current-owner-delta::complete_medical_paper_readiness_surface::typed-blocker",
            "owner_route_currentness_basis": {
                "truth_epoch": "truth-epoch-dm002-readiness",
                "runtime_health_epoch": "runtime-health-epoch-dm002-readiness",
                "work_unit_id": "complete_medical_paper_readiness_surface",
                "work_unit_fingerprint": "stage-current-owner-delta::complete_medical_paper_readiness_surface::typed-blocker",
            },
        },
        "idempotency_key": "owner-route::dm002::medical-paper-readiness",
    }
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": "quest-dm002",
                    "owner_route": owner_route,
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "quest_id": "quest-dm002",
                            "action_type": "complete_medical_paper_readiness_surface",
                            "authority": "mas_owner_surface",
                            "owner": "MedAutoScience",
                            "request_owner": "MedAutoScience",
                            "recommended_owner": "MedAutoScience",
                            "reason": "medical_paper_readiness_not_ready",
                            "required_output_surface": "complete_medical_paper_readiness_surface",
                            "surface_key": "literature_provider_runtime",
                            "work_unit_id": "complete_medical_paper_readiness_surface",
                            "work_unit_fingerprint": (
                                "stage-current-owner-delta::"
                                "complete_medical_paper_readiness_surface::typed-blocker"
                            ),
                            "owner_route": owner_route,
                            "handoff_packet": {
                                "action_type": "complete_medical_paper_readiness_surface",
                                "request_owner": "MedAutoScience",
                                "recommended_owner": "MedAutoScience",
                                "surface_key": "literature_provider_runtime",
                                "owner_route": owner_route,
                                "idempotency_key": owner_route["idempotency_key"],
                            },
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

    task = result["request_tasks"][0]
    dispatch = result["domain_progress_transition_requests"][0]
    request_ref = "artifacts/supervision/requests/medical_paper_readiness/latest.json"
    request_path = study_root / request_ref
    persisted_dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / "complete_medical_paper_readiness_surface.json"
    )
    assert task["dispatch_status"] == "transition_request_pending"
    assert task["readiness_surface_identity"] == {
        "action_type": "complete_medical_paper_readiness_surface",
        "surface_key": "literature_provider_runtime",
        "source": "current_owner_action",
    }
    assert task["surface_key"] == "literature_provider_runtime"
    assert task["operator_payload_ref"] == request_ref
    assert task["operator_payload_present"] is True
    assert task["operator_payload"]["payload_source"] == "medical_paper_readiness_owner_payload_authoring"
    assert task["operator_payload"]["provider_payloads"][0]["provider"] == "pubmed"
    assert task["payload_authoring_target"]["surface_key"] == "literature_provider_runtime"
    assert task["payload_authoring_target"]["operator_payload"]["payload_source"] == (
        "medical_paper_readiness_owner_payload_authoring"
    )
    assert task["payload_authoring_target"]["operator_payload_contract"]["empty_payload_is_not_success_evidence"] is True
    assert not request_path.exists()
    assert dispatch["dispatch_status"] == "transition_request_pending"
    assert dispatch["readiness_surface_identity"] == task["readiness_surface_identity"]
    assert dispatch["surface_key"] == "literature_provider_runtime"
    assert dispatch["operator_payload_present"] is True
    assert dispatch["operator_payload"]["provider_payloads"][2]["provider"] == "semantic_scholar"
    assert dispatch["operator_payload_ref"] == request_ref
    assert dispatch["prompt_contract_ref"]["surface_key"] == "literature_provider_runtime"
    assert dispatch["prompt_contract_ref"]["readiness_surface_identity"] == task["readiness_surface_identity"]
    assert dispatch["prompt_contract_ref"]["operator_payload_present"] is True
    assert dispatch["prompt_contract_ref"]["operator_payload"]["payload_source"] == (
        "medical_paper_readiness_owner_payload_authoring"
    )
    assert dispatch["prompt_contract_ref"]["operator_payload_ref"] == request_ref
    assert dispatch["prompt_contract_ref"]["payload_authoring_target"]["surface_key"] == "literature_provider_runtime"
    assert not persisted_dispatch_path.exists()


def test_materialize_prefers_stage_readiness_followup_over_stale_control_next_action(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm003")
    _write_ready_literature_intelligence(study_root)
    _write_json(
        study_root / "control" / "next_action.json",
        {
            "schema_version": 1,
            "status": "ready_for_owner_action",
            "action_id": "run_quality_repair_batch",
            "owner": "write",
            "source_surface": "control/next_action.json",
            "current_stage_id": "08-publication_package_handoff",
            "target_surface": "artifacts/reports/medical_publication_surface/latest.json",
        },
    )
    typed_blocker_ref = (
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/"
        "typed_blocker.json"
    )
    readiness_fingerprint = (
        "stage-current-owner-delta::complete_medical_paper_readiness_surface::"
        "literature_provider_runtime::"
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
    )
    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": "quest-dm003",
        "truth_epoch": "truth-epoch-dm003-readiness-followup",
        "runtime_health_epoch": "runtime-health-epoch-dm003-readiness-followup",
        "work_unit_fingerprint": readiness_fingerprint,
        "failure_signature": "medical_paper_readiness_not_ready",
        "trace_id": "owner-route-trace::dm003::medical-paper-readiness",
        "route_epoch": "truth-epoch-dm003-readiness-followup",
        "source_fingerprint": "truth-source-dm003-readiness-followup",
        "current_owner": "mas_controller",
        "next_owner": "MedAutoScience",
        "owner_reason": "medical_paper_readiness_not_ready",
        "active_run_id": None,
        "allowed_actions": ["complete_medical_paper_readiness_surface"],
        "blocked_actions": ["run_quality_repair_batch", "run_gate_clearing_batch"],
        "source_refs": {
            "work_unit_id": "complete_medical_paper_readiness_surface",
            "work_unit_fingerprint": readiness_fingerprint,
            "source_ref": typed_blocker_ref,
            "owner_route_currentness_basis": {
                "truth_epoch": "truth-epoch-dm003-readiness-followup",
                "runtime_health_epoch": "runtime-health-epoch-dm003-readiness-followup",
                "work_unit_id": "complete_medical_paper_readiness_surface",
                "work_unit_fingerprint": readiness_fingerprint,
            },
        },
        "idempotency_key": "owner-route::dm003::medical-paper-readiness-followup",
    }
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": "quest-dm003",
                    "owner_route": owner_route,
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "schema_version": 1,
                        "status": "ready",
                        "source": "stage_kernel_projection.current_owner_delta",
                        "next_owner": "MedAutoScience",
                        "work_unit_id": "complete_medical_paper_readiness_surface",
                        "allowed_actions": ["complete_medical_paper_readiness_surface"],
                        "required_delta_kind": "medical_paper_readiness_surface_or_typed_blocker",
                        "surface_key": "literature_provider_runtime",
                        "source_ref": typed_blocker_ref,
                    },
                    "action_queue": [
                        {
                            "action_type": "complete_medical_paper_readiness_surface",
                            "authority": "mas_owner_surface",
                            "owner": "MedAutoScience",
                            "request_owner": "MedAutoScience",
                            "recommended_owner": "MedAutoScience",
                            "reason": "medical_paper_readiness_not_ready",
                            "required_output_surface": "complete_medical_paper_readiness_surface",
                            "surface_key": "literature_provider_runtime",
                            "next_action": {
                                "action_id": "complete_medical_paper_readiness_surface",
                                "surface_key": "literature_provider_runtime",
                            },
                            "work_unit_id": "complete_medical_paper_readiness_surface",
                            "work_unit_fingerprint": readiness_fingerprint,
                            "source_surface": "stage_kernel_projection.current_owner_delta",
                            "source_ref": typed_blocker_ref,
                            "owner_route": owner_route,
                            "handoff_packet": {
                                "action_type": "complete_medical_paper_readiness_surface",
                                "request_owner": "MedAutoScience",
                                "recommended_owner": "MedAutoScience",
                                "surface_key": "literature_provider_runtime",
                                "source": "stage_kernel_projection.current_owner_delta",
                                "owner_route": owner_route,
                                "idempotency_key": owner_route["idempotency_key"],
                            },
                        }
                    ],
                }
            ],
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": "quest-dm003",
                    "action_type": "run_quality_repair_batch",
                    "owner": "write",
                    "request_owner": "write",
                    "recommended_owner": "write",
                    "reason": "stale_control_next_action",
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

    assert [item["action_type"] for item in result["domain_progress_transition_requests"]] == [
        "complete_medical_paper_readiness_surface"
    ]
    dispatch = result["domain_progress_transition_requests"][0]
    assert dispatch["dispatch_status"] == "transition_request_pending"
    assert dispatch["next_executable_owner"] == "MedAutoScience"
    assert dispatch["surface_key"] == "literature_provider_runtime"
    assert dispatch["owner_route"]["allowed_actions"] == ["complete_medical_paper_readiness_surface"]
    assert dispatch["source_action"]["source_ref"] == typed_blocker_ref
    assert any(
        item["reason"] == "superseded_by_current_stage_readiness_followup"
        and item["action_type"] == "run_quality_repair_batch"
        for item in result["ignored_actions"]
    )


def test_materialize_keeps_explicit_readiness_action_over_stage_native_repair_without_repair_current_action(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm003")
    repair_work_unit_fingerprint = (
        "canonical-current-work-unit::08-publication_package_handoff::"
        "medical_publication_surface_blocked_write_repair"
    )
    _write_json(
        study_root / "control" / "next_action.json",
        {
            "schema_version": 1,
            "status": "ready_for_owner_action",
            "action_id": "run_quality_repair_batch",
            "owner": "write",
            "source_surface": "artifacts/reports/medical_publication_surface/latest.json",
            "current_stage_id": "08-publication_package_handoff",
            "target_surface": "artifacts/reports/medical_publication_surface/latest.json",
            "next_work_unit": "medical_publication_surface_blocked_write_repair",
            "stage_transition_authority_boundary": {
                "stage_transition_authority": "OPL Stage Transition Authority",
                "intent_can_write_stage_current_pointer": False,
                "intent_can_write_stage_run_terminal_state": False,
                "intent_can_publish_current_owner_delta": False,
            },
            "current_work_unit_binding": {
                "source": "canonical_current_work_unit",
                "work_unit_id": "medical_publication_surface_blocked_write_repair",
                "work_unit_fingerprint": repair_work_unit_fingerprint,
            },
        },
    )
    typed_blocker_ref = (
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/"
        "typed_blocker.json"
    )
    readiness_fingerprint = (
        "stage-current-owner-delta::complete_medical_paper_readiness_surface::"
        "authoring_runtime_authorization::"
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
    )
    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": "quest-dm003",
        "truth_epoch": "truth-epoch-dm003-readiness-answer",
        "runtime_health_epoch": "runtime-health-epoch-dm003-readiness-answer",
        "work_unit_fingerprint": readiness_fingerprint,
        "failure_signature": "medical_paper_readiness_missing",
        "trace_id": "owner-route-trace::dm003::medical-paper-readiness-answer",
        "route_epoch": "truth-epoch-dm003-readiness-answer",
        "source_fingerprint": "truth-source-dm003-readiness-answer",
        "current_owner": "mas_controller",
        "next_owner": "MedAutoScience",
        "owner_reason": "medical_paper_readiness_missing",
        "active_run_id": None,
        "allowed_actions": ["complete_medical_paper_readiness_surface"],
        "blocked_actions": ["run_quality_repair_batch", "run_gate_clearing_batch"],
        "source_refs": {
            "work_unit_id": "complete_medical_paper_readiness_surface",
            "work_unit_fingerprint": readiness_fingerprint,
            "source_ref": typed_blocker_ref,
            "owner_route_currentness_basis": {
                "truth_epoch": "truth-epoch-dm003-readiness-answer",
                "runtime_health_epoch": "runtime-health-epoch-dm003-readiness-answer",
                "work_unit_id": "complete_medical_paper_readiness_surface",
                "work_unit_fingerprint": readiness_fingerprint,
            },
        },
        "idempotency_key": "owner-route::dm003::medical-paper-readiness-answer",
    }
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": "quest-dm003",
                    "owner_route": owner_route,
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "schema_version": 1,
                        "status": "ready",
                        "source": "stage_kernel_projection.current_owner_delta",
                        "next_owner": "MedAutoScience",
                        "work_unit_id": "complete_medical_paper_readiness_surface",
                        "allowed_actions": ["complete_medical_paper_readiness_surface"],
                        "required_delta_kind": "medical_paper_readiness_surface_or_typed_blocker",
                        "surface_key": "authoring_runtime_authorization",
                        "source_ref": typed_blocker_ref,
                        "latest_owner_answer_kind": "typed_blocker",
                        "artifact_first_precedence": {
                            "reason": "medical_paper_readiness_missing",
                            "typed_blocker_followup_takes_precedence": True,
                        },
                    },
                    "action_queue": [
                        {
                            "action_type": "complete_medical_paper_readiness_surface",
                            "authority": "mas_owner_surface",
                            "owner": "MedAutoScience",
                            "request_owner": "MedAutoScience",
                            "recommended_owner": "MedAutoScience",
                            "reason": "medical_paper_readiness_missing",
                            "required_output_surface": "complete_medical_paper_readiness_surface",
                            "surface_key": "authoring_runtime_authorization",
                            "next_action": {
                                "action_id": "complete_medical_paper_readiness_surface",
                                "surface_key": "authoring_runtime_authorization",
                            },
                            "work_unit_id": "complete_medical_paper_readiness_surface",
                            "work_unit_fingerprint": readiness_fingerprint,
                            "source_surface": "stage_kernel_projection.current_owner_delta",
                            "source_ref": typed_blocker_ref,
                            "owner_route": owner_route,
                        }
                    ],
                }
            ],
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": "quest-dm003",
                    "action_type": "complete_medical_paper_readiness_surface",
                    "owner": "MedAutoScience",
                    "reason": "medical_paper_readiness_missing",
                }
            ],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert [item["action_type"] for item in result["domain_progress_transition_requests"]] == [
        "complete_medical_paper_readiness_surface"
    ]
    dispatch = result["domain_progress_transition_requests"][0]
    assert dispatch["next_executable_owner"] == "MedAutoScience"
    source_action = dispatch["source_action"]
    assert source_action["authority"] == "mas_owner_surface"
    assert dispatch["owner_route"]["source_refs"]["work_unit_id"] == "complete_medical_paper_readiness_surface"
    assert dispatch["owner_route"]["work_unit_fingerprint"] == readiness_fingerprint
    assert any(
        item["reason"]
        == "stage_native_workspace_next_action_requires_current_work_unit_currentness_match"
        and item["action_type"] == "run_quality_repair_batch"
        for item in result["ignored_actions"]
    )


def test_materialize_prefers_readiness_blocker_derived_repair_over_old_readiness_queue(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    write_study(profile.workspace_root, study_id, quest_id="quest-dm003")
    old_readiness_fingerprint = (
        "stage-current-owner-delta::complete_medical_paper_readiness_surface::"
        "authoring_runtime_authorization::"
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
    )
    repair_fingerprint = (
        "readiness-blocker-repair::publication-eval::dm003::readiness-blocker-gaps::"
        "medical_publication_surface_blocked+reviewer_first_concerns_unresolved+"
        "stale_submission_minimal_authority"
    )
    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": "quest-dm003",
        "truth_epoch": "truth-epoch-dm003-readiness-repair",
        "runtime_health_epoch": "runtime-health-epoch-dm003-readiness-repair",
        "work_unit_fingerprint": repair_fingerprint,
        "failure_signature": "medical_paper_readiness_repair_required",
        "trace_id": "owner-route-trace::dm003::readiness-repair",
        "route_epoch": "truth-epoch-dm003-readiness-repair",
        "source_fingerprint": "truth-source-dm003-readiness-repair",
        "current_owner": "mas_controller",
        "next_owner": "write",
        "owner_reason": "medical_paper_readiness_repair_required",
        "active_run_id": None,
        "allowed_actions": ["run_quality_repair_batch"],
        "blocked_actions": ["complete_medical_paper_readiness_surface"],
        "source_refs": {
            "work_unit_id": "readiness_blocker_publication_repair",
            "work_unit_fingerprint": repair_fingerprint,
            "source_ref": "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
            "owner_route_currentness_basis": {
                "truth_epoch": "truth-epoch-dm003-readiness-repair",
                "runtime_health_epoch": "runtime-health-epoch-dm003-readiness-repair",
                "work_unit_id": "readiness_blocker_publication_repair",
                "work_unit_fingerprint": repair_fingerprint,
            },
        },
        "idempotency_key": "owner-route::dm003::readiness-repair",
    }
    repair_action = {
        "study_id": study_id,
        "quest_id": "quest-dm003",
        "action_type": "run_quality_repair_batch",
        "authority": "observability_only",
        "owner": "write",
        "request_owner": "write",
        "recommended_owner": "write",
        "reason": "medical_paper_readiness_repair_required",
        "required_output_surface": (
            "canonical manuscript story-surface delta, claim-evidence semantic delta, "
            "reviewer/gate delta, or typed blocker:readiness_blocker_publication_repair_required"
        ),
        "next_work_unit": "readiness_blocker_publication_repair",
        "executable_work_unit": "readiness_blocker_publication_repair",
        "controller_work_unit_id": "readiness_blocker_publication_repair",
        "work_unit_fingerprint": repair_fingerprint,
        "source_surface": "stage_kernel_projection.current_owner_delta",
        "source_ref": "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
        "readiness_blocker_followup_superseded": "complete_medical_paper_readiness_surface",
        "publication_eval_gap_ids": [
            "stale_submission_minimal_authority",
            "medical_publication_surface_blocked",
            "reviewer_first_concerns_unresolved",
        ],
        "owner_route": owner_route,
    }
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": "quest-dm003",
                    "owner_route": owner_route,
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "schema_version": 1,
                        "status": "ready",
                        "source": "stage_kernel_projection.current_owner_delta",
                        "next_owner": "write",
                        "work_unit_id": "readiness_blocker_publication_repair",
                        "allowed_actions": ["run_quality_repair_batch"],
                        "required_delta_kind": "paper_product_semantic_delta_or_concrete_typed_blocker",
                        "source_ref": (
                            "artifacts/stage_outputs/08-publication_package_handoff/"
                            "receipts/typed_blocker.json"
                        ),
                    },
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "quest_id": "quest-dm003",
                            "action_type": "complete_medical_paper_readiness_surface",
                            "owner": "MedAutoScience",
                            "reason": "medical_paper_readiness_missing",
                            "surface_key": "authoring_runtime_authorization",
                            "work_unit_id": "complete_medical_paper_readiness_surface",
                            "work_unit_fingerprint": old_readiness_fingerprint,
                        },
                        repair_action,
                    ],
                }
            ],
        },
    )

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
    assert dispatch["next_executable_owner"] == "write"
    assert dispatch["source_action"]["next_work_unit"] == "readiness_blocker_publication_repair"
    assert dispatch["source_action"]["readiness_blocker_followup_superseded"] == (
        "complete_medical_paper_readiness_surface"
    )
    assert any(
        item["reason"] == "superseded_by_readiness_blocker_derived_repair"
        and item["action_type"] == "complete_medical_paper_readiness_surface"
        for item in result["ignored_actions"]
    )
