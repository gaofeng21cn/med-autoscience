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
        retain_unscanned_studies: bool = True,
    ) -> dict[str, object]:
        called["profile"] = profile
        called["study_ids"] = study_ids
        called["apply_safe_actions"] = apply_safe_actions
        called["developer_supervisor_mode"] = developer_supervisor_mode
        called["retain_unscanned_studies"] = retain_unscanned_studies
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
    assert called["retain_unscanned_studies"] is False
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
        retain_unscanned_studies: bool = True,
    ) -> dict[str, object]:
        called["profile"] = profile
        called["study_ids"] = study_ids
        called["retain_unscanned_studies"] = retain_unscanned_studies
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
    assert called["retain_unscanned_studies"] is True
    assert json.loads(captured.out)["study_count"] == 2


def test_owner_route_reconcile_explicit_study_scan_output_stays_scoped() -> None:
    scan_output = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.scan_output"
    )

    studies, action_queue = scan_output.merge_previous_unscanned_study_handoff(
        previous_payload={
            "generated_at": "2026-06-02T00:00:00Z",
            "studies": [{"study_id": "003-dpcc", "handoff_scan_status": "scanned"}],
            "action_queue": [{"study_id": "003-dpcc", "action_id": "stale-003"}],
        },
        scanned_studies=[{"study_id": "002-dm", "handoff_scan_status": "scanned"}],
        scanned_action_queue=[{"study_id": "002-dm", "action_id": "current-002"}],
        retain_unscanned_studies=False,
    )

    assert studies == [{"study_id": "002-dm", "handoff_scan_status": "scanned"}]
    assert action_queue == [{"study_id": "002-dm", "action_id": "current-002"}]


def test_owner_route_reconcile_scoped_scan_does_not_retain_previous_execution_envelopes() -> None:
    scan_output = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.scan_output"
    )

    envelopes = scan_output.merge_current_execution_envelopes(
        previous_payload={
            "current_execution_envelopes": {
                "003-dpcc": {"state_kind": "running_provider_attempt"},
            },
        },
        output_studies=[
            {
                "study_id": "002-dm",
                "current_execution_envelope": {"state_kind": "executable_owner_action"},
            }
        ],
        scanned_studies=[{"study_id": "002-dm"}],
        retain_unscanned_studies=False,
    )

    assert envelopes == {"002-dm": {"state_kind": "executable_owner_action"}}


def test_owner_route_reconcile_retained_study_keeps_previous_live_running_envelope() -> None:
    scan_output = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.scan_output"
    )

    envelopes = scan_output.merge_current_execution_envelopes(
        previous_payload={
            "current_execution_envelopes": {
                "002-dm": {
                    "state_kind": "running_provider_attempt",
                    "owner": "med-autoscience",
                    "next_work_unit": "ai_reviewer_record_gate_consumption",
                    "source": "opl_provider_attempt",
                },
            },
        },
        output_studies=[
            {
                "study_id": "002-dm",
                "handoff_scan_status": "retained_from_previous_scan",
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "write",
                    "next_work_unit": "ai_reviewer_record_gate_consumption",
                    "source": "older_retained_study_projection",
                },
            },
            {
                "study_id": "003-dpcc",
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "ai_reviewer",
                    "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                },
            },
        ],
        scanned_studies=[{"study_id": "003-dpcc"}],
        retain_unscanned_studies=True,
    )

    assert envelopes["002-dm"]["state_kind"] == "running_provider_attempt"
    assert envelopes["002-dm"]["source"] == "opl_provider_attempt"
    assert envelopes["003-dpcc"]["owner"] == "ai_reviewer"
