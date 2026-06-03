from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.opl_artifact_operating_contract import (
    CONTRACT_REF as OPL_ARTIFACT_OPERATING_CONTRACT_REF,
    consumability_gate_projection,
    current_pointer_contract_projection,
    load_opl_artifact_operating_contract,
    operating_contract_projection,
    promotion_protocol_steps,
)
from med_autoscience.stage_surface_contract import (
    MAIN_STAGE_ROUTE_IDS,
    build_stage_surface_contract,
)

ALLOWED_ARTIFACT_STATUSES = (
    "missing",
    "missing_manifest_or_receipt",
    "partial",
    "artifact_delta_present",
    "ready_for_review",
    "blocked_by_required_artifact",
    "terminal_delivered",
)

_STATUS_MISSING = "missing"
_STATUS_MISSING_CONTRACT = "missing_manifest_or_receipt"
_STATUS_PARTIAL = "partial"
_STATUS_DELTA = "artifact_delta_present"
_STAGE_NATIVE_ARTIFACT_CONTRACT_REF = "mas-opl-stage-native-artifact-contract.v1"
_MANIFEST_FILENAME = "stage_artifact_manifest.json"
_RECEIPT_FILENAME = "owner_receipt.json"

_STAGE_OUTPUT_SURFACES: dict[str, tuple[tuple[str, str], ...]] = {
    "scout": (
        ("scout_note", "artifacts/stage_outputs/scout/scout_note.md"),
        ("literature_scout_os", "artifacts/stage_outputs/scout/literature_scout_os.json"),
        ("route_recommendation", "artifacts/stage_outputs/scout/route_recommendation.json"),
        ("open_questions", "artifacts/stage_outputs/scout/open_questions.json"),
    ),
    "idea": (
        ("line_selection_note", "artifacts/stage_outputs/idea/line_selection_note.md"),
        ("study_line_scorecard", "artifacts/stage_outputs/idea/study_line_scorecard.json"),
        ("next_route_recommendation", "artifacts/stage_outputs/idea/next_route_recommendation.json"),
        ("claim_sketch", "artifacts/stage_outputs/idea/claim_sketch.md"),
    ),
    "baseline": (
        ("baseline_artifact_set", "artifacts/stage_outputs/baseline/baseline_artifact_set.json"),
        ("baseline_summary", "artifacts/stage_outputs/baseline/baseline_summary.md"),
        (
            "next_route_recommendation",
            "artifacts/stage_outputs/baseline/next_route_recommendation.json",
        ),
    ),
    "experiment": (
        ("primary_result_artifact_set", "artifacts/stage_outputs/experiment/primary_result.json"),
        ("experiment_summary", "artifacts/stage_outputs/experiment/experiment_summary.md"),
        (
            "next_route_recommendation",
            "artifacts/stage_outputs/experiment/next_route_recommendation.json",
        ),
    ),
    "analysis-campaign": (
        (
            "analysis_campaign_summary",
            "artifacts/stage_outputs/analysis-campaign/analysis_campaign_summary.md",
        ),
        (
            "bounded_analysis_candidate_board",
            "artifacts/stage_outputs/analysis-campaign/bounded_analysis_candidate_board.json",
        ),
        ("evidence_refs", "paper/evidence_ledger.json"),
        ("remaining_gaps", "artifacts/stage_outputs/analysis-campaign/remaining_gaps.json"),
    ),
    "write": (
        ("manuscript_draft", "artifacts/stage_outputs/write/manuscript_draft.json"),
        ("canonical_draft", "paper/draft.md"),
        ("claim_evidence_map", "paper/claim_evidence_map.json"),
        ("reviewer_first_pass_note", "paper/review/reviewer_first_pass.md"),
        ("first_draft_quality_note", "artifacts/stage_outputs/write/first_draft_quality_note.md"),
    ),
    "review": (
        ("reviewer_action_matrix", "artifacts/stage_outputs/review/reviewer_action_matrix.json"),
        ("review_record", "paper/review/review_ledger.json"),
        ("publication_eval", "artifacts/publication_eval/latest.json"),
    ),
    "finalize": (
        ("publication_eval", "artifacts/publication_eval/latest.json"),
        ("controller_decision", "artifacts/controller_decisions/latest.json"),
        ("package_freshness_proof", "artifacts/stage_outputs/finalize/package_freshness_proof.json"),
        ("declarations", "artifacts/stage_outputs/finalize/declarations.json"),
    ),
    "decision": (
        ("decision_memo", "artifacts/stage_outputs/decision/decision_memo.md"),
        ("stop_loss_or_go_record", "artifacts/stage_outputs/decision/stop_loss_or_go_record.json"),
    ),
    "journal-resolution": (
        (
            "journal_resolution_record",
            "artifacts/stage_outputs/journal-resolution/journal_resolution_record.json",
        ),
        ("journal_guideline_refs", "artifacts/stage_outputs/journal-resolution/guideline_refs.json"),
    ),
}


