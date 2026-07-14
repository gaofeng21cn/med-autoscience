from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta
ROOT = Path(__file__).resolve().parents[1]


def test_package_import_and_authority_handler_entrypoint() -> None:
    package = importlib.import_module("med_autoscience")
    handlers = importlib.import_module("med_autoscience.authority_handlers")

    assert package.__version__ == "0.2.3"
    assert callable(handlers.evaluate_paper_mission_authority)


def test_direct_and_hosted_entry_sources_resolve() -> None:
    catalog = json.loads(
        (ROOT / "contracts/action_catalog.json").read_text(encoding="utf-8")
    )
    assert (ROOT / "agent/primary_skill/SKILL.md").is_file()
    assert len(catalog["actions"]) == 7
    for action in catalog["actions"]:
        binding = action["execution_binding"]
        if binding["kind"] == "stage_binding":
            assert (ROOT / binding["stage_manifest_ref"]).is_file()
