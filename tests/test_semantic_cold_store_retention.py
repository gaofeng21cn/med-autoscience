from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path


def test_semantic_cold_store_retention_plans_referenced_raw_body(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.semantic_cold_store_retention")
    cold_store = tmp_path / "cold-store"
    raw = cold_store / "Study" / "objects" / "aa" / "raw.tar.gz"
    raw.parent.mkdir(parents=True, exist_ok=True)
    raw.write_bytes(b"legacy raw restore body" * 1024)
    workspace = tmp_path / "workspace"
    ref = workspace / "runtime" / "artifacts" / "historical_body_retention" / "latest.json"
    ref.parent.mkdir(parents=True, exist_ok=True)
    ref.write_text(
        json.dumps(
            {
                "surface_kind": "legacy_ds_cold_archive_body_ref",
                "cold_object_path": str(raw),
                "original_sha256": _sha256(raw),
                "original_bytes": raw.stat().st_size,
                "workspace_relative_path": "runtime/archive/legacy_ds.tar.gz",
            }
        ),
        encoding="utf-8",
    )

    planned = module.run_semantic_cold_store_retention(
        root=cold_store,
        reference_roots=(workspace,),
        apply=False,
        retire_exact_raw_restore=False,
        min_mb=0,
    )

    assert planned["status"] == "planned"
    assert planned["candidate_count"] == 1
    assert planned["restore_policy"]["byte_for_byte_restore_of_legacy_raw_body"] is False
    assert planned["candidate_samples"][0]["reference_count"] == 1
    assert raw.read_bytes().startswith(b"legacy raw restore body")


def test_semantic_cold_store_retention_apply_requires_explicit_policy_flag(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.semantic_cold_store_retention")
    cold_store, workspace, raw = _semantic_fixture(tmp_path)

    result = module.run_semantic_cold_store_retention(
        root=cold_store,
        reference_roots=(workspace,),
        apply=True,
        retire_exact_raw_restore=False,
        min_mb=0,
    )

    assert result["status"] == "blocked"
    assert result["blocker_samples"][0]["reason"] == "--retire-exact-raw-restore is required with --apply"
    assert raw.read_bytes().startswith(b"legacy raw restore body")
    assert Path(result["latest_receipt_path"]).is_file()


def test_semantic_cold_store_retention_replaces_raw_body_with_capsule_ref(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.semantic_cold_store_retention")
    cold_store, workspace, raw = _semantic_fixture(tmp_path)
    original_sha = _sha256(raw)
    original_bytes = raw.stat().st_size

    result = module.run_semantic_cold_store_retention(
        root=cold_store,
        reference_roots=(workspace,),
        apply=True,
        retire_exact_raw_restore=True,
        min_mb=0,
    )

    assert result["status"] == "applied"
    assert result["replaced_count"] == 1
    assert result["actual_release_bytes"] > 0
    replacement = json.loads(raw.read_text(encoding="utf-8"))
    assert replacement["surface_kind"] == "semantic_cold_store_retention_ref"
    assert replacement["original_sha256"] == original_sha
    assert replacement["original_bytes"] == original_bytes
    assert replacement["restore_policy"]["byte_for_byte_restore_of_legacy_raw_body"] is False
    capsule = json.loads(Path(replacement["semantic_capsule_path"]).read_text(encoding="utf-8"))
    assert capsule["surface_kind"] == "semantic_cold_store_capsule"
    assert capsule["source_sha256"] == original_sha
    assert capsule["source_bytes"] == original_bytes
    ref = json.loads((workspace / "ref.json").read_text(encoding="utf-8"))
    assert ref["cold_object_path"] == str(raw)
    assert ref["restore_command"] is None
    assert ref["semantic_restore_policy"]["status"] == "exact_raw_restore_retired"
    assert ref["semantic_restore_policy"]["semantic_capsule_path"] == replacement["semantic_capsule_path"]


def test_semantic_cold_store_retention_accepts_reference_file_list(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.semantic_cold_store_retention")
    cold_store, workspace, raw = _semantic_fixture(tmp_path)
    ref_list = tmp_path / "refs.txt"
    ref_list.write_text(str(workspace / "ref.json") + "\n", encoding="utf-8")

    planned = module.run_semantic_cold_store_retention(
        root=cold_store,
        reference_roots=(),
        reference_file_lists=(ref_list,),
        apply=False,
        retire_exact_raw_restore=False,
        min_mb=0,
    )

    assert planned["status"] == "planned"
    assert planned["reference_file_lists"] == [str(ref_list.resolve())]
    assert planned["candidate_samples"][0]["path"] == str(raw)


def test_semantic_cold_store_retention_dry_run_uses_ref_digest_without_rehash(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.semantic_cold_store_retention")
    cold_store, workspace, raw = _semantic_fixture(tmp_path)

    def fail_sha256(path: Path) -> str:
        raise AssertionError(f"dry-run should not rehash {path}")

    monkeypatch.setattr(module, "_sha256", fail_sha256)

    planned = module.run_semantic_cold_store_retention(
        root=cold_store,
        reference_roots=(workspace,),
        apply=False,
        retire_exact_raw_restore=False,
        min_mb=0,
    )

    assert planned["status"] == "planned"
    assert planned["candidate_samples"][0]["sha256"] == json.loads((workspace / "ref.json").read_text())[
        "original_sha256"
    ]
    assert planned["candidate_samples"][0]["observed_size_bytes"] == raw.stat().st_size


def test_semantic_cold_store_retention_dry_run_blocks_missing_ref_digest_without_rehash(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.semantic_cold_store_retention")
    cold_store, workspace, raw = _semantic_fixture(tmp_path)
    ref_path = workspace / "ref.json"
    payload = json.loads(ref_path.read_text(encoding="utf-8"))
    payload.pop("original_sha256")
    payload.pop("sha256", None)
    ref_path.write_text(json.dumps(payload), encoding="utf-8")

    def fail_sha256(path: Path) -> str:
        raise AssertionError(f"dry-run should not rehash missing digest object {path}")

    monkeypatch.setattr(module, "_sha256", fail_sha256)

    planned = module.run_semantic_cold_store_retention(
        root=cold_store,
        reference_roots=(workspace,),
        apply=False,
        retire_exact_raw_restore=False,
        min_mb=0,
    )

    assert planned["status"] == "nothing_to_retain"
    assert planned["blocker_samples"][0]["status"] == "blocked_missing_ref_sha256"
    assert planned["blocker_samples"][0]["path"] == str(raw)


def test_semantic_cold_store_retention_dry_run_does_not_parse_large_json_body(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.semantic_cold_store_retention")
    cold_store = tmp_path / "cold-store"
    raw = cold_store / "Study" / "objects" / "aa" / "raw.json"
    raw.parent.mkdir(parents=True, exist_ok=True)
    raw.write_text("x" * (1024 * 1024 + 1), encoding="utf-8")
    workspace = tmp_path / "workspace"
    ref = workspace / "ref.json"
    ref.parent.mkdir(parents=True, exist_ok=True)
    ref.write_text(
        json.dumps(
            {
                "surface_kind": "historical_body_cold_ref",
                "cold_object_path": str(raw),
                "original_sha256": "ref-sha",
                "original_bytes": raw.stat().st_size,
            }
        ),
        encoding="utf-8",
    )

    original_read_text = Path.read_text

    def guarded_read_text(self: Path, *args, **kwargs) -> str:
        if self == raw:
            raise AssertionError("dry-run should not read large cold json body")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded_read_text)

    planned = module.run_semantic_cold_store_retention(
        root=cold_store,
        reference_roots=(workspace,),
        apply=False,
        retire_exact_raw_restore=False,
        min_mb=0,
    )

    assert planned["status"] == "planned"
    assert planned["candidate_samples"][0]["path"] == str(raw)


def test_semantic_cold_store_retention_skips_retired_ref_even_with_non_json_suffix(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.semantic_cold_store_retention")
    cold_store = tmp_path / "cold-store"
    raw = cold_store / "Study" / "objects" / "aa" / "raw.log"
    raw.parent.mkdir(parents=True, exist_ok=True)
    raw.write_text(
        json.dumps(
            {
                "surface_kind": "semantic_cold_store_retention_ref",
                "status": "exact_raw_body_retired",
                "original_sha256": "old-sha",
                "original_bytes": 123,
            }
        ),
        encoding="utf-8",
    )
    workspace = tmp_path / "workspace"
    ref = workspace / "ref.json"
    ref.parent.mkdir(parents=True, exist_ok=True)
    ref.write_text(
        json.dumps(
            {
                "surface_kind": "historical_body_cold_ref",
                "cold_object_path": str(raw),
                "original_sha256": "old-sha",
                "original_bytes": 123,
            }
        ),
        encoding="utf-8",
    )

    planned = module.run_semantic_cold_store_retention(
        root=cold_store,
        reference_roots=(workspace,),
        apply=False,
        retire_exact_raw_restore=False,
        min_mb=0,
    )

    assert planned["status"] == "nothing_to_retain"
    assert planned["candidate_count"] == 0


def test_semantic_cold_store_retention_cli_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_run_semantic_cold_store_retention(
        *,
        root: Path,
        reference_roots: tuple[Path, ...],
        apply: bool,
        retire_exact_raw_restore: bool,
        min_mb: int,
        max_objects: int | None,
        reference_file_lists: tuple[Path, ...],
    ) -> dict[str, object]:
        called["root"] = root
        called["reference_roots"] = reference_roots
        called["apply"] = apply
        called["retire_exact_raw_restore"] = retire_exact_raw_restore
        called["min_mb"] = min_mb
        called["max_objects"] = max_objects
        called["reference_file_lists"] = reference_file_lists
        return {"surface_kind": "semantic_cold_store_retention", "status": "planned"}

    monkeypatch.setattr(
        cli.semantic_cold_store_retention,
        "run_semantic_cold_store_retention",
        fake_run_semantic_cold_store_retention,
    )

    exit_code = cli.main(
        [
            "semantic-cold-store-retention",
            "--root",
            str(tmp_path / "cold-store"),
            "--reference-root",
            str(tmp_path / "workspace"),
            "--reference-file-list",
            str(tmp_path / "refs.txt"),
            "--dry-run",
            "--retire-exact-raw-restore",
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
        "retire_exact_raw_restore": True,
        "min_mb": 10,
        "max_objects": 2,
        "reference_file_lists": (tmp_path / "refs.txt",),
    }
    assert json.loads(capsys.readouterr().out)["status"] == "planned"


def _semantic_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    cold_store = tmp_path / "cold-store"
    raw = cold_store / "Study" / "objects" / "aa" / "raw.tar.gz"
    raw.parent.mkdir(parents=True, exist_ok=True)
    raw.write_bytes(b"legacy raw restore body" * 1024)
    workspace = tmp_path / "workspace"
    ref = workspace / "ref.json"
    ref.parent.mkdir(parents=True, exist_ok=True)
    ref.write_text(
        json.dumps(
            {
                "surface_kind": "legacy_ds_cold_archive_body_ref",
                "cold_object_path": str(raw),
                "original_sha256": _sha256(raw),
                "original_bytes": raw.stat().st_size,
                "restore_command": f"cp {raw} restored.tar.gz",
            }
        ),
        encoding="utf-8",
    )
    return cold_store, workspace, raw


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
