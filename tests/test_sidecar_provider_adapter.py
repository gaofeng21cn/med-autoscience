from __future__ import annotations

import importlib


def test_generic_sidecar_layout_supports_singleton_and_instance_providers(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.adapters.sidecar_provider")
    quest_root = tmp_path / "runtime" / "quests" / "q001"

    assert module.sidecar_root(quest_root, provider_id="aris") == quest_root / "sidecars" / "aris"
    assert module.handoff_root(quest_root, provider_id="aris") == quest_root / "sidecars" / "aris" / "handoff"
    assert module.artifact_root(
        quest_root,
        domain_id="algorithm_research",
        provider_id="aris",
    ) == quest_root / "artifacts" / "algorithm_research" / "aris"

    assert module.sidecar_root(quest_root, provider_id="autofigure_edit", instance_id="F3C") == (
        quest_root / "sidecars" / "autofigure_edit" / "F3C"
    )
    assert module.handoff_root(quest_root, provider_id="autofigure_edit", instance_id="F3C") == (
        quest_root / "sidecars" / "autofigure_edit" / "F3C" / "handoff"
    )
    assert module.artifact_root(
        quest_root,
        domain_id="figures",
        provider_id="autofigure_edit",
        instance_id="F3C",
    ) == quest_root / "artifacts" / "figures" / "autofigure_edit" / "F3C"


def test_generic_sidecar_layout_rejects_unsafe_instance_id(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.adapters.sidecar_provider")
    quest_root = tmp_path / "runtime" / "quests" / "q001"

    try:
        module.sidecar_root(quest_root, provider_id="autofigure_edit", instance_id="../bad")
    except ValueError as exc:
        assert "unsafe sidecar instance_id" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unsafe instance id")
