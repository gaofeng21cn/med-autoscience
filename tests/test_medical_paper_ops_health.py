from __future__ import annotations

import importlib
import json


AUTHORITY_FALSE_KEYS = (
    "can_authorize_quality",
    "can_authorize_submission",
    "can_authorize_finalize",
    "mechanical_projection_can_authorize_quality",
)


def assert_projection_authority_false(payload: object, *, path: str = "payload") -> None:
    if isinstance(payload, dict):
        authority_contract = payload.get("authority_contract")
        if isinstance(authority_contract, dict):
            for key in AUTHORITY_FALSE_KEYS:
                assert authority_contract.get(key) is False, f"{path}.authority_contract.{key}"
        if "quality_claim_authorized" in payload:
            assert payload["quality_claim_authorized"] is False, f"{path}.quality_claim_authorized"
        if "mechanical_projection_can_authorize_quality" in payload:
            assert payload["mechanical_projection_can_authorize_quality"] is False, (
                f"{path}.mechanical_projection_can_authorize_quality"
            )
        for key, value in payload.items():
            assert_projection_authority_false(value, path=f"{path}.{key}")
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            assert_projection_authority_false(value, path=f"{path}[{index}]")


def _readiness(*, provider_status: str = "present") -> dict[str, object]:
    return {
        "surface": "medical_paper_readiness",
        "overall_status": "blocked",
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "capability_surfaces": [
            {
                "surface_key": "literature_provider_runtime",
                "status": provider_status,
                "missing_reason": "" if provider_status == "present" else "provider_partial_outage_pubmed",
                "artifact_path": "artifacts/medical_paper/literature_provider_runtime.json",
                "evidence_refs": ["artifacts/medical_paper/literature_provider_runtime.json"],
                "required_for_ready": True,
                "provider_health": {
                    "status": "ready" if provider_status == "present" else "blocked",
                    "checks": ["credential_status", "cache_age"],
                    "diagnostics": []
                    if provider_status == "present"
                    else [{"reason_code": "provider_partial_outage_pubmed"}],
                    "cache_freshness": {"pubmed": {"status": "fresh"}},
                    "citation_ledger": {"complete": provider_status == "present"},
                    "screening_reasons": {"complete": provider_status == "present"},
                },
            },
            {
                "surface_key": "real_workspace_soak_monitor",
                "status": "partial",
                "missing_reason": "finalize rebuild proof stale",
                "artifact_path": "artifacts/runtime/soak_monitor.json",
                "evidence_refs": ["artifacts/runtime/soak_monitor.json"],
                "required_for_ready": True,
                "overall_status": "partial",
                "last_green_at": "2026-05-04T01:00:00Z",
                "last_green_scan_id": "scan-001",
                "drift_history": [
                    {"scan_id": "scan-001", "scan_started_at": "2026-05-04T01:00:00Z", "overall_status": "ready"},
                    {
                        "scan_id": "scan-002",
                        "scan_started_at": "2026-05-04T01:05:00Z",
                        "required_for_ready": True,
                "overall_status": "partial",
                        "next_action": "materialize_finalize_rebuild_proof",
                        "blocked_reason_summary": [
                            {"study_id": "001-risk", "blocked_reason": "finalize rebuild proof stale"}
                        ],
                        "stop_loss_triggered": True,
                    },
                ],
            },
            {
                "surface_key": "statistical_discipline_operations",
                "status": "blocked",
                "missing_reason": "missing_external_validation_plan",
                "artifact_path": "artifacts/medical_paper/statistical_discipline_operations.json",
                "evidence_refs": ["artifacts/medical_paper/statistical_discipline_operations.json"],
                "required_for_ready": True,
                "blockers": ["missing_external_validation_plan"],
                "guideline_pack": {"guideline_families": ["TRIPOD", "TRIPOD-AI"]},
                "evidence_contract": {"external_validation_plan": {"waiver_allowed": False}},
                "primary_evidence_rule": "AUC-only cannot be used as primary evidence.",
            },
            {
                "surface_key": "ai_reviewer_outcome_learning_regression",
                "status": "blocked",
                "missing_reason": "weak_external_validation",
                "required_for_ready": True,
                "required_calibration_refs": ["ai_reviewer_calibration_corpus#weak_external_validation"],
                "missing_required_failure_modes": ["weak_external_validation"],
                "planning_mode": "pre_draft_planning_only",
            },
        ],
    }


