from __future__ import annotations

import json
from pathlib import Path

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_runtime_domain_owner_action_dispatch_command_dispatches_controller(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    import importlib

    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    calls: list[dict[str, object]] = []

    def fake_dispatch_domain_owner_actions(**kwargs) -> dict[str, object]:
        calls.append(kwargs)
        return {
            "surface": "opl_authorized_owner_callable_adapter_dispatch",
            "dry_run": not kwargs["apply"],
            "requested_studies": list(kwargs["study_ids"]),
            "requested_action_types": list(kwargs["action_types"]),
            "execution_count": 0,
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
            "--study-id",
            "002-dm-china-us-mortality-attribution",
            "--studies",
            "003-dpcc-primary-care-phenotype-treatment-gap",
            "--mode",
            "developer_apply_safe",
            "--action-type",
            "return_to_ai_reviewer_workflow",
            "--apply",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["surface"] == "opl_authorized_owner_callable_adapter_dispatch"
    assert payload["dry_run"] is False
    assert payload["requested_studies"] == [
        "003-dpcc-primary-care-phenotype-treatment-gap",
        "002-dm-china-us-mortality-attribution",
    ]
    assert calls
    assert calls[0]["profile"].name == "nfpitnet"
    assert calls[0]["study_ids"] == (
        "003-dpcc-primary-care-phenotype-treatment-gap",
        "002-dm-china-us-mortality-attribution",
    )
    assert calls[0]["mode"] == "developer_apply_safe"
    assert calls[0]["apply"] is True
    assert calls[0]["action_types"] == ("return_to_ai_reviewer_workflow",)


def test_runtime_domain_owner_action_dispatch_command_defaults_to_dry_run(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    import importlib

    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    calls: list[dict[str, object]] = []

    def fake_dispatch_domain_owner_actions(**kwargs) -> dict[str, object]:
        calls.append(kwargs)
        return {"surface": "opl_authorized_owner_callable_adapter_dispatch", "dry_run": not kwargs["apply"]}

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
            "--study-id",
            "002-dm-china-us-mortality-attribution",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["dry_run"] is True
    assert calls[0]["mode"] == "external_observe"
    assert calls[0]["apply"] is False
