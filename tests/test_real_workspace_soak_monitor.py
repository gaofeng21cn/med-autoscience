from __future__ import annotations

import importlib
import json
from pathlib import Path


ALL_STAGES = (
    "literature_scout",
    "line_selection",
    "baseline",
    "primary_analysis",
    "bounded_analysis",
    "route_back",
    "stop_loss",
    "revision_reopen",
    "runtime_recovery",
    "finalize_rebuild",
    "final_pre_submission_audit",
)


def _module():
    return importlib.import_module("med_autoscience.controllers.real_workspace_soak_monitor")


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _matrix_path(study_root: Path) -> Path:
    return study_root / "artifacts" / "medical_paper" / "real_study_soak_matrix_evidence.json"


def _readiness_path(study_root: Path) -> Path:
    return study_root / "artifacts" / "medical_paper" / "medical_paper_readiness.json"


def _ready_matrix_payload(study_id: str, archetype: str) -> dict[str, object]:
    contracts: dict[str, object] = {
        "literature_contract": True,
        "statistical_contract": True,
    }
    if archetype == "prediction_model/external_validation":
        contracts["external_validation_fixture"] = True
    return {
        "surface": "real_study_soak_matrix_evidence",
        "study_id": study_id,
        "study_archetype": archetype,
        "stages": list(ALL_STAGES),
        "contracts": contracts,
        "result_strength": "adequate",
        "route_action": "continue",
        "durable_refs": [
            f"{study_id}/artifacts/publication_eval/latest.json",
            f"{study_id}/study_runtime_status.json",
        ],
    }


def test_real_workspace_soak_monitor_builds_ready_read_only_projection(tmp_path: Path) -> None:
    roots = [
        tmp_path / "risk-model",
        tmp_path / "real-world",
        tmp_path / "triage",
    ]
    _write_json(
        _matrix_path(roots[0]),
        _ready_matrix_payload("001-risk-model", "prediction_model/external_validation"),
    )
    _write_json(
        _matrix_path(roots[1]),
        _ready_matrix_payload("002-real-world", "observational_real_world"),
    )
    _write_json(
        _matrix_path(roots[2]),
        _ready_matrix_payload("003-triage", "subtype_or_triage"),
    )

    projection = _module().build_real_workspace_soak_monitor(study_roots=roots)

    assert projection["surface"] == "real_workspace_soak_monitor"
    assert projection["schema_version"] == 1
    assert projection["overall_status"] == "ready"
    assert projection["next_action"] == "continue_real_workspace_soak"
    assert projection["missing_archetypes"] == []
    assert projection["authority_contract"] == {
        "authority": "observability_read_model_only",
        "can_mutate_runtime": False,
        "can_authorize_quality": False,
        "can_authorize_submission": False,
        "can_authorize_finalize": False,
    }
    assert len(projection["studies"]) == 3
    assert projection["action_cards"] == []
    assert all(study["status"] == "ready" for study in projection["studies"])
    assert all(study["next_action"] == "continue_multistudy_soak" for study in projection["studies"])
    assert all(study["durable_refs"] for study in projection["studies"])
    assert not (roots[0] / "artifacts" / "medical_paper" / "real_workspace_soak_monitor.json").exists()


def test_real_workspace_soak_monitor_blocks_missing_literature_from_readiness_ref(
    tmp_path: Path,
) -> None:
    root = tmp_path / "missing-literature"
    _write_json(
        _readiness_path(root),
        {
            "surface": "medical_paper_readiness",
            "study_id": "004-missing-literature",
            "study_archetype": "observational_real_world",
            "result_strength": "adequate",
            "route_action": "continue",
            "capability_surfaces": [
                {"surface_key": "literature_scout", "status": "missing", "evidence_refs": []},
                {
                    "surface_key": "archetype_analysis_contract",
                    "status": "present",
                    "evidence_refs": ["paper/medical_analysis_contract.json"],
                },
                {
                    "surface_key": "real_study_soak_matrix_evidence",
                    "status": "present",
                    "evidence_refs": ["artifacts/real_study_soak_matrix/evidence.json"],
                },
            ],
        },
    )

    projection = _module().build_real_workspace_soak_monitor(study_roots=[root])

    assert projection["overall_status"] == "blocked"
    assert projection["next_action"] == "materialize_literature_contract"
    study = projection["studies"][0]
    assert study["status"] == "blocked"
    assert "contract:literature_contract" in study["blocking_gaps"]
    assert study["next_action"] == "materialize_literature_contract"
    assert study["durable_refs"] == [str(_readiness_path(root).resolve())]
    assert projection["action_cards"][0] == {
        "study_id": "004-missing-literature",
        "status": "blocked",
        "next_action": "materialize_literature_contract",
        "blocking_gaps": ["contract:literature_contract"],
        "durable_refs": [str(_readiness_path(root).resolve())],
    }


