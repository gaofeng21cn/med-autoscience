from __future__ import annotations

import importlib

import pytest


def test_controller_owned_startup_contract_extensions_rejects_unclassified_keys() -> None:
    ownership = importlib.import_module("med_autoscience.startup_contract")

    with pytest.raises(ValueError, match="unclassified startup contract keys: unexpected_field"):
        ownership.controller_owned_startup_contract_extensions(
            {
                "schema_version": 4,
                "scope": "full_research",
                "unexpected_field": "should-fail",
            }
        )


def test_compose_startup_contract_rejects_unclassified_controller_extension_keys() -> None:
    ownership = importlib.import_module("med_autoscience.startup_contract")

    with pytest.raises(ValueError, match="unclassified controller-owned startup contract keys: unexpected_field"):
        ownership.compose_startup_contract(
            runtime_owned={"launch_mode": "custom"},
            controller_extensions={"scope": "full_research", "unexpected_field": "should-fail"},
        )


def test_controller_owned_startup_contract_extensions_preserve_controller_summary_ref() -> None:
    ownership = importlib.import_module("med_autoscience.startup_contract")
    startup_contract = {
        "schema_version": 4,
        "launch_mode": "custom",
        "scope": "full_research",
        "study_charter_ref": {
            "charter_id": "charter::001-risk::v1",
            "artifact_path": "/tmp/workspace/studies/001-risk/artifacts/controller/study_charter.json",
        },
        "controller_summary_ref": {
            "summary_id": "controller-summary::001-risk::v1",
            "artifact_path": "/tmp/workspace/studies/001-risk/artifacts/controller/controller_summary.json",
        },
    }

    controller_extensions = ownership.controller_owned_startup_contract_extensions(startup_contract)

    assert controller_extensions["scope"] == "full_research"
    assert controller_extensions["study_charter_ref"] == startup_contract["study_charter_ref"]
    assert controller_extensions["controller_summary_ref"] == startup_contract["controller_summary_ref"]
