from __future__ import annotations

import importlib
from pathlib import Path


def test_terminal_attach_contract_fails_closed_until_input_owner_lands(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.terminal_attach_gate")

    payload = module.blocked_by_missing_terminal_input_owner(
        profile_ref=tmp_path / "profile.toml",
        study_id="001-risk",
        study_root=tmp_path / "study",
    )

    assert payload["surface_kind"] == "mas_terminal_attach_gate"
    assert payload["status"] == "blocked_by_missing_terminal_input_owner"
    assert payload["attach_started"] is False
    assert payload["read_only_default"] is True
    assert payload["forbidden_owner"] == "legacy_mds_daemon_websocket"
    assert payload["profile_ref"] == str(tmp_path / "profile.toml")
    assert payload["study_id"] == "001-risk"
    assert payload["study_root"] == str(tmp_path / "study")

    required = payload["required_owner_contract"]
    assert set(required) == {"token", "lease", "idempotency", "audit", "input", "resize", "detach"}
    assert "MAS-issued attach token" in required["token"]
    assert "append-only receipt" in required["audit"]

    risks = payload["threat_model"]["risks"]
    assert "unauthorized_terminal_input" in risks
    assert "legacy_daemon_regaining_runtime_ownership" in risks
    assert payload["threat_model"]["fail_closed_without_owner"] is True


def test_terminal_attach_contract_does_not_expose_legacy_runtime_actions() -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.terminal_attach_gate")

    assert module.SURFACE_KIND == "mas_terminal_attach_gate"
    assert module.BLOCKED_STATUS == "blocked_by_missing_terminal_input_owner"
    assert module.FORBIDDEN_OWNER == "legacy_mds_daemon_websocket"
    for legacy_or_unimplemented_name in (
        "attach_terminal",
        "terminal_input",
        "resize_terminal",
        "detach_terminal",
        "legacy_mds_websocket_attach",
    ):
        assert not hasattr(module, legacy_or_unimplemented_name)
