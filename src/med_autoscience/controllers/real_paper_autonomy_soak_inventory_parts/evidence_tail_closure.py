from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any


TAIL_IDS = (
    "real_paper_line_provider_apply",
    "publication_route_memory_writeback",
    "artifact_lifecycle",
    "human_gate_resume",
    "family_transition_live_receipt",
)


def build_evidence_tail_closure_summary(
    *,
    study_id: str,
    owner_receipt_refs: Sequence[str],
    stable_blocker_refs: Sequence[str],
    live_evidence_refs: Mapping[str, Any],
    family_transition_receipt_refs: Sequence[str],
) -> dict[str, Any]:
    owner_refs = _dedupe_text(owner_receipt_refs)
    blocker_refs = _dedupe_text(stable_blocker_refs)
    tails = {
        "real_paper_line_provider_apply": _tail_status(
            refs=owner_refs,
            stable_blocker_refs=blocker_refs,
        ),
        "publication_route_memory_writeback": _tail_status(
            refs=_sequence(live_evidence_refs.get("publication_route_memory_writeback_receipt_refs")),
            stable_blocker_refs=blocker_refs,
        ),
        "artifact_lifecycle": _tail_status(
            refs=_sequence(live_evidence_refs.get("artifact_lifecycle_receipt_refs")),
            stable_blocker_refs=blocker_refs,
        ),
        "human_gate_resume": _tail_status(
            refs=_sequence(live_evidence_refs.get("human_gate_or_resume_refs")),
            stable_blocker_refs=blocker_refs,
        ),
        "family_transition_live_receipt": _tail_status(
            refs=family_transition_receipt_refs,
            stable_blocker_refs=blocker_refs,
        ),
    }
    counts = _summary_counts(tails)
    return {
        "surface_kind": "mas_paper_line_evidence_tail_closure_summary",
        "version": "mas-paper-line-evidence-tail-closure-summary.v1",
        "study_id": _text(study_id),
        "required_tail_ids": list(TAIL_IDS),
        "all_required_tails_closed": (
            counts["closed_tail_count"] == counts["required_tail_count"]
        ),
        "summary_counts": counts,
        "tails": tails,
        "authority_boundary": {
            "summary_only": True,
            "body_free": True,
            "is_route_authority": False,
            "can_authorize_domain_ready": False,
            "can_authorize_publication_readiness": False,
            "can_authorize_artifact_mutation": False,
            "not_triggered_is_not_success": True,
        },
    }


def _tail_status(*, refs: Sequence[str], stable_blocker_refs: Sequence[str]) -> dict[str, Any]:
    normalized_refs = _dedupe_text(refs)
    normalized_blockers = _dedupe_text(stable_blocker_refs)
    if normalized_blockers and (
        not normalized_refs or set(normalized_refs).issubset(set(normalized_blockers))
    ):
        status = "closed_by_stable_typed_blocker"
        selected_refs = normalized_refs or normalized_blockers
    elif normalized_refs:
        status = "refs_observed"
        selected_refs = normalized_refs
    else:
        status = "not_triggered"
        selected_refs = []
    return {
        "status": status,
        "refs": selected_refs,
        "required": True,
        "body_included": False,
    }


def _summary_counts(tails: Mapping[str, Mapping[str, Any]]) -> dict[str, int]:
    statuses = [_text(tail.get("status")) for tail in tails.values()]
    return {
        "required_tail_count": len(TAIL_IDS),
        "closed_tail_count": sum(
            status in {"refs_observed", "closed_by_stable_typed_blocker"}
            for status in statuses
        ),
        "evidence_gap_count": sum(status == "evidence_gap" for status in statuses),
        "stable_blocker_count": sum(status == "closed_by_stable_typed_blocker" for status in statuses),
        "not_triggered_count": sum(status == "not_triggered" for status in statuses),
    }


def _sequence(value: object) -> list[Any]:
    return list(value) if isinstance(value, Sequence) and not isinstance(value, str | bytes) else []


def _text(value: object) -> str:
    return str(value or "").strip()


def _dedupe_text(values: Iterable[object]) -> list[str]:
    return list(dict.fromkeys(_text(value) for value in values if _text(value)))


__all__ = ["build_evidence_tail_closure_summary"]
