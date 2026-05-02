from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
from typing import Any


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _hash_file_bytes(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        digest.update(handle.read())
    return digest.hexdigest()


def _source_signature(*, paper_root: Path, source_root: Path, relative_paths: list[str]) -> str:
    fingerprint_payload: list[dict[str, Any]] = []
    for relative in relative_paths:
        relative_path = Path(relative)
        source = source_root / relative_path
        if not source.exists():
            source = paper_root / relative_path
        stat = source.stat()
        fingerprint_payload.append(
            {
                "path": relative_path.as_posix(),
                "size": stat.st_size,
                "sha256": _hash_file_bytes(source),
            }
        )
    canonical = json.dumps(fingerprint_payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _write_manifest(
    study_root: Path,
    *,
    source_signature: str,
    source_root: Path,
    paper_root: Path,
    relative_paths: list[str],
    blocking_artifact_refs: list[dict[str, Any]] | None = None,
) -> Path:
    current_package_root = study_root / "manuscript" / "current_package"
    current_package_zip = study_root / "manuscript" / "current_package.zip"
    current_package_root.mkdir(parents=True, exist_ok=True)
    _write_text(current_package_zip, "zip placeholder")
    manifest = {
        "schema_version": 1,
        "stage": "submission_minimal",
        "source_signature": source_signature,
        "evaluated_source_signature": source_signature,
        "authority_source_signature": source_signature,
        "source_relative_paths": relative_paths,
        "source": {
            "paper_root": str(paper_root.resolve()),
            "package_source_root": str(source_root.resolve()),
        },
        "surface_roles": {
            "controller_authorized_paper_root": str(paper_root.resolve()),
            "controller_authorized_package_source_root": str(source_root.resolve()),
            "human_facing_current_package_root": str(current_package_root.resolve()),
            "human_facing_current_package_zip": str(current_package_zip.resolve()),
        },
        "blocking_artifact_refs": blocking_artifact_refs or [],
    }
    manifest_path = study_root / "manuscript" / "delivery_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def _canonical_study(tmp_path: Path) -> tuple[Path, Path, Path, str, list[str]]:
    study_root = tmp_path / "study"
    paper_root = study_root / "paper"
    source_root = paper_root / "submission_minimal"
    _write_text(source_root / "manuscript.md", "# Manuscript\n\nCanonical source.\n")
    _write_text(source_root / "submission_manifest.json", '{"status":"ready"}\n')
    _write_text(paper_root / "evidence_ledger.json", '{"evidence":"canonical"}\n')
    relative_paths = ["evidence_ledger.json", "manuscript.md", "submission_manifest.json"]
    signature = _source_signature(paper_root=paper_root, source_root=source_root, relative_paths=relative_paths)
    return study_root, paper_root, source_root, signature, relative_paths


def test_canonical_source_with_matching_signatures_passes(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_runtime_proof")
    study_root, paper_root, source_root, signature, relative_paths = _canonical_study(tmp_path)
    manifest_path = _write_manifest(
        study_root,
        source_signature=signature,
        source_root=source_root,
        paper_root=paper_root,
        relative_paths=relative_paths,
    )

    proof = module.build_artifact_runtime_proof(study_root)

    assert proof["surface"] == "artifact_runtime_proof"
    assert proof["schema_version"] == 1
    assert proof["rebuild_status"] == "current"
    assert proof["current_package_from_canonical_source"] is True
    assert proof["blockers"] == []
    assert proof["refs"]["delivery_manifest_path"] == str(manifest_path.resolve())
    assert proof["refs"]["controller_authorized_package_source_root"] == str(source_root.resolve())
    assert proof["refs"]["source_signature"] == signature
    assert proof["refs"]["authority_source_signature"] == signature
    assert proof["authority"]["proof_can_authorize_scientific_quality"] is False
    assert proof["authority"]["derived_artifact_can_authorize_submission"] is False
    assert proof["authority"]["derived_artifact_can_be_quality_authority"] is False


def test_missing_manifest_fails_closed(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_runtime_proof")
    study_root = tmp_path / "study"

    proof = module.build_artifact_runtime_proof(study_root)

    assert proof["rebuild_status"] == "blocked"
    assert proof["current_package_from_canonical_source"] is False
    assert proof["blockers"] == [{"code": "delivery_manifest_missing"}]
    assert proof["refs"]["delivery_manifest_path"] == str((study_root / "manuscript" / "delivery_manifest.json").resolve())


def test_signature_drift_fails_closed(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_runtime_proof")
    study_root, paper_root, source_root, signature, relative_paths = _canonical_study(tmp_path)
    _write_manifest(
        study_root,
        source_signature=signature,
        source_root=source_root,
        paper_root=paper_root,
        relative_paths=relative_paths,
    )
    _write_text(source_root / "manuscript.md", "# Manuscript\n\nCanonical source drifted.\n")

    proof = module.build_artifact_runtime_proof(study_root)

    assert proof["rebuild_status"] == "blocked"
    assert proof["current_package_from_canonical_source"] is False
    assert {blocker["code"] for blocker in proof["blockers"]} == {"source_signature_mismatch"}
    assert proof["refs"]["authority_source_signature"] == signature
    assert proof["refs"]["source_signature"] != signature


def test_blocking_refs_fail_closed(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_runtime_proof")
    study_root, paper_root, source_root, signature, relative_paths = _canonical_study(tmp_path)
    blocking_refs = [
        {
            "blocker": "stale_study_delivery_mirror",
            "artifact_path": str(study_root / "manuscript" / "delivery_manifest.json"),
        }
    ]
    _write_manifest(
        study_root,
        source_signature=signature,
        source_root=source_root,
        paper_root=paper_root,
        relative_paths=relative_paths,
        blocking_artifact_refs=blocking_refs,
    )

    proof = module.build_artifact_runtime_proof(study_root)

    assert proof["rebuild_status"] == "blocked"
    assert proof["current_package_from_canonical_source"] is False
    assert proof["blockers"] == [
        {
            "code": "blocking_artifact_refs_present",
            "blocking_artifact_refs": blocking_refs,
        }
    ]
    assert proof["refs"]["blocking_artifact_refs"] == blocking_refs


def test_missing_controller_authorized_package_source_root_fails_closed(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_runtime_proof")
    study_root, paper_root, source_root, signature, relative_paths = _canonical_study(tmp_path)
    manifest_path = _write_manifest(
        study_root,
        source_signature=signature,
        source_root=source_root,
        paper_root=paper_root,
        relative_paths=relative_paths,
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["surface_roles"].pop("controller_authorized_package_source_root")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    proof = module.build_artifact_runtime_proof(study_root)

    assert proof["rebuild_status"] == "blocked"
    assert proof["current_package_from_canonical_source"] is False
    assert proof["blockers"] == [{"code": "controller_authorized_package_source_root_missing"}]


def test_authority_states_proof_cannot_authorize_scientific_quality(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_runtime_proof")
    study_root, paper_root, source_root, signature, relative_paths = _canonical_study(tmp_path)
    _write_manifest(
        study_root,
        source_signature=signature,
        source_root=source_root,
        paper_root=paper_root,
        relative_paths=relative_paths,
    )

    proof = module.build_artifact_runtime_proof(str(study_root))

    assert proof["authority"] == {
        "proof_can_authorize_scientific_quality": False,
        "scientific_quality_authority": "publication_eval_and_controller_decisions",
        "derived_artifact_can_authorize_submission": False,
        "derived_artifact_can_be_quality_authority": False,
        "derived_artifact_can_be_edit_source": False,
    }
