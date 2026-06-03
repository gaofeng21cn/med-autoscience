from __future__ import annotations


USER_STAGE_LOG_REQUIRED_FIELDS = (
    "stage_name",
    "problem_summary",
    "stage_goal",
    "stage_work_done",
    "changed_stage_surfaces",
    "outcome",
    "remaining_blockers",
    "evidence_refs",
)

USER_STAGE_LOG_CONTRACT = {
    "surface_kind": "opl_standard_agent_user_stage_log_contract",
    "version": "standard-user-stage-log.v1",
    "owner": "one-person-lab",
    "standard_agent_requirement": (
        "domain_stage_closeout_must_return_user_readable_stage_semantics_or_typed_blocker"
    ),
    "opl_projection_surface": "stage_progress_log.user_stage_log",
    "domain_semantic_sources": [
        "typed_closeout_packet.user_stage_log",
        "typed_closeout_packet.paper_stage_log",
        "typed_closeout_packet.stage_log_summary",
        "route_impact.user_stage_log",
        "route_impact.paper_stage_log",
        "route_impact.stage_log_summary",
    ],
    "required_domain_semantic_fields": list(USER_STAGE_LOG_REQUIRED_FIELDS),
    "mas_paper_alias_fields": {
        "stage_work_done_alias": "paper_work_done",
        "changed_stage_surfaces_alias": "changed_paper_surfaces",
    },
    "required_observability_fields": ["duration", "token_usage", "cost"],
    "missing_semantics_policy": "typed_blocker_or_missing_domain_semantic_summary_no_opl_inference",
    "token_policy": "observed_or_explicit_missing_null_no_zero_fill",
    "authority_boundary": {
        "opl_can_infer_domain_semantics": False,
        "opl_can_read_artifact_body": False,
        "opl_can_write_domain_truth": False,
        "opl_can_authorize_quality_or_export": False,
        "provider_completion_can_claim_stage_semantics_complete": False,
        "mas_retains_publication_quality_authority": True,
    },
}


__all__ = ["USER_STAGE_LOG_CONTRACT", "USER_STAGE_LOG_REQUIRED_FIELDS"]
