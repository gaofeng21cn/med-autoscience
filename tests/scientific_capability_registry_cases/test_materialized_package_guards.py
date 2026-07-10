from __future__ import annotations

from tests.scientific_capability_registry_cases.common import (
    SCHOLARSKILLS_MODULE_IDS,
    SCHOLARSKILLS_RECEIPT_REF_KEYS_BY_MODULE,
    _structured_payload,
    _write_tables_materialized_package,
    importlib,
    json,
    Path,
)


def test_scientific_capability_registry_rejects_file_materialized_scholarskills_authority_flags(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"
    receipt_path = tmp_path / "execution_receipt_candidate.json"
    receipt_path.write_text(
        json.dumps(
            {
                "module_id": "mas-scholar-skills.tables",
                "execution_receipt_refs": {
                    "input_fingerprint_ref": "opl-vault:inputs/tables.sha256",
                    "dependency_profile_ref": "opl-vault:prepare/tables-env.json",
                    "prepared_run_context_ref": "opl-vault:run-context/tables-run.json",
                    "table_manifest_ref": "opl-vault:tables/table-manifest.json",
                    "table_qc_ref": "opl-vault:tables/qc.json",
                },
                "authority_flags": {
                    "can_write_owner_receipt": True,
                    "can_write_publication_eval": False,
                },
            }
        ),
        encoding="utf-8",
    )
    current_owner_delta = {
        "action_type": "prepare_table_package",
        "action_id": "scholar-tables-bad-001",
        "work_unit_id": "scholar-tables-bad-candidate",
        "work_unit_fingerprint": "sha256:scholar-tables-bad",
        "capability_families": ["scholarskills_tables"],
    }
    invocation = module.invoke_scientific_capability(
        capability_id="mas-scholar-skills.tables",
        study_root=study_root,
        current_owner_delta=current_owner_delta,
        apply=True,
    )

    try:
        module.build_capability_owner_consumption_evidence(
            invocation_result=invocation,
            current_owner_delta=current_owner_delta,
            execution_receipt_path=receipt_path,
        )
    except ValueError as exc:
        assert "can_write_owner_receipt" in str(exc)
    else:
        raise AssertionError("truthy authority flag should fail closed")
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "package").exists()


def test_scientific_capability_registry_rejects_file_materialized_scholarskills_module_mismatch(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"
    receipt_path = tmp_path / "execution_receipt_candidate.json"
    receipt_path.write_text(
        json.dumps(
            {
                "module_id": "mas-scholar-skills.review",
                "execution_receipt_refs": {
                    "input_fingerprint_ref": "opl-vault:inputs/tables.sha256",
                    "dependency_profile_ref": "opl-vault:prepare/tables-env.json",
                    "prepared_run_context_ref": "opl-vault:run-context/tables-run.json",
                    "table_manifest_ref": "opl-vault:tables/table-manifest.json",
                    "table_qc_ref": "opl-vault:tables/qc.json",
                },
                "authority_flags": {
                    "can_write_owner_receipt": False,
                    "can_write_publication_eval": False,
                },
            }
        ),
        encoding="utf-8",
    )
    invocation = module.invoke_scientific_capability(
        capability_id="mas-scholar-skills.tables",
        study_root=study_root,
        current_owner_delta={
            "action_type": "prepare_table_package",
            "work_unit_id": "scholar-tables-mismatch-candidate",
            "capability_families": ["scholarskills_tables"],
        },
        apply=True,
    )

    try:
        module.build_capability_owner_consumption_evidence(
            invocation_result=invocation,
            execution_receipt_path=receipt_path,
        )
    except ValueError as exc:
        assert "module_id mismatch" in str(exc)
        assert "mas-scholar-skills.review" in str(exc)
    else:
        raise AssertionError("mismatched module_id should fail closed")
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "package").exists()


def test_scientific_capability_registry_rejects_file_materialized_scholarskills_top_level_authority_claims(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"
    receipt_path = tmp_path / "execution_receipt_candidate.json"
    receipt_path.write_text(
        json.dumps(
            {
                "module_id": "mas-scholar-skills.tables",
                "counts_as_paper_truth": True,
                "execution_receipt_refs": {
                    "input_fingerprint_ref": "opl-vault:inputs/tables.sha256",
                    "dependency_profile_ref": "opl-vault:prepare/tables-env.json",
                    "prepared_run_context_ref": "opl-vault:run-context/tables-run.json",
                    "table_manifest_ref": "opl-vault:tables/table-manifest.json",
                    "table_qc_ref": "opl-vault:tables/qc.json",
                },
                "authority_flags": {
                    "can_write_owner_receipt": False,
                    "can_write_publication_eval": False,
                },
            }
        ),
        encoding="utf-8",
    )
    invocation = module.invoke_scientific_capability(
        capability_id="mas-scholar-skills.tables",
        study_root=study_root,
        current_owner_delta={
            "action_type": "prepare_table_package",
            "work_unit_id": "scholar-tables-top-level-authority-candidate",
            "capability_families": ["scholarskills_tables"],
        },
        apply=True,
    )

    try:
        module.build_capability_owner_consumption_evidence(
            invocation_result=invocation,
            execution_receipt_path=receipt_path,
        )
    except ValueError as exc:
        assert "counts_as_paper_truth" in str(exc)
    else:
        raise AssertionError("truthy top-level authority claim should fail closed")
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "package").exists()
