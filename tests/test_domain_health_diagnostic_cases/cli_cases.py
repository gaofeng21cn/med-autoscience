from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_watch_runtime_alert_delivery_backend_contract_is_not_exposed() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    assert not hasattr(module, "runtime_backend_contract")
    assert not hasattr(module, "deliver_alert")
def test_suppresses_duplicate_data_asset_gate_blocker(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        return {
            "status": "blocked",
            "blockers": ["outdated_private_release"],
            "study_id": quest_root.name,
            "report_json": str(quest_root / "artifacts" / "reports" / "data_asset_gate" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "data_asset_gate" / "latest.md"),
            "intervention_enqueued": apply,
        }

    first = module.run_domain_health_diagnostic_for_quest(
        quest_root=quest_root,
        controller_runners={"data_asset_gate": fake_runner},
        apply=True,
    )
    second = module.run_domain_health_diagnostic_for_quest(
        quest_root=quest_root,
        controller_runners={"data_asset_gate": fake_runner},
        apply=True,
    )

    assert first["controllers"]["data_asset_gate"]["action"] == "applied"
    assert second["controllers"]["data_asset_gate"]["action"] == "suppressed"
    assert calls == [False, True, False]
def test_applies_data_asset_gate_advisory_once(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        return {
            "status": "advisory",
            "blockers": [],
            "advisories": ["public_data_extension_available"],
            "study_id": quest_root.name,
            "public_support_dataset_ids": ["geo-gse000001"],
            "report_json": str(quest_root / "artifacts" / "reports" / "data_asset_gate" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "data_asset_gate" / "latest.md"),
            "intervention_enqueued": apply,
        }

    first = module.run_domain_health_diagnostic_for_quest(
        quest_root=quest_root,
        controller_runners={"data_asset_gate": fake_runner},
        apply=True,
    )
    second = module.run_domain_health_diagnostic_for_quest(
        quest_root=quest_root,
        controller_runners={"data_asset_gate": fake_runner},
        apply=True,
    )

    assert first["controllers"]["data_asset_gate"]["status"] == "advisory"
    assert first["controllers"]["data_asset_gate"]["action"] == "applied"
    assert second["controllers"]["data_asset_gate"]["action"] == "suppressed"
    assert calls == [False, True, False]
def test_reapplies_data_asset_gate_when_unresolved_dataset_ids_change(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []
    state = {"unresolved_dataset_ids": ["ds_a"]}

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        return {
            "status": "blocked",
            "blockers": ["unresolved_private_data_contract"],
            "advisories": [],
            "study_id": quest_root.name,
            "outdated_dataset_ids": [],
            "unresolved_dataset_ids": list(state["unresolved_dataset_ids"]),
            "public_support_dataset_ids": [],
            "report_json": str(quest_root / "artifacts" / "reports" / "data_asset_gate" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "data_asset_gate" / "latest.md"),
            "intervention_enqueued": apply,
        }

    first = module.run_domain_health_diagnostic_for_quest(
        quest_root=quest_root,
        controller_runners={"data_asset_gate": fake_runner},
        apply=True,
    )
    state["unresolved_dataset_ids"] = ["ds_b"]
    second = module.run_domain_health_diagnostic_for_quest(
        quest_root=quest_root,
        controller_runners={"data_asset_gate": fake_runner},
        apply=True,
    )

    assert first["controllers"]["data_asset_gate"]["action"] == "applied"
    assert second["controllers"]["data_asset_gate"]["action"] == "applied"
    assert calls == [False, True, False, True]
def test_domain_health_diagnostic_no_longer_exports_repo_local_loop() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")

    assert not hasattr(module, "run_watch_loop")
    assert not hasattr(module, "run_managed_supervisor_loop")


def test_domain_health_diagnostic_no_longer_exports_managed_supervisor_tick_alias() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")

    assert not hasattr(module, "run_managed_supervisor_tick")


def test_domain_health_diagnostic_cli_accepts_explicit_dry_run() -> None:
    cli = importlib.import_module("med_autoscience.cli")

    args = cli.build_parser().parse_args(
        [
            "domain-health-diagnostic",
            "--runtime-root",
            "/tmp/runtime/quests",
            "--dry-run",
        ]
    )

    assert args.command == "domain-health-diagnostic"
    assert args.apply is False
    assert args.dry_run is True


def test_domain_health_diagnostic_cli_rejects_apply_and_dry_run_together() -> None:
    cli = importlib.import_module("med_autoscience.cli")

    with pytest.raises(SystemExit):
        cli.build_parser().parse_args(
            [
                "domain-health-diagnostic",
                "--runtime-root",
                "/tmp/runtime/quests",
                "--apply",
                "--dry-run",
            ]
        )
