from __future__ import annotations

import importlib


def test_registry_exposes_aris_only_for_supported_sidecar_providers() -> None:
    module = importlib.import_module("med_autoscience.sidecars.registry")

    aris = module.get_provider("aris")

    assert aris.provider_id == "aris"
    assert aris.domain_id == "algorithm_research"
    assert aris.instance_key_name is None


def test_get_provider_rejects_unknown_provider() -> None:
    module = importlib.import_module("med_autoscience.sidecars.registry")

    try:
        module.get_provider("unknown")
    except ValueError as exc:
        assert "Unknown sidecar provider" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown sidecar provider")


def test_get_provider_rejects_removed_autofigure_provider() -> None:
    module = importlib.import_module("med_autoscience.sidecars.registry")

    try:
        module.get_provider("autofigure_edit")
    except ValueError as exc:
        assert "Unknown sidecar provider" in str(exc)
    else:
        raise AssertionError("Expected ValueError for removed autofigure_edit provider")
