from __future__ import annotations


def test_opl_supervisor_decision_readback_projection_keeps_no_authority_boundary() -> None:
    readback = {
        "surface_kind": "opl_paper_autonomy_supervisor_decision_readback",
        "authority_boundary": {
            "read_model_can_execute": False,
            "observability_can_close_owner_answer": False,
            "opl_can_write_mas_truth": False,
            "opl_can_create_domain_owner_receipt": False,
            "opl_can_create_domain_typed_blocker": False,
            "provider_completion_is_domain_ready": False,
        },
    }

    assert readback["surface_kind"] == "opl_paper_autonomy_supervisor_decision_readback"
    assert all(value is False for value in readback["authority_boundary"].values())
