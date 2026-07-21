from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
STAGE_IDS = [
    "direction_and_route_selection",
    "baseline_and_evidence_setup",
    "bounded_analysis_campaign",
    "manuscript_authoring",
    "review_and_quality_gate",
    "finalize_and_publication_handoff",
]
COMMON_DOMAIN_EXTENSION_FIELDS = {
    "cohort_query_refs",
    "dashboard_metric_refs",
    "human_gate_progress_evidence",
    "hypothesis_portfolio_evidence_pack",
    "minimum_forward_delta",
    "monitor_refs",
    "route_obligation_lens",
    "research_trajectory",
    "source_scope_refs",
    "trigger_refs",
}
LATE_STAGE_EXTENSION_FIELDS = {
    "manuscript_authoring": {
        "late_stage_progress_sprint_contract",
        "typed_cognitive_subpacket_gate",
    },
    "review_and_quality_gate": {
        "late_stage_progress_sprint_contract",
        "typed_cognitive_subpacket_gate",
        "mandatory_pre_gate_checks",
    },
    "finalize_and_publication_handoff": {
        "late_stage_progress_sprint_contract",
        "typed_cognitive_subpacket_gate",
        "mandatory_pre_gate_checks",
    },
}
FORBIDDEN_FRAMEWORK_FIELDS = {
    "requires",
    "ensures",
    "boundary_assumptions",
    "properties",
    "expected_receipt_refs",
    "receipt_schema_refs",
    "authority_function_refs",
    "l4_entry_gate",
    "l5_entry_gate",
    "stage_completion_policy",
    "user_stage_log_contract",
    "progress_delta_policy",
    "typed_blocker_lineage_policy",
    "runtime_event_refs",
}
HANDOFF_REVIEW_BOUNDARY = {
    "artifact_effect": "reviewed_immutable_refs_only",
    "freezes_canonical_artifact_bytes": False,
    "issues_quality_export_publication_or_ready_claim": False,
    "downstream_owner_retains_acceptance": True,
}
HANDOFF_PROJECTION_ROLES = [
    "submission_status",
    "publication_evaluation",
    "next_action_envelope",
    "submission_projection_manifest",
]
PACKAGE_CURRENTNESS_PHASES = [
    "source_review",
    "descriptor_freeze",
    "deterministic_build_a",
    "deterministic_build_b",
    "exact_byte_delivery_review",
    "publish",
    "domain_status_and_publication_eval_reconciliation",
]


def _stage_manifest() -> dict[str, object]:
    return json.loads(
        (REPO_ROOT / "agent/stages/manifest.json").read_text(encoding="utf-8")
    )


def _paper_stage_pack() -> dict[str, object]:
    return json.loads(
        (REPO_ROOT / "contracts/mas-paper-study-stage-pack.json").read_text(
            encoding="utf-8"
        )
    )


