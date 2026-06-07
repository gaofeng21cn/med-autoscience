from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any

from med_autoscience.runtime_protocol import domain_authority_refs_index


SCHEMA_VERSION = 1
SURFACE_KIND = "stage_artifact_delta_materializer"
_PAPER_STUDY_STAGE_PACK_REF = "contracts/mas-paper-study-stage-pack.json"
_REPO_ROOT = Path(__file__).resolve().parents[3]
_MANIFEST_FILENAME = "stage_manifest.json"
_RECEIPT_FILENAME = "owner_receipt.json"
_RECEIPT_REF = f"receipts/{_RECEIPT_FILENAME}"
_INPUT_REFS_REF = "inputs/consumed_artifact_refs.json"
_LINEAGE_REF = "lineage/prov.json"
_PROJECTION_REF = "projection/current_owner_delta.json"
_TERMINAL_STAGE_ID = "08-publication_package_handoff"
_MAX_SOURCE_REFS_PER_DIRECTORY = 20
_MAX_SOURCE_REF_DIRECTORY_VISITS = 64
_MAX_SOURCE_REF_CHILDREN_PER_DIRECTORY = 128

_ROLE_SOURCE_CANDIDATES: dict[str, tuple[str, ...]] = {
    "study_truth_snapshot": ("study.yaml", "brief.md"),
    "source_readiness_assessment": (
        "data_input/dataset_manifest.yaml",
        "paper/source_authority_manifest.json",
        "artifacts/truth/latest.json",
        "artifacts/intake",
    ),
    "study_intake_owner_receipt": (
        "runtime_binding.yaml",
        "artifacts/study_delivery_mirror",
        "artifacts/stage_knowledge/scout",
    ),
    "protocol_specification": (
        "protocol.md",
        "paper/medical_analysis_contract.json",
        "paper/medical_reporting_contract.json",
    ),
    "statistical_analysis_plan": (
        "analysis/clean_room_runbook.md",
        "analysis/paper_facing_evidence_contract.md",
        "paper/methods_implementation_manifest.json",
        "paper/paper_experiment_matrix.json",
    ),
    "protocol_owner_receipt": (
        "artifacts/controller/publication_work_unit_lifecycle",
        "artifacts/stage_knowledge/decision",
    ),
    "data_asset_manifest": (
        "data_input/dataset_manifest.yaml",
        "paper/derived_analysis_manifest.json",
        "paper/analysis_catalog.json",
        "paper/paper_analysis_catalog.json",
        "paper/paper_analysis_groups.json",
    ),
    "cohort_definition_lock": (
        "paper/cohort_flow.json",
        "paper/baseline_inventory.json",
        "analysis/phenotype_ready/variable_contract.csv",
        "artifacts/intake",
    ),
    "source_readiness_receipt": (
        "artifacts/runtime/work_unit_ledger/events.jsonl",
        "artifacts/controller/source_provenance/latest.json",
        "artifacts/controller/analysis_harmonization/latest.json",
    ),
    "analysis_run_record": (
        "paper/analysis_results.json",
        "paper/analysis_results",
        "paper/analysis-results",
        "experiments/analysis-results",
        "analysis/clean_room_execution",
    ),
    "primary_results_artifact_set": (
        "paper/ready_analysis_groups.json",
        "paper/paper_facing_analysis_groups.json",
        "paper/analysis_groups.json",
        "paper/analysis_groups",
        "paper/tables/generated",
        "paper/figures/generated",
    ),
    "reproducibility_lineage": (
        "paper/manuscript_safe_reproducibility_supplement.json",
        "manuscript/current_package/reproducibility",
        "paper/source_authority_manifest.json",
        "paper/numeric_trace.json",
    ),
    "evidence_synthesis_matrix": (
        "paper/evidence_ledger.json",
        "artifacts/evidence_ledger.json",
        "paper/evidence_ledger.md",
        "paper/analysis_claim_evidence_repair_map.json",
        "paper/analysis_claim_evidence_repair_map.md",
    ),
    "claim_evidence_map": (
        "paper/claim_evidence_map.json",
        "paper/claim_evidence_traceability_map.json",
        "paper/table_figure_claim_map.json",
    ),
    "memory_accept_reject_receipts": (
        "artifacts/stage_knowledge/memory_write_router_receipts",
        "memory/portfolio/research_memory",
        "literature",
    ),
    "manuscript_draft_package": (
        "paper/draft.md",
        "paper/manuscript_submission.md",
        "paper/build/review_manuscript.md",
        "manuscript/manuscript.docx",
        "manuscript/paper.pdf",
    ),
    "manuscript_claim_trace": (
        "paper/claim_evidence_map.json",
        "paper/manuscript_coverage.json",
        "paper/results_narrative_map.json",
        "paper/medical_story_contract.json",
        "paper/story_contract.json",
    ),
    "artifact_package_authority_receipt": (
        "paper/paper_bundle_manifest.json",
        "paper/display_registry.json",
        "paper/figure_catalog.json",
        "paper/table_catalog.json",
        "artifacts/package_authority",
        "artifacts/delivery_bundles",
    ),
    "independent_reviewer_record": (
        "paper/review/review_ledger.json",
        "manuscript/review/review_ledger.json",
        "artifacts/review",
        "artifacts/publication_eval/latest.json",
        "artifacts/reports/medical_reporting_audit/latest.json",
        "artifacts/reports/publishability_gate/latest.json",
    ),
    "revision_action_matrix": (
        "paper/rebuttal/review_matrix.json",
        "paper/rebuttal/action_plan.md",
        "paper/revision_log.jsonl",
        "artifacts/controller/quality_repair_batch/latest.json",
        "artifacts/controller/gate_clearing_batch/latest.json",
    ),
    "reviewer_quality_receipt": (
        "artifacts/publication_eval/latest.json",
        "artifacts/agent_lab/medical_manuscript_quality/latest_suite.json",
        "paper/medical_prose_review.json",
        "paper/statistical_reviewer_audit.json",
    ),
    "publication_package_manifest": (
        "paper/submission_minimal",
        "paper/paper_bundle_manifest.json",
        "paper/submission_manifest.json",
        "manuscript/current_package",
        "manuscript/current_package.zip",
        "artifacts/submission_minimal",
        "artifacts/delivery",
    ),
    "publication_gate_receipt": (
        "artifacts/reports/publishability_gate/latest.json",
        "artifacts/publication_eval/latest.json",
        "artifacts/publication_gate_specificity",
    ),
    "handoff_owner_receipt": (
        "artifacts/controller_decisions/latest.json",
        "artifacts/controller/gate_clearing_batch/latest.json",
        "artifacts/delivery/latest_submission_authority.json",
        "artifacts/submission_authority",
    ),
}


