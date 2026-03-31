from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import re

from med_autoscience.literature_records import LiteratureRecord
import yaml


REFERENCE_PAPER_STAGE_REQUIREMENTS = {
    "scout": "required",
    "idea": "required",
    "write": "advisory",
}
_SUPPORTED_ROLE_IDS = {"anchor_paper", "closest_competitor", "adjacent_inspiration"}
_SOURCE_FIELD_ORDER = ("url", "doi", "pmid", "pmcid", "arxiv_id", "pdf_path")


@dataclass(frozen=True)
class ReferencePaper:
    paper_id: str
    title: str | None
    role: str
    url: str | None
    doi: str | None
    pmid: str | None
    pmcid: str | None
    arxiv_id: str | None
    pdf_path: Path | None
    borrow_contract: tuple[str, ...]
    do_not_borrow: tuple[str, ...]
    notes: str | None

    @property
    def source_types(self) -> tuple[str, ...]:
        source_types: list[str] = []
        if self.url:
            source_types.append("url")
        if self.doi:
            source_types.append("doi")
        if self.pmid:
            source_types.append("pmid")
        if self.pmcid:
            source_types.append("pmcid")
        if self.arxiv_id:
            source_types.append("arxiv_id")
        if self.pdf_path is not None:
            source_types.append("pdf_path")
        return tuple(source_types)

    @property
    def source_kind(self) -> str:
        return self.source_types[0]


@dataclass(frozen=True)
class ReferencePaperContract:
    quest_root: Path
    papers: tuple[ReferencePaper, ...]
    stage_requirements: dict[str, str]

    @property
    def paper_count(self) -> int:
        return len(self.papers)


def _load_yaml_dict(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def _normalize_string_list(raw_value: object) -> tuple[str, ...]:
    if not isinstance(raw_value, list):
        return tuple()
    items = []
    for item in raw_value:
        text = str(item).strip()
        if text:
            items.append(text)
    return tuple(items)


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.strip().lower())
    return slug.strip("-") or "reference-paper"


def _default_paper_id(*, payload: dict[str, Any], pdf_path: Path | None) -> str:
    raw_id = payload.get("id")
    if isinstance(raw_id, str) and raw_id.strip():
        return raw_id.strip()
    title = payload.get("title")
    if isinstance(title, str) and title.strip():
        return _slugify(title)
    for field in _SOURCE_FIELD_ORDER:
        value = payload.get(field)
        if isinstance(value, str) and value.strip():
            return _slugify(value)
    if pdf_path is not None:
        return _slugify(pdf_path.stem)
    raise ValueError("reference paper requires an id, title, or source locator")


def _resolve_pdf_path(*, quest_root: Path, raw_path: object) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None
    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (quest_root / candidate).resolve()


def _normalize_reference_paper(*, quest_root: Path, raw_paper: object) -> ReferencePaper:
    if not isinstance(raw_paper, dict):
        raise ValueError(f"unsupported reference paper payload: {raw_paper!r}")
    pdf_path = _resolve_pdf_path(quest_root=quest_root, raw_path=raw_paper.get("pdf_path"))
    title = str(raw_paper.get("title")).strip() if raw_paper.get("title") else None
    role = str(raw_paper.get("role", "anchor_paper")).strip() or "anchor_paper"
    if role not in _SUPPORTED_ROLE_IDS:
        supported = ", ".join(sorted(_SUPPORTED_ROLE_IDS))
        raise ValueError(f"unsupported reference paper role: {role}. Supported: {supported}")

    paper = ReferencePaper(
        paper_id=_default_paper_id(payload=raw_paper, pdf_path=pdf_path),
        title=title,
        role=role,
        url=str(raw_paper.get("url")).strip() if raw_paper.get("url") else None,
        doi=str(raw_paper.get("doi")).strip() if raw_paper.get("doi") else None,
        pmid=str(raw_paper.get("pmid")).strip() if raw_paper.get("pmid") else None,
        pmcid=str(raw_paper.get("pmcid")).strip() if raw_paper.get("pmcid") else None,
        arxiv_id=str(raw_paper.get("arxiv_id")).strip() if raw_paper.get("arxiv_id") else None,
        pdf_path=pdf_path,
        borrow_contract=_normalize_string_list(raw_paper.get("borrow_contract")),
        do_not_borrow=_normalize_string_list(raw_paper.get("do_not_borrow")),
        notes=str(raw_paper.get("notes")).strip() if raw_paper.get("notes") else None,
    )
    if not paper.source_types:
        raise ValueError(f"reference paper `{paper.paper_id}` requires at least one source locator")
    return paper


def resolve_reference_paper_contract(*, quest_root: Path | None) -> ReferencePaperContract | None:
    if quest_root is None:
        return None
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    payload = _load_yaml_dict(resolved_quest_root / "quest.yaml")
    startup_contract = payload.get("startup_contract") if isinstance(payload.get("startup_contract"), dict) else {}
    raw_papers = startup_contract.get("reference_papers")
    if raw_papers is None:
        raw_papers = payload.get("reference_papers")
    if raw_papers is None:
        return None
    if not isinstance(raw_papers, list):
        raise ValueError("reference_papers must be a list")
    if not raw_papers:
        return None
    papers = tuple(_normalize_reference_paper(quest_root=resolved_quest_root, raw_paper=item) for item in raw_papers)
    return ReferencePaperContract(
        quest_root=resolved_quest_root,
        papers=papers,
        stage_requirements=dict(REFERENCE_PAPER_STAGE_REQUIREMENTS),
    )


