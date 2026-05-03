from __future__ import annotations

import importlib
import json
from pathlib import Path


def _provider_payload() -> dict[str, object]:
    return {
        "search_strategy": {"query": "diabetes mortality prediction", "mesh_terms": ["Diabetes Mellitus"]},
        "search_date": "2026-05-04",
        "providers": [
            {
                "provider_name": "pubmed",
                "query": "diabetes mortality prediction",
                "retrieved_at": "2026-05-04T01:00:00+08:00",
                "source_refs": ["pubmed:query:001"],
                "items": [
                    {"category": "anchor_papers", "ref": "pmid:1"},
                    {"category": "guidelines", "ref": "guideline:tripod-ai"},
                    {"category": "systematic_reviews", "ref": "pmid:review"},
                    {"category": "journal_neighbor_refs", "ref": "journal:neighbor"},
                ],
            }
        ],
        "screening_decisions": [{"decision": "include", "reason": "same endpoint"}],
        "citation_ledger_refs": ["paper/citation_ledger.json"],
    }


def _candidate() -> dict[str, object]:
    return {
        "line_id": "transportable-risk-model",
        "dimensions": {
            "novelty": 4,
            "clinical_relevance": 5,
            "data_fit": 5,
            "external_validation": 4,
            "analysis_feasibility": 4,
            "journal_fit": 4,
            "risk_cost": 1,
            "stop_threshold": "stop if external validation unavailable",
        },
        "evidence_refs": ["artifacts/medical_paper/literature_provider_runtime.json"],
    }


def test_v2_materializer_dispatch_materializes_provider_and_route_surfaces(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_paper_v2_materializers")
    study_root = tmp_path / "study"

    literature = module.materialize_medical_paper_v2_surface(
        study_root=study_root,
        surface_key="literature_provider_runtime",
        payload=_provider_payload(),
    )
    route = module.materialize_medical_paper_v2_surface(
        study_root=study_root,
        surface_key="route_decision_orchestrator",
        payload={
            "candidates": [_candidate()],
            "requested_action": "select_line",
            "readiness": {"literature_status": "ready"},
        },
    )

    assert literature["status"] == "ready"
    assert literature["artifact_path"].endswith("artifacts/medical_paper/literature_provider_runtime.json")
    assert route["status"] == "ready"
    assert route["artifact_path"].endswith("artifacts/medical_paper/route_decision_orchestrator.json")
    controller_decision = study_root / "artifacts" / "controller_decisions" / "latest.json"
    assert controller_decision.is_file()
    written = json.loads(controller_decision.read_text(encoding="utf-8"))
    assert written["decision_type"] == "study_line_route_decision"
    assert written["selected_line_id"] == "transportable-risk-model"
    assert written["quality_claim_authorized"] is False


def test_v2_materializer_fails_closed_for_missing_inputs(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_paper_v2_materializers")

    result = module.materialize_medical_paper_v2_surface(
        study_root=tmp_path / "study",
        surface_key="literature_provider_runtime",
        payload={"providers": []},
    )

    assert result["status"] == "blocked"
    assert result["missing_reason"] == "missing_provider_sources"
    assert result["quality_claim_authorized"] is False
    assert result["mechanical_projection_can_authorize_quality"] is False


def test_v2_materializer_dispatch_rejects_unknown_surface(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_paper_v2_materializers")

    result = module.materialize_medical_paper_v2_surface(
        study_root=tmp_path / "study",
        surface_key="unknown_surface",
        payload={},
    )

    assert result["status"] == "blocked"
    assert result["missing_reason"] == "unsupported_surface_unknown_surface"
    assert result["artifact_path"] == ""