def materialize_stage_artifact_delta(
    *,
    study_id: str,
    study_root: Path,
    workspace_root: Path | None = None,
    stage_ids: Iterable[str] | None = None,
    apply: bool = False,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    resolved_workspace_root = (
        Path(workspace_root).expanduser().resolve()
        if workspace_root is not None
        else _infer_workspace_root(resolved_study_root)
    )
    selected_stage_ids = tuple(dict.fromkeys(str(item) for item in (stage_ids or ())))
    stage_specs = _selected_stage_specs(selected_stage_ids)
    generated_at = _utc_now()
    stage_results = [
        _materialize_stage(
            study_id=study_id,
            study_root=resolved_study_root,
            workspace_root=resolved_workspace_root,
            stage_spec=stage_spec,
            generated_at=generated_at,
            apply=apply,
        )
        for stage_spec in stage_specs
    ]
    materialized_count = sum(1 for item in stage_results if item["status"] == "materialized")
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": "materialized" if apply else "dry_run",
        "study_id": str(study_id),
        "study_root": str(resolved_study_root),
        "workspace_root": str(resolved_workspace_root),
        "generated_at": generated_at,
        "domain_stage_pack_ref": _PAPER_STUDY_STAGE_PACK_REF,
        "selected_stage_ids": [str(item["stage_id"]) for item in stage_specs],
        "materialized_stage_count": materialized_count,
        "body_policy": _body_policy(),
        "authority_boundary": _authority_boundary(),
        "stages": stage_results,
    }


