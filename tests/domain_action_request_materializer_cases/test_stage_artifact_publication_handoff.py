from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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

    assert [item["action_type"] for item in result["default_executor_dispatches"]] == [
        "publication_handoff_owner_gate"
    ]
    dispatch = result["default_executor_dispatches"][0]
    assert dispatch["dispatch_status"] == "ready"
    assert dispatch["next_executable_owner"] == "publication_gate_owner"
    assert dispatch["owner_route"]["next_owner"] == "publication_gate_owner"
    assert dispatch["owner_route"]["allowed_actions"] == ["publication_handoff_owner_gate"]
    assert dispatch["prompt_contract"]["request_packet_ref"] == (
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
        / "default_executor_dispatches"
        / "publication_handoff_owner_gate.json"
    )
    assert request_path.is_file()
    assert persisted_dispatch_path.is_file()


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
    dispatch = result["default_executor_dispatches"][0]
    request_ref = "artifacts/supervision/requests/medical_paper_readiness/latest.json"
    request_path = study_root / request_ref
    persisted_dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "complete_medical_paper_readiness_surface.json"
    )
    assert task["dispatch_status"] == "applied"
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
    persisted_request = json.loads(request_path.read_text(encoding="utf-8"))
    assert persisted_request["operator_payload_present"] is True
    assert persisted_request["readiness_surface_identity"] == task["readiness_surface_identity"]
    assert persisted_request["operator_payload"]["provider_payloads"][1]["provider"] == "crossref"
    assert dispatch["dispatch_status"] == "ready"
    assert dispatch["readiness_surface_identity"] == task["readiness_surface_identity"]
    assert dispatch["surface_key"] == "literature_provider_runtime"
    assert dispatch["operator_payload_present"] is True
    assert dispatch["operator_payload"]["provider_payloads"][2]["provider"] == "semantic_scholar"
    assert dispatch["operator_payload_ref"] == request_ref
    assert dispatch["prompt_contract"]["surface_key"] == "literature_provider_runtime"
    assert dispatch["prompt_contract"]["readiness_surface_identity"] == task["readiness_surface_identity"]
    assert dispatch["prompt_contract"]["operator_payload_present"] is True
    assert dispatch["prompt_contract"]["operator_payload"]["payload_source"] == (
        "medical_paper_readiness_owner_payload_authoring"
    )
    assert dispatch["prompt_contract"]["operator_payload_ref"] == request_ref
    assert dispatch["prompt_contract"]["payload_authoring_target"]["surface_key"] == "literature_provider_runtime"
    assert request_path.is_file()
    assert persisted_dispatch_path.is_file()
    persisted_dispatch = json.loads(persisted_dispatch_path.read_text(encoding="utf-8"))
    immutable_dispatch_path = Path(persisted_dispatch["refs"]["immutable_dispatch_path"])
    assert persisted_dispatch["readiness_surface_identity"] == task["readiness_surface_identity"]
    assert persisted_dispatch["prompt_contract"]["readiness_surface_identity"] == task["readiness_surface_identity"]
    assert immutable_dispatch_path.is_file()
    immutable_dispatch = json.loads(immutable_dispatch_path.read_text(encoding="utf-8"))
    assert immutable_dispatch["readiness_surface_identity"] == task["readiness_surface_identity"]
    assert immutable_dispatch["surface_key"] == "literature_provider_runtime"
    assert immutable_dispatch["prompt_contract"]["readiness_surface_identity"] == task["readiness_surface_identity"]
    assert immutable_dispatch["prompt_contract"]["surface_key"] == "literature_provider_runtime"
