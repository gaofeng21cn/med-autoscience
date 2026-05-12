from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith("__")
})


SEED_FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "policies"
    / "study-workflow"
    / "publication_route_memory_seed_fixture.json"
)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_publication_route_memory_apply_seed_cli_requires_explicit_apply_or_dry_run(tmp_path: Path) -> None:
    cli = importlib.import_module("med_autoscience.cli")

    with pytest.raises(SystemExit) as exc:
        cli.main(
            [
                "publication-route-memory-apply-seed",
                "--workspace-root",
                str(tmp_path / "workspace"),
                "--seed-fixture",
                str(SEED_FIXTURE),
            ]
        )

    assert exc.value.code == 2


def test_publication_route_memory_apply_seed_cli_dispatches_controller(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"

    exit_code = cli.main(
        [
            "publication-route-memory-apply-seed",
            "--workspace-root",
            str(workspace_root),
            "--seed-fixture",
            str(SEED_FIXTURE),
            "--apply",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["surface"] == "publication_route_memory_apply_receipt"
    assert payload["status"] == "applied"
    assert payload["accepted_memory_ids"] == [
        "publication_route_memory_seed__external_validation_rescue",
        "publication_route_memory_seed__negative_result_stoploss",
    ]
    assert Path(payload["memory_pack_ref"]).exists()


def test_publication_route_memory_inventory_cli_lists_cards_without_body_by_default(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    cli.main(
        [
            "publication-route-memory-apply-seed",
            "--workspace-root",
            str(workspace_root),
            "--seed-fixture",
            str(SEED_FIXTURE),
            "--apply",
        ]
    )
    capsys.readouterr()

    exit_code = cli.main(
        [
            "publication-route-memory-inventory",
            "--workspace-root",
            str(workspace_root),
            "--stage",
            "decision",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["surface"] == "publication_route_memory_inventory"
    assert payload["status"] == "ready"
    assert payload["read_only"] is True
    assert payload["body_included"] is False
    assert payload["card_count_total"] == 2
    assert payload["card_count_filtered"] == 1
    assert [card["memory_id"] for card in payload["cards"]] == [
        "publication_route_memory_seed__negative_result_stoploss"
    ]
    assert payload["receipt_summary"]["migration_receipt_count"] == 1
    assert payload["authority_boundary"]["can_authorize_publication_quality"] is False
    assert "Negative or unstable main analysis should trigger" in captured.out
    assert "When a bounded analysis campaign returns" not in captured.out


def test_publication_route_memory_inventory_cli_can_include_body_for_maintainers(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    cli.main(
        [
            "publication-route-memory-apply-seed",
            "--workspace-root",
            str(workspace_root),
            "--seed-fixture",
            str(SEED_FIXTURE),
            "--apply",
        ]
    )
    capsys.readouterr()

    exit_code = cli.main(
        [
            "publication-route-memory-inventory",
            "--workspace-root",
            str(workspace_root),
            "--route-family",
            "weak_or_negative_result_handling",
            "--include-card-body",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["body_included"] is True
    assert payload["card_count_filtered"] == 1
    assert payload["cards"][0]["route_family"] == "weak_or_negative_result_handling"
    assert "prose_summary" in payload["cards"][0]
    assert "failure_modes" in payload["cards"][0]
    assert "When a bounded analysis campaign returns" in captured.out


def test_stage_knowledge_packet_cli_materializes_packet(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "S1"
    _write_json(study_root / "artifacts" / "reference_context" / "latest.json", {"status": "present"})
    _write_json(
        workspace_root / "portfolio" / "research_memory" / "literature" / "coverage" / "latest.json",
        {"status": "present"},
    )
    cli.main(
        [
            "publication-route-memory-apply-seed",
            "--workspace-root",
            str(workspace_root),
            "--seed-fixture",
            str(SEED_FIXTURE),
            "--apply",
        ]
    )
    capsys.readouterr()

    exit_code = cli.main(
        [
            "stage-knowledge-packet",
            "--study-id",
            "S1",
            "--stage",
            "idea",
            "--study-root",
            str(study_root),
            "--workspace-root",
            str(workspace_root),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["surface"] == "stage_knowledge_packet"
    assert payload["status"] == "ready"
    assert payload["artifact_path"].endswith("artifacts/stage_knowledge/idea/latest.json")
    assert Path(payload["artifact_path"]).exists()
    assert payload["publication_route_memory_refs"][0]["memory_id"] == (
        "publication_route_memory_seed__external_validation_rescue"
    )
    assert payload["authority_boundary"]["can_replace_controller_decision"] is False


def test_stage_memory_closeout_route_cli_materializes_and_routes_typed_closeout(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "S1"
    closeout_payload = tmp_path / "closeout.json"
    _write_json(
        closeout_payload,
        {
            "idempotency_key": "closeout-cli",
            "source_refs": ["stage:decision:turn-1"],
            "reusable_lessons": [
                {
                    "write_id": "route-memory-lesson",
                    "scope": "workspace_reusable",
                    "lesson": "Stop-loss was appropriate after route evidence stayed weak.",
                }
            ],
            "failed_paths": [{"write_id": "route-failed-path", "reason": "Endpoint evidence remained thin."}],
        },
    )

    closeout_exit = cli.main(
        [
            "stage-memory-closeout-route",
            "--study-id",
            "S1",
            "--stage",
            "decision",
            "--study-root",
            str(study_root),
            "--workspace-root",
            str(workspace_root),
            "--closeout-payload",
            str(closeout_payload),
            "--materialize-closeout-packet",
            "--apply",
        ]
    )
    captured = capsys.readouterr()

    assert closeout_exit == 0
    payload = json.loads(captured.out)
    assert payload["surface"] == "memory_write_router_receipt"
    assert payload["status"] == "applied"
    assert payload["closeout_packet_ref"].endswith(
        "artifacts/stage_knowledge/decision/closeouts/closeout-cli.json"
    )
    assert payload["receipt_ref"].endswith(
        "artifacts/stage_knowledge/memory_write_router_receipts/closeout-cli.json"
    )
    assert Path(payload["closeout_packet_ref"]).exists()
    assert Path(payload["receipt_ref"]).exists()
    assert [item["write_id"] for item in payload["accepted_writes"]] == [
        "route-memory-lesson",
        "route-failed-path",
    ]


def test_stage_memory_closeout_route_cli_can_route_existing_packet(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "S1"
    packet_path = study_root / "artifacts" / "stage_knowledge" / "decision" / "closeouts" / "existing.json"
    _write_json(
        packet_path,
        {
            "surface": "stage_memory_closeout_packet",
            "study_id": "S1",
            "stage": "decision",
            "source_refs": ["stage:decision:turn-1"],
            "proposed_writes": [
                {
                    "write_id": "route-memory-lesson",
                    "source_category": "reusable_lessons",
                    "destination": "workspace_research_memory_proposal",
                }
            ],
            "typed_blockers": [],
            "idempotency_key": "existing-packet",
        },
    )

    exit_code = cli.main(
        [
            "stage-memory-closeout-route",
            "--study-root",
            str(study_root),
            "--workspace-root",
            str(workspace_root),
            "--closeout-packet",
            str(packet_path),
            "--apply",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["surface"] == "memory_write_router_receipt"
    assert payload["status"] == "applied"
    assert payload["closeout_packet_ref"] == str(packet_path)


def test_paper_soak_memory_proof_cli_materializes_readonly_proof(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "S1"
    sidecar_receipt = workspace_root / "artifacts" / "runtime" / "opl_family_sidecar" / "dispatch_receipts" / "r1.json"
    _write_json(
        sidecar_receipt,
        {
            "surface_kind": "mas_family_sidecar_dispatch_receipt",
            "accepted": True,
            "task_id": "task-1",
            "task_kind": "study_progress/read",
            "dispatch": {"study_id": "S1"},
        },
    )
    closeout_payload = tmp_path / "closeout.json"
    _write_json(
        closeout_payload,
        {
            "idempotency_key": "paper-soak-closeout",
            "source_refs": ["stage:decision:turn-1"],
            "reusable_lessons": [
                {
                    "write_id": "route-memory-lesson",
                    "scope": "workspace_reusable",
                    "lesson": "Stop-loss was appropriate after route evidence stayed weak.",
                }
            ],
            "failed_paths": [{"write_id": "route-failed-path", "reason": "Endpoint evidence remained thin."}],
        },
    )
    cli.main(
        [
            "publication-route-memory-apply-seed",
            "--workspace-root",
            str(workspace_root),
            "--seed-fixture",
            str(SEED_FIXTURE),
            "--apply",
        ]
    )
    cli.main(
        [
            "stage-knowledge-packet",
            "--study-id",
            "S1",
            "--stage",
            "decision",
            "--study-root",
            str(study_root),
            "--workspace-root",
            str(workspace_root),
        ]
    )
    cli.main(
        [
            "stage-memory-closeout-route",
            "--study-id",
            "S1",
            "--stage",
            "decision",
            "--study-root",
            str(study_root),
            "--workspace-root",
            str(workspace_root),
            "--closeout-payload",
            str(closeout_payload),
            "--materialize-closeout-packet",
            "--apply",
        ]
    )
    capsys.readouterr()

    exit_code = cli.main(
        [
            "paper-soak-memory-proof",
            "--study-id",
            "S1",
            "--stage",
            "decision",
            "--study-root",
            str(study_root),
            "--workspace-root",
            str(workspace_root),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["surface"] == "paper_soak_memory_apply_proof"
    assert payload["status"] == "ready"
    assert payload["missing_reasons"] == []
    assert payload["artifact_path"].endswith(
        "artifacts/stage_knowledge/paper_soak_memory_apply_proof/latest.json"
    )
    assert payload["stage_entry"]["route_memory_ref_count"] == 1
    assert payload["read_only_display_policy"]["consumer_role"] == "OPL/Aion read-only display"
    assert payload["read_only_display_policy"]["can_write_memory_body"] is False
    assert all(ref["body_included"] is False for ref in payload["opl_aion_readonly_receipt_refs"])
    assert "Stop-loss was appropriate" not in captured.out
