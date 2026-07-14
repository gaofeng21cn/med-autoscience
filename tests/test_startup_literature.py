from __future__ import annotations

import importlib


def _provider_receipts() -> tuple[dict[str, object], ...]:
    return (
        {
            "receipt_ref": "opl://connect/references/verify/startup",
            "provider_evidence": [
                {
                    "reference_id": "pmid:12345",
                    "provider": "pubmed",
                    "lookup_status": "found",
                    "status": "matched",
                    "match_status": "identifier_matched",
                    "matched_identifiers": {"pmid": "12345"},
                    "metadata": {
                        "title": "PubMed anchor paper",
                        "authors": ["A. Author"],
                        "year": "2024",
                        "journal": "Diabetes Care",
                    },
                    "provider_identifiers": {"pmid": "12345", "doi": "10.1000/pubmed-anchor"},
                },
                {
                    "reference_id": "doi:10.1000/example-doi",
                    "provider": "crossref",
                    "lookup_status": "found",
                    "status": "matched",
                    "match_status": "identifier_matched",
                    "matched_identifiers": {"doi": "10.1000/example-doi"},
                    "metadata": {
                        "title": "DOI-only neighboring paper",
                        "authors": ["B. Author"],
                        "year": "2022",
                        "journal": "BMJ Open",
                    },
                    "provider_identifiers": {"doi": "10.1000/example-doi"},
                },
            ],
        },
    )


def test_resolve_startup_literature_enriches_supported_startup_sources_from_receipts() -> None:
    module = importlib.import_module("med_autoscience.startup_literature")

    resolution = module.resolve_startup_literature(
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
        },
        provider_receipts=_provider_receipts(),
    )

    assert resolution["status"] == "resolved"
    assert resolution["provider_receipt_refs"] == ["opl://connect/references/verify/startup"]
    records = resolution["records"]
    assert [record["record_id"] for record in records] == [
        "pmid:12345",
        "doi:10.1000/example-doi",
    ]
    assert records[0]["relevance_role"] == "anchor_paper"
    assert records[1]["relevance_role"] == "adjacent_inspiration"
    assert records[1]["claim_support_scope"] == ("paper_framing", "journal_fit_neighbor")


def test_resolve_startup_literature_keeps_local_seed_without_provider_identifier() -> None:
    module = importlib.import_module("med_autoscience.startup_literature")

    resolution = module.resolve_startup_literature(
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

    assert resolution["status"] == "resolved"
    assert resolution["records"] == [
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
