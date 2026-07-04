from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


SCHEMA_VERSION = 1
ARK_SURFACE_KIND = "mas_ark_progress_worker_advisory"
AUTOSCI_SURFACE_KIND = "mas_autosci_source_experiment_advisory"
KDENSE_SURFACE_KIND = "mas_kdense_byok_pattern_advisory"
OPENSCIENCE_SURFACE_KIND = "mas_openscience_artifact_provenance_advisory"
ARK_FRAMEWORK_ID = "ark_progress_first"
AUTOSCI_FRAMEWORK_ID = "autosci_omegawiki"
KDENSE_FRAMEWORK_ID = "kdense_byok"
OPENSCIENCE_FRAMEWORK_ID = "openscience_artifact_provenance"
ARK_SOURCE_CONTRACT_REF = (
    "med_autoscience.progress_first_external_learning_contract."
    "build_ark_progress_first_learning_contract"
)
AUTOSCI_SOURCE_PROJECTION_REF = (
    "med_autoscience.autosci_learning_projection.build_autosci_learning_projection"
)
KDENSE_SOURCE_CONTRACT_REF = "contracts/kdense_byok_external_intake.json"
KDENSE_CAPABILITY_MAP_REF = "contracts/capability_map.json#/consumer_policy/external_specialist_library_policy"
OPENSCIENCE_SOURCE_REF = (
    "external_repo:ai4s-research/open-science@"
    "2200ad2ec4e2ac7c7ff59c5dcdfaeb0b9a5fda66"
)

ARK_REF_FAMILIES = (
    "micro_canary_ref",
    "human_decision_request_ref",
    "executor_real_run_closeout_ref",
    "citation_lifecycle_queue_ref",
    "semantic_no_progress_evidence_ref",
)
AUTOSCI_REF_FAMILIES = (
    "source_candidate_proposal_refs",
    "source_ingest_authorization_gap_refs",
    "experiment_lifecycle_receipt_refs",
    "negative_route_memory_refs",
    "artifact_render_qa_refs",
)
KDENSE_REF_FAMILIES = (
    "stagecraft_recipe_seed_refs",
    "atlas_source_ref_seed_refs",
    "specialist_allowlist_refs",
    "workspace_preview_pattern_refs",
    "attempt_replay_budget_receipt_refs",
    "connector_compute_policy_refs",
    "human_gate_schema_refs",
    "workbench_activity_display_refs",
    "fusion_watch_only_briefing_refs",
)
OPENSCIENCE_REF_FAMILIES = (
    "artifact_graph_ref",
    "claim_warning_ref",
    "annotation_regeneration_ref",
    "project_ledger_ref",
    "skill_pack_governance_ref",
    "native_viewer_watch_ref",
    "environment_capture_ref",
    "rerun_reproducibility_ref",
    "interactive_approval_or_permission_ref",
    "data_flow_disclosure_ref",
    "connector_provisioning_ref",
)
OPENSCIENCE_CLAIM_TYPES = ("computed", "parsed", "digitized", "hypothesis")

_ARK_REF_SUFFIXES = {
    "micro_canary_ref": "micro_canary",
    "human_decision_request_ref": "human_decision_request",
    "executor_real_run_closeout_ref": "executor_real_run_closeout",
    "citation_lifecycle_queue_ref": "citation_lifecycle_queue",
    "semantic_no_progress_evidence_ref": "semantic_no_progress_evidence",
}
_AUTOSCI_REF_SUFFIXES = {
    "source_candidate_proposal_refs": "source_candidate_proposal",
    "source_ingest_authorization_gap_refs": "source_ingest_authorization_gap",
    "experiment_lifecycle_receipt_refs": "experiment_lifecycle_receipt",
    "negative_route_memory_refs": "negative_route_memory",
    "artifact_render_qa_refs": "artifact_render_qa",
}
_KDENSE_REF_SUFFIXES = {
    "stagecraft_recipe_seed_refs": "stagecraft_recipe_seed",
    "atlas_source_ref_seed_refs": "atlas_source_ref_seed",
    "specialist_allowlist_refs": "specialist_allowlist",
    "workspace_preview_pattern_refs": "workspace_preview_pattern",
    "attempt_replay_budget_receipt_refs": "attempt_replay_budget_receipt",
    "connector_compute_policy_refs": "connector_compute_policy",
    "human_gate_schema_refs": "human_gate_schema",
    "workbench_activity_display_refs": "workbench_activity_display",
    "fusion_watch_only_briefing_refs": "fusion_watch_only_briefing",
}
_OPENSCIENCE_REF_SUFFIXES = {
    "artifact_graph_ref": "artifact_graph",
    "claim_warning_ref": "claim_warning",
    "annotation_regeneration_ref": "annotation_regeneration",
    "project_ledger_ref": "project_ledger",
    "skill_pack_governance_ref": "skill_pack_governance",
    "native_viewer_watch_ref": "native_viewer_watch",
    "environment_capture_ref": "environment_capture",
    "rerun_reproducibility_ref": "rerun_reproducibility",
    "interactive_approval_or_permission_ref": "interactive_approval_or_permission",
    "data_flow_disclosure_ref": "data_flow_disclosure",
    "connector_provisioning_ref": "connector_provisioning",
}

