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
SEED_LIBRARY = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "policies"
    / "study-workflow"
    / "publication_route_memory_library.md"
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
    assert len(payload["accepted_memory_ids"]) >= 9
    assert "publication_route_memory_seed__clinical_classifier" in payload["accepted_memory_ids"]
    assert "publication_route_memory_seed__external_validation_rescue" in payload["accepted_memory_ids"]
    assert "publication_route_memory_seed__negative_result_stoploss" in payload["accepted_memory_ids"]
    assert Path(payload["memory_pack_ref"]).exists()


def test_publication_route_memory_apply_seed_cli_accepts_markdown_library(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"

    exit_code = cli.main(
        [
            "publication-route-memory-apply-seed",
            "--workspace-root",
            str(workspace_root),
            "--seed-library",
            str(SEED_LIBRARY),
            "--apply",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["surface"] == "publication_route_memory_apply_receipt"
    assert payload["status"] == "applied"
    assert payload["canonical_body_ref"].endswith("publication_route_memory_library.md")
    assert "publication_route_memory_seed__clinical_classifier" in payload["accepted_memory_ids"]
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
    assert payload["card_count_total"] >= 9
    assert payload["card_count_filtered"] >= 3
    assert [card["memory_id"] for card in payload["cards"]][:3] == [
        "publication_route_memory_seed__clinical_classifier",
        "publication_route_memory_seed__clinical_subtype_reconstruction",
        "publication_route_memory_seed__negative_result_stoploss",
    ]
    assert payload["receipt_summary"]["migration_receipt_count"] == 1
    grouping = payload["operator_grouping"]
    assert grouping["surface"] == "publication_route_memory_operator_grouping"
    assert grouping["read_only"] is True
    assert grouping["body_included"] is False
    assert grouping["display_policy"]["display_role"] == "ref_only_grouping"
    assert grouping["display_policy"]["can_write_memory_body"] is False
    assert grouping["display_policy"]["can_accept_or_reject_writeback"] is False
    assert grouping["display_policy"]["can_authorize_publication_quality"] is False
    assert grouping["workspace"]["card_count"] == payload["card_count_filtered"]
    assert {item["stage"] for item in grouping["by_stage"]} >= {"decision"}
    assert {item["route_family"] for item in grouping["by_route_family"]} >= {
        "clinical_classifier",
        "clinical_subtype_reconstruction",
        "weak_or_negative_result_handling",
    }
    assert grouping["by_status"] == [
        {
            "status": "active",
            "memory_refs": grouping["workspace"]["memory_refs"],
            "card_count": payload["card_count_filtered"],
        }
    ]
    assert payload["review_summary"] == {
        "surface": "publication_route_memory_review_summary",
        "card_count": payload["card_count_filtered"],
        "active_count": payload["card_count_filtered"],
        "stale_count": 0,
        "deprecated_count": 0,
        "needs_review_count": 0,
        "stale_or_deprecated_refs": [],
        "authority_boundary": "review_signal_only_not_memory_body_or_quality_authority",
    }
    assert payload["opl_aion_receipt_inventory"]["body_included"] is False
    assert payload["opl_aion_receipt_inventory"]["receipt_count"] == 1
    assert payload["opl_aion_receipt_inventory"]["receipts"][0]["receipt_status"] == "applied"
    accepted_refs = payload["opl_aion_receipt_inventory"]["receipts"][0]["accepted_refs"]
    assert len(accepted_refs) == payload["card_count_total"]
    assert accepted_refs[:3] == [
        {
            "memory_id": "publication_route_memory_seed__clinical_classifier",
            "reason": "",
            "status": "accepted",
        },
        {
            "memory_id": "publication_route_memory_seed__clinical_subtype_reconstruction",
            "reason": "",
            "status": "accepted",
        },
        {
            "memory_id": "publication_route_memory_seed__negative_result_stoploss",
            "reason": "",
            "status": "accepted",
        },
    ]
    assert payload["authority_boundary"]["can_authorize_publication_quality"] is False
    assert "Negative or unstable main analysis should trigger" in captured.out
    assert "When a bounded analysis campaign returns" not in captured.out


def test_publication_route_memory_inventory_cli_groups_stale_and_deprecated_review_refs(
    tmp_path: Path,
    capsys,
) -> None:
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

    pack_path = workspace_root / "portfolio" / "research_memory" / "publication_route_memory" / "memory_pack.json"
    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    pack["cards"][0]["status"] = "stale_seed"
    pack["cards"][1]["status"] = "deprecated_seed"
    _write_json(pack_path, pack)

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
    assert payload["review_summary"]["stale_count"] == 1
    assert payload["review_summary"]["deprecated_count"] == 1
    assert payload["review_summary"]["needs_review_count"] == 2
    assert payload["review_summary"]["stale_or_deprecated_refs"][:2] == [
        "publication_route_memory_seed__clinical_classifier",
        "publication_route_memory_seed__clinical_subtype_reconstruction",
    ]
    by_status = {
        item["status"]: item
        for item in payload["operator_grouping"]["by_status"]
    }
    assert by_status["stale"]["memory_refs"][0]["memory_id"] == (
        "publication_route_memory_seed__clinical_classifier"
    )
    assert by_status["deprecated"]["memory_refs"][0]["memory_id"] == (
        "publication_route_memory_seed__clinical_subtype_reconstruction"
    )
    assert all("prose_summary" not in ref for ref in by_status["active"]["memory_refs"])


def test_publication_route_memory_inventory_cli_projects_accepted_and_rejected_writeback_receipts(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    first_study_root = workspace_root / "studies" / "S1"
    second_study_root = workspace_root / "studies" / "S2"
    first_closeout_payload = tmp_path / "accepted-closeout.json"
    second_closeout_payload = tmp_path / "rejected-closeout.json"
    _write_json(
        first_closeout_payload,
        {
            "idempotency_key": "accepted-writeback-receipt",
            "source_refs": ["stage:decision:s1"],
            "reusable_lessons": [
                {
                    "write_id": "accepted-route-back-lesson",
                    "scope": "workspace_reusable",
                    "route_family": "route_back_repair",
                    "stage_applicability": ["decision", "review"],
                    "title": "Route-back repair lesson",
                    "lesson": "Route back before rebuilding claims when reviewer evidence is underpowered.",
                    "source_refs": ["stage:decision:s1"],
                }
            ],
        },
    )
    _write_json(
        second_closeout_payload,
        {
            "idempotency_key": "rejected-writeback-receipt",
            "source_refs": ["stage:review:s2"],
            "reusable_lessons": [
                {
                    "write_id": "rejected-local-claim",
                    "scope": "study_specific_claim",
                    "route_family": "local_claim_boundary",
                    "stage_applicability": ["review"],
                    "lesson": "Only this study can use the local endpoint boundary.",
                    "source_refs": ["stage:review:s2"],
                }
            ],
        },
    )

    for study_id, stage, study_root, closeout_payload in (
        ("S1", "decision", first_study_root, first_closeout_payload),
        ("S2", "review", second_study_root, second_closeout_payload),
    ):
        exit_code = cli.main(
            [
                "stage-memory-closeout-route",
                "--study-id",
                study_id,
                "--stage",
                stage,
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
        assert exit_code == 0
        capsys.readouterr()

    exit_code = cli.main(
        [
            "publication-route-memory-inventory",
            "--workspace-root",
            str(workspace_root),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["body_included"] is False
    assert payload["card_count_total"] == 1
    assert "prose_summary" not in payload["cards"][0]
    assert "Route back before rebuilding claims" not in captured.out
    assert "Only this study can use" not in captured.out

    receipt_inventory = payload["opl_aion_receipt_inventory"]
    assert receipt_inventory["body_included"] is False
    assert receipt_inventory["display_policy"]["display_role"] == "receipt_ref_only"
    assert receipt_inventory["display_policy"]["can_read_memory_body"] is False
    assert receipt_inventory["display_policy"]["can_accept_or_reject_writeback"] is False
    by_status = {item["receipt_status"]: item for item in receipt_inventory["by_receipt_status"]}
    assert by_status["applied"]["receipt_count"] == 2
    by_route_family = {
        item["route_family"]: item
        for item in receipt_inventory["by_route_family"]
    }
    assert by_route_family["route_back_repair"]["receipt_count"] == 1
    assert by_route_family["local_claim_boundary"]["receipt_count"] == 1
    by_stage = {item["stage"]: item for item in receipt_inventory["by_stage"]}
    assert by_stage["decision"]["receipt_count"] == 1
    assert by_stage["review"]["receipt_count"] == 1

    receipts = {
        receipt["idempotency_key"]: receipt
        for receipt in receipt_inventory["receipts"]
    }
    accepted_receipt = receipts["accepted-writeback-receipt"]
    assert accepted_receipt["receipt_status"] == "applied"
    assert accepted_receipt["stage"] == "decision"
    assert accepted_receipt["route_family"] == "route_back_repair"
    assert accepted_receipt["source_receipt_ref"].endswith(
        "artifacts/stage_knowledge/memory_write_router_receipts/accepted-writeback-receipt.json"
    )
    assert accepted_receipt["writeback_receipt_ref"].endswith(
        "portfolio/research_memory/publication_route_memory/writeback_receipts/accepted-writeback-receipt.json"
    )
    assert accepted_receipt["route_back_refs"] == [
        {
            "write_id": "accepted-route-back-lesson",
            "memory_id": "publication_route_memory_writeback__accepted-route-back-lesson",
            "route_family": "route_back_repair",
            "stage_applicability": ["decision", "review"],
            "destination": "workspace_research_memory_proposal",
            "owner_target": "workspace_memory_owner",
            "proposal_ref": accepted_receipt["accepted_writeback_refs"][0]["proposal_ref"],
            "receipt_ref": accepted_receipt["accepted_writeback_refs"][0]["receipt_ref"],
            "source_receipt_ref": accepted_receipt["source_receipt_ref"],
            "writeback_receipt_ref": accepted_receipt["writeback_receipt_ref"],
            "reason": "",
            "status": "accepted",
            "receipt_status": "applied",
            "authority_boundary": "ref_only_not_memory_body_or_writeback_authority",
        }
    ]
    assert accepted_receipt["writeback_refs"] == accepted_receipt["accepted_writeback_refs"]
    rejected_receipt = receipts["rejected-writeback-receipt"]
    assert rejected_receipt["receipt_status"] == "applied"
    assert rejected_receipt["stage"] == "review"
    assert rejected_receipt["route_family"] == "local_claim_boundary"
    assert rejected_receipt["reason"] == "study_specific_claim_not_workspace_memory"
    assert rejected_receipt["rejected_writeback_refs"] == [
        {
            "write_id": "rejected-local-claim",
            "route_family": "local_claim_boundary",
            "stage_applicability": ["review"],
            "destination": "workspace_research_memory_proposal",
            "owner_target": "workspace_memory_owner",
            "reason": "study_specific_claim_not_workspace_memory",
            "source_receipt_ref": rejected_receipt["source_receipt_ref"],
            "writeback_receipt_ref": rejected_receipt["writeback_receipt_ref"],
            "status": "rejected",
            "receipt_status": "applied",
            "authority_boundary": "ref_only_not_memory_body_or_writeback_authority",
        }
    ]
    assert rejected_receipt["route_back_refs"] == []
    assert rejected_receipt["writeback_refs"] == rejected_receipt["rejected_writeback_refs"]
    assert payload["authority_boundary"]["can_authorize_publication_quality"] is False
    assert payload["authority_boundary"]["can_replace_controller_decision"] is False


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
    assert "best_fit" in payload["cards"][0]
    assert "minimum_evidence_package" in payload["cards"][0]
    assert "table_figure_pattern" in payload["cards"][0]
    assert "claim_boundary" in payload["cards"][0]
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
        "publication_route_memory_seed__clinical_classifier"
    )
    assert "route_memory_summary" in payload["publication_route_memory_refs"][0]
    assert "minimum_evidence_package" not in payload["publication_route_memory_refs"][0]
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
    domain_handler_receipt = workspace_root / "runtime" / "artifacts" / "opl_family_domain_handler" / "dispatch_receipts" / "r1.json"
    _write_json(
        domain_handler_receipt,
        {
            "surface_kind": "mas_family_domain_handler_dispatch_receipt",
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
    assert payload["stage_entry"]["route_memory_ref_count"] == 3
    assert payload["read_only_display_policy"]["consumer_role"] == "OPL/Aion read-only display"
    assert payload["read_only_display_policy"]["can_write_memory_body"] is False
    assert all(ref["body_included"] is False for ref in payload["opl_aion_readonly_receipt_refs"])
    assert "Stop-loss was appropriate" not in captured.out
