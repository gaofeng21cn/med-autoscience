from __future__ import annotations


CLAIM_EVIDENCE_ALIGNMENT_REPAIR_WORK_UNIT_ID = "claim_evidence_alignment_repair"
CURRENT_MANUSCRIPT_CLAIM_EVIDENCE_ALIGNMENT_REPAIR_WORK_UNIT_ID = (
    "current_manuscript_claim_evidence_alignment_repair"
)

CLAIM_EVIDENCE_ALIGNMENT_REPAIR_WORK_UNIT_IDS = frozenset(
    {
        CLAIM_EVIDENCE_ALIGNMENT_REPAIR_WORK_UNIT_ID,
        CURRENT_MANUSCRIPT_CLAIM_EVIDENCE_ALIGNMENT_REPAIR_WORK_UNIT_ID,
    }
)


def is_claim_evidence_alignment_repair_work_unit(unit_id: object) -> bool:
    return str(unit_id or "").strip() in CLAIM_EVIDENCE_ALIGNMENT_REPAIR_WORK_UNIT_IDS


__all__ = [
    "CLAIM_EVIDENCE_ALIGNMENT_REPAIR_WORK_UNIT_ID",
    "CLAIM_EVIDENCE_ALIGNMENT_REPAIR_WORK_UNIT_IDS",
    "CURRENT_MANUSCRIPT_CLAIM_EVIDENCE_ALIGNMENT_REPAIR_WORK_UNIT_ID",
    "is_claim_evidence_alignment_repair_work_unit",
]
