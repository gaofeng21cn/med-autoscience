import pytest
from med_autoscience.controllers import canonical_artifact_contract as artifact

pytestmark = pytest.mark.meta
TARGETS = "manuscript figures tables submission_package".split()
FLAGS = (
    "current_package_can_be_edit_source submission_minimal_can_be_edit_source artifacts_final_can_be_edit_source "
    "current_package_can_be_quality_authority submission_minimal_can_be_quality_authority "
    "artifacts_final_can_be_quality_authority derived_package_can_authorize_submission"
).split()
PROOF_FLAGS = (
    "derived_artifact_can_authorize_submission derived_artifact_can_be_quality_authority "
    "derived_artifact_can_be_edit_source"
).split()


def _codes(result):
    return {issue["code"] for issue in result["issues"]}


def test_canonical_artifact_contract_builders_and_validators_fail_closed():
    contract = artifact.build_canonical_artifact_contract()
    rebuild = artifact.build_artifact_rebuild_integrity_contract()
    projection = contract["lineage_graph_projection"]
    assert {key: contract[key] for key in FLAGS} == dict.fromkeys(FLAGS, False)
    assert contract["lineage_chain"] == (
        "canonical_source analysis_result evidence_ledger claim_map manuscript_table_figure submission_package".split()
    )
    assert tuple(projection[key] for key in ("path", "edit_source", "quality_authority", "dispatch_authority")) == (
        "reproducibility/artifact_lineage_graph.json", False, False, False
    )
    requirements = {item["target"]: item["must_rebuild_from"] for item in contract["rebuild_requirements"]}
    assert requirements == {target: ["canonical_sources", "ai_reviewer_quality_decision"] for target in TARGETS}
    proofs = {proof["target"]: proof for proof in rebuild["rebuild_proofs"]}
    proof_false = dict.fromkeys(PROOF_FLAGS, False)
    assert set(proofs) == set(TARGETS) and {key: rebuild[key] for key in PROOF_FLAGS} == proof_false
    assert all({key: proof[key] for key in PROOF_FLAGS} == proof_false for proof in proofs.values())
    assert all(
        proof["source_refs"] and proof["fingerprint_refs"]
        and (proof["quality_decision_ref"], proof["controller_decision_ref"])
        == ("artifacts/publication_eval/latest.json", "controller_decisions/latest.json")
        for proof in proofs.values()
    )
    assert artifact.validate_canonical_artifact_contract(contract)["ok"]
    assert artifact.validate_artifact_rebuild_integrity_contract(rebuild)["ok"]
    contract.update(current_package_can_be_edit_source=True, current_package_can_be_quality_authority=True,
                    submission_minimal_can_be_quality_authority=True, artifacts_final_can_be_quality_authority=True)
    contract["lineage_graph_projection"]["dispatch_authority"] = True
    rebuild["derived_artifact_can_authorize_submission"] = True
    rebuild["rebuild_proofs"][0]["source_refs"] = []
    assert _codes(artifact.validate_canonical_artifact_contract(contract)) == set(
        "current_package_used_as_edit_source current_package_used_as_quality_authority "
        "submission_minimal_used_as_quality_authority artifacts_final_used_as_quality_authority "
        "lineage_graph_projection_used_as_dispatch_authority".split()
    )
    assert _codes(artifact.validate_artifact_rebuild_integrity_contract(rebuild)) == {
        "derived_artifact_authorizes_submission", "rebuild_proof_missing_source_refs"
    }
