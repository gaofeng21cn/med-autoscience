from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path


def test_cold_store_dedupe_hardlinks_duplicate_objects_without_rewriting_refs(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.cold_store_dedupe")
    cold_store = tmp_path / "cold-store"
    first = cold_store / "DM-CVD" / "objects" / "aa" / "body-a.tar.gz"
    second = cold_store / "002-study" / "objects" / "bb" / "body-b.tar.gz"
    first.parent.mkdir(parents=True, exist_ok=True)
    second.parent.mkdir(parents=True, exist_ok=True)
    payload = b"duplicated cold body\n" * 1024
    first.write_bytes(payload)
    second.write_bytes(payload)
    ref_path = cold_store / "002-study" / "body-b.tar.gz.cold_ref.json"
    ref_payload = {"cold_object_path": str(second), "original_sha256": _sha256(second)}
    ref_path.write_text(json.dumps(ref_payload, sort_keys=True), encoding="utf-8")

    planned = module.run_cold_store_dedupe(root=cold_store, apply=False, min_mb=0)

    assert planned["status"] == "planned"
    assert planned["duplicate_group_count"] == 1
    assert planned["hardlinked_count"] == 0
    assert os.stat(first).st_ino != os.stat(second).st_ino

    applied = module.run_cold_store_dedupe(root=cold_store, apply=True, min_mb=0)

    assert applied["status"] == "applied"
    assert applied["hardlinked_count"] == 1
    assert applied["actual_logical_release_bytes"] == len(payload)
    assert first.read_bytes() == payload
    assert second.read_bytes() == payload
    assert os.stat(first).st_ino == os.stat(second).st_ino
    assert json.loads(ref_path.read_text(encoding="utf-8")) == ref_payload
    assert Path(applied["latest_receipt_path"]).is_file()


def test_cold_store_dedupe_keeps_same_size_different_hash_files(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.cold_store_dedupe")
    cold_store = tmp_path / "cold-store"
    first = cold_store / "A" / "objects" / "aa" / "body-a.json"
    second = cold_store / "B" / "objects" / "bb" / "body-b.json"
    first.parent.mkdir(parents=True, exist_ok=True)
    second.parent.mkdir(parents=True, exist_ok=True)
    first.write_bytes(b"a" * 4096)
    second.write_bytes(b"b" * 4096)

    result = module.run_cold_store_dedupe(root=cold_store, apply=True, min_mb=0)

    assert result["status"] == "nothing_to_dedupe"
    assert result["duplicate_group_count"] == 0
    assert os.stat(first).st_ino != os.stat(second).st_ino


def test_cold_store_dedupe_cli_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_run_cold_store_dedupe(
        *,
        root: Path,
        apply: bool,
        min_mb: int,
        max_groups: int | None,
    ) -> dict[str, object]:
        called["root"] = root
        called["apply"] = apply
        called["min_mb"] = min_mb
        called["max_groups"] = max_groups
        return {"surface_kind": "cold_store_dedupe", "status": "applied"}

    monkeypatch.setattr(cli.cold_store_dedupe, "run_cold_store_dedupe", fake_run_cold_store_dedupe)

    exit_code = cli.main(
        [
            "cold-store-dedupe",
            "--root",
            str(tmp_path / "cold-store"),
            "--apply",
            "--min-mb",
            "50",
            "--max-groups",
            "3",
        ]
    )

    assert exit_code == 0
    assert called == {
        "root": tmp_path / "cold-store",
        "apply": True,
        "min_mb": 50,
        "max_groups": 3,
    }
    assert json.loads(capsys.readouterr().out)["status"] == "applied"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
