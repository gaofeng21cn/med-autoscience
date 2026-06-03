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
    assert pilot["indexed_count"] == 6
    assert pilot["authority_boundary"]["body_included"] is False
    assert Path(pilot["sqlite_ref"]["db_path"]).is_file()
    latest_payload = json.loads(Path(result["latest_report_path"]).read_text(encoding="utf-8"))
    assert latest_payload["refs_only_state_index_pilot"]["sqlite_ref"]["workspace_relative_path"] == (
        "artifacts/runtime/mas_refs_only_state_index_pilot.sqlite"
    )
    assert "OWNER_RECEIPT_BODY_MUST_NOT_ENTER_SQLITE" not in json.dumps(
        latest_payload["refs_only_state_index_pilot"],
        ensure_ascii=False,
    )


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