def test_real_workspace_soak_monitor_requires_all_archetypes(tmp_path: Path) -> None:
    root = tmp_path / "single-real-world"
    _write_json(
        _matrix_path(root),
        _ready_matrix_payload("005-real-world", "observational_real_world"),
    )

    projection = _module().build_real_workspace_soak_monitor(study_roots=[root])

    assert projection["overall_status"] == "partial"
    assert projection["missing_archetypes"] == [
        "prediction_model/external_validation",
        "subtype_or_triage",
    ]
    assert projection["next_action"] == "add_missing_study_archetype_fixture"


def test_real_workspace_soak_monitor_blocks_weak_result_without_stop_loss_or_switch_line(
    tmp_path: Path,
) -> None:
    unsafe_root = tmp_path / "weak-unsafe"
    safe_root = tmp_path / "weak-safe"
    unsafe = _ready_matrix_payload("006-weak-unsafe", "subtype_or_triage")
    unsafe["result_strength"] = "weak"
    unsafe["route_action"] = "continue"
    safe = _ready_matrix_payload("007-weak-safe", "observational_real_world")
    safe["result_strength"] = "weak"
    safe["route_action"] = "switch_line"
    _write_json(_matrix_path(unsafe_root), unsafe)
    _write_json(_matrix_path(safe_root), safe)

    projection = _module().build_real_workspace_soak_monitor(study_roots=[unsafe_root, safe_root])

    assert projection["overall_status"] == "blocked"
    by_id = {study["study_id"]: study for study in projection["studies"]}
    assert by_id["006-weak-unsafe"]["next_action"] == (
        "materialize_route_weak_result_requires_stop_loss_or_switch_line"
    )
    assert by_id["006-weak-unsafe"]["blocking_gaps"] == [
        "route:weak_result_requires_stop_loss_or_switch_line"
    ]
    assert by_id["007-weak-safe"]["next_action"] == "switch_line"
    assert "route:weak_result_requires_stop_loss_or_switch_line" not in by_id["007-weak-safe"][
        "blocking_gaps"
    ]