def test_stage_manifest_declares_domain_extensions_for_opl_generated_plane() -> None:
    manifest = _stage_manifest()
    stages = manifest["stages"]
    assert isinstance(stages, list)
    assert [stage["stage_id"] for stage in stages] == STAGE_IDS

    for stage in stages:
        extension = stage.get("stage_contract_extension")
        assert isinstance(extension, dict)
        assert COMMON_DOMAIN_EXTENSION_FIELDS <= set(extension)
        assert not (FORBIDDEN_FRAMEWORK_FIELDS & set(extension))
        assert extension["monitor_refs"]
        assert extension["source_scope_refs"]

        minimum_delta = extension["minimum_forward_delta"]
        assert minimum_delta["owner_action"]["allowed_action_refs"] == stage[
            "allowed_action_refs"
        ]
        action_trigger = next(
            trigger
            for trigger in extension["trigger_refs"]
            if trigger["role"] == "mas_guarded_action_trigger_candidates"
        )
        assert action_trigger["ref"] == stage["allowed_action_refs"]
        expected_late_fields = LATE_STAGE_EXTENSION_FIELDS.get(stage["stage_id"], set())
        assert expected_late_fields <= set(extension)

    handoff_stage = next(
        stage
        for stage in stages
        if stage["stage_id"] == "finalize_and_publication_handoff"
    )
    assert handoff_stage["stage_kind"] == "packaging"
    assert handoff_stage["handoff_review_boundary"] == HANDOFF_REVIEW_BOUNDARY
    transport = handoff_stage["artifact_projection_transport"]
    assert transport["domain_owner"] == "MedAutoScience"
    assert transport["transport_owner"] == "One Person Lab"
    assert transport["transport_action_id"] == (
        "opl_pack_materialize_artifact_projection"
    )
    assert transport["required_manifest_scope"] == "publication_generation"
    assert transport["required_generation_artifact_roles"] == (
        HANDOFF_PROJECTION_ROLES
    )
    assert transport["completion_marker_paths"] == [
        "STATUS.json",
        "audit/submission_manifest.json",
    ]
    assert transport["same_generation_required"] is True
    assert transport["direct_incremental_preferred_root_write_forbidden"] is True
    assert transport["transport_can_write_domain_truth"] is False
    assert (
        transport["transport_can_authorize_quality_publication_or_submission"]
        is False
    )
    assert all(
        "handoff_review_boundary" not in stage
        for stage in stages
        if stage["stage_id"] != "finalize_and_publication_handoff"
    )


def test_stage_manifest_declares_deterministic_review_snapshot_lane_bindings() -> None:
    stages = _stage_manifest()["stages"]
    bounded = next(
        stage for stage in stages if stage["stage_id"] == "bounded_analysis_campaign"
    )
    bounded_transport = bounded["stage_contract_extension"][
        "review_input_snapshot_transport"
    ]
    assert bounded_transport == {
        "surface_kind": "mas_stage_review_input_snapshot_transport",
        "schema_version": 1,
        "manifest_scope": "analysis_generation",
        "review_lane_binding": "mas_stage_fixed",
        "review_lane": "statistical",
        "builder_ref": (
            "src/med_autoscience/authority_handlers/_generation_manifest.py#"
            "build_stage_review_input_snapshot_bundle"
        ),
        "producer_attempt_local_finalizer_ref": (
            "src/med_autoscience/authority_handlers/_stage_attempt_review_snapshot.py#"
            "finalize_bounded_analysis_producer_snapshot_closeout"
        ),
        "producer_finalizer_applies_when": (
            "complete_frozen_analysis_artifact_inventory_and_exact_"
            "statistical_locator_map_available"
        ),
        "zero_artifact_or_hard_boundary_snapshot_fabrication_allowed": False,
        "source_locator_policy": "explicit_source_refs_by_member_id_exact_scope",
        "missing_binding_effect": "quality_debt_without_quality_or_readiness_claim",
    }

    authoring = next(
        stage for stage in stages if stage["stage_id"] == "manuscript_authoring"
    )
    authoring_transport = authoring["stage_contract_extension"][
        "review_input_snapshot_transport"
    ]
    assert authoring_transport["review_lane_binding"] == "controller_required"
    assert authoring_transport["allowed_review_lanes"] == [
        "medical",
        "statistical",
        "reference",
        "display",
    ]
    assert authoring_transport["executor_may_select_lane"] is False


def test_publication_handoff_requires_one_exact_generation_package_sequence() -> None:
    stage_pack = _paper_stage_pack()
    handoff = next(
        stage
        for stage in stage_pack["stages"]
        if stage["stage_id"] == "08-publication_package_handoff"
    )
    currentness = handoff["done_definition"][
        "same_generation_package_currentness_contract"
    ]

    assert currentness["ordered_phases"] == PACKAGE_CURRENTNESS_PHASES
    assert currentness["single_generation_required"] is True
    assert currentness["exact_source_and_package_bytes_required"] is True
    assert currentness["stale_owner_sidecar_rejected"] is True
    assert (
        currentness["phase_completion_is_not_publication_or_submission_authority"]
        is True
    )
