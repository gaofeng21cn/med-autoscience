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
