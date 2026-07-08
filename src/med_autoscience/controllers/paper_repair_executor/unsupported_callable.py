from __future__ import annotations


BLOCKER = "unsupported_owner_callable_surface"
QUALITY_REPAIR_BATCH_CALLABLE = "quality_repair_batch.run_quality_repair_batch"
AI_REVIEWER_PUBLICATION_EVAL_CALLABLE = (
    "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
)
SUPPORTED_OWNER_CALLABLES = {
    QUALITY_REPAIR_BATCH_CALLABLE,
    AI_REVIEWER_PUBLICATION_EVAL_CALLABLE,
    "paper_repair_executor.dispatch_repair_work_unit",
    "",
}


def is_supported(callable_surface: str) -> bool:
    return callable_surface in SUPPORTED_OWNER_CALLABLES


def review_finding(callable_surface: str) -> dict[str, object]:
    return {
        "surface": "paper_repair_executor",
        "blocked_reason": BLOCKER,
        "owner_callable_surface": callable_surface,
        "retryable": False,
    }