def _materialize_stage(
    *,
    study_id: str,
    study_root: Path,
    workspace_root: Path,
    stage_spec: Mapping[str, Any],
    generated_at: str,
    apply: bool,
) -> dict[str, Any]:
    stage_id = _require_text(stage_spec.get("stage_id"), "stage_id")
    roles = _stage_roles(stage_spec)
    artifact_refs = [str(item["artifact_ref"]) for item in roles]
    role_results = [
        _role_bundle(
            study_id=study_id,
            study_root=study_root,
            stage_id=stage_id,
            role=str(role["role"]),
            artifact_ref=str(role["artifact_ref"]),
            generated_at=generated_at,
        )
        for role in roles
    ]
    manifest = _manifest_payload(
        study_id=study_id,
        stage_id=stage_id,
        artifact_refs=artifact_refs,
        role_results=role_results,
        generated_at=generated_at,
    )
    receipt = _receipt_payload(
        study_id=study_id,
        stage_id=stage_id,
        artifact_refs=artifact_refs,
        role_results=role_results,
        generated_at=generated_at,
    )
    manifest_ref = f"artifacts/stage_outputs/{stage_id}/{_MANIFEST_FILENAME}"
    receipt_ref = f"artifacts/stage_outputs/{stage_id}/{_RECEIPT_REF}"
    input_refs = _input_refs_payload(
        study_id=study_id,
        stage_id=stage_id,
        role_results=role_results,
        generated_at=generated_at,
    )
    lineage = _lineage_payload(
        study_id=study_id,
        stage_id=stage_id,
        artifact_refs=artifact_refs,
        receipt_ref=receipt["receipt_ref"],
        generated_at=generated_at,
    )
    current_owner_delta = _current_owner_delta_payload(stage_id=stage_id, receipt_ref=receipt_ref)
    if apply:
        for role_result in role_results:
            _write_json(study_root / str(role_result["artifact_ref"]), role_result["payload"])
        stage_root = study_root / "artifacts" / "stage_outputs" / stage_id
        _write_json(study_root / manifest_ref, manifest)
        _write_json(stage_root / _INPUT_REFS_REF, input_refs)
        _write_json(stage_root / _LINEAGE_REF, lineage)
        _write_json(stage_root / _PROJECTION_REF, current_owner_delta)
        _write_json(study_root / receipt_ref, receipt)
        index_result = domain_authority_refs_index.record_paper_work_unit_receipt(
            study_root=study_root,
            quest_root=workspace_root / "runtime" / "quests" / str(study_id),
            receipt=receipt,
            receipt_path=study_root / receipt_ref,
            db_path=domain_authority_refs_index.workspace_authority_refs_index_path(workspace_root),
        )
    else:
        index_result = None
    stage_closeout = _stage_closeout(stage_id=stage_id)
    return {
        "stage_id": stage_id,
        "status": "materialized" if apply else "dry_run",
        "artifact_refs": artifact_refs,
        "manifest_ref": manifest_ref,
        "receipt_ref": receipt_ref,
        "source_ref_count": sum(len(item["source_refs"]) for item in role_results),
        "role_bundles": [
            {
                "role": item["role"],
                "artifact_ref": item["artifact_ref"],
                "source_refs": item["source_refs"],
            }
            for item in role_results
        ],
        "stage_closeout": stage_closeout,
        "domain_authority_ref_index": index_result,
    }


