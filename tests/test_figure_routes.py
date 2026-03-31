from __future__ import annotations

import importlib

import pytest


def test_build_figure_route_normalizes_prefix_and_figure_id() -> None:
    module = importlib.import_module("med_autoscience.figure_routes")

    route = module.build_figure_route(module.FIGURE_ROUTE_SCRIPT_FIX, "f3c")

    assert route == "figure_script_fix:F3C"


def test_normalize_required_route_passes_through_mainline_route() -> None:
    module = importlib.import_module("med_autoscience.figure_routes")

    assert module.normalize_required_route("literature_scout") == "literature_scout"


def test_normalize_required_route_rejects_ambiguous_sidecar_prefix() -> None:
    module = importlib.import_module("med_autoscience.figure_routes")

    with pytest.raises(ValueError, match="Ambiguous figure sidecar route"):
        module.normalize_required_route("sidecar:F3C")


def test_normalize_required_route_rejects_bare_figure_route_prefix() -> None:
    module = importlib.import_module("med_autoscience.figure_routes")

    with pytest.raises(ValueError, match="must include <figure-id>"):
        module.normalize_required_route(module.FIGURE_ROUTE_SCRIPT_FIX)


def test_supported_required_route_help_mentions_explicit_prefixes() -> None:
    module = importlib.import_module("med_autoscience.figure_routes")

    text = module.supported_required_route_help()

    assert "figure_script_fix:<figure-id>" in text
    assert "figure_illustration_program:<figure-id>" in text


def test_normalize_required_route_rejects_removed_autofigure_route() -> None:
    module = importlib.import_module("med_autoscience.figure_routes")

    with pytest.raises(ValueError, match="Unsupported figure route prefix"):
        module.normalize_required_route("figure_illustration_autofigure:F3C")
