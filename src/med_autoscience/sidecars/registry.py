from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import yaml


ImportFinalizer = Callable[[Path, Path, dict[str, object], dict[str, object], str, str | None], dict[str, object]]
RecommendationEvaluator = Callable[[dict[str, object]], dict[str, object]]
ContractNormalizer = Callable[[dict[str, object]], dict[str, object]]
InstanceResolver = Callable[[dict[str, object]], str | None]


@dataclass(frozen=True)
class SidecarProviderSpec:
    provider_id: str
    domain_id: str
    instance_key_name: str | None
    required_handoff_files: tuple[str, ...]
    resolve_instance_id: InstanceResolver
    evaluate_recommendation: RecommendationEvaluator
    normalize_input_contract: ContractNormalizer
    finalize_import: ImportFinalizer


def _require_mapping(payload: dict[str, object], key: str, *, label: str) -> dict[str, object]:
    value = payload.get(key)
    if not isinstance(value, dict) or not value:
        raise ValueError(f"{label} requires {key} as a non-empty object")
    return value


def _require_string(payload: dict[str, object], key: str, *, label: str, path: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} requires {path}.{key} as a non-empty string")
    return value.strip()


def _require_string_list(
    payload: dict[str, object],
    key: str,
    *,
    label: str,
    path: str,
    min_items: int = 1,
) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or len(value) < min_items:
        raise ValueError(f"{label} requires {path}.{key} as a list of at least {min_items} non-empty strings")
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{label} requires {path}.{key} as a list of at least {min_items} non-empty strings")
        normalized.append(item.strip())
    return normalized


def _resolve_aris_instance_id(payload: dict[str, object]) -> str | None:
    return None


def _evaluate_aris_recommendation(payload: dict[str, object]) -> dict[str, object]:
    blockers: list[str] = []
    if payload.get("requires_algorithmic_innovation") is not True:
        blockers.append("algorithmic_innovation_not_required")
    if payload.get("task_definition_ready") is not True:
        blockers.append("task_definition_not_ready")
    if payload.get("data_contract_frozen") is not True:
        blockers.append("data_contract_not_frozen")
    if payload.get("evaluation_contract_ready") is not True:
        blockers.append("evaluation_contract_not_ready")
    if payload.get("compute_budget_available") is not True:
        blockers.append("compute_budget_unavailable")
    if not any(payload.get(key) is True for key in ("baseline_available", "reference_paper_available", "base_repo_available")):
        blockers.append("no_baseline_or_reference_context")
    status = "recommended" if not blockers else "not_candidate"
    return {
        "status": status,
        "recommendation": "request_user_confirmation" if status == "recommended" else "stay_mainline",
        "blockers": blockers,
        "signals": {
            "requires_algorithmic_innovation": bool(payload.get("requires_algorithmic_innovation")),
            "task_definition_ready": bool(payload.get("task_definition_ready")),
            "data_contract_frozen": bool(payload.get("data_contract_frozen")),
            "evaluation_contract_ready": bool(payload.get("evaluation_contract_ready")),
            "compute_budget_available": bool(payload.get("compute_budget_available")),
            "baseline_available": bool(payload.get("baseline_available")),
            "reference_paper_available": bool(payload.get("reference_paper_available")),
            "base_repo_available": bool(payload.get("base_repo_available")),
        },
    }