def build_stage_artifact_index(*, study_id: str, study_root: Path) -> dict[str, Any]:
    resolved_study_root = study_root.expanduser().resolve()
    stage_contract = build_stage_surface_contract()
    operating_contract = load_opl_artifact_operating_contract()
    operating_projection = operating_contract_projection(operating_contract)
    promotion_protocol = promotion_protocol_steps(operating_contract)
    consumability_gate = consumability_gate_projection(operating_contract)
    current_pointer_contract = current_pointer_contract_projection(operating_contract)
    cards_by_stage = {
        str(card["route_id"]): card
        for card in stage_contract["stage_cards"]
        if isinstance(card, Mapping)
    }
    stages = [
        _build_stage_artifact_state(
            stage_id=stage_id,
            stage_card=cards_by_stage[stage_id],
            study_root=resolved_study_root,
            operating_contract=operating_projection,
            promotion_protocol=promotion_protocol,
            consumability_gate=consumability_gate,
        )
        for stage_id in MAIN_STAGE_ROUTE_IDS
    ]
    current_stage = _current_stage(stages)
    stale_platform_repairs = _stale_platform_repairs(study_root=resolved_study_root, stages=stages)
    return {
        "schema_version": 1,
        "surface_kind": "stage_artifact_index",
        "study_id": str(study_id),
        "study_root": str(resolved_study_root),
        "allowed_artifact_statuses": list(ALLOWED_ARTIFACT_STATUSES),
        "artifact_native_contract_ref": _STAGE_NATIVE_ARTIFACT_CONTRACT_REF,
        "operating_contract": operating_projection,
        "promotion_protocol": promotion_protocol,
        "consumability_gate": consumability_gate,
        "current_pointer_contract": current_pointer_contract,
        "authority_boundary": _authority_boundary(),
        "current_stage": _current_stage_projection(current_stage),
        "next_owner_action": _next_owner_action(current_stage),
        "provider_liveness": _provider_liveness(study_root=resolved_study_root),
        "stale_platform_repairs": stale_platform_repairs,
        "stages": stages,
    }


