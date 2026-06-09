from __future__ import annotations

import importlib
import json
from pathlib import Path


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_restore_index_detail_retention_moves_large_verified_detail_arrays(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.restore_index_detail_retention")
    root = tmp_path / "quest" / "artifacts" / "runtime" / "runtime_storage_maintenance" / "restore_proof_archives"
    detail_entries = [
        {
            "path": f"runs/run-{index:04d}/stdout.jsonl",
            "entry_type": "file",
            "size_bytes": 128,
            "sha256": f"{index:064x}"[-64:],
        }
        for index in range(512)
    ]
    proof_path = root / "runtime_bucket_compaction" / "archive.restore_proof.json"
    _write_json(
        proof_path,
        {
            "surface_kind": "runtime_restore_proof",
            "status": "verified",
            "archive_sha256": "a" * 64,
            "source_file_count": len(detail_entries),
            "verified_file_count": len(detail_entries),
            "verified_entries": detail_entries,
            "errors": [],
        },
    )
    original_bytes = proof_path.stat().st_size

    planned = module.run_restore_index_detail_retention(
        root=root,
        apply=False,
        cold_store_root=tmp_path / "cold-store",
        min_mb=0,
    )

    assert planned["status"] == "planned"
    assert planned["candidate_count"] == 1
    assert "verified_entries" in json.loads(proof_path.read_text(encoding="utf-8"))

    applied = module.run_restore_index_detail_retention(
        root=root,
        apply=True,
        cold_store_root=tmp_path / "cold-store",
        min_mb=0,
    )

    assert applied["status"] == "applied"
    assert applied["moved_count"] == 1
    assert applied["actual_release_bytes"] > 0
    slim = json.loads(proof_path.read_text(encoding="utf-8"))
    assert slim["status"] == "verified"
    assert slim["source_file_count"] == len(detail_entries)
    assert slim["verified_file_count"] == len(detail_entries)
    assert "verified_entries" not in slim
    assert slim["detail_retention"]["detail_counts"] == {"verified_entries": len(detail_entries)}
    assert slim["detail_retention"]["body_included"] is False
    assert proof_path.stat().st_size < original_bytes
    ref_path = Path(str(proof_path) + ".detail_ref.json")
    assert ref_path.is_file()
    ref = json.loads(ref_path.read_text(encoding="utf-8"))
    cold_object = Path(ref["cold_object_path"])
    assert cold_object.is_file()
    detail = json.loads(cold_object.read_text(encoding="utf-8"))
    assert len(detail["detail"]["verified_entries"]) == len(detail_entries)


def test_restore_index_detail_retention_cli_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_run_restore_index_detail_retention(
        *,
        root: Path,
        apply: bool,
        cold_store_root: Path,
        min_mb: int,
        max_files: int | None,
    ) -> dict[str, object]:
        called["root"] = root
        called["apply"] = apply
        called["cold_store_root"] = cold_store_root
        called["min_mb"] = min_mb
        called["max_files"] = max_files
        return {"surface_kind": "restore_index_detail_retention", "status": "applied"}

    monkeypatch.setattr(
        cli.restore_index_detail_retention,
        "run_restore_index_detail_retention",
        fake_run_restore_index_detail_retention,
    )

    exit_code = cli.main(
        [
            "restore-index-detail-retention",
            "--root",
            str(tmp_path / "restore-index"),
            "--apply",
            "--cold-store-root",
            str(tmp_path / "cold-store"),
            "--min-mb",
            "2",
            "--max-files",
            "7",
        ]
    )

    assert exit_code == 0
    assert called == {
        "root": tmp_path / "restore-index",
        "apply": True,
        "cold_store_root": tmp_path / "cold-store",
        "min_mb": 2,
        "max_files": 7,
    }
    assert json.loads(capsys.readouterr().out)["status"] == "applied"
