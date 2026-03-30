from __future__ import annotations

import importlib


def test_registry_exposes_aris_and_autofigure_edit() -> None:
    module = importlib.import_module("med_autoscience.sidecars.registry")

    aris = module.get_provider("aris")
    figure = module.get_provider("autofigure_edit")

    assert aris.provider_id == "aris"
    assert aris.domain_id == "algorithm_research"
    assert aris.instance_key_name is None

    assert figure.provider_id == "autofigure_edit"
    assert figure.domain_id == "figures"
    assert figure.instance_key_name == "figure_id"
    assert "figure_catalog_entry.json" in figure.required_handoff_files


def test_get_provider_rejects_unknown_provider() -> None:
    module = importlib.import_module("med_autoscience.sidecars.registry")

    try:
        module.get_provider("unknown")
    except ValueError as exc:
        assert "Unknown sidecar provider" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown sidecar provider")
