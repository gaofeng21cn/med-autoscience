from __future__ import annotations

import importlib

from .shared import *  # noqa: F403,F401
from .action_catalog_parity import _write_opl_production_proof


def test_product_entry_manifest_projects_current_development_lines_closure(
    tmp_path: Path,
) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")

    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    proof_ref = tmp_path / "opl-production-proof.json"
    _write_opl_production_proof(proof_ref)

    manifest = product_entry.build_product_entry_manifest(
        profile=profile,
        profile_ref=profile_ref,
        opl_production_proof_ref=proof_ref,
    )
    closure = manifest["mas_functional_closure_status_projection"]

    assert closure["surface_kind"] == "mas_functional_closure_status_projection"
    assert closure["status"] == "functional_surfaces_projected_production_evidence_gated"
    assert closure["planning_ref"] == "docs/active/current_development_lines.md"
    assert closure["authority_boundary"]["read_only"] is True
    assert closure["authority_boundary"]["can_write_domain_truth"] is False
    assert closure["authority_boundary"]["can_write_memory_body"] is False
    assert closure["authority_boundary"]["can_authorize_publication_quality"] is False
    assert closure["authority_boundary"]["provider_completion_is_paper_closure"] is False
    assert closure["authority_boundary"]["publication_closure_claimed"] is False
    assert closure["summary"]["line_count"] == 9
    assert closure["summary"]["production_evidence_gate_count"] == 2
    assert closure["summary"]["production_evidence_pending_count"] == 2
    assert closure["summary"]["publication_closure_claimed"] is False
    assert closure["summary"]["provider_completion_is_paper_closure"] is False

    by_line = {line["line_id"]: line for line in closure["lines"]}
    assert set(by_line) == {
        "p2_provider_residency_and_activity_soak",
        "p2_mas_framework_migration",
        "publication_route_memory_management",
        "stage_surface_standardization",
        "p1_app_runtime_workbench",
        "p0_live_paper_autonomy_acceptance",
        "legacy_residue_retirement",
        "standard_skeleton_physicalization",
        "p3_foundation_guard",
    }
    provider_line = by_line["p2_provider_residency_and_activity_soak"]
    assert provider_line["status"] == "provider_residency_projected_domain_activity_soak_pending"
    assert provider_line["production_evidence_complete"] is False
    assert provider_line["typed_blockers"][0]["blocker_id"] == "mas_domain_activity_long_soak_pending"
    assert str(proof_ref) in provider_line["evidence_refs"]

    paper_line = by_line["p0_live_paper_autonomy_acceptance"]
    assert paper_line["status"] == "guarded_apply_surface_landed_live_provider_apply_pending"
    assert paper_line["production_evidence_complete"] is False
    assert paper_line["typed_blockers"][0]["blocker_id"] == "provider_hosted_live_paper_apply_pending"
    assert by_line["legacy_residue_retirement"]["status"] == (
        "no_active_default_caller_proven_cleanup_policy_satisfied"
    )
    assert by_line["legacy_residue_retirement"]["typed_blockers"] == []
    assert by_line["standard_skeleton_physicalization"]["status"] == (
        "repo_source_anchors_landed_ongoing_slot_discipline"
    )
    assert by_line["standard_skeleton_physicalization"]["typed_blockers"] == []
    assert "agent/standard-domain-agent-anchor.json" in by_line[
        "standard_skeleton_physicalization"
    ]["evidence_refs"]

    blocker_ids = {blocker["blocker_id"] for blocker in closure["open_typed_blockers"]}
    assert "mas_domain_activity_long_soak_pending" in blocker_ids
    assert "provider_hosted_live_paper_apply_pending" in blocker_ids
