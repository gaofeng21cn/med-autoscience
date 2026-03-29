from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from med_autoscience.adapters import aris_sidecar as adapter


SCHEMA_VERSION = 1
SIDECAR_ID = "aris"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _require_mapping(payload: dict[str, object], key: str) -> dict[str, object]:
    value = payload.get(key)
    if not isinstance(value, dict) or not value:
        raise ValueError(f"ARIS input contract requires {key} as a non-empty object")
    return value


def _require_string(payload: dict[str, object], key: str, *, path: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"ARIS input contract requires {path}.{key} as a non-empty string")
    return value.strip()


def _require_string_list(payload: dict[str, object], key: str, *, path: str, min_items: int = 1) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or len(value) < min_items or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"ARIS input contract requires {path}.{key} as a list of at least {min_items} non-empty strings")
    return [item.strip() for item in value]


def _normalize_input_contract(payload: dict[str, object]) -> dict[str, object]:
    problem_anchor = _require_mapping(payload, "problem_anchor")
    data_contract = _require_mapping(payload, "data_contract")
    evaluation_contract = _require_mapping(payload, "evaluation_contract")
    innovation_scope = _require_mapping(payload, "innovation_scope")
    optional_context = payload.get("optional_context")

    _require_string(problem_anchor, "clinical_question", path="problem_anchor")
    _require_string(problem_anchor, "research_object", path="problem_anchor")
    _require_string(problem_anchor, "endpoint", path="problem_anchor")
    _require_string(problem_anchor, "task_type", path="problem_anchor")

    _require_string(data_contract, "dataset_version", path="data_contract")
    _require_string_list(data_contract, "modalities", path="data_contract")
    if "splits" not in data_contract:
        raise ValueError("ARIS input contract requires data_contract.splits")
    _require_string(data_contract, "preprocessing_boundary", path="data_contract")
    external_validation_required = data_contract.get("external_validation_required")
    if not isinstance(external_validation_required, bool):
        raise ValueError("ARIS input contract requires data_contract.external_validation_required as a boolean")

    _require_string(evaluation_contract, "primary_metric", path="evaluation_contract")
    _require_string_list(evaluation_contract, "secondary_metrics", path="evaluation_contract")
    _require_string_list(evaluation_contract, "required_baselines", path="evaluation_contract")
    _require_string_list(evaluation_contract, "statistics", path="evaluation_contract")
    compute_budget = evaluation_contract.get("compute_budget")
    if not isinstance(compute_budget, dict) or not compute_budget:
        raise ValueError("ARIS input contract requires evaluation_contract.compute_budget as a non-empty object")

    _require_string_list(innovation_scope, "allowed", path="innovation_scope")
    _require_string_list(innovation_scope, "forbidden", path="innovation_scope")

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
        "writing_questions": writing_questions,
        "optional_context": optional_context,
    }


