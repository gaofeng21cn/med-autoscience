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


def test_scientific_capability_registry_indexes_resolves_and_invokes_all_scholarskills_modules(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"

    registry = module.build_scientific_capability_registry()
    capabilities = {
        item["capability_id"]: item
        for item in registry["capabilities"]
    }

    assert set(SCHOLARSKILLS_MODULE_IDS) <= set(capabilities)
    for module_id in SCHOLARSKILLS_MODULE_IDS:
        capability = capabilities[module_id]
        module_name = module_id.removeprefix("opl.scholarskills.")

        assert capability["module_id"] == module_id
        assert capability["capability_family"] == f"scholarskills_{module_name}"
        assert capability["invocation_kind"] == "descriptor_only_current_owner_input_refs"
        assert capability["descriptor_only"] is True
        assert capability["refs_only"] is True
        assert capability["external_runner_invocation_allowed"] is False
        assert "contracts/opl-framework/scholar-skills-capability-modules.json" in capability[
            "descriptor_refs"
        ]
        assert "opl:runtime-env:prepare" in capability["dependency_profile_refs"]
        assert "opl:run-context:prepared-runtime-env" in capability["run_context_refs"]
        assert capability["artifact_refs"]
        assert capability["execution_receipt_expectation"]["module_id"] == module_id
        assert capability["execution_receipt_expectation"][
            "execution_receipt_can_authorize_publication_readiness"
        ] is False
        assert capability["owner_consumption_boundary"]["candidate_output_only"] is True
        assert capability["owner_consumption_boundary"]["counts_as_paper_truth"] is False
        assert capability["authority_boundary"]["can_write_publication_eval"] is False
        assert capability["authority_boundary"]["can_write_owner_receipt"] is False

        current_owner_delta = {
            "action_type": f"prepare_{module_name}_candidate",
            "action_id": f"{module_name}-001",
            "work_unit_id": f"{module_name}-candidate",
            "work_unit_fingerprint": f"sha256:{module_name}",
            "capability_families": [capability["capability_family"]],
        }
        resolution = module.resolve_scientific_capabilities(
            current_owner_delta=current_owner_delta,
        )
        selected = {
            item["capability_id"]: item
            for item in resolution["selected_capabilities"]
        }
        assert module_id in selected
        assert selected[module_id]["trigger_reason"] == (
            "current_delta_requested_capability_family"
        )

        invocation = module.invoke_scientific_capability(
            capability_id=module_id,
            study_root=study_root,
            current_owner_delta=current_owner_delta,
            apply=True,
        )
        assert invocation["status"] == "descriptor_only"
        assert invocation["request_only"] is False
        assert invocation["descriptor_only"] is True
        assert invocation["external_runner_invocation_allowed"] is False
        assert invocation["opl_capability_runtime_required"] is False
        assert invocation["result"]["readback"]["module_id"] == module_id
        assert invocation["result"]["readback"]["execution_receipt_expectation"][
            "module_id"
        ] == module_id
        assert invocation["result"]["readback"]["owner_consumption_boundary"][
            "counts_as_owner_receipt"
        ] is False


def test_scientific_capability_registry_indexes_and_resolves_scholar_display_descriptor(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"
    current_owner_delta = {
        "action_type": "prepare_manuscript_visual_package",
        "action_id": "scholar-display-001",
        "owner": "display",
        "work_unit_id": "scholar-display-candidate",
        "work_unit_fingerprint": "sha256:scholar-display",
        "capability_families": ["scholarskills_display"],
        "declared_needs": [
            "Scholar Display refs",
            "Display Pack gallery preview",
            "publication display candidate artifact refs",
        ],
    }

    registry = module.build_scientific_capability_registry()
    capabilities = {
        item["capability_id"]: item
        for item in registry["capabilities"]
    }
    capability = capabilities["opl.scholarskills.display"]

    assert capability["module_id"] == "opl.scholarskills.display"
    assert capability["capability_family"] == "scholarskills_display"
    assert capability["invocation_kind"] == "descriptor_only_current_owner_input_refs"
    assert capability["descriptor_only"] is True
    assert capability["refs_only"] is True
    assert capability["external_runner_invocation_allowed"] is False
    assert capability["bridged_capability_refs"] == [
        "scientific-capability:display_pack_visual_capability",
        "display-pack-contract.v2",
    ]
    assert "contracts/display-pack-contract.v2.json" in capability["descriptor_refs"]
    assert {
        "opl:runtime-env:prepare",
        "opl:scholarskills.display:dependency-profile",
        "opl:scholarskills.display:doctor",
    } <= set(capability["dependency_profile_refs"])
    assert {
        "opl:run-context:prepared-runtime-env",
        "opl:scholarskills.display:run-context",
        "opl:scholarskills.display:render-cache",
    } <= set(capability["run_context_refs"])
    assert {
        "display_pack_agent_orchestration",
        "paper/build/display_pack_lock.json",
        "paper/figure_render_receipt.json",
        "paper/figure_visual_audit_receipt.json",
        "display_pack_gallery_manifest",
    } <= set(capability["artifact_refs"])
    assert capability["execution_receipt_expectation"] == {
        "surface_kind": "mas_scholar_display_execution_receipt_expectation",
        "schema_version": 1,
        "module_id": "opl.scholarskills.display",
        "receipt_owner": "one-person-lab",
        "receipt_role": "candidate_display_execution_receipt",
        "required_ref_families": [
            "input_fingerprint_ref",
            "dependency_profile_ref",
            "prepared_run_context_ref",
            "render_cache_ref",
            "artifact_manifest_ref",
            "visual_audit_or_gallery_preview_ref",
        ],
        "mas_owner_receipt_required_for_paper_truth": True,
        "execution_receipt_can_authorize_publication_readiness": False,
    }
    assert capability["owner_consumption_boundary"] == {
        "surface_kind": "mas_scholar_display_owner_consumption_boundary",
        "schema_version": 1,
        "candidate_output_only": True,
        "owner_consumption_evidence": "refs_only",
        "counts_as_paper_truth": False,
        "counts_as_current_package_authority": False,
        "counts_as_owner_receipt": False,
        "mas_owner_gate_required_for_paper_truth": True,
    }
    assert capability["authority_boundary"]["can_write_publication_eval"] is False
    assert capability["authority_boundary"]["can_write_paper_or_package"] is False
    assert capability["authority_boundary"]["can_write_owner_receipt"] is False

    resolution = module.resolve_scientific_capabilities(
        current_owner_delta=current_owner_delta,
    )
    selected = {
        item["capability_id"]: item
        for item in resolution["selected_capabilities"]
    }
    candidate = selected["opl.scholarskills.display"]

    assert candidate["module_id"] == "opl.scholarskills.display"
    assert candidate["trigger_reason"] == "current_delta_requested_capability_family"
    assert candidate["descriptor_only"] is True
    assert candidate["refs_only"] is True
    assert candidate["external_runner_invocation_allowed"] is False
    assert candidate["can_block_current_owner_action"] is False
    assert candidate["descriptor_refs"] == capability["descriptor_refs"]
    assert candidate["dependency_profile_refs"] == capability["dependency_profile_refs"]
    assert candidate["run_context_refs"] == capability["run_context_refs"]
    assert candidate["artifact_refs"] == capability["artifact_refs"]
    assert candidate["execution_receipt_expectation"] == capability[
        "execution_receipt_expectation"
    ]
    assert candidate["owner_consumption_boundary"] == capability[
        "owner_consumption_boundary"
    ]
    assert candidate["readback"]["module_id"] == "opl.scholarskills.display"
    assert candidate["readback"]["authority_false_flags"] == {
        "can_write_domain_truth": False,
        "can_write_publication_eval": False,
        "can_write_controller_decisions": False,
        "can_write_paper_or_package": False,
        "can_write_memory_body": False,
        "can_write_owner_receipt": False,
        "can_write_typed_blocker": False,
        "can_authorize_owner_action": False,
        "can_authorize_provider_admission": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_artifact_authority": False,
        "can_close_stage": False,
    }

    invocation = module.invoke_scientific_capability(
        capability_id="opl.scholarskills.display",
        study_root=study_root,
        current_owner_delta=current_owner_delta,
        apply=True,
    )
    assert invocation["status"] == "descriptor_only"
    assert invocation["request_only"] is False
    assert invocation["descriptor_only"] is True
    assert invocation["external_runner_invocation_allowed"] is False
    assert invocation["opl_capability_runtime_required"] is False
    assert invocation["output_refs"] == capability["output_refs"]
    assert invocation["result"]["contract_refs"] == capability["contract_refs"]
    assert invocation["result"]["readback"]["dependency_profile_refs"] == capability[
        "dependency_profile_refs"
    ]
    assert invocation["result"]["readback"]["run_context_refs"] == capability[
        "run_context_refs"
    ]
    assert invocation["result"]["readback"]["owner_consumption_boundary"][
        "owner_consumption_evidence"
    ] == "refs_only"
    assert invocation["authority_boundary"]["can_write_publication_eval"] is False
    assert invocation["authority_boundary"]["can_write_controller_decisions"] is False
    assert invocation["authority_boundary"]["can_write_paper_or_package"] is False
    assert invocation["authority_boundary"]["can_write_owner_receipt"] is False
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "package").exists()

    evidence = module.build_capability_owner_consumption_evidence(
        invocation_result=invocation,
        current_owner_delta=current_owner_delta,
    )
    assert evidence["capability_id"] == "opl.scholarskills.display"
    assert evidence["refs_only"] is True
    assert evidence["owner_consumption_status"] == "no_owner_response_refs"
    assert evidence["consumption_evidence_only"] is True
    assert evidence["counts_as_progress"] is False
    assert evidence["owner_receipt_ref"] is None
    assert evidence["typed_blocker_ref"] is None
    assert evidence["can_authorize_owner_action"] is False
    assert evidence["can_authorize_publication_readiness"] is False
    assert evidence["counts_as_paper_truth"] is False
    assert evidence["counts_as_owner_receipt"] is False
    assert evidence["execution_receipt_status"] == "missing_required_refs"
    assert evidence["observed_execution_receipt_ref_families"] == []
    assert evidence["missing_execution_receipt_ref_families"] == [
        "input_fingerprint_ref",
        "dependency_profile_ref",
        "prepared_run_context_ref",
        "render_cache_ref",
        "artifact_manifest_ref",
        "visual_audit_or_gallery_preview_ref",
    ]
    assert evidence["no_forbidden_write_proof"]["forbidden_refs_absent"] is True


def test_scientific_capability_registry_consumes_opl_scholar_display_receipt_candidate_as_refs_only(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"
    current_owner_delta = {
        "action_type": "prepare_manuscript_visual_package",
        "action_id": "scholar-display-001",
        "owner": "display",
        "work_unit_id": "scholar-display-candidate",
        "work_unit_fingerprint": "sha256:scholar-display",
        "capability_families": ["scholarskills_display"],
    }
    invocation = module.invoke_scientific_capability(
        capability_id="opl.scholarskills.display",
        study_root=study_root,
        current_owner_delta=current_owner_delta,
        apply=True,
    )

    opl_receipt_candidate = {
        "surface_kind": "opl_scholarskills_execution_receipt_candidate",
        "status": "receipt_candidate_unsigned",
        "module_id": "opl.scholarskills.display",
        "execution_receipt_ref": "opl-vault:receipts/scholar-display/receipt.json",
        "execution_receipt_refs": {
            "input_fingerprint_ref": "opl-vault:inputs/fingerprint.sha256",
            "dependency_profile_ref": "opl-vault:prepare/display-env.json",
            "prepared_run_context_ref": "opl-vault:run-context/display-run.json",
            "render_cache_ref": "opl-vault:cache/display-render-cache.json",
            "artifact_manifest_ref": "opl-vault:artifacts/display-manifest.json",
            "visual_audit_or_gallery_preview_ref": "opl-vault:gallery/preview.json",
        },
        "execution_receipt_counts_as_candidate_artifact": True,
        "counts_as_paper_truth": False,
        "counts_as_owner_receipt": False,
        "can_authorize_publication_readiness": False,
        "can_sign_owner_receipt": False,
    }

    evidence = module.build_capability_owner_consumption_evidence(
        invocation_result=invocation,
        current_owner_delta=current_owner_delta,
        execution_receipt=opl_receipt_candidate,
    )

    assert evidence["execution_receipt_ref"] == (
        "opl-vault:receipts/scholar-display/receipt.json"
    )
    assert evidence["execution_receipt_status"] == "complete"
    assert evidence["observed_execution_receipt_ref_families"] == [
        "input_fingerprint_ref",
        "dependency_profile_ref",
        "prepared_run_context_ref",
        "render_cache_ref",
        "artifact_manifest_ref",
        "visual_audit_or_gallery_preview_ref",
    ]
    assert evidence["missing_execution_receipt_ref_families"] == []
    assert evidence["execution_receipt_refs"] == {
        "input_fingerprint_ref": "opl-vault:inputs/fingerprint.sha256",
        "dependency_profile_ref": "opl-vault:prepare/display-env.json",
        "prepared_run_context_ref": "opl-vault:run-context/display-run.json",
        "render_cache_ref": "opl-vault:cache/display-render-cache.json",
        "artifact_manifest_ref": "opl-vault:artifacts/display-manifest.json",
        "visual_audit_or_gallery_preview_ref": "opl-vault:gallery/preview.json",
    }
    assert evidence["execution_receipt_counts_as_candidate_artifact"] is True
    assert evidence["counts_as_progress"] is False
    assert evidence["counts_as_paper_truth"] is False
    assert evidence["counts_as_owner_receipt"] is False
    assert evidence["can_authorize_owner_action"] is False
    assert evidence["can_authorize_publication_readiness"] is False
    assert evidence["authority_boundary"]["can_write_publication_eval"] is False
    assert evidence["authority_boundary"]["can_write_controller_decisions"] is False
    assert evidence["authority_boundary"]["can_write_owner_receipt"] is False
    assert evidence["authority_boundary"]["can_write_typed_blocker"] is False
    assert evidence["no_forbidden_write_proof"]["forbidden_refs_absent"] is True
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "package").exists()


def test_scientific_capability_registry_scholar_display_missing_receipt_refs_and_owner_refs_stay_non_authorizing(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"
    current_owner_delta = {
        "action_type": "prepare_manuscript_visual_package",
        "action_id": "scholar-display-002",
        "owner": "display",
        "work_unit_id": "scholar-display-candidate",
        "work_unit_fingerprint": "sha256:scholar-display-missing",
        "capability_families": ["scholarskills_display"],
    }
    invocation = module.invoke_scientific_capability(
        capability_id="opl.scholarskills.display",
        study_root=study_root,
        current_owner_delta=current_owner_delta,
        apply=True,
    )

    evidence = module.build_capability_owner_consumption_evidence(
        invocation_result=invocation,
        current_owner_delta=current_owner_delta,
        dependency_prepared_receipt_ref="opl-vault:prepare/display-env.json",
        artifact_manifest_ref="opl-vault:artifacts/display-manifest.json",
        owner_response_refs={
            "owner_receipt_ref": "artifacts/stage_outputs/08-publication_package_handoff/receipts/owner_receipt.json",
            "typed_blocker_ref": "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
        },
    )

    assert evidence["owner_consumption_status"] == "owner_response_refs_observed"
    assert evidence["owner_receipt_ref"] == (
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/owner_receipt.json"
    )
    assert evidence["typed_blocker_ref"] == (
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
    )
    assert evidence["execution_receipt_status"] == "missing_required_refs"
    assert evidence["observed_execution_receipt_ref_families"] == [
        "dependency_profile_ref",
        "artifact_manifest_ref",
    ]
    assert evidence["missing_execution_receipt_ref_families"] == [
        "input_fingerprint_ref",
        "prepared_run_context_ref",
        "render_cache_ref",
        "visual_audit_or_gallery_preview_ref",
    ]
    assert evidence["execution_receipt_counts_as_candidate_artifact"] is False
    assert evidence["counts_as_progress"] is False
    assert evidence["counts_as_paper_truth"] is False
    assert evidence["counts_as_owner_receipt"] is False
    assert evidence["can_authorize_owner_action"] is False
    assert evidence["can_authorize_publication_readiness"] is False
    tail = evidence["standard_agent_feedback_loop_tail"]
    assert tail["owner_answer_or_typed_blocker_observed"] is True
    assert tail["counts_as_opl_family_completion"] is False
    assert evidence["authority_boundary"]["can_write_owner_receipt"] is False
    assert evidence["authority_boundary"]["can_write_typed_blocker"] is False
    assert evidence["authority_boundary"]["can_authorize_publication_readiness"] is False
    assert evidence["no_forbidden_write_proof"]["forbidden_refs_absent"] is True
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "package").exists()


def test_scientific_capability_registry_consumes_non_display_scholarskills_receipts_as_refs_only(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"
    current_owner_delta = {
        "action_type": "prepare_table_package",
        "action_id": "scholar-tables-001",
        "work_unit_id": "scholar-tables-candidate",
        "work_unit_fingerprint": "sha256:scholar-tables",
        "capability_families": ["scholarskills_tables"],
    }
    invocation = module.invoke_scientific_capability(
        capability_id="opl.scholarskills.tables",
        study_root=study_root,
        current_owner_delta=current_owner_delta,
        apply=True,
    )

    complete_receipt = {
        "surface_kind": "opl_scholarskills_execution_receipt_candidate",
        "status": "receipt_candidate_unsigned",
        "module_id": "opl.scholarskills.tables",
        "execution_receipt_ref": "opl-vault:receipts/scholar-tables/receipt.json",
        "execution_receipt_refs": {
            "input_fingerprint_ref": "opl-vault:inputs/tables.sha256",
            "dependency_profile_ref": "opl-vault:prepare/tables-env.json",
            "prepared_run_context_ref": "opl-vault:run-context/tables-run.json",
            "table_manifest_ref": "opl-vault:tables/table-manifest.json",
            "table_qc_ref": "opl-vault:tables/qc.json",
        },
        "counts_as_paper_truth": False,
        "counts_as_owner_receipt": False,
        "can_authorize_publication_readiness": False,
    }
    evidence = module.build_capability_owner_consumption_evidence(
        invocation_result=invocation,
        current_owner_delta=current_owner_delta,
        execution_receipt=complete_receipt,
    )

    assert evidence["capability_id"] == "opl.scholarskills.tables"
    assert evidence["execution_receipt_status"] == "complete"
    assert evidence["missing_execution_receipt_ref_families"] == []
    assert evidence["observed_execution_receipt_ref_families"] == [
        "input_fingerprint_ref",
        "dependency_profile_ref",
        "prepared_run_context_ref",
        "table_manifest_ref",
        "table_qc_ref",
    ]
    assert evidence["execution_receipt_counts_as_candidate_artifact"] is True
    assert evidence["counts_as_progress"] is False
    assert evidence["counts_as_paper_truth"] is False
    assert evidence["counts_as_owner_receipt"] is False
    assert evidence["can_authorize_publication_readiness"] is False
    assert "owner_gate_request" not in evidence
    assert "owner_gate_handoff" not in evidence
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "package").exists()

    missing_evidence = module.build_capability_owner_consumption_evidence(
        invocation_result=invocation,
        current_owner_delta=current_owner_delta,
        execution_receipt_refs={
            "dependency_prepared_receipt_ref": "opl-vault:prepare/tables-env.json",
            "table_manifest_ref": "opl-vault:tables/table-manifest.json",
        },
    )

    assert missing_evidence["execution_receipt_status"] == "missing_required_refs"
    assert missing_evidence["observed_execution_receipt_ref_families"] == [
        "dependency_profile_ref",
        "table_manifest_ref",
    ]
    assert missing_evidence["missing_execution_receipt_ref_families"] == [
        "input_fingerprint_ref",
        "prepared_run_context_ref",
        "table_qc_ref",
    ]
    assert missing_evidence["execution_receipt_counts_as_candidate_artifact"] is False
    assert missing_evidence["counts_as_owner_receipt"] is False


def test_scientific_capability_registry_consumes_opl_shaped_receipts_for_every_scholarskills_module(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"

    for module_id, expected_ref_keys in SCHOLARSKILLS_RECEIPT_REF_KEYS_BY_MODULE.items():
        module_name = module_id.removeprefix("opl.scholarskills.")
        current_owner_delta = {
            "action_type": f"prepare_{module_name}_candidate",
            "action_id": f"{module_name}-receipt-001",
            "work_unit_id": f"{module_name}-receipt-candidate",
            "work_unit_fingerprint": f"sha256:{module_name}-receipt",
            "capability_families": [f"scholarskills_{module_name}"],
        }
        invocation = module.invoke_scientific_capability(
            capability_id=module_id,
            study_root=study_root / module_name,
            current_owner_delta=current_owner_delta,
            apply=True,
        )
        complete_receipt = {
            "surface_kind": "opl_scholarskills_execution_receipt_candidate",
            "status": "receipt_candidate_unsigned",
            "module_id": module_id,
            "execution_receipt_ref": f"opl-vault:receipts/{module_name}/receipt.json",
            "execution_receipt_refs": {
                ref_key: f"opl-vault:{module_name}/{ref_key}.json"
                for ref_key in expected_ref_keys
            },
            "counts_as_paper_truth": False,
            "counts_as_owner_receipt": False,
            "can_authorize_publication_readiness": False,
        }
        evidence = module.build_capability_owner_consumption_evidence(
            invocation_result=invocation,
            current_owner_delta=current_owner_delta,
            execution_receipt=complete_receipt,
        )

        assert invocation["result"]["readback"]["execution_receipt_expectation"][
            "required_ref_families"
        ] == expected_ref_keys
        assert evidence["capability_id"] == module_id
        assert evidence["execution_receipt_status"] == "complete"
        assert evidence["missing_execution_receipt_ref_families"] == []
        assert evidence["observed_execution_receipt_ref_families"] == expected_ref_keys
        assert list(evidence["execution_receipt_refs"]) == expected_ref_keys
        assert evidence["execution_receipt_counts_as_candidate_artifact"] is True
        assert evidence["counts_as_progress"] is False
        assert evidence["counts_as_paper_truth"] is False
        assert evidence["counts_as_owner_receipt"] is False
        assert evidence["can_authorize_publication_readiness"] is False


def test_scientific_capability_registry_consumes_file_materialized_scholarskills_package_as_refs_only(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"
    package_root = tmp_path / "opl-package"
    package_root.mkdir()
    receipt_path = package_root / "execution_receipt_candidate.json"
    manifest_path = package_root / "manifest.json"
    artifact_manifest_path = package_root / "artifacts" / "table_manifest.json"
    artifact_manifest_path.parent.mkdir()
    artifact_manifest_path.write_text('{"items":[]}', encoding="utf-8")
    receipt_path.write_text(
        json.dumps(
            {
                "surface_kind": "opl_scholarskills_execution_receipt_candidate",
                "module_id": "opl.scholarskills.tables",
                "execution_receipt_ref": "opl-vault:receipts/tables/receipt.json",
                "artifact_manifest_path": str(artifact_manifest_path),
                "candidate_artifacts": [
                    {
                        "kind": "table_manifest",
                        "ref": "opl-vault:tables/table_manifest.json",
                        "sha256": "sha256:table-manifest",
                        "readiness_notes": [
                            "candidate table package ready for MAS owner review"
                        ],
                        "missing_inputs": [],
                    }
                ],
                "candidate_artifact_bodies": {
                    "table_summary": {
                        "body": {"rows": 2, "columns": ["metric", "value"]},
                        "readiness_notes": [
                            "body carried only as candidate artifact evidence"
                        ],
                        "missing_inputs": ["owner_acceptance_ref"],
                    }
                },
                "execution_receipt_refs": {
                    "input_fingerprint_ref": "opl-vault:inputs/tables.sha256",
                    "dependency_profile_ref": "opl-vault:prepare/tables-env.json",
                    "prepared_run_context_ref": "opl-vault:run-context/tables-run.json",
                    "table_qc_ref": "opl-vault:tables/qc.json",
                },
                "written_files": [
                    "opl-vault:tables/table_manifest.json",
                    "opl-vault:tables/qc.json",
                ],
                "sha256": "sha256:receipt",
                "authority_flags": {
                    "can_write_publication_eval": False,
                    "can_write_controller_decisions": False,
                    "can_write_current_package": False,
                    "can_write_paper_or_package": False,
                    "can_write_study_truth": False,
                    "can_write_owner_receipt": False,
                    "can_write_typed_blocker": False,
                    "can_write_human_gate": False,
                },
            }
        ),
        encoding="utf-8",
    )
    manifest_path.write_text(
        json.dumps(
            {
                "surface_kind": "opl_scholarskills_materialized_package_manifest",
                "module_id": "opl.scholarskills.tables",
                "execution_receipt_candidate_path": receipt_path.name,
                "artifact_manifest_path": str(artifact_manifest_path),
                "written_files": [str(artifact_manifest_path)],
                "sha256": "sha256:manifest",
                "authority_flags": {
                    "can_write_publication_eval": False,
                    "can_write_controller_decisions": False,
                    "can_write_current_package": False,
                    "can_write_paper_or_package": False,
                    "can_write_study_truth": False,
                    "can_write_owner_receipt": False,
                    "can_write_typed_blocker": False,
                    "can_write_human_gate": False,
                },
            }
        ),
        encoding="utf-8",
    )
    current_owner_delta = {
        "action_type": "prepare_table_package",
        "action_id": "scholar-tables-file-001",
        "work_unit_id": "scholar-tables-file-candidate",
        "work_unit_fingerprint": "sha256:scholar-tables-file",
        "capability_families": ["scholarskills_tables"],
    }
    invocation = module.invoke_scientific_capability(
        capability_id="opl.scholarskills.tables",
        study_root=study_root,
        current_owner_delta=current_owner_delta,
        apply=True,
    )

    evidence = module.build_capability_owner_consumption_evidence(
        invocation_result=invocation,
        current_owner_delta=current_owner_delta,
        materialized_package_manifest_path=manifest_path,
    )

    assert evidence["execution_receipt_status"] == "complete"
    assert evidence["execution_receipt_refs"]["table_manifest_ref"] == str(
        artifact_manifest_path
    )
    assert evidence["observed_execution_receipt_ref_families"] == [
        "input_fingerprint_ref",
        "dependency_profile_ref",
        "prepared_run_context_ref",
        "table_manifest_ref",
        "table_qc_ref",
    ]
    package_consumption = evidence["materialized_package_consumption"]
    assert package_consumption["refs_only"] is True
    assert package_consumption["manifest_path"] == str(manifest_path.resolve())
    assert package_consumption["execution_receipt_path"] == str(receipt_path.resolve())
    assert package_consumption["authority_flags_false"] is True
    assert package_consumption["candidate_artifact_count"] == 4
    candidate_artifacts = package_consumption["candidate_artifacts"]
    ref_artifact = next(
        artifact
        for artifact in candidate_artifacts
        if artifact["kind"] == "table_manifest"
        and artifact["ref"] == "opl-vault:tables/table_manifest.json"
    )
    assert ref_artifact == {
        "kind": "table_manifest",
        "ref": "opl-vault:tables/table_manifest.json",
        "sha256": "sha256:table-manifest",
        "authority": False,
        "authority_flags": {},
        "authority_flags_false": True,
        "readiness_notes": ["candidate table package ready for MAS owner review"],
        "missing_inputs": [],
        "body_included": False,
        "body_carried_to_owner_request": False,
        "written_files": [],
        "forbidden_written_file_collisions": [],
        "counts_as_paper_truth": False,
        "counts_as_owner_receipt": False,
        "can_authorize_publication_readiness": False,
    }
    body_artifact = next(
        artifact for artifact in candidate_artifacts if artifact["kind"] == "table_summary"
    )
    assert body_artifact["kind"] == "table_summary"
    assert body_artifact["ref"] is None
    assert body_artifact["sha256"].startswith("sha256:")
    assert body_artifact["authority"] is False
    assert body_artifact["body_included"] is True
    assert body_artifact["body_carried_to_owner_request"] is False
    assert body_artifact["readiness_notes"] == [
        "body carried only as candidate artifact evidence"
    ]
    assert body_artifact["missing_inputs"] == ["owner_acceptance_ref"]
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
    owner_gate_request = evidence["owner_gate_request"]
    assert owner_gate_request["surface_kind"] == "mas_scholarskills_owner_gate_request"
    assert owner_gate_request["request_status"] == "ready_for_owner_gate_review"
    assert owner_gate_request["non_authoritative_request"] is True
    assert owner_gate_request["capability_id"] == "opl.scholarskills.tables"
    assert owner_gate_request["module_id"] == "opl.scholarskills.tables"
    assert owner_gate_request["execution_receipt_status"] == "complete"
    assert owner_gate_request["materialized_package_manifest_path"] == str(
        manifest_path.resolve()
    )
    assert owner_gate_request["materialized_package_sha256"] == "sha256:receipt"
    assert owner_gate_request["candidate_artifact_count"] == 4
    assert owner_gate_request["candidate_artifact_missing_inputs"] == [
        "owner_acceptance_ref"
    ]
    owner_ref_artifact = next(
        artifact
        for artifact in owner_gate_request["candidate_artifacts"]
        if artifact["kind"] == "table_manifest"
        and artifact["ref"] == "opl-vault:tables/table_manifest.json"
    )
    assert owner_ref_artifact == {
        "kind": "table_manifest",
        "ref": "opl-vault:tables/table_manifest.json",
        "sha256": "sha256:table-manifest",
        "authority": False,
        "authority_flags_false": True,
        "readiness_notes": ["candidate table package ready for MAS owner review"],
        "missing_inputs": [],
        "body_included": False,
        "body_carried_to_owner_request": False,
        "counts_as_paper_truth": False,
        "counts_as_owner_receipt": False,
        "can_authorize_publication_readiness": False,
    }
    owner_body_artifact = next(
        artifact
        for artifact in owner_gate_request["candidate_artifacts"]
        if artifact["kind"] == "table_summary"
    )
    assert owner_body_artifact["kind"] == "table_summary"
    assert owner_body_artifact["sha256"] == body_artifact["sha256"]
    assert owner_body_artifact["body_included"] is True
    assert owner_body_artifact["body_carried_to_owner_request"] is False
    assert owner_body_artifact["missing_inputs"] == ["owner_acceptance_ref"]
    assert owner_gate_request["required_owner_response_shapes"] == [
        "owner_receipt_ref",
        "typed_blocker_ref",
        "route_back_evidence_ref",
        "reviewer_receipt_ref",
    ]
    assert owner_gate_request["counts_as_progress"] is False
    assert owner_gate_request["counts_as_paper_truth"] is False
    assert owner_gate_request["counts_as_owner_receipt"] is False
    assert owner_gate_request["can_authorize_publication_readiness"] is False
    assert owner_gate_request["can_write_owner_receipt"] is False
    owner_gate_handoff = evidence["owner_gate_handoff"]
    assert owner_gate_handoff["surface_kind"] == "mas_scholarskills_owner_gate_handoff"
    assert owner_gate_handoff["handoff_status"] == "ready_for_owner_gate_review"
    assert owner_gate_handoff["next_owner"] == "MAS owner gate"
    assert owner_gate_handoff["source_request_ref"] == "inline:owner_gate_request"
    assert owner_gate_handoff["candidate_artifact_missing_inputs"] == [
        "owner_acceptance_ref"
    ]
    assert owner_gate_handoff["candidate_artifacts"] == owner_gate_request[
        "candidate_artifacts"
    ]
    assert owner_gate_handoff["mas_consumer_written_files"] == []
    assert evidence["required_owner_response_shapes"] == [
        {
            "shape": "owner_receipt_ref",
            "required_for": "accept_candidate_into_mas_paper_truth",
            "may_be_written_by_this_request": False,
        },
        {
            "shape": "typed_blocker_ref",
            "required_for": "block_candidate_with_stable_owner_reason",
            "may_be_written_by_this_request": False,
        },
        {
            "shape": "route_back_evidence_ref",
            "required_for": "return_candidate_to_capability_or_executor",
            "may_be_written_by_this_request": False,
        },
        {
            "shape": "reviewer_receipt_ref",
            "required_for": "attach_non_authoritative_reviewer_readback",
            "may_be_written_by_this_request": False,
        },
    ]
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "package").exists()
