from __future__ import annotations

from typing import Any, Mapping


SCHEMA_VERSION = 1


ARTIFACT_LAYERS: tuple[dict[str, Any], ...] = (
    {
        "layer_id": "canonical_sources",
        "authority": "study_charter_evidence_analysis_ai_review_sources",
        "examples": (
            "study_charter",
            "paper/evidence_ledger.json",
            "analysis_outputs",
            "artifacts/publication_eval/latest.json",
            "paper/medical_manuscript_blueprint.json",
        ),
    },
    {
        "layer_id": "derived_manuscript",
        "authority": "rebuilt_from_canonical_sources",
        "examples": ("paper/manuscript.md", "paper/tables/", "paper/figures/"),
    },
    {
        "layer_id": "submission_package",
        "authority": "controller_authorized_delivery_projection",
        "examples": ("submission_minimal/", "current_package.zip"),
    },
    {
        "layer_id": "human_handoff_mirror",
        "authority": "read_only_handoff_projection",
        "examples": ("manuscript/current_package/", "artifacts/final/"),
    },
)

DERIVED_ARTIFACT_PATHS: tuple[str, ...] = (
    "manuscript/current_package/",
    "artifacts/final/",
    "current_package.zip",
    "submission_minimal/",
)

REBUILD_TARGETS: tuple[str, ...] = (
    "manuscript",
    "figures",
    "tables",
    "submission_package",
)

REBUILD_REQUIRED_INPUTS: tuple[str, ...] = (
    "canonical_sources",
    "ai_reviewer_quality_decision",
)


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _text(value: object) -> str:
    return str(value or "").strip()


def build_canonical_artifact_contract() -> dict[str, Any]:
    return {
        "surface": "canonical_artifact_contract",
        "schema_version": SCHEMA_VERSION,
        "artifact_owner": "MedAutoScience Artifact OS",
        "current_package_can_be_edit_source": False,
        "submission_minimal_can_be_edit_source": False,
        "artifacts_final_can_be_edit_source": False,
        "current_package_can_be_quality_authority": False,
        "submission_minimal_can_be_quality_authority": False,
        "artifacts_final_can_be_quality_authority": False,
        "derived_package_can_authorize_submission": False,
        "artifact_layers": [dict(layer) for layer in ARTIFACT_LAYERS],
        "derived_paths": [
            {
                "path": path,
                "edit_source": False,
                "quality_authority": False,
                "role": "derived_projection",
            }
            for path in DERIVED_ARTIFACT_PATHS
        ],
        "rebuild_chain": [
            "study_charter",
            "evidence_ledger",
            "analysis_outputs",
            "ai_reviewer_quality_decision",
            "canonical_manuscript_source",
            "derived_submission_package",
        ],
        "traceability_requirements": [
            "source_ref",
            "source_fingerprint",
            "quality_decision_ref",
            "controller_decision_ref",
            "generated_at",
        ],
        "rebuild_requirements": [
            {
                "target": target,
                "must_rebuild_from": list(REBUILD_REQUIRED_INPUTS),
                "may_read_derived_projection_as_source": False,
                "may_infer_quality_from_projection": False,
            }
            for target in REBUILD_TARGETS
        ],
        "forbidden_paths_as_authority": list(DERIVED_ARTIFACT_PATHS),
    }


def validate_canonical_artifact_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    forbidden_flags = {
        "current_package_can_be_edit_source": "current_package_used_as_edit_source",
        "submission_minimal_can_be_edit_source": "submission_minimal_used_as_edit_source",
        "artifacts_final_can_be_edit_source": "artifacts_final_used_as_edit_source",
        "current_package_can_be_quality_authority": "current_package_used_as_quality_authority",
        "submission_minimal_can_be_quality_authority": "submission_minimal_used_as_quality_authority",
        "artifacts_final_can_be_quality_authority": "artifacts_final_used_as_quality_authority",
    }
    for flag, code in forbidden_flags.items():
        if contract.get(flag) is not False:
            issues.append({"code": code})
    if contract.get("derived_package_can_authorize_submission") is not False:
        issues.append({"code": "derived_package_authorizes_submission"})
    derived_paths = _list(contract.get("derived_paths"))
    paths_by_name = {
        _text(item.get("path")): item for item in derived_paths if isinstance(item, Mapping)
    }
    for path in DERIVED_ARTIFACT_PATHS:
        item = paths_by_name.get(path)
        if item is None:
            issues.append({"code": "derived_path_missing", "path": path})
            continue
        if item.get("edit_source") is not False:
            issues.append({"code": "derived_path_used_as_edit_source", "path": path})
        if item.get("quality_authority") is not False:
            issues.append({"code": "derived_path_used_as_quality_authority", "path": path})
    layers = _list(contract.get("artifact_layers"))
    if not layers:
        issues.append({"code": "artifact_layers_missing"})
    else:
        first = layers[0]
        if not isinstance(first, Mapping) or _text(first.get("layer_id")) != "canonical_sources":
            issues.append({"code": "canonical_layer_missing"})
        elif _text(first.get("authority")) != "study_charter_evidence_analysis_ai_review_sources":
            issues.append({"code": "canonical_layer_authority_drift"})
    rebuild_requirements = _list(contract.get("rebuild_requirements"))
    requirements_by_target = {
        _text(item.get("target")): item
        for item in rebuild_requirements
        if isinstance(item, Mapping)
    }
    for target in REBUILD_TARGETS:
        item = requirements_by_target.get(target)
        if item is None:
            issues.append({"code": "rebuild_requirement_missing", "target": target})
            continue
        required_inputs = {
            _text(value) for value in _list(item.get("must_rebuild_from")) if _text(value)
        }
        for required_input in REBUILD_REQUIRED_INPUTS:
            if required_input not in required_inputs:
                issues.append(
                    {
                        "code": "rebuild_requirement_missing_input",
                        "target": target,
                        "required_input": required_input,
                    }
                )
        if item.get("may_read_derived_projection_as_source") is not False:
            issues.append({"code": "rebuild_reads_derived_projection_as_source", "target": target})
        if item.get("may_infer_quality_from_projection") is not False:
            issues.append({"code": "rebuild_infers_quality_from_projection", "target": target})
    return {
        "surface": "canonical_artifact_contract_validation",
        "schema_version": SCHEMA_VERSION,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
    }