def _build_stage_artifact_state(
    *,
    stage_id: str,
    stage_card: Mapping[str, Any],
    study_root: Path,
    operating_contract: Mapping[str, Any],
    promotion_protocol: list[str],
    consumability_gate: Mapping[str, Any],
) -> dict[str, Any]:
    stage_folder_contract = _stage_folder_contract(stage_id)
    manifest_requirements = _manifest_requirements(stage_folder_contract)
    receipt_requirements = _receipt_requirements(stage_folder_contract)
    required_refs = [
        {
            "role": role,
            "ref": ref,
            "source": "stage_artifact_index_declared_output",
            "body_included": False,
            "native_contract_required": True,
        }
        for role, ref in _required_output_surfaces(stage_id)
    ]
    legacy_observed_refs = [
        {
            "role": item["role"],
            "ref": item["ref"],
            "path": str(study_root / str(item["ref"])),
            "body_included": False,
            "classification": "historical",
        }
        for item in required_refs
        if (study_root / str(item["ref"])).exists()
    ]
    artifact_classification = _artifact_classification(
        stage_id=stage_id,
        stage_folder_contract=stage_folder_contract,
        manifest_requirements=manifest_requirements,
        receipt_requirements=receipt_requirements,
        required_refs=required_refs,
        legacy_observed_refs=legacy_observed_refs,
        study_root=study_root,
    )
    observed_refs = [
        {
            "role": item["role"],
            "ref": item["ref"],
            "path": str(study_root / str(item["ref"])),
            "body_included": False,
            "classification": "current",
            "manifest_ref": manifest_requirements["ref"],
            "receipt_ref": receipt_requirements["ref"],
        }
        for item in required_refs
        if str(item["ref"]) in set(artifact_classification["current"])
    ]
    artifact_status = _artifact_status(required_refs=required_refs, observed_refs=observed_refs)
    if (
        artifact_status == _STATUS_MISSING
        and artifact_classification["missing_manifest_or_receipt"]
    ):
        artifact_status = _STATUS_MISSING_CONTRACT
    if artifact_status != _STATUS_DELTA and (
        artifact_classification["broken"] or artifact_classification["orphan"]
    ):
        artifact_status = "blocked_by_required_artifact"
    next_missing = _next_missing_surface(required_refs=required_refs, observed_refs=observed_refs)
    current_pointer = _current_pointer(
        stage_folder_contract=stage_folder_contract,
        artifact_classification=artifact_classification,
        operating_contract=operating_contract,
        promotion_protocol=promotion_protocol,
    )
    return {
        "surface_kind": "stage_artifact_state",
        "stage_id": stage_id,
        "display_name": str(stage_card.get("display_name") or stage_id),
        "artifact_native_contract_ref": _STAGE_NATIVE_ARTIFACT_CONTRACT_REF,
        "stage_folder_contract": stage_folder_contract,
        "manifest_requirements": manifest_requirements,
        "receipt_requirements": receipt_requirements,
        "required_output_refs": required_refs,
        "observed_artifact_refs": observed_refs,
        "legacy_observed_artifact_refs": legacy_observed_refs,
        "artifact_classification": artifact_classification,
        "current_pointer": current_pointer,
        "consumability_gate": _stage_consumability_gate(
            consumability_gate=consumability_gate,
            current_pointer=current_pointer,
        ),
        "artifact_status": artifact_status,
        "freshness": _freshness(artifact_status),
        "stage_progress_status": _stage_progress_status(artifact_status),
        "next_missing_surface": next_missing,
        "next_routes": list(stage_card.get("next_routes") or ()),
        "authority_boundary": _authority_boundary(),
    }


def _stage_folder_contract(stage_id: str) -> dict[str, Any]:
    stage_folder_ref = f"artifacts/stage_outputs/{stage_id}"
    return {
        "surface_kind": "stage_folder_contract",
        "contract_ref": f"{_STAGE_NATIVE_ARTIFACT_CONTRACT_REF}#/stage_folder",
        "stage_folder_ref": stage_folder_ref,
        "manifest_ref": f"{stage_folder_ref}/{_MANIFEST_FILENAME}",
        "receipt_ref": f"{stage_folder_ref}/{_RECEIPT_FILENAME}",
        "legacy_declared_refs_fallback": True,
        "body_included": False,
        "authority_boundary": _authority_boundary(),
    }


def _manifest_requirements(stage_folder_contract: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "surface_kind": "stage_artifact_manifest_requirements",
        "contract_ref": f"{_STAGE_NATIVE_ARTIFACT_CONTRACT_REF}#/manifest",
        "required": True,
        "ref": str(stage_folder_contract["manifest_ref"]),
        "required_fields": ["surface_kind", "schema_version", "stage_id", "artifact_refs"],
        "artifact_refs_must_cover_required_outputs": True,
        "body_included": False,
    }


