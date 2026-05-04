from __future__ import annotations

import importlib
from pathlib import Path


def _complete_payload() -> dict[str, object]:
    return {
        "study_id": "003-invasive-architecture",
        "search_strategy": {
            "query": "Pituitary neuroendocrine tumor invasive architecture",
            "mesh_terms": ["Pituitary Neoplasms", "Biomarkers"],
            "keywords": ["invasive architecture", "pituitary neuroendocrine tumor"],
        },
        "search_date": "2026-05-03",
        "searched_sources": ["pubmed:query-run-2026-05-03", "guideline:trpod-ai"],
        "provider_provenance": [
            {
                "provider_name": "pubmed",
                "query": "pituitary neuroendocrine tumor invasive architecture",
                "retrieved_at": "2026-05-03T08:00:00Z",
                "response_status": "ok",
                "source_refs": ["pubmed:query-run-2026-05-03"],
            }
        ],
        "why_worth_doing": "Guideline-bound evidence and recent neighboring papers support the study question.",
        "anchor_papers": ["pmid:anchor-1"],
        "guidelines": ["guideline:TRIPOD+AI"],
        "systematic_reviews": ["doi:10.1000/systematic-review"],
        "journal_neighbor_refs": ["journal-neighbor:clinical-endocrinology-2025"],
        "high_score_neighbor_refs": [
            {
                "ref": "journal-neighbor:clinical-endocrinology-2025",
                "score": 0.91,
                "score_source_ref": "semantic-scholar:query-run-2026-05-03",
            }
        ],
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
        "evidence_nodes": [
            {
                "node_id": "anchor-invasive-pattern",
                "claim": "Invasive architecture is clinically relevant for pituitary tumor characterization.",
                "pmid": "12345678",
                "source_ref": "pubmed:query-run-2026-05-03#12345678",
                "evidence_type": "anchor_paper",
            },
            {
                "node_id": "guideline-reporting",
                "claim": "Prediction or reporting claims require transparent citation grounding.",
                "guideline_ref": "guideline:TRIPOD+AI",
                "evidence_type": "guideline",
            },
        ],
        "perspective_questions": [
            {
                "question": "Which invasion definitions are clinically stable enough to anchor the study claim?",
                "source_refs": ["pmid:12345678"],
            }
        ],
        "contradiction_flags": [
            {
                "flag_id": "definition-heterogeneity",
                "signal": "Different studies use non-identical invasion definitions.",
                "evidence_refs": ["pmid:12345678", "guideline:TRIPOD+AI"],
                "review_signal_only": True,
            }
        ],
        "metadata_quality": {
            "pmid_coverage": "partial",
            "doi_coverage": "partial",
            "guideline_ref_coverage": "present",
        },
        "citation_grounding": {
            "grounded_node_count": 2,
            "ungrounded_node_count": 0,
            "ledger_refs": ["paper/evidence_ledger.json#anchor-1"],
        },
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
    assert read_model["schema_version"] == 1
    assert read_model["study_id"] == "003-invasive-architecture"
    assert read_model["search_strategy"]["query"] == "Pituitary neuroendocrine tumor invasive architecture"
    assert read_model["source_coverage"] == {
        "searched_source_count": 2,
        "provider_provenance_count": 1,
        "anchor_paper_count": 1,
        "guideline_count": 1,
        "systematic_review_count": 1,
        "journal_neighbor_ref_count": 1,
        "high_score_neighbor_ref_count": 1,
        "citation_ledger_ref_count": 1,
        "evidence_node_count": 2,
        "perspective_question_count": 1,
        "contradiction_flag_count": 1,
    }
    assert read_model["evidence_nodes"][0]["pmid"] == "12345678"
    assert read_model["perspective_questions"][0]["question"].startswith("Which invasion definitions")
    assert read_model["contradiction_flags"][0]["review_signal_only"] is True
    assert read_model["metadata_quality"]["guideline_ref_coverage"] == "present"
    assert read_model["citation_grounding"]["ungrounded_node_count"] == 0
    assert read_model["authority"] == {
        "can_authorize_publication_quality": False,
        "can_authorize_submission": False,
        "can_authorize_finalize": False,
        "contradiction_flags_authority": "evidence_review_signal_only",
    }
    assert read_model["quality_claim_authorized"] is False
    assert read_model["mechanical_projection_can_authorize_quality"] is False

    summary = module.build_literature_intelligence_os_summary(study_root=study_root)
    assert summary["status"] == "ready"
    assert summary["coverage"] == {
        "searched_source_count": 2,
        "provider_provenance_count": 1,
        "anchor_paper_count": 1,
        "guideline_count": 1,
        "systematic_review_count": 1,
        "journal_neighbor_ref_count": 1,
        "high_score_neighbor_ref_count": 1,
        "screening_decision_count": 2,
        "citation_ledger_ref_count": 1,
        "evidence_node_count": 2,
        "perspective_question_count": 1,
        "contradiction_flag_count": 1,
    }
    assert summary["quality_claim_authorized"] is False
    assert summary["mechanical_projection_can_authorize_quality"] is False
    assert summary["authority"]["can_authorize_publication_quality"] is False


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
    assert result["diagnostics"] == [
        {
            "reason_code": "missing_searched_sources",
            "severity": "blocking",
            "category": "source_readiness",
        }
    ]
    read_model = module.read_literature_intelligence_os(study_root=tmp_path / "study")
    assert read_model["status"] == "blocked"
    assert read_model["diagnostics"] == result["diagnostics"]
    assert read_model["quality_claim_authorized"] is False
    assert read_model["mechanical_projection_can_authorize_quality"] is False


def test_literature_intelligence_os_fails_closed_when_search_date_is_missing(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.literature_intelligence_os")
    payload = _complete_payload()
    payload["search_date"] = ""

    result = module.materialize_literature_intelligence_os(
        study_root=tmp_path / "study",
        payload=payload,
    )

    assert result["status"] == "blocked"
    assert result["missing_reason"] == "missing_search_date"
    assert result["diagnostics"] == [
        {
            "reason_code": "missing_search_date",
            "severity": "blocking",
            "category": "search_readiness",
        }
    ]


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
    assert result["diagnostics"] == [
        {
            "reason_code": "missing_citation_ledger_refs",
            "severity": "blocking",
            "category": "citation_readiness",
        }
    ]
    summary = module.build_literature_intelligence_os_summary(study_root=tmp_path / "study")
    assert summary["status"] == "blocked"
    assert summary["diagnostics"] == result["diagnostics"]
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
    assert result["diagnostics"] == [
        {
            "reason_code": "missing_screening_decision_reason",
            "severity": "blocking",
            "category": "screening_readiness",
        }
    ]
    read_model = module.read_literature_intelligence_os(study_root=tmp_path / "study")
    assert read_model["status"] == "blocked"


def test_literature_intelligence_os_requires_keywords_and_study_rationale(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.literature_intelligence_os")
    payload = _complete_payload()
    payload["search_strategy"] = {
        "query": "Pituitary neuroendocrine tumor invasive architecture",
        "mesh_terms": ["Pituitary Neoplasms", "Biomarkers"],
    }

    result = module.materialize_literature_intelligence_os(
        study_root=tmp_path / "study",
        payload=payload,
    )

    assert result["status"] == "blocked"
    assert result["missing_reason"] == "missing_keyword_terms"

    payload = _complete_payload()
    payload["why_worth_doing"] = ""

    result = module.materialize_literature_intelligence_os(
        study_root=tmp_path / "study",
        payload=payload,
    )

    assert result["status"] == "blocked"
    assert result["missing_reason"] == "missing_study_rationale"


def test_literature_intelligence_os_requires_provider_provenance_and_high_score_neighbors(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.literature_intelligence_os")
    payload = _complete_payload()
    payload["provider_provenance"] = []

    result = module.materialize_literature_intelligence_os(
        study_root=tmp_path / "study",
        payload=payload,
    )

    assert result["status"] == "blocked"
    assert result["missing_reason"] == "missing_provider_provenance"

    payload = _complete_payload()
    payload["high_score_neighbor_refs"] = []

    result = module.materialize_literature_intelligence_os(
        study_root=tmp_path / "study",
        payload=payload,
    )

    assert result["status"] == "blocked"
    assert result["missing_reason"] == "missing_high_score_neighbor_refs"


def test_literature_intelligence_os_requires_evidence_node_provenance(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.literature_intelligence_os")
    payload = _complete_payload()
    payload["evidence_nodes"] = [
        {
            "node_id": "ungrounded-node",
            "claim": "This claim has no PMID, DOI, guideline ref, or source ref.",
            "evidence_type": "anchor_paper",
        }
    ]

    result = module.materialize_literature_intelligence_os(
        study_root=tmp_path / "study",
        payload=payload,
    )

    assert result["status"] == "blocked"
    assert result["missing_reason"] == "missing_evidence_node_provenance"
    read_model = module.read_literature_intelligence_os(study_root=tmp_path / "study")
    assert read_model["status"] == "blocked"
    assert read_model["evidence_nodes"][0]["node_id"] == "ungrounded-node"
    assert read_model["authority"]["contradiction_flags_authority"] == "evidence_review_signal_only"


def test_literature_intelligence_os_contradictions_are_review_signals_only(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.literature_intelligence_os")
    payload = _complete_payload()
    payload["contradiction_flags"] = [
        {
            "flag_id": "opposite-effect-direction",
            "signal": "Two evidence nodes point in different effect directions.",
            "evidence_refs": ["pmid:12345678", "doi:10.1000/systematic-review"],
        }
    ]

    result = module.materialize_literature_intelligence_os(
        study_root=tmp_path / "study",
        payload=payload,
    )

    assert result["status"] == "ready"
    assert result["quality_claim_authorized"] is False
    read_model = module.read_literature_intelligence_os(study_root=tmp_path / "study")
    assert read_model["contradiction_flags"][0]["review_signal_only"] is True
    assert read_model["authority"]["can_authorize_publication_quality"] is False
    assert read_model["authority"]["contradiction_flags_authority"] == "evidence_review_signal_only"


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
    assert summary["authority"]["can_authorize_publication_quality"] is False
