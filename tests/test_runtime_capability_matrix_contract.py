from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta
REPO_ROOT = Path(__file__).resolve().parents[1]


def test_runtime_capability_matrix_pins_backend_health_fields() -> None:
    doc = (REPO_ROOT / "docs/runtime/runtime_capability_matrix.md").read_text(encoding="utf-8")
    for field in (
        "backend_id",
        "transport_owner",
        "mcp_ready",
        "long_running_tool_timeout_sec",
        "supports_pause_resume",
        "supports_user_message_queue",
        "supports_artifact_inventory",
        "supports_workspace_file_refs",
        "doctor_status",
        "blocking_reasons",
    ):
        assert field in doc
    assert "不要求 MAS 追随 upstream 的 Claude、Kimi、OpenCode provider 扩面" in doc
