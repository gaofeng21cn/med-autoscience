from __future__ import annotations

from .common import (
    SCHOLARSKILLS_MODULE_IDS,
    SCHOLARSKILLS_RECEIPT_REF_KEYS_BY_MODULE,
    _structured_payload,
    _write_tables_materialized_package,
    importlib,
    json,
    Path,
)


def test_scientific_capability_registry_cli_consumes_materialized_scholarskills_package_as_refs_only(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_root = tmp_path / "studies" / "001-risk"
    package = _write_tables_materialized_package(tmp_path / "opl-package")

    exit_code = cli.main(
        [
            "scientific-capability-registry",
            "--mode",
            "owner-consumption",
            "--capability-id",
            "opl.scholarskills.tables",
            "--study-root",
            str(study_root),
            "--current-owner-delta-json",
            json.dumps(
                {
                    "action_type": "prepare_table_package",
                    "work_unit_id": "scholar-tables-cli-candidate",
                    "work_unit_fingerprint": "sha256:scholar-tables-cli",
                    "capability_families": ["scholarskills_tables"],
                }
            ),
            "--materialized-package-manifest-path",
            str(package["manifest_path"]),
        ]
    )

    assert exit_code == 0
    evidence = json.loads(capsys.readouterr().out)
    assert evidence["surface_kind"] == (
        "mas_scientific_capability_owner_consumption_evidence"
    )
    assert evidence["refs_only"] is True
    assert evidence["capability_id"] == "opl.scholarskills.tables"
    assert evidence["execution_receipt_status"] == "complete"
    assert evidence["missing_execution_receipt_ref_families"] == []
    assert evidence["execution_receipt_refs"]["table_manifest_ref"] == str(
        package["artifact_manifest_path"]
    )
    package_consumption = evidence["materialized_package_consumption"]
    assert package_consumption["refs_only"] is True
    assert package_consumption["manifest_path"] == str(package["manifest_path"].resolve())
    assert package_consumption["execution_receipt_path"] == str(
        package["receipt_path"].resolve()
    )
    assert package_consumption["authority_flags_false"] is True
    assert package_consumption["candidate_artifact_count"] == 4
    assert package_consumption["candidate_artifact_missing_inputs"] == [
        "owner_acceptance_ref"
    ]
    assert package_consumption["forbidden_written_file_collisions"] == []
    assert package_consumption["mas_consumer_written_files"] == []
    assert package_consumption["counts_as_paper_truth"] is False
    assert package_consumption["counts_as_owner_receipt"] is False
    assert package_consumption["can_authorize_publication_readiness"] is False
    assert package_consumption["can_write_publication_eval"] is False
    assert package_consumption["can_write_controller_decisions"] is False
    assert package_consumption["can_write_current_package"] is False
    assert package_consumption["can_write_paper_or_package"] is False
    assert package_consumption["can_write_study_truth"] is False
    assert package_consumption["can_write_typed_blocker"] is False
    assert package_consumption["can_write_human_gate"] is False
    assert evidence["counts_as_progress"] is False
    assert evidence["counts_as_paper_truth"] is False
    assert evidence["counts_as_owner_receipt"] is False
    assert evidence["can_authorize_publication_readiness"] is False
    assert evidence["owner_gate_request"]["request_status"] == (
        "ready_for_owner_gate_review"
    )
    assert evidence["owner_gate_request"]["non_authoritative_request"] is True
    assert evidence["owner_gate_request"]["candidate_artifact_count"] == 4
    cli_ref_artifact = next(
        artifact
        for artifact in evidence["owner_gate_request"]["candidate_artifacts"]
        if artifact["kind"] == "table_manifest"
        and artifact["ref"] == "opl-vault:tables/table_manifest.json"
    )
    assert cli_ref_artifact["authority"] is False
    assert evidence["owner_gate_request"]["candidate_artifact_missing_inputs"] == [
        "owner_acceptance_ref"
    ]
    assert evidence["owner_gate_handoff"]["handoff_status"] == (
        "ready_for_owner_gate_review"
    )
    assert evidence["owner_gate_handoff"]["candidate_artifact_missing_inputs"] == [
        "owner_acceptance_ref"
    ]
    assert evidence["owner_gate_handoff"]["mas_consumer_written_files"] == []
    assert evidence["required_owner_response_shapes"][0]["shape"] == (
        "owner_receipt_ref"
    )
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "package").exists()


