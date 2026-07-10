from __future__ import annotations

import builtins
import importlib
from pathlib import Path
import sys

from tests.study_progress_cases.shared_base import _write_json


def test_study_progress_import_does_not_require_submission_pdf_dependency(monkeypatch) -> None:
    for module_name in list(sys.modules):
        if module_name in {
            "med_autoscience.controllers.study_progress",
            "med_autoscience.controllers.study_progress.projection",
            "med_autoscience.controllers.gate_clearing_batch",
            "med_autoscience.controllers.publication_gate",
            "med_autoscience.controllers.submission_minimal",
            "pypdf",
        }:
            sys.modules.pop(module_name, None)

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "pypdf" or name.startswith("pypdf."):
            raise ModuleNotFoundError("No module named 'pypdf'")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    module = importlib.import_module("med_autoscience.controllers.study_progress.projection")

    assert callable(module.read_study_progress)


def test_publishability_gate_report_path_prefers_fresher_latest_gate_over_runtime_readback_pointer(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress.projection")
    quest_root = tmp_path / "runtime" / "quests" / "quest-001"
    gate_root = quest_root / "artifacts" / "reports" / "publishability_gate"
    stale_gate_path = gate_root / "2026-04-24T024953Z.json"
    latest_gate_path = gate_root / "latest.json"

    _write_json(
        stale_gate_path,
        {
            "schema_version": 1,
            "generated_at": "2026-04-24T02:49:53+00:00",
            "status": "blocked",
        },
    )
    _write_json(
        latest_gate_path,
        {
            "schema_version": 1,
            "generated_at": "2026-04-24T04:07:59+00:00",
            "status": "clear",
        },
    )

    result = module._publishability_gate_report_path(
        runtime_readback_payload={
            "controllers": {
                "publication_gate": {
                    "report_json": str(stale_gate_path),
                }
            }
        },
        quest_root=quest_root,
    )

    assert result == latest_gate_path.resolve()
