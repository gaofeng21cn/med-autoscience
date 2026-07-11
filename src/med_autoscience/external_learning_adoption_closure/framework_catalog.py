from __future__ import annotations

from typing import Any, Mapping


def framework_from_projection(
    *,
    framework_id: str,
    source_project: str,
    projection: Mapping[str, Any],
    closure_status: str,
    owner_surface: str,
    worker_or_executor_landing: str,
    missing_landing_work: list[str],
    next_landing_path: str,
    extra_source_refs: list[str | None] | None = None,
) -> dict[str, Any]:
    source = mapping(projection.get("source_snapshot"))
    return framework(
        framework_id=framework_id,
        source_project=source_project,
        source_refs=[
            text(source.get("repository")),
            text(source.get("intake_doc_ref")),
            text(projection.get("contract_ref")),
            text(projection.get("progress_accelerator_contract_ref")),
            *(extra_source_refs or []),
        ],
        absorbed_pattern_ids=(
            [text(item) for item in list_value(projection.get("absorbed_pattern_ids"))]
            or [
                text(pattern.get("pattern_id"))
                for pattern in list_value(projection.get("absorbed_patterns"))
                if isinstance(pattern, Mapping)
            ]
        ),
        local_execution_state=text(projection.get("status")) or closure_status,
        closure_status=closure_status,
        owner_surface=owner_surface,
        worker_or_executor_landing=worker_or_executor_landing,
        missing_landing_work=missing_landing_work,
        next_landing_path=next_landing_path,
    )


def framework(
    *,
    framework_id: str,
    source_project: str,
    source_refs: list[str | None],
    absorbed_pattern_ids: list[str | None],
    local_execution_state: str,
    closure_status: str,
    owner_surface: str,
    worker_or_executor_landing: str,
    missing_landing_work: list[str],
    next_landing_path: str,
) -> dict[str, Any]:
    return {
        "framework_id": framework_id,
        "source_project": source_project,
        "source_refs": [ref for ref in source_refs if ref],
        "dependency_introduced": False,
        "absorbed_pattern_ids": [item for item in absorbed_pattern_ids if item],
        "local_execution_state": local_execution_state,
        "closure_status": closure_status,
        "owner_surface": owner_surface,
        "worker_or_executor_landing": worker_or_executor_landing,
        "missing_landing_work": missing_landing_work,
        "next_landing_path": next_landing_path,
        "friction_policy": {
            "can_block_current_owner_action": False,
            "mainline_waits_for_framework": False,
            "external_runtime_dependency": False,
            "owner_policy_wins": True,
        },
        "authority_boundary": {
            "can_write_domain_truth": False,
            "can_write_publication_eval": False,
            "can_write_controller_decisions": False,
            "can_write_owner_receipt": False,
            "can_write_typed_blocker": False,
            "can_write_paper_or_package": False,
            "can_write_artifact_authority": False,
            "can_authorize_publication_quality": False,
            "can_authorize_submission_readiness": False,
            "can_authorize_artifact_authority": False,
            "can_close_stage": False,
        },
    }


def counts(frameworks: list[Mapping[str, Any]]) -> dict[str, int]:
    totals = {
        "framework_count": len(frameworks),
        "owner_surface_landed_count": 0,
        "sidecar_execution_slot_count": 0,
        "contract_or_projection_only_gap_count": 0,
        "not_landed_gap_count": 0,
    }
    for item in frameworks:
        status = text(item.get("closure_status"))
        if status in {
            "owner_surface_landed",
            "contract_projection_landed",
            "read_model_landed",
        }:
            totals["owner_surface_landed_count"] += 1
        if status in {"sidecar_execution_slot_landed", "sidecar_or_worker_landed"}:
            totals["sidecar_execution_slot_count"] += 1
        if status in {
            "projection_only_gap",
            "thin_projection_landed_worker_scaleout_gap",
            "contract_only_gap",
            "history_only_gap",
        }:
            totals["contract_or_projection_only_gap_count"] += 1
        if status == "not_landed_gap":
            totals["not_landed_gap_count"] += 1
    return totals


def mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def list_value(value: object) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def text(value: object) -> str | None:
    normalized = str(value or "").strip()
    return normalized or None
