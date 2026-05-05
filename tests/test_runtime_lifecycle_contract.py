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
    assert "retention_actions" in contract["sqlite_sidecar_tables"]
    assert "migration_runs" in contract["sqlite_sidecar_tables"]
    assert "apply" in contract["migration_run_modes"]
    assert "rollback_plan" in contract["migration_run_modes"]
    assert "*.sqlite-wal" in contract["sqlite_gitignore_patterns"]
    assert "*.sqlite-shm" in contract["sqlite_gitignore_patterns"]


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