def test_scientific_capability_registry_cli_index_exposes_inventory_surface(capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")

    exit_code = cli.main(
        [
            "scientific-capability-registry",
            "--mode",
            "index",
        ]
    )

    assert exit_code == 0
    registry = json.loads(capsys.readouterr().out)
    assert registry["surface_kind"] == "mas_scientific_capability_registry"
    assert registry["schema_version"] == 1
    assert registry["capability_count"] == len(registry["capabilities"])
    assert registry["default_policy"]["fail_open"] is True
    assert registry["default_policy"]["always_on_scan"] is False
    assert registry["default_policy"]["wildcard_action_triggers_require_explicit_capability_request"] is True
    assert registry["owner_consumption_evidence_schema"]["surface_kind"] == (
        "mas_scientific_capability_owner_consumption_evidence"
    )
    assert registry["authority_boundary"]["can_write_domain_truth"] is False
    assert registry["authority_boundary"]["can_write_owner_receipt"] is False


def test_scientific_capability_registry_cli_resolve_exposes_summary_surface(
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")

    exit_code = cli.main(
        [
            "scientific-capability-registry",
            "--mode",
            "resolve",
            "--current-owner-delta-json",
            json.dumps(
                {
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "repair-story",
                    "work_unit_fingerprint": "sha256:repair",
                }
            ),
        ]
    )

    assert exit_code == 0
    resolution = json.loads(capsys.readouterr().out)
    assert resolution["surface_kind"] == "mas_scientific_capability_resolution"
    assert resolution["schema_version"] == 1
    assert resolution["planning_root"] == "current_owner_delta"
    assert resolution["current_owner_delta"]["work_unit_id"] == "repair-story"
    assert resolution["status"] == "resolved"
    assert resolution["selected_count"] >= 1
    assert resolution["mainline_waits_for_capability"] is False
    assert resolution["missing_capability_blocks_owner_action"] is False
    assert resolution["authority_boundary"]["can_authorize_provider_admission"] is False
    assert resolution["authority_boundary"]["can_write_owner_receipt"] is False


def test_scientific_capability_registry_cli_rejects_materialized_package_module_mismatch(
    tmp_path: Path,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_root = tmp_path / "studies" / "001-risk"
    package = _write_tables_materialized_package(
        tmp_path / "opl-package",
        manifest_overrides={"module_id": "opl.scholarskills.review"},
    )

    try:
        cli.main(
            [
                "scientific-capability-registry",
                "--mode",
                "owner-consumption",
                "--capability-id",
                "opl.scholarskills.tables",
                "--study-root",
                str(study_root),
                "--materialized-package-manifest-path",
                str(package["manifest_path"]),
            ]
        )
    except SystemExit as exc:
        assert "module_id mismatch" in str(exc)
        assert "opl.scholarskills.review" in str(exc)
    else:
        raise AssertionError("mismatched module_id should fail closed")
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "package").exists()


def test_scientific_capability_registry_cli_rejects_materialized_package_authority_flag(
    tmp_path: Path,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_root = tmp_path / "studies" / "001-risk"
    package = _write_tables_materialized_package(
        tmp_path / "opl-package",
        receipt_overrides={
            "authority_flags": {
                "can_write_owner_receipt": True,
                "can_write_publication_eval": False,
            }
        },
    )

    try:
        cli.main(
            [
                "scientific-capability-registry",
                "--mode",
                "owner-consumption",
                "--capability-id",
                "opl.scholarskills.tables",
                "--study-root",
                str(study_root),
                "--materialized-package-manifest-path",
                str(package["manifest_path"]),
            ]
        )
    except SystemExit as exc:
        assert "authority flags must be false" in str(exc)
        assert "can_write_owner_receipt" in str(exc)
    else:
        raise AssertionError("truthy authority flag should fail closed")
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "package").exists()


def test_scientific_capability_registry_cli_rejects_materialized_package_forbidden_written_file(
    tmp_path: Path,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_root = tmp_path / "studies" / "001-risk"
    package = _write_tables_materialized_package(
        tmp_path / "opl-package",
        manifest_overrides={
            "written_files": [
                "artifacts/publication_eval/latest.json",
                "artifacts/tables/table_manifest.json",
            ]
        },
    )

    try:
        cli.main(
            [
                "scientific-capability-registry",
                "--mode",
                "owner-consumption",
                "--capability-id",
                "opl.scholarskills.tables",
                "--study-root",
                str(study_root),
                "--materialized-package-manifest-path",
                str(package["manifest_path"]),
            ]
        )
    except SystemExit as exc:
        assert "forbidden authority writes" in str(exc)
        assert "artifacts/publication_eval/latest.json" in str(exc)
    else:
        raise AssertionError("forbidden written_file should fail closed")
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "package").exists()


def test_scientific_capability_registry_cli_rejects_materialized_package_candidate_artifact_authority_claim(
    tmp_path: Path,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_root = tmp_path / "studies" / "001-risk"
    package = _write_tables_materialized_package(
        tmp_path / "opl-package",
        receipt_overrides={
            "candidate_artifact_bodies": {
                "table_summary": {
                    "body": {"rows": 2},
                    "counts_as_paper_truth": True,
                }
            }
        },
    )

    try:
        cli.main(
            [
                "scientific-capability-registry",
                "--mode",
                "owner-consumption",
                "--capability-id",
                "opl.scholarskills.tables",
                "--study-root",
                str(study_root),
                "--materialized-package-manifest-path",
                str(package["manifest_path"]),
            ]
        )
    except SystemExit as exc:
        assert "candidate artifact authority flags" in str(exc)
        assert "counts_as_paper_truth" in str(exc)
    else:
        raise AssertionError("candidate artifact authority claim should fail closed")
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "package").exists()


def test_scientific_capability_registry_rejects_file_materialized_scholarskills_authority_flags(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"
    receipt_path = tmp_path / "execution_receipt_candidate.json"
    receipt_path.write_text(
        json.dumps(
            {
                "module_id": "opl.scholarskills.tables",
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
        capability_id="opl.scholarskills.tables",
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
                "module_id": "opl.scholarskills.review",
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
        capability_id="opl.scholarskills.tables",
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
        assert "opl.scholarskills.review" in str(exc)
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
                "module_id": "opl.scholarskills.tables",
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
        capability_id="opl.scholarskills.tables",
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
