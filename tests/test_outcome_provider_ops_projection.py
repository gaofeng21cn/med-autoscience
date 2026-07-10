from med_autoscience.controllers import outcome_provider_ops_projection as outcome

FALSE_KEYS = (
    "can_authorize_quality can_authorize_drafting can_authorize_submission can_authorize_finalize "
    "can_bypass_ai_reviewer can_bypass_publication_gate"
).split()
TOP_FALSE_KEYS = (
    "quality_claim_authorized submission_ready_authorized finalize_authorized "
    "mechanical_projection_can_authorize_quality can_bypass_ai_reviewer can_bypass_publication_gate"
).split()


def test_outcome_provider_ops_projection_is_blocked_observability_only():
    payload = outcome.build_outcome_provider_ops_projection()
    assert (payload["status"], payload["provider_ops"]["provider_health_status"], bool(payload["diagnostics"])) == (
        "blocked", "blocked", True
    )
    boundary = payload["authority_contract"]
    assert set(boundary) == {"authority", "read_model_only", "observability_only", *FALSE_KEYS,
                             "required_authority_surfaces"}
    assert (boundary["authority"], boundary["read_model_only"], boundary["observability_only"]) == (
        "observability_projection_only", True, True
    )
    assert {key: boundary[key] for key in FALSE_KEYS} == dict.fromkeys(FALSE_KEYS, False)
    assert boundary["required_authority_surfaces"] == [
        "artifacts/publication_eval/latest.json",
        "artifacts/controller_decisions/latest.json",
        "AI reviewer publication gate",
    ]
    assert {key: payload[key] for key in TOP_FALSE_KEYS} == dict.fromkeys(TOP_FALSE_KEYS, False)
