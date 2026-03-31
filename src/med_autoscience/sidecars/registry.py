from __future__ import annotations

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
}


def get_provider(provider_id: str) -> SidecarProviderSpec:
    try:
        return _PROVIDERS[str(provider_id).strip()]
    except KeyError as exc:
        raise ValueError(f"Unknown sidecar provider: {provider_id}") from exc


def list_providers() -> tuple[SidecarProviderSpec, ...]:
    return tuple(_PROVIDERS.values())
