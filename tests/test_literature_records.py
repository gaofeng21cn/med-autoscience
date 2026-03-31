from __future__ import annotations

import importlib


def test_literature_record_prefers_pubmed_over_arxiv() -> None:
    module = importlib.import_module("med_autoscience.literature_records")

    record = module.LiteratureRecord(
        record_id="pmid:12345",
        title="Prediction model paper",
        authors=("A. Author",),
        year=2024,
        journal="BMC Medicine",
        doi="10.1000/example",
        pmid="12345",
        pmcid=None,
        arxiv_id="2401.12345",
        abstract="Structured abstract",
        full_text_availability="abstract_only",
        source_priority=2,
        citation_payload={"journal": "BMC Medicine"},
        local_asset_paths=(),
        relevance_role="anchor",
        claim_support_scope=("primary_claim",),
    )

    assert record.primary_source == "pubmed"


def test_literature_record_primary_source_priority_chain() -> None:
    module = importlib.import_module("med_autoscience.literature_records")

    pmc_over_doi = module.LiteratureRecord(
        record_id="pmc:PMC777",
        title="PMC backed paper",
        authors=(),
        year=None,
        journal=None,
        doi="10.1000/example",
        pmid=None,
        pmcid="PMC777",
        arxiv_id="2401.22222",
        abstract=None,
        full_text_availability="full_text",
        source_priority=1,
        citation_payload={},
        local_asset_paths=(),
        relevance_role="candidate",
        claim_support_scope=(),
    )
    doi_over_arxiv = module.LiteratureRecord(
        record_id="doi:10.1000/example",
        title="DOI paper",
        authors=(),
        year=None,
        journal=None,
        doi="10.1000/example",
        pmid=None,
        pmcid=None,
        arxiv_id="2401.22222",
        abstract=None,
        full_text_availability="abstract_only",
        source_priority=1,
        citation_payload={},
        local_asset_paths=(),
        relevance_role="candidate",
        claim_support_scope=(),
    )
    arxiv_over_local = module.LiteratureRecord(
        record_id="arxiv:2401.22222",
        title="Arxiv paper",
        authors=(),
        year=None,
        journal=None,
        doi=None,
        pmid=None,
        pmcid=None,
        arxiv_id="2401.22222",
        abstract=None,
        full_text_availability="abstract_only",
        source_priority=1,
        citation_payload={},
        local_asset_paths=("refs/local.pdf",),
        relevance_role="candidate",
        claim_support_scope=(),
    )
    local_only = module.LiteratureRecord(
        record_id="local:001",
        title="Local paper",
        authors=(),
        year=None,
        journal=None,
        doi=None,
        pmid=None,
        pmcid=None,
        arxiv_id=None,
        abstract=None,
        full_text_availability="full_text",
        source_priority=1,
        citation_payload={},
        local_asset_paths=("refs/local.pdf",),
        relevance_role="candidate",
        claim_support_scope=(),
    )

    assert pmc_over_doi.primary_source == "pmc"
    assert doi_over_arxiv.primary_source == "doi"
    assert arxiv_over_local.primary_source == "arxiv"
    assert local_only.primary_source == "local"