FORBIDDEN_WRITES = (
    "artifacts/publication_eval/latest.json",
    "artifacts/controller_decisions/latest.json",
    "artifacts/owner_receipts/**",
    "artifacts/typed_blockers/**",
    "artifacts/artifact_authority/**",
    "paper/**",
    "manuscript/current_package/**",
    "submission_package/**",
    "current_package/**",
    "memory/**/body",
)


def build_ark_progress_worker_advisory(dispatch: Mapping[str, Any] | None) -> dict[str, Any]:
    context = _dispatch_context(dispatch)
    payload = _base_advisory(
        surface_kind=ARK_SURFACE_KIND,
        framework_id=ARK_FRAMEWORK_ID,
        dispatch=context,
    )
    payload["source_contract_ref"] = ARK_SOURCE_CONTRACT_REF
    payload["candidate_ref_families"] = list(ARK_REF_FAMILIES)
    for family in ARK_REF_FAMILIES:
        payload[family] = _candidate_ref(
            framework_id=ARK_FRAMEWORK_ID,
            dispatch_id=context["candidate_dispatch_id"],
            suffix=_ARK_REF_SUFFIXES[family],
        )
    return payload


def build_autosci_source_experiment_advisory(
    dispatch: Mapping[str, Any] | None,
) -> dict[str, Any]:
    context = _dispatch_context(dispatch)
    payload = _base_advisory(
        surface_kind=AUTOSCI_SURFACE_KIND,
        framework_id=AUTOSCI_FRAMEWORK_ID,
        dispatch=context,
    )
    payload["source_projection_ref"] = AUTOSCI_SOURCE_PROJECTION_REF
    payload["candidate_ref_families"] = list(AUTOSCI_REF_FAMILIES)
    for family in AUTOSCI_REF_FAMILIES:
        payload[family] = [
            _candidate_ref(
                framework_id=AUTOSCI_FRAMEWORK_ID,
                dispatch_id=context["candidate_dispatch_id"],
                suffix=_AUTOSCI_REF_SUFFIXES[family],
            )
        ]
    return payload


def build_kdense_byok_pattern_advisory(dispatch: Mapping[str, Any] | None) -> dict[str, Any]:
    context = _dispatch_context(dispatch)
    payload = _base_advisory(
        surface_kind=KDENSE_SURFACE_KIND,
        framework_id=KDENSE_FRAMEWORK_ID,
        dispatch=context,
    )
    payload["source_contract_ref"] = KDENSE_SOURCE_CONTRACT_REF
    payload["capability_map_ref"] = KDENSE_CAPABILITY_MAP_REF
    payload["source_project_role"] = "external_pattern_source_only"
    payload["runtime_dependency"] = False
    payload["pi_runtime_dependency"] = False
    payload["external_library_bulk_load_allowed"] = False
    payload["openrouter_fusion_authority"] = False
    payload["candidate_ref_families"] = list(KDENSE_REF_FAMILIES)
    for family in KDENSE_REF_FAMILIES:
        payload[family] = [
            _candidate_ref(
                framework_id=KDENSE_FRAMEWORK_ID,
                dispatch_id=context["candidate_dispatch_id"],
                suffix=_KDENSE_REF_SUFFIXES[family],
            )
        ]
    return payload


