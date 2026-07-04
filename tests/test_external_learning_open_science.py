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
            "refs": {
                "dispatch_path": "artifacts/supervision/openscience.json",
                "rerun_recipe_refs": ["artifacts/rerun/figure-1.json"],
                "permission_request_refs": ["artifacts/approvals/write-once.json"],
                "data_flow_disclosure_refs": ["artifacts/privacy/data-flow.json"],
                "connector_provisioning_refs": ["artifacts/connectors/pubmed.json"],
            },
            "artifact_candidates": [
                {
                    "artifact_id": "figure-1",
                    "artifact_ref": "artifacts/candidates/figure-1.png",
                    "claim_type": "computed",
                    "source_refs": ["sources/analysis.py"],
                    "log_refs": ["artifacts/logs/figure-1.json"],
                    "annotation_refs": ["annotations/reviewer-1.json"],
                    "environment_ref": "artifacts/env/python-lock.json",
                    "source_locator_ref": "src/figures/figure_1.py",
                    "content_hash": "sha256:figure1",
                },
                {
                    "artifact_id": "table-1",
                },
                {
                    "artifact_id": "figure-2",
                    "artifact_ref": "artifacts/candidates/figure-2.png",
                    "claim_type": "parsed",
                    "source_refs": ["sources/table.csv"],
                    "log_refs": ["artifacts/logs/figure-2.json"],
                    "annotation_refs": ["annotations/reviewer-2.json"],
                },
            ],
        }
    )

    assert advisory["surface_kind"] == "mas_openscience_artifact_provenance_advisory"
    assert advisory["framework_id"] == "openscience_artifact_provenance"
    assert advisory["source_ref"] == (
        "external_repo:ai4s-research/open-science@"
        "2200ad2ec4e2ac7c7ff59c5dcdfaeb0b9a5fda66"
    )
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
        "environment_capture_ref",
        "rerun_reproducibility_ref",
        "interactive_approval_or_permission_ref",
        "data_flow_disclosure_ref",
        "connector_provisioning_ref",
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
    assert advisory["environment_capture_ref"] == (
        "external-learning:openscience_artifact_provenance:"
        "dispatch-openscience-001:environment_capture"
    )
    assert advisory["rerun_reproducibility_ref"] == (
        "external-learning:openscience_artifact_provenance:"
        "dispatch-openscience-001:rerun_reproducibility"
    )
    assert advisory["interactive_approval_or_permission_ref"] == (
        "external-learning:openscience_artifact_provenance:"
        "dispatch-openscience-001:interactive_approval_or_permission"
    )
    assert advisory["data_flow_disclosure_ref"] == (
        "external-learning:openscience_artifact_provenance:"
        "dispatch-openscience-001:data_flow_disclosure"
    )
    assert advisory["connector_provisioning_ref"] == (
        "external-learning:openscience_artifact_provenance:"
        "dispatch-openscience-001:connector_provisioning"
    )
    assert advisory["claim_type_policy"] == {
        "allowed_claim_types": ["computed", "parsed", "digitized", "hypothesis"],
        "unknown_claim_type_warning": "missing_or_invalid_claim_type",
        "can_authorize_quality_verdict": False,
    }
    graph = advisory["artifact_graph_projection"]
    assert graph["surface_kind"] == "openscience_artifact_graph_refs_projection"
    assert graph["refs_only"] is True
    assert graph["node_count"] == 3
    assert graph["edge_count"] == 6
    assert graph["can_write_artifact_authority"] is False
    warnings = {
        (item["artifact_id"], item["warning_type"])
        for item in advisory["claim_warning_checks"]
    }
    assert warnings == {
        ("table-1", "missing_claim_type"),
        ("table-1", "untraced_artifact"),
        ("table-1", "unsupported_claim"),
        ("table-1", "missing_log"),
        ("table-1", "missing_environment_capture"),
        ("figure-2", "missing_source_locator_for_regeneration"),
        ("figure-2", "missing_environment_capture"),
    }
    assert advisory["annotation_regeneration_requests"] == [
        {
            "surface_kind": "openscience_annotation_regeneration_ref",
            "artifact_id": "figure-1",
            "annotation_refs": ["annotations/reviewer-1.json"],
            "source_locator_ref": "src/figures/figure_1.py",
            "status": "ready_for_source_regeneration_hint",
            "refs_only": True,
            "can_mutate_source": False,
            "can_write_artifact_body": False,
        },
        {
            "surface_kind": "openscience_annotation_regeneration_ref",
            "artifact_id": "figure-2",
            "annotation_refs": ["annotations/reviewer-2.json"],
            "source_locator_ref": None,
            "status": "missing_source_locator",
            "refs_only": True,
            "can_mutate_source": False,
            "can_write_artifact_body": False,
        },
    ]
    ledger_pointer = advisory["project_ledger_pointer"]
    assert ledger_pointer["surface_kind"] == "openscience_project_local_ledger_pointer"
    assert ledger_pointer["ledger_ref"] == (
        "external-learning:openscience_artifact_provenance:"
        "dispatch-openscience-001:project_ledger"
    )
    assert ledger_pointer["content_hash_algorithm"] == "sha256:stable-json"
    assert ledger_pointer["candidate_count"] == 3
    assert ledger_pointer["proves_owner_acceptance"] is False
    assert ledger_pointer["proves_artifact_authority"] is False
    assert advisory["native_viewer_watch_projection"] == {
        "surface_kind": "openscience_native_viewer_watch_projection",
        "watch_only": True,
        "viewer_ref": advisory["native_viewer_watch_ref"],
        "displayed_artifact_refs": [
            "artifacts/candidates/figure-1.png",
            "artifacts/candidates/figure-2.png",
        ],
        "can_authorize_visual_quality": False,
        "can_authorize_source_readiness": False,
        "can_authorize_publication_readiness": False,
    }
    assert advisory["environment_capture_briefing"] == {
        "surface_kind": "openscience_environment_capture_briefing",
        "candidate_ref": advisory["environment_capture_ref"],
        "environment_refs": ["artifacts/env/python-lock.json"],
        "refs_only": True,
        "body_included": False,
        "can_authorize_reproducibility": False,
    }
    assert advisory["rerun_reproducibility_route_back_hint"] == {
        "surface_kind": "openscience_rerun_reproducibility_route_back_hint",
        "candidate_ref": advisory["rerun_reproducibility_ref"],
        "rerun_recipe_refs": ["artifacts/rerun/figure-1.json"],
        "missing_ref_hints": [
            {
                "artifact_id": "table-1",
                "missing_ref_families": [
                    "source_refs",
                    "log_refs",
                    "content_hash",
                    "environment_refs",
                ],
            },
            {
                "artifact_id": "figure-2",
                "missing_ref_families": ["content_hash", "environment_refs"],
            },
        ],
        "refs_only": True,
        "can_block_current_owner_action": False,
        "can_write_typed_blocker": False,
        "can_authorize_artifact_authority": False,
    }
    assert advisory["interactive_approval_or_permission_hint"] == {
        "surface_kind": "openscience_interactive_approval_or_permission_hint",
        "candidate_ref": advisory["interactive_approval_or_permission_ref"],
        "permission_request_refs": ["artifacts/approvals/write-once.json"],
        "refs_only": True,
        "can_create_human_gate": False,
        "can_authorize_owner_action": False,
    }
    assert advisory["data_flow_disclosure_briefing"] == {
        "surface_kind": "openscience_data_flow_disclosure_briefing",
        "candidate_ref": advisory["data_flow_disclosure_ref"],
        "data_flow_refs": ["artifacts/privacy/data-flow.json"],
        "refs_only": True,
        "body_included": False,
        "can_authorize_privacy_or_source_readiness": False,
    }
    assert advisory["connector_provisioning_hint"] == {
        "surface_kind": "openscience_connector_provisioning_hint",
        "candidate_ref": advisory["connector_provisioning_ref"],
        "connector_refs": ["artifacts/connectors/pubmed.json"],
        "refs_only": True,
        "can_install_connector": False,
        "can_claim_runtime_landed": False,
    }


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
    assert openscience["connector_provisioning_ref"] == (
        "external-learning:openscience_artifact_provenance:unknown_dispatch:connector_provisioning"
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
