from __future__ import annotations

import json


def _fresh_guarded_apply_delta(**overrides: object) -> dict[str, object]:
    return {
        "surface_kind": "opl_current_owner_delta",
        "schema_version": "current-owner-delta.v1",
        "delta_id": "current-owner-delta:medautoscience:paper-autonomy-guarded-apply:owner-answer-or-typed-blocker",
        "domain": "medautoscience",
        "domain_id": "medautoscience",
        "task_or_study_ref": "medautoscience:frt_dfb2a46c1e1286b88bd02ce6",
        "stage_ref": "paper_autonomy/guarded-apply",
        "stage_id": "paper_autonomy/guarded-apply",
        "lineage_ref": "sat_19c64e81217e5b7f8531abc6",
        "source_fingerprint": (
            "owner_delta_first:med-autoscience:medautoscience:paper-autonomy-guarded-apply:"
            "medautoscience-frt-dfb2a46c1e1286b88bd02ce6:sat-19c64e81217e5b7f8531abc6:"
            "domain-owner-receipt-quality-gate-or-typed-blocker-required:"
            "domain-owner-receipt-ref-or-quality-gate-receipt-ref-or-typed-blocker-ref-or-hum"
        ),
        "desired_delta_kind": "owner_answer_or_typed_blocker",
        "desired_delta_description": "domain_owner_receipt_quality_gate_or_typed_blocker_required",
        "payload_requirement": "domain_owner_receipt_quality_gate_or_typed_blocker_required",
        "current_owner": "med-autoscience",
        "owner": "med-autoscience",
        "accepted_answer_shape": [
            "domain_owner_receipt_ref",
            "quality_gate_receipt_ref",
            "typed_blocker_ref",
            "human_gate_ref",
            "route_back_evidence_ref",
        ],
        "required_return_shapes": [
            "domain_owner_receipt_ref",
            "quality_gate_receipt_ref",
            "typed_blocker_ref",
            "human_gate_ref",
            "route_back_evidence_ref",
        ],
        "hard_gate": {
            "state": "owner_delta_open",
            "human_or_domain_owner_required": True,
            "owner_answer_ref": None,
            "owner_answer_kind": None,
            "domain_ready_authorized": False,
            "quality_or_export_authorized": False,
        },
        "latest_owner_answer_ref": None,
        "latest_owner_answer_kind": None,
        **overrides,
    }


