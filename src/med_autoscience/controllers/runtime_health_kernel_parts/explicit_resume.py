from __future__ import annotations


EXPLICIT_RESUME_REASONS = frozenset(
    {
        "quest_stopped_requires_explicit_rerun",
        "quest_parked_on_unchanged_finalize_state",
        "quest_waiting_for_explicit_wakeup_after_manual_hold",
        "quest_waiting_for_submission_metadata",
        "quest_waiting_for_submission_metadata_but_auto_resume_disabled",
    }
)


def reason_requires_explicit_resume(reason: str | None) -> bool:
    return reason in EXPLICIT_RESUME_REASONS
