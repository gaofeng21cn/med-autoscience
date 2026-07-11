from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src" / "med_autoscience"


def test_owner_callable_dispatch_residue_cleanup_surface_is_physically_retired() -> None:
    assert not (
        SRC_ROOT / "controllers" / "owner_callable_dispatch_residue_cleanup.py"
    ).exists()
    assert not (REPO_ROOT / "tests" / "test_owner_callable_dispatch_residue_cleanup.py").exists()

    assert not any((SRC_ROOT / "cli").rglob("*.py"))


def test_open_runtime_surfaces_cannot_use_active_callers_as_retention_reason() -> None:
    inventory_path = REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    open_surfaces = [
        surface
        for surface in inventory["surfaces"]
        if surface["disposition"] != "physically_retired"
    ]

    assert open_surfaces
    for surface in open_surfaces:
        assert surface["mas_runtime_authority"] is False
        assert surface["replacement_ref"].startswith("opl:")
        assert surface["retained_mas_role"] != "none"


def test_owner_callable_receipt_latest_reader_ignores_legacy_latest_wire(tmp_path) -> None:
    candidates = importlib.import_module(
        "med_autoscience.controllers.study_transition_receipt_consumption.owner_callable_candidates"
    )
    study_root = tmp_path / "studies" / "study-1"
    canonical_path = study_root / "artifacts" / "supervision" / "consumer" / "owner_callable_adapter_receipts" / "latest.json"
    legacy_path = study_root / "artifacts" / "supervision" / "consumer" / "owner_callable_adapter_receipt" / "latest.json"
    legacy_path.parent.mkdir(parents=True)
    legacy_path.write_text(
        json.dumps(
            {
                "surface": "owner_callable_dispatch_execution_study_latest",
                "executions": [
                    {
                        "surface": "owner_callable_dispatch_execution",
                        "execution_status": "blocked",
                        "action_type": "legacy_action",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    canonical_path.parent.mkdir(parents=True)
    canonical_path.write_text(
        json.dumps(
            {
                "surface": "owner_callable_adapter_receipt_study_latest",
                "executions": [
                    {
                        "surface": "owner_callable_adapter_receipt",
                        "execution_status": "blocked",
                        "action_type": "canonical_action",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    payload, receipt_ref = candidates.latest_owner_callable_receipt_payload(study_root=study_root)

    assert receipt_ref == "artifacts/supervision/consumer/owner_callable_adapter_receipts/latest.json"
    assert payload["executions"][0]["action_type"] == "canonical_action"
    assert payload["executions"][0]["canonical_surface"] == "owner_callable_adapter_receipt"
    assert payload["projection_authority"] is False
    assert payload["queue_authority"] is False

    canonical_path.unlink()
    payload, receipt_ref = candidates.latest_owner_callable_receipt_payload(study_root=study_root)

    assert payload is None
    assert receipt_ref == "artifacts/supervision/consumer/owner_callable_adapter_receipts/latest.json"
    assert candidates.owner_callable_receipt_candidates(study_root=study_root) == []


def test_domain_owner_dispatch_execution_latest_payload_ignores_legacy_opt_in(
    tmp_path,
) -> None:
    execution_io = importlib.import_module(
        "med_autoscience.controllers.stage_outcome_authority.execution_io"
    )
    profiles = importlib.import_module("med_autoscience.profiles")
    profile = profiles.WorkspaceProfile(
        name="test",
        workspace_root=tmp_path,
        runtime_root=tmp_path / "runtime",
        studies_root=tmp_path / "studies",
        portfolio_root=tmp_path / "portfolio",
        med_deepscientist_runtime_root=tmp_path / "legacy-runtime",
        med_deepscientist_repo_root=None,
        default_publication_profile="default",
        default_citation_style="vancouver",
        research_route_bias_policy="none",
        preferred_study_archetypes=(),
        default_submission_targets=(),
    )
    legacy_path = (
        profile.studies_root
        / "study-1"
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapter_receipt"
        / "latest.json"
    )
    legacy_path.parent.mkdir(parents=True)
    legacy_path.write_text(
        json.dumps(
            {
                "surface": "owner_callable_dispatch_execution_study_latest",
                "executions": [
                    {
                        "surface": "owner_callable_dispatch_execution",
                        "execution_status": "blocked",
                        "action_type": "legacy_action",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    assert execution_io.execution_latest_payload(profile, "study-1") is None

    assert execution_io.execution_latest_payload(
        profile,
        "study-1",
        allow_legacy_fallback=True,
    ) is None
