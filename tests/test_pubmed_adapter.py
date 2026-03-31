from __future__ import annotations

import importlib
from urllib.parse import parse_qs, urlsplit


def test_fetch_pubmed_summary_parses_esummary_json(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.adapters.literature.pubmed")
    payload = (
        b'{"result": {"uids": ["12345"], "12345": {"uid": "12345", "title": "Paper title", '
        b'"pubdate": "2024 Jan", "fulljournalname": "BMC Medicine"}}}'
    )
    requested_urls: list[str] = []

    def fake_fetch(url: str) -> bytes:
        requested_urls.append(url)
        return payload

    monkeypatch.setattr(module, "_fetch_bytes", fake_fetch)

    records = module.fetch_pubmed_summary(pmids=["12345"])

    assert len(records) == 1
    assert records[0].pmid == "12345"
    assert records[0].journal == "BMC Medicine"
    assert records[0].title == "Paper title"
    assert records[0].year == 2024
    assert len(requested_urls) == 1
    query = parse_qs(urlsplit(requested_urls[0]).query)
    assert query["db"] == ["pubmed"]
    assert query["id"] == ["12345"]
    assert query["retmode"] == ["json"]
