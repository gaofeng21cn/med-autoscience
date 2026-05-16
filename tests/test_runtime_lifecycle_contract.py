from __future__ import annotations

import importlib


def test_runtime_lifecycle_contract_exposes_shared_schema_and_authority_boundary() -> None:
    contract_module = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_contract")

    contract = contract_module.runtime_lifecycle_contract()

    assert contract["surface_kind"] == "runtime_lifecycle_sqlite_index"
    assert contract["schema_version"] == 1
    assert contract["default_db_filename"] == "runtime_lifecycle.sqlite"
    assert "publication_eval/latest.json" in contract["file_authority_surfaces"]
    assert "controller_decisions/latest.json" in contract["file_authority_surfaces"]
    assert "runtime_events" in contract["sqlite_sidecar_tables"]
    assert "lineage_nodes" in contract["sqlite_sidecar_tables"]
    assert "lineage_edges" in contract["sqlite_sidecar_tables"]
    assert "workspace_allocations" in contract["sqlite_sidecar_tables"]
    assert "runtime_snapshots" in contract["sqlite_sidecar_tables"]
    assert "snapshot_file_refs" in contract["sqlite_sidecar_tables"]
    assert "revision_diffs" in contract["sqlite_sidecar_tables"]
    assert "canvas_projection" in contract["sqlite_sidecar_tables"]
    assert "retention_actions" in contract["sqlite_sidecar_tables"]
    assert "migration_runs" in contract["sqlite_sidecar_tables"]
    assert "study_macro_state_snapshots" in contract["sqlite_sidecar_tables"]
    assert "owner_route_receipts" in contract["sqlite_sidecar_tables"]
    assert "dispatch_receipts" in contract["sqlite_sidecar_tables"]
    assert "turn_receipts" in contract["sqlite_sidecar_tables"]
    assert "paper_work_unit_receipts" in contract["sqlite_sidecar_tables"]
    assert "surface_refs" in contract["sqlite_sidecar_tables"]
    assert "apply" in contract["migration_run_modes"]
    assert "rollback_plan" in contract["migration_run_modes"]
    assert "*.sqlite-wal" in contract["sqlite_gitignore_patterns"]
    assert "*.sqlite-shm" in contract["sqlite_gitignore_patterns"]


def test_runtime_lifecycle_contract_declares_sidecar_index_not_macro_state_authority() -> None:
    contract_module = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_contract")

    contract = contract_module.runtime_lifecycle_contract()

    assert contract["sidecar_indexed_surfaces"] == [
        "study_macro_state_snapshot",
        "owner_route_receipt",
        "dispatch_receipt",
        "turn_receipt",
        "paper_work_unit_receipt",
        "surface_ref",
        "lineage_node",
        "lineage_edge",
        "workspace_allocation",
        "runtime_snapshot",
        "snapshot_file_ref",
        "revision_diff",
        "canvas_projection",
    ]
    assert contract["sidecar_authority_policy"] == "index_only_authority_remains_file_surfaces"
    assert contract["sidecar_role"] == "mas_domain_sidecar_index_reference_adapter"
    assert contract["generic_persistence_owner"] == "one-person-lab"
    assert contract["generic_persistence_engine_claim_allowed"] is False
    assert "study_macro_state/latest.json" in contract["file_authority_surfaces"]
    assert "runtime_supervisor_owner_route" in contract["file_authority_surfaces"]
    assert "runtime_supervisor_dispatch_receipt" in contract["file_authority_surfaces"]
    assert "paper_work_unit_outbox_receipt" in contract["file_authority_surfaces"]


