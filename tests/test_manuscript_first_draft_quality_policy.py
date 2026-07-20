from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POLICY_REF = "contracts/manuscript_first_draft_quality_policy.json"


def _load(relative_path: str) -> dict[str, object]:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def test_external_validation_first_draft_contract_preserves_risk_semantics() -> None:
    policy = _load(POLICY_REF)
    external = policy["prediction_model_external_validation"]
    horizon = external["fixed_horizon_risk_semantics"]
    comparability = external["construct_comparability"]
    display = external["display_source_currentness"]

    assert horizon["recorded_event_count_fraction_role"] == (
        "descriptive_count_fraction_not_risk_estimate"
    )
    assert horizon[
        "binary_event_fraction_may_be_called_observed_risk_with_early_censoring"
    ] is False
    assert "censored_before_horizon_count" in horizon["must_bind"]
    assert "independent_censoring_assumption" in horizon["must_bind"]
    assert comparability["missing_mapping_or_identity_linkage_disposition"] == (
        "not_estimable"
    )
    assert comparability["proxy_substitution_without_owner_acceptance_allowed"] is False
    assert comparability[
        "non_estimability_may_imply_similarity_difference_or_mechanism"
    ] is False
    assert display[
        "numeric_denominator_estimand_or_construct_change_invalidates_embedded_render_payload"
    ] is True
    assert display["stale_render_request_reuse_allowed"] is False
    assert display["successful_render_exit_proves_source_currentness"] is False


def test_effective_authoring_surfaces_consume_first_draft_quality_policy() -> None:
    manifest = _load("agent/stages/manifest.json")
    stage_pack = _load("contracts/mas-paper-study-stage-pack.json")
    pack_input = _load("contracts/pack_compiler_input.json")
    prompt = (ROOT / "agent/prompts/manuscript_authoring.md").read_text(
        encoding="utf-8"
    )
    normalized_prompt = " ".join(prompt.split())

    authoring = next(
        stage
        for stage in manifest["stages"]
        if stage["stage_id"] == "manuscript_authoring"
    )
    routing = authoring["stage_contract_extension"][
        "first_draft_professional_skill_routing"
    ]
    paper_routing = stage_pack["reviewer_revision_default_mechanism"][
        "stage_attempt_readback_contract"
    ]["first_draft_professional_skill_routing"]

    assert routing["quality_policy_ref"] == POLICY_REF
    assert paper_routing["quality_policy_ref"] == POLICY_REF
    assert "medical-risk-model-transportability-reviewer" in routing[
        "conditional_specialists"
    ]
    assert "medical-survival-analysis-plan" in routing["conditional_specialists"]
    assert pack_input["required_domain_pack_paths"].count(POLICY_REF) == 1
    assert pack_input["source_refs"][
        "manuscript_first_draft_quality_policy_ref"
    ] == POLICY_REF
    assert pack_input["source_refs"]["required_domain_pack_paths"].count(
        POLICY_REF
    ) == 1
    for required_text in (
        "fixed_horizon_risk_semantics_ref",
        "construct_comparability_ref",
        "structured_display_source_map_ref",
        "recorded event fraction is descriptive",
        "comparison not estimable",
        "invalidate any table or figure render request",
    ):
        assert required_text in normalized_prompt


def test_specialist_skill_writeback_uses_current_developer_route_not_oma_work_order() -> None:
    stage_pack = _load("contracts/mas-paper-study-stage-pack.json")
    mechanism = stage_pack["reviewer_revision_default_mechanism"]
    writeback = mechanism["specialist_skill_writeback_contract"]
    handoff = writeback["work_order_handoff"]

    assert all(
        "OMA developer work order" not in route
        for route in mechanism["trigger"]["large_revision_routes"]
    )
    assert writeback["route"].startswith("OPL developer-supervisor")
    assert handoff["source_owner"] == "one-person-lab"
    assert handoff["source_surface"] == (
        "developer_supervisor_direct_repo_fix_or_pr_route"
    )
    assert handoff["oma_can_emit_work_order"] is False
