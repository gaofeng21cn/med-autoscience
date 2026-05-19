from __future__ import annotations

import importlib
import json
from pathlib import Path

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
            "runtime",
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
            "runtime",
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
        managed_runtime_worker: bool,
    ) -> dict[str, object]:
        called["profile"] = profile
        called["study_ids"] = study_ids
        called["action_types"] = action_types
        called["mode"] = mode
        called["apply"] = apply
        called["managed_runtime_worker"] = managed_runtime_worker
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
            "runtime",
            "domain-owner-action-dispatch",
            "--profile",
            str(profile_path),
            "--studies",
            "NF003",
            "DM002",
            "--action-types",
            "runtime_platform_repair",
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
    assert called["action_types"] == ("runtime_platform_repair", "return_to_ai_reviewer_workflow")
    assert called["mode"] == "developer_apply_safe"
    assert called["apply"] is True
    assert called["managed_runtime_worker"] is False
    assert json.loads(captured.out)["surface"] == "default_executor_dispatch_executor"


def test_domain_owner_action_dispatch_command_accepts_managed_runtime_worker_flag(
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
        managed_runtime_worker: bool,
    ) -> dict[str, object]:
        called["profile"] = profile
        called["study_ids"] = study_ids
        called["action_types"] = action_types
        called["mode"] = mode
        called["apply"] = apply
        called["managed_runtime_worker"] = managed_runtime_worker
        return {
            "surface": "default_executor_dispatch_executor",
            "managed_runtime_worker": managed_runtime_worker,
        }

    monkeypatch.setattr(
        cli.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        fake_dispatch_domain_owner_actions,
    )

    exit_code = cli.main(
        [
            "runtime",
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
            "--managed-runtime-worker",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["study_ids"] == ("DM003",)
    assert called["action_types"] == ("return_to_ai_reviewer_workflow",)
    assert called["mode"] == "developer_apply_safe"
    assert called["apply"] is True
    assert called["managed_runtime_worker"] is True
    assert json.loads(captured.out)["managed_runtime_worker"] is True


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
            "runtime",
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
