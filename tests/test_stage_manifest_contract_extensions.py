from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

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


def _stage_manifest() -> dict[str, object]:
    return json.loads(
        (REPO_ROOT / "agent/stages/manifest.json").read_text(encoding="utf-8")
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
