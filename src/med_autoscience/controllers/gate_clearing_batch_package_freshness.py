from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable


STABLE_CURRENT_PACKAGE_FRESHNESS_RELATIVE_PATH = Path("artifacts/controller/current_package_freshness/latest.json")
_BLOCKING_SYNC_STATUSES = frozenset(
    {
        "control_plane_route_blocked",
        "failed",
        "missing",
        "skipped_failed_dependency",
        "skipped_authority_not_settled",
    }
)


def stable_current_package_freshness_path(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / STABLE_CURRENT_PACKAGE_FRESHNESS_RELATIVE_PATH


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _first_non_empty_text(*values: object) -> str | None:
    for value in values:
        text = _non_empty_text(value)
        if text is not None:
            return text
    return None


def build_current_package_freshness_proof(
    *,
    study_root: Path,
    source_eval_id: str,
    gate_report: dict[str, Any] | None = None,
    unit_results: list[dict[str, Any]],
    clock: Callable[[], tuple[int, str]],
    schema_version: int,
) -> dict[str, Any] | None:
    gate_report = gate_report or {}
    for item in unit_results:
        if _non_empty_text(item.get("unit_id")) != "sync_submission_minimal_delivery":
            continue
        status = _non_empty_text(item.get("status"))
        if status in _BLOCKING_SYNC_STATUSES:
            continue
        result = item.get("result") if isinstance(item.get("result"), dict) else {}
        _started_ns, recorded_at = clock()
        return {
            "schema_version": schema_version,
            "status": "fresh",
            "source_eval_id": source_eval_id,
            "source_unit_id": "sync_submission_minimal_delivery",
            "recorded_at": recorded_at,
            "unit_status": status,
            "submission_manifest_path": _first_non_empty_text(
                (result or {}).get("submission_manifest_path"),
                gate_report.get("submission_minimal_manifest_path"),
            ),
            "delivery_manifest_path": _first_non_empty_text(
                (result or {}).get("delivery_manifest_path"),
                gate_report.get("study_delivery_manifest_path"),
            ),
            "current_package_root": _first_non_empty_text(
                (result or {}).get("current_package_root"),
                item.get("current_package_root"),
                gate_report.get("study_delivery_current_package_root"),
            ),
            "current_package_zip": _first_non_empty_text(
                (result or {}).get("current_package_zip"),
                item.get("current_package_zip"),
                gate_report.get("study_delivery_current_package_zip"),
            ),
            "source_signature": _first_non_empty_text(
                (result or {}).get("source_signature"),
                (result or {}).get("evaluated_source_signature"),
                gate_report.get("study_delivery_evaluated_source_signature"),
                gate_report.get("submission_minimal_evaluated_source_signature"),
            ),
            "authority_source_signature": _first_non_empty_text(
                (result or {}).get("authority_source_signature"),
                gate_report.get("study_delivery_authority_source_signature"),
                gate_report.get("submission_minimal_authority_source_signature"),
            ),
            "gate_fingerprint": _non_empty_text(gate_report.get("gate_fingerprint")),
            "authority_fingerprints": item.get("authority_fingerprints"),
            "settle_window_ns": item.get("settle_window_ns"),
            "proof_path": str(stable_current_package_freshness_path(study_root=study_root)),
        }
    return None


def write_current_package_freshness_proof(
    *,
    study_root: Path,
    source_eval_id: str,
    gate_report: dict[str, Any] | None = None,
    unit_results: list[dict[str, Any]],
    clock: Callable[[], tuple[int, str]],
    schema_version: int,
) -> dict[str, Any] | None:
    proof = build_current_package_freshness_proof(
        study_root=study_root,
        source_eval_id=source_eval_id,
        gate_report=gate_report,
        unit_results=unit_results,
        clock=clock,
        schema_version=schema_version,
    )
    if proof is None:
        return None
    proof_path = stable_current_package_freshness_path(study_root=study_root)
    proof_path.parent.mkdir(parents=True, exist_ok=True)
    proof_path.write_text(json.dumps(proof, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return proof
