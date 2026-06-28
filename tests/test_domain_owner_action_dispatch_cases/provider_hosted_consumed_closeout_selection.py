from __future__ import annotations

from pathlib import Path

from med_autoscience.controllers.domain_owner_action_dispatch_parts import persisted_dispatches
from tests.domain_owner_action_dispatch_helpers import write_json as _write_json
from tests.study_runtime_test_helpers import make_profile


def test_provider_hosted_exact_stage_packet_survives_consumed_closeout_selection_filter(
    tmp_path: Path,
    monkeypatch,
) -> None:
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_type = "run_quality_repair_batch"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    stage_attempt_id = "sat_08da46bea43329723d2fbbea"
    dispatch_root = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
    )
    latest_path = dispatch_root / f"{action_type}.json"
    immutable_path = dispatch_root / "immutable" / action_type / "33abc53e0c18295f5fa03738.json"
    owner_route = _owner_route(
        study_id=study_id,
        action_type=action_type,
        work_unit_id=work_unit_id,
        fingerprint=fingerprint,
    )
    dispatch = _dispatch(
        study_id=study_id,
        action_type=action_type,
        work_unit_id=work_unit_id,
        fingerprint=fingerprint,
        owner_route=owner_route,
        latest_path=latest_path,
        immutable_path=immutable_path,
    )
    _write_json(latest_path, dispatch)
    _write_json(immutable_path, dispatch)
    _write_json(
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / f"{stage_attempt_id}.closeout.json",
        _closeout(
            study_id=study_id,
            action_type=action_type,
            work_unit_id=work_unit_id,
            fingerprint=fingerprint,
            stage_attempt_id=stage_attempt_id,
            immutable_path=immutable_path,
            owner_route=owner_route,
        ),
    )
    monkeypatch.setenv("OPL_STAGE_ID", "paper_mission/stage-outcome")
    monkeypatch.setenv("OPL_STAGE_ATTEMPT_ID", stage_attempt_id)
    monkeypatch.setenv("OPL_STAGE_PACKET_REF", str(immutable_path))
    monkeypatch.setenv("OPL_STUDY_ID", study_id)
    monkeypatch.setenv("OPL_ACTION_TYPE", action_type)
    monkeypatch.setenv("OPL_WORK_UNIT_ID", work_unit_id)
    monkeypatch.setenv("OPL_PROVIDER_ATTEMPT_REF", f"temporal://attempt/{stage_attempt_id}")
    monkeypatch.setenv(
        "OPL_SOURCE_FINGERPRINT",
        "mas_default_executor_provider_admission_source_95eb75e51e25e7fc938b8682",
    )
    monkeypatch.setenv("OPL_IDEMPOTENCY_KEY", "idem_2f8ab5c3e2608435ee8ccde0")

    selected = persisted_dispatches.selected_dispatches(
        profile=profile,
        study_id=study_id,
        action_types=(action_type,),
        consumer_payload=None,
        consumer_latest_path=(
            profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json"
        ),
        scan_payload={"studies": [{"study_id": study_id}]},
        supported_action_types=frozenset({action_type}),
        dispatch_relative_root=Path("artifacts/supervision/consumer/default_executor_dispatches"),
        fresh_progress=_blocked_progress(
            study_id=study_id,
            action_type=action_type,
            work_unit_id=work_unit_id,
            fingerprint=fingerprint,
            stage_attempt_id=stage_attempt_id,
            immutable_path=immutable_path,
        ),
    )

    assert [Path(item["refs"]["immutable_dispatch_path"]) for item in selected] == [immutable_path]


def _owner_route(
    *,
    study_id: str,
    action_type: str,
    work_unit_id: str,
    fingerprint: str,
) -> dict[str, object]:
    return {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": study_id,
        "truth_epoch": fingerprint,
        "runtime_health_epoch": fingerprint,
        "route_epoch": fingerprint,
        "current_owner": "MedAutoScience",
        "next_owner": "write",
        "owner_reason": work_unit_id,
        "allowed_actions": [action_type],
        "source_fingerprint": fingerprint,
        "work_unit_fingerprint": fingerprint,
        "source_refs": {
            "owner_route_currentness_basis": {
                "truth_epoch": fingerprint,
                "runtime_health_epoch": fingerprint,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
            },
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
        },
        "idempotency_key": f"paper-recovery::{study_id}::{action_type}::{fingerprint}",
    }


