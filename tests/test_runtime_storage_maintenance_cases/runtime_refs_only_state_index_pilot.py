from __future__ import annotations

from tests.test_runtime_storage_maintenance_cases.runtime_storage_maintenance_helpers import *


def test_refs_only_state_index_pilot_indexes_small_runtime_refs_without_bodies(tmp_path: Path) -> None:
    state_index = importlib.import_module("med_autoscience.runtime_protocol.refs_only_state_index_pilot")
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    quest_id = "quest-001"
    study_root = profile.studies_root / study_id
    quest_root = profile.runtime_root / quest_id
    _write_study(study_root, study_id=study_id, quest_id=quest_id)
    _write_quest(quest_root, quest_id=quest_id, status="stopped")
    _write_refs_only_pilot_fixture(study_root=study_root, quest_root=quest_root)

    result = state_index.rebuild_refs_only_state_index(
        workspace_root=profile.workspace_root,
        study_root=study_root,
        quest_root=quest_root,
    )

    assert result["surface_kind"] == "mas_runtime_refs_only_state_index_pilot"
    assert result["status"] == "indexed"
    assert result["authority_boundary"] == {
        "sqlite_role": "rebuildable_refs_only_sidecar_index",
        "body_included": False,
        "stores_study_truth": False,
        "stores_manuscript_body": False,
        "stores_artifact_body": False,
        "stores_owner_receipt_body": False,
        "sqlite_record_counts_as_stage_complete": False,
        "generic_state_index_owner": "one-person-lab",
    }
    assert result["indexed_count"] == 6
    assert result["skipped_forbidden_count"] == 2
    assert result["skipped_forbidden_refs_inlined"] is False
    assert result["skipped_forbidden_ref_sample_count"] == 2
    assert result["family_counts"] == {
        "cursor": 1,
        "index": 1,
        "lifecycle": 1,
        "outbox": 1,
        "receipt_ref": 2,
    }
    assert result["sqlite_ref"]["workspace_relative_path"] == (
        "artifacts/runtime/mas_refs_only_state_index_pilot.sqlite"
    )
    assert len(result["skipped_forbidden_ref_sample"]) == 2

    db_path = Path(result["sqlite_ref"]["db_path"])
    assert db_path.is_file()
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT ref_family, source_ref, payload_role, body_included, content_hash
            FROM small_file_refs
            ORDER BY source_ref
            """
        ).fetchall()
        metadata = dict(conn.execute("SELECT key, value FROM state_index_metadata").fetchall())

    assert len(rows) == 6
    assert metadata["surface_kind"] == "mas_runtime_refs_only_state_index_pilot"
    assert metadata["body_included"] == "false"
    assert all(row[2] == "ref_metadata_only" for row in rows)
    assert all(row[3] == 0 for row in rows)
    assert all(len(row[4]) == 64 for row in rows)
    source_refs = {row[1] for row in rows}
    assert {
        "runtime/quests/quest-001/.ds/runtime_state.json",
        "studies/001-risk/artifacts/runtime/owner_route/latest.json",
        "studies/001-risk/artifacts/runtime/opl_family_domain_handler/dispatch_receipts/dispatch-001.json",
        "studies/001-risk/artifacts/runtime/paper_work_unit_outbox/receipts.jsonl",
        "studies/001-risk/artifacts/runtime/cursors/owner-route.cursor.json",
        "studies/001-risk/artifacts/runtime/indexes/stage_artifact_index.json",
    } == source_refs
    sqlite_text = "\n".join("|".join(str(cell) for cell in row) for row in rows)
    assert "OWNER_RECEIPT_BODY_MUST_NOT_ENTER_SQLITE" not in sqlite_text
    assert "PUBLICATION_TRUTH_MUST_NOT_ENTER_SQLITE" not in sqlite_text
    assert "MANUSCRIPT_BODY_MUST_NOT_ENTER_SQLITE" not in sqlite_text


def test_refs_only_state_index_pilot_prefers_canonical_runtime_state_surface(tmp_path: Path) -> None:
    state_index = importlib.import_module("med_autoscience.runtime_protocol.refs_only_state_index_pilot")
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    quest_id = "quest-001"
    study_root = profile.studies_root / study_id
    quest_root = profile.runtime_root / quest_id
    _write_study(study_root, study_id=study_id, quest_id=quest_id)
    _write_quest(quest_root, quest_id=quest_id, status="paused")
    canonical = quest_root / "artifacts" / "runtime" / "state" / "runtime_state.json"
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_text(
        json.dumps({"quest_id": quest_id, "status": "paused", "active_run_id": None}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    result = state_index.rebuild_refs_only_state_index(
        workspace_root=profile.workspace_root,
        study_root=study_root,
        quest_root=quest_root,
    )

    assert result["family_counts"] == {
        "legacy_lifecycle": 1,
        "lifecycle": 1,
    }
    db_path = Path(result["sqlite_ref"]["db_path"])
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT ref_family, source_ref, body_included
            FROM small_file_refs
            ORDER BY ref_family, source_ref
            """
        ).fetchall()

    assert rows == [
        ("legacy_lifecycle", "runtime/quests/quest-001/.ds/runtime_state.json", 0),
        ("lifecycle", "runtime/quests/quest-001/artifacts/runtime/state/runtime_state.json", 0),
    ]