def _receipt_requirements(stage_folder_contract: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "surface_kind": "stage_artifact_receipt_requirements",
        "contract_ref": f"{_STAGE_NATIVE_ARTIFACT_CONTRACT_REF}#/receipt",
        "required": True,
        "ref": str(stage_folder_contract["receipt_ref"]),
        "required_fields": [
            "surface_kind",
            "schema_version",
            "stage_id",
            "owner",
            "receipt_kind",
            "artifact_refs",
        ],
        "artifact_refs_must_cover_required_outputs": True,
        "body_included": False,
    }


def _artifact_classification(
    *,
    stage_id: str,
    stage_folder_contract: Mapping[str, Any],
    manifest_requirements: Mapping[str, Any],
    receipt_requirements: Mapping[str, Any],
    required_refs: list[dict[str, Any]],
    legacy_observed_refs: list[dict[str, Any]],
    study_root: Path,
) -> dict[str, Any]:
    required = [str(item["ref"]) for item in required_refs]
    legacy_observed = [str(item["ref"]) for item in legacy_observed_refs]
    manifest_ref = str(manifest_requirements["ref"])
    receipt_ref = str(receipt_requirements["ref"])
    manifest = _read_contract_json(study_root / manifest_ref)
    receipt = _read_contract_json(study_root / receipt_ref)
    missing_contract_refs = [
        ref for ref, payload in ((manifest_ref, manifest), (receipt_ref, receipt)) if payload is None
    ]
    broken = _broken_contract_refs(
        stage_id=stage_id,
        required_refs=required,
        manifest_ref=manifest_ref,
        manifest=manifest,
        receipt_ref=receipt_ref,
        receipt=receipt,
    )
    orphan = _orphan_stage_artifact_refs(
        stage_folder_ref=str(stage_folder_contract["stage_folder_ref"]),
        required_refs=required,
        contract_refs=[manifest_ref, receipt_ref],
        study_root=study_root,
    )
    existing_artifacts = set(required).issubset(legacy_observed)
    manifest_valid = _contract_payload_valid(
        stage_id=stage_id,
        required_refs=required,
        payload=manifest,
        required_fields=("surface_kind", "schema_version", "stage_id", "artifact_refs"),
    )
    receipt_accepted = _contract_payload_valid(
        stage_id=stage_id,
        required_refs=required,
        payload=receipt,
        required_fields=(
            "surface_kind",
            "schema_version",
            "stage_id",
            "owner",
            "receipt_kind",
            "artifact_refs",
        ),
    )
    contract_complete = existing_artifacts and manifest_valid and receipt_accepted and not orphan
    current = sorted(required) if contract_complete else []
    historical = sorted(ref for ref in legacy_observed if ref not in current)
    missing_outputs = sorted(ref for ref in required if ref not in legacy_observed)
    missing_manifest_or_receipt = sorted(historical) if missing_contract_refs else []
    status = _classification_status(
        current=current,
        historical=historical,
        missing_manifest_or_receipt=missing_manifest_or_receipt,
        broken=broken,
        orphan=orphan,
        missing_outputs=missing_outputs,
        required_refs=required,
    )
    return {
        "surface_kind": "stage_artifact_classification",
        "contract_ref": f"{_STAGE_NATIVE_ARTIFACT_CONTRACT_REF}#/classification",
        "status": status,
        "current": current,
        "historical": historical,
        "missing_manifest_or_receipt": missing_manifest_or_receipt,
        "orphan": orphan,
        "broken": broken,
        "missing": missing_outputs,
        "fail_closed": status != "current",
        "fail_closed_reason": _fail_closed_reason(
            status=status,
            missing_contract_refs=missing_contract_refs,
            broken=broken,
            missing_outputs=missing_outputs,
        ),
        "manifest_ref": manifest_ref,
        "receipt_ref": receipt_ref,
        "current_pointer_basis": {
            "existing_artifacts": existing_artifacts,
            "manifest_valid": manifest_valid,
            "receipt_accepted": receipt_accepted,
        },
        "legacy_declared_refs_fallback": True,
        "body_included": False,
    }


