from __future__ import annotations

import importlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "contracts" / "kdense_byok_external_intake.json"

SURFACE_IDS = {
    "attempt_replay_lab_notebook_export",
    "cost_ledger_budget_cap",
    "mcp_connector_doctor_test",
    "remote_compute_execution_receipt",
    "human_gate_form_schema",
    "console_workbench_activity_selector_timeline",
    "openrouter_fusion_watch_only_briefing",
}


def _contract() -> dict[str, object]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _projection(dispatch: dict[str, object] | None = None) -> dict[str, object]:
    module = importlib.import_module("med_autoscience.kdense_byok_runtime_surfaces")
    return module.build_kdense_byok_runtime_surfaces(dispatch)


def test_kdense_runtime_projection_pins_intake_sources() -> None:
    contract = _contract()

    projection = _projection({"action_id": "dispatch-kdense-runtime"})

    assert projection["source_contract_ref"] == "contracts/kdense_byok_external_intake.json"
    assert projection["source_pins"] == {
        "kdense_byok": {
            "repo": contract["source_evidence"]["kdense_byok"]["repo"],
            "inspected_head_commit": contract["source_evidence"]["kdense_byok"][
                "inspected_head_commit"
            ],
            "latest_release_tag": contract["source_evidence"]["kdense_byok"][
                "latest_release_tag"
            ],
            "release_tag_commit": contract["source_evidence"]["kdense_byok"][
                "release_tag_commit"
            ],
            "license": contract["source_evidence"]["kdense_byok"]["license"],
        },
        "scientific_agent_skills": {
            "repo": contract["source_evidence"]["scientific_agent_skills"]["repo"],
            "inspected_head_commit": contract["source_evidence"]["scientific_agent_skills"][
                "inspected_head_commit"
            ],
            "license": contract["source_evidence"]["scientific_agent_skills"]["license"],
        },
    }


def test_kdense_runtime_projection_emits_all_seven_surfaces() -> None:
    projection = _projection({"action_id": "dispatch-kdense-runtime"})

    surfaces = {item["surface_id"]: item for item in projection["surfaces"]}

    assert set(projection["surface_ids"]) == SURFACE_IDS
    assert set(surfaces) == SURFACE_IDS
    for surface_id in SURFACE_IDS:
        assert surface_id in projection
        assert projection[surface_id] == surfaces[surface_id]


def test_kdense_runtime_projection_surfaces_are_no_authority_refs_only() -> None:
    projection = _projection({"action_id": "dispatch-kdense-runtime"})

    assert projection["refs_only"] is True
    assert projection["advisory_only"] is True
    assert projection["allowed_writes"] == []
    assert projection["writes_mas_truth"] is False
    assert projection["writes_runtime"] is False
    assert projection["can_claim_publication_ready"] is False
    assert projection["can_claim_paper_progress"] is False
    assert projection["authority_boundary"] == {
        "refs_only": True,
        "advisory_only": True,
        "nonblocking": True,
        "fail_open": True,
        "allowed_writes": [],
        "writes_mas_truth": False,
        "writes_runtime": False,
        "can_write_publication_eval": False,
        "can_write_controller_decisions": False,
        "can_sign_owner_receipt": False,
        "can_create_typed_blocker": False,
        "can_create_human_gate": False,
        "can_claim_publication_ready": False,
        "can_claim_paper_progress": False,
    }

    for surface in projection["surfaces"]:
        assert surface["refs_only"] is True
        assert surface["advisory_only"] is True
        assert surface["nonblocking"] is True
        assert surface["fail_open"] is True
        assert surface["allowed_writes"] == []
        assert surface["writes_mas_truth"] is False
        assert surface["writes_runtime"] is False
        assert surface["can_claim_publication_ready"] is False
        assert surface["can_claim_paper_progress"] is False


def test_kdense_runtime_projection_fail_open_without_dispatch() -> None:
    projection = _projection(None)

    assert projection["status"] == "projection_emitted"
    assert projection["fail_open"] is True
    assert projection["diagnostic"] == {"reason": "missing_or_invalid_dispatch"}
    assert projection["current_owner_action"] == {
        "action_type": None,
        "action_id": None,
        "owner": None,
        "work_unit_id": None,
        "work_unit_fingerprint": None,
        "dispatch_path": None,
    }


def test_kdense_runtime_projection_surfaces_do_not_write_files(tmp_path: Path) -> None:
    projection = _projection({"action_id": "dispatch-no-writes", "study_root": str(tmp_path)})

    assert projection["allowed_writes"] == []
    assert projection["written_refs"] == []
    assert all(surface["allowed_writes"] == [] for surface in projection["surfaces"])
    assert not (tmp_path / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (tmp_path / "artifacts" / "controller_decisions" / "latest.json").exists()
    assert not (tmp_path / "artifacts" / "runtime").exists()
    assert not (tmp_path / "runtime").exists()


def test_kdense_runtime_projection_marks_fusion_watch_only_and_nonblocking() -> None:
    projection = _projection({"action_id": "dispatch-kdense-runtime"})

    fusion = projection["openrouter_fusion_watch_only_briefing"]

    assert fusion["watch_only"] is True
    assert fusion["classification"] == "watch_only"
    assert fusion["nonblocking"] is True
    assert fusion["mainline_waits_for_surface"] is False
    assert fusion["can_claim_publication_ready"] is False
    assert fusion["can_claim_paper_progress"] is False