def build_openscience_artifact_provenance_advisory(
    dispatch: Mapping[str, Any] | None,
) -> dict[str, Any]:
    dispatch_mapping = _mapping(dispatch)
    context = _dispatch_context(dispatch)
    payload = _base_advisory(
        surface_kind=OPENSCIENCE_SURFACE_KIND,
        framework_id=OPENSCIENCE_FRAMEWORK_ID,
        dispatch=context,
    )
    payload["source_ref"] = OPENSCIENCE_SOURCE_REF
    payload["source_project_role"] = "external_pattern_source_only"
    payload["runtime_dependency"] = False
    payload["electron_dependency"] = False
    payload["mcp_dependency"] = False
    payload["agpl_code_imported"] = False
    payload["candidate_ref_families"] = list(OPENSCIENCE_REF_FAMILIES)
    for family in OPENSCIENCE_REF_FAMILIES:
        payload[family] = _candidate_ref(
            framework_id=OPENSCIENCE_FRAMEWORK_ID,
            dispatch_id=context["candidate_dispatch_id"],
            suffix=_OPENSCIENCE_REF_SUFFIXES[family],
        )
    artifacts = _openscience_artifacts(dispatch_mapping)
    payload["claim_type_policy"] = {
        "allowed_claim_types": list(OPENSCIENCE_CLAIM_TYPES),
        "unknown_claim_type_warning": "missing_or_invalid_claim_type",
        "can_authorize_quality_verdict": False,
    }
    payload["artifact_graph_projection"] = _artifact_graph_projection(artifacts)
    payload["claim_warning_checks"] = _claim_warning_checks(artifacts)
    payload["annotation_regeneration_requests"] = _annotation_regeneration_requests(
        artifacts
    )
    payload["project_ledger_pointer"] = _project_ledger_pointer(
        dispatch_id=context["candidate_dispatch_id"],
        artifacts=artifacts,
    )
    payload["native_viewer_watch_projection"] = {
        "surface_kind": "openscience_native_viewer_watch_projection",
        "watch_only": True,
        "viewer_ref": payload["native_viewer_watch_ref"],
        "displayed_artifact_refs": [
            artifact["artifact_ref"]
            for artifact in artifacts
            if artifact.get("artifact_ref")
        ],
        "can_authorize_visual_quality": False,
        "can_authorize_source_readiness": False,
        "can_authorize_publication_readiness": False,
    }
    payload["environment_capture_briefing"] = _environment_capture_briefing(
        dispatch_mapping=dispatch_mapping,
        artifacts=artifacts,
        candidate_ref=payload["environment_capture_ref"],
    )
    payload["rerun_reproducibility_route_back_hint"] = (
        _rerun_reproducibility_route_back_hint(
            dispatch_mapping=dispatch_mapping,
            artifacts=artifacts,
            candidate_ref=payload["rerun_reproducibility_ref"],
        )
    )
    payload["interactive_approval_or_permission_hint"] = (
        _interactive_approval_or_permission_hint(
            dispatch_mapping=dispatch_mapping,
            candidate_ref=payload["interactive_approval_or_permission_ref"],
        )
    )
    payload["data_flow_disclosure_briefing"] = _data_flow_disclosure_briefing(
        dispatch_mapping=dispatch_mapping,
        candidate_ref=payload["data_flow_disclosure_ref"],
    )
    payload["connector_provisioning_hint"] = _connector_provisioning_hint(
        dispatch_mapping=dispatch_mapping,
        candidate_ref=payload["connector_provisioning_ref"],
    )
    return payload


def _base_advisory(
    *,
    surface_kind: str,
    framework_id: str,
    dispatch: dict[str, Any],
) -> dict[str, Any]:
    return {
        "surface_kind": surface_kind,
        "schema_version": SCHEMA_VERSION,
        "status": "candidate_refs_emitted",
        "framework_id": framework_id,
        "refs_only": True,
        "body_included": False,
        "advisory_only": True,
        "nonblocking": True,
        "fail_open": True,
        "mainline_waits": False,
        "mainline_waits_for_worker": False,
        "can_block_current_owner_action": False,
        "current_owner_action": dispatch["current_owner_action"],
        "diagnostic": dispatch["diagnostic"],
        "allowed_writes": [],
        "forbidden_writes": list(FORBIDDEN_WRITES),
        "written_refs": [],
        "authority_boundary": _authority_boundary(),
        "readiness_authorization": _readiness_authorization(),
    }


def _dispatch_context(dispatch: Mapping[str, Any] | None) -> dict[str, Any]:
    dispatch_mapping = _mapping(dispatch)
    action_id = _dispatch_text(dispatch_mapping, "action_id")
    return {
        "candidate_dispatch_id": action_id or "unknown_dispatch",
        "current_owner_action": _current_owner_action(dispatch_mapping),
        "diagnostic": (
            {"reason": "missing_or_invalid_dispatch"} if not dispatch_mapping else None
        ),
    }


