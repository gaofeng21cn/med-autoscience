from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
SURFACE = "repair_execution_evidence"
STABLE_REPAIR_EXECUTION_EVIDENCE_RELATIVE_PATH = Path(
    "artifacts/controller/repair_execution_evidence/latest.json"
)

_CURRENT_PACKAGE_BLOCKER = "current_package_ref_not_canonical_delta"
_AUTHORITY_CLAIM_BLOCKERS = {
    "quality_authorized": "quality_override_not_allowed",
    "quality_ready_authorized": "quality_override_not_allowed",
    "quality_authority_granted": "quality_override_not_allowed",
    "publication_ready_authorized": "quality_override_not_allowed",
    "submission_authorized": "submission_override_not_allowed",
    "submission_ready_authorized": "submission_override_not_allowed",
    "current_package_write_authorized": "current_package_write_not_allowed",
    "can_write_current_package": "current_package_write_not_allowed",
}


def stable_repair_execution_evidence_path(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / STABLE_REPAIR_EXECUTION_EVIDENCE_RELATIVE_PATH


def write_repair_execution_evidence(*, study_root: Path, evidence: Mapping[str, Any]) -> Path:
    path = stable_repair_execution_evidence_path(study_root=study_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(evidence), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def build_repair_execution_evidence(
    *,
    study_id: str,
    quest_id: str,
    study_root: Path,
    repair_work_unit: Mapping[str, Any] | None,
    review_finding: Mapping[str, Any] | None,
    source_refs: Iterable[object],
    changed_artifact_refs: Iterable[object],
    revision_log_ref: object | None = None,
    evidence_ledger_ref: object | None = None,
    review_ledger_ref: object | None = None,
    gate_replay_target: str | None = None,
    gate_replay_refs: Iterable[object] | None = None,
    ai_reviewer_recheck_request_ref: object | None = None,
    authority_claims: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    work_unit = _mapping(repair_work_unit)
    finding = _mapping(review_finding)
    blockers: list[str] = []
    valid_changed_refs, excluded_refs, ref_blockers = _canonical_changed_refs(
        study_root=resolved_study_root,
        changed_artifact_refs=changed_artifact_refs,
    )
    blockers.extend(ref_blockers)
    meaningful_delta = bool(valid_changed_refs)
    if not meaningful_delta:
        blockers.append("canonical_artifact_delta_missing")

    resolved_gate_replay_target = (
        _text(gate_replay_target)
        or _text(work_unit.get("gate_replay_target"))
        or _text(work_unit.get("gate_replay_surface"))
    )
    normalized_gate_refs = _reference_list(gate_replay_refs or ())
    normalized_source_refs = _reference_list(source_refs)
    normalized_revision_log_ref = _first_reference(revision_log_ref)
    normalized_evidence_ledger_ref = _first_reference(evidence_ledger_ref)
    normalized_review_ledger_ref = _first_reference(review_ledger_ref) or normalized_revision_log_ref
    normalized_ai_recheck_ref = _first_reference(ai_reviewer_recheck_request_ref)

    evidence_ledger_required = meaningful_delta
    review_ledger_required = meaningful_delta
    evidence_ledger_done = evidence_ledger_required and _ref_exists(normalized_evidence_ledger_ref)
    review_ledger_done = review_ledger_required and _ref_exists(normalized_review_ledger_ref)
    if evidence_ledger_required and not evidence_ledger_done:
        blockers.append("evidence_ledger_update_missing")
    if review_ledger_required and not review_ledger_done:
        blockers.append("review_ledger_update_missing")

    gate_replay_required = meaningful_delta and resolved_gate_replay_target is not None
    gate_replay_done = gate_replay_required and bool(normalized_gate_refs)
    if gate_replay_required and not gate_replay_done:
        blockers.append("gate_replay_missing")

    ai_reviewer_recheck_required = meaningful_delta
    ai_reviewer_recheck_done = ai_reviewer_recheck_required and _ref_exists(normalized_ai_recheck_ref)
    if ai_reviewer_recheck_required and not ai_reviewer_recheck_done:
        blockers.append("ai_reviewer_recheck_request_missing")

    blockers.extend(_authority_claim_blockers(authority_claims))
    source_fingerprint = _source_fingerprint(
        study_root=resolved_study_root,
        work_unit=work_unit,
        finding=finding,
        source_refs=normalized_source_refs,
        changed_refs=valid_changed_refs,
        gate_replay_refs=normalized_gate_refs,
    )
    work_unit_id = _text(work_unit.get("unit_id")) or _text(work_unit.get("work_unit_id")) or "repair_work_unit"
    idempotency_key = (
        f"paper-repair-execution::{study_id}::{quest_id}::{work_unit_id}::{source_fingerprint.removeprefix('sha256:')[:16]}"
    )
    required_missing = {
        "evidence_ledger_update_missing",
        "review_ledger_update_missing",
        "gate_replay_missing",
        "ai_reviewer_recheck_request_missing",
    }
    progress_delta_candidate = meaningful_delta and gate_replay_done
    status = (
        "blocked"
        if not meaningful_delta
        else "pending"
        if any(blocker in required_missing for blocker in blockers)
        else "progress_delta_candidate"
    )
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "study_id": study_id,
        "quest_id": quest_id,
        "status": status,
        "repair_work_unit": work_unit,
        "review_finding": finding,
        "source_refs": normalized_source_refs,
        "canonical_artifact_delta": {
            "status": "fresh" if meaningful_delta else "missing",
            "meaningful_artifact_delta": meaningful_delta,
            "changed_artifact_ref_count": len(valid_changed_refs),
            "excluded_artifact_ref_count": len(excluded_refs),
            "artifact_refs": valid_changed_refs,
        },
        "changed_artifact_refs": valid_changed_refs,
        "excluded_artifact_refs": excluded_refs,
        "revision_log_ref": normalized_revision_log_ref,
        "evidence_ledger_update_required": evidence_ledger_required,
        "evidence_ledger_update_done": evidence_ledger_done,
        "evidence_ledger_ref": normalized_evidence_ledger_ref,
        "review_ledger_update_required": review_ledger_required,
        "review_ledger_update_done": review_ledger_done,
        "review_ledger_ref": normalized_review_ledger_ref,
        "gate_replay_target": resolved_gate_replay_target,
        "gate_replay_required": gate_replay_required,
        "gate_replay_done": gate_replay_done,
        "gate_replay_refs": normalized_gate_refs,
        "ai_reviewer_recheck_required": ai_reviewer_recheck_required,
        "ai_reviewer_recheck_done": ai_reviewer_recheck_done,
        "ai_reviewer_recheck_request_ref": normalized_ai_recheck_ref,
        "progress_delta_candidate": progress_delta_candidate,
        "idempotency_key": idempotency_key,
        "source_fingerprint": source_fingerprint,
        "blockers": _dedupe(blockers),
        "quality_authorized": False,
        "submission_authorized": False,
        "current_package_write_authorized": False,
    }


def build_from_quality_repair_batch_result(
    *,
    study_id: str,
    quest_id: str,
    study_root: Path,
    source_eval_id: str | None,
    source_eval_artifact_path: str,
    source_summary_id: str | None,
    source_summary_artifact_path: str,
    gate_clearing_result: Mapping[str, Any],
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    work_unit = _repair_work_unit(gate_clearing_result)
    gate_replay = _mapping(gate_clearing_result.get("gate_replay"))
    gate_replay_refs = _gate_replay_refs(gate_replay=gate_replay, gate_clearing_result=gate_clearing_result)
    return build_repair_execution_evidence(
        study_id=study_id,
        quest_id=quest_id,
        study_root=resolved_study_root,
        repair_work_unit=work_unit,
        review_finding={
            "source_eval_id": source_eval_id,
            "source_summary_id": source_summary_id,
        },
        source_refs=[
            source_eval_artifact_path,
            source_summary_artifact_path,
            gate_clearing_result.get("record_path"),
        ],
        changed_artifact_refs=_changed_refs_from_unit_results(gate_clearing_result.get("unit_results")),
        revision_log_ref=_default_review_ledger_ref(resolved_study_root),
        evidence_ledger_ref=_default_evidence_ledger_ref(resolved_study_root),
        review_ledger_ref=_default_review_ledger_ref(resolved_study_root),
        gate_replay_target=_text(work_unit.get("gate_replay_target")) or ("publication_gate" if gate_replay else None),
        gate_replay_refs=gate_replay_refs,
        ai_reviewer_recheck_request_ref=_default_ai_reviewer_recheck_ref(resolved_study_root),
        authority_claims=_authority_claims_from_unit_results(gate_clearing_result.get("unit_results")),
    )


def _canonical_changed_refs(
    *,
    study_root: Path,
    changed_artifact_refs: Iterable[object],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    valid: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    blockers: list[str] = []
    seen: set[str] = set()
    for raw_ref in changed_artifact_refs:
        raw_payload = _ref_payload(raw_ref)
        raw_path = _ref_path(raw_ref)
        if raw_path is None:
            continue
        resolved = _resolve_ref_path(study_root=study_root, raw_path=raw_path)
        ref = {
            **{key: value for key, value in raw_payload.items() if key != "path"},
            "path": str(resolved),
        }
        if _is_current_package_ref(resolved):
            excluded.append(ref)
            blockers.append(_CURRENT_PACKAGE_BLOCKER)
            continue
        if not _is_canonical_delta_ref(study_root=study_root, path=resolved):
            excluded.append(ref)
            blockers.append("non_canonical_artifact_ref")
            continue
        if not resolved.exists() or not resolved.is_file():
            excluded.append(ref)
            blockers.append("changed_artifact_ref_missing")
            continue
        fingerprint = _path_fingerprint(resolved)
        if fingerprint is not None:
            ref["fingerprint"] = fingerprint
        if ref["path"] in seen:
            continue
        seen.add(ref["path"])
        valid.append(ref)
    return valid, excluded, _dedupe(blockers)


def _changed_refs_from_unit_results(unit_results: object) -> list[object]:
    if not isinstance(unit_results, list):
        return []
    refs: list[object] = []
    for item in unit_results:
        payload = _mapping(item)
        result = _mapping(payload.get("result"))
        for container in (result, payload):
            for key in (
                "changed_artifact_refs",
                "canonical_artifact_refs",
                "artifact_refs",
                "output_artifact_refs",
                "output_refs",
                "generated_files",
            ):
                value = container.get(key)
                if isinstance(value, list):
                    refs.extend(value)
                elif value:
                    refs.append(value)
        for key in ("path", "artifact_path", "source_path", "output_path", "manifest_path"):
            if result.get(key):
                refs.append(result.get(key))
    return refs


def _authority_claims_from_unit_results(unit_results: object) -> dict[str, Any]:
    claims: dict[str, Any] = {}
    if not isinstance(unit_results, list):
        return claims
    for item in unit_results:
        payload = _mapping(item)
        result = _mapping(payload.get("result"))
        for container in (payload, result, _mapping(result.get("authority_claims"))):
            for key in _AUTHORITY_CLAIM_BLOCKERS:
                if container.get(key) is True:
                    claims[key] = True
    return claims


def _authority_claim_blockers(authority_claims: Mapping[str, Any] | None) -> list[str]:
    payload = _mapping(authority_claims)
    return _dedupe(blocker for key, blocker in _AUTHORITY_CLAIM_BLOCKERS.items() if payload.get(key) is True)


def _repair_work_unit(gate_clearing_result: Mapping[str, Any]) -> dict[str, Any]:
    for key in ("selected_publication_work_unit", "current_publication_work_unit", "explicit_publication_work_unit"):
        payload = gate_clearing_result.get(key)
        if isinstance(payload, Mapping) and payload:
            return dict(payload)
    for item in gate_clearing_result.get("unit_results") or []:
        payload = _mapping(item)
        unit_id = _text(payload.get("unit_id"))
        if unit_id:
            return {"unit_id": unit_id, "status": _text(payload.get("status"))}
    return {"unit_id": "quality_repair_batch"}


def _gate_replay_refs(*, gate_replay: Mapping[str, Any], gate_clearing_result: Mapping[str, Any]) -> list[object]:
    refs: list[object] = []
    for key in ("report_json", "record_path"):
        value = gate_replay.get(key)
        if value:
            refs.append(value)
    result_record = gate_clearing_result.get("record_path")
    if result_record:
        refs.append(result_record)
    return refs


def _default_evidence_ledger_ref(study_root: Path) -> str | None:
    path = study_root / "paper" / "evidence_ledger.json"
    return str(path.resolve()) if path.exists() else None


def _default_review_ledger_ref(study_root: Path) -> str | None:
    for relpath in (Path("paper/review/review_ledger.json"), Path("paper/review_ledger.json")):
        path = study_root / relpath
        if path.exists():
            return str(path.resolve())
    return None


def _default_ai_reviewer_recheck_ref(study_root: Path) -> str | None:
    path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    return str(path.resolve()) if path.exists() else None


def _is_canonical_delta_ref(*, study_root: Path, path: Path) -> bool:
    resolved = path.expanduser().resolve()
    for root in (
        study_root / "paper",
        study_root / "artifacts" / "results",
        study_root / "results",
    ):
        if _is_relative_to(resolved, root.expanduser().resolve()):
            try:
                relative = resolved.relative_to(root.expanduser().resolve())
            except ValueError:
                return False
            if relative.parts and relative.parts[0] in {"submission_minimal", "current_package"}:
                return False
            return True
    return False


def _is_current_package_ref(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    return "current_package" in parts or path.name in {"current_package.zip", "current_package.tar.gz"}


def _resolve_ref_path(*, study_root: Path, raw_path: str) -> Path:
    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (study_root / candidate).resolve()


def _ref_payload(raw_ref: object) -> dict[str, Any]:
    if isinstance(raw_ref, Mapping):
        return dict(raw_ref)
    return {}


def _ref_path(raw_ref: object) -> str | None:
    if isinstance(raw_ref, Mapping):
        for key in ("path", "artifact_path", "source_path", "output_path", "manifest_path", "ref"):
            text = _text(raw_ref.get(key))
            if text:
                return text
        return None
    return _text(raw_ref)


def _reference_list(values: Iterable[object]) -> list[str]:
    refs: list[str] = []
    for value in values:
        text = _first_reference(value)
        if text and text not in refs:
            refs.append(text)
    return refs


def _first_reference(value: object | None) -> str | None:
    raw = _ref_path(value)
    if raw is None:
        raw = _text(value)
    if raw is None:
        return None
    path = Path(raw).expanduser()
    if path.exists() or path.is_absolute() or "/" in raw:
        return str(path.resolve())
    return raw


def _ref_exists(value: str | None) -> bool:
    if value is None:
        return False
    try:
        return Path(value).expanduser().exists()
    except OSError:
        return False


def _source_fingerprint(
    *,
    study_root: Path,
    work_unit: Mapping[str, Any],
    finding: Mapping[str, Any],
    source_refs: list[str],
    changed_refs: list[dict[str, Any]],
    gate_replay_refs: list[str],
) -> str:
    payload = {
        "study_root": str(study_root),
        "work_unit": dict(work_unit),
        "review_finding": dict(finding),
        "source_refs": [_fingerprint_ref(value) for value in source_refs],
        "changed_refs": changed_refs,
        "gate_replay_refs": [_fingerprint_ref(value) for value in gate_replay_refs],
    }
    digest = hashlib.sha256(json.dumps(payload, ensure_ascii=True, sort_keys=True).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _fingerprint_ref(value: str) -> dict[str, Any] | str:
    try:
        path = Path(value).expanduser()
    except TypeError:
        return value
    if path.exists():
        fingerprint = _path_fingerprint(path)
        return {"ref": str(path.resolve()), "fingerprint": fingerprint}
    return value


def _path_fingerprint(path: Path) -> dict[str, Any] | None:
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists() or not resolved.is_file():
        return None
    digest = hashlib.sha256()
    with resolved.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    stat = resolved.stat()
    return {
        "size": stat.st_size,
        "content_sha256": digest.hexdigest(),
    }


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _dedupe(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = _text(value)
        if text and text not in result:
            result.append(text)
    return result


__all__ = [
    "SCHEMA_VERSION",
    "SURFACE",
    "STABLE_REPAIR_EXECUTION_EVIDENCE_RELATIVE_PATH",
    "build_from_quality_repair_batch_result",
    "build_repair_execution_evidence",
    "stable_repair_execution_evidence_path",
    "write_repair_execution_evidence",
]
