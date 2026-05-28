from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from med_autoscience.controllers import stage_knowledge_plane
from med_autoscience.controllers.real_paper_autonomy_soak_inventory_parts import (
    apply_evidence,
    guarded_apply,
    projection_builders,
    provider_guarded_apply,
)
from med_autoscience.profiles import WorkspaceProfile, load_profile, profile_to_dict


SURFACE = "real_paper_autonomy_soak_inventory"
SCHEMA_VERSION = 1
DEFAULT_PROFILE_GLOB = "*/ops/medautoscience/profiles/*.toml"
DEFAULT_YANG_ROOT = Path("/Users/gaofeng/workspace/Yang")

READ_ONLY_CONTRACT = {
    "mode": "dry_run_inventory",
    "writes_real_workspace": False,
    "can_mutate_runtime": False,
    "can_write_current_package": False,
    "can_write_publication_gate": False,
    "allowed_actions": ["read_profiles", "read_status_surfaces", "report_inventory"],
    "prohibited_actions": [
        "migration_apply",
        "reconcile_apply",
        "runtime_relaunch",
        "current_package_write",
        "publication_gate_write",
    ],
}
SOAK_PROJECTION_SURFACE = "real_paper_autonomy_soak_projection"
SOAK_CLOSEOUT_SURFACE = "real_paper_autonomy_soak_closeout_projection"
PROVIDER_HOSTED_PROOF_SURFACE = "real_paper_autonomy_provider_hosted_paper_proof"
GUARDED_APPLY_PROOF_SURFACE = "real_paper_autonomy_guarded_apply_proof"
PROVIDER_HOSTED_GUARDED_APPLY_RECEIPT_SURFACE = "real_paper_autonomy_provider_hosted_guarded_apply_receipt"
SOAK_ACCEPTED_STATES = (
    "artifact_delta", "gate_replay", "ai_reviewer_re_eval", "route_decision",
    "stop_loss", "human_gate", "stable_blocker", "continuing_repair", "unknown",
)
SOAK_EVIDENCE_STATES = set(SOAK_ACCEPTED_STATES) - {"unknown"}

STATUS_SURFACE_REFS: tuple[str, ...] = (
    "artifacts/runtime/runtime_status_summary.json",
    "artifacts/supervision/opl_runtime_owner_handoff/latest.json",
    "artifacts/runtime/study_macro_state/latest.json",
    "artifacts/truth/latest.json",
    "artifacts/controller_decisions/latest.json",
    "artifacts/publication_eval/latest.json",
)

LEGACY_MDS_LAUNCHER_REFS: tuple[str, ...] = (
    "ops/med-deepscientist",
    "ops/medautoscience/bin/watch-runtime",
)


def discover_yang_profile_paths(
    yang_root: str | Path = DEFAULT_YANG_ROOT,
    *,
    profile_glob: str = DEFAULT_PROFILE_GLOB,
) -> list[Path]:
    root = Path(yang_root).expanduser()
    if not root.exists():
        return []
    return sorted(path.resolve() for path in root.glob(profile_glob) if path.is_file())


def build_real_paper_autonomy_soak_inventory(
    *,
    yang_root: str | Path = DEFAULT_YANG_ROOT,
    profile_paths: Sequence[str | Path] | None = None,
) -> dict[str, Any]:
    paths = [Path(path).expanduser().resolve() for path in profile_paths] if profile_paths else discover_yang_profile_paths(yang_root)
    reports = [_profile_report(path) for path in paths]
    status_counts: dict[str, int] = {}
    for report in reports:
        readiness = _text(report.get("migration_readiness"))
        status_counts[readiness] = status_counts.get(readiness, 0) + 1
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "mode": "dry_run_inventory",
        "read_only_contract": dict(READ_ONLY_CONTRACT),
        "profile_glob": str(Path(yang_root).expanduser() / DEFAULT_PROFILE_GLOB),
        "profile_count": len(reports),
        "profiles": reports,
        "summary": {
            "profiles_discovered": len(reports),
            "migration_readiness_counts": status_counts,
            "writes_performed": False,
            "real_workspace_mutation_allowed": False,
        },
    }


def build_real_paper_autonomy_soak_projection(
    *,
    yang_root: str | Path = DEFAULT_YANG_ROOT,
    profile_paths: Sequence[str | Path] | None = None,
    target_studies: Sequence[str] = ("DM002", "DM003", "Obesity"),
) -> dict[str, Any]:
    paths = [Path(path).expanduser().resolve() for path in profile_paths] if profile_paths else discover_yang_profile_paths(yang_root)
    targets = tuple(target_studies)
    profiles = [_profile_soak_projection(path, target_studies=targets) for path in paths]
    return projection_builders.build_soak_projection_payload(
        profiles=profiles,
        target_studies=targets,
    )


