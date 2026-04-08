from __future__ import annotations

from dataclasses import asdict
import importlib


def test_resolve_startup_literature_records_enriches_supported_startup_sources(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.startup_literature")
    records_module = importlib.import_module("med_autoscience.literature_records")

    pubmed_record = records_module.LiteratureRecord(
        record_id="pmid:12345",
        title="PubMed anchor paper",
        authors=("A. Author",),
        year=2024,
        journal="Diabetes Care",
        doi="10.1000/pubmed-anchor",
        pmid="12345",
        pmcid=None,
        arxiv_id=None,
        abstract=None,
        full_text_availability="abstract_only",
        source_priority=2,
        citation_payload={"source": "pubmed"},
        local_asset_paths=(),
        relevance_role="candidate",
        claim_support_scope=(),
    )
    doi_record = records_module.LiteratureRecord(
        record_id="doi:10.1000/example-doi",
        title="DOI-only neighboring paper",
        authors=("B. Author",),
        year=2022,
        journal="BMJ Open",
        doi="10.1000/example-doi",
        pmid=None,
        pmcid=None,
        arxiv_id=None,
        abstract=None,
        full_text_availability="metadata_only",
        source_priority=3,
        citation_payload={"source": "crossref"},
        local_asset_paths=(),
        relevance_role="candidate",
        claim_support_scope=(),
    )

    monkeypatch.setattr(
        module.pubmed_adapter,
        "fetch_pubmed_summary",
        lambda *, pmids: [pubmed_record] if pmids == ["12345"] else [],
    )
    monkeypatch.setattr(
        module.doi_adapter,
        "fetch_crossref_work",
        lambda *, doi: doi_record if doi == "10.1000/example-doi" else None,
    )

    payload = module.resolve_startup_literature_records(
        startup_contract={
            "paper_urls": [
                "https://pubmed.ncbi.nlm.nih.gov/12345/",
            ],
            "journal_shortlist": {
                "candidates": [
                    {
                        "similar_paper_examples": [
                            {
                                "title": "Duplicate PubMed example",
                                "source_url": "https://pubmed.ncbi.nlm.nih.gov/12345/",
                                "pmid": "12345",
                            },
                            {
                                "title": "DOI-only neighboring paper",
                                "source_url": "https://doi.org/10.1000/example-doi",
                                "doi": "10.1000/example-doi",
                            },
                        ]
                    }
                ]
            },
        }
    )

    assert payload == [
        {
            **asdict(pubmed_record),
            "relevance_role": "anchor_paper",
            "claim_support_scope": (),
        },
        {
            **asdict(doi_record),
            "relevance_role": "adjacent_inspiration",
            "claim_support_scope": ("paper_framing", "journal_fit_neighbor"),
        },
    ]


def test_resolve_startup_literature_records_falls_back_to_title_plus_url_for_non_identifier_example(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.startup_literature")

    monkeypatch.setattr(module.pubmed_adapter, "fetch_pubmed_summary", lambda *, pmids: [])
    monkeypatch.setattr(module.doi_adapter, "fetch_crossref_work", lambda *, doi: None)

    payload = module.resolve_startup_literature_records(
        startup_contract={
            "journal_shortlist": {
                "candidates": [
                    {
                        "similar_paper_examples": [
                            {
                                "title": "Narrative review without PubMed id",
                                "journal": "The Lancet",
                                "year": 2021,
                                "source_url": "https://example.org/narrative-review",
                            }
                        ]
                    }
                ]
            }
        }
    )

    assert payload == [
        {
            "record_id": "url:https_example_org_narrative_review",
            "title": "Narrative review without PubMed id",
            "authors": (),
            "year": 2021,
            "journal": "The Lancet",
            "doi": None,
            "pmid": None,
            "pmcid": None,
            "arxiv_id": None,
            "abstract": None,
            "full_text_availability": "metadata_only",
            "source_priority": 5,
            "citation_payload": {"url": "https://example.org/narrative-review"},
            "local_asset_paths": (),
            "relevance_role": "adjacent_inspiration",
            "claim_support_scope": ("paper_framing", "journal_fit_neighbor"),
        }
    ]
