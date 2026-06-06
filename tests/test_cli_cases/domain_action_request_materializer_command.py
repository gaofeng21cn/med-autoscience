from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from .shared import write_profile


def test_domain_action_request_materializer_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_materialize_domain_action_requests(
        *,
        profile,
        study_ids,
        mode: str,
        apply: bool,
    ) -> dict[str, object]:
        called["profile"] = profile
        called["study_ids"] = study_ids
        called["mode"] = mode
        called["apply"] = apply
        return {"surface": "domain_action_request_materializer", "repair_task_count": len(study_ids)}

    monkeypatch.setattr(cli.domain_action_request_materializer, "materialize_domain_action_requests", fake_materialize_domain_action_requests)

    exit_code = cli.main(
        [
            "domain-action-request-materialize",
            "--profile",
            str(profile_path),
            "--studies",
            "NF003",
            "DM002",
            "--mode",
            "developer_apply_safe",
            "--dry-run",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["study_ids"] == ("NF003", "DM002")
    assert called["mode"] == "developer_apply_safe"
    assert called["apply"] is False
    assert json.loads(captured.out)["surface"] == "domain_action_request_materializer"


def test_domain_action_request_materializer_command_apply_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_materialize_domain_action_requests(
        *,
        profile,
        study_ids,
        mode: str,
        apply: bool,
    ) -> dict[str, object]:
        called["profile"] = profile
        called["study_ids"] = study_ids
        called["mode"] = mode
        called["apply"] = apply
        return {
            "surface": "domain_action_request_materializer",
            "default_executor_dispatch_count": len(study_ids),
        }

    monkeypatch.setattr(cli.domain_action_request_materializer, "materialize_domain_action_requests", fake_materialize_domain_action_requests)

    exit_code = cli.main(
        [
            "domain-action-request-materialize",
            "--profile",
            str(profile_path),
            "--studies",
            "NF003",
            "DM002",
            "--mode",
            "developer_apply_safe",
            "--apply",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["study_ids"] == ("NF003", "DM002")
    assert called["mode"] == "developer_apply_safe"
    assert called["apply"] is True
    assert json.loads(captured.out)["default_executor_dispatch_count"] == 2


def test_domain_owner_action_dispatch_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_dispatch_domain_owner_actions(
        *,
        profile,
        study_ids,
        action_types,
        mode: str,
        apply: bool,
        consumer_payload,
    ) -> dict[str, object]:
        called["profile"] = profile
        called["study_ids"] = study_ids
        called["action_types"] = action_types
        called["mode"] = mode
        called["apply"] = apply
        called["consumer_payload"] = consumer_payload
        return {
            "surface": "default_executor_dispatch_executor",
            "execution_count": len(study_ids),
        }

    monkeypatch.setattr(
        cli.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        fake_dispatch_domain_owner_actions,
    )

    exit_code = cli.main(
        [
            "domain-owner-action-dispatch",
            "--profile",
            str(profile_path),
            "--studies",
            "NF003",
            "DM002",
            "--action-types",
            "return_to_ai_reviewer_workflow",
            "--mode",
            "developer_apply_safe",
            "--apply",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["study_ids"] == ("NF003", "DM002")
    assert called["action_types"] == ("return_to_ai_reviewer_workflow",)
    assert called["mode"] == "developer_apply_safe"
    assert called["apply"] is True
    assert called["consumer_payload"] is None
    assert json.loads(captured.out)["surface"] == "default_executor_dispatch_executor"


def test_domain_owner_action_dispatch_command_accepts_payload_file(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    payload_path = tmp_path / "consumer-payload.json"
    consumer_payload = {
        "surface": "domain_action_request_materializer",
        "schema_version": 1,
        "default_executor_dispatch_count": 1,
        "default_executor_dispatches": [
            {
                "surface": "default_executor_dispatch_request",
                "study_id": "DM003",
                "action_type": "complete_medical_paper_readiness_surface",
                "refs": {
                    "dispatch_path": (
                        "artifacts/supervision/consumer/default_executor_dispatches/"
                        "complete_medical_paper_readiness_surface.json"
                    )
                },
                "closeout_binding": {
                    "surface_kind": "opl_stage_run_closeout_binding",
                    "stage_run_id": "app-stage-run:medautoscience:domain-owner-default-executor-dispatch",
                    "stage_manifest_ref": "opl://stage-manifests/domain_owner%2Fdefault-executor-dispatch",
                    "current_pointer_ref": "opl://stage-runs/current",
                    "source_fingerprint": "mas_default_executor_source_current",
                    "idempotency_key": "idem_current",
                },
            }
        ],
    }
    payload_path.write_text(json.dumps(consumer_payload), encoding="utf-8")
    called: dict[str, object] = {}

    def fake_dispatch_domain_owner_actions(
        *,
        profile,
        study_ids,
        action_types,
        mode: str,
        apply: bool,
        consumer_payload,
    ) -> dict[str, object]:
        called["profile"] = profile
        called["study_ids"] = study_ids
        called["action_types"] = action_types
        called["mode"] = mode
        called["apply"] = apply
        called["consumer_payload"] = consumer_payload
        return {
            "surface": "default_executor_dispatch_executor",
            "received_payload_surface": consumer_payload["surface"],
        }

    monkeypatch.setattr(
        cli.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        fake_dispatch_domain_owner_actions,
    )

    exit_code = cli.main(
        [
            "domain-owner-action-dispatch",
            "--profile",
            str(profile_path),
            "--payload-file",
            str(payload_path),
            "--action-types",
            "complete_medical_paper_readiness_surface",
            "--mode",
            "developer_apply_safe",
            "--dry-run",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["study_ids"] == ()
    assert called["action_types"] == ("complete_medical_paper_readiness_surface",)
    assert called["mode"] == "developer_apply_safe"
    assert called["apply"] is False
    assert called["consumer_payload"] == consumer_payload
    assert json.loads(captured.out)["received_payload_surface"] == "domain_action_request_materializer"


def test_domain_owner_action_dispatch_command_rejects_retired_worker_flag(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_dispatch_domain_owner_actions(
        *,
        profile,
        study_ids,
        action_types,
        mode: str,
        apply: bool,
        consumer_payload,
    ) -> dict[str, object]:
        called["profile"] = profile
        called["study_ids"] = study_ids
        called["action_types"] = action_types
        called["mode"] = mode
        called["apply"] = apply
        called["consumer_payload"] = consumer_payload
        return {
            "surface": "default_executor_dispatch_executor",
        }

    monkeypatch.setattr(
        cli.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        fake_dispatch_domain_owner_actions,
    )

    retired_worker_flag = "--" + "managed-runtime" + "-worker"
    with pytest.raises(SystemExit) as excinfo:
        cli.main(
            [
                "domain-owner-action-dispatch",
                "--profile",
                str(profile_path),
                "--studies",
                "DM003",
                "--action-types",
                "return_to_ai_reviewer_workflow",
                "--mode",
                "developer_apply_safe",
                "--apply",
                retired_worker_flag,
            ]
        )
    err = capsys.readouterr().err

    assert excinfo.value.code == 2
    assert called == {}
    assert retired_worker_flag in err


def test_domain_owner_refresh_controller_decisions_command_dispatches_controller(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_refresh_controller_decisions_for_current_publication_eval(
        *,
        profile,
        study_ids,
        mode: str,
        apply: bool,
    ) -> dict[str, object]:
        called["profile"] = profile
        called["study_ids"] = study_ids
        called["mode"] = mode
        called["apply"] = apply
        return {
            "surface": "domain_owner_action_controller_decision_refresh",
            "refresh_count": len(study_ids),
        }

    monkeypatch.setattr(
        cli.domain_owner_action_dispatch,
        "refresh_controller_decisions_for_current_publication_eval",
        fake_refresh_controller_decisions_for_current_publication_eval,
    )

    exit_code = cli.main(
        [
            "domain-owner-action-refresh-controller-decisions",
            "--profile",
            str(profile_path),
            "--studies",
            "DM002",
            "DM003",
            "--mode",
            "developer_apply_safe",
            "--apply",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["study_ids"] == ("DM002", "DM003")
    assert called["mode"] == "developer_apply_safe"
    assert called["apply"] is True
    assert json.loads(captured.out)["surface"] == "domain_owner_action_controller_decision_refresh"


def test_medical_paper_readiness_owner_blocker_command_materializes_controller_decision(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_root = tmp_path / "study"

    exit_code = cli.main(
        [
            "medical-paper-readiness-owner-blocker",
            "--study-root",
            str(study_root),
            "--source",
            "test-cli",
            "--apply",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"

    assert exit_code == 0
    assert payload["surface"] == "medical_paper_readiness_owner_blocker"
    assert payload["status"] == "materialized"
    assert payload["applied"] is True
    assert payload["controller_decision_ref"] == str(decision_path.resolve())
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    assert decision["route_decision"] == "stable_blocker"
    assert decision["runtime_decision"] == "blocked"
    assert decision["quality_claim_authorized"] is False
    assert decision["submission_authorized"] is False