def build_real_paper_autonomy_soak_projection_for_profile(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    target_studies: Sequence[str] | None = None,
) -> dict[str, Any]:
    return projection_builders.build_soak_projection_for_profile(
        profile=profile,
        profile_ref=profile_ref,
        target_studies=target_studies,
    )


def build_real_paper_autonomy_soak_closeout_projection(
    *,
    yang_root: str | Path = DEFAULT_YANG_ROOT,
    profile_paths: Sequence[str | Path] | None = None,
    target_studies: Sequence[str] = ("DM002", "DM003", "Obesity"),
) -> dict[str, Any]:
    projection = build_real_paper_autonomy_soak_projection(
        yang_root=yang_root,
        profile_paths=profile_paths,
        target_studies=target_studies,
    )
    return projection_builders.build_soak_closeout_projection_payload(
        projection=projection,
        target_studies=target_studies,
    )


def build_real_paper_autonomy_soak_closeout_projection_for_profile(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    target_studies: Sequence[str] | None = None,
) -> dict[str, Any]:
    return projection_builders.build_soak_closeout_projection_for_profile(
        profile=profile,
        profile_ref=profile_ref,
        target_studies=target_studies,
    )


def build_real_paper_autonomy_provider_hosted_paper_proof(
    *,
    yang_root: str | Path = DEFAULT_YANG_ROOT,
    profile_paths: Sequence[str | Path] | None = None,
    target_studies: Sequence[str] = ("DM002", "DM003", "Obesity"),
) -> dict[str, Any]:
    closeout_projection = build_real_paper_autonomy_soak_closeout_projection(
        yang_root=yang_root,
        profile_paths=profile_paths,
        target_studies=target_studies,
    )
    return projection_builders.build_provider_hosted_paper_proof_from_projection(
        closeout_projection=closeout_projection,
        target_studies=target_studies,
    )


def build_real_paper_autonomy_guarded_apply_proof(
    *,
    yang_root: str | Path = DEFAULT_YANG_ROOT,
    profile_paths: Sequence[str | Path] | None = None,
    target_studies: Sequence[str] = ("DM002", "DM003", "Obesity"),
) -> dict[str, Any]:
    provider_proof = build_real_paper_autonomy_provider_hosted_paper_proof(
        yang_root=yang_root,
        profile_paths=profile_paths,
        target_studies=target_studies,
    )
    return guarded_apply.build_guarded_apply_proof_from_provider_proof(
        provider_proof=provider_proof,
        schema_version=SCHEMA_VERSION,
        surface=GUARDED_APPLY_PROOF_SURFACE,
        target_studies=target_studies,
    )


def build_real_paper_autonomy_guarded_apply_proof_for_profile(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    target_studies: Sequence[str] | None = None,
) -> dict[str, Any]:
    return projection_builders.build_guarded_apply_proof_for_profile(
        profile=profile,
        profile_ref=profile_ref,
        target_studies=target_studies,
    )


def build_real_paper_autonomy_provider_hosted_guarded_apply_receipt(
    *,
    profile_path: str | Path,
    provider_attempt_id: str,
    idempotency_key: str,
    target_studies: Sequence[str],
) -> dict[str, Any]:
    targets = tuple(_text(study_id) for study_id in target_studies if _text(study_id))
    proof = build_real_paper_autonomy_guarded_apply_proof(
        profile_paths=[Path(profile_path)],
        target_studies=targets,
    )
    return provider_guarded_apply.build_provider_hosted_guarded_apply_receipt_from_proof(
        proof=proof,
        schema_version=SCHEMA_VERSION,
        surface=PROVIDER_HOSTED_GUARDED_APPLY_RECEIPT_SURFACE,
        provider_attempt_id=provider_attempt_id,
        idempotency_key=idempotency_key,
        target_studies=targets,
    )


