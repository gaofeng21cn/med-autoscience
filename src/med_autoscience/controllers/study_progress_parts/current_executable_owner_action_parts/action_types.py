from __future__ import annotations

AI_REVIEWER_ACTION = "return_to_ai_reviewer_workflow"
AI_REVIEWER_OWNER = "ai_reviewer"
AI_REVIEWER_WORK_UNIT = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
GATE_CLEARING_ACTION = "run_gate_clearing_batch"
GATE_CLEARING_OWNER = "gate_clearing_batch"
GATE_CLEARING_WORK_UNIT = "publication_gate_replay"
QUALITY_REPAIR_ACTION = "run_quality_repair_batch"
TERMINAL_NEXT_FORCED_DELTA_ACTIONS = frozenset(
    {
        GATE_CLEARING_ACTION,
        QUALITY_REPAIR_ACTION,
        "consume_record_only_ai_reviewer_closeout_or_route_next_owner",
    }
)

__all__ = [
    "AI_REVIEWER_ACTION",
    "AI_REVIEWER_OWNER",
    "AI_REVIEWER_WORK_UNIT",
    "GATE_CLEARING_ACTION",
    "GATE_CLEARING_OWNER",
    "GATE_CLEARING_WORK_UNIT",
    "QUALITY_REPAIR_ACTION",
    "TERMINAL_NEXT_FORCED_DELTA_ACTIONS",
]
