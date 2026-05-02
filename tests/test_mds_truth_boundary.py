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
    assert manifest["allowed_runtime_health_event_types"] == [
        "runtime_state_observed",
        "daemon_probe",
        "worker_heartbeat",
        "session_probe",
        "runtime_event_observed",
    ]
    assert manifest["forbidden_authority_surfaces"] == [
        "canonical_next_action",
        "publication_gate_state",
        "package_state",
        "delivery_state",
    ]
    assert manifest["forbidden_runtime_health_surfaces"] == [
        "runtime_health_epoch",
        "canonical_runtime_action",
        "worker_liveness_state",
        "allowed_controller_actions",
    ]
    assert manifest["parity_deconstruction_summary"]["surface"] == "mds_capability_parity_deconstruction_summary"
    assert manifest["parity_deconstruction_summary"]["mds_role"] == "replaceable_backend_oracle"
    assert manifest["parity_deconstruction_summary"]["mds_quality_authority"] == "none"
    assert manifest["parity_deconstruction_summary"]["quality_owner"] == "MedAutoScience"
    assert manifest["parity_deconstruction_summary"]["medical_quality_authority_owner"] == "MedAutoScience"
    assert manifest["parity_deconstruction_summary"]["medical_quality_authority_granted_to_mds"] is False