def _role_bundle(
    *,
    study_id: str,
    study_root: Path,
    stage_id: str,
    role: str,
    artifact_ref: str,
    generated_at: str,
) -> dict[str, Any]:
    source_refs = _source_refs_for_role(study_root=study_root, role=role)
    payload = {
        "surface_kind": "stage_artifact_ref_bundle",
        "schema_version": SCHEMA_VERSION,
        "study_id": study_id,
        "stage_id": stage_id,
        "role": role,
        "artifact_ref": artifact_ref,
        "generated_at": generated_at,
        "source_refs": source_refs,
        "source_ref_count": len(source_refs),
        "source_ref_fingerprint": _fingerprint(source_refs),
        "body_included": False,
        "legacy_body_copied": False,
        "refs_only": True,
        "paper_or_package_mutated": False,
        "publication_truth_mutated": False,
        "authority_boundary": _authority_boundary(),
    }
    return {
        "role": role,
        "artifact_ref": artifact_ref,
        "source_refs": source_refs,
        "payload": payload,
    }


def _source_refs_for_role(*, study_root: Path, role: str) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for candidate_ref in _ROLE_SOURCE_CANDIDATES.get(role, ()):
        candidate = study_root / candidate_ref
        if candidate.is_file():
            refs.append(_source_ref_payload(study_root=study_root, path=candidate))
        elif candidate.is_dir():
            refs.extend(
                _source_ref_payload(study_root=study_root, path=path)
                for path in _sample_files(candidate)
            )
    if refs:
        return _dedupe_refs(refs)
    return [
        {
            "ref": "study.yaml",
            "path": str(study_root / "study.yaml"),
            "exists": (study_root / "study.yaml").exists(),
            "source_role": "fallback_study_truth_locator",
            "body_included": False,
        }
    ]