def test_real_workspace_soak_monitor_materializer_writes_only_monitor_artifact(
    tmp_path: Path,
) -> None:
    root = tmp_path / "materialized"
    _write_json(
        _matrix_path(root),
        _ready_matrix_payload("008-materialized", "observational_real_world"),
    )

    result = _module().materialize_real_workspace_soak_monitor(study_roots=[root])

    monitor_path = root / "artifacts" / "medical_paper" / "real_workspace_soak_monitor.json"
    assert result["artifact_path"] == str(monitor_path.resolve())
    assert monitor_path.is_file()
    persisted = json.loads(monitor_path.read_text(encoding="utf-8"))
    assert persisted["surface"] == "real_workspace_soak_monitor"
    assert persisted["authority_contract"]["can_mutate_runtime"] is False
    assert persisted["read_only_monitor_contract"] == {
        "mode": "read_only_monitor",
        "writes_runtime_owned_surfaces": False,
        "writable_surfaces": ["real_workspace_soak_monitor"],
        "prohibited_runtime_owned_surfaces": [
            "study_runtime_status",
            "runtime_watch",
            "publication_eval/latest.json",
            "runtime_escalation_record.json",
            "controller_decisions/latest.json",
            "quality_authorization",
            "submission_authorization",
        ],
    }
    assert result["read_only_monitor_contract"] == persisted["read_only_monitor_contract"]
    assert not (root / "study_runtime_status.json").exists()
    assert not (root / "runtime_watch.json").exists()
    assert not (root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (root / "runtime_escalation_record.json").exists()
    assert not (root / "controller_decisions" / "latest.json").exists()


def test_continuous_real_workspace_monitor_reads_catalog_payload_and_records_drift(
    tmp_path: Path,
) -> None:
    roots = [
        tmp_path / "risk-model",
        tmp_path / "real-world",
        tmp_path / "triage",
    ]
    for root, archetype in zip(
        roots,
        (
            "prediction_model/external_validation",
            "observational_real_world",
            "subtype_or_triage",
        ),
        strict=True,
    ):
        _write_json(_matrix_path(root), _ready_matrix_payload(root.name, archetype))

    catalog_payload = {
        "catalog_id": "sanitized-real-workspace-catalog",
        "studies": [
            {
                "study_id": roots[0].name,
                "study_root": str(roots[0]),
                "previous_readiness_status": "partial",
                "readiness_status": "ready",
                "route_decision": {"action": "continue", "reason": "calibration stable"},
                "revision_reopen_seen": True,
                "runtime_recovery_seen": True,
                "finalize_rebuild_seen": True,
            },
            {
                "study_id": roots[1].name,
                "study_root": str(roots[1]),
                "route_action": "stop_loss",
                "stop_loss_triggered": True,
                "blocked_reason": "",
            },
            {
                "study_id": roots[2].name,
                "study_root": str(roots[2]),
                "readiness": {"overall_status": "ready"},
                "route_action": "continue",
            },
        ],
    }

    projection = _module().build_real_workspace_soak_monitor(
        study_roots=roots,
        catalog_payload=catalog_payload,
    )

    assert projection["monitor_mode"] == "continuous_read_only"
    assert projection["catalog_source"] == {
        "kind": "payload",
        "path": "",
        "catalog_id": "sanitized-real-workspace-catalog",
        "study_count": 3,
    }
    assert projection["overall_status"] == "ready"
    assert projection["stop_loss_triggered"] is True
    assert projection["revision_reopen_seen"] is True
    assert projection["runtime_recovery_seen"] is True
    assert projection["finalize_rebuild_seen"] is True
    assert projection["drift_signals"] == [
        {
            "study_id": "risk-model",
            "signals": ["readiness_status_changed:partial->ready"],
        }
    ]
    assert projection["route_decision_summary"][0] == {
        "study_id": "risk-model",
        "route_action": "continue",
        "result_strength": "adequate",
        "next_action": "continue_multistudy_soak",
        "reason": "calibration stable",
    }


def test_continuous_real_workspace_monitor_reads_catalog_path_without_study_roots(
    tmp_path: Path,
) -> None:
    roots = [
        tmp_path / "catalog-risk",
        tmp_path / "catalog-real-world",
        tmp_path / "catalog-triage",
    ]
    for root, archetype in zip(
        roots,
        (
            "prediction_model/external_validation",
            "observational_real_world",
            "subtype_or_triage",
        ),
        strict=True,
    ):
        _write_json(_matrix_path(root), _ready_matrix_payload(root.name, archetype))
    catalog_path = tmp_path / "workspace_catalog.json"
    _write_json(
        catalog_path,
        {
            "studies": [{"study_root": str(root)} for root in roots],
        },
    )

    projection = _module().build_real_workspace_soak_monitor(
        study_roots=[],
        catalog_path=catalog_path,
    )

    assert projection["overall_status"] == "ready"
    assert projection["catalog_source"]["kind"] == "path"
    assert projection["catalog_source"]["path"] == str(catalog_path.resolve())
    assert {study["study_id"] for study in projection["studies"]} == {
        "catalog-risk",
        "catalog-real-world",
        "catalog-triage",
    }


def test_continuous_real_workspace_monitor_materializer_accepts_catalog_path(
    tmp_path: Path,
) -> None:
    roots = [
        tmp_path / "materialize-catalog-risk",
        tmp_path / "materialize-catalog-real-world",
        tmp_path / "materialize-catalog-triage",
    ]
    for root, archetype in zip(
        roots,
        (
            "prediction_model/external_validation",
            "observational_real_world",
            "subtype_or_triage",
        ),
        strict=True,
    ):
        _write_json(_matrix_path(root), _ready_matrix_payload(root.name, archetype))
    catalog_path = tmp_path / "workspace_catalog.json"
    _write_json(
        catalog_path,
        {
            "studies": [{"study_root": str(root)} for root in roots],
        },
    )

    result = _module().materialize_real_workspace_soak_monitor(
        study_roots=[],
        catalog_path=catalog_path,
    )

    monitor_path = roots[0] / "artifacts" / "medical_paper" / "real_workspace_soak_monitor.json"
    assert result["artifact_path"] == str(monitor_path.resolve())
    assert monitor_path.is_file()


def test_continuous_real_workspace_monitor_cannot_be_ready_without_durable_refs(
    tmp_path: Path,
) -> None:
    catalog_payload = {
        "studies": [
            {
                "study_id": "catalog-only-risk",
                "study_archetype": "prediction_model/external_validation",
                "stages": list(ALL_STAGES),
                "contracts": {
                    "literature_contract": True,
                    "statistical_contract": True,
                    "external_validation_fixture": True,
                },
            },
            {
                "study_id": "catalog-only-real-world",
                "study_archetype": "observational_real_world",
                "stages": list(ALL_STAGES),
                "contracts": {
                    "literature_contract": True,
                    "statistical_contract": True,
                },
                "durable_refs": ["artifacts/medical_paper/readiness.json"],
            },
            {
                "study_id": "catalog-only-triage",
                "study_archetype": "subtype_or_triage",
                "stages": list(ALL_STAGES),
                "contracts": {
                    "literature_contract": True,
                    "statistical_contract": True,
                },
                "durable_refs": ["artifacts/medical_paper/readiness.json"],
            },
        ]
    }

    projection = _module().build_real_workspace_soak_monitor(
        study_roots=[],
        catalog_payload=catalog_payload,
    )

    assert projection["overall_status"] == "partial"
    study = {item["study_id"]: item for item in projection["studies"]}["catalog-only-risk"]
    assert study["status"] == "partial"
    assert "durable_refs:missing" in study["missing_gaps"]
    assert study["next_action"] == "materialize_durable_refs"


def test_continuous_real_workspace_monitor_cannot_be_ready_without_finalize_proof(
    tmp_path: Path,
) -> None:
    catalog_payload = {
        "studies": [
            {
                "study_id": "catalog-risk",
                "study_archetype": "prediction_model/external_validation",
                "stages": list(ALL_STAGES),
                "contracts": {
                    "literature_contract": True,
                    "statistical_contract": True,
                    "external_validation_fixture": True,
                },
                "durable_refs": ["artifacts/medical_paper/readiness.json"],
                "finalize_rebuild_seen": False,
            },
            {
                "study_id": "catalog-real-world",
                "study_archetype": "observational_real_world",
                "stages": list(ALL_STAGES),
                "contracts": {
                    "literature_contract": True,
                    "statistical_contract": True,
                },
                "durable_refs": ["artifacts/medical_paper/readiness.json"],
            },
            {
                "study_id": "catalog-triage",
                "study_archetype": "subtype_or_triage",
                "stages": list(ALL_STAGES),
                "contracts": {
                    "literature_contract": True,
                    "statistical_contract": True,
                },
                "durable_refs": ["artifacts/medical_paper/readiness.json"],
            },
        ]
    }

    projection = _module().build_real_workspace_soak_monitor(
        study_roots=[],
        catalog_payload=catalog_payload,
    )

    assert projection["overall_status"] == "partial"
    study = {item["study_id"]: item for item in projection["studies"]}["catalog-risk"]
    assert study["finalize_rebuild_seen"] is False
    assert "proof:finalize_rebuild" in study["missing_gaps"]
    assert study["next_action"] == "materialize_finalize_rebuild_proof"


def test_continuous_real_workspace_monitor_materializer_appends_scan_history_and_last_green(
    tmp_path: Path,
) -> None:
    roots = [
        tmp_path / "history-risk",
        tmp_path / "history-real-world",
        tmp_path / "history-triage",
    ]
    for root, archetype in zip(
        roots,
        (
            "prediction_model/external_validation",
            "observational_real_world",
            "subtype_or_triage",
        ),
        strict=True,
    ):
        _write_json(_matrix_path(root), _ready_matrix_payload(root.name, archetype))

    ready_catalog = {
        "catalog_id": "continuous-history-catalog",
        "scan_id": "scan-001",
        "scan_started_at": "2026-05-04T01:00:00Z",
        "studies": [
            {
                "study_id": roots[0].name,
                "study_root": str(roots[0]),
                "previous_readiness_status": "partial",
                "readiness_status": "ready",
                "route_decision": {"action": "continue", "reason": "green proof restored"},
                "revision_reopen_seen": True,
                "runtime_recovery_seen": True,
                "finalize_rebuild_seen": True,
            },
            {"study_id": roots[1].name, "study_root": str(roots[1]), "readiness_status": "ready"},
            {"study_id": roots[2].name, "study_root": str(roots[2]), "readiness_status": "ready"},
        ],
    }

    result = _module().materialize_real_workspace_soak_monitor(
        study_roots=roots,
        catalog_payload=ready_catalog,
    )

    monitor_path = Path(result["artifact_path"])
    first = json.loads(monitor_path.read_text(encoding="utf-8"))
    assert first["overall_status"] == "ready"
    assert first["last_green_at"] == "2026-05-04T01:00:00Z"
    assert first["last_green_scan_id"] == "scan-001"
    assert first["drift_history"] == [
        {
            "scan_id": "scan-001",
            "scan_started_at": "2026-05-04T01:00:00Z",
            "overall_status": "ready",
            "next_action": "continue_real_workspace_soak",
            "drift_signals": [
                {
                    "study_id": "history-risk",
                    "signals": ["readiness_status_changed:partial->ready"],
                }
            ],
            "blocked_reason_summary": [],
            "route_decision_summary": first["route_decision_summary"],
            "stop_loss_triggered": False,
            "revision_reopen_seen": True,
            "runtime_recovery_seen": True,
            "finalize_rebuild_seen": True,
        }
    ]

    partial_catalog = {
        "catalog_id": "continuous-history-catalog",
        "scan_id": "scan-002",
        "scan_started_at": "2026-05-04T01:05:00Z",
        "studies": [
            {
                "study_id": roots[0].name,
                "study_root": str(roots[0]),
                "previous_readiness_status": "ready",
                "readiness_status": "partial",
                "blocked_reason": "finalize rebuild proof stale",
                "route_action": "continue",
                "finalize_rebuild_seen": False,
            },
            {
                "study_id": roots[1].name,
                "study_root": str(roots[1]),
                "readiness_status": "ready",
                "route_action": "stop_loss",
                "stop_loss_triggered": True,
            },
            {"study_id": roots[2].name, "study_root": str(roots[2]), "readiness_status": "ready"},
        ],
    }

    _module().materialize_real_workspace_soak_monitor(
        study_roots=roots,
        catalog_payload=partial_catalog,
    )

    second = json.loads(monitor_path.read_text(encoding="utf-8"))
    assert second["overall_status"] == "partial"
    assert second["last_green_at"] == "2026-05-04T01:00:00Z"
    assert second["last_green_scan_id"] == "scan-001"
    assert [entry["scan_id"] for entry in second["drift_history"]] == ["scan-001", "scan-002"]
    assert second["drift_history"][1]["scan_started_at"] == "2026-05-04T01:05:00Z"
    assert second["drift_history"][1]["overall_status"] == "partial"
    assert second["drift_history"][1]["drift_signals"] == [
        {
            "study_id": "history-risk",
            "signals": ["readiness_status_changed:ready->partial"],
        }
    ]
    assert second["drift_history"][1]["blocked_reason_summary"] == [
        {
            "study_id": "history-risk",
            "status": "partial",
            "blocked_reason": "finalize rebuild proof stale",
            "gaps": ["proof:finalize_rebuild"],
        }
    ]
    assert second["drift_history"][1]["stop_loss_triggered"] is True
    assert second["authority_contract"]["can_authorize_quality"] is False
    assert second["authority_contract"]["can_authorize_submission"] is False
    assert second["authority_contract"]["can_authorize_finalize"] is False
