from __future__ import annotations

from . import shared as _shared


globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_cleanup_apply_command_passes_control_plane_snapshot_json(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}
    snapshot = {
        "surface": "control_plane_snapshot",
        "authority_refs": {
            "study_truth": {"epoch": "truth-1"},
            "runtime_health": {"epoch": "runtime-1"},
        },
        "dispatch_gate": {"state": "open", "blocking_reasons": []},
        "route_authorization": {"cleanup_apply_allowed": True},
    }

    def fake_run_cleanup_apply(
        *,
        workspace_roots,
        apply: bool,
        control_plane_snapshot=None,
        retention_report=None,
    ) -> dict[str, object]:
        called.update({
            "workspace_roots": list(workspace_roots),
            "apply": apply,
            "control_plane_snapshot": control_plane_snapshot,
            "retention_report": retention_report,
        })
        return {"surface": "control_plane_cleanup_apply", "apply": apply, "action_counts": {"mutating": 0}}

    monkeypatch.setattr(cli.control_plane_cleanup_apply, "run_cleanup_apply", fake_run_cleanup_apply)

    exit_code = cli.main([
        "control-plane-cleanup-apply",
        "--workspace-root",
        str(tmp_path / "workspace"),
        "--apply",
        "--control-plane-snapshot-json",
        json.dumps(snapshot),
    ])

    assert exit_code == 0
    assert called == {
        "workspace_roots": [tmp_path / "workspace"],
        "apply": True,
        "control_plane_snapshot": snapshot,
        "retention_report": None,
    }
    assert json.loads(capsys.readouterr().out)["surface"] == "control_plane_cleanup_apply"


def test_cleanup_apply_command_passes_retention_report_file(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}
    retention_report = {
        "surface": "control_plane_lifecycle_report",
        "workspaces": [
            {
                "workspace_root": str(tmp_path / "workspace"),
                "retention_plan": {
                    "operation_sample": [
                        {
                            "retention_action": "delete_safe_cache",
                            "cleanup_candidate_action": "delete-safe-cache",
                            "physical_delete_allowed": True,
                            "workspace_relative_path": "scratch/cache",
                        }
                    ]
                },
            }
        ],
    }
    report_path = tmp_path / "retention-report.json"
    report_path.write_text(json.dumps(retention_report), encoding="utf-8")

    def fake_run_cleanup_apply(
        *,
        workspace_roots,
        apply: bool,
        control_plane_snapshot=None,
        retention_report=None,
    ) -> dict[str, object]:
        called.update({
            "workspace_roots": list(workspace_roots),
            "apply": apply,
            "control_plane_snapshot": control_plane_snapshot,
            "retention_report": retention_report,
        })
        return {"surface": "control_plane_cleanup_apply", "apply": apply, "action_counts": {"mutating": 0}}

    monkeypatch.setattr(cli.control_plane_cleanup_apply, "run_cleanup_apply", fake_run_cleanup_apply)

    exit_code = cli.main([
        "control-plane-cleanup-apply",
        "--workspace-root",
        str(tmp_path / "workspace"),
        "--retention-report-file",
        str(report_path),
    ])

    assert exit_code == 0
    assert called == {
        "workspace_roots": [tmp_path / "workspace"],
        "apply": False,
        "control_plane_snapshot": None,
        "retention_report": retention_report,
    }
    assert json.loads(capsys.readouterr().out)["surface"] == "control_plane_cleanup_apply"


def test_backfill_apply_command_passes_control_plane_snapshot_json(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}
    snapshot = {
        "surface": "control_plane_snapshot",
        "authority_refs": {
            "study_truth": {"epoch": "truth-1"},
            "runtime_health": {"epoch": "runtime-1"},
        },
        "dispatch_gate": {"state": "open", "blocking_reasons": []},
        "route_authorization": {"bundle_build_allowed": True},
    }

    def fake_run_backfill_apply(*, workspace_roots, apply: bool, control_plane_snapshot=None) -> dict[str, object]:
        called.update({
            "workspace_roots": list(workspace_roots),
            "apply": apply,
            "control_plane_snapshot": control_plane_snapshot,
        })
        return {"surface": "control_plane_backfill_apply", "apply": apply, "action_counts": {"mutating": 0}}

    monkeypatch.setattr(cli.control_plane_backfill_apply, "run_backfill_apply", fake_run_backfill_apply)

    exit_code = cli.main([
        "control-plane-backfill-apply",
        "--workspace-root",
        str(tmp_path / "workspace"),
        "--apply",
        "--control-plane-snapshot-json",
        json.dumps(snapshot),
    ])

    assert exit_code == 0
    assert called == {
        "workspace_roots": [tmp_path / "workspace"],
        "apply": True,
        "control_plane_snapshot": snapshot,
    }
    assert json.loads(capsys.readouterr().out)["surface"] == "control_plane_backfill_apply"
