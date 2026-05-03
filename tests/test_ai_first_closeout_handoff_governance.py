from __future__ import annotations

from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
GOVERNANCE_PATH = REPO_ROOT / "docs/program/ai_first_closeout_handoff_governance.md"
LEDGER_PATH = REPO_ROOT / "docs/program/plan_completion_ledger.md"
USABLE_CLOSEOUT_PROJECTION_PATH = (
    REPO_ROOT / "docs/program/ai_first_usable_closeout_projection.md"
)

REQUIRED_LEDGER_FIELDS = (
    "plan_id",
    "planned_items",
    "landed_commits",
    "tests_run",
    "pushed",
    "worktrees_cleaned",
    "live_surface_verified",
    "skipped_with_user_acceptance",
    "remaining_gaps",
    "handoff_receiver",
    "handoff_entrypoint",
    "out_of_scope_boundaries",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _markdown_table_headers(text: str) -> set[str]:
    headers: set[str] = set()
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        headers.update(cell for cell in cells if cell)
    return headers


def test_ai_first_handoff_governance_defines_required_ledger_schema() -> None:
    governance = _read(GOVERNANCE_PATH)
    headers = _markdown_table_headers(governance)

    for field in REQUIRED_LEDGER_FIELDS:
        assert field in headers


def test_plan_completion_ledger_exposes_handoff_template_fields() -> None:
    ledger = _read(LEDGER_PATH)
    headers = _markdown_table_headers(ledger)

    for field in REQUIRED_LEDGER_FIELDS:
        assert field in headers


def test_ai_first_handoff_governance_records_owner_and_cleanup_enums() -> None:
    combined = "\n".join((_read(GOVERNANCE_PATH), _read(LEDGER_PATH)))

    for required_status in (
        "external_active_owner",
        "not_performed_by_request",
        "yes",
        "no",
        "none",
    ):
        assert required_status in combined


def test_ai_first_handoff_governance_records_non_scope_boundaries() -> None:
    combined = "\n".join((_read(GOVERNANCE_PATH), _read(LEDGER_PATH)))

    for boundary in (
        "DM002",
        "risk-*",
        "真实论文 soak",
        "external worktree",
    ):
        assert boundary in combined


def test_usable_closeout_projection_records_fillable_fields_and_plan_items() -> None:
    projection = _read(USABLE_CLOSEOUT_PROJECTION_PATH)

    for field in (
        *REQUIRED_LEDGER_FIELDS,
        "closure_claim",
        "claim_boundary",
    ):
        assert f"`{field}`" in projection

    for item in (
        "dispatch default materialization",
        "operator lifecycle",
        "cross-study runtime integration",
        "quality learning ops report",
        "external lane safety gate",
        "usable closeout projection",
    ):
        assert item in projection


def test_usable_closeout_projection_keeps_claims_inside_lane_boundaries() -> None:
    projection = _read(USABLE_CLOSEOUT_PROJECTION_PATH)

    for boundary in (
        "不新增文档 wording gate",
        "不修改 `README*`",
        "不读写 `DM002` live artifact",
        "不清理任何 worktree",
        "不宣称真实论文 soak 已完成",
        "不宣称真实论文质量改善",
    ):
        assert boundary in projection
