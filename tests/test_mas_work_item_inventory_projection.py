from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PORTFOLIO_ROOT = Path.home() / "workspace" / "Yang"
PORTFOLIO_WORKSPACES = {
    "DM-CVD-Mortality-Risk": {
        "001-dm-cvd-mortality-risk",
        "002-dm-china-us-mortality-attribution",
        "003-dpcc-primary-care-phenotype-treatment-gap",
        "004-dpcc-longitudinal-care-inertia-intensification-gap",
    },
    "NF-PitNET": {
        "001-lineage-pfs",
        "002-early-residual-risk",
        "003-endocrine-burden-followup",
        "004-invasive-architecture",
    },
    "Obesity": {"obesity_multicenter_phenotype_atlas"},
}


def _domain_descriptor() -> dict[str, Any]:
    return json.loads(
        (REPO_ROOT / "contracts" / "domain_descriptor.json").read_text(encoding="utf-8")
    )


def _inventory_projection() -> dict[str, Any]:
    return _domain_descriptor()["standard_agent_interface"]["inventory_projection"]


def _resolve_pointer(payload: Any, pointer: str) -> Any:
    current = payload
    for token in pointer.lstrip("/").split("/"):
        if not token:
            continue
        current = current[token.replace("~1", "/").replace("~0", "~")]
    return current


def _project_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    projection = _inventory_projection()
    items = _resolve_pointer(payload, projection["items_pointer"])
    projected: list[dict[str, Any]] = []
    for item in items:
        row = {
            target: item[source] for target, source in projection["field_map"].items()
        }
        projected.append(row)
    return projected


def test_inventory_projection_preserves_domain_owned_business_values() -> None:
    descriptor = _domain_descriptor()
    projection = _inventory_projection()
    source = {
        "studies": [
            {
                "study_id": "study-001",
                "canonical_study_root": "studies/study-001",
                "status": "domain_status_value",
                "current_stage_id": "stage-02",
                "current_stage_status": "domain_stage_status_value",
                "package_status": "domain_package_status_value",
                "study_status_ref": "STUDY_STATUS.md",
                "stage_index_ref": "control/stage_index.json",
            }
        ]
    }

    assert _project_items(source) == [
        {
            "work_item_id": "study-001",
            "work_item_root": "studies/study-001",
            "business_status": "domain_status_value",
            "current_stage_id": "stage-02",
            "current_stage_status": "domain_stage_status_value",
            "package_status": "domain_package_status_value",
            "lifecycle_ref": "STUDY_STATUS.md",
        }
    ]
    assert descriptor["authority_boundary"]["domain_truth_owner"] == "MedAutoScience"
    assert descriptor["authority_boundary"]["opl_can_write_domain_truth"] is False
    assert {"execution_state", "telemetry", "token_usage"}.isdisjoint(
        projection["field_map"]
    )


def test_current_local_portfolio_indexes_project_all_nine_studies() -> None:
    portfolio_root = Path(
        os.environ.get("MAS_RUNTIME_V2_PORTFOLIO_ROOT", str(DEFAULT_PORTFOLIO_ROOT))
    ).expanduser()
    projection = _inventory_projection()
    index_paths = {
        name: portfolio_root / name / projection["relative_path"]
        for name in PORTFOLIO_WORKSPACES
    }
    missing = [str(path) for path in index_paths.values() if not path.is_file()]
    if missing:
        pytest.skip(f"local MAS portfolio indexes are unavailable: {missing}")

    observed_ids: dict[str, set[str]] = {}
    for workspace_name, expected_ids in PORTFOLIO_WORKSPACES.items():
        payload = json.loads(index_paths[workspace_name].read_text(encoding="utf-8"))
        source_items = _resolve_pointer(payload, projection["items_pointer"])
        projected_items = _project_items(payload)

        assert len(source_items) == len(projected_items)
        for source, projected in zip(source_items, projected_items, strict=True):
            assert projected["work_item_id"] == source["study_id"]
            assert projected["work_item_root"] == source["canonical_study_root"]
            assert projected["business_status"] == source["status"]
            assert projected["current_stage_id"] == source["current_stage_id"]
            assert projected["current_stage_status"] == source["current_stage_status"]
            assert projected["package_status"] == source["package_status"]
            assert projected["lifecycle_ref"] == source["study_status_ref"]
            assert source["stage_index_ref"] == "control/stage_index.json"

        observed_ids[workspace_name] = {
            item["work_item_id"] for item in projected_items
        }
        assert expected_ids <= observed_ids[workspace_name]

    assert sum(len(study_ids) for study_ids in PORTFOLIO_WORKSPACES.values()) == 9
