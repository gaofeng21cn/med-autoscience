from __future__ import annotations

import importlib
import json
from pathlib import Path

from .shared import write_profile


def test_owner_route_reconcile_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_scan_domain_routes(
        *,
        profile,
        study_ids,
        apply_safe_actions: bool,
        developer_supervisor_mode: str | None = None,
    ) -> dict[str, object]:
        called["profile"] = profile
        called["study_ids"] = study_ids
        called["apply_safe_actions"] = apply_safe_actions
        called["developer_supervisor_mode"] = developer_supervisor_mode
        return {"surface": "owner_route_reconcile", "study_count": len(study_ids)}

    monkeypatch.setattr(cli.owner_route_reconcile, "scan_domain_routes", fake_scan_domain_routes)

    exit_code = cli.main(
        [
            "owner-route-reconcile",
            "--profile",
            str(profile_path),
            "--studies",
            "NF003",
            "DM002",
            "--apply-safe-actions",
            "--developer-supervisor-mode",
            "developer_apply_safe",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["study_ids"] == ("NF003", "DM002")
    assert called["apply_safe_actions"] is True
    assert called["developer_supervisor_mode"] == "developer_apply_safe"
    assert json.loads(captured.out)["surface"] == "owner_route_reconcile"


def test_owner_route_reconcile_command_discovers_studies_when_not_explicit(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    studies_root = workspace_root / "studies"
    for study_id in ("002-second", "001-first"):
        study_root = studies_root / study_id
        study_root.mkdir(parents=True)
        (study_root / "study.yaml").write_text("study_id: test\n", encoding="utf-8")
    (studies_root / "not-a-study").mkdir()
    called: dict[str, object] = {}

    def fake_scan_domain_routes(
        *,
        profile,
        study_ids,
        apply_safe_actions: bool,
        developer_supervisor_mode: str | None = None,
    ) -> dict[str, object]:
        called["profile"] = profile
        called["study_ids"] = study_ids
        return {"surface": "owner_route_reconcile", "study_count": len(study_ids)}

    monkeypatch.setattr(cli.owner_route_reconcile, "scan_domain_routes", fake_scan_domain_routes)

    exit_code = cli.main(
        [
            "owner-route-reconcile",
            "--profile",
            str(profile_path),
            "--apply-safe-actions",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["study_ids"] == ("001-first", "002-second")
    assert json.loads(captured.out)["study_count"] == 2
