from __future__ import annotations

from pathlib import Path

from med_autoscience.reference_papers import (
    render_reference_paper_contract_summary,
    resolve_reference_paper_contract,
)


def resolve_reference_papers(*, quest_root: Path) -> dict[str, object]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    contract = resolve_reference_paper_contract(quest_root=resolved_quest_root)
    if contract is None:
        return {
            "status": "absent",
            "quest_root": str(resolved_quest_root),
            "paper_count": 0,
            "papers": [],
            "stage_requirements": {},
            "summary_markdown": "",
        }
    return {
        "status": "resolved",
        "quest_root": str(contract.quest_root),
        "paper_count": contract.paper_count,
        "stage_requirements": dict(contract.stage_requirements),
        "papers": [
            {
                "paper_id": paper.paper_id,
                "title": paper.title,
                "role": paper.role,
                "source_kind": paper.source_kind,
                "source_types": list(paper.source_types),
                "borrow_contract": list(paper.borrow_contract),
                "do_not_borrow": list(paper.do_not_borrow),
                "notes": paper.notes,
                "pdf_path": str(paper.pdf_path) if paper.pdf_path is not None else None,
            }
            for paper in contract.papers
        ],
        "summary_markdown": render_reference_paper_contract_summary(contract),
    }
