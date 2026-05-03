from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
SURFACE = "artifact_runtime_proof"


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _hash_file_bytes(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _authority() -> dict[str, Any]:
    return {
        "proof_can_authorize_scientific_quality": False,
        "scientific_quality_authority": "publication_eval_and_controller_decisions",
        "derived_artifact_can_authorize_submission": False,
        "derived_artifact_can_be_quality_authority": False,
        "derived_artifact_can_be_edit_source": False,
    }


def _blocked_proof(
    *,
    study_root: Path,
    manifest_path: Path,
    blockers: list[dict[str, Any]],
    refs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "rebuild_status": "blocked",
        "current_package_from_canonical_source": False,
        "blockers": blockers,
        "refs": {
            "study_root": str(study_root),
            "delivery_manifest_path": str(manifest_path),
            **(refs or {}),
        },
        "authority": _authority(),
    }


def _source_ref_text(item: object) -> str | None:
    if isinstance(item, str):
        return _text(item)
    if not isinstance(item, Mapping):
        return None
    for key in ("relative_path", "path", "ref", "source_ref"):
        text = _text(item.get(key))
        if text is not None:
            return text
    return _text(item.get("source_path"))


def _canonical_source_ref_texts(manifest: Mapping[str, Any]) -> list[str]:
    source_refs: list[str] = []
    for field_name in ("source_relative_paths", "canonical_source_refs", "source_refs"):
        for item in _list(manifest.get(field_name)):
            text = _source_ref_text(item)
            if text is not None:
                source_refs.append(text)
        if source_refs:
            return source_refs

    for item in _list(manifest.get("copied_files")):
        text = _source_ref_text(item)
        if text is not None:
            source_refs.append(text)
    return source_refs


def _relative_label_for_path(*, path: Path, source_root: Path, paper_root: Path | None, study_root: Path) -> str:
    resolved = path.expanduser().resolve()
    for root in (source_root, paper_root, study_root):
        if root is None:
            continue
        try:
            return resolved.relative_to(root.expanduser().resolve()).as_posix()
        except ValueError:
            continue
    return str(resolved)


def _resolve_source_ref(
    *,
    ref: str,
    study_root: Path,
    source_root: Path,
    paper_root: Path | None,
) -> tuple[str, Path]:
    candidate = Path(ref).expanduser()
    if candidate.is_absolute():
        resolved = candidate.resolve()
        return _relative_label_for_path(
            path=resolved,
            source_root=source_root,
            paper_root=paper_root,
            study_root=study_root,
        ), resolved

    candidates = [source_root / candidate]
    if paper_root is not None:
        candidates.append(paper_root / candidate)
    candidates.append(study_root / candidate)
    for path in candidates:
        resolved = path.expanduser().resolve()
        if resolved.is_file():
            return candidate.as_posix(), resolved
    return candidate.as_posix(), candidates[0].expanduser().resolve()


def _source_signature(
    *,
    study_root: Path,
    source_root: Path,
    paper_root: Path | None,
    source_refs: list[str],
) -> tuple[str | None, list[dict[str, Any]], list[str]]:
    entries: list[dict[str, Any]] = []
    missing_refs: list[str] = []
    seen_labels: set[str] = set()
    for ref in source_refs:
        label, path = _resolve_source_ref(
            ref=ref,
            study_root=study_root,
            source_root=source_root,
            paper_root=paper_root,
        )
        if label in seen_labels:
            continue
        seen_labels.add(label)
        if not path.is_file():
            missing_refs.append(label)
            continue
        stat = path.stat()
        entries.append(
            {
                "path": label,
                "source_path": str(path),
                "size": stat.st_size,
                "sha256": _hash_file_bytes(path),
            }
        )
    if missing_refs or not entries:
        return None, entries, sorted(missing_refs)
    payload = [
        {
            "path": item["path"],
            "size": item["size"],
            "sha256": item["sha256"],
        }
        for item in sorted(entries, key=lambda value: str(value["path"]))
    ]
    signature = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return signature, sorted(entries, key=lambda value: str(value["path"])), []


def _stable_blocking_refs(value: object) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for item in _list(value):
        if isinstance(item, Mapping):
            compact = {str(key): item[key] for key in sorted(item) if str(item.get(key) or "").strip()}
            if compact:
                refs.append(compact)
            continue
        text = str(item or "").strip()
        if text:
            refs.append({"ref": text})
    return refs


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _read_delivery_manifest(
    *,
    study_root: Path,
    manifest_path: Path,
) -> tuple[Mapping[str, Any] | None, dict[str, Any] | None]:
    if not manifest_path.exists():
        return None, _blocked_proof(
            study_root=study_root,
            manifest_path=manifest_path,
            blockers=[{"code": "delivery_manifest_missing"}],
        )
    try:
        manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, _blocked_proof(
            study_root=study_root,
            manifest_path=manifest_path,
            blockers=[{"code": "delivery_manifest_invalid"}],
        )
    if not isinstance(manifest_payload, Mapping):
        return None, _blocked_proof(
            study_root=study_root,
            manifest_path=manifest_path,
            blockers=[{"code": "delivery_manifest_invalid"}],
        )
    return manifest_payload, None


def _status_from_bool(*, passed: bool | None, exists: bool = True) -> str:
    if not exists:
        return "missing"
    if passed is True:
        return "pass"
    if passed is False:
        return "fail"
    return "unknown"


def _submission_minimal_truth(*, study_root: Path, manifest_payload: Mapping[str, Any] | None) -> dict[str, Any]:
    manifest_path = study_root / "paper" / "submission_minimal" / "submission_manifest.json"
    manifest = _read_json_object(manifest_path)
    if manifest is None:
        manifest = dict(_mapping(manifest_payload.get("submission_minimal")) if manifest_payload is not None else {})
    surface_qc = _mapping(_mapping(manifest.get("manuscript")).get("surface_qc"))
    failures = [
        dict(item)
        for item in _list(surface_qc.get("failures"))
        if isinstance(item, Mapping)
    ]
    return {
        "surface": "submission_minimal_truth",
        "status": "present" if manifest else "missing",
        "manifest_path": str(manifest_path) if manifest_path.exists() else None,
        "citation_style": _text(manifest.get("citation_style")),
        "publication_profile": _text(manifest.get("publication_profile")),
        "surface_qc": {
            "status": _text(surface_qc.get("status")) or ("unknown" if manifest else "missing"),
            "failure_count": len(failures),
            "failures": failures,
            "internal_language_leakage": any(
                _text(item.get("failure_reason")) == "submission_source_markdown_internal_instruction_leakage"
                for item in failures
            ),
        },
    }


def _publication_surface_qc_truth(
    *,
    publication_eval_payload: Mapping[str, Any] | None,
    evaluation_summary_payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    verdict = _mapping(publication_eval_payload.get("verdict")) if publication_eval_payload is not None else {}
    quality_closure_truth = (
        _mapping(evaluation_summary_payload.get("quality_closure_truth"))
        if evaluation_summary_payload is not None
        else {}
    )
    deterministic_gates = (
        _mapping(publication_eval_payload.get("deterministic_quality_gates"))
        if publication_eval_payload is not None
        else {}
    )
    return {
        "surface": "publication_surface_qc_truth",
        "status": _publication_surface_qc_status(
            deterministic_gates=deterministic_gates,
            verdict=verdict,
            quality_closure_truth=quality_closure_truth,
            publication_eval_payload=publication_eval_payload,
            evaluation_summary_payload=evaluation_summary_payload,
        ),
        "overall_verdict": _text(verdict.get("overall_verdict")),
        "quality_closure_state": _text(quality_closure_truth.get("state")),
        "blocking_gate_keys": list(deterministic_gates.get("blocking_gate_keys") or []),
        "blockers": _publication_surface_qc_blockers(
            publication_eval_payload=publication_eval_payload,
            quality_closure_truth=quality_closure_truth,
            deterministic_gates=deterministic_gates,
        ),
    }


def _publication_surface_qc_status(
    *,
    deterministic_gates: Mapping[str, Any],
    verdict: Mapping[str, Any],
    quality_closure_truth: Mapping[str, Any],
    publication_eval_payload: Mapping[str, Any] | None,
    evaluation_summary_payload: Mapping[str, Any] | None,
) -> str:
    return (
        _text(deterministic_gates.get("status"))
        or _text(verdict.get("overall_verdict"))
        or _text(quality_closure_truth.get("state"))
        or ("missing" if publication_eval_payload is None and evaluation_summary_payload is None else "unknown")
    )


def _publication_surface_qc_blockers(
    *,
    publication_eval_payload: Mapping[str, Any] | None,
    quality_closure_truth: Mapping[str, Any],
    deterministic_gates: Mapping[str, Any],
) -> list[str]:
    blockers: list[str] = []
    for source in (
        publication_eval_payload.get("blockers") if publication_eval_payload is not None else None,
        quality_closure_truth.get("blockers"),
        deterministic_gates.get("blocking_gate_keys"),
    ):
        for item in _list(source):
            text = _text(item)
            if text is not None and text not in blockers:
                blockers.append(text)
    return blockers


def _deterministic_gate_status(
    *,
    deterministic_gates: Mapping[str, Any],
    gate_key: str,
    fallback_blockers: list[str],
    exists: bool = True,
) -> dict[str, Any]:
    gate_payload = _mapping(_mapping(deterministic_gates.get("gates")).get(gate_key))
    blockers = list(gate_payload.get("blockers") or [])
    if not blockers:
        blockers = list(fallback_blockers)
    return {
        "gate_key": gate_key,
        "status": _text(gate_payload.get("status")) or _status_from_bool(passed=not blockers, exists=exists),
        "blockers": blockers,
        "evidence_refs": list(gate_payload.get("evidence_refs") or []),
    }


def _submission_hygiene_flow(*, status: str, blockers: list[str]) -> dict[str, Any]:
    if status == "clear":
        step_id = "inspect_study_progress"
        summary = "投稿卫生 truth 已清晰，继续通过 study-progress 监管 artifact 与质量门控。"
    elif "artifact_rebuild" in blockers or "artifact_runtime_proof_blocked" in blockers:
        step_id = "rebuild_from_canonical_source"
        summary = "先从 canonical source 重建投稿包，再刷新 artifact_runtime_proof。"
    else:
        step_id = "return_to_publication_gate"
        summary = "先回到 publication gate / submission minimal 修复 hygiene blockers。"
    return {
        "surface": "product_recommended_flow_projection",
        "recommended_step_id": step_id,
        "summary": summary,
        "steps": [
            {
                "step_id": "inspect_study_progress",
                "surface_kind": "study_progress",
                "field_path": "submission_hygiene_truth",
            },
            {
                "step_id": "repair_hygiene_blockers",
                "surface_kind": "publication_eval_or_submission_minimal",
                "field_path": "submission_hygiene_truth.gates",
            },
            {
                "step_id": "rebuild_from_canonical_source",
                "surface_kind": "artifact_runtime_proof",
                "field_path": "submission_hygiene_truth.artifact_runtime_proof",
            },
        ],
    }


def _failure_reasons(failures: list[Any]) -> list[str]:
    return [
        _text(item.get("failure_reason")) or "submission_surface_qc_failure_present"
        for item in failures
        if isinstance(item, Mapping)
    ]


def _submission_hygiene_gates(
    *,
    deterministic_gates: Mapping[str, Any],
    publication_eval_payload: Mapping[str, Any] | None,
    surface_failures: list[Any],
    proof: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    internal_language_failures = [
        item
        for item in surface_failures
        if _text((item if isinstance(item, Mapping) else {}).get("failure_reason"))
        == "submission_source_markdown_internal_instruction_leakage"
    ]
    artifact_blocked = proof.get("rebuild_status") != "current" or not bool(
        proof.get("current_package_from_canonical_source")
    )
    return {
        "citation_grounding": _deterministic_gate_status(
            deterministic_gates=deterministic_gates,
            gate_key="citation_grounding",
            fallback_blockers=[],
            exists=publication_eval_payload is not None,
        ),
        "numeric_grounding": _deterministic_gate_status(
            deterministic_gates=deterministic_gates,
            gate_key="numeric_grounding",
            fallback_blockers=[],
            exists=publication_eval_payload is not None,
        ),
        "display_grounding": _deterministic_gate_status(
            deterministic_gates=deterministic_gates,
            gate_key="display_grounding",
            fallback_blockers=_failure_reasons(surface_failures),
            exists=publication_eval_payload is not None or bool(surface_failures),
        ),
        "internal_language_leakage": _deterministic_gate_status(
            deterministic_gates=deterministic_gates,
            gate_key="internal_language_leakage",
            fallback_blockers=_failure_reasons(internal_language_failures),
            exists=publication_eval_payload is not None or bool(internal_language_failures),
        ),
        "artifact_rebuild": {
            "gate_key": "artifact_rebuild",
            "status": "blocked" if artifact_blocked else "pass",
            "blockers": [
                _text(item.get("code")) or "artifact_runtime_proof_blocked"
                for item in _list(proof.get("blockers"))
                if isinstance(item, Mapping)
            ],
            "evidence_refs": [{"artifact_runtime_proof_refs": dict(proof.get("refs") or {})}],
        },
    }


def build_submission_hygiene_truth(
    study_root: str | Path,
    *,
    artifact_runtime_proof: Mapping[str, Any] | None = None,
    publication_eval_payload: Mapping[str, Any] | None = None,
    evaluation_summary_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    proof = dict(artifact_runtime_proof or build_artifact_runtime_proof(resolved_study_root))
    manifest_payload = _read_json_object(resolved_study_root / "manuscript" / "delivery_manifest.json")
    if publication_eval_payload is None:
        publication_eval_payload = _read_json_object(
            resolved_study_root / "artifacts" / "publication_eval" / "latest.json"
        )
    if evaluation_summary_payload is None:
        evaluation_summary_payload = _read_json_object(
            resolved_study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
        )
    submission_minimal_truth = _submission_minimal_truth(
        study_root=resolved_study_root,
        manifest_payload=manifest_payload,
    )
    publication_surface_qc_truth = _publication_surface_qc_truth(
        publication_eval_payload=publication_eval_payload,
        evaluation_summary_payload=evaluation_summary_payload,
    )
    deterministic_gates = (
        _mapping(publication_eval_payload.get("deterministic_quality_gates"))
        if publication_eval_payload is not None
        else {}
    )
    surface_failures = list(_mapping(submission_minimal_truth.get("surface_qc")).get("failures") or [])
    gates = _submission_hygiene_gates(
        deterministic_gates=deterministic_gates,
        publication_eval_payload=publication_eval_payload,
        surface_failures=surface_failures,
        proof=proof,
    )
    blockers = [
        gate_key
        for gate_key, gate in gates.items()
        if _text(gate.get("status")) in {"blocked", "fail", "missing"}
    ]
    status = "clear" if not blockers else "blocked"
    return {
        "surface": "submission_hygiene_truth",
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "summary": (
            "Submission hygiene gates are clear."
            if status == "clear"
            else f"Submission hygiene blocked by {', '.join(blockers)}."
        ),
        "submission_minimal": submission_minimal_truth,
        "publication_surface_qc": publication_surface_qc_truth,
        "internal_language_leakage": gates["internal_language_leakage"],
        "gates": gates,
        "blocking_gate_keys": blockers,
        "artifact_runtime_proof": proof,
        "recommended_flow": _submission_hygiene_flow(status=status, blockers=blockers),
        "authority": {
            "hygiene_truth_can_authorize_scientific_quality": False,
            "hygiene_truth_can_authorize_submission": False,
            "scientific_quality_authority": "publication_eval_and_controller_decisions",
            "artifact_authority": "artifact_runtime_proof",
        },
        "refs": {
            "study_root": str(resolved_study_root),
            "publication_eval_path": str(resolved_study_root / "artifacts" / "publication_eval" / "latest.json"),
            "evaluation_summary_path": str(
                resolved_study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
            ),
            "submission_manifest_path": str(
                resolved_study_root / "paper" / "submission_minimal" / "submission_manifest.json"
            ),
        },
    }


def _artifact_proof_manifest_blockers(
    *,
    source_root: Path | None,
    recorded_source_signature: str | None,
    recorded_authority_source_signature: str | None,
    blocking_artifact_refs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    if source_root is None:
        blockers.append({"code": "controller_authorized_package_source_root_missing"})
    if recorded_source_signature is None:
        blockers.append({"code": "source_signature_missing"})
    if blocking_artifact_refs:
        blockers.append(
            {
                "code": "blocking_artifact_refs_present",
                "blocking_artifact_refs": blocking_artifact_refs,
            }
        )
    if (
        recorded_source_signature is not None
        and recorded_authority_source_signature is not None
        and recorded_source_signature != recorded_authority_source_signature
    ):
        blockers.append(
            {
                "code": "authority_source_signature_mismatch",
                "delivery_source_signature": recorded_source_signature,
                "authority_source_signature": recorded_authority_source_signature,
            }
        )
    return blockers


def _artifact_proof_manifest_refs(
    *,
    source_root: Path | None,
    paper_root: Path | None,
    current_package_root: str | None,
    current_package_zip: str | None,
    recorded_source_signature: str | None,
    recorded_authority_source_signature: str | None,
    blocking_artifact_refs: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "controller_authorized_package_source_root": str(source_root) if source_root is not None else None,
        "controller_authorized_paper_root": str(paper_root) if paper_root is not None else None,
        "current_package_root": current_package_root,
        "current_package_zip": current_package_zip,
        "delivery_source_signature": recorded_source_signature,
        "authority_source_signature": recorded_authority_source_signature,
        "blocking_artifact_refs": blocking_artifact_refs,
    }


def _append_source_signature_blockers(
    *,
    study_root: Path,
    source_root: Path,
    paper_root: Path | None,
    source_refs: list[str],
    recorded_source_signature: str | None,
    refs: dict[str, Any],
    blockers: list[dict[str, Any]],
) -> None:
    evaluated_source_signature, source_entries, missing_refs = _source_signature(
        study_root=study_root,
        source_root=source_root,
        paper_root=paper_root,
        source_refs=source_refs,
    )
    refs["source_signature"] = evaluated_source_signature
    refs["canonical_source_entries"] = source_entries
    if missing_refs:
        refs["missing_source_refs"] = missing_refs
        blockers.append({"code": "canonical_source_ref_missing", "missing_source_refs": missing_refs})
    if (
        evaluated_source_signature is not None
        and recorded_source_signature is not None
        and evaluated_source_signature != recorded_source_signature
    ):
        blockers.append(
            {
                "code": "source_signature_mismatch",
                "evaluated_source_signature": evaluated_source_signature,
                "delivery_source_signature": recorded_source_signature,
            }
        )


def build_artifact_runtime_proof(study_root: str | Path) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    manifest_path = resolved_study_root / "manuscript" / "delivery_manifest.json"
    manifest_payload, blocked_manifest = _read_delivery_manifest(
        study_root=resolved_study_root,
        manifest_path=manifest_path,
    )
    if blocked_manifest is not None:
        return blocked_manifest

    manifest = manifest_payload or {}
    surface_roles = _mapping(manifest.get("surface_roles"))
    source_payload = _mapping(manifest.get("source"))
    targets = _mapping(manifest.get("targets"))
    source_root_text = _text(surface_roles.get("controller_authorized_package_source_root"))
    paper_root_text = _text(surface_roles.get("controller_authorized_paper_root")) or _text(source_payload.get("paper_root"))
    source_root = Path(source_root_text).expanduser().resolve() if source_root_text is not None else None
    paper_root = Path(paper_root_text).expanduser().resolve() if paper_root_text is not None else None
    recorded_source_signature = _text(manifest.get("source_signature"))
    recorded_authority_source_signature = _text(manifest.get("authority_source_signature")) or recorded_source_signature
    blocking_artifact_refs = _stable_blocking_refs(manifest.get("blocking_artifact_refs"))
    current_package_root = _text(surface_roles.get("human_facing_current_package_root")) or _text(
        targets.get("current_package_root")
    )
    current_package_zip = _text(surface_roles.get("human_facing_current_package_zip")) or _text(
        targets.get("current_package_zip")
    )

    refs = _artifact_proof_manifest_refs(
        source_root=source_root,
        paper_root=paper_root,
        current_package_root=current_package_root,
        current_package_zip=current_package_zip,
        recorded_source_signature=recorded_source_signature,
        recorded_authority_source_signature=recorded_authority_source_signature,
        blocking_artifact_refs=blocking_artifact_refs,
    )
    blockers = _artifact_proof_manifest_blockers(
        source_root=source_root,
        recorded_source_signature=recorded_source_signature,
        recorded_authority_source_signature=recorded_authority_source_signature,
        blocking_artifact_refs=blocking_artifact_refs,
    )

    if source_root is None:
        return _blocked_proof(
            study_root=resolved_study_root,
            manifest_path=manifest_path,
            blockers=blockers,
            refs=refs,
        )

    source_refs = _canonical_source_ref_texts(manifest)
    refs["canonical_source_refs"] = source_refs
    if not source_refs:
        blockers.append({"code": "canonical_source_refs_missing"})

    _append_source_signature_blockers(
        study_root=resolved_study_root,
        source_root=source_root,
        paper_root=paper_root,
        source_refs=source_refs,
        recorded_source_signature=recorded_source_signature,
        refs=refs,
        blockers=blockers,
    )

    if blockers:
        return _blocked_proof(
            study_root=resolved_study_root,
            manifest_path=manifest_path,
            blockers=blockers,
            refs=refs,
        )

    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "rebuild_status": "current",
        "current_package_from_canonical_source": True,
        "blockers": [],
        "refs": {
            "study_root": str(resolved_study_root),
            "delivery_manifest_path": str(manifest_path),
            **refs,
        },
        "authority": _authority(),
    }
