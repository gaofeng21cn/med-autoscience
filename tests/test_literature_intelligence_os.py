from __future__ import annotations

import importlib
from pathlib import Path


def _complete_payload() -> dict[str, object]:
    return {
        "search_strategy": {
            "query": "Pituitary neuroendocrine tumor invasive architecture",
            "mesh_terms": ["Pituitary Neoplasms", "Biomarkers"],
        },
        "search_date": "2026-05-03",
        "searched_sources": ["pubmed:query-run-2026-05-03", "guideline:trpod-ai"],
        "anchor_papers": ["pmid:anchor-1"],
        "guidelines": ["guideline:TRIPOD+AI"],
        "systematic_reviews": ["doi:10.1000/systematic-review"],
        "journal_neighbor_refs": ["journal-neighbor:clinical-endocrinology-2025"],
        "screening_decisions": [
            {
                "ref": "pmid:anchor-1",
                "decision": "include",
                "reason": "Defines the clinical anchor and endpoint context.",
            },
            {
                "ref": "pmid:off-topic",
                "decision": "exclude",
                "reason": "Wrong population for the target claim.",
            },
        ],
        "citation_ledger_refs": ["paper/evidence_ledger.json#anchor-1"],
    }


def test_literature_intelligence_os_materializes_complete_ready_surface(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.literature_intelligence_os")
    study_root = tmp_path / "study"

    result = module.materialize_literature_intelligence_os(
        study_root=study_root,
        payload=_complete_payload(),
    )

    assert result["status"] == "ready"
    assert result["missing_reason"] == ""
    assert result["artifact_path"].endswith("artifacts/medical_paper/literature_intelligence_os.json")
    assert result["quality_claim_authorized"] is False
    assert result["mechanical_projection_can_authorize_quality"] is False

    read_model = module.read_literature_intelligence_os(study_root=study_root)
    assert read_model["surface"] == "literature_intelligence_os"
    assert read_model["status"] == "ready"
    assert read_model["search_strategy"]["query"] == "Pituitary neuroendocrine tumor invasive architecture"
    assert read_model["quality_claim_authorized"] is False
    assert read_model["mechanical_projection_can_authorize_quality"] is False

    summary = module.build_literature_intelligence_os_summary(study_root=study_root)
    assert summary["status"] == "ready"
    assert summary["coverage"] == {
        "searched_source_count": 2,
        "anchor_paper_count": 1,
        "guideline_count": 1,
        "systematic_review_count": 1,
        "journal_neighbor_ref_count": 1,
        "screening_decision_count": 2,
        "citation_ledger_ref_count": 1,
    }
    assert summary["quality_claim_authorized"] is False
    assert summary["mechanical_projection_can_authorize_quality"] is False


def test_literature_intelligence_os_fails_closed_when_network_sources_are_missing(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.literature_intelligence_os")
    payload = _complete_payload()
    payload["searched_sources"] = []

    result = module.materialize_literature_intelligence_os(
        study_root=tmp_path / "study",
        payload=payload,
    )

    assert result["status"] == "blocked"
    assert result["missing_reason"] == "missing_searched_sources"
    read_model = module.read_literature_intelligence_os(study_root=tmp_path / "study")
    assert read_model["status"] == "blocked"
    assert read_model["quality_claim_authorized"] is False
    assert read_model["mechanical_projection_can_authorize_quality"] is False


def test_literature_intelligence_os_fails_closed_when_citation_refs_are_missing(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.literature_intelligence_os")
    payload = _complete_payload()
    payload["citation_ledger_refs"] = []

    result = module.materialize_literature_intelligence_os(
        study_root=tmp_path / "study",
        payload=payload,
    )

    assert result["status"] == "blocked"
    assert result["missing_reason"] == "missing_citation_ledger_refs"
    summary = module.build_literature_intelligence_os_summary(study_root=tmp_path / "study")
    assert summary["status"] == "blocked"
    assert summary["quality_claim_authorized"] is False
    assert summary["mechanical_projection_can_authorize_quality"] is False


def test_literature_intelligence_os_requires_screening_reason(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.literature_intelligence_os")
    payload = _complete_payload()
    payload["screening_decisions"] = [
        {"ref": "pmid:anchor-1", "decision": "include", "reason": ""},
    ]

    result = module.materialize_literature_intelligence_os(
        study_root=tmp_path / "study",
        payload=payload,
    )

    assert result["status"] == "blocked"
    assert result["missing_reason"] == "missing_screening_decision_reason"
    read_model = module.read_literature_intelligence_os(study_root=tmp_path / "study")
    assert read_model["status"] == "blocked"


def test_literature_intelligence_os_summary_fails_closed_without_canonical_artifact(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.literature_intelligence_os")

    summary = module.build_literature_intelligence_os_summary(study_root=tmp_path / "study")

    assert summary["status"] == "blocked"
    assert summary["missing_reason"] == "missing_canonical_artifact"
    assert summary["artifact_path"].endswith("artifacts/medical_paper/literature_intelligence_os.json")
    assert summary["quality_claim_authorized"] is False
    assert summary["mechanical_projection_can_authorize_quality"] is False
