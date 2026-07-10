from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.paper_mission_domain.common import (
    _load_json_object,
)
from med_autoscience.paper_mission_output_roots import (
    _assert_safe_one_shot_output_root,
    _is_yang_ops_candidate_root,
)
from med_autoscience.paper_mission import (
    build_paper_mission_one_shot_migration_pack,
    paper_mission_by_study,
    paper_mission_candidate_artifact_delta,
    paper_mission_canary_candidate_manifest,
    paper_mission_owner_decision_packet,
)


ONE_SHOT_MIGRATION_FORBIDDEN_AUTHORITY_WRITES = (
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "owner receipt",
    "typed blocker",
    "human gate",
    "current_package",
    "runtime queue/provider attempts",
    "Yang study truth surfaces",
    "Yang runtime authority surfaces",
    "Yang output outside ops/medautoscience/paper_mission_one_shot_migration",
)


def build_one_shot_migration_cli_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    study_progress_payload: str | Path | None,
    runtime_readback_payload: str | Path | None,
    output_root: str | Path | None,
    source: str,
    contract_ref: str,
    contract_version: str,
    no_write_output_manifest: Callable[[], dict[str, Any]],
    paper_mission_transaction_readback: Callable[..., dict[str, Any]],
    transaction_readback_output_fields: Callable[[Mapping[str, Any]], dict[str, Any]],
    validate_with_contract: Callable[[dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    if study_progress_payload is None:
        raise ValueError("--study-progress-payload is required for --one-shot-migration")
    progress_path = Path(study_progress_payload).expanduser().resolve()
    domain_diagnostic_path = (
        Path(runtime_readback_payload).expanduser().resolve()
        if runtime_readback_payload is not None
        else None
    )
    progress = _load_json_object(progress_path)
    domain_diagnostic = (
        _load_json_object(domain_diagnostic_path)
        if domain_diagnostic_path is not None
        else {}
    )
    migration_pack = build_paper_mission_one_shot_migration_pack(
        study_progress_payloads=progress,
        runtime_readback_payload=domain_diagnostic,
        profile_ref=str(profile_ref),
    )
    mission = paper_mission_by_study(migration_pack, study_id)
    readback = mission["one_shot_migration_readback"]
    candidate_manifest = paper_mission_canary_candidate_manifest(mission)
    candidate_artifact_delta = paper_mission_candidate_artifact_delta(mission)
    owner_decision_packet = paper_mission_owner_decision_packet(mission)
    output_manifest = (
        _write_one_shot_migration_outputs(
            output_root=Path(output_root),
            study_id=study_id,
            legacy_truth_import_pack=readback["legacy_truth_import_pack"],
            paper_mission_run=mission,
            default_readback=readback,
            candidate_manifest=candidate_manifest,
            candidate_artifact_delta=candidate_artifact_delta,
            owner_decision_packet=owner_decision_packet,
        )
        if output_root is not None
        else no_write_output_manifest()
    )
    return {
        "surface_kind": "paper_mission_one_shot_migration_cli_readback",
        "schema_version": 1,
        "contract_ref": contract_ref,
        "contract_version": contract_version,
        "paper_mission_command": "inspect",
        "action_intent": "paper_mission/inspect",
        "source": source,
        "dry_run": True,
        "profile": {
            "profile_name": str(getattr(profile, "name", "")),
            "profile_ref": str(profile_ref),
        },
        "study_id": study_id,
        "study_root": str(Path(profile.studies_root) / study_id),
        "study_root_exists": (Path(profile.studies_root) / study_id).exists(),
        "study_progress_payload_ref": str(progress_path),
        **(
            {"runtime_readback_payload_ref": str(domain_diagnostic_path)}
            if domain_diagnostic_path is not None
            else {}
        ),
        "migration_pack": migration_pack,
        "legacy_truth_import_pack": readback["legacy_truth_import_pack"],
        "paper_mission_run": mission,
        "default_readback": readback,
        "candidate_manifest": candidate_manifest,
        "mission_candidate_artifact_delta": candidate_artifact_delta,
        "owner_decision_packet": owner_decision_packet,
        "authority_consume_readback": readback["consume_candidate_readback"],
        "consume_candidate_status": readback["consume_candidate_status"],
        **transaction_readback_output_fields(
            paper_mission_transaction_readback(
                mission_id=str(mission["mission_id"]),
                study_id=study_id,
                objective=str(mission["objective"]),
                paper_mission_command="inspect",
                study_root=Path(profile.studies_root) / study_id,
                mission=mission,
                authority_consume_readback=readback["consume_candidate_readback"],
            )
        ),
        "mutation_policy": {
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang_authority": False,
            "writes_yang_ops_candidate_package": _is_yang_ops_candidate_root(output_root),
            "writes_paper_body": False,
            "writes_candidate_workspace": output_root is not None,
            "dry_run_only": True,
            "forbidden_authority_writes": list(
                ONE_SHOT_MIGRATION_FORBIDDEN_AUTHORITY_WRITES
            ),
        },
        "output_manifest": output_manifest,
        "contract_validation": validate_with_contract(mission),
        "cutover_proof": {
            "legacy_truth_import_pack_generated": True,
            "formal_paper_mission_run_generated": True,
            "mission_candidate_artifact_delta_generated": True,
            "owner_decision_packet_generated": True,
            "default_readback_surface": "PaperMissionRun",
            "legacy_blocker_controls_default_execution": False,
            "legacy_current_work_unit_role": "mission_input_constraint",
            "authority_materialized": False,
        },
    }


def _write_one_shot_migration_outputs(
    *,
    output_root: Path,
    study_id: str,
    legacy_truth_import_pack: dict[str, Any],
    paper_mission_run: dict[str, Any],
    default_readback: dict[str, Any],
    candidate_manifest: dict[str, Any],
    candidate_artifact_delta: dict[str, Any],
    owner_decision_packet: dict[str, Any],
) -> dict[str, Any]:
    root = output_root.expanduser().resolve()
    _assert_safe_one_shot_output_root(root)
    study_root = root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    outputs = {
        "legacy_truth_import_pack": study_root / "legacy_truth_import_pack.json",
        "paper_mission_run": study_root / "paper_mission_run.json",
        "default_readback": study_root / "default_readback.json",
        "candidate_manifest": study_root / "candidate_manifest.json",
        "mission_candidate_artifact_delta": study_root
        / "mission_candidate_artifact_delta.json",
        "owner_decision_packet": study_root / "owner_decision_packet.json",
    }
    payloads = {
        "legacy_truth_import_pack": legacy_truth_import_pack,
        "paper_mission_run": paper_mission_run,
        "default_readback": default_readback,
        "candidate_manifest": {
            **candidate_manifest,
            "mission_candidate_sidecar_refs": {
                "paper_mission_run": str(outputs["paper_mission_run"]),
                "default_readback": str(outputs["default_readback"]),
                "mission_candidate_artifact_delta": str(
                    outputs["mission_candidate_artifact_delta"]
                ),
                "owner_decision_packet": str(outputs["owner_decision_packet"]),
            },
        },
        "mission_candidate_artifact_delta": candidate_artifact_delta,
        "owner_decision_packet": owner_decision_packet,
    }
    written_files: list[str] = []
    for key, path in outputs.items():
        path.write_text(
            json.dumps(payloads[key], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        written_files.append(str(path))
    return {
        "mode": "non_authority_candidate_package",
        "output_root": str(study_root),
        "written_files": written_files,
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang_authority": False,
        "writes_yang_ops_candidate_package": _is_yang_ops_candidate_root(root),
        "candidate_manifest_ref": str(outputs["candidate_manifest"]),
        "mission_candidate_artifact_delta_ref": str(
            outputs["mission_candidate_artifact_delta"]
        ),
        "owner_decision_packet_ref": str(outputs["owner_decision_packet"]),
    }


__all__ = [
    "ONE_SHOT_MIGRATION_FORBIDDEN_AUTHORITY_WRITES",
    "build_one_shot_migration_cli_readback",
]
