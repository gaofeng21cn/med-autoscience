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


V2_SURFACES = (
    "literature_provider_runtime",
    "route_decision_orchestrator",
    "statistical_discipline_operations",
    "revision_rebuttal_loop",
    "authoring_runtime_authorization",
    "real_workspace_soak_monitor",
)
LEGACY_SURFACES = (
    "literature_scout",
    "study_line_selection",
    "archetype_analysis_contract",
    "bounded_analysis_candidate_board",
    "stop_loss_memo",
    "target_journal_writing_layer",
    "real_study_soak_matrix_evidence",
)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _matrix_payload(study_id: str, archetype: str) -> dict[str, object]:
    contracts = {
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
        "fixtures": {"external_validation": True},
        "result_strength": "adequate",
        "route_action": "continue",
        "durable_refs": [
            f"{study_id}/artifacts/medical_paper/readiness.json",
            f"{study_id}/artifacts/publication_eval/latest.json",
        ],
    }


def _readiness_payload(study_root: Path, *, archetype: str) -> dict[str, object]:
    surfaces = [
        {
            "surface_key": surface_key,
            "label": surface_key.replace("_", " ").title(),
            "status": "present",
            "missing_reason": "",
            "artifact_path": f"artifacts/medical_paper/{surface_key}.json",
            "evidence_refs": [f"artifacts/medical_paper/{surface_key}.json"],
            "required_for_ready": True,
        }
        for surface_key in V2_SURFACES
    ]
    surfaces.extend(
        {
            "surface_key": surface_key,
            "label": surface_key.replace("_", " ").title(),
            "status": "present",
            "missing_reason": "",
            "artifact_path": f"artifacts/medical_paper/{surface_key}.json",
            "evidence_refs": [f"artifacts/medical_paper/{surface_key}.json"],
            "required_for_ready": True,
        }
        for surface_key in LEGACY_SURFACES
    )
    return {
        "surface": "medical_paper_readiness",
        "study_id": study_root.name,
        "study_archetype": archetype,
        "overall_status": "ready",
        "ready_count": len(surfaces),
        "required_count": len(surfaces),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "capability_surfaces": surfaces,
        "next_action": {
            "action_id": "continue_managed_execution",
            "surface_key": None,
            "summary": "自动医学论文能力闭环已具备可见 readiness surface，可继续托管执行。",
        },
    }


def _materialize_fixture(tmp_path: Path) -> list[Path]:
    roots = [
        tmp_path / "001-risk-model",
        tmp_path / "002-real-world",
        tmp_path / "003-triage",
    ]
    archetypes = [
        "prediction_model/external_validation",
        "observational_real_world",
        "subtype_or_triage",
    ]
    for root, archetype in zip(roots, archetypes, strict=True):
        _write_json(
            root / "artifacts" / "medical_paper" / "readiness.json",
            _readiness_payload(root, archetype=archetype),
        )
        _write_json(
            root / "artifacts" / "medical_paper" / "real_study_soak_matrix_evidence.json",
            _matrix_payload(root.name, archetype),
        )
    return roots


def test_final_soak_reads_canonical_readiness_and_preserves_observability_authority(
    tmp_path: Path,
) -> None:
    monitor = importlib.import_module("med_autoscience.controllers.real_workspace_soak_monitor")
    roots = _materialize_fixture(tmp_path)

    result = monitor.materialize_real_workspace_soak_monitor(study_roots=roots)

    persisted_path = roots[0] / "artifacts" / "medical_paper" / "real_workspace_soak_monitor.json"
    persisted = json.loads(persisted_path.read_text(encoding="utf-8"))
    assert result["artifact_path"] == str(persisted_path.resolve())
    assert persisted["overall_status"] == "ready"
    assert persisted["next_action"] == "continue_real_workspace_soak"
    assert persisted["missing_archetypes"] == []
    assert persisted["authority_contract"] == {
        "authority": "observability_read_model_only",
        "can_mutate_runtime": False,
        "can_authorize_quality": False,
        "can_authorize_submission": False,
        "can_authorize_finalize": False,
    }
    assert {study["source_surface"] for study in persisted["studies"]} == {
        "real_study_soak_matrix_evidence"
    }
    assert all(study["status"] == "ready" for study in persisted["studies"])


def test_final_soak_uses_canonical_readiness_when_matrix_is_absent(tmp_path: Path) -> None:
    monitor = importlib.import_module("med_autoscience.controllers.real_workspace_soak_monitor")
    roots = _materialize_fixture(tmp_path)
    for root in roots:
        (root / "artifacts" / "medical_paper" / "real_study_soak_matrix_evidence.json").unlink()

    projection = monitor.build_real_workspace_soak_monitor(study_roots=roots)

    assert projection["overall_status"] == "ready"
    assert {study["source_surface"] for study in projection["studies"]} == {
        "medical_paper_readiness"
    }
    assert all(
        study["source_path"].endswith("artifacts/medical_paper/readiness.json")
        for study in projection["studies"]
    )


def test_final_soak_readiness_payload_projects_into_mcp_and_product_actions(tmp_path: Path) -> None:
    mcp_projection = importlib.import_module("med_autoscience.mcp_server_parts.study_progress_projection")
    cockpit_payload = importlib.import_module(
        "med_autoscience.controllers.product_entry_parts.workspace_cockpit.cockpit_payload"
    )
    root = _materialize_fixture(tmp_path)[0]
    readiness = json.loads(
        (root / "artifacts" / "medical_paper" / "readiness.json").read_text(encoding="utf-8")
    )
    readiness["capability_surfaces"][0]["status"] = "missing"
    readiness["capability_surfaces"][0]["missing_reason"] = "missing_provider_provenance"
    readiness["overall_status"] = "blocked"

    compact = mcp_projection.compact_study_progress_projection(
        {"study_id": root.name, "medical_paper_readiness": readiness}
    )
    missing = compact["medical_paper_readiness"]["missing_surfaces"][0]
    normalized = cockpit_payload._normalized_medical_paper_readiness_projection(readiness)
    card = normalized["action_cards"][0]

    assert missing["surface_key"] == "literature_provider_runtime"
    assert missing["action_id"] == "run_provider_literature_scout"
    assert missing["action_label"] == "联网补文献"
    assert card["action_id"] == "run_provider_literature_scout"
    assert card["authority"] == "observability_projection_only"
    assert card["quality_claim_authorized"] is False
    assert normalized["mechanical_projection_can_authorize_quality"] is False
