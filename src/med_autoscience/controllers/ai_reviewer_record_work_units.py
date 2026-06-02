from __future__ import annotations


CURRENT_MANUSCRIPT_AI_REVIEWER_RECORD_WORK_UNIT = (
    "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
)

AI_REVIEWER_RECORD_CONSUMPTION_WORK_UNIT_IDS = frozenset(
    {
        "consume_current_ai_reviewer_record",
        "consume_current_ai_reviewer_record_and_replay_gate",
        "consume_current_input_ai_reviewer_record",
        "consume_current_ai_reviewer_record_then_prose_gate_package_replay",
    }
)


__all__ = [
    "AI_REVIEWER_RECORD_CONSUMPTION_WORK_UNIT_IDS",
    "CURRENT_MANUSCRIPT_AI_REVIEWER_RECORD_WORK_UNIT",
]
