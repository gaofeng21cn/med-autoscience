from med_autoscience.controllers import research_memory


def test_research_frontier_advisory_keeps_domain_authority_closed() -> None:
    board = research_memory.build_research_frontier_board(
        study_id="S1",
        stage="idea",
        packet={
            "active_candidates": [
                {
                    "candidate_id": "clinical-subtype-line",
                    "summary": "Clinical subtype line remains plausible.",
                    "evidence_refs": ["evidence:subtype-feasibility"],
                }
            ]
        },
    )

    assert board["summary"]["counts_by_status"]["active"] == 1
    assert board["authority_boundary"]["can_authorize_stage_completion"] is False
    assert board["authority_boundary"]["can_write_domain_truth"] is False
    assert board["rollback_target_policy"]["advisory_only"] is True
