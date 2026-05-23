from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_sidecar_export_hydrates_owner_route_handoff_artifact_without_runtime_state_mutation(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_handoff")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    handoff_path = study_root / "artifacts" / "supervision" / "owner_route_handoff" / "latest.json"
    runtime_state_path = profile.runtime_root / study_id / ".ds" / "runtime_state.json"
    runtime_queue_path = profile.runtime_root / study_id / ".ds" / "user_message_queue.json"
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    controller_decisions_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    current_package_readme = study_root / "manuscript" / "current_package" / "README.md"
    current_package_zip = study_root / "manuscript" / "current_package.zip"
    _write_json(
        runtime_state_path,
        {
            "status": "waiting_for_user",
            "quest_id": study_id,
            "active_run_id": "run-opl-owned",
            "worker_running": True,
            "continuation_policy": "auto",
            "continuation_anchor": "decision",
            "continuation_reason": "controller_work_unit_pending",
        },
    )
    _write_json(runtime_queue_path, {"messages": ["do-not-touch"]})
    _write_json(publication_eval_path, {"status": "ready", "body": "do-not-touch"})
    _write_json(controller_decisions_path, {"decision_type": "continue", "body": "do-not-touch"})
    current_package_readme.parent.mkdir(parents=True, exist_ok=True)
    current_package_readme.write_text("do-not-touch\n", encoding="utf-8")
    current_package_zip.parent.mkdir(parents=True, exist_ok=True)
    current_package_zip.write_bytes(b"do-not-touch")
    _write_json(
        handoff_path,
        {
            "surface_kind": "mas_runtime_owner_route_handoff_record",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": study_id,
            "runtime_state_mutated": False,
            "handoff": {
                "surface_kind": "mas_runtime_owner_route_handoff",
                "domain_truth_owner": "med-autoscience",
                "queue_owner": "one-person-lab",
                "dispatch_surface": "medautosci sidecar export -> medautosci sidecar dispatch",
                "recommended_task_kind": "domain_route/owner-handoff",
                "study_id": study_id,
                "quest_id": study_id,
                "runtime_state_path": str(runtime_state_path),
                "source": "owner_route_reconcile_platform_repair",
                "reason": "quest_waiting_opl_runtime_owner_route",
                "repair_kind": "controller_work_unit_pending_redrive",
                "authority_boundary": {
                    "mas_writes_generic_runtime_queue": False,
                    "mas_submits_runtime_chat": False,
                    "mas_resumes_provider_worker": False,
                    "opl_writes_mas_truth": False,
                    "mas_owner_receipt_required": True,
                },
            },
        },
    )

    export = module.export_family_sidecar(
        profile=profile,
        profile_ref=tmp_path / "profile.toml",
    )

    tasks = [
        task
        for task in export["pending_family_tasks"]
        if task["task_kind"] == "domain_route/owner-handoff"
        and task["dedupe_key"] == (
            "mas:diabetes:002-dm-china-us-mortality-attribution:"
            "owner-route-handoff:quest_waiting_opl_runtime_owner_route"
        )
    ]
    assert len(tasks) == 1
    task = tasks[0]
    assert task["queue_owner"] == "one-person-lab"
    assert task["domain_truth_owner"] == "med-autoscience"
    assert task["opl_runtime_owner_route_handoff"]["authority_boundary"]["mas_resumes_provider_worker"] is False
    route_contract = task["route_transition_contract"]
    assert route_contract["route_is_stage"] is False
    assert route_contract["queue_owner"] == "one-person-lab"
    assert route_contract["domain_truth_owner"] == "med-autoscience"
    assert route_contract["runtime_transition_owner"] == "one-person-lab"
    assert "owner_route_ref" in route_contract["allowed_payload_refs"]
    assert "runtime_event_refs" in route_contract["allowed_payload_refs"]
    assert "artifact_body" in route_contract["forbidden_payload_refs"]
    assert "current_package_mutation" in route_contract["forbidden_writes"]
    assert ".ds/runtime_state.json" in route_contract["forbidden_writes"]
    assert "runtime_queue_state" in route_contract["forbidden_writes"]
    assert route_contract["authority_boundary"]["mas_owner_receipt_required"] is True
    assert route_contract["authority_boundary"]["opl_writes_mas_truth"] is False
    assert task["payload"]["route_transition_contract"] == route_contract

    graph_handoff = task["stage_graph_handoff"]
    assert graph_handoff["route_is_stage"] is False
    assert graph_handoff["stage_graph_owner"] == "one-person-lab"
    assert graph_handoff["domain_truth_owner"] == "med-autoscience"
    journal_hint = graph_handoff["route_stage_graph_hints"]["journal-resolution"]
    assert journal_hint["stage"] == "finalize_and_publication_handoff"
    assert journal_hint["route"] == "journal-resolution"
    assert "journal_requirements_resolution" in journal_hint["stage_graph_nodes"]
    assert "format_delta_plan" in journal_hint["stage_graph_nodes"]
    assert "artifact_mutation_authorization" in journal_hint["stage_graph_nodes"]
    assert "independent_format_review" in journal_hint["stage_graph_nodes"]
    assert "target_journal_ref" in journal_hint["allowed_handoff_refs"]
    assert "format_requirement_refs" in journal_hint["allowed_handoff_refs"]
    assert "artifact_body" in journal_hint["forbidden_handoff_refs"]
    assert graph_handoff["route_stage_graph_hints"]["finalize"]["stage"] == (
        "finalize_and_publication_handoff"
    )
    assert task["payload"]["stage_graph_handoff"] == graph_handoff
    evidence_payload = task["domain_dispatch_evidence_record_payload"]
    assert evidence_payload["surface_kind"] == "mas_domain_dispatch_evidence_record_payload"
    assert evidence_payload["task_kind"] == "domain_route/owner-handoff"
    assert evidence_payload["study_id"] == study_id
    assert task["source_fingerprint"]
    assert evidence_payload["source_fingerprint"] == task["source_fingerprint"]
    assert evidence_payload["profile_name"] == profile.name
    assert {
        key: evidence_payload["record_payload"][key]
        for key in ("domain_id", "task_kind", "study_id", "source_fingerprint", "profile_name")
    } == {
        "domain_id": "medautoscience",
        "task_kind": "domain_route/owner-handoff",
        "study_id": study_id,
        "source_fingerprint": task["source_fingerprint"],
        "profile_name": profile.name,
    }
    assert evidence_payload["body_included"] is False
    assert evidence_payload["domain_ready_claimed"] is False
    assert evidence_payload["publication_ready_claimed"] is False
    assert evidence_payload["artifact_mutation_authorized"] is False
    assert evidence_payload["record_payload"]["typed_blocker_refs"]
    assert evidence_payload["record_payload"]["evidence_refs"] == [
        "studies/002-dm-china-us-mortality-attribution/"
        "artifacts/supervision/owner_route_handoff/latest.json",
        "contracts/production_acceptance/mas-production-acceptance.json"
        "#/paper_line_guarded_apply_evidence",
    ]
    assert evidence_payload["record_payload"]["no_regression_refs"]
    assert evidence_payload["authority_boundary"]["opl_records_refs_only"] is True
    assert evidence_payload["authority_boundary"]["provider_completion_is_domain_ready"] is False
    assert {
        packet["role"] for packet in evidence_payload["body_free_evidence_packets"]
    } == {"stable_typed_blocker_ref", "no_forbidden_write_proof_ref"}
    rendered_payload = json.dumps(evidence_payload, ensure_ascii=False)
    assert "current_package_body" in evidence_payload["forbidden_payload_fields"]
    assert "do-not-touch" not in rendered_payload

    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))
    assert runtime_state["active_run_id"] == "run-opl-owned"
    assert runtime_state["worker_running"] is True
    assert "last_opl_runtime_owner_route_handoff" not in runtime_state
    assert json.loads(runtime_queue_path.read_text(encoding="utf-8")) == {"messages": ["do-not-touch"]}
    assert json.loads(publication_eval_path.read_text(encoding="utf-8")) == {
        "status": "ready",
        "body": "do-not-touch",
    }
    assert json.loads(controller_decisions_path.read_text(encoding="utf-8")) == {
        "decision_type": "continue",
        "body": "do-not-touch",
    }
    assert current_package_readme.read_text(encoding="utf-8") == "do-not-touch\n"
    assert current_package_zip.read_bytes() == b"do-not-touch"
