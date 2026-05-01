from __future__ import annotations

import importlib
import json
from pathlib import Path


def test_mds_manifest_is_event_source_not_hidden_authority(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.med_deepscientist_repo_manifest")
    repo_root = tmp_path / "med-deepscientist"
    repo_root.mkdir()
    (repo_root / "MEDICAL_FORK_MANIFEST.json").write_text(
        json.dumps(
            {
                "engine_id": "med-deepscientist",
                "engine_family": "MedDeepScientist",
                "is_controlled_fork": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = module.inspect_med_deepscientist_repo_manifest(repo_root)

    assert manifest["truth_authority_role"] == "event_source_only"
    assert manifest["allowed_truth_event_types"] == [
        "runtime_native_event",
        "runtime_supervision_tick",
        "quality_review_eval",
    ]
    assert manifest["forbidden_authority_surfaces"] == [
        "canonical_next_action",
        "publication_gate_state",
        "package_state",
        "delivery_state",
    ]
