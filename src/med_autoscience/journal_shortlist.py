from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


SUPPORTED_SELECTION_BANDS = ("primary_fit", "strong_alternative", "stretch", "backup")
SUPPORTED_CONFIDENCE_LABELS = ("high", "medium", "low")


@dataclass(frozen=True)
class SimilarPaperExample:
    title: str
    journal: str
    year: int | None
    source_url: str | None
    pmid: str | None
    similarity_rationale: str


@dataclass(frozen=True)
class TierSnapshot:
    source: str
    retrieved_on: str
    quartile: str | None
    journal_impact_factor: str | None
    citescore: str | None
    category_rank: str | None
    acceptance_rate: str | None

    @property
    def has_signal(self) -> bool:
        return any(
            (
                self.quartile,
                self.journal_impact_factor,
                self.citescore,
                self.category_rank,
                self.acceptance_rate,
            )
        )


@dataclass(frozen=True)
class JournalShortlistEvidence:
    journal_name: str
    selection_band: str
    fit_summary: str
    risk_summary: str
    official_scope_sources: tuple[str, ...]
    similar_paper_examples: tuple[SimilarPaperExample, ...]
    tier_snapshot: TierSnapshot
    confidence: str
    notes: str | None

    @property
    def target_key(self) -> str:
        return self.journal_name.strip().lower()


@dataclass(frozen=True)
class JournalShortlistContract:
    study_root: Path
    shortlist: tuple[str, ...]
    evidence_items: tuple[JournalShortlistEvidence, ...]
    uncovered_shortlist_entries: tuple[str, ...]
    extra_evidence_entries: tuple[str, ...]

    @property
    def candidate_count(self) -> int:
        return len(self.evidence_items)

    @property
    def ready(self) -> bool:
        return bool(self.evidence_items) and not self.uncovered_shortlist_entries


def _load_yaml_dict(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def _non_empty_string(raw_value: object, *, field_name: str) -> str:
    if not isinstance(raw_value, str) or not raw_value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return raw_value.strip()


def _optional_string(raw_value: object) -> str | None:
    if not isinstance(raw_value, str) or not raw_value.strip():
        return None
    return raw_value.strip()


def _non_empty_scalar_string(raw_value: object, *, field_name: str) -> str:
    if raw_value is None:
        raise ValueError(f"{field_name} must be a non-empty scalar")
    text = str(raw_value).strip()
    if not text:
        raise ValueError(f"{field_name} must be a non-empty scalar")
    return text


def _string_list(raw_value: object, *, field_name: str) -> tuple[str, ...]:
    if not isinstance(raw_value, list):
        raise ValueError(f"{field_name} must be a list of strings")
    items: list[str] = []
    for item in raw_value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field_name} must be a list of non-empty strings")
        items.append(item.strip())
    return tuple(items)


def _int_or_none(raw_value: object, *, field_name: str) -> int | None:
    if raw_value is None or raw_value == "":
        return None
    if isinstance(raw_value, int):
        return raw_value
    raise ValueError(f"{field_name} must be an integer when provided")


def _normalize_similar_paper(raw_value: object, *, field_name: str) -> SimilarPaperExample:
    if not isinstance(raw_value, dict):
        raise ValueError(f"{field_name} must be a list of mappings")
    title = _non_empty_string(raw_value.get("title"), field_name=f"{field_name}.title")
    journal = _non_empty_string(raw_value.get("journal"), field_name=f"{field_name}.journal")
    source_url = _optional_string(raw_value.get("source_url"))
    pmid = _optional_string(raw_value.get("pmid"))
    if source_url is None and pmid is None:
        raise ValueError(f"{field_name} item requires source_url or pmid")
    return SimilarPaperExample(
        title=title,
        journal=journal,
        year=_int_or_none(raw_value.get("year"), field_name=f"{field_name}.year"),
        source_url=source_url,
        pmid=pmid,
        similarity_rationale=_non_empty_string(
            raw_value.get("similarity_rationale"),
            field_name=f"{field_name}.similarity_rationale",
        ),
    )


def _normalize_similar_papers(raw_value: object, *, field_name: str) -> tuple[SimilarPaperExample, ...]:
    if not isinstance(raw_value, list) or not raw_value:
        raise ValueError(f"{field_name} must be a non-empty list")
    return tuple(
        _normalize_similar_paper(item, field_name=f"{field_name}[{index}]")
        for index, item in enumerate(raw_value)
    )


def _normalize_tier_snapshot(raw_value: object, *, field_name: str) -> TierSnapshot:
    if not isinstance(raw_value, dict):
        raise ValueError(f"{field_name} must be a mapping")
    snapshot = TierSnapshot(
        source=_non_empty_string(raw_value.get("source"), field_name=f"{field_name}.source"),
        retrieved_on=_non_empty_scalar_string(raw_value.get("retrieved_on"), field_name=f"{field_name}.retrieved_on"),
        quartile=_optional_string(raw_value.get("quartile")),
        journal_impact_factor=_optional_string(raw_value.get("journal_impact_factor")),
        citescore=_optional_string(raw_value.get("citescore")),
        category_rank=_optional_string(raw_value.get("category_rank")),
        acceptance_rate=_optional_string(raw_value.get("acceptance_rate")),
    )
    if not snapshot.has_signal:
        raise ValueError(
            f"{field_name} requires at least one of quartile, journal_impact_factor, citescore, category_rank, or acceptance_rate"
        )
    return snapshot


