from __future__ import annotations


TERMINAL_HANDOFF_STAGE_ID = "08-publication_package_handoff"


def assert_opl_closeout_binding(
    binding: dict[str, object],
    *,
    study_id: str,
    receipt_ref: str | None = None,
) -> None:
    assert binding["stage_run_id"] == f"stage-run::{study_id}::{TERMINAL_HANDOFF_STAGE_ID}"
    assert binding["stage_manifest_ref"] == (
        f"artifacts/stage_outputs/{TERMINAL_HANDOFF_STAGE_ID}/stage_manifest.json"
    )
    assert binding["current_pointer_ref"] == f"artifacts/stage_outputs/{TERMINAL_HANDOFF_STAGE_ID}/current.json"
    assert binding["source_fingerprint"] == f"truth-source::{study_id}::publication-handoff-binding"
    assert binding["idempotency_key"] == (
        f"owner-route::{study_id}::publication_handoff_owner_gate::publication_gate_owner"
    )
    assert binding["provider_attempt_ref"] == f"opl://stage-attempts/{study_id}/publication-handoff"
    assert binding["attempt_lease_ref"] == f"opl://stage-attempts/{study_id}/publication-handoff/leases/current"
    assert binding["attempt_lease_status"] == "active"
    assert binding["execution_authorization_decision_ref"] == (
        f"opl://stage-attempts/{study_id}/publication-handoff/execution-authorizations/current"
    )
    assert binding["closeout_refs"] == [
        "artifacts/supervision/consumer/stage_attempt_closeouts/sat-publication-handoff.json"
    ]
    if receipt_ref is not None:
        assert binding["receipt_ref"] == receipt_ref


def attach_publication_handoff_closeout_binding(dispatch: dict[str, object], *, study_id: str) -> None:
    source_fingerprint = f"truth-source::{study_id}::publication-handoff-binding"
    closeout_ref = (
        "artifacts/supervision/consumer/stage_attempt_closeouts/"
        "sat-publication-handoff.json"
    )
    binding = {
        "surface_kind": "publication_handoff_closeout_binding",
        "stage_run_id": f"stage-run::{study_id}::{TERMINAL_HANDOFF_STAGE_ID}",
        "stage_run_ref": f"stage-run::{study_id}::{TERMINAL_HANDOFF_STAGE_ID}",
        "stage_manifest_ref": (
            f"artifacts/stage_outputs/{TERMINAL_HANDOFF_STAGE_ID}/stage_manifest.json"
        ),
        "current_pointer_ref": f"artifacts/stage_outputs/{TERMINAL_HANDOFF_STAGE_ID}/current.json",
        "closeout_refs": [closeout_ref],
        "source_fingerprint": source_fingerprint,
        "work_unit_fingerprint": source_fingerprint,
        "body_included": False,
    }
    dispatch["closeout_binding"] = binding
    dispatch["closeout_refs"] = [closeout_ref]
    dispatch["source_fingerprint"] = source_fingerprint
    dispatch["work_unit_fingerprint"] = source_fingerprint
    dispatch["opl_execution_authorization"] = {
        "owner": "one-person-lab",
        "executor_kind": "codex_cli",
        "provider_attempt_ref": f"opl://stage-attempts/{study_id}/publication-handoff",
        "stage_attempt_id": f"stage-attempt::{study_id}::publication-handoff",
        "attempt_lease_ref": f"opl://stage-attempts/{study_id}/publication-handoff/leases/current",
        "attempt_lease_status": "active",
        "execution_authorization_decision_ref": (
            f"opl://stage-attempts/{study_id}/publication-handoff/execution-authorizations/current"
        ),
    }
    prompt_contract = dispatch["prompt_contract"]
    assert isinstance(prompt_contract, dict)
    prompt_contract["closeout_binding"] = binding
    prompt_contract["closeout_refs"] = [closeout_ref]
    prompt_contract["source_fingerprint"] = source_fingerprint
    prompt_contract["work_unit_fingerprint"] = source_fingerprint
    prompt_contract["opl_execution_authorization"] = dispatch["opl_execution_authorization"]


def remove_opl_execution_authorization(dispatch: dict[str, object]) -> None:
    dispatch.pop("opl_execution_authorization", None)
    prompt_contract = dispatch.get("prompt_contract")
    if isinstance(prompt_contract, dict):
        prompt_contract.pop("opl_execution_authorization", None)
