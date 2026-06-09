from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path


def test_cold_store_reference_audit_deletes_only_unreferenced_cold_objects(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.cold_store_reference_audit")
    cold_store = tmp_path / "cold-store"
    referenced = cold_store / "Study" / "objects" / "aa" / "referenced.json"
    orphan = cold_store / "Study" / "objects" / "bb" / "orphan.json"
    referenced.parent.mkdir(parents=True, exist_ok=True)
    orphan.parent.mkdir(parents=True, exist_ok=True)
    referenced.write_text('{"keep": true}', encoding="utf-8")
    orphan.write_text('{"delete": true}', encoding="utf-8")
    workspace = tmp_path / "workspace"
    ref = workspace / "runtime" / "artifacts" / "historical_body_retention" / "latest.json"
    ref.parent.mkdir(parents=True, exist_ok=True)
    ref.write_text(json.dumps({"cold_object_path": str(referenced)}), encoding="utf-8")

    planned = module.run_cold_store_reference_audit(
        root=cold_store,
        reference_roots=(workspace, cold_store),
        apply=False,
        min_mb=0,
    )

    assert planned["status"] == "planned"
    assert planned["orphan_candidate_count"] == 1
    assert planned["candidate_samples"][0]["path"] == str(orphan)
    assert referenced.is_file()
    assert orphan.is_file()

    applied = module.run_cold_store_reference_audit(
        root=cold_store,
        reference_roots=(workspace, cold_store),
        apply=True,
        min_mb=0,
    )

    assert applied["status"] == "applied"
    assert applied["deleted_count"] == 1
    assert applied["actual_release_bytes"] == len('{"delete": true}')
    assert referenced.is_file()
    assert not orphan.exists()
    assert Path(applied["latest_receipt_path"]).is_file()


def test_cold_store_reference_audit_blocks_changed_candidate_before_delete(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.cold_store_reference_audit")
    cold_store = tmp_path / "cold-store"
    orphan = cold_store / "Study" / "objects" / "bb" / "orphan.json"
    orphan.parent.mkdir(parents=True, exist_ok=True)
    orphan.write_text('{"delete": true}', encoding="utf-8")
    original_sha = _sha256(orphan)
    stale_candidate = {
        "status": "candidate",
        "path": str(orphan),
        "bytes": orphan.stat().st_size,
        "sha256": original_sha,
        "reason": "not_referenced_by_any_scanned_cold_ref",
    }
    orphan.write_text('{"changed": true}', encoding="utf-8")

    def fake_orphan_candidates(*, root: Path, refs: set[str]) -> list[dict[str, object]]:
        return [stale_candidate]

    monkeypatch.setattr(module, "_orphan_candidates", fake_orphan_candidates)

    applied = module.run_cold_store_reference_audit(root=cold_store, reference_roots=(cold_store,), apply=True, min_mb=0)

    assert applied["status"] == "blocked"
    assert applied["deleted_count"] == 0
    assert orphan.is_file()


def test_cold_store_reference_audit_cli_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_run_cold_store_reference_audit(
        *,
        root: Path,
        reference_roots: tuple[Path, ...],
        apply: bool,
        min_mb: int,
        max_objects: int | None,
    ) -> dict[str, object]:
        called["root"] = root
        called["reference_roots"] = reference_roots
        called["apply"] = apply
        called["min_mb"] = min_mb
        called["max_objects"] = max_objects
        return {"surface_kind": "cold_store_reference_audit", "status": "planned"}

    monkeypatch.setattr(
        cli.cold_store_reference_audit,
        "run_cold_store_reference_audit",
        fake_run_cold_store_reference_audit,
    )

    exit_code = cli.main(
        [
            "cold-store-reference-audit",
            "--root",
            str(tmp_path / "cold-store"),
            "--reference-root",
            str(tmp_path / "workspace"),
            "--dry-run",
            "--min-mb",
            "10",
            "--max-objects",
            "2",
        ]
    )

    assert exit_code == 0
    assert called == {
        "root": tmp_path / "cold-store",
        "reference_roots": (tmp_path / "workspace",),
        "apply": False,
        "min_mb": 10,
        "max_objects": 2,
    }
    assert json.loads(capsys.readouterr().out)["status"] == "planned"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
