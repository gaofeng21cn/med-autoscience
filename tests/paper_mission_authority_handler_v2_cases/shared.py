from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from med_autoscience.authority_handlers.paper_mission import (
    evaluate_paper_mission_authority,
)
from med_autoscience.authority_handlers._generation_manifest import (
    build_generation_manifest_v2,
    build_review_scopes,
    normalize_generation_manifest,
)


ROOT = Path(__file__).resolve().parents[2]


def _evaluate(request: dict[str, Any]) -> dict[str, Any]:
    return evaluate_paper_mission_authority(request)


def _assert_progress_debt(
    result: dict[str, Any],
    reason_code: str,
) -> dict[str, Any]:
    assert result["status"] == "completed_with_quality_debt"
    assert result["stage_outcome"]["stage_transition_allowed"] is True
    assert result["typed_blocker"] is None
    assert reason_code in result["quality_debt"]["reason_codes"]
    assert result["owner_receipt"] is None
    return result["route_back"]


def _assert_finalize_route_back(
    result: dict[str, Any], reason_code: str
) -> dict[str, Any]:
    assert result["status"] == "route_back"
    assert result["stage_outcome"]["stage_transition_allowed"] is False
    assert result["route_back"]["reason_code"] == reason_code
    return result["route_back"]


def _output_validator() -> Draft202012Validator:
    schema = json.loads(
        (
            ROOT / "contracts/schemas/v2/mas-paper-mission-authority.output.schema.json"
        ).read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _schema_validator(filename: str) -> Draft202012Validator:
    schema_dir = ROOT / "contracts/schemas/v2"
    schemas = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in schema_dir.glob("mas-*.schema.json")
    ]
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas
    )
    schema = next(item for item in schemas if item["$id"].endswith(f"/{filename}"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, registry=registry)


def _authorize_reused_lane(
    current: dict[str, Any],
    origin: dict[str, Any],
    lane: str,
    authority_records: Any,
    *,
    invalidating_changes: list[dict[str, Any]] | None = None,
    ignored_changes: list[dict[str, Any]] | None = None,
) -> None:
    origin_wrapper = next(
        item
        for item in origin["generation_manifest"]["independent_review_receipts"]
        if item["receipt"]["review_lane"] == lane
    )
    current["generation_manifest"]["independent_review_receipts"] = [
        deepcopy(origin_wrapper) if item["receipt"]["review_lane"] == lane else item
        for item in current["generation_manifest"]["independent_review_receipts"]
    ]
    lane_state = next(
        item
        for item in current["review_authority"]["currentness_receipt"][
            "lane_currentness"
        ]
        if item["review_lane"] == lane
    )
    receipt = origin_wrapper["receipt"]
    lane_state.update(
        {
            "review_authority_epoch": receipt["authority_epoch"],
            "currentness_status": "reused_unchanged_scope",
            "review_scope_sha256": next(
                item["review_scope_sha256"]
                for item in current["generation_manifest"]["review_scopes"]
                if item["review_lane"] == lane
            ),
            "review_receipt_issued_generation_id": receipt["issued_generation_id"],
            "review_receipt_issued_generation_manifest_sha256": receipt[
                "issued_generation_manifest_sha256"
            ],
            "current_review_request_ref": deepcopy(receipt["review_request_ref"]),
            "current_review_receipt_ref": deepcopy(origin_wrapper["receipt_ref"]),
            "reuse_provenance": {
                "origin_generation_id": origin["generation_manifest"]["generation_id"],
                "origin_generation_manifest_ref": deepcopy(
                    origin["generation_manifest_ref"]
                ),
                "origin_review_request_ref": deepcopy(receipt["review_request_ref"]),
                "origin_review_receipt_ref": deepcopy(origin_wrapper["receipt_ref"]),
                "origin_review_scope_sha256": receipt["review_scope_sha256"],
                "origin_candidate_admission_receipt_refs": deepcopy(
                    receipt["accepted_candidate_receipt_refs"]
                ),
            },
            "epistemic_currentness": authority_records.epistemic_currentness(
                current["generation_manifest"],
                lane,
                invalidating_changes=invalidating_changes,
                ignored_changes=ignored_changes,
            ),
        }
    )
    authority_records.reseal_review_currentness(current)


def _epistemic_change(
    authority_records: Any,
    *,
    node_ref: str,
    change_class: str,
    semantic_changed: bool = True,
    before: str = "before",
    after: str = "after",
    reason: str | None = None,
) -> dict[str, Any]:
    change = {
        "node_ref": node_ref,
        "change_class": change_class,
        "semantic_changed": semantic_changed,
        "locator_sha256_before": authority_records.digest(before),
        "locator_sha256_after": authority_records.digest(after),
    }
    if reason is not None:
        change["reason"] = reason
    return change



__all__ = [name for name in globals() if not name.startswith("__")]
