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
        "state_index_owner": "one-person-lab",
        "mas_state_index_authority": False,
        "body_included": False,
        "rebuildable": True,
        "refs_projection_only": True,
        "body_free": True,
        "stores_study_truth": False,
        "stores_manuscript_body": False,
        "stores_artifact_body": False,
        "stores_owner_receipt_body": False,
        "can_drive_lifecycle": False,
        "can_select_next_action": False,
        "can_authorize_currentness": False,
        "can_generate_next_action_authority": False,
        "can_authorize_provider_admission": False,
        "can_create_worker_attempt": False,
        "can_create_outbox_record": False,
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
        "paper_progress_transition_ref": 1,
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
        "runtime/quests/quest-001/artifacts/runtime/state/runtime_state.json",
        "studies/001-risk/artifacts/runtime/owner_route/latest.json",
        "studies/001-risk/artifacts/runtime/opl_family_domain_handler/dispatch_receipts/dispatch-001.json",
        "studies/001-risk/artifacts/runtime/paper_progress_transition_refs/receipts.jsonl",
        "studies/001-risk/artifacts/runtime/cursors/owner-route.cursor.json",
        "studies/001-risk/artifacts/runtime/indexes/stage_artifact_index.json",
    } == source_refs
    sqlite_text = "\n".join("|".join(str(cell) for cell in row) for row in rows)
    assert "OWNER_RECEIPT_BODY_MUST_NOT_ENTER_SQLITE" not in sqlite_text
    assert "PUBLICATION_TRUTH_MUST_NOT_ENTER_SQLITE" not in sqlite_text
    assert "MANUSCRIPT_BODY_MUST_NOT_ENTER_SQLITE" not in sqlite_text
    assert result["projection_policy"]["rebuildable"] is True
    assert result["projection_policy"]["started_worker"] is False
    assert result["projection_policy"]["outbox_record"] is False
    assert result["projection_policy"]["can_generate_next_action_authority"] is False
    assert result["projection_policy"]["can_authorize_provider_admission"] is False
    assert result["projection_policy"]["can_authorize_quality_verdict"] is False
    assert result["projection_policy"]["can_authorize_publication_ready"] is False
    assert result["private_control_plane_boundary"] == {
        "surface_role": "temporary_refs_projection",
        "opt_in_only": True,
        "default_runtime_path": False,
        "legacy_backend_result_authority": False,
        "can_change_storage_maintenance_outcome": False,
        "can_start_worker": False,
        "can_create_attempt": False,
        "can_create_outbox_record": False,
        "can_generate_provider_admission": False,
        "can_generate_next_action": False,
        "can_claim_runtime_currentness": False,
        "can_claim_stage_progress": False,
        "replacement_owner_surface": "one-person-lab StateIndexKernel",
    }
    readback_requirement = result["opl_state_index_kernel_readback_requirement"]
    assert readback_requirement["surface_kind"] == "opl_state_index_kernel_readback_requirement"
    assert readback_requirement["required_owner_surface"] == "one-person-lab StateIndexKernel"
    assert readback_requirement["mas_surface_role"] == "temporary_refs_projection"
    assert readback_requirement["mas_can_satisfy_readback"] is False
    assert readback_requirement["required_readback_identity_fields"] == [
        "domain_id",
        "program_id",
        "stage_id",
        "attempt_id",
        "surface_id",
        "source_ref",
        "receipt_ref",
        "content_hash",
        "observed_at",
        "indexed_at",
        "index_version",
        "rebuild_epoch",
    ]
    assert readback_requirement["required_authority_boundary"] == {
        "state_index_owner": "one-person-lab",
        "mas_state_index_authority": False,
        "refs_projection_only": True,
        "body_free": True,
        "can_drive_lifecycle": False,
        "can_select_next_action": False,
        "can_authorize_currentness": False,
        "can_authorize_provider_admission": False,
    }
    assert readback_requirement["mas_projection_cannot_replace"] == [
        "opl_state_index_kernel_readback",
        "opl_lifecycle_index",
        "opl_operator_read_model",
        "opl_artifact_index",
        "opl_queue_index",
    ]
    assert result["legacy_surface_policy"] == {
        "runtime_events": "tombstone_provenance_only",
        "runtime_snapshots": "tombstone_provenance_only",
        "lineage_nodes": "tombstone_provenance_only",
        "workspace_allocations": "tombstone_provenance_only",
        "turn_receipts": "tombstone_provenance_only",
        "surface_refs": "tombstone_provenance_only",
        "report_index": "tombstone_provenance_only",
    }