def _source_ref_payload(*, study_root: Path, path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    try:
        ref = resolved.relative_to(study_root).as_posix()
    except ValueError:
        ref = str(resolved)
    stat = resolved.stat()
    return {
        "ref": ref,
        "path": str(resolved),
        "exists": True,
        "bytes": stat.st_size,
        "sha256": _file_sha256(resolved),
        "body_included": False,
    }


def _sample_files(path: Path) -> tuple[Path, ...]:
    samples: list[Path] = []
    pending = [path]
    visited_directories = 0
    while (
        pending
        and len(samples) < _MAX_SOURCE_REFS_PER_DIRECTORY
        and visited_directories < _MAX_SOURCE_REF_DIRECTORY_VISITS
    ):
        current = pending.pop(0)
        visited_directories += 1
        try:
            children = current.iterdir()
        except OSError:
            continue
        child_count = 0
        child_directories: list[Path] = []
        for child in children:
            if child_count >= _MAX_SOURCE_REF_CHILDREN_PER_DIRECTORY:
                break
            child_count += 1
            try:
                if child.is_file():
                    samples.append(child)
                    if len(samples) >= _MAX_SOURCE_REFS_PER_DIRECTORY:
                        return tuple(samples)
                elif child.is_dir():
                    child_directories.append(child)
            except OSError:
                continue
        remaining_directory_budget = max(
            0,
            _MAX_SOURCE_REF_DIRECTORY_VISITS - visited_directories - len(pending),
        )
        pending.extend(child_directories[:remaining_directory_budget])
    return tuple(samples)


def _manifest_payload(
    *,
    study_id: str,
    stage_id: str,
    artifact_refs: list[str],
    role_results: list[dict[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    return {
        "surface_kind": "stage_manifest",
        "schema_version": SCHEMA_VERSION,
        "study_id": study_id,
        "stage_id": stage_id,
        "stage_run_id": f"stage-run::{study_id}::{stage_id}",
        "attempt_id": f"stage-artifact-materialize::{study_id}::{stage_id}",
        "work_unit": "materialize_stage_artifact_delta",
        "generated_at": generated_at,
        "artifact_refs": artifact_refs,
        "stage_run_ref": f"stage-run::{study_id}::{stage_id}",
        "required_input_artifact_refs": [_INPUT_REFS_REF],
        "required_role_artifacts": [
            {
                "role": item["role"],
                "artifact_ref": item["artifact_ref"],
            }
            for item in role_results
        ],
        "produced_artifact_refs": artifact_refs,
        "owner_receipt_refs": [_RECEIPT_REF],
        "typed_blocker_refs": [],
        "lineage_refs": [_LINEAGE_REF],
        "projection_refs": [_PROJECTION_REF],
        "roles": [
            {
                "role": item["role"],
                "artifact_ref": item["artifact_ref"],
                "source_refs": item["source_refs"],
            }
            for item in role_results
        ],
        "source_artifact_refs_are_locators_only": True,
        "body_included": False,
        "legacy_body_copied": False,
        "authority_boundary": _authority_boundary(),
    }


def _receipt_payload(
    *,
    study_id: str,
    stage_id: str,
    artifact_refs: list[str],
    role_results: list[dict[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    source_fingerprint = _fingerprint(
        [
            {
                "role": role_result["role"],
                "artifact_ref": role_result["artifact_ref"],
                "source_refs": role_result["source_refs"],
            }
            for role_result in role_results
        ]
    )
    receipt_id = f"stage-artifact-delta:{study_id}:{stage_id}:{source_fingerprint[:16]}"
    return {
        "surface_kind": "mas_stage_owner_receipt",
        "schema_version": SCHEMA_VERSION,
        "receipt_id": receipt_id,
        "study_id": study_id,
        "quest_id": study_id,
        "stage_id": stage_id,
        "owner": "MedAutoScience",
        "authority_type": "medical_owner_receipt",
        "receipt_ref": receipt_id,
        "schema_refs": [
            "contracts/stage_artifact_kernel_adoption.json#/semantic_consumability_gate",
            "contracts/mas-paper-study-stage-pack.json#/authority_boundary",
        ],
        "capability_refs": [
            "contracts/mas-paper-study-stage-pack.json#/authority_boundary/mas_authority_functions/medical_owner_receipt",
        ],
        "domain_semantic_refs": {
            "owner_route_refs": [f"stage-artifact-owner-route:{study_id}:{stage_id}"],
            "medical_owner_receipt_refs": [receipt_id],
        },
        "receipt_kind": "stage_artifact_delta",
        "receipt_status": "materialized",
        "artifact_refs": artifact_refs,
        "consumed_artifact_refs": [
            source_ref
            for role_result in role_results
            for source_ref in role_result["source_refs"]
        ],
        "produced_artifact_refs": artifact_refs,
        "lineage_refs": [_LINEAGE_REF],
        "next_owner_delta": _current_owner_delta_payload(
            stage_id=stage_id,
            receipt_ref=f"artifacts/stage_outputs/{stage_id}/{_RECEIPT_REF}",
        ),
        "idempotency_key": receipt_id,
        "intent_fingerprint": _fingerprint([{"stage_id": stage_id, "artifact_refs": artifact_refs}]),
        "source_fingerprint": source_fingerprint,
        "source_refs": [
            source_ref
            for role_result in role_results
            for source_ref in role_result["source_refs"]
        ],
        "recorded_at": generated_at,
        "started_worker": False,
        "body_included": False,
        "refs_only": True,
        "legacy_body_copied": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_ready": False,
        "can_authorize_submission_ready": False,
        "stage_closeout": _stage_closeout(stage_id=stage_id),
        "authority_boundary": _authority_boundary(),
    }


def _input_refs_payload(
    *,
    study_id: str,
    stage_id: str,
    role_results: list[dict[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    return {
        "surface_kind": "stage_consumed_artifact_refs",
        "schema_version": SCHEMA_VERSION,
        "study_id": study_id,
        "stage_id": stage_id,
        "generated_at": generated_at,
        "artifact_refs": [
            source_ref
            for role_result in role_results
            for source_ref in role_result["source_refs"]
        ],
        "body_included": False,
    }


def _lineage_payload(
    *,
    study_id: str,
    stage_id: str,
    artifact_refs: list[str],
    receipt_ref: str,
    generated_at: str,
) -> dict[str, Any]:
    return {
        "surface_kind": "stage_lineage_prov",
        "schema_version": SCHEMA_VERSION,
        "study_id": study_id,
        "stage_id": stage_id,
        "generated_at": generated_at,
        "produced_artifact_refs": artifact_refs,
        "owner_receipt_refs": [receipt_ref],
        "body_included": False,
    }


def _current_owner_delta_payload(*, stage_id: str, receipt_ref: str) -> dict[str, Any]:
    if stage_id == _TERMINAL_STAGE_ID:
        return {
            "owner": "publication_gate_owner",
            "action": "publication_handoff_owner_gate",
            "reason": "terminal_stage_artifact_delta_materialized",
            "source_ref": receipt_ref,
        }
    return {
        "owner": "MedAutoScience",
        "action": "advance_stage_from_stage_artifact_receipt",
        "reason": "stage_artifact_delta_materialized",
        "source_ref": receipt_ref,
    }


def _stage_closeout(*, stage_id: str) -> dict[str, Any]:
    terminal = stage_id == _TERMINAL_STAGE_ID
    return {
        "minimum_durable_output_present": True,
        "owner_receipt_present": True,
        "nonterminal_stage_can_advance": not terminal,
        "publishability_required_for_stage_advance": terminal,
        "submission_readiness_required_for_stage_advance": terminal,
        "terminal_publication_handoff": terminal,
    }


def _selected_stage_specs(stage_ids: tuple[str, ...]) -> tuple[Mapping[str, Any], ...]:
    stage_pack = _load_paper_study_stage_pack()
    stages = [stage for stage in stage_pack["stages"] if isinstance(stage, Mapping)]
    if not stage_ids:
        return tuple(stages)
    known = {_require_text(stage.get("stage_id"), "stage_id"): stage for stage in stages}
    missing = [stage_id for stage_id in stage_ids if stage_id not in known]
    if missing:
        raise ValueError(f"unknown stage_ids: {', '.join(missing)}")
    return tuple(known[stage_id] for stage_id in stage_ids)


def _stage_roles(stage_spec: Mapping[str, Any]) -> tuple[dict[str, str], ...]:
    roles: list[dict[str, str]] = []
    for item in stage_spec.get("stable_artifact_roles") or []:
        if not isinstance(item, Mapping):
            continue
        roles.append(
            {
                "role": _require_text(item.get("role"), "role"),
                "artifact_ref": _require_text(item.get("artifact_ref"), "artifact_ref"),
            }
        )
    if not roles:
        raise ValueError(f"stage {stage_spec.get('stage_id')} has no artifact roles")
    return tuple(roles)


def _load_paper_study_stage_pack() -> dict[str, Any]:
    path = _REPO_ROOT / _PAPER_STUDY_STAGE_PACK_REF
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping) or payload.get("surface_kind") != "mas_paper_study_stage_pack":
        raise ValueError(f"invalid stage pack: {_PAPER_STUDY_STAGE_PACK_REF}")
    return dict(payload)


def _infer_workspace_root(study_root: Path) -> Path:
    if study_root.parent.name == "studies":
        return study_root.parent.parent.resolve()
    return study_root.parent.resolve()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _body_policy() -> dict[str, bool]:
    return {
        "refs_only": True,
        "legacy_body_copied": False,
        "paper_or_package_mutated": False,
        "publication_truth_mutated": False,
    }


def _authority_boundary() -> dict[str, bool]:
    return {
        "refs_only": True,
        "can_write_paper_or_package": False,
        "can_write_publication_eval": False,
        "can_write_controller_decisions": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_ready": False,
        "can_authorize_submission_ready": False,
    }


def _dedupe_refs(refs: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for ref in refs:
        key = str(ref.get("ref") or ref.get("path") or "")
        if key in seen:
            continue
        seen.add(key)
        result.append(dict(ref))
    return result


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fingerprint(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _require_text(value: object, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} must be non-empty")
    return text


__all__ = ["SURFACE_KIND", "materialize_stage_artifact_delta"]
