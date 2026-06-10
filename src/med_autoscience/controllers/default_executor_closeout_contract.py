from __future__ import annotations

from typing import Any

from .default_executor_stage_log import (
    ACCOUNTING_POLICY,
    SEMANTIC_INCOMPLETE_POLICY,
    STANDARD_USER_STAGE_LOG_ALIASES,
)


def default_executor_typed_closeout_contract(*, action_type: str) -> dict[str, Any]:
    return {
        "typed_closeout_required_for_completion": True,
        "free_text_closeout_accepted": False,
        "accepted_surface_kinds": [
            "stage_attempt_closeout_packet",
            "stage_memory_closeout_packet",
            "domain_stage_closeout_packet",
        ],
        "required_ref_field": "closeout_refs",
        "minimum_closeout_refs": 1,
        "required_user_stage_log_field": "paper_stage_log",
        "accepted_user_stage_log_fields": [
            "paper_stage_log",
            "user_stage_log",
            "stage_log_summary",
        ],
        "standard_user_stage_log_aliases": dict(STANDARD_USER_STAGE_LOG_ALIASES),
        "required_user_stage_log_fields": [
            "stage_name",
            "problem_summary",
            "stage_goal",
            "stage_work_done",
            "paper_work_done",
            "changed_stage_surfaces",
            "changed_paper_surfaces",
            "outcome",
            "remaining_blockers",
            "duration",
            "token_usage",
            "cost",
            "usage_refs",
            "cost_refs",
            "progress_delta_classification",
            "deliverable_progress_delta",
            "paper_progress_delta",
            "platform_repair_delta",
            "next_forced_delta",
            "evidence_refs",
        ],
        "user_stage_log_policy": {
            "surface_kind": "mas_paper_facing_stage_log_summary",
            "summary_scope": "stage_log_read_model_only",
            "paper_body_included": False,
            "paper_body_target": False,
            "internal_review_language_allowed_in_paper_body": False,
            "quality_verdict_authorized": False,
            "submission_readiness_authorized": False,
            "progress_delta_policy": {
                "classification_values": [
                    "deliverable_progress",
                    "platform_repair",
                    "mixed",
                    "typed_blocker",
                    "human_gate",
                    "stop_loss",
                ],
                "deliverable_progress_delta_shape": {
                    "count": "integer",
                    "token_usage_total": "integer_or_null",
                    "refs": "optional_string_list",
                },
                "paper_progress_delta": "alias_of_deliverable_progress_delta_for_paper_lines",
                "platform_repair_delta_does_not_count_as_paper_progress": True,
                "next_forced_delta_required_for_no_deliverable_progress": True,
            },
        },
        "accounting_policy": dict(ACCOUNTING_POLICY),
        "semantic_incomplete_policy": dict(SEMANTIC_INCOMPLETE_POLICY),
        "completion_boundary": {
            "provider_completion": "typed_closeout_packet_observed",
            "domain_ready_verdict": "read_from_mas_publication_or_gate_surface",
            "provider_completion_is_domain_ready": False,
        },
        "authority_boundary": {
            "opl": "closeout_transport_only",
            "mas": "truth_quality_artifact_gate_owner",
        },
        "terminal_output_instruction": (
            "After completing the MAS owner-authorized work or identifying a typed blocker, "
            "end the response with exactly one JSON object whose surface_kind is one of "
            "stage_attempt_closeout_packet, stage_memory_closeout_packet, or "
            "domain_stage_closeout_packet. Include closeout_refs with the owner receipt, "
            "artifact delta, or typed blocker evidence refs. Include paper_stage_log with "
            "stage_name, problem_summary, stage_goal, stage_work_done, changed_stage_surfaces, "
            "paper_work_done, changed_paper_surfaces, outcome, remaining_blockers, duration, "
            "token_usage, cost, usage_refs, cost_refs, progress_delta_classification, "
            "deliverable_progress_delta, paper_progress_delta, platform_repair_delta, "
            "next_forced_delta, and evidence_refs so OPL "
            "stage_progress_log.user_stage_log can answer user progress questions. This "
            "same content may be supplied as user_stage_log or stage_log_summary only when "
            "it is identical to paper_stage_log. Report duration, token_usage, and cost as "
            "observed or explicitly missing with null numeric values; do not zero-fill or "
            "invent token/cost telemetry. If any required domain log field is missing, include "
            "missing_domain_fields and typed blocker reason "
            "domain_closeout_provided_incomplete_user_stage_log. This "
            "paper_stage_log is read-model/log content only; "
            "do not write it into the manuscript body and do not use it to claim quality, submission, "
            "or publication readiness. Do not use prose as the final completion signal."
        ),
        "action_type": action_type,
    }


__all__ = ["default_executor_typed_closeout_contract"]
