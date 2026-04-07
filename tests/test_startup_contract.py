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