def _reference_paper_source_priority(paper: ReferencePaper) -> int:
    if paper.pmid:
        return 1
    if paper.pmcid:
        return 2
    if paper.doi:
        return 3
    if paper.arxiv_id:
        return 4
    if paper.url:
        return 5
    if paper.pdf_path is not None:
        return 6
    raise ValueError(f"reference paper `{paper.paper_id}` requires at least one source locator")


def _reference_paper_full_text_availability(paper: ReferencePaper) -> str:
    if paper.pdf_path is not None or paper.pmcid:
        return "full_text"
    if paper.pmid:
        return "abstract_only"
    return "metadata_only"


def export_reference_papers_to_literature_records(*, contract: ReferencePaperContract) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for paper in contract.papers:
        if not paper.title:
            raise ValueError(f"reference paper `{paper.paper_id}` requires title for literature hydration")
        record = LiteratureRecord(
            record_id=paper.paper_id,
            title=paper.title,
            authors=(),
            year=None,
            journal=None,
            doi=paper.doi,
            pmid=paper.pmid,
            pmcid=paper.pmcid,
            arxiv_id=paper.arxiv_id,
            abstract=None,
            full_text_availability=_reference_paper_full_text_availability(paper),
            source_priority=_reference_paper_source_priority(paper),
            citation_payload={
                key: value
                for key, value in {
                    "url": paper.url,
                    "doi": paper.doi,
                    "pmid": paper.pmid,
                    "pmcid": paper.pmcid,
                    "arxiv_id": paper.arxiv_id,
                }.items()
                if value is not None
            },
            local_asset_paths=(str(paper.pdf_path),) if paper.pdf_path is not None else (),
            relevance_role=paper.role,
            claim_support_scope=(),
        )
        records.append(asdict(record))
    return records


def render_reference_paper_contract_summary(contract: ReferencePaperContract) -> str:
    lines = [
        "# Quest Reference Paper Contract",
        "",
        "Stage requirements:",
        *[f"- {stage}: {mode}" for stage, mode in contract.stage_requirements.items()],
        "",
        "Papers:",
    ]
    for paper in contract.papers:
        title = paper.title or "<untitled>"
        lines.extend(
            [
                f"- {paper.paper_id}: {title}",
                f"  role: {paper.role}",
                f"  source_kind: {paper.source_kind}",
                f"  borrow_contract: {', '.join(paper.borrow_contract) if paper.borrow_contract else '<none>'}",
                f"  do_not_borrow: {', '.join(paper.do_not_borrow) if paper.do_not_borrow else '<none>'}",
            ]
        )
        if paper.notes:
            lines.append(f"  notes: {paper.notes}")
    return "\n".join(lines) + "\n"


def render_reference_paper_overlay_block(*, stage_id: str) -> str:
    if stage_id not in REFERENCE_PAPER_STAGE_REQUIREMENTS:
        supported = ", ".join(sorted(REFERENCE_PAPER_STAGE_REQUIREMENTS))
        raise ValueError(f"unsupported reference paper overlay stage: {stage_id}. Supported: {supported}")

    stage_requirement = REFERENCE_PAPER_STAGE_REQUIREMENTS[stage_id]
    stage_specific_lines = {
        "scout": [
            "For this stage: required for this stage.",
            "Before broad literature expansion, first inspect whether `quest.yaml -> startup_contract.reference_papers` or top-level `reference_papers` exists.",
            "Treat those papers as the quest-local framing anchors for task definition, evaluation package, and baseline neighborhood.",
            "Do not silently ignore a listed reference paper. If it is not transferable, record why.",
        ],
        "idea": [
            "For this stage: required for this stage.",
            "Every selected direction must explicitly explain whether it inherits from, departs from, or rejects each relevant reference paper.",
            "Do not promote a selected direction without naming the relationship between the selected direction and the quest reference papers.",
        ],
        "write": [
            "For this stage: advisory for this stage.",
            "You may borrow figure, section, or narrative surface patterns only when the actual quest artifacts support them.",
            "do not back-solve missing analyses or unsupported claims merely to resemble a reference paper.",
        ],
    }[stage_id]
    lines = [
        "## Reference paper contract",
        "",
        "If `quest.yaml -> startup_contract.reference_papers` or top-level `reference_papers` exists, treat it as a quest-local runtime contract.",
        "This is a read-only audit surface for agent execution and human review, not a human-facing toolbox workflow.",
        "",
        "Stage contract:",
        "- scout: required",
        "- idea: required",
        "- write: advisory",
        "",
        *stage_specific_lines,
        "",
        "For every retained reference paper, keep the audit surface explicit:",
        "- role in this quest",
        "- what may be borrowed",
        "- what must not be borrowed",
        "- why any deviation is justified",
        "",
        "Never treat a reference paper as substitute evidence for the current quest.",
    ]
    return "\n".join(lines) + "\n"
