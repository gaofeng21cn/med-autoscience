from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any


SURFACE_KIND = "mas_live_runtime_evidence_rollup_redirect"
VERSION = "mas-live-runtime-evidence-rollup-redirect.v2"
CONTRACT_PATH = Path("contracts/runtime/mas-live-runtime-evidence-rollup.json")
REPLACEMENT_REF = "opl:runtime-evidence-readback"


def live_runtime_evidence_rollup_readback(
    *,
    repo_root: Path,
    live_tail_evidence_records: list[Mapping[str, Any]] | None = None,
    live_runtime_gap_evidence_records: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    contract = _load_contract(Path(repo_root).resolve() / CONTRACT_PATH)
    supplied_count = len(live_tail_evidence_records or []) + len(
        live_runtime_gap_evidence_records or []
    )
    return {
        "surface_kind": SURFACE_KIND,
        "version": VERSION,
        "status": "redirect_to_opl_runtime_evidence_readback",
        "contract_ref": str(CONTRACT_PATH),
        "contract_validation": {
            "status": "passed" if _valid_contract(contract) else "failed"
        },
        "replacement_ref": REPLACEMENT_REF,
        "mas_live_work_order_generation": "retired",
        "mas_live_evidence_intake": "retired",
        "supplied_record_count": supplied_count,
        "supplied_records_consumed": False,
        "completion_claim_allowed": False,
        "live_runtime_readiness_claim_allowed": False,
        "physical_delete_allowed": False,
        "next_owner": "one-person-lab",
    }


def evidence_records_from_bundle(
    bundle: Mapping[str, Any],
) -> tuple[list[Mapping[str, Any]], list[Mapping[str, Any]]]:
    if not isinstance(bundle, Mapping):
        raise TypeError("live runtime evidence bundle must be a JSON object")
    tail_records = bundle.get("live_tail_evidence_records", [])
    gap_records = bundle.get("live_runtime_gap_evidence_records", [])
    if not isinstance(tail_records, list):
        raise TypeError("live_tail_evidence_records must be a JSON list")
    if not isinstance(gap_records, list):
        raise TypeError("live_runtime_gap_evidence_records must be a JSON list")
    return tail_records, gap_records


def _load_contract(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, Mapping) else {}


def _valid_contract(contract: Mapping[str, Any]) -> bool:
    return (
        contract.get("surface_kind") == SURFACE_KIND
        and contract.get("version") == VERSION
        and contract.get("replacement_ref") == REPLACEMENT_REF
        and contract.get("completion_claim_allowed") is False
    )


__all__ = [
    "evidence_records_from_bundle",
    "live_runtime_evidence_rollup_readback",
]
