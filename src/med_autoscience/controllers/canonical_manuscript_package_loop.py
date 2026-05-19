from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SURFACE = "canonical_manuscript_package_loop"
SCHEMA_VERSION = 1
PROHIBITED_MANUSCRIPT_MARKERS = {
    "author_todo_or_placeholder_in_manuscript": ("TODO", "TBD", "author pending", "placeholder"),
    "package_anchor_in_manuscript": ("current_package", "submission_manifest", "package anchor"),
    "reviewer_facing_label_in_manuscript": ("reviewer-facing", "Reviewer-facing", "reviewer facing"),
    "controller_prose_in_manuscript": ("controller decision", "owner_route", "domain route"),
}


def materialize_canonical_package_loop_proofs(
    *,
    study_root: str | Path,
    study_id: str,
    quest_id: str,
    source_refs: Iterable[str | Path],
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    generated_at = _utc_now()
    normalized_refs = _source_refs(source_refs)
    prose_gate = _manuscript_native_prose_gate(resolved_study_root / "paper" / "manuscript.md")
    source_signature = _source_signature(normalized_refs)
    rebuild_proof = {
        "surface": "canonical_manuscript_rebuild_proof",
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "study_id": study_id,
        "quest_id": quest_id,
        "source_refs": normalized_refs,
        "source_signature": source_signature,
        "canonical_source_owner": "med-autoscience",
        "current_package_write_authorized": False,
        "manuscript_native_prose_gate": prose_gate,
    }
    freshness_proof = {
        "surface": "current_package_freshness_proof",
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "study_id": study_id,
        "quest_id": quest_id,
        "source_signature": source_signature,
        "freshness_state": "controller_rebuild_required" if prose_gate["status"] == "passed" else "blocked",
        "current_package_write_authorized": False,
        "controller_authorized_rebuild_required": prose_gate["status"] == "passed",
    }
    delivery_manifest = {
        "surface": "delivery_manifest",
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "study_id": study_id,
        "quest_id": quest_id,
        "source_kind": SURFACE,
        "source_refs": normalized_refs,
        "source_signature": source_signature,
        "current_package_write_authorized": False,
    }
    rebuild_proof_ref = resolved_study_root / "artifacts" / "controller" / "canonical_package_loop" / "rebuild_proof.json"
    freshness_ref = resolved_study_root / "artifacts" / "controller" / "canonical_package_loop" / "current_package_freshness_proof.json"
    delivery_ref = resolved_study_root / "manuscript" / "delivery_manifest.json"
    _write_json(rebuild_proof_ref, rebuild_proof)
    _write_json(freshness_ref, freshness_proof)
    _write_json(delivery_ref, delivery_manifest)
    status = "ready_for_controller_authorized_package_refresh" if prose_gate["status"] == "passed" else "blocked"
    payload = {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "status": status,
        "study_id": study_id,
        "quest_id": quest_id,
        "source_refs": normalized_refs,
        "source_signature": source_signature,
        "manuscript_native_prose_gate": prose_gate,
        "rebuild_proof_ref": str(rebuild_proof_ref),
        "current_package_freshness_proof": freshness_proof,
        "current_package_freshness_proof_ref": str(freshness_ref),
        "delivery_manifest": delivery_manifest,
        "delivery_manifest_ref": str(delivery_ref),
        "current_package_write_authorized": False,
        "quality_authorized": False,
        "submission_authorized": False,
    }
    _write_json(resolved_study_root / "artifacts" / "controller" / "canonical_package_loop" / "latest.json", payload)
    return payload


def _manuscript_native_prose_gate(manuscript_path: Path) -> dict[str, Any]:
    try:
        text = manuscript_path.read_text(encoding="utf-8")
    except OSError:
        return {
            "surface": "manuscript_native_prose_gate",
            "status": "blocked",
            "blockers": ["canonical_manuscript_missing"],
            "manuscript_ref": str(manuscript_path),
        }
    blockers: list[str] = []
    for blocker, markers in PROHIBITED_MANUSCRIPT_MARKERS.items():
        if any(marker in text for marker in markers):
            blockers.append(blocker)
    return {
        "surface": "manuscript_native_prose_gate",
        "status": "blocked" if blockers else "passed",
        "blockers": blockers,
        "manuscript_ref": str(manuscript_path),
    }


def _source_refs(source_refs: Iterable[str | Path]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for ref in source_refs:
        text = str(ref).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _source_signature(source_refs: list[str]) -> str:
    digest = hashlib.sha256(json.dumps(source_refs, sort_keys=True).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


__all__ = ["materialize_canonical_package_loop_proofs"]