def test_medical_paper_ops_health_aggregates_v5_operational_truth_without_authority() -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_paper_ops_health")

    payload = module.build_medical_paper_ops_health(_readiness())

    assert payload["surface"] == "medical_paper_ops_health"
    assert payload["read_model"] == "medical_paper_ops_health_read_model"
    assert payload["overall_status"] == "blocked"
    assert payload["last_green_at"] == "2026-05-04T01:00:00Z"
    assert payload["next_operator_action"] == {
        "health_key": "operator_replay_health",
        "summary": "replay_or_dispatch_guarded_operator_actions",
        "missing_reason": "operator_replay_actions_pending",
    }
    assert payload["authority_contract"] == {
        "authority": "observability_projection_only",
        "read_model_only": True,
        "can_authorize_quality": False,
        "can_authorize_submission": False,
        "can_authorize_finalize": False,
        "mechanical_projection_can_authorize_quality": False,
    }
    assert payload["quality_claim_authorized"] is False
    assert payload["mechanical_projection_can_authorize_quality"] is False
    assert payload["health"]["provider_health"]["status"] == "ready"
    assert payload["health"]["soak_drift_health"]["details"]["drift_history_count"] == 2
    assert payload["health"]["outcome_learning_health"]["details"]["required_calibration_refs"] == [
        "ai_reviewer_calibration_corpus#weak_external_validation"
    ]
    assert payload["health"]["stat_guideline_health"]["details"]["guideline_families"] == [
        "TRIPOD",
        "TRIPOD-AI",
    ]
    assert_projection_authority_false(payload)


def test_workspace_medical_paper_ops_health_counts_studies_and_preserves_last_green() -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_paper_ops_health")

    workspace = module.workspace_medical_paper_ops_health(
        [
            {"study_id": "001-risk", "medical_paper_readiness": _readiness()},
            {"study_id": "002-clean", "medical_paper_readiness": _readiness(provider_status="missing")},
        ]
    )

    assert workspace["surface"] == "workspace_medical_paper_ops_health"
    assert workspace["status"] == "blocked"
    assert workspace["counts"] == {"study_count": 2, "ready": 0, "partial": 0, "blocked": 2}
    assert workspace["last_green_at"] == "2026-05-04T01:00:00Z"
    assert workspace["authority_contract"]["can_authorize_quality"] is False
    assert workspace["authority_contract"]["can_authorize_submission"] is False
    assert workspace["authority_contract"]["can_authorize_finalize"] is False
    assert workspace["authority_contract"]["mechanical_projection_can_authorize_quality"] is False
    assert_projection_authority_false(workspace)


def test_readiness_materializer_cannot_persist_quality_authority_from_input_payload(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_paper_readiness")
    study_root = tmp_path / "study"

    result = module.materialize_medical_paper_readiness_surface(
        study_root=study_root,
        surface_key="target_journal_writing_layer",
        payload={
            "surface": "unsafe_input_surface",
            "schema_version": 999,
            "quality_claim_authorized": True,
            "mechanical_projection_can_authorize_quality": True,
            "authority_contract": {
                "can_authorize_quality": True,
                "can_authorize_submission": True,
                "can_authorize_finalize": True,
                "mechanical_projection_can_authorize_quality": True,
            },
        },
    )
    persisted = json.loads(
        (
            study_root
            / "paper"
            / "target_journal_writing_layer.json"
        ).read_text(encoding="utf-8")
    )

    assert result["surface"] == "target_journal_writing_layer"
    assert result["status"] == "blocked"
    assert result["quality_claim_authorized"] is False
    assert result["mechanical_projection_can_authorize_quality"] is False
    assert persisted["surface"] == "target_journal_writing_layer"
    assert persisted["schema_version"] == 1
    assert persisted["quality_claim_authorized"] is False
    assert persisted["mechanical_projection_can_authorize_quality"] is False
    assert persisted["authority_contract"] == {
        "authority": "observability_projection_only",
        "read_model_only": True,
        "can_authorize_quality": False,
        "can_authorize_submission": False,
        "can_authorize_finalize": False,
        "mechanical_projection_can_authorize_quality": False,
    }
