from __future__ import annotations

import importlib


SURFACE_IDS = {
    "attempt_replay_lab_notebook_export",
    "cost_ledger_budget_cap",
    "mcp_connector_doctor_test",
    "remote_compute_execution_receipt",
    "human_gate_form_schema",
    "console_workbench_activity_selector_timeline",
    "openrouter_fusion_watch_only_briefing",
}
AUTHORITY_FALSE_FIELDS = {
    "writes_mas_truth",
    "writes_runtime",
    "can_write_publication_eval",
    "can_write_controller_decisions",
    "can_sign_owner_receipt",
    "can_create_typed_blocker",
    "can_create_human_gate",
    "can_claim_publication_ready",
    "can_claim_paper_progress",
}


def _projection(dispatch: dict[str, object] | None = None) -> dict[str, object]:
    module = importlib.import_module("med_autoscience.kdense_byok_runtime_surfaces")
    return module.build_kdense_byok_runtime_surfaces(dispatch)


def test_kdense_runtime_projection_emits_refs_only_non_authority_surfaces() -> None:
    projection = _projection({"action_id": "dispatch-kdense-runtime"})
    surfaces = {item["surface_id"]: item for item in projection["surfaces"]}

    assert projection["source_contract_ref"] == (
        "contracts/kdense_byok_external_intake.json"
    )
    assert set(projection["surface_ids"]) == SURFACE_IDS
    assert set(surfaces) == SURFACE_IDS
    assert all(projection[surface_id] == surfaces[surface_id] for surface_id in SURFACE_IDS)

    authority = projection["authority_boundary"]
    assert set(authority) == {
        "refs_only",
        "advisory_only",
        "nonblocking",
        "fail_open",
        "allowed_writes",
        *AUTHORITY_FALSE_FIELDS,
    }
    assert authority["refs_only"] is True
    assert authority["allowed_writes"] == []
    assert not any(authority[field] for field in AUTHORITY_FALSE_FIELDS)
    for surface in surfaces.values():
        assert surface["refs_only"] is True
        assert surface["allowed_writes"] == []
        assert surface["authority_boundary"] == authority
        assert surface["writes_mas_truth"] is False
        assert surface["writes_runtime"] is False
        assert surface["can_claim_publication_ready"] is False
        assert surface["can_claim_paper_progress"] is False

    fusion = surfaces["openrouter_fusion_watch_only_briefing"]
    assert fusion["watch_only"] is True
    assert fusion["classification"] == "watch_only"
    assert fusion["mainline_waits_for_surface"] is False


def test_kdense_runtime_projection_fail_open_without_dispatch() -> None:
    projection = _projection()

    assert projection["status"] == "projection_emitted"
    assert projection["fail_open"] is True
    assert projection["diagnostic"] == {"reason": "missing_or_invalid_dispatch"}
    assert projection["current_owner_action"]["action_id"] is None
