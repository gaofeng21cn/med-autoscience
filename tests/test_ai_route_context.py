from med_autoscience.controllers.ai_route_context import build_ai_route_context


def test_ai_route_context_is_non_authoritative_and_progress_first() -> None:
    context = build_ai_route_context(
        study_id="study-1",
        action_type="hypothesis_generation",
        work_unit_id="hypothesis-2",
        work_unit_fingerprint="sha256:negative-result",
        policy_kind="route_back_with_negative_result",
    )

    assert context["surface_kind"] == "mas_ai_route_context"
    assert context["route_selection_owner"] == "codex_cli"
    assert context["progress_first"]["negative_result_is_evidence"] is True
    assert context["progress_first"]["blocks_stage_transition"] is False
    assert context["authority_boundary"]["context_can_reject_codex_route"] is False


def test_ai_route_context_does_not_require_runtime_transaction_shape() -> None:
    context = build_ai_route_context(study_id="study-1", action_type="analysis")

    assert "target_runtime_kind" not in context
    assert "required_readback_shape" not in context
    assert "recommended_transition_kind" not in context
    assert "required_postcondition" not in context
