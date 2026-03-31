from __future__ import annotations

import importlib
from urllib.parse import urlsplit


def test_fetch_pmc_record_parses_article_xml(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.adapters.literature.pmc")
    payload = b"""<?xml version="1.0" encoding="UTF-8"?>
<article>
  <front>
    <journal-meta>
      <journal-title-group>
        <journal-title>Journal of Clinical Study</journal-title>
      </journal-title-group>
    </journal-meta>
    <article-meta>
      <article-id pub-id-type="pmc">PMC123456</article-id>
      <article-id pub-id-type="pmid">39876543</article-id>
      <article-id pub-id-type="doi">10.1000/pmc.example</article-id>
      <title-group>
        <article-title>PMC full text paper</article-title>
      </title-group>
      <pub-date>
        <year>2022</year>
      </pub-date>
      <abstract>
        <p>Structured abstract sentence.</p>
      </abstract>
    </article-meta>
  </front>
</article>
"""
    requested_urls: list[str] = []

    def fake_fetch(url: str) -> bytes:
        requested_urls.append(url)
        return payload

    monkeypatch.setattr(module, "_fetch_bytes", fake_fetch)

    record = module.fetch_pmc_record(pmcid="PMC123456")

    assert record.pmcid == "PMC123456"
    assert record.pmid == "39876543"
    assert record.doi == "10.1000/pmc.example"
    assert record.title == "PMC full text paper"
    assert record.journal == "Journal of Clinical Study"
    assert record.year == 2022
    assert record.abstract == "Structured abstract sentence."
    assert len(requested_urls) == 1
    assert urlsplit(requested_urls[0]).path.endswith("/PMC123456/xml")