def _read_contract_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"_invalid_json": True}
    return dict(payload) if isinstance(payload, Mapping) else {"_invalid_json": True}


def _broken_contract_refs(
    *,
    stage_id: str,
    required_refs: list[str],
    manifest_ref: str,
    manifest: Mapping[str, Any] | None,
    receipt_ref: str,
    receipt: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    broken: list[dict[str, Any]] = []
    for ref, payload, required_fields in (
        (manifest_ref, manifest, ("surface_kind", "schema_version", "stage_id", "artifact_refs")),
        (
            receipt_ref,
            receipt,
            ("surface_kind", "schema_version", "stage_id", "owner", "receipt_kind", "artifact_refs"),
        ),
    ):
        if payload is None:
            continue
        if payload.get("_invalid_json") is True:
            broken.append({"ref": ref, "reason": "invalid_json_or_non_mapping"})
            continue
        missing_fields = [field for field in required_fields if field not in payload]
        if missing_fields:
            broken.append({"ref": ref, "reason": "missing_required_fields", "fields": missing_fields})
            continue
        if str(payload.get("stage_id")) != stage_id:
            broken.append({"ref": ref, "reason": "stage_id_mismatch", "expected_stage_id": stage_id})
            continue
        artifact_refs = _artifact_ref_set(payload.get("artifact_refs"))
        missing_artifact_refs = [required_ref for required_ref in required_refs if required_ref not in artifact_refs]
        if missing_artifact_refs:
            broken.append(
                {
                    "ref": ref,
                    "reason": "required_output_refs_not_declared",
                    "missing_refs": missing_artifact_refs,
                }
            )
    return broken


def _contract_payload_valid(
    *,
    stage_id: str,
    required_refs: list[str],
    payload: Mapping[str, Any] | None,
    required_fields: tuple[str, ...],
) -> bool:
    if payload is None or payload.get("_invalid_json") is True:
        return False
    if any(field not in payload for field in required_fields):
        return False
    if str(payload.get("stage_id")) != stage_id:
        return False
    artifact_refs = _artifact_ref_set(payload.get("artifact_refs"))
    return all(required_ref in artifact_refs for required_ref in required_refs)


def _artifact_ref_set(value: object) -> set[str]:
    if isinstance(value, str):
        text = value.strip()
        return {text} if text else set()
    if not isinstance(value, list | tuple | set):
        return set()
    refs: set[str] = set()
    for item in value:
        if isinstance(item, str) and item.strip():
            refs.add(item.strip())
        elif isinstance(item, Mapping) and isinstance(item.get("ref"), str) and item["ref"].strip():
            refs.add(item["ref"].strip())
    return refs


def _orphan_stage_artifact_refs(
    *,
    stage_folder_ref: str,
    required_refs: list[str],
    contract_refs: list[str],
    study_root: Path,
) -> list[str]:
    stage_folder = study_root / stage_folder_ref
    if not stage_folder.exists():
        return []
    known = set(required_refs) | set(contract_refs)
    orphan: list[str] = []
    for path in stage_folder.rglob("*"):
        if not path.is_file():
            continue
        ref = path.relative_to(study_root).as_posix()
        if ref not in known:
            orphan.append(ref)
    return sorted(orphan)


def _classification_status(
    *,
    current: list[str],
    historical: list[str],
    missing_manifest_or_receipt: list[str],
    broken: list[dict[str, Any]],
    orphan: list[str],
    missing_outputs: list[str],
    required_refs: list[str],
) -> str:
    if broken:
        return "broken"
    if orphan:
        return "orphan"
    if current and len(current) == len(required_refs) and not missing_outputs:
        return "current"
    if missing_manifest_or_receipt:
        return "missing_manifest_or_receipt"
    if historical:
        return "historical"
    return "missing"


def _fail_closed_reason(
    *,
    status: str,
    missing_contract_refs: list[str],
    broken: list[dict[str, Any]],
    missing_outputs: list[str],
) -> str | None:
    if status == "current":
        return None
    if missing_contract_refs:
        return "missing_manifest_or_receipt"
    if broken:
        return "broken_stage_native_contract"
    if missing_outputs:
        return "missing_required_output"
    return status


def _required_output_surfaces(stage_id: str) -> tuple[tuple[str, str], ...]:
    return _STAGE_OUTPUT_SURFACES.get(
        stage_id,
        ((f"{stage_id}_stage_output", f"artifacts/stage_outputs/{stage_id}/latest.json"),),
    )


def _artifact_status(*, required_refs: list[dict[str, Any]], observed_refs: list[dict[str, Any]]) -> str:
    if not observed_refs:
        return _STATUS_MISSING
    if len(observed_refs) < len(required_refs):
        return _STATUS_PARTIAL
    return _STATUS_DELTA


def _stage_progress_status(artifact_status: str) -> str:
    if artifact_status == _STATUS_MISSING:
        return "artifact_required"
    if artifact_status == _STATUS_MISSING_CONTRACT:
        return "artifact_contract_required"
    if artifact_status == _STATUS_PARTIAL:
        return "artifact_partial"
    if artifact_status == "blocked_by_required_artifact":
        return "artifact_contract_broken"
    return "artifact_delta_present"


def _freshness(artifact_status: str) -> dict[str, Any]:
    if artifact_status == _STATUS_MISSING:
        return {
            "status": "red_missing",
            "meaning": "required stage artifact refs are missing",
            "blocks_auto_advance_by_default": False,
        }
    if artifact_status == _STATUS_PARTIAL:
        return {
            "status": "yellow_partial",
            "meaning": "some required stage artifact refs are present",
            "blocks_auto_advance_by_default": False,
        }
    if artifact_status == _STATUS_MISSING_CONTRACT:
        return {
            "status": "red_missing_manifest_or_receipt",
            "meaning": "legacy declared artifact refs exist but the stage-native manifest or receipt is missing",
            "blocks_auto_advance_by_default": True,
        }
    if artifact_status == "blocked_by_required_artifact":
        return {
            "status": "red_broken_stage_artifact_contract",
            "meaning": "stage-native artifact manifest or receipt is invalid",
            "blocks_auto_advance_by_default": True,
        }
    return {
        "status": "green_artifact_delta_present",
        "meaning": "required stage artifact refs are present",
        "blocks_auto_advance_by_default": False,
    }


def _next_missing_surface(
    *,
    required_refs: list[dict[str, Any]],
    observed_refs: list[dict[str, Any]],
) -> str | None:
    observed = {str(item["ref"]) for item in observed_refs}
    for item in required_refs:
        ref = str(item["ref"])
        if ref not in observed:
            return ref
    return None


def _current_pointer(
    *,
    stage_folder_contract: Mapping[str, Any],
    artifact_classification: Mapping[str, Any],
    operating_contract: Mapping[str, Any],
    promotion_protocol: list[str],
) -> dict[str, Any]:
    basis = dict(artifact_classification["current_pointer_basis"])
    promotion_state = _current_pointer_promotion_state(
        basis=basis,
        classification_status=str(artifact_classification["status"]),
    )
    return {
        "surface_kind": "stage_artifact_current_pointer_projection",
        "contract_ref": f"{OPL_ARTIFACT_OPERATING_CONTRACT_REF}#/current_pointer",
        "pointer_ref": f"{stage_folder_contract['stage_folder_ref']}/current_pointer.json",
        "basis": basis,
        "progress_basis": list(operating_contract["progress_basis"]),
        "promotion_protocol": list(promotion_protocol),
        "promotion_state": promotion_state,
        "projection_rebuild_required": promotion_state == "current_pointer_promoted",
        "manifest_validity_is_semantic_receipt_validity": operating_contract[
            "manifest_validity_is_semantic_receipt_validity"
        ],
        "controller_read_model_currentness_role": operating_contract[
            "controller_read_model_currentness_role"
        ],
        "body_included": False,
    }


def _current_pointer_promotion_state(
    *,
    basis: Mapping[str, Any],
    classification_status: str,
) -> str:
    if basis.get("existing_artifacts") is not True:
        return "attempt_output_required"
    if basis.get("manifest_valid") is not True:
        return "manifest_required"
    if basis.get("receipt_accepted") is not True:
        return "receipt_required"
    if classification_status != "current":
        return "projection_blocked"
    return "current_pointer_promoted"


def _stage_consumability_gate(
    *,
    consumability_gate: Mapping[str, Any],
    current_pointer: Mapping[str, Any],
) -> dict[str, Any]:
    status = (
        "ready_for_consumability_validation"
        if current_pointer["promotion_state"] == "current_pointer_promoted"
        else "blocked"
    )
    return {
        **dict(consumability_gate),
        "status": status,
        "blocked_reason": None if status != "blocked" else current_pointer["promotion_state"],
        "current_pointer_promotion_state": current_pointer["promotion_state"],
    }


def _current_stage(stages: list[dict[str, Any]]) -> dict[str, Any]:
    furthest_observed_index = max(
        (
            index
            for index, stage in enumerate(stages)
            if stage["observed_artifact_refs"]
        ),
        default=-1,
    )
    if furthest_observed_index >= 0:
        for stage in stages[: furthest_observed_index + 1]:
            if not stage["observed_artifact_refs"]:
                return stage
        next_index = min(furthest_observed_index + 1, len(stages) - 1)
        return stages[next_index]
    for stage in stages:
        if stage["artifact_status"] != _STATUS_DELTA:
            return stage
    return stages[-1]


def _current_stage_projection(stage: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "stage_id": stage["stage_id"],
        "artifact_status": stage["artifact_status"],
        "stage_progress_status": stage["stage_progress_status"],
        "next_missing_surface": stage["next_missing_surface"],
    }


def _next_owner_action(stage: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "owner": stage["stage_id"],
        "action_type": "materialize_stage_artifact_delta",
        "required_output_surface": stage["next_missing_surface"],
        "artifact_native_contract_ref": stage["artifact_native_contract_ref"],
        "manifest_ref": stage["manifest_requirements"]["ref"],
        "receipt_ref": stage["receipt_requirements"]["ref"],
        "authority_boundary": _authority_boundary(),
        "artifact_first_authority": True,
        "can_authorize_quality_verdict": False,
        "can_authorize_submission_readiness": False,
    }


def _provider_liveness(*, study_root: Path) -> dict[str, Any]:
    runtime_ref = study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"
    return {
        "runtime_ref": str(runtime_ref),
        "runtime_ref_exists": runtime_ref.exists(),
        "provider_completion_is_paper_progress": False,
        "paper_progress_source": "stage_artifact_index",
    }


def _stale_platform_repairs(*, study_root: Path, stages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    has_artifact_delta = any(
        stage["observed_artifact_refs"] or stage.get("legacy_observed_artifact_refs")
        for stage in stages
    )
    if not has_artifact_delta:
        return []
    candidates = (
        ("controller_decisions/latest.json", study_root / "artifacts" / "controller_decisions" / "latest.json"),
        ("publication_eval/latest.json", study_root / "artifacts" / "publication_eval" / "latest.json"),
        (
            "runtime/provider_liveness",
            study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        ),
    )
    return [
        {
            "source": source,
            "ref": str(path),
            "reason": "artifact_delta_takes_precedence_over_platform_currentness",
            "counts_as_paper_progress": False,
        }
        for source, path in candidates
        if path.exists()
    ]


def _authority_boundary() -> dict[str, bool]:
    return {
        "artifact_first_can_determine_stage_progress": True,
        "can_write_mas_truth": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_submission_readiness": False,
        "provider_completion_is_paper_progress": False,
    }


__all__ = [
    "ALLOWED_ARTIFACT_STATUSES",
    "build_stage_artifact_index",
]
