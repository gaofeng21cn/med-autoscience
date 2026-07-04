from __future__ import annotations

import importlib
from pathlib import Path


FORBIDDEN_TRUTH_WRITES = {
    "artifacts/publication_eval/latest.json",
    "artifacts/controller_decisions/latest.json",
    "artifacts/owner_receipts/**",
    "artifacts/typed_blockers/**",
    "artifacts/artifact_authority/**",
    "paper/**",
    "manuscript/current_package/**",
    "submission_package/**",
    "current_package/**",
    "memory/**/body",
}


def test_openscience_worker_emits_refs_only_artifact_provenance_candidates() -> None:
    module = importlib.import_module("med_autoscience.external_learning_progress_workers")

    advisory = module.build_openscience_artifact_provenance_advisory(
        {
            "action_type": "unit_harmonized_external_validation_rerun",
            "action_id": "dispatch-openscience-001",
            "owner_route": {
                "owner": "artifact_authority",
                "work_unit_id": "figure-regeneration",
                "work_unit_fingerprint": "fp-openscience",
            },
            "refs": {"dispatch_path": "artifacts/supervision/openscience.json"},
        }
    )

    assert advisory["surface_kind"] == "mas_openscience_artifact_provenance_advisory"
    assert advisory["framework_id"] == "openscience_artifact_provenance"
    assert advisory["source_ref"] == "external_repo:OpenScience@f120290"
    assert advisory["refs_only"] is True
    assert advisory["advisory_only"] is True
    assert advisory["nonblocking"] is True
    assert advisory["fail_open"] is True
    assert advisory["mainline_waits"] is False
    assert advisory["mainline_waits_for_worker"] is False
    assert advisory["can_block_current_owner_action"] is False
    assert advisory["allowed_writes"] == []
    assert FORBIDDEN_TRUTH_WRITES <= set(advisory["forbidden_writes"])
    assert advisory["runtime_dependency"] is False
    assert advisory["electron_dependency"] is False
    assert advisory["mcp_dependency"] is False
    assert advisory["agpl_code_imported"] is False
    assert advisory["candidate_ref_families"] == [
        "artifact_graph_ref",
        "claim_warning_ref",
        "annotation_regeneration_ref",
        "project_ledger_ref",
        "skill_pack_governance_ref",
        "native_viewer_watch_ref",
    ]
    assert advisory["artifact_graph_ref"] == (
        "external-learning:openscience_artifact_provenance:"
        "dispatch-openscience-001:artifact_graph"
    )
    assert advisory["claim_warning_ref"] == (
        "external-learning:openscience_artifact_provenance:"
        "dispatch-openscience-001:claim_warning"
    )
    assert advisory["annotation_regeneration_ref"] == (
        "external-learning:openscience_artifact_provenance:"
        "dispatch-openscience-001:annotation_regeneration"
    )
    assert advisory["project_ledger_ref"] == (
        "external-learning:openscience_artifact_provenance:"
        "dispatch-openscience-001:project_ledger"
    )
    assert advisory["skill_pack_governance_ref"] == (
        "external-learning:openscience_artifact_provenance:"
        "dispatch-openscience-001:skill_pack_governance"
    )
    assert advisory["native_viewer_watch_ref"] == (
        "external-learning:openscience_artifact_provenance:"
        "dispatch-openscience-001:native_viewer_watch"
    )


def test_openscience_sidecar_dry_run_is_fail_open_without_dispatch(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.external_learning_adoption_closure")

    result = module.run_external_learning_sidecar(study_root=tmp_path / "study", apply=False)

    assert result["status"] == "dry_run"
    assert result["refs_only"] is True
    assert result["advisory_only"] is True
    assert result["nonblocking"] is True
    assert result["fail_open"] is True
    assert result["mainline_waits"] is False
    assert result["mainline_waits_for_sidecar"] is False
    assert result["can_block_current_owner_action"] is False
    assert result["allowed_writes"] == ["artifacts/advisory/external_learning_sidecar/latest.json"]
    assert FORBIDDEN_TRUTH_WRITES <= set(result["forbidden_writes"])

    candidates = {item["framework_id"]: item for item in result["advisory_candidates"]}
    assert "openscience_artifact_provenance" in candidates
    assert candidates["openscience_artifact_provenance"][
        "can_block_current_owner_action"
    ] is False
    workers = {item["framework_id"]: item for item in result["advisory_worker_results"]}
    openscience = workers["openscience_artifact_provenance"]
    assert openscience["diagnostic"] == {"reason": "missing_or_invalid_dispatch"}
    assert openscience["artifact_graph_ref"] == (
        "external-learning:openscience_artifact_provenance:unknown_dispatch:artifact_graph"
    )
    assert openscience["allowed_writes"] == []
    assert openscience["mainline_waits"] is False
    assert openscience["can_block_current_owner_action"] is False
    boundary = openscience["authority_boundary"]
    assert boundary["can_write_domain_truth"] is False
    assert boundary["can_write_publication_eval"] is False
    assert boundary["can_write_controller_decisions"] is False
    assert boundary["can_write_owner_receipt"] is False
    assert boundary["can_write_typed_blocker"] is False
    assert boundary["can_write_artifact_authority"] is False
    assert boundary["can_authorize_artifact_authority"] is False
    assert not (tmp_path / "study" / "artifacts").exists()
