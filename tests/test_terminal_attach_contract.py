from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

import yaml


def _write_quest(runtime_root: Path, *, quest_id: str, study_id: str, run_id: str) -> Path:
    quest_root = runtime_root / "quests" / quest_id
    run_root = quest_root / ".ds" / "runs" / run_id
    run_root.mkdir(parents=True)
    (quest_root / "quest.yaml").write_text(
        yaml.safe_dump(
            {
                "quest_id": quest_id,
                "study_id": study_id,
                "status": "running",
                "runtime_backend_id": "mas_runtime_core",
                "runtime_engine_id": "mas-runtime-core",
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (quest_root / ".ds" / "runtime_state.json").write_text(
        json.dumps(
            {
                "quest_id": quest_id,
                "study_id": study_id,
                "status": "running",
                "active_run_id": run_id,
                "worker_running": True,
                "runtime_backend_id": "mas_runtime_core",
                "runtime_engine_id": "mas-runtime-core",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (run_root / "worker_lease.json").write_text(
        json.dumps({"run_id": run_id, "terminal_attach_capable": True}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return quest_root


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


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


def test_terminal_attach_contract_exposes_mas_owned_runtime_actions() -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.terminal_attach_gate")

    assert module.SURFACE_KIND == "mas_terminal_attach_gate"
    assert module.BLOCKED_STATUS == "blocked_by_missing_terminal_input_owner"
    assert module.FORBIDDEN_OWNER == "legacy_mds_daemon_websocket"
    assert callable(module.attach_terminal)
    assert callable(module.terminal_input)
    assert callable(module.resize_terminal)
    assert callable(module.detach_terminal)
    assert not hasattr(module, "legacy_mds_websocket_attach")


def test_terminal_attach_contract_attaches_records_input_resize_and_detaches(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.terminal_attach_gate")
    runtime_root = tmp_path / "runtime"
    quest_root = _write_quest(runtime_root, quest_id="001-risk", study_id="001-risk", run_id="run-001")

    attached = module.attach_terminal(
        runtime_root=runtime_root,
        quest_id="001-risk",
        run_id="run-001",
        study_id="001-risk",
        idempotency_key="attach-1",
        source="test",
    )

    assert attached["ok"] is True
    assert attached["status"] == "attached"
    assert attached["surface_kind"] == "mas_terminal_attach_contract"
    token = attached["attach_token"]
    lease_id = attached["lease"]["lease_id"]

    input_receipt = module.terminal_input(
        runtime_root=runtime_root,
        quest_id="001-risk",
        run_id="run-001",
        study_id="001-risk",
        token=token,
        lease_id=lease_id,
        text="continue\n",
        idempotency_key="input-1",
        source="test",
    )
    assert input_receipt["ok"] is True
    assert input_receipt["status"] == "accepted"
    assert input_receipt["operation"] == "terminal_input"
    assert input_receipt["input"]["byte_count"] == len("continue\n".encode("utf-8"))
    assert input_receipt["command"]["status"] == "pending"
    assert "text" not in input_receipt["input"]

    resize_receipt = module.resize_terminal(
        runtime_root=runtime_root,
        quest_id="001-risk",
        run_id="run-001",
        study_id="001-risk",
        token=token,
        lease_id=lease_id,
        rows=40,
        cols=120,
        idempotency_key="resize-1",
        source="test",
    )
    assert resize_receipt["ok"] is True
    assert resize_receipt["status"] == "accepted"
    assert resize_receipt["terminal_size"] == {"rows": 40, "cols": 120}

    detached = module.detach_terminal(
        runtime_root=runtime_root,
        quest_id="001-risk",
        run_id="run-001",
        study_id="001-risk",
        token=token,
        lease_id=lease_id,
        idempotency_key="detach-1",
        source="test",
    )
    assert detached["ok"] is True
    assert detached["status"] == "detached"

    read_model = module.inspect_terminal_attach(
        runtime_root=runtime_root,
        quest_id="001-risk",
        run_id="run-001",
        study_id="001-risk",
        token=token,
        source="test",
    )
    assert read_model["status"] == "detached"
    assert read_model["latest_receipt"]["operation"] == "detach_terminal"

    store_root = quest_root / "artifacts" / "runtime" / "terminal_attach"
    latest = _read_json(store_root / "read_model" / "latest.json")
    assert latest["status"] == "detached"
    commands = (quest_root / ".ds" / "runs" / "run-001" / "terminal_commands.jsonl").read_text(encoding="utf-8")
    assert "terminal_input" in commands
    assert "resize_terminal" in commands
    assert "detach_terminal" in commands


def test_terminal_attach_contract_is_idempotent_for_replayed_keys(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.terminal_attach_gate")
    runtime_root = tmp_path / "runtime"
    quest_root = _write_quest(runtime_root, quest_id="001-risk", study_id="001-risk", run_id="run-001")

    first = module.attach_terminal(
        runtime_root=runtime_root,
        quest_id="001-risk",
        run_id="run-001",
        study_id="001-risk",
        idempotency_key="attach-1",
        source="test",
    )
    second = module.attach_terminal(
        runtime_root=runtime_root,
        quest_id="001-risk",
        run_id="run-001",
        study_id="001-risk",
        idempotency_key="attach-1",
        source="test",
    )

    assert second == first
    lines = (quest_root / "artifacts" / "runtime" / "terminal_attach" / "receipts.jsonl").read_text(
        encoding="utf-8"
    ).strip().splitlines()
    assert len(lines) == 1


def test_terminal_attach_contract_denies_wrong_run_without_opening_lease(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.terminal_attach_gate")
    runtime_root = tmp_path / "runtime"
    _write_quest(runtime_root, quest_id="001-risk", study_id="001-risk", run_id="run-001")

    denied = module.attach_terminal(
        runtime_root=runtime_root,
        quest_id="001-risk",
        run_id="run-wrong",
        study_id="001-risk",
        idempotency_key="attach-denied",
        source="test",
    )

    assert denied["ok"] is False
    assert denied["status"] == "denied"
    assert denied["reason"] == "run_id_mismatch"
    assert denied["lease"] is None


def test_terminal_attach_contract_denies_invalid_runtime_owner(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.terminal_attach_gate")
    runtime_root = tmp_path / "runtime"
    quest_root = _write_quest(runtime_root, quest_id="001-risk", study_id="001-risk", run_id="run-001")
    state_path = quest_root / ".ds" / "runtime_state.json"
    state = _read_json(state_path)
    state["runtime_backend_id"] = "legacy_mds_daemon_websocket"
    state_path.write_text(json.dumps(state, sort_keys=True) + "\n", encoding="utf-8")

    denied = module.attach_terminal(
        runtime_root=runtime_root,
        quest_id="001-risk",
        run_id="run-001",
        study_id="001-risk",
        idempotency_key="attach-denied-owner",
        source="test",
    )

    assert denied["ok"] is False
    assert denied["status"] == "denied"
    assert denied["reason"] == "invalid_runtime_owner"


def test_terminal_attach_contract_denies_invalid_token_and_stale_lease(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.terminal_attach_gate")
    runtime_root = tmp_path / "runtime"
    _write_quest(runtime_root, quest_id="001-risk", study_id="001-risk", run_id="run-001")
    attached = module.attach_terminal(
        runtime_root=runtime_root,
        quest_id="001-risk",
        run_id="run-001",
        study_id="001-risk",
        idempotency_key="attach-1",
        source="test",
    )

    denied_token = module.terminal_input(
        runtime_root=runtime_root,
        quest_id="001-risk",
        run_id="run-001",
        study_id="001-risk",
        token="wrong-token",
        lease_id=attached["lease"]["lease_id"],
        text="x",
        idempotency_key="input-denied-token",
        source="test",
    )
    stale = module.terminal_input(
        runtime_root=runtime_root,
        quest_id="001-risk",
        run_id="run-001",
        study_id="001-risk",
        token=attached["attach_token"],
        lease_id="stale-lease",
        text="x",
        idempotency_key="input-denied-lease",
        source="test",
    )

    assert denied_token["ok"] is False
    assert denied_token["reason"] == "invalid_token"
    assert stale["ok"] is False
    assert stale["reason"] == "lease_mismatch"
