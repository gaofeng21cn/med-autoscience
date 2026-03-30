from __future__ import annotations

from pathlib import Path

from med_autoscience.journal_shortlist import (
    render_journal_shortlist_contract_summary,
    resolve_journal_shortlist_contract,
)


def resolve_journal_shortlist(*, study_root: Path) -> dict[str, object]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    try:
        contract = resolve_journal_shortlist_contract(study_root=resolved_study_root)
    except ValueError as exc:
        return {
            "status": "invalid",
            "study_root": str(resolved_study_root),
            "shortlist": [],
            "candidate_count": 0,
            "uncovered_shortlist_entries": [],
            "extra_evidence_entries": [],
            "candidates": [],
            "errors": [str(exc)],
            "summary_markdown": "",
        }

    if contract is None:
        return {
            "status": "absent",
            "study_root": str(resolved_study_root),
            "shortlist": [],
            "candidate_count": 0,
            "uncovered_shortlist_entries": [],
            "extra_evidence_entries": [],
            "candidates": [],
            "errors": [],
            "summary_markdown": "",
        }

    return {
        "status": "resolved" if contract.ready else "incomplete",
        "study_root": str(contract.study_root),
        "shortlist": list(contract.shortlist),
        "candidate_count": contract.candidate_count,
        "uncovered_shortlist_entries": list(contract.uncovered_shortlist_entries),
        "extra_evidence_entries": list(contract.extra_evidence_entries),
        "candidates": [
            {
                "journal_name": item.journal_name,
                "selection_band": item.selection_band,
                "fit_summary": item.fit_summary,
                "risk_summary": item.risk_summary,
                "official_scope_sources": list(item.official_scope_sources),
                "confidence": item.confidence,
                "notes": item.notes,
                "tier_snapshot": {
                    "source": item.tier_snapshot.source,
                    "retrieved_on": item.tier_snapshot.retrieved_on,
                    "quartile": item.tier_snapshot.quartile,
                    "journal_impact_factor": item.tier_snapshot.journal_impact_factor,
                    "citescore": item.tier_snapshot.citescore,
                    "category_rank": item.tier_snapshot.category_rank,
                    "acceptance_rate": item.tier_snapshot.acceptance_rate,
                },
                "similar_paper_examples": [
                    {
                        "title": example.title,
                        "journal": example.journal,
                        "year": example.year,
                        "source_url": example.source_url,
                        "pmid": example.pmid,
                        "similarity_rationale": example.similarity_rationale,
                    }
                    for example in item.similar_paper_examples
                ],
            }
            for item in contract.evidence_items
        ],
        "errors": [],
        "summary_markdown": render_journal_shortlist_contract_summary(contract),
    }