def _normalize_aris_input_contract(payload: dict[str, object]) -> dict[str, object]:
    label = "ARIS input contract"
    problem_anchor = _require_mapping(payload, "problem_anchor", label=label)
    data_contract = _require_mapping(payload, "data_contract", label=label)
    evaluation_contract = _require_mapping(payload, "evaluation_contract", label=label)
    innovation_scope = _require_mapping(payload, "innovation_scope", label=label)
    optional_context = payload.get("optional_context")

    _require_string(problem_anchor, "clinical_question", label=label, path="problem_anchor")
    _require_string(problem_anchor, "research_object", label=label, path="problem_anchor")
    _require_string(problem_anchor, "endpoint", label=label, path="problem_anchor")
    _require_string(problem_anchor, "task_type", label=label, path="problem_anchor")

    _require_string(data_contract, "dataset_version", label=label, path="data_contract")
    _require_string_list(data_contract, "modalities", label=label, path="data_contract")
    if "splits" not in data_contract:
        raise ValueError("ARIS input contract requires data_contract.splits")
    _require_string(data_contract, "preprocessing_boundary", label=label, path="data_contract")
    external_validation_required = data_contract.get("external_validation_required")
    if not isinstance(external_validation_required, bool):
        raise ValueError("ARIS input contract requires data_contract.external_validation_required as a boolean")

    _require_string(evaluation_contract, "primary_metric", label=label, path="evaluation_contract")
    _require_string_list(evaluation_contract, "secondary_metrics", label=label, path="evaluation_contract")
    _require_string_list(evaluation_contract, "required_baselines", label=label, path="evaluation_contract")
    _require_string_list(evaluation_contract, "statistics", label=label, path="evaluation_contract")
    compute_budget = evaluation_contract.get("compute_budget")
    if not isinstance(compute_budget, dict) or not compute_budget:
        raise ValueError("ARIS input contract requires evaluation_contract.compute_budget as a non-empty object")

    _require_string_list(innovation_scope, "allowed", label=label, path="innovation_scope")
    _require_string_list(innovation_scope, "forbidden", label=label, path="innovation_scope")

    writing_questions = payload.get("writing_questions")
    if not isinstance(writing_questions, list) or len(writing_questions) < 4:
        raise ValueError("ARIS input contract requires writing_questions with at least 4 items")
    if any(not isinstance(item, str) or not item.strip() for item in writing_questions):
        raise ValueError("ARIS input contract requires writing_questions to contain only non-empty strings")

    if optional_context is None:
        optional_context = {}
    if not isinstance(optional_context, dict):
        raise ValueError("ARIS input contract requires optional_context to be an object when provided")

    return {
        "problem_anchor": problem_anchor,
        "data_contract": data_contract,
        "evaluation_contract": evaluation_contract,
        "innovation_scope": innovation_scope,
        "writing_questions": [str(item).strip() for item in writing_questions],
        "optional_context": optional_context,
    }


def _load_claim_evidence_pairs(artifact_root: Path) -> list[dict[str, object]]:
    claim_map_path = artifact_root / "claim_to_evidence_map.md"
    raw_text = claim_map_path.read_text(encoding="utf-8")
    if not raw_text.startswith("---\n"):
        raise ValueError("ARIS sidecar import requires claim_to_evidence_map.md to start with YAML front matter")
    try:
        _, front_matter, _ = raw_text.split("---\n", 2)
    except ValueError as exc:
        raise ValueError("ARIS sidecar import requires claim_to_evidence_map.md with closed YAML front matter") from exc
    payload = yaml.safe_load(front_matter) or {}
    claim_evidence_pairs = payload.get("claim_evidence_pairs")
    if not isinstance(claim_evidence_pairs, list) or not claim_evidence_pairs:
        raise ValueError("ARIS sidecar import requires claim_to_evidence_map.md claim_evidence_pairs")
    for item in claim_evidence_pairs:
        if not isinstance(item, dict):
            raise ValueError("ARIS sidecar import requires claim_to_evidence_map.md claim_evidence_pairs entries to be objects")
        claim_id = item.get("claim_id")
        evidence_artifacts = item.get("evidence_artifacts")
        if not isinstance(claim_id, str) or not claim_id.strip():
            raise ValueError("ARIS sidecar import requires claim_to_evidence_map.md claim_evidence_pairs[*].claim_id")
        if not isinstance(evidence_artifacts, list) or not evidence_artifacts:
            raise ValueError("ARIS sidecar import requires claim_to_evidence_map.md claim_evidence_pairs[*].evidence_artifacts")
        for artifact_name in evidence_artifacts:
            if not isinstance(artifact_name, str) or not artifact_name.strip():
                raise ValueError("ARIS sidecar import requires evidence_artifacts entries to be non-empty strings")
            if not (artifact_root / artifact_name).is_file():
                raise ValueError(
                    "ARIS sidecar import requires claim_to_evidence_map.md to reference existing handoff evidence artifacts"
                )
    return claim_evidence_pairs