def test_refs_only_state_index_pilot_prefers_canonical_runtime_state_surface(tmp_path: Path) -> None:
    state_index = importlib.import_module("med_autoscience.runtime_protocol.refs_only_state_index_pilot")
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    quest_id = "quest-001"
    study_root = profile.studies_root / study_id
    quest_root = profile.runtime_root / quest_id
    _write_study(study_root, study_id=study_id, quest_id=quest_id)
    _write_quest(quest_root, quest_id=quest_id, status="paused", legacy_runtime_state=True)

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


def test_domain_authority_refs_index_is_refs_only_no_body_and_no_worker_outbox(tmp_path: Path) -> None:
    refs = importlib.import_module("med_autoscience.runtime_protocol.domain_authority_refs_index")
    source_adapter = importlib.import_module("med_autoscience.runtime_protocol.opl_state_index_source_adapter")
    profile = make_profile(tmp_path)
    study_root = profile.studies_root / "001-risk"
    quest_root = profile.runtime_root / "quest-001"
    _write_study(study_root, study_id="001-risk", quest_id="quest-001")
    _write_quest(quest_root, quest_id="quest-001", status="paused")
    receipt_path = study_root / "artifacts" / "runtime" / "paper_progress_transition_refs" / "receipt-001.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "receipt_id": "receipt-001",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "idempotency_key": "idem-001",
        "intent_fingerprint": "intent-fp-001",
        "source_fingerprint": "source-fp-001",
        "receipt_status": "typed_blocker",
        "started_worker": True,
        "worker_start_ref": "worker://must-not-be-authorized",
        "recorded_at": "2026-06-01T00:00:00+00:00",
        "owner_receipt_body": "OWNER_RECEIPT_BODY_MUST_NOT_ENTER_SQLITE",
    }
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False), encoding="utf-8")

    contract = refs.domain_authority_refs_index_contract()
    assert contract["authority_policy"]["stores_body"] is False
    assert contract["authority_policy"]["rebuildable"] is True
    assert contract["authority_policy"]["started_worker"] is False
    assert contract["authority_policy"]["outbox_record"] is False
    assert contract["authority_policy"]["can_generate_next_action_authority"] is False
    bridge = contract["opl_state_index_kernel_takeover_bridge"]
    legacy_helper_scan = bridge.pop("legacy_helper_active_caller_scan")
    runtime_active_scan = bridge.pop("runtime_active_private_state_index_caller_scan")
    assert runtime_active_scan == {
        "status": "no_runtime_active_private_state_index_callers",
        "no_runtime_active_private_state_index_caller_proven": True,
        "runtime_active_caller_count": 0,
        "active_runtime_callers": [],
        "current_runtime_caller_route": (
            "med_autoscience.runtime_protocol.opl_state_index_source_adapter"
        ),
        "legacy_helper_status": "history_replay_or_local_inspection_only_tail_open",
        "physical_delete_allowed": False,
        "forbidden_completion_claims": [
            "runtime_active_no_private_caller_as_physical_delete",
            "history_replay_opt_in_as_runtime_active_caller",
            "source_adapter_manifest_as_live_opl_state_index_readback",
        ],
    }
    assert legacy_helper_scan == {
        "status": "no_active_replay_or_local_inspection_callers",
        "no_active_replay_or_local_inspection_caller_proven": True,
        "physical_delete_allowed": False,
        "required_before_physical_delete": (
            "domain_authority_refs_index_live_state_index_takeover_or_"
            "no_active_replay_local_inspection_caller_physical_delete_ref"
        ),
        "active_callers": [],
        "retired_callers": [
            (
                "paper_progress_transition_refs.record_paper_progress_transition_ref::"
                "persist_authority_refs_index_explicit_opt_in"
            ),
        ],
        "allowed_consumption": [
            "explicit_history_replay",
            "explicit_local_refs_inspection",
            "tombstone_provenance",
        ],
        "forbidden_completion_claims": [
            "legacy_helper_no_active_scan_as_physical_delete",
            "opl_family_adoption_sqlite_inspection_as_current_projection",
            "legacy_sqlite_payload_projection_as_state_index_kernel_takeover",
            "explicit_replay_opt_in_as_live_opl_readback",
            "no_active_replay_local_inspection_scan_as_live_state_index_kernel_takeover",
        ],
    }
    assert bridge == {
        "surface_kind": "domain_authority_refs_index_state_index_takeover_bridge",
        "bridge_status": "repo_replacement_parity_proven_live_takeover_tail_open",
        "replacement_owner_surface": "one-person-lab StateIndexKernel",
        "mas_source_adapter_role": "refs_only_domain_authority_receipt_source_adapter",
        "active_caller_status": "repo_active_callers_migrated_to_opl_state_index_source_adapter",
        "active_caller_effect": "opl_state_index_source_adapter_emitted_no_sqlite_persistence",
        "default_sqlite_persistence": False,
        "sqlite_persistence_requires_explicit_opt_in": True,
        "active_caller_retains_surface": False,
        "active_caller_retains_authority": False,
        "active_caller_db_path_does_not_imply_persistence": True,
        "legacy_domain_authority_refs_index_role": (
            "explicit_history_replay_or_local_refs_inspection_only"
        ),
        "source_tables": list(refs.AUTHORITY_REF_TABLES),
        "forbidden_legacy_tables": list(refs.LEGACY_TABLE_POLICY),
        "repo_replacement_parity_refs": [
            "src/med_autoscience/runtime_protocol/refs_only_state_index_pilot.py",
            "src/med_autoscience/controllers/opl_state_index_kernel.py",
            (
                "tests/test_runtime_storage_maintenance_cases/"
                "runtime_refs_only_state_index_pilot.py::"
                "test_refs_only_state_index_pilot_indexes_small_runtime_refs_without_bodies"
            ),
            (
                "tests/test_opl_state_index_kernel.py::"
                "test_state_index_kernel_rows_are_refs_only_and_rebuildable"
            ),
        ],
        "required_opl_readback_ref": (
            "src/med_autoscience/runtime_protocol/refs_only_state_index_pilot.py#"
            "opl_state_index_kernel_readback_requirement"
        ),
        "live_takeover_required_before_physical_delete": True,
        "no_active_caller_required_before_physical_delete": True,
        "tombstone_or_provenance_required_before_physical_delete": True,
        "completion_claim_requires_live_opl_readback_or_no_active_caller": True,
        "mas_projection_cannot_replace": [
            "opl_state_index_kernel_readback",
            "opl_lifecycle_index",
            "opl_operator_read_model",
            "opl_artifact_index",
            "opl_queue_index",
        ],
    }
    assert contract["legacy_table_policy"] == {
        "runtime_events": "tombstone_provenance_only",
        "runtime_snapshots": "tombstone_provenance_only",
        "lineage_nodes": "tombstone_provenance_only",
        "workspace_allocations": "tombstone_provenance_only",
        "turn_receipts": "tombstone_provenance_only",
        "surface_refs": "tombstone_provenance_only",
        "report_index": "tombstone_provenance_only",
    }

    result = refs.record_paper_progress_transition_ref(
        study_root=study_root,
        quest_root=quest_root,
        receipt=receipt,
        receipt_path=receipt_path,
    )

    assert result["status"] == "source_adapter_emitted"
    assert result["sqlite_persisted"] is False
    assert result["sqlite_persistence_requires_explicit_opt_in"] is True
    assert result["source_adapter_role"] == "refs_only_domain_authority_receipt_source_adapter"
    assert result["replacement_owner_surface"] == "one-person-lab StateIndexKernel"
    assert result["opl_state_index_kernel_required"] is True
    assert result["started_worker"] is False
    assert result["outbox_record"] is False
    assert result["body_included"] is False
    assert result["authority_boundary"]["can_start_worker"] is False
    assert result["authority_boundary"]["can_create_outbox_record"] is False
    assert result["authority_boundary"]["can_authorize_provider_admission"] is False
    db_path = Path(result["db_path"])
    assert not db_path.exists()

    adapter_contract = source_adapter.source_adapter_contract()
    assert adapter_contract["sqlite_persistence_parameter_exposed"] is False
    assert adapter_contract["sqlite_persistence_allowed"] is False
    assert adapter_contract["active_caller_retains_surface"] is False
    assert adapter_contract["active_caller_retains_authority"] is False
    assert adapter_contract["active_caller_retains_runtime_authority"] is False
    assert adapter_contract["active_caller_status"] == (
        "repo_active_callers_migrated_to_opl_state_index_source_adapter"
    )
    assert adapter_contract["active_caller_effect"] == (
        "opl_state_index_source_adapter_emitted_no_sqlite_persistence"
    )
    assert adapter_contract["runtime_active_private_state_index_caller_scan"][
        "no_runtime_active_private_state_index_caller_proven"
    ] is True
    assert (
        adapter_contract["runtime_active_private_state_index_caller_scan"][
            "runtime_active_caller_count"
        ]
        == 0
    )
    assert adapter_contract["live_takeover_required_before_physical_delete"] is True
    assert adapter_contract["legacy_domain_authority_refs_index_role"] == (
        "explicit_history_replay_or_local_refs_inspection_only"
    )
    adapter_result = source_adapter.emit_paper_progress_transition_source(
        study_root=study_root,
        quest_root=quest_root,
        receipt=receipt,
        receipt_path=receipt_path,
    )
    assert adapter_result["surface_kind"] == "mas_opl_state_index_source_adapter"
    assert adapter_result["legacy_domain_authority_refs_surface_kind"] == (
        "mas_domain_authority_refs_index"
    )
    assert adapter_result["status"] == "opl_state_index_source_adapter_emitted"
    assert adapter_result["source_adapter_role"] == (
        "opl_state_index_source_adapter_for_domain_authority_refs"
    )
    assert adapter_result["sqlite_persistence_parameter_exposed"] is False
    assert adapter_result["sqlite_persisted"] is False
    assert adapter_result["authority_boundary"]["state_index_owner"] == "one-person-lab"
    assert adapter_result["authority_boundary"]["mas_state_index_authority"] is False
    assert not Path(adapter_result["db_path"]).exists()

    persisted = refs.record_paper_progress_transition_ref(
        study_root=study_root,
        quest_root=quest_root,
        receipt=receipt,
        receipt_path=receipt_path,
        persist_sqlite=True,
    )
    assert persisted["status"] == "indexed"
    db_path = Path(persisted["db_path"])
    with sqlite3.connect(db_path) as conn:
        columns = [row[1] for row in conn.execute("PRAGMA table_info(paper_progress_transition_refs)").fetchall()]
        row = conn.execute(
            """
            SELECT started_worker, worker_start_ref, source_path, payload_sha256
            FROM paper_progress_transition_refs
            """
        ).fetchone()
        table_text = "\n".join(
            "|".join(str(cell) for cell in item)
            for item in conn.execute("SELECT * FROM paper_progress_transition_refs").fetchall()
        )

    assert "payload_json" not in columns
    assert "body" not in columns
    assert row == (0, None, str(receipt_path.resolve()), persisted["payload_sha256"])
    assert "OWNER_RECEIPT_BODY_MUST_NOT_ENTER_SQLITE" not in table_text


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
        (str(quest_a.resolve()), "runtime/quests/quest-001/artifacts/runtime/state/runtime_state.json"),
        (str(quest_b.resolve()), "runtime/quests/quest-002/artifacts/runtime/state/runtime_state.json"),
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
        opl_maintenance_authorization=_opl_quest_storage_authorization(profile, quest_root),
    )

    assert result["status"] == "maintained"
    pilot = result["refs_only_state_index_pilot"]
    assert pilot["status"] == "indexed"
    assert pilot["indexed_count"] == 6
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
            "lifecycle": 1,
            "paper_progress_transition_ref": 1,
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
    assert (
        latest_payload["refs_only_state_index_pilot"]["opl_state_index_kernel_readback_requirement"][
            "mas_can_satisfy_readback"
        ]
        is False
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
        opl_maintenance_authorization=_opl_quest_storage_authorization(profile, quest_root),
    )

    assert result["status"] == "maintained"
    assert result["legacy_backend_status"] == "blocked_backend_unavailable"
    assert result["summary"] == "refs-only state index pilot 已完成；legacy backend storage maintenance 当前不可用。"
    pilot = result["refs_only_state_index_pilot"]
    assert pilot["status"] == "indexed"
    assert pilot["indexed_count"] == 6
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
    assert "legacy_lifecycle" not in result["refs_only_state_index_pilot"]["family_counts"]
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
    transition_refs = study_root / "artifacts" / "runtime" / "paper_progress_transition_refs" / "receipts.jsonl"
    transition_refs.parent.mkdir(parents=True, exist_ok=True)
    transition_refs.write_text(
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
