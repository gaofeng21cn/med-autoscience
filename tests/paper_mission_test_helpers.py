from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

from tests.profile_test_helpers import write_profile

FORBIDDEN_AUTHORITY_RELATIVE_PATHS = (
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "paper/current_package",
)
DM_CANARY_FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1] / "fixtures" / "paper_mission_dm_canary"
)

def _paper_mission_forbidden_write_guard() -> dict:
    return {
        "candidate_writes_authority": False,
        "blocked_paths": [
            "publication_eval/latest.json",
            "controller_decisions/latest.json",
            "current_package",
            "runtime queue/provider attempts",
            "/Users/gaofeng/workspace/Yang/**",
        ],
        "forbidden_claims": [
            "publication_ready",
            "current_package",
            "owner_receipt_written",
        ],
    }


def _write_profile_with_study(tmp_path: Path, *, study_id: str = "001-paper") -> Path:
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path, workspace_root=workspace_root)
    (workspace_root / "studies" / study_id).mkdir(parents=True)
    return profile_path


def _assert_forbidden_authority_untouched(tmp_path: Path, *, study_id: str = "001-paper") -> None:
    study_root = tmp_path / "workspace" / "studies" / study_id
    for relative_path in FORBIDDEN_AUTHORITY_RELATIVE_PATHS:
        assert not (study_root / relative_path).exists()


def _assert_route_identity_matches_carrier(projected: dict, carrier: dict) -> None:
    for field in (
        "route_identity_key",
        "attempt_idempotency_key",
        "request_idempotency_key",
    ):
        assert projected[field] == carrier[field]