def _finalize_aris_import(
    quest_root: Path,
    artifact_root: Path,
    manifest: dict[str, object],
    input_contract: dict[str, object],
    input_contract_hash: str,
    instance_id: str | None,
) -> dict[str, object]:
    del quest_root, manifest, input_contract, input_contract_hash, instance_id
    return {"claim_evidence_pairs": _load_claim_evidence_pairs(artifact_root)}


AUTOFIGURE_ALLOWED_TYPES = {
    "method_overview",
    "study_workflow",
    "graphical_abstract",
    "cohort_schema",
}
AUTOFIGURE_ALLOWED_PAPER_ROLES = {"main_text", "appendix", "graphical_abstract"}
AUTOFIGURE_MANDATORY_FORBIDDEN_SCOPE = {
    "metric_number_editing",
    "claim_change",
    "result_plot_generation",
}


def _resolve_autofigure_edit_instance_id(payload: dict[str, object]) -> str | None:
    top_level = payload.get("figure_id")
    if isinstance(top_level, str) and top_level.strip():
        return top_level.strip()
    figure_request = payload.get("figure_request")
    if isinstance(figure_request, dict):
        nested = figure_request.get("figure_id")
        if isinstance(nested, str) and nested.strip():
            return nested.strip()
    return None


def _evaluate_autofigure_edit_recommendation(payload: dict[str, object]) -> dict[str, object]:
    blockers: list[str] = []
    figure_id = _resolve_autofigure_edit_instance_id(payload)
    if not figure_id:
        blockers.append("missing_figure_id")
    if payload.get("figure_ticket_open") is not True:
        blockers.append("figure_ticket_not_open")
    if payload.get("storyboard_ready") is not True:
        blockers.append("storyboard_not_ready")
    if payload.get("source_artifacts_ready") is not True:
        blockers.append("source_artifacts_not_ready")
    if payload.get("paper_role_allowed") is not True:
        blockers.append("paper_role_not_allowed")
    if payload.get("non_evidence_figure") is not True:
        blockers.append("result_figure_not_supported")
    if payload.get("editable_svg_required") is not True:
        blockers.append("editable_svg_not_requested")
    status = "recommended" if not blockers else "not_candidate"
    return {
        "status": status,
        "recommendation": "request_user_confirmation" if status == "recommended" else "stay_mainline",
        "blockers": blockers,
        "signals": {
            "figure_id": figure_id,
            "figure_ticket_open": bool(payload.get("figure_ticket_open")),
            "storyboard_ready": bool(payload.get("storyboard_ready")),
            "source_artifacts_ready": bool(payload.get("source_artifacts_ready")),
            "paper_role_allowed": bool(payload.get("paper_role_allowed")),
            "non_evidence_figure": bool(payload.get("non_evidence_figure")),
            "editable_svg_required": bool(payload.get("editable_svg_required")),
        },
    }


