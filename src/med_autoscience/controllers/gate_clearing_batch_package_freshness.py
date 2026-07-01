from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from med_autoscience.controllers import paper_authority_delivery_guard
from med_autoscience.publication_figure_quality_contract import load_figure_visual_audit_receipt
from med_autoscience.stable_json import write_stable_json


STABLE_CURRENT_PACKAGE_FRESHNESS_RELATIVE_PATH = Path("artifacts/controller/current_package_freshness/latest.json")
_BLOCKING_SYNC_STATUSES = frozenset(
    {
        "authority_route_blocked",
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


def _path_exists(path: str | None) -> bool:
    if path is None:
        return False
    return Path(path).expanduser().exists()


def _default_package_pdf_path(root: str | None) -> str | None:
    if root is None:
        return None
    return str((Path(root).expanduser() / "paper.pdf").resolve())


def _default_visual_audit_receipt_path(root: str | None) -> str | None:
    if root is None:
        return None
    return str((Path(root).expanduser() / "figure_visual_audit_receipt.json").resolve())


def _visual_audit_receipt_clear(path: str | None) -> bool:
    if path is None:
        return False
    receipt_path = Path(path).expanduser()
    if not receipt_path.exists():
        return False
    try:
        return load_figure_visual_audit_receipt(receipt_path).get("final_status") == "clear"
    except (OSError, ValueError):
        pass
    try:
        import json

        payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(payload, dict):
        return False
    status = _non_empty_text(payload.get("status")) or _non_empty_text(payload.get("visual_audit_final_status"))
    if status in {"clear", "passed", "pass", "audit_clear", "visual_audit_clear"}:
        return True
    review = payload.get("review") if isinstance(payload.get("review"), dict) else {}
    review_status = _non_empty_text(review.get("status")) or _non_empty_text(review.get("visual_audit_final_status"))
    return review_status in {"clear", "passed", "pass", "audit_clear", "visual_audit_clear"}


def _visual_audit_not_older_than_pdf(*, proof: dict[str, Any]) -> bool:
    paper_pdf = _non_empty_text(proof.get("paper_pdf_path"))
    visual_audit = _non_empty_text(proof.get("visual_audit_receipt_path"))
    if paper_pdf is None or visual_audit is None:
        return False
    try:
        return Path(visual_audit).expanduser().stat().st_mtime_ns >= Path(paper_pdf).expanduser().stat().st_mtime_ns
    except OSError:
        return False


def freshness_proof_paths_exist(proof: dict[str, Any] | None, *, require_proof_path: bool = False) -> bool:
    if not isinstance(proof, dict):
        return False
    if require_proof_path and not _path_exists(_non_empty_text(proof.get("proof_path"))):
        return False
    if not _path_exists(_non_empty_text(proof.get("submission_manifest_path"))):
        return False
    current_package_root = _non_empty_text(proof.get("current_package_root"))
    current_package_zip = _non_empty_text(proof.get("current_package_zip"))
    if not (_path_exists(current_package_root) or _path_exists(current_package_zip)):
        return False
    if not _path_exists(_non_empty_text(proof.get("paper_pdf_path"))):
        return False
    return _visual_audit_receipt_clear(_non_empty_text(proof.get("visual_audit_receipt_path"))) and (
        _visual_audit_not_older_than_pdf(proof=proof)
    )


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
        result = item.get("result") if isinstance(item.get("result"), dict) else None
        if not result:
            continue
        _started_ns, recorded_at = clock()
        current_package_root = _first_non_empty_text(
            result.get("current_package_root"),
            item.get("current_package_root"),
            gate_report.get("study_delivery_current_package_root"),
        )
        return {
            "schema_version": schema_version,
            "status": "fresh",
            "source_eval_id": source_eval_id,
            "source_unit_id": "sync_submission_minimal_delivery",
            "recorded_at": recorded_at,
            "unit_status": status,
            "submission_manifest_path": _first_non_empty_text(
                result.get("submission_manifest_path"),
                gate_report.get("submission_minimal_manifest_path"),
            ),
            "delivery_manifest_path": _first_non_empty_text(
                result.get("delivery_manifest_path"),
                gate_report.get("study_delivery_manifest_path"),
            ),
            "current_package_root": current_package_root,
            "current_package_zip": _first_non_empty_text(
                result.get("current_package_zip"),
                item.get("current_package_zip"),
                gate_report.get("study_delivery_current_package_zip"),
            ),
            "paper_pdf_path": _first_non_empty_text(
                result.get("paper_pdf_path"),
                gate_report.get("study_delivery_current_package_pdf"),
                _default_package_pdf_path(current_package_root),
            ),
            "visual_audit_receipt_path": _first_non_empty_text(
                result.get("visual_audit_receipt_path"),
                gate_report.get("study_delivery_visual_audit_receipt_path"),
                _default_visual_audit_receipt_path(current_package_root),
            ),
            "source_signature": _first_non_empty_text(
                result.get("source_signature"),
                result.get("evaluated_source_signature"),
                gate_report.get("study_delivery_evaluated_source_signature"),
                gate_report.get("submission_minimal_evaluated_source_signature"),
            ),
            "authority_source_signature": _first_non_empty_text(
                result.get("authority_source_signature"),
                gate_report.get("study_delivery_authority_source_signature"),
                gate_report.get("submission_minimal_authority_source_signature"),
            ),
            "gate_fingerprint": _non_empty_text(gate_report.get("gate_fingerprint")),
            "authority_fingerprints": item.get("authority_fingerprints"),
            "settle_window_ns": item.get("settle_window_ns"),
            "proof_path": str(stable_current_package_freshness_path(study_root=study_root)),
        }
    return None


def _delivery_sync_unit_present(unit_results: list[dict[str, Any]]) -> bool:
    return any(_non_empty_text(item.get("unit_id")) == "sync_submission_minimal_delivery" for item in unit_results)


def _gate_report_current_package_freshness_proof(
    *,
    study_root: Path,
    source_eval_id: str,
    gate_report: dict[str, Any],
    clock: Callable[[], tuple[int, str]],
    schema_version: int,
) -> dict[str, Any] | None:
    if _non_empty_text(gate_report.get("study_delivery_status")) != "current":
        return None
    source_signature = _first_non_empty_text(
        gate_report.get("study_delivery_evaluated_source_signature"),
        gate_report.get("submission_minimal_evaluated_source_signature"),
    )
    authority_source_signature = _first_non_empty_text(
        gate_report.get("study_delivery_authority_source_signature"),
        gate_report.get("submission_minimal_authority_source_signature"),
    )
    if source_signature is None or authority_source_signature is None:
        return None
    if source_signature != authority_source_signature:
        return None
    submission_manifest_path = _non_empty_text(gate_report.get("submission_minimal_manifest_path"))
    current_package_root = _non_empty_text(gate_report.get("study_delivery_current_package_root"))
    current_package_zip = _non_empty_text(gate_report.get("study_delivery_current_package_zip"))
    if submission_manifest_path is None or (current_package_root is None and current_package_zip is None):
        return None
    _started_ns, recorded_at = clock()
    return {
        "schema_version": schema_version,
        "status": "fresh",
        "source_eval_id": source_eval_id,
        "source_unit_id": "publication_gate_current_delivery",
        "recorded_at": recorded_at,
        "unit_status": "current",
        "submission_manifest_path": submission_manifest_path,
        "delivery_manifest_path": _non_empty_text(gate_report.get("study_delivery_manifest_path")),
        "current_package_root": current_package_root,
        "current_package_zip": current_package_zip,
        "paper_pdf_path": _first_non_empty_text(
            gate_report.get("study_delivery_current_package_pdf"),
            _default_package_pdf_path(current_package_root),
        ),
        "visual_audit_receipt_path": _first_non_empty_text(
            gate_report.get("study_delivery_visual_audit_receipt_path"),
            _default_visual_audit_receipt_path(current_package_root),
        ),
        "source_signature": source_signature,
        "authority_source_signature": authority_source_signature,
        "gate_fingerprint": _non_empty_text(gate_report.get("gate_fingerprint")),
        "authority_fingerprints": None,
        "settle_window_ns": None,
        "proof_path": str(stable_current_package_freshness_path(study_root=study_root)),
    }


def write_current_package_freshness_proof(
    *,
    study_root: Path,
    source_eval_id: str,
    gate_report: dict[str, Any] | None = None,
    unit_results: list[dict[str, Any]],
    clock: Callable[[], tuple[int, str]],
    schema_version: int,
) -> dict[str, Any] | None:
    proof_path = stable_current_package_freshness_path(study_root=study_root)
    if paper_authority_delivery_guard.delivery_write_blocked(study_root=study_root):
        proof_path.unlink(missing_ok=True)
        return None
    proof = build_current_package_freshness_proof(
        study_root=study_root,
        source_eval_id=source_eval_id,
        gate_report=gate_report,
        unit_results=unit_results,
        clock=clock,
        schema_version=schema_version,
    )
    if proof is None and gate_report is not None and not _delivery_sync_unit_present(unit_results):
        proof = _gate_report_current_package_freshness_proof(
            study_root=study_root,
            source_eval_id=source_eval_id,
            gate_report=gate_report,
            clock=clock,
            schema_version=schema_version,
        )
    if proof is None:
        if _delivery_sync_unit_present(unit_results):
            proof_path.unlink(missing_ok=True)
        return None
    if not freshness_proof_paths_exist(proof):
        proof_path.unlink(missing_ok=True)
        return None
    write_stable_json(proof_path, proof)
    return proof