def test_materializes_current_owner_delta_bound_typed_blocker_and_opl_payloads() -> None:
    from med_autoscience.controllers.current_owner_delta_owner_answer import (
        materialize_current_owner_delta_owner_answer,
    )

    result = materialize_current_owner_delta_owner_answer(_fresh_guarded_apply_delta())

    assert result["status"] == "materialized"
    assert result["write_permitted"] is False
    typed_blocker = result["typed_blocker"]
    assert typed_blocker["typed_blocker_ref"] == (
        "mas-stage-typed-blocker:medautoscience:"
        "current-owner-delta:medautoscience:paper-autonomy-guarded-apply:owner-answer-or-typed-blocker:"
        "frt_dfb2a46c1e1286b88bd02ce6:sat_19c64e81217e5b7f8531abc6:"
        "paper_autonomy-guarded-apply:owner-answer-required"
    )
    assert typed_blocker["current_owner_delta_id"] == (
        "current-owner-delta:medautoscience:paper-autonomy-guarded-apply:owner-answer-or-typed-blocker"
    )
    assert typed_blocker["source_fingerprint"] == result["target_identity"]["source_fingerprint"]
    assert typed_blocker["domain_ready"] is False
    assert typed_blocker["production_ready"] is False
    assert typed_blocker["authority_boundary"]["mas_created_typed_blocker"] is True
    assert typed_blocker["authority_boundary"]["can_claim_domain_ready"] is False

    target = result["target_identity"]
    assert target == result["domain_owner_payload_summary_record"]["target_identity"]
    assert target["target_key"] == (
        "medautoscience/current_owner_delta_bridge/owner_payload_item/"
        "current-owner-delta:medautoscience:paper-autonomy-guarded-apply:owner-answer-or-typed-blocker/"
        "medautoscience:frt_dfb2a46c1e1286b88bd02ce6/"
        "sat_19c64e81217e5b7f8531abc6/"
        + result["target_identity"]["source_fingerprint"]
    )
    assert result["domain_owner_payload_summary_record"]["payload"] == {
        "source_ref": typed_blocker["source_ref"],
        "typed_blocker_refs": [typed_blocker["typed_blocker_ref"]],
        "receipt_ref": (
            "opl://domain-owner-payload-summary/"
            "medautoscience%2Fcurrent_owner_delta_bridge%2Fowner_payload_item%2F"
            "current-owner-delta%3Amedautoscience%3Apaper-autonomy-guarded-apply%3Aowner-answer-or-typed-blocker%2F"
            "medautoscience%3Afrt_dfb2a46c1e1286b88bd02ce6%2F"
            "sat_19c64e81217e5b7f8531abc6%2F"
            + result["target_identity"]["source_fingerprint"].replace(":", "%3A").replace("/", "%2F")
        ),
    }

    stage_record = result["stage_run_authorization_record"]["payload"]
    assert stage_record["phase"] == "closeout"
    assert stage_record["decision"] == "typed_blocker"
    assert stage_record["owner_answer_kind"] == "typed_blocker"
    assert stage_record["owner_answer_ref"] == typed_blocker["typed_blocker_ref"]
    assert stage_record["stage_run_id"] == "app-stage-run:medautoscience:paper-autonomy-guarded-apply"
    assert stage_record["study_id"] == "frt_dfb2a46c1e1286b88bd02ce6"
    assert stage_record["domain_context"] == {
        "domain_id": "medautoscience",
        "study_id": "frt_dfb2a46c1e1286b88bd02ce6",
        "stage_id": "paper_autonomy/guarded-apply",
    }
    assert stage_record["stage_attempt_id"] == "sat_19c64e81217e5b7f8531abc6"
    assert stage_record["owner_answer_stage_run_id"] == stage_record["stage_run_id"]
    assert stage_record["owner_answer_generation"] == stage_record["generation"]
    assert stage_record["owner_answer_manifest_ref"] == stage_record["stage_manifest_ref"]
    assert stage_record["owner_answer_current_pointer_ref"] == stage_record["current_pointer_ref"]
    assert stage_record["owner_answer_source_fingerprint"] == stage_record["source_fingerprint"]
    assert stage_record["owner_answer_idempotency_key"] == stage_record["idempotency_key"]
    assert stage_record["authority_boundary"]["can_create_typed_blocker"] is False
    assert stage_record["authority_boundary"]["can_claim_production_ready"] is False


def test_materializer_fails_closed_for_stale_or_invalid_delta_identity() -> None:
    from med_autoscience.controllers.current_owner_delta_owner_answer import (
        materialize_current_owner_delta_owner_answer,
    )

    invalid = _fresh_guarded_apply_delta(lineage_ref=None, latest_owner_answer_ref="already-recorded")
    invalid.pop("lineage_ref", None)

    result = materialize_current_owner_delta_owner_answer(invalid)

    assert result["status"] == "blocked"
    assert result["write_permitted"] is False
    assert result["typed_blocker"]["blocker_id"] == "current_owner_delta_identity_missing_or_invalid"
    assert set(result["typed_blocker"]["missing_required_fields"]) == {
        "lineage_ref",
        "latest_owner_answer_ref_must_be_null",
    }
    assert "domain_owner_payload_summary_record" not in result
    assert "stage_run_authorization_record" not in result
    assert result["authority_boundary"]["can_claim_domain_ready"] is False
    assert result["authority_boundary"]["can_create_owner_receipt"] is False


def test_current_owner_delta_owner_answer_cli_outputs_record_payloads(tmp_path, capsys) -> None:
    from med_autoscience import cli

    delta_file = tmp_path / "current-owner-delta.json"
    delta_file.write_text(json.dumps(_fresh_guarded_apply_delta()), encoding="utf-8")

    exit_code = cli.main(
        [
            "current-owner-delta-owner-answer",
            "--current-owner-delta-file",
            str(delta_file),
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["status"] == "materialized"
    assert payload["typed_blocker"]["latest_owner_answer_kind"] == "typed_blocker"
    assert payload["domain_owner_payload_summary_record"]["command"] == (
        "opl runtime domain-owner-payload-summary record --target-identity <json> --payload <json>"
    )
    assert payload["stage_run_authorization_record"]["command"] == (
        "opl runtime stage-run-authorization record --payload <json>"
    )
