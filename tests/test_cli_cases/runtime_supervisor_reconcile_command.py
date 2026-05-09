from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from .shared import write_profile


@pytest.mark.parametrize(
    "command",
    (
        ["runtime", "supervisor-reconcile"],
        ["runtime-supervisor-reconcile"],
    ),
)
def test_runtime_supervisor_reconcile_command_runs_one_shot_and_writes_receipt(
    command: list[str],
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    reconcile = importlib.import_module("med_autoscience.controllers.runtime_supervisor_reconcile")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    calls: list[tuple[str, tuple[str, ...]]] = []

    def fake_supervisor_scan(
        *,
        profile,
        study_ids,
        apply_safe_actions: bool,
        apply_runtime_platform_repair: bool = False,
        developer_supervisor_mode: str | None = None,
    ) -> dict[str, object]:
        calls.append(("scan", tuple(study_ids)))
        suffix = len([name for name, _ in calls if name == "scan"])
        return {
            "surface": "portable_runtime_supervisor_scan",
            "workspace_root": str(profile.workspace_root),
            "studies": [
                {
                    "study_id": "DM002",
                    "owner_route": {"next_owner": f"owner-{suffix}", "idempotency_key": f"route-{suffix}"},
                    "action_queue": [{"action_type": f"action-{suffix}"}],
                    "why_not_applied": None if suffix == 1 else "publication_gate_blocked",
                    "owner_forwarded": suffix == 2,
                    "stable_blocker": {"kind": "publication_gate", "status": "blocked"},
                }
            ],
            "action_queue": [{"study_id": "DM002", "action_type": f"action-{suffix}"}],
        }

    def fake_supervisor_consume(
        *,
        profile,
        study_ids,
        mode: str,
        apply: bool,
    ) -> dict[str, object]:
        calls.append(("consume", tuple(study_ids)))
        return {
            "surface": "runtime_supervisor_consumer",
            "requested_studies": list(study_ids),
            "request_tasks": [{"study_id": "DM002", "dispatch_status": "applied"}],
            "default_executor_dispatches": [
                {"study_id": "DM002", "action_type": "publication_gate_specificity_required", "dispatch_status": "ready"}
            ],
        }

    def fake_execute_default_executor_dispatches(
        *,
        profile,
        study_ids,
        action_types,
        mode: str,
        apply: bool,
    ) -> dict[str, object]:
        calls.append(("execute-dispatch", tuple(study_ids)))
        return {
            "surface": "default_executor_dispatch_executor",
            "requested_studies": list(study_ids),
            "codex_dispatch_count": 0,
            "suppressed_dispatch_count": 1,
            "dry_run_count": 0,
            "blocked_count": 1,
            "executions": [
                {
                    "study_id": "DM002",
                    "action_type": "publication_gate_specificity_required",
                    "execution_status": "blocked",
                    "blocked_reason": "quest_root_missing",
                }
            ],
        }

    monkeypatch.setattr(reconcile.runtime_supervisor_scan, "supervisor_scan", fake_supervisor_scan)
    monkeypatch.setattr(reconcile.runtime_supervisor_consumer, "supervisor_consume", fake_supervisor_consume)
    monkeypatch.setattr(
        reconcile.runtime_supervisor_dispatch_executor,
        "execute_default_executor_dispatches",
        fake_execute_default_executor_dispatches,
    )

    exit_code = cli.main(
        [
            *command,
            "--profile",
            str(profile_path),
            "--studies",
            "DM002",
            "--mode",
            "developer_apply_safe",
            "--apply",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert calls == [
        ("scan", ("DM002",)),
        ("consume", ("DM002",)),
        ("execute-dispatch", ("DM002",)),
        ("scan", ("DM002",)),
    ]
    assert payload["surface"] == "runtime_supervisor_reconcile_receipt"
    assert payload["before"]["studies"][0]["owner_route"]["next_owner"] == "owner-1"
    assert payload["after"]["studies"][0]["owner_route"]["next_owner"] == "owner-2"
    assert payload["executed_dispatch"]["executions"][0]["blocked_reason"] == "quest_root_missing"
    assert payload["codex_dispatch_count"] == 0
    assert payload["suppressed_dispatch_count"] == 1
    assert payload["will_start_llm"] is False
    assert payload["action_cost"]["action_class"] == "controller_apply"
    assert payload["study_receipts"][0]["before"]["action_queue"][0]["action_type"] == "action-1"
    assert payload["study_receipts"][0]["after"]["why_not_applied"] == "publication_gate_blocked"
    assert payload["study_receipts"][0]["after"]["owner_forwarded"] is True
    assert payload["study_receipts"][0]["after"]["stable_blocker"]["kind"] == "publication_gate"
    latest_path = workspace_root / "artifacts" / "supervision" / "reconcile" / "latest.json"
    history_path = workspace_root / "artifacts" / "supervision" / "reconcile" / "history.jsonl"
    assert json.loads(latest_path.read_text(encoding="utf-8"))["surface"] == "runtime_supervisor_reconcile_receipt"
    assert history_path.read_text(encoding="utf-8").strip()