def _current_owner_action(dispatch: Mapping[str, Any]) -> dict[str, str | None]:
    owner_route = _mapping(dispatch.get("owner_route")) or _mapping(
        _mapping(dispatch.get("prompt_contract")).get("owner_route")
    )
    refs = _mapping(dispatch.get("refs"))
    return {
        "action_type": _dispatch_text(dispatch, "action_type"),
        "action_id": _dispatch_text(dispatch, "action_id"),
        "owner": _text(owner_route.get("owner")) or _dispatch_text(dispatch, "owner"),
        "work_unit_id": _text(owner_route.get("work_unit_id"))
        or _text(owner_route.get("unit_id")),
        "work_unit_fingerprint": _text(owner_route.get("work_unit_fingerprint")),
        "dispatch_path": _text(refs.get("dispatch_path")),
    }


def _authority_boundary() -> dict[str, Any]:
    return {
        "surface_role": "refs_only_progress_worker_candidate",
        "can_write_domain_truth": False,
        "can_write_publication_eval": False,
        "can_write_controller_decisions": False,
        "can_write_owner_receipt": False,
        "can_write_typed_blocker": False,
        "can_write_paper_or_package": False,
        "can_write_memory_body": False,
        "can_write_artifact_authority": False,
        "can_authorize_owner_action": False,
        "can_authorize_source_readiness": False,
        "can_authorize_artifact_authority": False,
        "can_authorize_artifact_mutation": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_submission_readiness": False,
        "can_close_stage": False,
    }


def _readiness_authorization() -> dict[str, bool]:
    return {
        "may_authorize_publication_readiness": False,
        "may_authorize_source_readiness": False,
        "may_authorize_artifact_readiness": False,
        "may_authorize_artifact_mutation": False,
        "may_authorize_quality_verdict": False,
        "may_authorize_submission_readiness": False,
    }


def _candidate_ref(*, framework_id: str, dispatch_id: str, suffix: str) -> str:
    return f"external-learning:{framework_id}:{dispatch_id}:{suffix}"


