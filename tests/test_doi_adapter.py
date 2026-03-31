from __future__ import annotations

import importlib
from urllib.parse import unquote, urlsplit


def test_fetch_crossref_work_parses_doi_json(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.adapters.literature.doi")
    payload = (
        b'{"message": {"DOI": "10.1000/example", "title": ["Paper title"], '
        b'"container-title": ["Journal of Clinical Study"], '
        b'"published-print": {"date-parts": [[2023]]}}}'
    )
    requested_urls: list[str] = []

    def fake_fetch(url: str) -> bytes:
        requested_urls.append(url)
        return payload

    monkeypatch.setattr(module, "_fetch_bytes", fake_fetch)

    record = module.fetch_crossref_work(doi="10.1000/example")

    assert record.doi == "10.1000/example"
    assert record.journal == "Journal of Clinical Study"
    assert record.title == "Paper title"
    assert record.year == 2023
    assert len(requested_urls) == 1
    path = unquote(urlsplit(requested_urls[0]).path)
    assert path.endswith("/works/10.1000/example")
