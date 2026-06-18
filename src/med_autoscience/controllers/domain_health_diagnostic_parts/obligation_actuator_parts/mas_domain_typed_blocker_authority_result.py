from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


SURFACE_KIND = "mas_domain_typed_blocker_authority_result_adapter"
AUTHORITY_RESULT_SURFACE = "mas_domain_typed_blocker"
AUTHORITY_OWNER = "med-autoscience"


def persist_obligation_typed_blocker(
    *,
    study_root: Path,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    blocker = dict(payload)
    if blocker.get("surface_kind") != AUTHORITY_RESULT_SURFACE:
        raise ValueError("obligation typed blocker adapter only persists mas_domain_typed_blocker")
    blocker_path = obligation_typed_blocker_latest_path(study_root=study_root)
    history_path = blocker_path.parent / "history.jsonl"
    boundary = authority_result_adapter_boundary()
    blocker["authority_result_adapter"] = SURFACE_KIND
    blocker["authority_owner"] = AUTHORITY_OWNER
    blocker["actuator_private_write_authority"] = False
    blocker["typed_blocker_ref"] = str(blocker_path)
    blocker["authority_result_ref"] = str(blocker_path)
    blocker["authority_result_surface"] = AUTHORITY_RESULT_SURFACE
    blocker["authority_result_boundary"] = boundary
    blocker_path.parent.mkdir(parents=True, exist_ok=True)
    blocker_path.write_text(
        json.dumps(blocker, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with history_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(blocker, ensure_ascii=False, sort_keys=True) + "\n")
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": 1,
        "status": "persisted",
        "authority_owner": AUTHORITY_OWNER,
        "authority_result_surface": AUTHORITY_RESULT_SURFACE,
        "typed_blocker_ref": str(blocker_path),
        "history_ref": str(history_path),
        "payload": blocker,
        "authority_boundary": boundary,
    }


def obligation_typed_blocker_latest_path(*, study_root: Path) -> Path:
    return (
        Path(study_root)
        / "artifacts"
        / "mas_authority"
        / "typed_blockers"
        / "domain_health_diagnostic_obligation"
        / "latest.json"
    )


def authority_result_adapter_boundary() -> dict[str, Any]:
    return {
        "surface_kind": "mas_domain_typed_blocker_authority_result_boundary",
        "authority_owner": AUTHORITY_OWNER,
        "authority_result_surface": AUTHORITY_RESULT_SURFACE,
        "adapter_role": "persist_mas_domain_typed_blocker_authority_result",
        "actuator_private_write_authority": False,
        "can_create_opl_command": False,
        "can_create_opl_event": False,
        "can_create_opl_outbox": False,
        "can_create_opl_stage_run": False,
        "can_store_recovery_obligation": False,
        "can_run_supervisor_decision_engine": False,
        "can_authorize_provider_admission": False,
        "can_claim_paper_progress": False,
        "can_write_publication_eval": False,
        "can_write_controller_decision": False,
    }


__all__ = [
    "AUTHORITY_OWNER",
    "AUTHORITY_RESULT_SURFACE",
    "SURFACE_KIND",
    "authority_result_adapter_boundary",
    "obligation_typed_blocker_latest_path",
    "persist_obligation_typed_blocker",
]