def test_refs_only_state_index_pilot_replaces_only_current_quest_slice(tmp_path: Path) -> None:
    state_index = importlib.import_module("med_autoscience.runtime_protocol.refs_only_state_index_pilot")
    profile = make_profile(tmp_path)
    study_a = profile.studies_root / "001-risk"
    study_b = profile.studies_root / "002-risk"
    quest_a = profile.runtime_root / "quest-001"
    quest_b = profile.runtime_root / "quest-002"
    _write_study(study_a, study_id="001-risk", quest_id="quest-001")
    _write_study(study_b, study_id="002-risk", quest_id="quest-002")
    _write_quest(quest_a, quest_id="quest-001", status="paused")
    _write_quest(quest_b, quest_id="quest-002", status="paused")

    first = state_index.rebuild_refs_only_state_index(
        workspace_root=profile.workspace_root,
        study_root=study_a,
        quest_root=quest_a,
    )
    second = state_index.rebuild_refs_only_state_index(
        workspace_root=profile.workspace_root,
        study_root=study_b,
        quest_root=quest_b,
    )

    assert first["indexed_count"] == 1
    assert first["sqlite_total_indexed_count"] == 1
    assert second["indexed_count"] == 1
    assert second["sqlite_total_indexed_count"] == 2
    db_path = Path(second["sqlite_ref"]["db_path"])
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT quest_root, source_ref
            FROM small_file_refs
            ORDER BY source_ref
            """
        ).fetchall()

    assert rows == [
        (str(quest_a.resolve()), "runtime/quests/quest-001/.ds/runtime_state.json"),
        (str(quest_b.resolve()), "runtime/quests/quest-002/.ds/runtime_state.json"),
    ]


def test_maintain_runtime_storage_can_write_refs_only_state_index_pilot_summary(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    _write_fake_mds_repo(profile.med_deepscientist_repo_root)
    study_id = "001-risk"
    quest_id = "quest-001"
    study_root = profile.studies_root / study_id
    quest_root = profile.runtime_root / quest_id
    _write_study(study_root, study_id=study_id, quest_id=quest_id)
    _write_quest(quest_root, quest_id=quest_id, status="stopped")
    _write_refs_only_pilot_fixture(study_root=study_root, quest_root=quest_root)

    result = module.maintain_runtime_storage(
        profile=profile,
        study_id=study_id,
        study_root=None,
        refs_only_state_index_pilot=True,
    )

    assert result["status"] == "maintained"
    pilot = result["refs_only_state_index_pilot"]
    assert pilot["status"] == "indexed"
    assert pilot["indexed_count"] == 7
    assert pilot["authority_boundary"]["body_included"] is False
    assert pilot["stage_folder_attempt_projection"] == {
        "surface_kind": "opl_stage_folder_attempt_projection_evidence",
        "projection_role": "refs_only_attempt_read_model_evidence",
        "source_of_truth": "physical_stage_folder_manifest_receipt_refs",
        "stage_completion_signal": False,
        "body_included": False,
        "attempt_root_ref": "runtime/quests/quest-001",
        "indexed_ref_families": {
            "cursor": 1,
            "index": 1,
            "legacy_lifecycle": 1,
            "lifecycle": 1,
            "outbox": 1,
            "receipt_ref": 2,
        },
        "sqlite_summary_ref": "artifacts/runtime/mas_refs_only_state_index_pilot.sqlite",
    }
    sqlite_no_body_proof = pilot["sqlite_no_body_proof"]
    assert sqlite_no_body_proof["schema_columns_forbid_body"] is True
    assert sqlite_no_body_proof["body_column_present"] is False
    assert sqlite_no_body_proof["body_included_values"] == [0]
    assert sqlite_no_body_proof["forbidden_body_marker_found"] is False
    assert sqlite_no_body_proof["checked_forbidden_marker_roles"] == [
        "owner_receipt_body_fixture",
        "publication_truth_body_fixture",
        "manuscript_body_fixture",
    ]
    assert Path(pilot["sqlite_ref"]["db_path"]).is_file()
    latest_payload = json.loads(Path(result["latest_report_path"]).read_text(encoding="utf-8"))
    assert latest_payload["refs_only_state_index_pilot"]["sqlite_ref"]["workspace_relative_path"] == (
        "artifacts/runtime/mas_refs_only_state_index_pilot.sqlite"
    )
    assert "OWNER_RECEIPT_BODY_MUST_NOT_ENTER_SQLITE" not in json.dumps(
        latest_payload["refs_only_state_index_pilot"],
        ensure_ascii=False,
    )


def test_refs_only_state_index_pilot_runs_when_legacy_backend_is_unavailable(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    quest_id = "quest-001"
    study_root = profile.studies_root / study_id
    quest_root = profile.runtime_root / quest_id
    _write_study(study_root, study_id=study_id, quest_id=quest_id)
    _write_quest(quest_root, quest_id=quest_id, status="paused")
    _write_refs_only_pilot_fixture(study_root=study_root, quest_root=quest_root)

    result = module.maintain_runtime_storage(
        profile=profile,
        study_id=study_id,
        study_root=None,
        refs_only_state_index_pilot=True,
        include_worktrees=False,
        dedupe_worktree_min_mb=None,
        slim_jsonl_threshold_mb=None,
    )

    assert result["status"] == "maintained"
    assert result["legacy_backend_status"] == "blocked_backend_unavailable"
    assert result["summary"] == "refs-only state index pilot 已完成；legacy backend storage maintenance 当前不可用。"
    pilot = result["refs_only_state_index_pilot"]
    assert pilot["status"] == "indexed"
    assert pilot["indexed_count"] == 7
    assert pilot["stage_folder_attempt_projection"]["attempt_root_ref"] == "runtime/quests/quest-001"
    assert pilot["sqlite_no_body_proof"]["forbidden_body_marker_found"] is False
    latest_payload = json.loads(Path(result["latest_report_path"]).read_text(encoding="utf-8"))
    assert latest_payload["legacy_backend_status"] == "blocked_backend_unavailable"
    assert latest_payload["refs_only_state_index_pilot"]["status"] == "indexed"


def test_refs_only_state_index_only_skips_legacy_backend(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    quest_id = "quest-001"
    study_root = profile.studies_root / study_id
    quest_root = profile.runtime_root / quest_id
    _write_study(study_root, study_id=study_id, quest_id=quest_id)
    _write_quest(quest_root, quest_id=quest_id, status="paused")
    _write_refs_only_pilot_fixture(study_root=study_root, quest_root=quest_root)
    called = {"backend": False}

    def fail_if_backend_runs(**_: object) -> None:
        called["backend"] = True
        raise AssertionError("legacy backend must not run in refs-only state index only mode")

    def fail_if_size_scan_runs(_: Path) -> int:
        raise AssertionError("recursive size scan must not run in refs-only state index only mode")

    monkeypatch.setattr(module.backend_maintenance, "run_quest_storage_maintenance", fail_if_backend_runs)
    monkeypatch.setattr(module, "_directory_size_bytes", fail_if_size_scan_runs)

    result = module.maintain_runtime_storage(
        profile=profile,
        study_id=study_id,
        study_root=None,
        refs_only_state_index_pilot=True,
        refs_only_state_index_only=True,
        include_worktrees=False,
        dedupe_worktree_min_mb=None,
        slim_jsonl_threshold_mb=None,
    )

    assert called["backend"] is False
    assert result["status"] == "maintained"
    assert result["legacy_backend_status"] == "skipped_by_refs_only_state_index_only"
    assert result["size_before"] == {
        "root": str(quest_root / ".ds"),
        "status": "skipped",
        "skip_reason": "refs_only_state_index_only",
        "total_bytes": None,
        "lightweight_buckets": [],
        "buckets": {},
    }
    assert result["size_after"] == result["size_before"]
    assert result["refs_only_state_index_pilot"]["status"] == "indexed"
    assert result["refs_only_state_index_pilot"]["family_counts"]["lifecycle"] == 1
    assert result["refs_only_state_index_pilot"]["family_counts"]["legacy_lifecycle"] == 1
    assert result["refs_only_state_index_pilot"]["sqlite_no_body_proof"]["forbidden_body_marker_found"] is False
    latest_payload = json.loads(Path(result["latest_report_path"]).read_text(encoding="utf-8"))
    assert latest_payload["legacy_backend_status"] == "skipped_by_refs_only_state_index_only"
    assert latest_payload["refs_only_state_index_only"] is True
    assert latest_payload["size_before"]["skip_reason"] == "refs_only_state_index_only"


def test_quest_root_refs_only_state_index_only_skips_backend_and_size_scan(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.runtime_storage_maintenance_parts.quest_root_maintenance"
    )
    profile = make_profile(tmp_path)
    quest_id = "quest-001"
    quest_root = profile.runtime_root / quest_id
    _write_quest(quest_root, quest_id=quest_id, status="paused")
    called = {"backend": False}

    def fail_if_backend_runs(**_: object) -> None:
        called["backend"] = True
        raise AssertionError("legacy backend must not run in refs-only state index only mode")

    def fail_if_size_scan_runs(_: Path) -> int:
        raise AssertionError("recursive size scan must not run in refs-only state index only mode")

    monkeypatch.setattr(module.backend_maintenance, "run_quest_storage_maintenance", fail_if_backend_runs)
    monkeypatch.setattr(module, "_directory_size_bytes", fail_if_size_scan_runs)

    result = module.maintain_quest_runtime_storage(
        profile=profile,
        quest_root=quest_root,
        refs_only_state_index_pilot=True,
        refs_only_state_index_only=True,
        include_worktrees=False,
        dedupe_worktree_min_mb=None,
        slim_jsonl_threshold_mb=None,
    )

    assert called["backend"] is False
    assert result["status"] == "maintained"
    assert result["legacy_backend_status"] == "skipped_by_refs_only_state_index_only"
    assert result["size_before"]["status"] == "skipped"
    assert result["size_before"]["skip_reason"] == "refs_only_state_index_only"
    assert result["size_after"] == result["size_before"]
    assert result["refs_only_state_index_pilot"]["status"] == "indexed"


def test_refs_only_state_index_only_requires_pilot_flag(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    quest_id = "quest-001"
    study_root = profile.studies_root / study_id
    quest_root = profile.runtime_root / quest_id
    _write_study(study_root, study_id=study_id, quest_id=quest_id)
    _write_quest(quest_root, quest_id=quest_id, status="paused")

    result = module.maintain_runtime_storage(
        profile=profile,
        study_id=study_id,
        study_root=None,
        refs_only_state_index_only=True,
    )

    assert result["status"] == "blocked_refs_only_state_index_only_without_pilot"
    assert result["refs_only_state_index_pilot"]["status"] == "skipped"


def _write_refs_only_pilot_fixture(*, study_root: Path, quest_root: Path) -> None:
    payloads = {
        study_root / "artifacts" / "runtime" / "owner_route" / "latest.json": {
            "surface": "domain_route_owner_route",
            "idempotency_key": "route-001",
            "receipt_body": "OWNER_RECEIPT_BODY_MUST_NOT_ENTER_SQLITE",
        },
        study_root
        / "artifacts"
        / "runtime"
        / "opl_family_domain_handler"
        / "dispatch_receipts"
        / "dispatch-001.json": {
            "surface": "domain_owner_action_dispatch_receipt",
            "dispatch_id": "dispatch-001",
            "owner_receipt_body": "OWNER_RECEIPT_BODY_MUST_NOT_ENTER_SQLITE",
        },
        study_root / "artifacts" / "runtime" / "cursors" / "owner-route.cursor.json": {
            "cursor": "route-001",
            "source_fingerprint": "source-fp-001",
        },
        study_root / "artifacts" / "runtime" / "indexes" / "stage_artifact_index.json": {
            "surface_kind": "stage_artifact_index",
            "artifact_refs": ["artifacts/runtime/owner_route/latest.json"],
        },
        study_root / "artifacts" / "publication_eval" / "latest.json": {
            "verdict": "PUBLICATION_TRUTH_MUST_NOT_ENTER_SQLITE",
        },
    }
    for path, payload in payloads.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    outbox = study_root / "artifacts" / "runtime" / "paper_work_unit_outbox" / "receipts.jsonl"
    outbox.parent.mkdir(parents=True, exist_ok=True)
    outbox.write_text(
        json.dumps(
            {
                "receipt_id": "receipt-001",
                "intent": {"body": "OWNER_RECEIPT_BODY_MUST_NOT_ENTER_SQLITE"},
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    manuscript = study_root / "manuscript" / "current_package" / "body.md"
    manuscript.parent.mkdir(parents=True, exist_ok=True)
    manuscript.write_text("MANUSCRIPT_BODY_MUST_NOT_ENTER_SQLITE\n", encoding="utf-8")