def recommend_aris_sidecar(*, quest_root: Path, payload: dict[str, object]) -> dict[str, object]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
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
    recommendation_payload = {
        "status": status,
        "quest_root": str(resolved_quest_root),
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
    if status == "recommended":
        persisted_payload = dict(recommendation_payload)
        persisted_payload["status"] = "awaiting_user_confirmation"
        persisted_payload["recorded_at"] = utc_now()
        adapter.dump_json(adapter.sidecar_root(resolved_quest_root) / "recommendation.json", persisted_payload)
    return recommendation_payload


def _validate_user_confirmation(payload: dict[str, object]) -> dict[str, object]:
    value = payload.get("user_confirmation")
    if not isinstance(value, dict):
        raise ValueError("ARIS sidecar provisioning requires user_confirmation")
    if value.get("confirmed") is not True:
        raise ValueError("ARIS sidecar provisioning requires user_confirmation.confirmed=true")
    confirmed_by = value.get("confirmed_by")
    confirmed_at = value.get("confirmed_at")
    if not isinstance(confirmed_by, str) or not confirmed_by.strip():
        raise ValueError("ARIS sidecar provisioning requires user_confirmation.confirmed_by")
    if not isinstance(confirmed_at, str) or not confirmed_at.strip():
        raise ValueError("ARIS sidecar provisioning requires user_confirmation.confirmed_at")
    return value


def provision_aris_sidecar(*, quest_root: Path, payload: dict[str, object]) -> dict[str, object]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    recommendation = adapter.load_json(adapter.sidecar_root(resolved_quest_root) / "recommendation.json")
    if not isinstance(recommendation, dict) or recommendation.get("status") != "awaiting_user_confirmation":
        raise ValueError("ARIS sidecar provisioning requires an awaiting_user_confirmation recommendation gate")
    user_confirmation = _validate_user_confirmation(payload)
    contract_payload = dict(payload)
    contract_payload.pop("user_confirmation", None)
    normalized_contract = _normalize_input_contract(contract_payload)
    input_contract_hash = adapter.build_contract_hash(normalized_contract)
    sidecar_root = adapter.sidecar_root(resolved_quest_root)
    input_contract_path = sidecar_root / "input_contract.json"
    existing_contract = adapter.load_json(input_contract_path)
    if isinstance(existing_contract, dict):
        existing_hash = adapter.build_contract_hash(existing_contract)
        if existing_hash != input_contract_hash:
            raise ValueError("ARIS sidecar contract drift detected for the existing frozen input contract")

    adapter.dump_json(input_contract_path, normalized_contract)
    adapter.handoff_root(resolved_quest_root).mkdir(parents=True, exist_ok=True)
    state_payload = {
        "schema_version": SCHEMA_VERSION,
        "sidecar_id": SIDECAR_ID,
        "provider": "aris",
        "status": "contract_frozen",
        "quest_root": str(resolved_quest_root),
        "sidecar_root": str(sidecar_root),
        "handoff_root": str(adapter.handoff_root(resolved_quest_root)),
        "input_contract_hash": input_contract_hash,
        "input_contract_path": str(input_contract_path),
        "user_confirmation": user_confirmation,
        "updated_at": utc_now(),
    }
    adapter.dump_json(sidecar_root / "sidecar_state.json", state_payload)
    return {
        "status": "contract_frozen",
        "quest_root": str(resolved_quest_root),
        "sidecar_root": str(sidecar_root),
        "handoff_root": str(adapter.handoff_root(resolved_quest_root)),
        "input_contract_hash": input_contract_hash,
        "input_contract_path": str(input_contract_path),
        "state_path": str(sidecar_root / "sidecar_state.json"),
    }


def _load_sidecar_manifest(*, handoff_root: Path) -> dict[str, object]:
    manifest_path = handoff_root / "sidecar_manifest.json"
    manifest = adapter.load_json(manifest_path)
    if not isinstance(manifest, dict):
        raise ValueError("ARIS sidecar handoff requires a valid sidecar_manifest.json")
    return manifest


def _load_claim_evidence_pairs(*, handoff_root: Path) -> list[dict[str, object]]:
    claim_map_path = handoff_root / "claim_to_evidence_map.md"
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
            if not (handoff_root / artifact_name).is_file():
                raise ValueError(
                    "ARIS sidecar import requires claim_to_evidence_map.md to reference existing handoff evidence artifacts"
                )
    return claim_evidence_pairs


def _validate_import_manifest(*, manifest: dict[str, object], input_contract_hash: str) -> None:
    if manifest.get("provider") != "aris":
        raise ValueError("ARIS sidecar import requires sidecar_manifest.json provider=aris")
    if manifest.get("status") != "result_ready":
        raise ValueError("ARIS sidecar import requires sidecar_manifest.json status=result_ready")
    if manifest.get("input_contract_hash") != input_contract_hash:
        raise ValueError("ARIS sidecar import requires sidecar_manifest.json to match the frozen input contract hash")
    artifacts_generated = manifest.get("artifacts_generated")
    required_files = set(adapter.required_handoff_files())
    if not isinstance(artifacts_generated, list) or not required_files.issubset({item for item in artifacts_generated if isinstance(item, str)}):
        raise ValueError("ARIS sidecar import requires sidecar_manifest.json artifacts_generated to cover all required handoff files")


def import_aris_sidecar_result(*, quest_root: Path) -> dict[str, object]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    sidecar_root = adapter.sidecar_root(resolved_quest_root)
    handoff_root = adapter.handoff_root(resolved_quest_root)
    input_contract_path = sidecar_root / "input_contract.json"
    input_contract = adapter.load_json(input_contract_path)
    if not isinstance(input_contract, dict):
        raise FileNotFoundError(f"Frozen ARIS input contract not found: {input_contract_path}")
    input_contract_hash = adapter.build_contract_hash(input_contract)

    missing = [name for name in adapter.required_handoff_files() if not (handoff_root / name).is_file()]
    if missing:
        raise FileNotFoundError("Missing required ARIS handoff files: " + ", ".join(missing))

    manifest = _load_sidecar_manifest(handoff_root=handoff_root)
    _validate_import_manifest(manifest=manifest, input_contract_hash=input_contract_hash)
    claim_evidence_pairs = _load_claim_evidence_pairs(handoff_root=handoff_root)

    artifact_root = adapter.artifact_root(resolved_quest_root)
    adapter.copy_file(source=input_contract_path, destination=artifact_root / "input_contract.json")
    for name in adapter.required_handoff_files():
        adapter.copy_file(source=handoff_root / name, destination=artifact_root / name)

    imported_manifest = dict(manifest)
    imported_manifest.update(
        {
            "schema_version": SCHEMA_VERSION,
            "input_contract_path": str(artifact_root / "input_contract.json"),
            "source_sidecar_root": str(sidecar_root),
            "claim_evidence_pairs": claim_evidence_pairs,
            "imported_at": utc_now(),
        }
    )
    adapter.dump_json(artifact_root / "sidecar_manifest.json", imported_manifest)
    return {
        "status": "imported",
        "quest_root": str(resolved_quest_root),
        "sidecar_root": str(sidecar_root),
        "artifact_root": str(artifact_root),
        "imported_manifest_path": str(artifact_root / "sidecar_manifest.json"),
        "input_contract_hash": input_contract_hash,
    }


def resolve_aris_sidecar_artifacts(*, quest_root: Path) -> dict[str, object]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    artifact_root = adapter.artifact_root(resolved_quest_root)
    input_contract_path = artifact_root / "input_contract.json"
    if not input_contract_path.is_file():
        return {
            "status": "absent",
            "quest_root": str(resolved_quest_root),
            "artifact_root": str(artifact_root),
            "artifacts": {},
        }

    required_paths = {"input_contract.json": input_contract_path}
    for name in adapter.required_handoff_files():
        path = artifact_root / name
        if not path.is_file():
            raise FileNotFoundError(f"Imported ARIS artifact missing from audit surface: {path}")
        required_paths[name] = path
    return {
        "status": "imported",
        "quest_root": str(resolved_quest_root),
        "artifact_root": str(artifact_root),
        "artifacts": {name: str(path) for name, path in required_paths.items()},
    }
