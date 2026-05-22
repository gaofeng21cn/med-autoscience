from __future__ import annotations

import importlib
import json
from pathlib import Path


def _module():
    return importlib.import_module("med_autoscience.controllers.medical_paper_pilot_harness")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _matrix_path(root: Path) -> Path:
    return root / "artifacts" / "medical_paper" / "real_study_soak_matrix_evidence.json"


def _field(ref: str, *, status: str = "ready") -> dict[str, object]:
    return {
        "status": status,
        "durable_refs": [ref],
    }


def _pilot_fields(study_id: str) -> dict[str, object]:
    return {
        "literature": _field(f"{study_id}/artifacts/medical_paper/literature_intelligence_os.json"),
        "route_decision": _field(f"{study_id}/artifacts/controller_decisions/route_decision.json"),
        "statistical_discipline": _field(f"{study_id}/artifacts/medical_paper/statistical_discipline_operations.json"),
        "stop_loss_switch_line": _field(f"{study_id}/artifacts/medical_paper/stop_loss_memo.json"),
        "authoring": _field(f"{study_id}/artifacts/medical_paper/authoring_runtime_authorization.json"),
        "ai_reviewer": _field(f"{study_id}/artifacts/publication_eval/latest.json"),
        "soak": _field(f"{study_id}/artifacts/medical_paper/real_workspace_soak_monitor.json"),
        "finalize_rebuild": _field(f"{study_id}/artifacts/submission/current_package_rebuild.json"),
    }


def _ready_matrix_payload(study_id: str, archetype: str) -> dict[str, object]:
    return {
        "surface": "real_study_soak_matrix_evidence",
        "study_id": study_id,
        "study_archetype": archetype,
        "stages": [
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
        ],
        "contracts": {
            "literature_contract": True,
            "statistical_contract": True,
            "external_validation_fixture": archetype == "prediction_model/external_validation",
        },
        "result_strength": "adequate",
        "route_action": "continue",
        "durable_refs": [
            f"{study_id}/artifacts/medical_paper/real_study_soak_matrix_evidence.json"
        ],
    }


def _ready_roots(tmp_path: Path) -> list[Path]:
    roots = [
        tmp_path / "risk-model",
        tmp_path / "real-world",
        tmp_path / "triage",
    ]
    archetypes = [
        "prediction_model/external_validation",
        "observational_real_world",
        "subtype_or_triage",
    ]
    for root, archetype in zip(roots, archetypes, strict=True):
        _write_json(_matrix_path(root), _ready_matrix_payload(root.name, archetype))
    return roots


def _catalog_for(roots: list[Path]) -> dict[str, object]:
    return {
        "catalog_id": "sanitized-pilot-catalog",
        "studies": [
            {
                "study_id": root.name,
                "study_root": str(root),
                "study_archetype": archetype,
                "pilot_fields": _pilot_fields(root.name),
                "durable_refs": [f"{root.name}/artifacts/medical_paper/readiness.json"],
                "finalize_rebuild_seen": True,
                "revision_reopen_seen": True,
                "runtime_recovery_seen": True,
            }
            for root, archetype in zip(
                roots,
                [
                    "prediction_model/external_validation",
                    "observational_real_world",
                    "subtype_or_triage",
                ],
                strict=True,
            )
        ],
    }


def test_pilot_harness_proves_three_archetype_research_loop_read_only(tmp_path: Path) -> None:
    roots = _ready_roots(tmp_path)

    projection = _module().build_medical_paper_pilot_harness(
        study_roots=roots,
        catalog_payload=_catalog_for(roots),
    )

    assert projection["surface"] == "medical_paper_pilot_harness"
    assert projection["overall_status"] == "ready"
    assert projection["missing_archetypes"] == []
    assert projection["next_action"] == {
        "action_id": "continue_managed_execution",
        "summary": "pilot harness 已证明三类 study 的自动论文闭环可监督。",
        "study_id": "",
        "field_key": "",
    }
    assert projection["authority_contract"] == {
        "authority": "observability_read_model_only",
        "read_model_only": True,
        "can_mutate_runtime": False,
        "can_authorize_quality": False,
        "can_authorize_submission": False,
        "can_authorize_finalize": False,
        "mechanical_projection_can_authorize_quality": False,
    }
    assert len(projection["pilot_studies"]) == 3
    for study in projection["pilot_studies"]:
        assert study["status"] == "ready"
        assert {field["field_key"] for field in study["fields"]} == set(_module().PILOT_FIELDS)
        assert all(field["status"] == "ready" for field in study["fields"])
        assert all(field["durable_refs"] for field in study["fields"])
    assert not (roots[0] / "artifacts" / "medical_paper" / "medical_paper_pilot_harness.json").exists()
    assert not (roots[0] / "progress_projection.json").exists()


def test_pilot_harness_blocks_missing_ai_reviewer_and_keeps_scientific_next_action(
    tmp_path: Path,
) -> None:
    roots = _ready_roots(tmp_path)
    catalog = _catalog_for(roots)
    first = catalog["studies"][0]
    assert isinstance(first, dict)
    fields = first["pilot_fields"]
    assert isinstance(fields, dict)
    fields["ai_reviewer"] = {"status": "blocked", "missing_reason": "missing_ai_reviewer_provenance"}

    projection = _module().build_medical_paper_pilot_harness(
        study_roots=roots,
        catalog_payload=catalog,
    )

    assert projection["overall_status"] == "blocked"
    assert projection["next_action"] == {
        "action_id": "repair_pilot_harness_field",
        "summary": "补 AI reviewer provenance 和 recheck 记录",
        "study_id": roots[0].name,
        "field_key": "ai_reviewer",
    }
    by_id = {study["study_id"]: study for study in projection["pilot_studies"]}
    reviewer_field = [
        field for field in by_id[roots[0].name]["fields"] if field["field_key"] == "ai_reviewer"
    ][0]
    assert reviewer_field["status"] == "blocked"
    assert reviewer_field["missing_reason"] == "missing_ai_reviewer_provenance"
    assert reviewer_field["why_it_matters"].startswith("AI reviewer provenance")


def test_pilot_harness_materializer_writes_only_its_read_model(tmp_path: Path) -> None:
    roots = _ready_roots(tmp_path)

    result = _module().materialize_medical_paper_pilot_harness(
        study_roots=roots,
        catalog_payload=_catalog_for(roots),
    )

    pilot_path = roots[0] / "artifacts" / "medical_paper" / "medical_paper_pilot_harness.json"
    assert result["artifact_path"] == str(pilot_path.resolve())
    assert pilot_path.is_file()
    persisted = json.loads(pilot_path.read_text(encoding="utf-8"))
    assert persisted["surface"] == "medical_paper_pilot_harness"
    assert persisted["read_only_contract"]["writes_runtime_owned_surfaces"] is False
    assert persisted["read_only_contract"]["writable_surfaces"] == ["medical_paper_pilot_harness"]
    assert not (roots[0] / "progress_projection.json").exists()
    assert not (roots[0] / "domain_health_diagnostic.json").exists()
    assert not (roots[0] / "controller_decisions" / "latest.json").exists()
