from __future__ import annotations


def build_data_access_ground_truth_isolation() -> dict[str, object]:
    return {
        "source_project": "academic-research-skills",
        "absorbed_as": "mas_native_stage_quality_data_access_descriptor",
        "descriptor_only": True,
        "runtime_permission_authority": False,
        "levels": [
            {
                "level_id": "raw_source_intake",
                "ars_data_access_level": "raw",
                "mas_scope": "source_intake_or_unverified_workspace_material",
                "may_feed_candidate_generation": True,
                "may_authorize_reviewer_verdict": False,
            },
            {
                "level_id": "verified_evidence_only",
                "ars_data_access_level": "verified_only",
                "mas_scope": "evidence_or_review_refs_after_integrity_gate",
                "may_feed_candidate_generation": True,
                "may_authorize_reviewer_verdict": False,
            },
            {
                "level_id": "reviewer_verdict_only",
                "ars_data_access_level": "verified_only",
                "mas_scope": "reviewer_or_auditor_verdict_record",
                "may_feed_candidate_generation": False,
                "may_authorize_reviewer_verdict": False,
            },
        ],
        "ground_truth_boundary": {
            "rubric_or_verdict_must_not_seed_candidate_generation": True,
            "reviewer_must_run_as_separate_invocation": True,
            "rubric_may_authorize_quality_verdict": False,
            "rubric_may_write_truth": False,
            "descriptor_grants_runtime_access": False,
        },
    }


def data_access_level_ids() -> list[str]:
    return [
        str(item["level_id"])
        for item in build_data_access_ground_truth_isolation()["levels"]
    ]
