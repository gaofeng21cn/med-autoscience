from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.contract

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "contracts" / "test-lane-manifest.json"
CONTRACT_DOCS = (
    "docs/runtime/mas_live_console_mds_webui_parity_plan.md",
    "docs/runtime/progress_portal.md",
    "docs/runtime/live_console_ui_contract.md",
    "docs/references/mds_behavior_equivalence_gap_matrix.md",
    "docs/references/mds_webui_cleanroom_behavior_spec.md",
    "docs/references/mds_webui_user_parity_gap_review.md",
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


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


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
    assert lane["docs"] == list(CONTRACT_DOCS)
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


def test_live_console_parity_docs_expose_staged_contract_metadata() -> None:
    contract_doc = _read(CONTRACT_DOCS[0])
    portal_doc = _read(CONTRACT_DOCS[1])
    ui_doc = _read(CONTRACT_DOCS[2])
    gap_matrix = _read(CONTRACT_DOCS[3])
    user_gap_review = _read(CONTRACT_DOCS[5])

    assert "Contract ID: `live-console-parity`" in contract_doc
    assert "Status: `landed" in contract_doc
    assert "Related contract: `live-console-parity`" in portal_doc
    assert "Related contract: `live-console-parity`" in ui_doc
    assert "Related contract: `live-console-parity`" in gap_matrix

    assert "focused_lanes.live-console-parity" in contract_doc
    assert "Progress Portal 与 Live Console 分工" in contract_doc
    assert "Live Console Integration Boundary" in portal_doc
    assert "Live Console UI Contract" in ui_doc
    assert "Live Console Parity" in gap_matrix
    assert "Status: `active UX parity reference`" in user_gap_review
    assert "per-study/per-paper page" in user_gap_review
    assert "interactive parity candidate" in user_gap_review


def test_live_console_parity_docs_keep_paper_and_package_authority_forbidden() -> None:
    contract_doc = _read(CONTRACT_DOCS[0])
    portal_doc = _read(CONTRACT_DOCS[1])
    gap_matrix = _read(CONTRACT_DOCS[3])
    manifest_forbidden = set(
        _manifest()["focused_lanes"]["live-console-parity"]["forbidden_authority_writes"]
    )

    assert manifest_forbidden == set(FORBIDDEN_AUTHORITY_SURFACES)
    for surface in FORBIDDEN_AUTHORITY_SURFACES:
        assert surface in contract_doc
        assert surface in gap_matrix

    assert "pause / resume / relaunch / reconcile" in portal_doc
    assert "UI 不直接执行 apply" in portal_doc
    assert "不得修改 paper/package" in portal_doc