def test_runtime_lifecycle_contract_declares_q1_q6_git_replacement_cutover() -> None:
    contract_module = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_contract")

    contract = contract_module.runtime_lifecycle_contract()

    assert contract["git_era_replacement_surfaces"] == {
        "quest_lineage": ["lineage_nodes", "lineage_edges"],
        "workspace_checkout_allocation": ["workspace_allocations"],
        "quest_runtime_snapshot": ["runtime_snapshots", "snapshot_file_refs"],
        "revision_comparison": ["revision_diffs"],
        "canvas_projection_index": ["canvas_projection"],
    }
    assert [item["quarter"] for item in contract["q1_q6_cutover_contract"]] == [
        "Q1",
        "Q2",
        "Q3",
        "Q4",
        "Q5",
        "Q6",
    ]
    assert contract["q1_q6_cutover_contract"][0]["required_tables"] == [
        "lineage_nodes",
        "lineage_edges",
        "workspace_allocations",
        "runtime_snapshots",
        "snapshot_file_refs",
        "revision_diffs",
        "canvas_projection",
    ]
    assert contract["q1_q6_cutover_contract"][-1]["required_proof"] == (
        "sqlite_lifecycle_store_remains_index_only_and_file_truth_surfaces_remain_authoritative"
    )


def test_migration_ledger_validation_is_structural_not_markdown_wording() -> None:
    contract_module = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_contract")
    payload = {
        field: "value" for field in contract_module.MIGRATION_LEDGER_REQUIRED_FIELDS
    }
    payload.update(
        {
            "mode": "dry_run",
            "schema_version": contract_module.SCHEMA_VERSION,
            "workspace_classification": "stopped_cold",
        }
    )

    assert contract_module.validate_migration_ledger(payload) == {
        "ok": True,
        "missing_required_fields": [],
        "invalid_fields": {},
    }

    invalid = dict(payload)
    invalid.pop("restore_proofs")
    invalid["mode"] = "implicit_cleanup"

    assert contract_module.validate_migration_ledger(invalid) == {
        "ok": False,
        "missing_required_fields": ["restore_proofs"],
        "invalid_fields": {"mode": "implicit_cleanup"},
    }


def test_compatibility_verification_validation_rejects_unknown_reader() -> None:
    contract_module = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_contract")
    payload = {
        field: "value" for field in contract_module.COMPATIBILITY_VERIFICATION_REQUIRED_FIELDS
    }
    payload["reader_name"] = "study_progress"

    assert contract_module.validate_compatibility_verification(payload)["ok"] is True

    payload["reader_name"] = "sqlite_as_publication_authority"
    result = contract_module.validate_compatibility_verification(payload)

    assert result["ok"] is False
    assert result["invalid_fields"] == {"reader_name": "sqlite_as_publication_authority"}


def test_sqlite_authority_contract_is_lifecycle_only_and_rejects_study_truth() -> None:
    contract_module = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_contract")

    contract = contract_module.runtime_lifecycle_contract()

    assert contract["sqlite_authority_scope"] == [
        "runtime_lifecycle",
        "runtime_index",
        "runtime_receipt",
        "runtime_retention",
        "runtime_cursor",
    ]
    assert contract["sqlite_forbidden_authority_surfaces"] == [
        "study_authority",
        "paper_authority",
        "publication_authority",
        "artifact_authority",
        "file_authority",
    ]

    allowed = contract_module.validate_sqlite_authority_scope(
        {
            "authority_scope": [
                "runtime_lifecycle",
                "runtime_index",
                "runtime_receipt",
                "runtime_retention",
                "runtime_cursor",
            ],
            "authority_surfaces": ["runtime_events", "retention_actions", "compatibility_exports"],
        }
    )
    assert allowed == {
        "ok": True,
        "invalid_scopes": [],
        "forbidden_authority_surfaces": [],
    }

    rejected = contract_module.validate_sqlite_authority_scope(
        {
            "authority_scope": ["runtime_lifecycle", "publication_authority"],
            "authority_surfaces": ["publication_eval/latest.json", "current_package.zip"],
        }
    )
    assert rejected == {
        "ok": False,
        "invalid_scopes": ["publication_authority"],
        "forbidden_authority_surfaces": ["publication_eval/latest.json", "current_package.zip"],
    }