def _openscience_artifacts(dispatch: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw = dispatch.get("artifact_candidates")
    if raw is None:
        raw = _mapping(dispatch.get("refs")).get("artifact_candidates")
    if not isinstance(raw, list):
        return []
    artifacts: list[dict[str, Any]] = []
    for index, item in enumerate(raw, start=1):
        candidate = _mapping(item)
        if not candidate:
            continue
        artifact_id = _text(candidate.get("artifact_id")) or f"artifact_{index}"
        artifacts.append(
            {
                "artifact_id": artifact_id,
                "artifact_ref": _text(candidate.get("artifact_ref"))
                or _text(candidate.get("ref")),
                "claim_type": _text(candidate.get("claim_type")),
                "source_refs": _text_list(candidate.get("source_refs")),
                "log_refs": _text_list(candidate.get("log_refs")),
                "annotation_refs": _text_list(candidate.get("annotation_refs")),
                "environment_refs": _text_refs(candidate.get("environment_refs"))
                or _text_refs(candidate.get("environment_ref")),
                "source_locator_ref": _text(candidate.get("source_locator_ref"))
                or _text(candidate.get("source_locator")),
                "content_hash": _text(candidate.get("content_hash"))
                or _text(candidate.get("sha256")),
            }
        )
    return artifacts


def _artifact_graph_projection(artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    nodes = [
        {
            "node_kind": "candidate_artifact",
            "artifact_id": artifact["artifact_id"],
            "artifact_ref": artifact.get("artifact_ref"),
            "claim_type": artifact.get("claim_type"),
            "content_hash": artifact.get("content_hash"),
            "environment_refs": artifact["environment_refs"],
        }
        for artifact in artifacts
    ]
    edges: list[dict[str, str]] = []
    for artifact in artifacts:
        artifact_id = str(artifact["artifact_id"])
        for source_ref in artifact["source_refs"]:
            edges.append(
                {
                    "edge_kind": "artifact_source_ref",
                    "from": artifact_id,
                    "to": source_ref,
                }
            )
        for log_ref in artifact["log_refs"]:
            edges.append(
                {
                    "edge_kind": "artifact_log_ref",
                    "from": artifact_id,
                    "to": log_ref,
                }
            )
        for annotation_ref in artifact["annotation_refs"]:
            edges.append(
                {
                    "edge_kind": "annotation_to_artifact_ref",
                    "from": annotation_ref,
                    "to": artifact_id,
                }
            )
    return {
        "surface_kind": "openscience_artifact_graph_refs_projection",
        "refs_only": True,
        "nodes": nodes,
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "can_write_artifact_authority": False,
    }


def _claim_warning_checks(artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    for artifact in artifacts:
        artifact_id = str(artifact["artifact_id"])
        claim_type = artifact.get("claim_type")
        if not claim_type:
            warnings.append(_warning(artifact_id, "missing_claim_type"))
        elif claim_type not in OPENSCIENCE_CLAIM_TYPES:
            warnings.append(_warning(artifact_id, "invalid_claim_type"))
        if not artifact.get("artifact_ref"):
            warnings.append(_warning(artifact_id, "untraced_artifact"))
        if not artifact["source_refs"]:
            warnings.append(_warning(artifact_id, "unsupported_claim"))
        if not artifact["log_refs"]:
            warnings.append(_warning(artifact_id, "missing_log"))
        if artifact["annotation_refs"] and not artifact.get("source_locator_ref"):
            warnings.append(
                _warning(artifact_id, "missing_source_locator_for_regeneration")
            )
        if not artifact["environment_refs"]:
            warnings.append(_warning(artifact_id, "missing_environment_capture"))
    return warnings


def _annotation_regeneration_requests(
    artifacts: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    requests: list[dict[str, Any]] = []
    for artifact in artifacts:
        if not artifact["annotation_refs"]:
            continue
        requests.append(
            {
                "surface_kind": "openscience_annotation_regeneration_ref",
                "artifact_id": artifact["artifact_id"],
                "annotation_refs": artifact["annotation_refs"],
                "source_locator_ref": artifact.get("source_locator_ref"),
                "status": (
                    "ready_for_source_regeneration_hint"
                    if artifact.get("source_locator_ref")
                    else "missing_source_locator"
                ),
                "refs_only": True,
                "can_mutate_source": False,
                "can_write_artifact_body": False,
            }
        )
    return requests


def _project_ledger_pointer(
    *, dispatch_id: str, artifacts: list[dict[str, Any]]
) -> dict[str, Any]:
    ledger_material = [
        {
            "artifact_id": artifact["artifact_id"],
            "artifact_ref": artifact.get("artifact_ref"),
            "claim_type": artifact.get("claim_type"),
            "source_refs": artifact["source_refs"],
            "log_refs": artifact["log_refs"],
            "annotation_refs": artifact["annotation_refs"],
            "environment_refs": artifact["environment_refs"],
            "content_hash": artifact.get("content_hash"),
        }
        for artifact in artifacts
    ]
    digest = hashlib.sha256(
        json.dumps(ledger_material, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {
        "surface_kind": "openscience_project_local_ledger_pointer",
        "ledger_ref": _candidate_ref(
            framework_id=OPENSCIENCE_FRAMEWORK_ID,
            dispatch_id=dispatch_id,
            suffix="project_ledger",
        ),
        "content_hash": digest,
        "content_hash_algorithm": "sha256:stable-json",
        "candidate_count": len(artifacts),
        "proves_owner_acceptance": False,
        "proves_artifact_authority": False,
    }


def _environment_capture_briefing(
    *,
    dispatch_mapping: Mapping[str, Any],
    artifacts: list[dict[str, Any]],
    candidate_ref: str,
) -> dict[str, Any]:
    return {
        "surface_kind": "openscience_environment_capture_briefing",
        "candidate_ref": candidate_ref,
        "environment_refs": _dispatch_refs(dispatch_mapping, "environment_refs")
        + [
            ref
            for artifact in artifacts
            for ref in artifact["environment_refs"]
        ],
        "refs_only": True,
        "body_included": False,
        "can_authorize_reproducibility": False,
    }


def _rerun_reproducibility_route_back_hint(
    *,
    dispatch_mapping: Mapping[str, Any],
    artifacts: list[dict[str, Any]],
    candidate_ref: str,
) -> dict[str, Any]:
    missing = []
    for artifact in artifacts:
        missing_fields = [
            field
            for field in ("source_refs", "log_refs", "content_hash", "environment_refs")
            if not artifact.get(field)
        ]
        if missing_fields:
            missing.append(
                {
                    "artifact_id": artifact["artifact_id"],
                    "missing_ref_families": missing_fields,
                }
            )
    return {
        "surface_kind": "openscience_rerun_reproducibility_route_back_hint",
        "candidate_ref": candidate_ref,
        "rerun_recipe_refs": _dispatch_refs(dispatch_mapping, "rerun_recipe_refs"),
        "missing_ref_hints": missing,
        "refs_only": True,
        "can_block_current_owner_action": False,
        "can_write_typed_blocker": False,
        "can_authorize_artifact_authority": False,
    }


def _interactive_approval_or_permission_hint(
    *, dispatch_mapping: Mapping[str, Any], candidate_ref: str
) -> dict[str, Any]:
    return {
        "surface_kind": "openscience_interactive_approval_or_permission_hint",
        "candidate_ref": candidate_ref,
        "permission_request_refs": _dispatch_refs(
            dispatch_mapping,
            "permission_request_refs",
            "approval_request_refs",
        ),
        "refs_only": True,
        "can_create_human_gate": False,
        "can_authorize_owner_action": False,
    }


def _data_flow_disclosure_briefing(
    *, dispatch_mapping: Mapping[str, Any], candidate_ref: str
) -> dict[str, Any]:
    return {
        "surface_kind": "openscience_data_flow_disclosure_briefing",
        "candidate_ref": candidate_ref,
        "data_flow_refs": _dispatch_refs(
            dispatch_mapping,
            "data_flow_disclosure_refs",
            "data_flow_refs",
        ),
        "refs_only": True,
        "body_included": False,
        "can_authorize_privacy_or_source_readiness": False,
    }


def _connector_provisioning_hint(
    *, dispatch_mapping: Mapping[str, Any], candidate_ref: str
) -> dict[str, Any]:
    return {
        "surface_kind": "openscience_connector_provisioning_hint",
        "candidate_ref": candidate_ref,
        "connector_refs": _dispatch_refs(
            dispatch_mapping,
            "connector_provisioning_refs",
            "connector_refs",
        ),
        "refs_only": True,
        "can_install_connector": False,
        "can_claim_runtime_landed": False,
    }


def _warning(artifact_id: str, warning_type: str) -> dict[str, Any]:
    return {
        "surface_kind": "openscience_graph_warning",
        "artifact_id": artifact_id,
        "warning_type": warning_type,
        "severity": "advisory",
        "refs_only": True,
        "can_block_current_owner_action": False,
        "can_authorize_quality_verdict": False,
        "may_route_back_candidate": warning_type
        in {
            "unsupported_claim",
            "missing_source_locator_for_regeneration",
            "missing_environment_capture",
        },
    }


def _dispatch_text(dispatch: Mapping[str, Any], key: str) -> str | None:
    return _text(dispatch.get(key)) or _text(_mapping(dispatch.get("source_action")).get(key))


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := _text(item))]


def _text_refs(value: object) -> list[str]:
    if isinstance(value, list):
        return _text_list(value)
    text = _text(value)
    return [text] if text else []


def _dispatch_refs(dispatch: Mapping[str, Any], *keys: str) -> list[str]:
    refs = _mapping(dispatch.get("refs"))
    values: list[str] = []
    for key in keys:
        values.extend(_text_refs(dispatch.get(key)))
        values.extend(_text_refs(refs.get(key)))
    return values


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "ARK_FRAMEWORK_ID",
    "ARK_REF_FAMILIES",
    "ARK_SOURCE_CONTRACT_REF",
    "ARK_SURFACE_KIND",
    "AUTOSCI_FRAMEWORK_ID",
    "AUTOSCI_REF_FAMILIES",
    "AUTOSCI_SOURCE_PROJECTION_REF",
    "AUTOSCI_SURFACE_KIND",
    "FORBIDDEN_WRITES",
    "KDENSE_CAPABILITY_MAP_REF",
    "KDENSE_FRAMEWORK_ID",
    "KDENSE_REF_FAMILIES",
    "KDENSE_SOURCE_CONTRACT_REF",
    "KDENSE_SURFACE_KIND",
    "OPENSCIENCE_FRAMEWORK_ID",
    "OPENSCIENCE_CLAIM_TYPES",
    "OPENSCIENCE_REF_FAMILIES",
    "OPENSCIENCE_SOURCE_REF",
    "OPENSCIENCE_SURFACE_KIND",
    "SCHEMA_VERSION",
    "build_ark_progress_worker_advisory",
    "build_autosci_source_experiment_advisory",
    "build_kdense_byok_pattern_advisory",
    "build_openscience_artifact_provenance_advisory",
]
