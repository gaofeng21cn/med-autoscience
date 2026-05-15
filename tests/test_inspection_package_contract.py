from __future__ import annotations

from pathlib import Path

import pytest


pytestmark = pytest.mark.contract

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_DOCS = (
    REPO_ROOT / "docs/runtime/contracts/delivery_plane_contract_map.md",
    REPO_ROOT / "docs/runtime/control/controllers.md",
    REPO_ROOT / "docs/product/inspection_package.md",
    REPO_ROOT / "docs/delivery/inspection_package.md",
)
FORBIDDEN_SURFACE_TOKENS = (
    "paper/submission_minimal",
    "manuscript/current_package",
    "current_package.zip",
    "artifacts/publication_eval/latest.json",
    "artifacts/controller_decisions/latest.json",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_inspection_package_contract_documents_human_inspection_only_authority() -> None:
    combined = "\n".join(_read(path) for path in CONTRACT_DOCS)

    assert "inspection_package" in combined
    assert "human_inspection_only" in combined
    assert "not_for_submission" in combined
    assert "gate_blocked_snapshot" in combined
    assert "can_authorize_submission = false" in combined
    assert "can_authorize_publication_quality = false" in combined
    assert "can_clear_publishability_gate = false" in combined
    assert "can_dispatch_delivery_sync = false" in combined
    for token in FORBIDDEN_SURFACE_TOKENS:
        assert token in combined


def test_inspection_package_contract_keeps_formal_delivery_and_quality_writes_forbidden() -> None:
    delivery_contract = _read(REPO_ROOT / "docs/delivery/inspection_package.md")

    assert "允许写入" in delivery_contract
    assert "study_root/manuscript/inspection_package/" in delivery_contract
    assert "study_root/artifacts/inspection_package/manifest.json" in delivery_contract
    assert "Forbidden writes" in delivery_contract
    assert "submission_minimal" in delivery_contract
    assert "study_delivery_sync" in delivery_contract
    assert "AI reviewer eval materializer" in delivery_contract
    assert "outer-loop decision writer" in delivery_contract
    assert "不生成 `current_package` freshness proof" in delivery_contract


def test_delivery_inspection_projection_remains_observability_only_for_inspection_package_path() -> None:
    from med_autoscience.controllers.delivery_visibility_projection import (
        compact_delivery_inspection_projection,
    )

    projection = compact_delivery_inspection_projection(
        {
            "surface": "delivery_inspector",
            "schema_version": 1,
            "study_id": "001-risk",
            "freshness": {"verdict": "stale", "delivery_status": "stale_source_changed"},
            "mutation_policy": {"read_only": True, "writes_package": False},
            "source_package": {
                "role": "controller_authorized_source",
                "root": "/workspace/studies/001-risk/paper/submission_minimal",
                "exists": True,
                "layout_status": "v2",
            },
            "human_package": {
                "role": "human_facing_mirror",
                "root": "/workspace/studies/001-risk/manuscript/current_package",
                "exists": True,
                "layout_status": "v2",
            },
            "next_sync_command": "medautosci study delivery-sync --paper-root /workspace/studies/001-risk/paper",
        }
    )

    assert projection is not None
    assert projection["authority"] == "observability_projection_only"
    assert projection["projection_only"] is True
    assert projection["can_authorize_submission"] is False
    assert projection["can_authorize_publication_quality"] is False
    assert projection["can_dispatch_delivery_sync"] is False
    assert projection["status"] == "stale"


def test_inspection_package_plan_distinguishes_allowed_outputs_from_submission_outputs() -> None:
    allowed_outputs = {
        "manuscript/inspection_package",
        "manuscript/inspection_package.zip",
        "artifacts/inspection_package/manifest.json",
        "artifacts/inspection_package/source_inventory.json",
        "artifacts/inspection_package/export_receipt.json",
    }
    forbidden_outputs = {
        "paper/submission_minimal",
        "manuscript/current_package",
        "manuscript/current_package.zip",
        "artifacts/publication_eval/latest.json",
        "artifacts/controller_decisions/latest.json",
    }
    export_plan = {
        "surface_kind": "inspection_package",
        "authority": "human_inspection_only",
        "gate_blocked_snapshot": True,
        "not_for_submission": True,
        "allowed_outputs": sorted(allowed_outputs),
        "forbidden_writes": sorted(forbidden_outputs),
        "can_authorize_submission": False,
        "can_authorize_publication_quality": False,
        "can_clear_publishability_gate": False,
        "can_dispatch_delivery_sync": False,
    }

    assert export_plan["surface_kind"] == "inspection_package"
    assert export_plan["allowed_outputs"] == sorted(allowed_outputs)
    assert not set(export_plan["allowed_outputs"]) & set(export_plan["forbidden_writes"])
    assert "manuscript/current_package" in export_plan["forbidden_writes"]
    assert "artifacts/publication_eval/latest.json" in export_plan["forbidden_writes"]
    assert export_plan["can_authorize_submission"] is False
    assert export_plan["can_authorize_publication_quality"] is False
    assert export_plan["can_clear_publishability_gate"] is False
    assert export_plan["can_dispatch_delivery_sync"] is False
