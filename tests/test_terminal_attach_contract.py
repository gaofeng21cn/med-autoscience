from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

import pytest
import yaml


def _write_quest(runtime_root: Path, *, quest_id: str, study_id: str, run_id: str) -> Path:
    quest_root = runtime_root / "quests" / quest_id
    quest_root.mkdir(parents=True)
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
    state_path = quest_root / ".ds" / "runtime_state.json"
    state_path.parent.mkdir(parents=True)
    state_path.write_text(
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
    return quest_root


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


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
    assert attached["lease"]["status"] == "active"
    assert attached["lease"]["run_id"] == "run-001"
    assert attached["attach_token"]

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
    assert read_model["lease"]["lease_id"] == lease_id
    assert read_model["latest_receipt"]["operation"] == "detach_terminal"

    store_root = quest_root / "artifacts" / "runtime" / "terminal_attach"
    latest = _read_json(store_root / "read_model" / "latest.json")
    assert latest["status"] == "detached"
    lines = (store_root / "receipts.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert [json.loads(line)["operation"] for line in lines] == [
        "attach_terminal",
        "terminal_input",
        "resize_terminal",
        "detach_terminal",
    ]


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
    quest_root = _write_quest(runtime_root, quest_id="001-risk", study_id="001-risk", run_id="run-001")

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
    read_model = _read_json(quest_root / "artifacts" / "runtime" / "terminal_attach" / "read_model" / "latest.json")
    assert read_model["status"] == "denied"
    assert read_model["latest_receipt"]["reason"] == "run_id_mismatch"


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
    assert denied_token["ok"] is False
    assert denied_token["reason"] == "invalid_token"

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
    assert stale["ok"] is False
    assert stale["reason"] == "lease_mismatch"


def test_runtime_backend_contract_exposes_terminal_attach_owner_operations() -> None:
    module = importlib.import_module("med_autoscience.runtime_backend")
    backend = module.get_managed_runtime_backend(module.DEFAULT_MANAGED_RUNTIME_BACKEND_ID)

    for operation_name in (
        "inspect_terminal_attach",
        "attach_terminal",
        "terminal_input",
        "resize_terminal",
        "detach_terminal",
    ):
        assert callable(getattr(backend, operation_name))
        assert operation_name in module._BACKEND_CALLABLE_CONTRACT