def _write_fake_opl_stage_route_runtime(
    path: Path,
    *,
    capture_path: Path,
    task_id: str,
    running_stage_attempt_id: str,
    terminal_stage_attempt_id: str | None = None,
    terminal_on_first_readback: bool = False,
    include_queue_stage_attempts: bool = False,
) -> Path:
    if terminal_on_first_readback and terminal_stage_attempt_id is None:
        raise ValueError("terminal_stage_attempt_id is required")
    terminal_stage_attempt_id = terminal_stage_attempt_id or running_stage_attempt_id
    path.write_text(
        dedent(
            f"""\
            #!/usr/bin/env python3
            import json, sys
            capture_path = {str(capture_path)!r}
            terminal_on_first = {terminal_on_first_readback!r}
            include_queue_stage_attempts = {include_queue_stage_attempts!r}
            args = sys.argv[1:]
            try:
                records = json.loads(open(capture_path, encoding='utf-8').read())
            except Exception:
                records = []
            def persist(record):
                records.append(record)
                open(capture_path, 'w', encoding='utf-8').write(json.dumps(records))
            def payloads():
                return [r['payload'] for r in records if 'payload' in r]
            def current_payload():
                ps = payloads()
                return (ps[-1] if terminal_on_first else ps[0]) if ps else {{}}
            def workspace_locator(payload):
                return {{key: payload.get(key) for key in (
                    'study_id', 'paper_mission_transaction_ref', 'opl_route_command_ref',
                    'command_kind', 'route_target'
                )}}
            def running_attempt(payload):
                return {{
                    'surface_kind': 'opl_stage_attempt_running_readback',
                    'status': 'running',
                    'stage_id': payload.get('route_target'),
                    'stage_attempt_id': {running_stage_attempt_id!r},
                    'provider_status': 'running',
                    'workspace_locator': workspace_locator(payload),
                }}
            def terminal_attempt(payload):
                return {{
                    'surface_kind': 'opl_stage_attempt_terminal_readback',
                    'status': 'completed',
                    'stage_id': payload.get('route_target'),
                    'stage_attempt_id': {terminal_stage_attempt_id!r},
                    'closeout_receipt_status': 'accepted_typed_closeout',
                    'typed_blocker_ref': 'typed-blocker:domain-gate-pending',
                    'blocked_reason': 'paper_mission_stage_route_domain_gate_pending',
                    'domain_ready_verdict': 'domain_gate_pending',
                    'closeout_refs': [payload.get('opl_route_command_ref'), payload.get('paper_mission_transaction_ref')],
                    'workspace_locator': workspace_locator(payload),
                }}
            def current_attempt(payload):
                ps = payloads()
                return terminal_attempt(payload) if terminal_on_first and len(ps) == 1 else running_attempt(payload)
            def current_task(payload):
                return {{
                    'task_id': {task_id!r},
                    'domain_id': 'medautoscience',
                    'task_kind': 'domain_route/stage-route',
                    'status': 'running',
                    'payload': payload,
                }}
            if args[:2] == ['family-runtime', 'enqueue']:
                payload = json.loads(args[args.index('--payload') + 1])
                persist({{'argv': args, 'payload': payload}})
                print(json.dumps({{'version':'g2','family_runtime_enqueue':{{'surface_id':'opl_family_runtime_enqueue','accepted':True,'idempotent_noop':False,'task':{{'task_id':{task_id!r},'status':'queued','payload':payload}}}}}}))
            elif args[:2] == ['family-runtime', 'tick']:
                persist({{'argv': args}})
                print(json.dumps({{'family_runtime_tick':{{'selected_count':1,'dispatches':[{{'status':'running','stage_run_request':{{'stage_run_created':True,'provider_attempt_requested':True,'provider_running':True}}}}]}}}}))
            elif args[:3] == ['family-runtime', 'queue', 'list']:
                payload = current_payload()
                attempt = current_attempt(payload)
                task = current_task(payload)
                queue = {{'tasks': [task]}}
                if include_queue_stage_attempts:
                    queue.update({{'queue': {{'total': 1}}, 'stage_attempts': [attempt]}})
                print(json.dumps({{'family_runtime_queue': queue}}))
            elif args[:3] == ['family-runtime', 'queue', 'inspect']:
                payload = current_payload()
                attempt = current_attempt(payload)
                task = current_task(payload)
                print(json.dumps({{'family_runtime_task':{{'task':task,'stage_attempts':[attempt]}}}}))
            else:
                persist({{'argv': args}})
                print(json.dumps({{'error':'unexpected_args','args':args}}))
            """
        ),
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


def _write_paper_source_fixture(tmp_path: Path, *, study_id: str) -> None:
    paper_root = tmp_path / "workspace" / "studies" / study_id / "paper"
    (paper_root / "build").mkdir(parents=True, exist_ok=True)
    (paper_root / "tables").mkdir(parents=True, exist_ok=True)
    (paper_root / "figures").mkdir(parents=True, exist_ok=True)
    (paper_root / "review").mkdir(parents=True, exist_ok=True)
    (paper_root / "draft.md").write_text(
        "\n".join(
            [
                "# DM paper draft",
                "",
                "## Methods",
                "Current methods text.",
                "",
                "## Results",
                "Current results text.",
                "",
                "## Limitations",
                "Current limitations text.",
            ]
        ),
        encoding="utf-8",
    )
    (paper_root / "build" / "review_manuscript.md").write_text(
        "\n".join(
            [
                "# Review manuscript",
                "",
                "## Discussion",
                "Reviewer-facing discussion text.",
            ]
        ),
        encoding="utf-8",
    )
    (paper_root / "claim_evidence_map.json").write_text(
        json.dumps(
            {
                "claims": [
                    {
                        "claim_id": "claim-primary",
                        "title": "Primary mortality gap claim",
                        "status": "needs_binding",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (paper_root / "evidence_ledger.json").write_text(
        json.dumps(
            {
                "evidence": [
                    {
                        "evidence_id": "ev-primary",
                        "title": "Model comparison evidence",
                        "source_ref": "analysis://primary-model",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (paper_root / "tables" / "table_catalog.json").write_text(
        json.dumps(
            {
                "tables": [
                    {
                        "table_id": "T1",
                        "title": "Cohort characteristics",
                        "status": "candidate",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (paper_root / "figures" / "figure_catalog.json").write_text(
        json.dumps(
            {
                "figures": [
                    {
                        "figure_id": "F1",
                        "title": "Attribution curve",
                        "status": "candidate",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (paper_root / "review" / "review_ledger.json").write_text(
        json.dumps(
            {
                "reviews": [
                    {
                        "id": "gate-1",
                        "verdict": "revise",
                        "section": "Results",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


def _write_candidate_manifest(
    tmp_path: Path,
    *,
    study_id: str = "001-paper",
    requested_outcome: str = "accepted_candidate",
    paper_mission_transaction: dict | None = None,
) -> Path:
    candidate_path = tmp_path / "candidate.json"
    candidate = {
        "candidate_id": "pmc-001",
        "mission_id": f"paper-mission::{study_id}::gate-clearing::manual",
        "study_id": study_id,
        "requested_outcome": requested_outcome,
        "candidate_manifest_ref": "paper-mission/pmc-001.json",
        "candidate_artifact_refs": ["paper-mission/patch-plan.md"],
        "source_readiness_refs": ["source-readiness:001"],
        "quality_auditor_requirement": {
            "independent_auditor_required": True,
            "owner": "MedAutoScience",
        },
        "artifact_authority_boundary": {
            "artifact_authority_owner": "MedAutoScience",
            "candidate_is_authority": False,
            "can_update_current_package": False,
            "can_write_paper_body": False,
        },
        "next_owner": "mas_authority_kernel",
        "resume_condition": "MAS consumes or routes back the mission candidate",
    }
    if paper_mission_transaction is not None:
        candidate["paper_mission_transaction"] = paper_mission_transaction
    if requested_outcome == "typed_blocker_required":
        candidate["typed_blocker_request"] = {
            "blocker_id": "source_readiness_missing",
            "blocker_ref": "typed-blocker-request:pmc-001",
        }
    if requested_outcome == "human_gate_required":
        candidate["human_gate_request"] = {
            "decision_packet_ref": "human-gate-request:pmc-001",
        }
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    return candidate_path


def _paper_mission_transaction_payload(
    *,
    mission_id: str,
    study_id: str,
    decision_kind: str = "route_back",
) -> dict:
    transaction_id = "paper-mission-transaction::pmc-001"
    stage_id = "paper-stage::gate-clearing"
    stage_run_ref = "opl-stage-run://pmc-001"
    if decision_kind == "advance":
        terminal_decision = {
            "decision_kind": "advance",
            "status": "accepted",
            "reason": "candidate accepted for the next MAS paper stage",
            "next_owner": "analysis-campaign",
            "next_stage_id": "finalize_and_publication_handoff",
        }
        route_command = {
            "command_kind": "start_next_stage",
            "target": "finalize_and_publication_handoff",
            "reason": "candidate accepted for the next MAS paper stage",
            "source_terminal_decision_ref": f"{transaction_id}#stage_terminal_decision",
            "stage_run_ref": stage_run_ref,
            "runtime_owner": "one-person-lab",
            "declarative_target_stage_id": "finalize_and_publication_handoff",
        }
        transaction_state = "accepted"
    elif decision_kind == "continue_same_stage":
        terminal_decision = {
            "decision_kind": "continue_same_stage",
            "status": "accepted_submission_milestone_candidate",
            "reason": "candidate accepted for continued paper-facing work",
            "next_owner": "mission_executor",
            "target_stage_id": "finalize_and_publication_handoff",
            "next_work_unit": "continue paper-facing submission milestone work",
        }
        route_command = {
            "command_kind": "resume_stage",
            "target": "continue paper-facing submission milestone work",
            "reason": "candidate accepted for continued paper-facing work",
            "source_terminal_decision_ref": f"{transaction_id}#stage_terminal_decision",
            "stage_run_ref": stage_run_ref,
            "runtime_owner": "one-person-lab",
            "declarative_target_stage_id": "finalize_and_publication_handoff",
        }
        transaction_state = "accepted_submission_milestone_candidate"
    elif decision_kind == "typed_blocker":
        terminal_decision = {
            "decision_kind": "typed_blocker",
            "status": "typed_blocker",
            "reason": "source readiness is missing",
            "next_owner": "mas_authority_kernel",
            "blocker_id": "source_readiness_missing",
            "unblock_condition": "MAS authority kernel records or rejects the typed blocker request",
        }
        route_command = {
            "command_kind": "stop_with_typed_blocker",
            "target": "source_readiness_missing",
            "reason": "source readiness is missing",
            "source_terminal_decision_ref": f"{transaction_id}#stage_terminal_decision",
            "stage_run_ref": stage_run_ref,
            "runtime_owner": "one-person-lab",
        }
        transaction_state = "typed_blocker"
    else:
        terminal_decision = {
            "decision_kind": "route_back",
            "status": "terminal_decision_recorded",
            "reason": "candidate needs a claim/evidence repair pass",
            "next_owner": "mission_executor",
            "target_stage_id": "review_and_quality_gate",
            "repair_scope": "claim-evidence-repair",
        }
        route_command = {
            "command_kind": "route_back",
            "target": "review_and_quality_gate",
            "reason": "MAS terminal decision requested route back",
            "source_terminal_decision_ref": f"{transaction_id}#stage_terminal_decision",
            "stage_run_ref": stage_run_ref,
            "runtime_owner": "one-person-lab",
            "declarative_target_stage_id": "review_and_quality_gate",
        }
        transaction_state = "terminal_decision_recorded"
    fingerprint = (
        f"{mission_id}::{stage_id}::{terminal_decision['decision_kind']}::"
        f"{terminal_decision['status']}"
    )
    return {
        "transaction_id": transaction_id,
        "mission_id": mission_id,
        "study_id": study_id,
        "stage_id": stage_id,
        "stage_run_ref": stage_run_ref,
        "stage_terminal_decision": terminal_decision,
        "opl_route_command": route_command,
        "artifact_delta_refs": [
            {
                "ref_id": "artifact-delta::pmc-001",
                "ref_kind": "candidate_artifact_delta",
                "uri": "mission://pmc-001/artifact-delta",
            }
        ],
        "paper_audit_pack_refs": {
            family: [
                {
                    "ref_id": f"{family}::pmc-001",
                    "ref_kind": family,
                    "uri": f"mission://pmc-001/{family}",
                }
            ]
            for family in (
                "analysis_rationale_log",
                "decision_trace",
                "evidence_ledger_delta",
                "review_ledger_delta",
                "revision_log_delta",
                "failed_path_ledger",
                "artifact_lineage",
                "reproducibility_refs",
            )
        },
        "authority_boundary": {
            "mas_authority_owner": "MedAutoScience",
            "runtime_owner": "one-person-lab",
            "writes_authority_surface": False,
            "writes_publication_eval": False,
            "writes_controller_decision": False,
            "writes_owner_receipt": False,
            "writes_typed_blocker": False,
            "writes_human_gate": False,
            "writes_current_package": False,
            "writes_runtime_queue": False,
            "writes_provider_attempt": False,
            "writes_yang_authority": False,
        },
        "idempotency": {
            "idempotency_key": f"{study_id}::{stage_id}::{decision_kind}",
            "transaction_fingerprint": fingerprint,
        },
        "transaction_state": transaction_state,
    }


def _write_matching_domain_gate_closeout(
    *,
    study_root: Path,
    study_id: str,
    transaction: dict,
) -> Path:
    closeout_root = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapter_receipt"
    )
    closeout_root.mkdir(parents=True, exist_ok=True)
    closeout_ref = closeout_root / "sat-terminal.closeout.json"
    closeout_ref.write_text(
        json.dumps(
            {
                "surface_kind": "stage_attempt_closeout_packet",
                "status": "blocked",
                "study_id": study_id,
                "stage_id": transaction["opl_route_command"]["target"],
                "stage_attempt_id": "sat-terminal",
                "action_type": transaction["opl_route_command"]["command_kind"],
                "work_unit_id": transaction["stage_id"],
                "work_unit_fingerprint": transaction["idempotency"][
                    "transaction_fingerprint"
                ],
                "stage_packet_ref": (
                    f"{transaction['transaction_id']}#stage_terminal_decision"
                ),
                "opl_route_command_ref": (
                    f"{transaction['transaction_id']}#opl_route_command"
                ),
                "provider_attempt_ref": "temporal://attempt/sat-terminal",
                "provider_completion_is_domain_completion": False,
                "provider_completion_is_domain_ready": False,
                "domain_completion_claimed": False,
                "domain_ready_claimed": False,
                "typed_blocker_ref": (
                    "artifacts/supervision/consumer/owner_callable_adapter_receipt/"
                    "sat-terminal.closeout.json#domain_blocker"
                ),
                "blocked_reason": "domain_gate_pending",
                "closeout_refs": [
                    f"{transaction['transaction_id']}#opl_route_command",
                    "artifacts/supervision/consumer/owner_callable_adapter_receipt/"
                    "sat-terminal.closeout.json",
                    "typed-blocker:domain_gate_pending",
                ],
                "authority_boundary": {
                    "record_only_surface": True,
                    "provider_completion_is_domain_completion": False,
                    "artifact_mutation_authorized": False,
                    "publication_eval_latest_write_authorized": False,
                    "controller_decision_write_authorized": False,
                },
            }
        ),
        encoding="utf-8",
    )
    return closeout_ref


def _write_submission_milestone_package(
    *,
    workspace_root: Path,
    study_id: str,
    mission_id: str,
    base_transaction: dict,
    requested_outcome: str = "accepted_candidate",
) -> Path:
    package_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_candidate_package"
        / "sat-current"
        / study_id
    )
    package_root.mkdir(parents=True)
    candidate_manifest = {
        "candidate_id": f"paper-mission-candidate::{study_id}::submission",
        "mission_id": mission_id,
        "study_id": study_id,
        "requested_outcome": requested_outcome,
        "candidate_manifest_ref": str(package_root / "candidate_manifest.json"),
        "candidate_artifact_refs": [
            str(package_root / "paper_facing_candidate_delta.json"),
        ],
        "source_readiness_refs": [f"source-readiness:{study_id}"],
        "quality_auditor_requirement": {
            "independent_auditor_required": True,
            "owner": "MedAutoScience",
        },
        "artifact_authority_boundary": {
            "artifact_authority_owner": "MedAutoScience",
            "candidate_is_authority": False,
            "can_update_current_package": False,
            "can_write_paper_body": False,
        },
        "next_owner": "one-person-lab",
        "resume_condition": "MAS consumes or routes the milestone package",
        "paper_mission_transaction": base_transaction,
    }
    (package_root / "candidate_manifest.json").write_text(
        json.dumps(candidate_manifest),
        encoding="utf-8",
    )
    (package_root / "owner_blocker_packet.json").write_text(
        json.dumps(
            {
                "surface_kind": "paper_mission_owner_blocker_packet",
                "status": "owner_blocker_candidate_ready",
                "blocker_kind": "missing_opl_runtime_readback",
                "study_id": study_id,
                "mission_id": mission_id,
                "next_owner": "one-person-lab",
            }
        ),
        encoding="utf-8",
    )
    package_manifest = {
        "surface_kind": "paper_mission_foreground_candidate_package_manifest",
        "schema_version": 1,
        "mode": "non_authority_candidate_package",
        "milestone_kind": "submission_milestone_candidate",
        "requested_outcome": requested_outcome,
        "study_id": study_id,
        "mission_id": mission_id,
        "counts_as_paper_progress": True,
        "candidate_is_authority": False,
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang_authority": False,
        "writes_paper_body": False,
        "can_claim_submission_ready": False,
        "can_claim_publication_ready": False,
        "can_claim_current_package": False,
        "can_claim_owner_receipt_written": False,
        "artifact_refs": {
            "candidate_manifest": str(package_root / "candidate_manifest.json"),
            "paper_facing_candidate_delta": str(
                package_root / "paper_facing_candidate_delta.json"
            ),
        },
        "paper_facing_candidate_delta_ref": str(
            package_root / "paper_facing_candidate_delta.json"
        ),
        "owner_consumption_request_ref": str(
            package_root / "owner_consumption_request.json"
        ),
        "owner_blocker_packet_ref": str(package_root / "owner_blocker_packet.json"),
    }
    package_manifest_path = package_root / "package_manifest.json"
    package_manifest_path.write_text(json.dumps(package_manifest), encoding="utf-8")
    return package_manifest_path


__all__ = [
    "DM_CANARY_FIXTURE_ROOT",
    "FORBIDDEN_AUTHORITY_RELATIVE_PATHS",
    "_assert_forbidden_authority_untouched",
    "_assert_route_identity_matches_carrier",
    "_paper_mission_forbidden_write_guard",
    "_paper_mission_transaction_payload",
    "_write_candidate_manifest",
    "_write_fake_opl_stage_route_runtime",
    "_write_matching_domain_gate_closeout",
    "_write_paper_source_fixture",
    "_write_profile_with_study",
    "_write_submission_milestone_package",
]
