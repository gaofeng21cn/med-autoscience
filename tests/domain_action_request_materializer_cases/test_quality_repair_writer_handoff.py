from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _owner_route(
    *,
    study_id: str,
    quest_id: str,
    next_owner: str,
    owner_reason: str,
    allowed_actions: list[str],
) -> dict[str, object]:
    return {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": quest_id,
        "truth_epoch": "truth-epoch::dm002::writer-handoff",
        "runtime_health_epoch": "runtime-health::dm002::writer-handoff",
        "work_unit_fingerprint": "dm002_same_line_methods_display_package_repair",
        "failure_signature": owner_reason,
        "trace_id": "owner-route-trace::dm002::writer-handoff",
        "route_epoch": "truth-epoch::dm002::writer-handoff",
        "source_fingerprint": "truth-source::dm002::writer-handoff",
        "current_owner": "mas_controller",
        "next_owner": next_owner,
        "owner_reason": owner_reason,
        "active_run_id": None,
        "allowed_actions": allowed_actions,
        "blocked_actions": [],
        "idempotency_key": "owner-route::dm002::writer-handoff",
    }


def test_materialize_domain_action_requests_preserves_current_quality_repair_writer_handoff(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    monkeypatch.setenv("OPL_STATE_DIR", str(tmp_path / "opl-state"))
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm002")
    route = _owner_route(
        study_id=study_id,
        quest_id="quest-dm002",
        next_owner="write",
        owner_reason="manuscript_story_surface_delta_missing",
        allowed_actions=["run_quality_repair_batch"],
    )
    action = {
        "study_id": study_id,
        "quest_id": "quest-dm002",
        "action_type": "run_quality_repair_batch",
        "authority": "observability_only",
        "owner": "write",
        "reason": "manuscript_story_surface_delta_missing",
        "required_output_surface": (
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        "owner_route": route,
        "next_work_unit": {"unit_id": "dm002_same_line_methods_display_package_repair", "lane": "write"},
        "handoff_packet": {
            "request_kind": "run_quality_repair_batch",
            "authority": "observability_only",
            "request_owner": "write",
            "owner_route": route,
        },
    }
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": "quest-dm002",
                    "owner_route": route,
                    "action_queue": [action],
                }
            ],
            "action_queue": [action],
        },
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    _write_json(dispatch_path, _writer_handoff(study_id=study_id, dispatch_path=dispatch_path, route=route))
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "quality_repair_batch" / "latest.json",
        {
            "request_kind": "run_quality_repair_batch",
            "status": "requested",
            "study_id": study_id,
            "quest_id": "quest-dm002",
            "request_owner": "write",
            "expected_owner": "write",
            "next_executable_owner": "write",
            "dispatch_authority": "quality_repair_batch_writer_handoff",
            "owner_route": route,
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    dispatch = result["default_executor_dispatches"][0]
    written_dispatch = json.loads(dispatch_path.read_text(encoding="utf-8"))
    immutable_dispatch_path = Path(written_dispatch["refs"]["immutable_dispatch_path"])
    assert dispatch["dispatch_authority"] == "quality_repair_batch_writer_handoff"
    assert dispatch["medical_claim_authoring_allowed"] is True
    assert dispatch["prompt_contract"]["medical_claim_authoring_allowed"] is True
    assert dispatch["prompt_contract"]["allowed_write_surfaces"] == [
        "paper/draft.md",
        "paper/build/review_manuscript.md",
        "paper/claim_evidence_map.json",
        "paper/evidence_ledger.json",
        "paper/review/**",
    ]
    assert dispatch["prompt_contract"]["search_boundaries"]["surface"] == "default_executor_search_discipline.v1"
    assert "grep -R" in dispatch["prompt_contract"]["search_boundaries"]["forbidden_command_patterns"]
    assert "runtime/.ds/**" in dispatch["prompt_contract"]["search_boundaries"]["forbidden_path_globs"]
    assert dispatch["source_action"]["surface"] == "quality_repair_batch"
    assert dispatch["source_action"]["blocked_reason"] == "manuscript_story_surface_delta_missing"
    assert written_dispatch["dispatch_authority"] == "quality_repair_batch_writer_handoff"
    assert written_dispatch["medical_claim_authoring_allowed"] is True
    assert immutable_dispatch_path.is_file()
    assert immutable_dispatch_path.parent.name == "run_quality_repair_batch"
    assert immutable_dispatch_path.parent.parent.name == "immutable"
    immutable_dispatch = json.loads(immutable_dispatch_path.read_text(encoding="utf-8"))
    assert immutable_dispatch["owner_route"] == route
    assert immutable_dispatch["prompt_contract"]["search_boundaries"] == dispatch["prompt_contract"]["search_boundaries"]


def _writer_handoff(*, study_id: str, dispatch_path: Path, route: dict[str, object]) -> dict[str, object]:
    required_output = (
        "canonical manuscript story-surface delta or "
        "typed blocker:manuscript_story_surface_delta_missing"
    )
    return {
        "surface": "default_executor_dispatch_request",
        "schema_version": 1,
        "executor_kind": "codex_cli_default",
        "chat_completion_only_executor_forbidden": True,
        "dispatch_status": "ready",
        "dispatch_authority": "quality_repair_batch_writer_handoff",
        "study_id": study_id,
        "quest_id": "quest-dm002",
        "action_type": "run_quality_repair_batch",
        "action_id": "quality-repair-writer-handoff::dm002::latest",
        "next_executable_owner": "write",
        "required_output_surface": required_output,
        "owner_route": route,
        "idempotency_key": route["idempotency_key"],
        "repeat_suppression_key": route["work_unit_fingerprint"],
        "medical_claim_authoring_allowed": True,
        "prompt_contract": {
            "study_id": study_id,
            "quest_id": "quest-dm002",
            "action_type": "run_quality_repair_batch",
            "next_executable_owner": "write",
            "required_output_surface": required_output,
            "owner_route": route,
            "idempotency_key": route["idempotency_key"],
            "prompt_budget": {"max_prompt_tokens": 6000},
            "compact_evidence_packet_ref": "artifacts/supervision/compact_evidence_packets/run_quality_repair_batch.json",
            "do_not_repeat": True,
            "repeat_suppression_key": route["work_unit_fingerprint"],
            "request_packet_ref": "artifacts/supervision/requests/quality_repair_batch/latest.json",
            "forbidden_surfaces": [
                "manuscript/**",
                "current_package/**",
                "paper/current_package/**",
                "manuscript/current_package/**",
                "src/med_autoscience/platform/**",
                "artifacts/publication_eval/latest.json",
                "artifacts/controller_decisions/latest.json",
            ],
            "allowed_write_surfaces": [
                "paper/draft.md",
                "paper/build/review_manuscript.md",
                "paper/claim_evidence_map.json",
                "paper/evidence_ledger.json",
                "paper/review/**",
            ],
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "manual_study_patch_allowed": False,
            "medical_claim_authoring_allowed": True,
        },
        "source_action": {
            "surface": "quality_repair_batch",
            "blocked_reason": "manuscript_story_surface_delta_missing",
            "next_work_unit": {"unit_id": "dm002_same_line_methods_display_package_repair", "lane": "write"},
        },
        "refs": {"dispatch_path": str(dispatch_path)},
    }
