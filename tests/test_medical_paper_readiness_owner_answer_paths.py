from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.controllers.stage_outcome_authority.action_execution import (
    medical_paper_readiness_stage_closeout,
)


def test_readiness_owner_answers_do_not_mutate_opl_stage_files(tmp_path: Path) -> None:
    study_root = tmp_path / "study"
    stage_root = study_root / "artifacts/stage_outputs/08-publication_package_handoff"
    manifest_path = stage_root / "stage_manifest.json"
    current_path = stage_root / "current.json"
    stage_root.mkdir(parents=True)
    manifest_path.write_text('{"owner":"one-person-lab","sentinel":"manifest"}\n', encoding="utf-8")
    current_path.write_text('{"owner":"one-person-lab","sentinel":"current"}\n', encoding="utf-8")
    manifest_before = manifest_path.read_bytes()
    current_before = current_path.read_bytes()
    binding = {
        "trusted_opl_execution_authorization": True,
        "provider_attempt_ref": "opl://stage-attempts/readiness",
        "attempt_lease_ref": "opl://stage-attempts/readiness/leases/current",
        "execution_authorization_decision_ref": "opl://stage-attempts/readiness/authorization",
        "stage_run_id": "stage-run::readiness",
        "stage_run_ref": "opl://stage-runs/readiness",
        "stage_manifest_ref": "opl://stage-runs/readiness/manifest",
        "current_pointer_ref": "opl://stage-runs/readiness/current",
        "closeout_refs": ["opl://stage-attempts/readiness/closeouts/current"],
        "source_fingerprint": "sha256:readiness",
        "work_unit_fingerprint": "sha256:readiness-work-unit",
        "idempotency_key": "readiness",
    }
    owner_result = {"readiness_ref": "artifacts/medical_paper/readiness.json"}

    owner_closeout = medical_paper_readiness_stage_closeout.materialize_stage_native_owner_answer(
        study_id="test-study",
        study_root=study_root,
        owner_result=owner_result,
        owner_delta_result={
            "result_kind": "owner_receipt",
            "quality_gate_receipt_refs": ["quality-gate:test-study"],
        },
        closeout_binding=binding,
        apply=True,
    )
    owner_receipt = json.loads((study_root / owner_closeout["written_ref"]).read_text(encoding="utf-8"))
    blocker_closeout = medical_paper_readiness_stage_closeout.materialize_stage_native_owner_answer(
        study_id="test-study",
        study_root=study_root,
        owner_result={**owner_result, "blocked_reason": "readiness_not_ready"},
        owner_delta_result={
            "result_kind": "stable_typed_blocker",
            "stable_typed_blocker_refs": ["typed-blocker:test-study"],
            "typed_blocker": {"blocker_id": "readiness_not_ready"},
        },
        closeout_binding=binding,
        apply=True,
    )

    assert owner_closeout["written_ref"] == "artifacts/medical_paper/readiness_owner_receipt.json"
    assert blocker_closeout["written_ref"] == "artifacts/medical_paper/readiness_typed_blocker.json"
    assert not (study_root / owner_closeout["written_ref"]).exists()
    assert (study_root / blocker_closeout["written_ref"]).is_file()
    assert owner_receipt["stage_run_ref"] == binding["stage_run_ref"]
    assert owner_receipt["stage_manifest_ref"] == binding["stage_manifest_ref"]
    assert owner_receipt["current_pointer_ref"] == binding["current_pointer_ref"]
    assert owner_receipt["closeout_refs"] == binding["closeout_refs"]
    assert manifest_path.read_bytes() == manifest_before
    assert current_path.read_bytes() == current_before
