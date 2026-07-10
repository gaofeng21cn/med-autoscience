from __future__ import annotations

from tests.scientific_capability_registry_cases.common import (
    SCHOLARSKILLS_MODULE_IDS,
    SCHOLARSKILLS_RECEIPT_REF_KEYS_BY_MODULE,
    Path,
    importlib,
)


def test_scientific_capability_registry_indexes_resolves_and_invokes_all_scholarskills_modules(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    capabilities = {
        item["capability_id"]: item
        for item in module.build_scientific_capability_registry()["capabilities"]
    }

    assert set(SCHOLARSKILLS_MODULE_IDS) <= set(capabilities)
    for module_id in SCHOLARSKILLS_MODULE_IDS:
        module_name = module_id.removeprefix("mas-scholar-skills.")
        study_root = tmp_path / module_id
        capability = capabilities[module_id]
        delta = {
            "action_type": f"prepare_{module_name}_candidate",
            "action_id": f"{module_name}-001",
            "work_unit_id": f"{module_name}-candidate",
            "work_unit_fingerprint": f"sha256:{module_name}",
            "capability_families": [f"scholarskills_{module_name}"],
        }

        assert capability["module_id"] == module_id
        assert capability["descriptor_only"] is True
        assert capability["refs_only"] is True
        assert capability["external_runner_invocation_allowed"] is False
        assert capability["execution_receipt_expectation"]["required_ref_families"] == (
            SCHOLARSKILLS_RECEIPT_REF_KEYS_BY_MODULE[module_id]
        )
        assert capability["owner_consumption_boundary"]["candidate_output_only"] is True
        assert capability["owner_consumption_boundary"]["counts_as_paper_truth"] is False
        assert capability["module_classification"]["authority_owner"] is False

        resolution = module.resolve_scientific_capabilities(current_owner_delta=delta)
        selected = {
            item["capability_id"]: item
            for item in resolution["selected_capabilities"]
        }
        assert selected[module_id]["trigger_reason"] == (
            "current_delta_requested_capability_family"
        )

        invocation = module.invoke_scientific_capability(
            capability_id=module_id,
            study_root=study_root,
            current_owner_delta=delta,
            apply=True,
        )
        assert invocation["status"] == "descriptor_only"
        assert invocation["request_only"] is False
        assert invocation["external_runner_invocation_allowed"] is False
        assert invocation["result"]["readback"]["module_id"] == module_id
        assert not (study_root / "artifacts/publication_eval/latest.json").exists()
        assert not (study_root / "paper").exists()


def test_scientific_capability_registry_consumes_opl_shaped_receipts_for_every_scholarskills_module(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")

    for module_id, required_refs in SCHOLARSKILLS_RECEIPT_REF_KEYS_BY_MODULE.items():
        module_name = module_id.removeprefix("mas-scholar-skills.")
        delta = {
            "action_type": f"prepare_{module_name}_candidate",
            "action_id": f"{module_name}-001",
            "work_unit_id": f"{module_name}-candidate",
            "work_unit_fingerprint": f"sha256:{module_name}",
            "capability_families": [f"scholarskills_{module_name}"],
        }
        invocation = module.invoke_scientific_capability(
            capability_id=module_id,
            study_root=tmp_path / module_id,
            current_owner_delta=delta,
            apply=True,
        )
        receipt = {
            "surface_kind": "opl_scholarskills_execution_receipt_candidate",
            "status": "receipt_candidate_unsigned",
            "module_id": module_id,
            "execution_receipt_ref": f"opl-vault:receipts/{module_id}/receipt.json",
            "execution_receipt_refs": {
                key: f"opl-vault:{module_id}/{key}.json" for key in required_refs
            },
            "counts_as_paper_truth": False,
            "counts_as_owner_receipt": False,
            "can_authorize_publication_readiness": False,
        }

        evidence = module.build_capability_owner_consumption_evidence(
            invocation_result=invocation,
            current_owner_delta=delta,
            execution_receipt=receipt,
        )

        assert evidence["execution_receipt_status"] == "complete"
        assert evidence["observed_execution_receipt_ref_families"] == required_refs
        assert evidence["missing_execution_receipt_ref_families"] == []
        assert evidence["counts_as_progress"] is False
        assert evidence["counts_as_paper_truth"] is False
        assert evidence["counts_as_owner_receipt"] is False
        assert evidence["can_authorize_publication_readiness"] is False
