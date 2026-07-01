from __future__ import annotations

import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.test_publication_eval_latest import _minimal_payload


def test_ai_reviewer_publication_eval_controller_rejects_mechanical_projection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    controller = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    payload = _minimal_payload(study_root)
    payload["assessment_provenance"] = {
        "owner": "mechanical_projection",
        "source_kind": "publication_gate_report",
        "policy_id": "publication_gate_projection_v1",
        "source_refs": [payload["runtime_context_refs"]["runtime_escalation_ref"]],
        "ai_reviewer_required": True,
    }

    monkeypatch.setattr(
        controller.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
        },
    )

    with pytest.raises(ValueError, match="owner=ai_reviewer"):
        controller.materialize_ai_reviewer_publication_eval(
            profile=SimpleNamespace(name="nfpitnet"),
            study_id=None,
            study_root=study_root,
            entry_mode=None,
            record=payload,
            source="pytest",
        )
