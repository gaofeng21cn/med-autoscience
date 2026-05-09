from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.contract

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "contracts" / "test-lane-manifest.json"
CONTRACT_DOC_PATHS = (
    "docs/runtime/display/mas_live_console_mds_webui_parity_plan.md",
    "docs/runtime/display/progress_portal.md",
    "docs/runtime/display/live_console_ui_contract.md",
    "docs/references/mds-parity/mds_behavior_equivalence_gap_matrix.md",
    "docs/references/mds-parity/mds_webui_cleanroom_behavior_spec.md",
    "docs/references/mds-parity/mds_webui_user_parity_gap_review.md",
)
FORBIDDEN_AUTHORITY_SURFACES = (
    "paper/current_package",
    "manuscript/current_package",
    "paper/submission_minimal",
    "manuscript/submission_minimal",
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "study_truth",
    "runtime_lifecycle.sqlite",
)


def _manifest() -> dict[str, object]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_live_console_parity_lane_declares_read_only_contract_and_soak_boundary() -> None:
    lane = _manifest()["focused_lanes"]["live-console-parity"]

    assert lane["kind"] == "focused_live_console_parity_contract_gate"
    assert lane["paths"] == [
        "tests/test_live_console_docs_contract.py",
        "tests/test_live_console_cleanroom_spec.py",
        "tests/test_runtime_live_console_read_model.py",
        "tests/test_runtime_live_console_stream.py",
        "tests/test_runtime_live_console_ui.py",
        "tests/test_progress_portal.py",
        "tests/test_cli_cases/progress_portal_commands.py",
        "tests/test_workspace_init_cases/workspace_creation.py",
    ]
    assert lane["docs"] == list(CONTRACT_DOC_PATHS)
    assert lane["overlap_policy"] == "allowed_with_regression"
    assert lane["authority_boundary"] == "read_only_streaming_parity_contract"
    assert lane["implementation_status"] == "landed"
    assert lane["clean_room_required"] is True
    assert lane["forbidden_authority_writes"] == list(FORBIDDEN_AUTHORITY_SURFACES)

    soak = lane["real_workspace_soak"]
    assert soak["profile_path"].endswith(
        "/DM-CVD-Mortality-Risk/ops/medautoscience/profiles/dm-cvd-mortality-risk.workspace.toml"
    )
    assert soak["study_lines"] == ["DM002", "DPCC003"]
    assert soak["latest_status"] in {"pending_fresh_verification", "passed_read_only_snapshot"}
    assert isinstance(soak["latest_observed_at"], str)
    assert soak["commands"] == [
        'uv run python -m med_autoscience.cli workspace progress-portal --profile "$PROFILE" --format json',
        'uv run python -m med_autoscience.cli runtime live-console --profile "$PROFILE" --snapshot --format json',
    ]


def test_portal_route_decision_trail_and_terminal_attach_have_machine_contracts() -> None:
    lanes = _manifest()["focused_lanes"]
    route = lanes["portal-route-decision-trail"]
    terminal = lanes["terminal-attach-gate"]
    soak = lanes["portal-console-soak"]

    assert route["implementation_status"] == "landed_read_only_contract"
    assert route["surface_kind"] == "mas_progress_portal_route_decision_trail"
    assert route["authority_boundary"] == "read_only_route_decision_projection"
    assert route["fail_closed_when_inputs_missing"] is True
    assert route["required_inputs"] == [
        "controller_decisions",
        "evidence_or_review_ledgers",
        "runtime_lifecycle_lineage_or_canvas",
        "source_refs",
    ]
    assert set(route["required_display_fields"]) == {
        "route_node",
        "decision_rationale",
        "blocked_reason",
        "pivot_rationale",
        "superseded_path",
        "active_path",
        "winning_path",
        "source_refs",
    }
    assert "publication_eval/latest.json" in route["forbidden_authority_writes"]
    assert "controller_decisions/latest.json" in route["forbidden_authority_writes"]
    assert "tests/progress_portal_cases" in route["paths"]
    assert "route_decision_trail" in soak["required_evidence_keys"]
    assert "conversation_portal_panel" in soak["required_evidence_keys"]
    assert "authorized_action_apply_receipts" in soak["required_evidence_keys"]
    assert "tests/progress_portal_cases" in soak["paths"]

    assert terminal["implementation_status"] == "landed_fail_closed_gate"
    assert terminal["surface_kind"] == "mas_terminal_attach_gate"
    assert terminal["blocked_status"] == "blocked_by_missing_terminal_input_owner"
    assert terminal["forbidden_owner"] == "legacy_mds_daemon_websocket"
    assert terminal["read_only_default"] is True
    assert terminal["attach_session_started_when_blocked"] is False
    assert set(terminal["required_owner_contract"]) == {
        "token",
        "lease",
        "idempotency",
        "audit",
        "input",
        "resize",
        "detach",
    }


def test_live_console_parity_manifest_keeps_doc_refs_and_forbidden_authority_surfaces() -> None:
    lane = _manifest()["focused_lanes"]["live-console-parity"]
    manifest_forbidden = set(
        lane["forbidden_authority_writes"]
    )

    assert lane["docs"] == list(CONTRACT_DOC_PATHS)
    assert manifest_forbidden == set(FORBIDDEN_AUTHORITY_SURFACES)