def _profile_soak_projection(profile_path: Path, *, target_studies: Sequence[str]) -> dict[str, Any]:
    base: dict[str, Any] = {
        "profile_path": str(profile_path),
        "profile_readable": False,
        "profile_error": "",
        "studies": [],
    }
    try:
        profile = load_profile(profile_path)
    except Exception as exc:  # pragma: no cover - exact parser errors are reported, not normalized.
        base["profile_error"] = f"{type(exc).__name__}: {exc}"
        return base
    target_set = {str(study_id).strip() for study_id in target_studies if str(study_id).strip()}
    studies = [
        _study_soak_projection(study_root)
        for study_root in _study_roots(profile)
        if not target_set or _matches_target_study(study_root.name, target_set)
    ]
    base.update(
        {
            "profile_readable": True,
            "profile_name": profile.name,
            "workspace_root": str(profile.workspace_root),
            "studies": studies,
        }
    )
    return base


def _projection_state_counts(profiles: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    state_counts = {state: 0 for state in SOAK_ACCEPTED_STATES}
    for profile in profiles:
        for study in profile.get("studies", []):
            state = _text(_mapping(study).get("final_projection")) or "unknown"
            state_counts[state] = state_counts.get(state, 0) + 1
    return state_counts


def _dedupe_target_studies(profiles: Sequence[object]) -> list[dict[str, Any]]:
    by_target: dict[str, dict[str, Any]] = {}
    for profile in profiles:
        profile_map = _mapping(profile)
        for study in profile_map.get("studies", []):
            study_map = dict(_mapping(study))
            if not study_map:
                continue
            target_key = _study_identity_key(_text(study_map.get("study_id")))
            current = by_target.get(target_key)
            if current is None or _study_evidence_rank(study_map) > _study_evidence_rank(current):
                study_map["profile_path"] = _text(profile_map.get("profile_path"))
                study_map["profile_name"] = _text(profile_map.get("profile_name"))
                study_map["workspace_root"] = _text(profile_map.get("workspace_root"))
                by_target[target_key] = study_map
    return list(by_target.values())


def _target_closeout_packets(
    *,
    selected_studies: Sequence[Mapping[str, Any]],
    target_studies: Sequence[str],
    target_coverage: Sequence[object],
) -> list[tuple[str, dict[str, Any]]]:
    coverage_by_target = {
        _study_identity_key(_text(_mapping(item).get("target_study"))): _mapping(item)
        for item in target_coverage
    }
    closeouts: list[tuple[str, dict[str, Any]]] = []
    for target in target_studies:
        target_text = _text(target)
        if not target_text:
            continue
        target_key = _study_identity_key(target_text)
        matches = [
            study
            for study in selected_studies
            if _matches_target_study(_text(study.get("study_id")), {target_text})
        ]
        if matches:
            study = max(matches, key=_study_evidence_rank)
            closeouts.append(_study_closeout_packet(study))
        else:
            closeouts.append(_target_blocker_closeout_packet(target=target_text, coverage=coverage_by_target.get(target_key, {})))
    return closeouts


def _study_evidence_rank(study: Mapping[str, Any]) -> int:
    state = _text(study.get("final_projection")) or "unknown"
    return {
        "artifact_delta": 80,
        "gate_replay": 70,
        "ai_reviewer_re_eval": 65,
        "route_decision": 60,
        "stop_loss": 55,
        "human_gate": 55,
        "stable_blocker": 50,
        "continuing_repair": 40,
        "unknown": 0,
    }.get(state, 0)


def _study_closeout_packet(study: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    study_id = _text(study.get("study_id"))
    final_projection = _text(study.get("final_projection")) or "unknown"
    evidence_refs = _closeout_evidence_refs(study)
    typed_blocker = final_projection not in SOAK_EVIDENCE_STATES
    closeout_id = f"mas-real-paper-soak:{study_id}:{final_projection}:{_fingerprint(evidence_refs)}"
    return study_id, {
        "surface_kind": "domain_stage_closeout_packet",
        "closeout_id": closeout_id,
        "closeout_refs": [
            f"mas-paper-soak:{study_id}:{final_projection}",
            *[ref["ref"] for ref in evidence_refs[:3]],
        ],
        "consumed_refs": [ref["ref"] for ref in evidence_refs],
        "consumed_memory_refs": _memory_refs(study),
        "writeback_receipt_refs": _memory_writeback_refs(study),
        "mas_owner_apply_evidence": apply_evidence.build_mas_owner_apply_evidence(study),
        "rejected_writes": [
            {
                "reason": "opl_forbidden_to_write_mas_truth",
                "forbidden_surfaces": [
                    "publication_eval/latest.json",
                    "controller_decisions/latest.json",
                    "current_package",
                    "publication_quality_verdict",
                    "memory_body",
                ],
            }
        ],
        "next_owner": _text(study.get("next_owner")) or "med-autoscience",
        "domain_ready_verdict": "typed_blocker" if typed_blocker else final_projection,
        "route_impact": {
            "decision": final_projection,
            "study_id": study_id,
            "profile_ref": _text(study.get("profile_path")),
            "workspace_root": _text(study.get("workspace_root")),
            "status": _text(study.get("status")),
            "reason": _text(study.get("reason")),
            "typed_blocker": typed_blocker,
        },
        "authority_boundary": _closeout_authority_boundary(),
    }


def _target_blocker_closeout_packet(*, target: str, coverage: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    typed_blockers = [dict(_mapping(item)) for item in coverage.get("typed_blockers", []) if _mapping(item)]
    if not typed_blockers:
        typed_blockers = [
            {
                "blocker_id": f"target_study_not_discovered:{_target_blocker_key(target)}",
                "target_study": target,
                "owner": "MedAutoScience",
                "reason": "no matching study directory was found under the inspected MAS workspace profiles",
                "required_owner_surface": "MAS profile/studies_root discovery",
                "write_permitted": False,
            }
        ]
    blocker_refs = [_text(blocker.get("blocker_id")) for blocker in typed_blockers if _text(blocker.get("blocker_id"))]
    consumed_refs = [f"mas-paper-soak:{target}:typed_blocker", *blocker_refs]
    return target, {
        "surface_kind": "domain_stage_closeout_packet",
        "closeout_id": f"mas-real-paper-soak:{target}:typed_blocker:{_fingerprint(typed_blockers)}",
        "closeout_refs": consumed_refs,
        "consumed_refs": consumed_refs,
        "consumed_memory_refs": [],
        "writeback_receipt_refs": [],
        "mas_owner_apply_evidence": apply_evidence.empty_mas_owner_apply_evidence(),
        "rejected_writes": [
            {
                "reason": "opl_forbidden_to_write_mas_truth",
                "forbidden_surfaces": [
                    "publication_eval/latest.json",
                    "controller_decisions/latest.json",
                    "current_package",
                    "publication_quality_verdict",
                    "memory_body",
                ],
            }
        ],
        "next_owner": "med-autoscience",
        "domain_ready_verdict": "typed_blocker",
        "typed_blockers": typed_blockers,
        "route_impact": {
            "decision": "typed_blocker",
            "study_id": target,
            "profile_ref": "",
            "workspace_root": "",
            "status": "typed_blocker",
            "reason": "; ".join(_text(blocker.get("reason")) for blocker in typed_blockers if _text(blocker.get("reason"))),
            "typed_blocker": True,
        },
        "authority_boundary": _closeout_authority_boundary(),
    }


def _closeout_evidence_refs(study: Mapping[str, Any]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for item in study.get("source_refs", []):
        ref = _mapping(item)
        if ref.get("exists") is True and _text(ref.get("path")):
            refs.append(
                {
                    "ref_kind": "workspace_runtime_ref",
                    "role": _text(ref.get("relative_ref")),
                    "ref": _text(ref.get("path")),
                    "body_included": False,
                }
            )
    for payload_key, role in (
        ("domain_handler_task", "mas_domain_handler_task"),
        ("dispatch_receipt", "mas_domain_handler_dispatch_receipt"),
        ("repair_execution_receipt", "mas_repair_execution_receipt"),
        ("repair_execution_evidence", "mas_repair_execution_evidence"),
    ):
        payload = _mapping(study.get(payload_key))
        if _text(payload.get("source_ref")):
            refs.append(
                {
                    "ref_kind": "workspace_runtime_ref",
                    "role": role,
                    "ref": _text(payload.get("source_ref")),
                    "body_included": False,
                }
            )
    return _dedupe_ref_records(refs)


def _memory_refs(study: Mapping[str, Any]) -> list[str]:
    proof = _mapping(study.get("memory_paper_soak_proof"))
    stage_entry = _mapping(proof.get("stage_entry"))
    refs = []
    for item in stage_entry.get("publication_route_memory_refs", []):
        item_map = _mapping(item)
        if memory_id := _text(item_map.get("memory_id")):
            refs.append(memory_id)
    return list(dict.fromkeys(refs))


def _memory_writeback_refs(study: Mapping[str, Any]) -> list[str]:
    proof = _mapping(study.get("memory_paper_soak_proof"))
    refs = []
    for key in ("mas_router_receipt_refs", "workspace_writeback_receipt_refs", "opl_aion_readonly_receipt_refs"):
        for item in proof.get(key, []):
            item_map = _mapping(item)
            ref = _text(item_map.get("ref") or item_map.get("receipt_ref") or item_map.get("path"))
            if ref:
                refs.append(ref)
    return list(dict.fromkeys(refs))


def _dedupe_text(values: Iterable[object]) -> list[str]:
    return list(dict.fromkeys(_text(value) for value in values if _text(value)))


def _dedupe_ref_records(refs: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for ref in refs:
        text = _text(ref.get("ref"))
        if text:
            deduped[text] = dict(ref)
    return list(deduped.values())


def _closeout_authority_boundary() -> dict[str, Any]:
    return {
        "projection_owner": "med-autoscience",
        "provider_attempt_owner": "one-person-lab",
        "domain_truth_owner": "med-autoscience",
        "quality_gate_owner": "med-autoscience",
        "artifact_authority_owner": "med-autoscience",
        "writes_real_workspace": False,
        "opl_can_write_mas_truth": False,
        "opl_can_authorize_publication_quality": False,
        "opl_can_write_artifact_authority": False,
        "opl_can_write_memory_body": False,
    }


def _target_coverage(
    *,
    profiles: Sequence[Mapping[str, Any]],
    target_studies: Sequence[str],
) -> list[dict[str, Any]]:
    coverage: list[dict[str, Any]] = []
    for target in target_studies:
        target_text = _text(target)
        if not target_text:
            continue
        matched = [
            dict(study)
            for profile in profiles
            for study in profile.get("studies", [])
            if isinstance(study, Mapping) and _matches_target_study(_text(study.get("study_id")), {target_text})
        ]
        projection_counts: dict[str, int] = {}
        for study in matched:
            projection = _text(study.get("final_projection")) or "unknown"
            projection_counts[projection] = projection_counts.get(projection, 0) + 1
        typed_blockers = []
        if not matched:
            typed_blockers.append(
                {
                    "blocker_id": f"target_study_not_discovered:{_target_blocker_key(target_text)}",
                    "target_study": target_text,
                    "owner": "MedAutoScience",
                    "reason": "no matching study directory was found under the inspected MAS workspace profiles",
                    "required_owner_surface": "MAS profile/studies_root discovery",
                    "write_permitted": False,
                }
            )
        elif not any((_text(study.get("final_projection")) or "unknown") in SOAK_EVIDENCE_STATES for study in matched):
            typed_blockers.append(
                {
                    "blocker_id": f"target_study_has_no_projection_evidence:{_target_blocker_key(target_text)}",
                    "target_study": target_text,
                    "owner": "MedAutoScience",
                    "reason": (
                        "matching study directory was found but no artifact delta, gate replay, reviewer update, "
                        "route decision, human gate, stop-loss, continuing repair, or stable blocker surface was readable"
                    ),
                    "required_owner_surface": "MAS progress/controller/publication domain refs plus OPL current-control-state",
                    "write_permitted": False,
                }
            )
        coverage.append(
            {
                "target_study": target_text,
                "status": "typed_blocker" if typed_blockers else "has_projection_evidence",
                "matched_study_count": len(matched),
                "matched_study_ids": [_text(study.get("study_id")) for study in matched],
                "final_projection_counts": projection_counts,
                "typed_blockers": typed_blockers,
            }
        )
    return coverage


def _matches_target_study(study_id: str, target_studies: set[str]) -> bool:
    study_key = _study_identity_key(study_id)
    return any(_study_matches_target_key(study_key, _study_identity_key(target)) for target in target_studies)


def _normalize_study_id(study_id: str) -> str:
    return _target_blocker_key(study_id)


def _study_identity_key(study_id: str) -> str:
    return str(study_id or "").strip().lower().replace("_", "-")


def _study_matches_target_key(study_key: str, target_key: str) -> bool:
    if not target_key:
        return False
    if study_key == target_key:
        return True
    if _is_dm002_alias(target_key):
        return study_key in {"dm002", "dm-002", "002", "002-dm-china-us-mortality-attribution"}
    if _is_dm003_alias(target_key):
        return study_key in {"dm003", "dm-003", "003", "003-dpcc-primary-care-phenotype-treatment-gap"}
    if _is_obesity_alias(target_key):
        return "obesity" in study_key
    return False


def _target_blocker_key(study_id: str) -> str:
    text = _study_identity_key(study_id)
    aliases = {
        "dm002": "002",
        "dm-002": "002",
        "dm003": "003",
        "dm-003": "003",
        "obesity": "obesity",
    }
    if text in aliases:
        return aliases[text]
    return text


def _is_dm002_alias(target_key: str) -> bool:
    return target_key in {"dm002", "dm-002", "002"}


def _is_dm003_alias(target_key: str) -> bool:
    return target_key in {"dm003", "dm-003", "003"}


def _is_obesity_alias(target_key: str) -> bool:
    return target_key == "obesity"


def _study_soak_projection(study_root: Path) -> dict[str, Any]:
    surfaces = {
        "domain_handler_task": _latest_json_from_candidates(
            study_root / "artifacts" / "runtime" / "opl_family_domain_handler",
            patterns=("exported_task.json", "*task*.json"),
        ),
        "dispatch_receipt": _latest_json_from_candidates(
            study_root / "artifacts" / "runtime" / "opl_family_domain_handler" / "dispatch_receipts",
            patterns=("latest.json", "*.json"),
        ),
        "repair_execution_receipt": _read_json_mapping(
            study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json"
        ),
        "repair_execution_evidence": _read_json_mapping(
            study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
        ),
        "gate_replay": _read_json_mapping(study_root / "artifacts" / "controller" / "gate_replay_requests" / "latest.json"),
        "controller_decisions": _read_json_mapping(study_root / "artifacts" / "controller_decisions" / "latest.json"),
        "publication_eval": _read_json_mapping(study_root / "artifacts" / "publication_eval" / "latest.json"),
        "ai_reviewer_request": _read_json_mapping(
            study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
        ),
        "memory_paper_soak_proof": _read_json_mapping(
            stage_knowledge_plane.paper_soak_memory_apply_proof_path(study_root=study_root)
        ),
    }
    lifecycle = _study_lifecycle([payload for payload in surfaces.values() if isinstance(payload, Mapping)])
    final_projection = _final_projection(surfaces)
    return {
        "study_id": study_root.name,
        "study_root": str(study_root),
        "status": lifecycle["status"],
        "reason": lifecycle["reason"],
        "active_run_id": lifecycle["active_run_id"],
        "final_projection": final_projection,
        "next_owner": _next_owner(surfaces),
        "source_refs": _soak_source_refs(study_root),
        **surfaces,
        "ai_reviewer_evidence": _ai_reviewer_evidence(surfaces["publication_eval"], surfaces["ai_reviewer_request"]),
    }


def _final_projection(surfaces: Mapping[str, Mapping[str, Any]]) -> str:
    repair_evidence = _mapping(surfaces.get("repair_execution_evidence"))
    if _mapping(repair_evidence.get("canonical_artifact_delta")).get("meaningful_artifact_delta") is True:
        return "artifact_delta"
    if repair_evidence.get("progress_delta_candidate") is True:
        return "artifact_delta"
    if _mapping(surfaces.get("publication_eval")).get("assessment_provenance"):
        return "ai_reviewer_re_eval"
    if _mapping(surfaces.get("gate_replay")):
        return "gate_replay"
    controller = _mapping(surfaces.get("controller_decisions"))
    if _text(controller.get("route_decision")):
        if _text(controller.get("route_decision")) in {"stop_loss", "terminal_stop"} or _text(controller.get("route_target")) == "stop":
            return "stop_loss"
        if controller.get("requires_human_confirmation") is True:
            return "human_gate"
        if _text(controller.get("route_decision")) in {"stable_blocker", "blocked"}:
            return "stable_blocker"
        return "route_decision"
    if _text(controller.get("runtime_decision")) == "blocked" or _text(controller.get("blocked_reason")):
        return "stable_blocker"
    if _mapping(surfaces.get("dispatch_receipt")).get("accepted") is False:
        return "stable_blocker"
    if _mapping(surfaces.get("domain_handler_task")):
        return "continuing_repair"
    return "unknown"


def _next_owner(surfaces: Mapping[str, Mapping[str, Any]]) -> str | None:
    repair_receipt = _mapping(surfaces.get("repair_execution_receipt"))
    if repair_receipt.get("execution_status") == "executed":
        return "ai_reviewer"
    task = _mapping(surfaces.get("domain_handler_task"))
    payload = _mapping(task.get("payload"))
    unit = _mapping(payload.get("repair_work_unit"))
    if owner := _text(unit.get("owner")):
        return owner
    controller = _mapping(surfaces.get("controller_decisions"))
    return _text(controller.get("next_owner") or controller.get("route_target"))


def _ai_reviewer_evidence(publication_eval: Mapping[str, Any], ai_reviewer_request: Mapping[str, Any]) -> dict[str, Any]:
    provenance = _mapping(publication_eval.get("assessment_provenance"))
    return {
        "owner": _text(provenance.get("owner")) or None,
        "eval_id": _text(publication_eval.get("eval_id")) or None,
        "request_id": _text(ai_reviewer_request.get("request_id")) or None,
        "request_state": _text(_mapping(ai_reviewer_request.get("request_lifecycle")).get("state")) or None,
    }


def _soak_source_refs(study_root: Path) -> list[dict[str, Any]]:
    refs = []
    for relative_ref in (
        "artifacts/runtime/opl_family_domain_handler",
        "artifacts/controller/repair_execution_receipts/latest.json",
        "artifacts/controller/repair_execution_evidence/latest.json",
        "artifacts/controller/gate_replay_requests/latest.json",
        "artifacts/publication_eval/latest.json",
        "artifacts/controller_decisions/latest.json",
    ):
        path = study_root / relative_ref
        refs.append({"relative_ref": relative_ref, "path": str(path), "exists": path.exists()})
    return refs


def _latest_json_from_candidates(root: Path, *, patterns: Sequence[str]) -> dict[str, Any]:
    if not root.exists():
        return {}
    candidates: list[Path] = []
    for pattern in patterns:
        candidates.extend(path for path in root.glob(pattern) if path.is_file())
    if not candidates:
        return {}
    path = sorted(candidates, key=lambda item: item.stat().st_mtime_ns, reverse=True)[0]
    payload = _read_json_mapping(path)
    return {**dict(payload), "source_ref": str(path)} if payload else {}


def _profile_report(profile_path: Path) -> dict[str, Any]:
    base: dict[str, Any] = {
        "profile_path": str(profile_path),
        "profile_readable": False,
        "profile_error": "",
        "migration_readiness": "profile_unreadable",
        "studies": [],
        "legacy_mds_evidence": [],
    }
    try:
        profile = load_profile(profile_path)
    except Exception as exc:  # pragma: no cover - exact parser errors are reported, not normalized.
        base["profile_error"] = f"{type(exc).__name__}: {exc}"
        return base

    profile_dict = profile_to_dict(profile)
    studies = [_study_report(study_root) for study_root in _study_roots(profile)]
    legacy_evidence = _legacy_mds_evidence(profile=profile, profile_dict=profile_dict)
    readiness = _migration_readiness(
        profile=profile,
        studies=studies,
        legacy_evidence=legacy_evidence,
    )
    base.update(
        {
            "profile_readable": True,
            "profile_name": profile.name,
            "workspace_root": str(profile.workspace_root),
            "runtime_root": str(profile.runtime_root),
            "managed_runtime_home": str(profile.managed_runtime_home),
            "studies_root": str(profile.studies_root),
            "migration_readiness": readiness,
            "status_progress_readability": _status_progress_readability(studies),
            "studies": studies,
            "legacy_mds_evidence": legacy_evidence,
        }
    )
    return base


def _study_roots(profile: WorkspaceProfile) -> list[Path]:
    if not profile.studies_root.is_dir():
        return []
    return sorted(path.resolve() for path in profile.studies_root.iterdir() if path.is_dir())


def _canonical_study_roots(profile: WorkspaceProfile) -> list[Path]:
    return [root for root in _study_roots(profile) if _is_canonical_study_root(root)]


def _is_canonical_study_root(study_root: Path) -> bool:
    return (study_root / "study.yaml").is_file() or (study_root / "runtime_binding.yaml").is_file()


def _study_report(study_root: Path) -> dict[str, Any]:
    surfaces = [_surface_report(study_root, relative_ref) for relative_ref in STATUS_SURFACE_REFS]
    readable = [surface for surface in surfaces if surface["readable"]]
    status_payloads = [surface["payload"] for surface in readable if isinstance(surface.get("payload"), Mapping)]
    lifecycle = _study_lifecycle(status_payloads)
    return {
        "study_id": _study_id(study_root, status_payloads),
        "study_root": str(study_root),
        "status": lifecycle["status"],
        "reason": lifecycle["reason"],
        "active_run_id": lifecycle["active_run_id"],
        "status_progress_readable": bool(readable),
        "readable_surface_count": len(readable),
        "surface_refs": [
            {
                "relative_ref": surface["relative_ref"],
                "path": surface["path"],
                "exists": surface["exists"],
                "readable": surface["readable"],
                "error": surface["error"],
            }
            for surface in surfaces
        ],
    }


def _surface_report(study_root: Path, relative_ref: str) -> dict[str, Any]:
    path = study_root / relative_ref
    report: dict[str, Any] = {
        "relative_ref": relative_ref,
        "path": str(path),
        "exists": path.is_file(),
        "readable": False,
        "error": "",
        "payload": {},
    }
    if not path.is_file():
        return report
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        return report
    report["readable"] = isinstance(payload, Mapping)
    report["payload"] = dict(payload) if isinstance(payload, Mapping) else {}
    if not report["readable"]:
        report["error"] = "json payload is not an object"
    return report


def _read_json_mapping(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _study_lifecycle(payloads: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    active_run_id = _first_text(payloads, "active_run_id")
    quest_status = _first_text(payloads, "quest_status", "runtime_status", "health_status", "overall_status")
    reason = _first_text(
        payloads,
        "runtime_reason",
        "reason",
        "blocked_reason",
        "status_summary",
        "next_action_summary",
    )
    if active_run_id:
        status = "active"
    elif any(_truthy_nested(payload, ("auto_runtime_parked", "parked")) for payload in payloads):
        status = "parked"
        reason = reason or "auto_runtime_parked"
    elif quest_status in {"completed", "done", "complete"}:
        status = "completed"
    elif quest_status in {"inactive", "blocked", "stopped", "paused", "parked"}:
        status = "parked" if "park" in reason or quest_status == "parked" else "inactive"
    elif payloads:
        status = "readable_unknown"
    else:
        status = "status_unreadable"
        reason = "no readable status/progress surface found"
    return {
        "status": status,
        "reason": reason,
        "active_run_id": active_run_id,
    }


def _study_id(study_root: Path, payloads: Sequence[Mapping[str, Any]]) -> str:
    return _first_text(payloads, "study_id") or study_root.name


def _status_progress_readability(studies: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    readable = [study for study in studies if study.get("status_progress_readable") is True]
    return {
        "study_count": len(studies),
        "readable_study_count": len(readable),
        "all_discovered_studies_readable": len(readable) == len(studies) if studies else False,
    }


def _legacy_mds_evidence(
    *,
    profile: WorkspaceProfile,
    profile_dict: Mapping[str, Any],
) -> list[dict[str, str]]:
    evidence: list[dict[str, str]] = []
    for key in ("runtime_root", "managed_runtime_home"):
        value = _text(profile_dict.get(key))
        if "med-deepscientist" in value or "/.ds" in value:
            evidence.append({"kind": "profile_path", "key": key, "value": value})
    for table_name in ("historical_fixture_ref", "source_provenance", "explicit_archive_import_ref"):
        table = profile_dict.get(table_name)
        if isinstance(table, Mapping):
            for key, raw_value in table.items():
                value = _text(raw_value)
                if "med-deepscientist" in value or "/.ds" in value:
                    evidence.append({"kind": table_name, "key": str(key), "value": value})
    for relative_ref in LEGACY_MDS_LAUNCHER_REFS:
        path = profile.workspace_root / relative_ref
        if path.exists():
            evidence.append({"kind": "workspace_path", "key": relative_ref, "value": str(path)})
    return evidence


def _migration_readiness(
    *,
    profile: WorkspaceProfile,
    studies: Sequence[Mapping[str, Any]],
    legacy_evidence: Sequence[Mapping[str, str]],
) -> str:
    if not profile.workspace_root.exists() or not profile.studies_root.exists():
        return "blocked_missing_workspace_surfaces"
    if not studies:
        return "blocked_no_discovered_studies"
    if any(study.get("status") == "active" for study in studies):
        return "audit_only_active_study_present"
    if legacy_evidence:
        return "dry_run_ready_legacy_evidence_present"
    return "dry_run_ready_no_legacy_evidence"


def _first_text(payloads: Sequence[Mapping[str, Any]], *keys: str) -> str:
    for payload in payloads:
        for key in keys:
            value = _text(payload.get(key))
            if value:
                return value
    return ""


def _truthy_nested(payload: Mapping[str, Any], keys: tuple[str, str]) -> bool:
    parent = payload.get(keys[0])
    return isinstance(parent, Mapping) and parent.get(keys[1]) is True


def _fingerprint(payload: object) -> str:
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    import hashlib

    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()[:16]


def _text(value: object) -> str:
    return str(value or "").strip()


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}