def _dispatch(
    *,
    study_id: str,
    action_type: str,
    work_unit_id: str,
    fingerprint: str,
    owner_route: dict[str, object],
    latest_path: Path,
    immutable_path: Path,
) -> dict[str, object]:
    return {
        "surface": "default_executor_dispatch_request",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": action_type,
        "action_id": f"paper-recovery-successor::{study_id}::{action_type}::{work_unit_id}",
        "dispatch_status": "ready",
        "dispatch_authority": "quality_repair_batch_writer_handoff",
        "next_executable_owner": "write",
        "executor_kind": "codex_cli_default",
        "chat_completion_only_executor_forbidden": True,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "repeat_suppression_key": fingerprint,
        "idempotency_key": owner_route["idempotency_key"],
        "owner_route": owner_route,
        "prompt_contract": {
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": action_type,
            "next_executable_owner": "write",
            "owner_route": owner_route,
            "prompt_budget": {"max_prompt_tokens": 6000},
            "compact_evidence_packet_ref": (
                f"studies/{study_id}/artifacts/supervision/compact_evidence_packets/{action_type}.json"
            ),
            "do_not_repeat": True,
            "repeat_suppression_key": fingerprint,
            "required_output_surface": (
                "canonical manuscript story-surface delta or "
                "typed blocker:manuscript_story_surface_delta_missing"
            ),
            "allowed_write_surfaces": ["paper/draft.md"],
            "forbidden_surfaces": [
                "paper/**",
                "manuscript/**",
                "current_package/**",
                "paper/current_package/**",
                "manuscript/current_package/**",
                "src/med_autoscience/platform/**",
                "artifacts/publication_eval/latest.json",
                "artifacts/controller_decisions/latest.json",
            ],
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "manual_study_patch_allowed": False,
            "medical_claim_authoring_allowed": False,
        },
        "refs": {
            "dispatch_path": str(latest_path),
            "immutable_dispatch_path": str(immutable_path),
            "stage_packet_path": str(immutable_path),
        },
    }


def _closeout(
    *,
    study_id: str,
    action_type: str,
    work_unit_id: str,
    fingerprint: str,
    stage_attempt_id: str,
    immutable_path: Path,
    owner_route: dict[str, object],
) -> dict[str, object]:
    return {
        "surface_kind": "stage_attempt_closeout_packet",
        "status": "blocked",
        "stage_id": "paper_mission/stage-outcome",
        "stage_attempt_id": stage_attempt_id,
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "stage_packet_ref": str(immutable_path),
        "owner_route": owner_route,
        "typed_blocker": {
            "surface_kind": "mas_domain_typed_blocker",
            "schema_version": 1,
            "reason": "no_selected_dispatch_for_authorized_stage_packet",
            "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
            "stage_attempt_id": stage_attempt_id,
            "stage_packet_ref": str(immutable_path),
            "next_owner": "one-person-lab",
            "write_permitted": False,
        },
        "paper_stage_log": {
            "surface_kind": "mas_paper_facing_stage_log_summary",
            "schema_version": 1,
            "status": "available",
            "stage_name": action_type,
            "problem_summary": "selector returned zero selected dispatches",
            "stage_goal": "Execute the exact provider-hosted immutable stage packet.",
            "stage_work_done": ["typed blocker returned"],
            "paper_work_done": [],
            "changed_stage_surfaces": [],
            "changed_paper_surfaces": [],
            "outcome": "typed_blocker:no_selected_dispatch_for_authorized_stage_packet",
            "remaining_blockers": ["no_selected_dispatch_for_authorized_stage_packet"],
            "progress_delta_classification": "typed_blocker",
        },
    }


def _blocked_progress(
    *,
    study_id: str,
    action_type: str,
    work_unit_id: str,
    fingerprint: str,
    stage_attempt_id: str,
    immutable_path: Path,
) -> dict[str, object]:
    return {
        "study_id": study_id,
        "current_execution_envelope": {
            "state_kind": "typed_blocker",
            "typed_blocker": {
                "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
                "stage_attempt_id": stage_attempt_id,
                "stage_packet_ref": str(immutable_path),
                "action_type": action_type,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
            },
        },
        "current_work_unit": {
            "status": "typed_blocker",
            "owner": "one-person-lab",
            "action_type": action_type,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
        },
    }