def _normalize_evidence(raw_value: object, *, field_name: str) -> JournalShortlistEvidence:
    if not isinstance(raw_value, dict):
        raise ValueError(f"{field_name} must be a mapping")
    selection_band = _non_empty_string(raw_value.get("selection_band"), field_name=f"{field_name}.selection_band")
    if selection_band not in SUPPORTED_SELECTION_BANDS:
        supported = ", ".join(SUPPORTED_SELECTION_BANDS)
        raise ValueError(f"{field_name}.selection_band must be one of: {supported}")
    confidence = _non_empty_string(raw_value.get("confidence"), field_name=f"{field_name}.confidence")
    if confidence not in SUPPORTED_CONFIDENCE_LABELS:
        supported = ", ".join(SUPPORTED_CONFIDENCE_LABELS)
        raise ValueError(f"{field_name}.confidence must be one of: {supported}")
    return JournalShortlistEvidence(
        journal_name=_non_empty_string(raw_value.get("journal_name"), field_name=f"{field_name}.journal_name"),
        selection_band=selection_band,
        fit_summary=_non_empty_string(raw_value.get("fit_summary"), field_name=f"{field_name}.fit_summary"),
        risk_summary=_non_empty_string(raw_value.get("risk_summary"), field_name=f"{field_name}.risk_summary"),
        official_scope_sources=_string_list(
            raw_value.get("official_scope_sources"),
            field_name=f"{field_name}.official_scope_sources",
        ),
        similar_paper_examples=_normalize_similar_papers(
            raw_value.get("similar_paper_examples"),
            field_name=f"{field_name}.similar_paper_examples",
        ),
        tier_snapshot=_normalize_tier_snapshot(
            raw_value.get("tier_snapshot"),
            field_name=f"{field_name}.tier_snapshot",
        ),
        confidence=confidence,
        notes=_optional_string(raw_value.get("notes")),
    )


def resolve_journal_shortlist_contract(*, study_root: Path | None) -> JournalShortlistContract | None:
    if study_root is None:
        return None
    resolved_study_root = Path(study_root).expanduser().resolve()
    payload = _load_yaml_dict(resolved_study_root / "study.yaml")
    raw_shortlist = payload.get("journal_shortlist")
    shortlist: tuple[str, ...]
    if raw_shortlist is None:
        shortlist = tuple()
    else:
        shortlist = _string_list(raw_shortlist, field_name="journal_shortlist")

    raw_evidence = payload.get("journal_shortlist_evidence")
    if raw_evidence is None:
        return None
    if not isinstance(raw_evidence, list) or not raw_evidence:
        raise ValueError("journal_shortlist_evidence must be a non-empty list")

    evidence_items = tuple(
        _normalize_evidence(item, field_name=f"journal_shortlist_evidence[{index}]")
        for index, item in enumerate(raw_evidence)
    )
    by_key = {item.target_key: item for item in evidence_items}
    resolved_shortlist = shortlist or tuple(item.journal_name for item in evidence_items)
    uncovered_shortlist_entries = tuple(
        item for item in resolved_shortlist if item.strip().lower() not in by_key
    )
    shortlist_keys = {item.strip().lower() for item in resolved_shortlist}
    extra_evidence_entries = tuple(
        item.journal_name for item in evidence_items if item.target_key not in shortlist_keys
    )
    return JournalShortlistContract(
        study_root=resolved_study_root,
        shortlist=resolved_shortlist,
        evidence_items=evidence_items,
        uncovered_shortlist_entries=uncovered_shortlist_entries,
        extra_evidence_entries=extra_evidence_entries,
    )


def render_journal_shortlist_contract_summary(contract: JournalShortlistContract) -> str:
    lines = [
        "# Study Journal Shortlist Contract",
        "",
        f"- study_root: {contract.study_root}",
        f"- shortlist_count: {len(contract.shortlist)}",
        f"- evidence_count: {contract.candidate_count}",
        f"- ready: {'true' if contract.ready else 'false'}",
    ]
    if contract.uncovered_shortlist_entries:
        lines.append(
            f"- uncovered_shortlist_entries: {', '.join(contract.uncovered_shortlist_entries)}"
        )
    if contract.extra_evidence_entries:
        lines.append(f"- extra_evidence_entries: {', '.join(contract.extra_evidence_entries)}")
    lines.extend(["", "Candidates:"])
    for item in contract.evidence_items:
        lines.extend(
            [
                f"- {item.journal_name}",
                f"  selection_band: {item.selection_band}",
                f"  confidence: {item.confidence}",
                f"  similar_paper_count: {len(item.similar_paper_examples)}",
                f"  official_scope_source_count: {len(item.official_scope_sources)}",
            ]
        )
    return "\n".join(lines) + "\n"
