from __future__ import annotations

from med_autoscience.controllers.guarded_apply_owner_delta_contract import (
    GUARDED_APPLY_ACCEPTED_ANSWER_SHAPES,
    guarded_apply_current_owner_delta_contract,
    guarded_apply_current_owner_delta_validation,
    guarded_apply_identity_typed_blocker,
)


def _live_delta(**overrides: object) -> dict[str, object]:
    payload = guarded_apply_current_owner_delta_contract()
    payload.update(
        {
            "surface_kind": "opl_current_owner_delta",
            "lineage_ref": "sat_d1bbac5b1671e6afc08d743d",
            "owner": "med-autoscience",
            "current_owner": "med-autoscience",
        }
    )
    payload.update(overrides)
    return payload


def test_guarded_apply_current_owner_delta_validation_accepts_live_five_shape_identity() -> None:
    validation = guarded_apply_current_owner_delta_validation(_live_delta())

    assert validation["valid"] is True
    assert validation["missing_required_fields"] == []
    assert validation["required_accepted_answer_shape"] == list(GUARDED_APPLY_ACCEPTED_ANSWER_SHAPES)
    assert guarded_apply_identity_typed_blocker(_live_delta()) is None


def test_guarded_apply_current_owner_delta_validation_rejects_missing_lineage_ref() -> None:
    payload = _live_delta(lineage_ref=None)

    validation = guarded_apply_current_owner_delta_validation(payload)

    assert validation["valid"] is False
    assert "lineage_ref" in validation["missing_required_fields"]
    blocker = guarded_apply_identity_typed_blocker(payload)
    assert blocker is not None
    assert blocker["blocker_id"] == "current_owner_delta_identity_missing_or_invalid"
    assert blocker["write_permitted"] is False


def test_guarded_apply_current_owner_delta_validation_rejects_three_shape_contract() -> None:
    validation = guarded_apply_current_owner_delta_validation(
        _live_delta(
            accepted_answer_shape=[
                "domain_owner_receipt_ref",
                "quality_gate_receipt_ref",
                "typed_blocker_ref",
            ],
            accepted_return_shapes=[
                "domain_owner_receipt_ref",
                "quality_gate_receipt_ref",
                "typed_blocker_ref",
            ],
        )
    )

    assert validation["valid"] is False
    assert validation["missing_required_fields"] == [
        "accepted_answer_shape.human_gate_ref",
        "accepted_answer_shape.route_back_evidence_ref",
    ]


def test_guarded_apply_current_owner_delta_validation_rejects_wrong_identity_or_answer_state() -> None:
    wrong = guarded_apply_current_owner_delta_validation(_live_delta(stage_id="domain_owner/default-executor-dispatch"))
    answered = guarded_apply_current_owner_delta_validation(_live_delta(latest_owner_answer_ref="receipt://done"))
    domain_ready = guarded_apply_current_owner_delta_validation(_live_delta(domain_ready_authorized=True))

    assert "stage_id" in wrong["missing_required_fields"]
    assert "latest_owner_answer_ref_must_be_null" in answered["missing_required_fields"]
    assert "domain_ready_authorized_false" in domain_ready["missing_required_fields"]