def _normalize_autofigure_edit_input_contract(payload: dict[str, object]) -> dict[str, object]:
    label = "AutoFigure-Edit input contract"
    figure_request = _require_mapping(payload, "figure_request", label=label)
    source_contract = _require_mapping(payload, "source_contract", label=label)
    output_contract = _require_mapping(payload, "output_contract", label=label)
    editing_scope = _require_mapping(payload, "editing_scope", label=label)
    optional_context = payload.get("optional_context")

    figure_id = _require_string(figure_request, "figure_id", label=label, path="figure_request")
    figure_type = _require_string(figure_request, "figure_type", label=label, path="figure_request")
    paper_role = _require_string(figure_request, "paper_role", label=label, path="figure_request")
    _require_string(figure_request, "title", label=label, path="figure_request")
    _require_string(figure_request, "question_answered", label=label, path="figure_request")
    _require_string(figure_request, "caption_takeaway", label=label, path="figure_request")
    if figure_type not in AUTOFIGURE_ALLOWED_TYPES:
        raise ValueError(
            "AutoFigure-Edit input contract only supports figure_request.figure_type in "
            + ", ".join(sorted(AUTOFIGURE_ALLOWED_TYPES))
        )
    if paper_role not in AUTOFIGURE_ALLOWED_PAPER_ROLES:
        raise ValueError(
            "AutoFigure-Edit input contract only supports figure_request.paper_role in "
            + ", ".join(sorted(AUTOFIGURE_ALLOWED_PAPER_ROLES))
        )

    _require_string(source_contract, "storyboard_path", label=label, path="source_contract")
    _require_string_list(source_contract, "source_artifacts", label=label, path="source_contract")
    reference_style_paths = source_contract.get("reference_style_paths")
    if reference_style_paths is None:
        reference_style_paths = []
    if not isinstance(reference_style_paths, list) or any(not isinstance(item, str) or not item.strip() for item in reference_style_paths):
        raise ValueError("AutoFigure-Edit input contract requires source_contract.reference_style_paths as a list of strings")

    required_formats = _require_string_list(output_contract, "required_formats", label=label, path="output_contract")
    if not {"svg", "pdf", "png"}.issubset(set(required_formats)):
        raise ValueError("AutoFigure-Edit input contract requires output_contract.required_formats to include svg, pdf, and png")
    editable_svg_required = output_contract.get("editable_svg_required")
    caption_safe = output_contract.get("caption_safe")
    if editable_svg_required is not True:
        raise ValueError("AutoFigure-Edit input contract requires output_contract.editable_svg_required=true")
    if not isinstance(caption_safe, bool):
        raise ValueError("AutoFigure-Edit input contract requires output_contract.caption_safe as a boolean")

    allowed = _require_string_list(editing_scope, "allowed", label=label, path="editing_scope")
    forbidden = _require_string_list(editing_scope, "forbidden", label=label, path="editing_scope")
    if not AUTOFIGURE_MANDATORY_FORBIDDEN_SCOPE.issubset(set(forbidden)):
        raise ValueError(
            "AutoFigure-Edit input contract requires editing_scope.forbidden to include "
            + ", ".join(sorted(AUTOFIGURE_MANDATORY_FORBIDDEN_SCOPE))
        )

    if optional_context is None:
        optional_context = {}
    if not isinstance(optional_context, dict):
        raise ValueError("AutoFigure-Edit input contract requires optional_context to be an object when provided")

    return {
        "figure_request": {
            **figure_request,
            "figure_id": figure_id,
            "figure_type": figure_type,
            "paper_role": paper_role,
        },
        "source_contract": {
            **source_contract,
            "reference_style_paths": [str(item).strip() for item in reference_style_paths],
        },
        "output_contract": output_contract,
        "editing_scope": {
            "allowed": allowed,
            "forbidden": forbidden,
        },
        "optional_context": optional_context,
    }


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