def test_quest_git_retirement_policy_rejects_daily_lifecycle_git_usage() -> None:
    contract_module = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_contract")

    contract = contract_module.runtime_lifecycle_contract()

    assert contract["quest_live_writer_root_policy"] == "workspace_runtime_quests"
    assert contract["quest_git_retirement_policy"]["allowed_live_writer_roots"] == ["runtime/quests"]
    assert contract["quest_git_retirement_policy"]["legacy_import_restore_sources"] == [
        "quest-local .git",
        ".ds/worktrees",
        "ops/med-deepscientist runtime Git era",
    ]
    assert contract["quest_git_retirement_policy"]["forbidden_daily_lifecycle_surfaces"] == [
        "quest-local .git",
        ".ds/worktrees",
        "ops/med-deepscientist runtime Git era",
    ]

    allowed = contract_module.validate_quest_git_daily_lifecycle(
        {
            "live_writer_root": "runtime/quests",
            "daily_lifecycle_surfaces": ["runtime/quests"],
            "legacy_sources": ["quest-local .git", ".ds/worktrees"],
        }
    )
    assert allowed == {
        "ok": True,
        "invalid_live_writer_root": None,
        "forbidden_daily_lifecycle_surfaces": [],
        "invalid_legacy_sources": [],
    }

    rejected = contract_module.validate_quest_git_daily_lifecycle(
        {
            "live_writer_root": "quest-local .git",
            "daily_lifecycle_surfaces": ["runtime/quests", ".ds/worktrees"],
            "legacy_sources": ["workspace runtime/quests"],
        }
    )
    assert rejected == {
        "ok": False,
        "invalid_live_writer_root": "quest-local .git",
        "forbidden_daily_lifecycle_surfaces": [".ds/worktrees"],
        "invalid_legacy_sources": ["workspace runtime/quests"],
    }


def test_runtime_lifecycle_contract_declares_opl_family_adapter_surface() -> None:
    contract_module = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_contract")

    contract = contract_module.runtime_lifecycle_contract()

    assert contract["opl_family_adapter_surface"] == {
        "surface_kind": "mas_opl_family_persistence_lifecycle_owner_route_adoption",
        "shape": ["refs", "payload"],
        "authority": "refs_payload_projection_only",
        "maps_to_opl_contracts": {
            "persistence": "opl_family_persistence_contract.v1",
            "lifecycle": "opl_family_lifecycle_contract.v1",
            "owner_route": "opl_family_owner_route_contract.v1",
        },
        "source_tables": [
            "lineage_nodes",
            "lineage_edges",
            "workspace_allocations",
            "runtime_snapshots",
            "snapshot_file_refs",
            "revision_diffs",
            "canvas_projection",
            "study_macro_state_snapshots",
            "owner_route_receipts",
            "dispatch_receipts",
            "turn_receipts",
            "paper_work_unit_receipts",
            "surface_refs",
            "archive_refs",
            "report_index",
        ],
        "forbidden_authority_surfaces": [
            "publication_eval/latest.json",
            "controller_decisions/latest.json",
            "manuscript/current_package",
            "current_package.zip",
        ],
        "runtime_lifecycle_sqlite_role": {
            "classification": "A_opl_owned_mas_consumes",
            "current_mas_role": "mas_domain_sidecar_index_reference_adapter",
            "owner": "one-person-lab",
            "authority": "refs_payload_projection_only",
            "generic_persistence_engine_claim_allowed": False,
            "replacement_expectation_audit_ref": (
                "contracts/test-lane-manifest.json#focused_lanes/mas-functional-consumer-followthrough"
            ),
            "replacement_expected_from_opl": [
                "opl_runtime_lifecycle_index_contract",
                "opl_artifact_lifecycle_storage_audit_shell",
                "opl_restore_retention_receipt_shell",
                "opl_provider_attempt_receipt_ledger",
            ],
        },
    }
