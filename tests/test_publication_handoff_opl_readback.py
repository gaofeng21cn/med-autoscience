from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.controllers.stage_outcome_authority.action_execution import publication_handoff
from tests.stage_outcome_authority_helpers import dispatch


def test_publication_handoff_requires_explicit_opl_stage_run_readback_refs() -> None:
    payload = dispatch(
        study_id="test-study",
        action_type="publication_handoff_owner_gate",
        owner="publication_gate_owner",
        required_output_surface="publication_handoff_owner_gate_result",
    )

    incomplete = publication_handoff._trusted_closeout_binding(
        dispatch=payload,
    )
    assert incomplete is not None
    assert incomplete["stage_run_ref"] is None
    assert incomplete["current_pointer_ref"] is None
    assert incomplete["closeout_refs"] == []
    decision = publication_handoff._handoff_decision(
        study_root=Path("/tmp/test-study"),
        readiness={},
        closeout_binding=incomplete,
    )
    assert decision["reason"] == "opl_stage_run_readback_refs_incomplete"

    payload["closeout_binding"] = {
        "stage_run_id": "stage-run::test-study::publication-handoff",
        "stage_run_ref": "opl://stage-runs/test-study/publication-handoff",
        "stage_manifest_ref": "opl://stage-runs/test-study/publication-handoff/manifest",
        "current_pointer_ref": "opl://stage-runs/test-study/publication-handoff/current",
        "closeout_refs": ["opl://stage-attempts/test-study/publication-handoff/closeouts/current"],
        "source_fingerprint": "sha256:test-study-publication-handoff",
    }
    binding = publication_handoff._trusted_closeout_binding(
        dispatch=payload,
    )

    assert binding is not None
    assert binding["stage_run_ref"] == payload["closeout_binding"]["stage_run_ref"]
    assert binding["current_pointer_ref"] == payload["closeout_binding"]["current_pointer_ref"]
    assert binding["closeout_refs"] == payload["closeout_binding"]["closeout_refs"]
    assert binding["body_included"] is False


def test_publication_owner_answers_do_not_mutate_opl_stage_files(tmp_path: Path) -> None:
    study_root = tmp_path / "study"
    stage_root = study_root / "artifacts/stage_outputs/08-publication_package_handoff"
    manifest_path = stage_root / "stage_manifest.json"
    current_path = stage_root / "current.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text('{"owner":"one-person-lab","sentinel":"manifest"}\n', encoding="utf-8")
    current_path.write_text('{"owner":"one-person-lab","sentinel":"current"}\n', encoding="utf-8")
    manifest_before = manifest_path.read_bytes()
    current_before = current_path.read_bytes()
    binding = {
        "surface_kind": "publication_handoff_closeout_binding",
        "trusted_opl_execution_authorization": True,
        "provider_attempt_ref": "opl://stage-attempts/publication-handoff",
        "attempt_lease_ref": "opl://stage-attempts/publication-handoff/leases/current",
        "execution_authorization_decision_ref": "opl://stage-attempts/publication-handoff/authorization",
        "stage_run_id": "stage-run::publication-handoff",
        "stage_run_ref": "opl://stage-runs/publication-handoff",
        "stage_manifest_ref": "opl://stage-runs/publication-handoff/manifest",
        "current_pointer_ref": "opl://stage-runs/publication-handoff/current",
        "closeout_refs": ["opl://stage-attempts/publication-handoff/closeouts/current"],
        "source_fingerprint": "sha256:publication-handoff",
        "work_unit_fingerprint": "sha256:publication-handoff-work-unit",
        "idempotency_key": "publication-handoff",
        "body_included": False,
    }
    readiness = {"overall_status": "ready", "study_root": str(study_root)}
    decision = {
        "status": "ready_for_human_submission_handoff",
        "reason": "terminal_stage_and_medical_paper_readiness_ready",
        "next_owner": "human_gate",
        "next_action": "human_submission_decision",
    }

    owner_result = publication_handoff._write_handoff_receipt(
        study_id="test-study",
        study_root=study_root,
        decision=decision,
        readiness=readiness,
        closeout_binding=binding,
    )
    owner_receipt = json.loads(Path(owner_result["owner_receipt_ref"]).read_text(encoding="utf-8"))
    blocker_result = publication_handoff._write_typed_blocker(
        study_id="test-study",
        study_root=study_root,
        decision={**decision, "status": "typed_blocker_or_stop_loss", "reason": "not_ready"},
        readiness=readiness,
        closeout_binding=binding,
    )

    assert Path(blocker_result["typed_blocker_ref"]).is_file()
    assert not Path(owner_result["owner_receipt_ref"]).exists()
    assert owner_receipt["stage_run_ref"] == binding["stage_run_ref"]
    assert owner_receipt["stage_manifest_ref"] == binding["stage_manifest_ref"]
    assert owner_receipt["current_pointer_ref"] == binding["current_pointer_ref"]
    assert owner_receipt["closeout_refs"] == binding["closeout_refs"]
    assert manifest_path.read_bytes() == manifest_before
    assert current_path.read_bytes() == current_before