def _finalize_autofigure_edit_import(
    quest_root: Path,
    artifact_root: Path,
    manifest: dict[str, object],
    input_contract: dict[str, object],
    input_contract_hash: str,
    instance_id: str | None,
) -> dict[str, object]:
    del input_contract_hash
    expected_figure_id = str(input_contract["figure_request"]["figure_id"])
    if not instance_id or instance_id != expected_figure_id:
        raise ValueError("AutoFigure-Edit sidecar import requires instance_id to match figure_request.figure_id")
    if manifest.get("figure_id") != expected_figure_id:
        raise ValueError("AutoFigure-Edit sidecar import requires sidecar_manifest.json figure_id to match the frozen contract")

    source_trace = _load_json(artifact_root / "source_trace.json")
    source_items = source_trace.get("source_artifacts")
    if not isinstance(source_items, list) or not source_items:
        raise ValueError("AutoFigure-Edit sidecar import requires source_trace.json source_artifacts")
    normalized_source_trace: list[dict[str, str]] = []
    for item in source_items:
        if not isinstance(item, dict):
            raise ValueError("AutoFigure-Edit sidecar import requires source_trace.json entries to be objects")
        path = item.get("path")
        role = item.get("role")
        if not isinstance(path, str) or not path.strip():
            raise ValueError("AutoFigure-Edit sidecar import requires source_trace.json entries to include path")
        if not isinstance(role, str) or not role.strip():
            raise ValueError("AutoFigure-Edit sidecar import requires source_trace.json entries to include role")
        source_path = quest_root / path
        if not source_path.is_file():
            raise ValueError("AutoFigure-Edit sidecar import requires source_trace.json to reference existing quest files")
        normalized_source_trace.append({"path": path.strip(), "role": role.strip()})

    figure_catalog_entry = _load_json(artifact_root / "figure_catalog_entry.json")
    if figure_catalog_entry.get("figure_id") != expected_figure_id:
        raise ValueError("AutoFigure-Edit sidecar import requires figure_catalog_entry.json figure_id to match the frozen contract")
    paper_role = figure_catalog_entry.get("paper_role")
    if not isinstance(paper_role, str) or paper_role not in AUTOFIGURE_ALLOWED_PAPER_ROLES:
        raise ValueError("AutoFigure-Edit sidecar import requires figure_catalog_entry.json paper_role to stay within the allowed publication surface")
    export_files = figure_catalog_entry.get("export_files")
    if not isinstance(export_files, list) or not export_files:
        raise ValueError("AutoFigure-Edit sidecar import requires figure_catalog_entry.json export_files")
    export_paths: list[str] = []
    for filename in export_files:
        if not isinstance(filename, str) or not filename.strip():
            raise ValueError("AutoFigure-Edit sidecar import requires figure_catalog_entry.json export_files to contain only strings")
        artifact_path = artifact_root / filename
        if not artifact_path.is_file():
            raise ValueError("AutoFigure-Edit sidecar import requires figure_catalog_entry.json export_files to reference copied artifacts")
        export_paths.append(str(artifact_path.relative_to(quest_root)))

    normalized_catalog_entry = {
        "figure_id": expected_figure_id,
        "title": str(figure_catalog_entry.get("title") or ""),
        "caption": str(figure_catalog_entry.get("caption") or ""),
        "paper_role": paper_role,
        "export_paths": export_paths,
        "source_artifacts": list(figure_catalog_entry.get("source_artifacts") or []),
    }
    (artifact_root / "figure_catalog_entry.json").write_text(
        json.dumps(normalized_catalog_entry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "figure_catalog_entry": normalized_catalog_entry,
        "source_trace": {"source_artifacts": normalized_source_trace},
    }


_PROVIDERS = {
    "aris": SidecarProviderSpec(
        provider_id="aris",
        domain_id="algorithm_research",
        instance_key_name=None,
        required_handoff_files=(
            "algorithm_scout_report.md",
            "innovation_hypotheses.md",
            "final_method_proposal.md",
            "experiment_plan.md",
            "experiment_results_summary.md",
            "review_loop_summary.md",
            "prior_limitations.md",
            "why_our_method_can_work.md",
            "claim_to_evidence_map.md",
            "sidecar_manifest.json",
        ),
        resolve_instance_id=_resolve_aris_instance_id,
        evaluate_recommendation=_evaluate_aris_recommendation,
        normalize_input_contract=_normalize_aris_input_contract,
        finalize_import=_finalize_aris_import,
    ),
    "autofigure_edit": SidecarProviderSpec(
        provider_id="autofigure_edit",
        domain_id="figures",
        instance_key_name="figure_id",
        required_handoff_files=(
            "final_figure.svg",
            "final_figure.pdf",
            "preview.png",
            "caption.md",
            "source_trace.json",
            "figure_catalog_entry.json",
            "sidecar_manifest.json",
        ),
        resolve_instance_id=_resolve_autofigure_edit_instance_id,
        evaluate_recommendation=_evaluate_autofigure_edit_recommendation,
        normalize_input_contract=_normalize_autofigure_edit_input_contract,
        finalize_import=_finalize_autofigure_edit_import,
    ),
}


def get_provider(provider_id: str) -> SidecarProviderSpec:
    try:
        return _PROVIDERS[str(provider_id).strip()]
    except KeyError as exc:
        raise ValueError(f"Unknown sidecar provider: {provider_id}") from exc


def list_providers() -> tuple[SidecarProviderSpec, ...]:
    return tuple(_PROVIDERS.values())
