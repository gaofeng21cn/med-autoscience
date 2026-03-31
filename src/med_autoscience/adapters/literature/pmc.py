from __future__ import annotations

from urllib.request import urlopen
import xml.etree.ElementTree as ET

from med_autoscience.literature_records import LiteratureRecord


PMC_ARTICLE_XML_URL = "https://pmc.ncbi.nlm.nih.gov/articles"


def _fetch_bytes(url: str) -> bytes:
    with urlopen(url, timeout=30) as response:
        return response.read()


def _normalize_space(text: str) -> str:
    return " ".join(text.split())


def _node_text(root: ET.Element, xpath: str) -> str | None:
    node = root.find(xpath)
    if node is None:
        return None
    text = "".join(node.itertext()).strip()
    if not text:
        return None
    return _normalize_space(text)


def _article_id(root: ET.Element, pub_id_type: str) -> str | None:
    node = root.find(f".//article-id[@pub-id-type='{pub_id_type}']")
    if node is None or node.text is None:
        return None
    value = node.text.strip()
    return value or None


def fetch_pmc_record(*, pmcid: str) -> LiteratureRecord:
    normalized_pmcid = pmcid.strip()
    if not normalized_pmcid:
        raise ValueError("pmcid must not be empty")

    payload = _fetch_bytes(f"{PMC_ARTICLE_XML_URL}/{normalized_pmcid}/xml")
    root = ET.fromstring(payload)

    title = _node_text(root, ".//article-meta/title-group/article-title")
    if title is None:
        raise ValueError("PMC article XML missing article title")

    journal = _node_text(root, ".//journal-meta/journal-title-group/journal-title")
    year_text = _node_text(root, ".//article-meta/pub-date/year")
    year = int(year_text) if year_text is not None and year_text.isdigit() else None

    return LiteratureRecord(
        record_id=f"pmc:{normalized_pmcid}",
        title=title,
        authors=(),
        year=year,
        journal=journal,
        doi=_article_id(root, "doi"),
        pmid=_article_id(root, "pmid"),
        pmcid=_article_id(root, "pmc") or normalized_pmcid,
        arxiv_id=None,
        abstract=_node_text(root, ".//article-meta/abstract"),
        full_text_availability="full_text",
        source_priority=1,
        citation_payload={"pmc_xml_source": normalized_pmcid},
        local_asset_paths=(),
        relevance_role="candidate",
        claim_support_scope=(),
    )
