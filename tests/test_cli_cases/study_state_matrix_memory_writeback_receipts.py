from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

from .shared import write_profile


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _profile_workspace(tmp_path: Path) -> tuple[Path, Path]:
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    return profile_path, workspace_root


def _study_root(workspace_root: Path, study_id: str) -> Path:
    study_root = workspace_root / "studies" / study_id
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")
    return study_root


def _write_memory_router_receipt(
    *,
    workspace_root: Path,
    study_root: Path,
    study_id: str,
    receipt_name: str,
    status: str = "applied",
    memory_family: str = "publication_route_memory",
    receipt_refs: list[str] | None = None,
    writeback_receipt_locator_ref: str = "portfolio/research_memory/publication_route_memory/writeback_receipts",
    accepted_writes: list[dict[str, Any]] | None = None,
    rejected_writes: list[dict[str, Any]] | None = None,
    typed_blockers: list[dict[str, Any]] | None = None,
) -> tuple[Path, Path]:
    router_receipt_ref = Path(f"artifacts/stage_knowledge/memory_write_router_receipts/{receipt_name}.json")
    writeback_receipt_ref = (
        workspace_root
        / "portfolio"
        / "research_memory"
        / "publication_route_memory"
        / "writeback_receipts"
        / f"{receipt_name}.json"
    )
    _write_json(
        study_root / router_receipt_ref,
        {
            "surface": "memory_write_router_receipt",
            "schema_version": 1,
            "study_id": study_id,
            "stage": "decision",
            "memory_family": memory_family,
            "idempotency_key": receipt_name,
            "status": status,
            "apply": True,
            "receipt_refs": receipt_refs
            if receipt_refs is not None
            else [str(study_root / router_receipt_ref), str(writeback_receipt_ref)],
            "writeback_receipt_locator_ref": writeback_receipt_locator_ref,
            "authority_boundary": {"can_write_publication_eval": False, "can_write_memory_body_to_opl": False},
            "accepted_writes": accepted_writes or [],
            "rejected_writes": rejected_writes or [],
            "typed_blockers": typed_blockers or [],
        },
    )
    return router_receipt_ref, writeback_receipt_ref


def _stub_paused_status(*, cli: object, monkeypatch: object, study_root: Path, study_id: str) -> None:
    monkeypatch.setattr(
        cli.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_status": "paused",
            "active_run_id": None,
        },
    )


def _run_state_matrix(*, cli: object, profile_path: Path, capsys: object) -> tuple[int, dict[str, Any]]:
    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()
    return exit_code, json.loads(captured.out)


def test_study_state_matrix_consumes_publication_route_memory_writeback_receipt(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path, workspace_root = _profile_workspace(tmp_path)
    study_id = "002-memory"
    study_root = _study_root(workspace_root, study_id)
    expected_writeback_receipt_ref = (
        workspace_root
        / "portfolio"
        / "research_memory"
        / "publication_route_memory"
        / "writeback_receipts"
        / "accepted-writeback.json"
    )
    router_receipt_ref, writeback_receipt_ref = _write_memory_router_receipt(
        workspace_root=workspace_root,
        study_root=study_root,
        study_id=study_id,
        receipt_name="accepted-writeback",
        accepted_writes=[
            {
                "write_id": "accepted-route-back-lesson",
                "route_family": "route_back_repair",
                "stage_applicability": ["decision", "review"],
                "destination": "workspace_research_memory_proposal",
                "owner_target": "workspace_memory_owner",
                "proposal_ref": "proposal:accepted-route-back-lesson",
                "receipt_ref": str(expected_writeback_receipt_ref),
                "payload": {
                    "lesson": "This memory body must not leak into state matrix output.",
                    "prose_summary": "This prose summary must stay out of the transition table.",
                },
            }
        ],
    )
    assert writeback_receipt_ref == expected_writeback_receipt_ref
    _stub_paused_status(cli=cli, monkeypatch=monkeypatch, study_root=study_root, study_id=study_id)

    exit_code, payload = _run_state_matrix(cli=cli, profile_path=profile_path, capsys=capsys)
    transition = payload["studies"][0]["domain_transition"]
    case = payload["domain_transition_table"]["family_transition_matrix_cases"][0]
    rule = payload["domain_transition_table"]["family_transition_spec"]["transitions"][0]
    consumption = transition["completion_receipt_consumption"]
    rendered = json.dumps(transition, ensure_ascii=False)

    assert exit_code == 0
    assert transition["decision_type"] == "memory_writeback_receipt_consumed"
    assert transition["route_target"] == "inspect"
    assert transition["next_work_unit"]["unit_id"] == "publication_route_memory_writeback_receipt_review"
    assert transition["next_work_unit"]["lane"] == "inspect"
    assert transition["controller_action"] == "none"
    assert transition["owner"] == "med-autoscience"
    assert transition["typed_blocker"]["blocker_id"] == "memory_writeback_receipt_observed"
    assert transition["typed_blocker"]["write_permitted"] is False
    assert transition["guard_boundary"]["required_owner_surface"] == "memory_write_router_receipt"
    assert transition["guard_boundary"]["opl_generic_runner_may_resume"] is False
    assert transition["guard_boundary"]["can_write_domain_truth"] is False
    assert consumption["status"] == "consumed"
    assert consumption["receipt_kind"] == "publication_route_memory_writeback_receipt"
    assert consumption["router_receipt_refs"] == [str(router_receipt_ref)]
    assert consumption["writeback_receipt_refs"] == [str(writeback_receipt_ref)]
    assert consumption["receipt_statuses"] == ["applied"]
    assert consumption["accepted_writeback_ref_count"] == 1
    assert consumption["rejected_writeback_ref_count"] == 0
    assert consumption["typed_blocker_count"] == 0
    assert consumption["body_included"] is False
    assert consumption["quality_authorized"] is False
    assert consumption["submission_authorized"] is False
    assert consumption["can_accept_or_reject_writeback"] is False
    assert consumption["next_action"] == "honor_mas_memory_owner_writeback_receipt"
    assert "This memory body must not leak" not in rendered
    assert "This prose summary must stay out" not in rendered
    assert case["expected"]["decision_type"] == "memory_writeback_receipt_consumed"
    assert case["expected"]["route_target"] == "inspect"
    assert case["expected"]["next_work_unit_id"] == "publication_route_memory_writeback_receipt_review"
    assert case["context"]["completion_receipt_consumption"]["receipt_kind"] == (
        "publication_route_memory_writeback_receipt"
    )
    assert rule["typed_blocker"]["blocker_code"] == "memory_writeback_receipt_observed"
    assert rule["receipt"]["completion_receipt_consumption"]["accepted_writeback_ref_count"] == 1


def test_study_state_matrix_consumes_rejected_publication_route_memory_writeback_receipt(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path, workspace_root = _profile_workspace(tmp_path)
    study_id = "002-memory-rejected"
    study_root = _study_root(workspace_root, study_id)
    router_receipt_ref, writeback_receipt_ref = _write_memory_router_receipt(
        workspace_root=workspace_root,
        study_root=study_root,
        study_id=study_id,
        receipt_name="rejected-writeback",
        rejected_writes=[
            {
                "write_id": "claim-specific-memory",
                "route_family": "local_claim_boundary",
                "stage_applicability": ["review"],
                "destination": "workspace_research_memory_proposal",
                "owner_target": "workspace_memory_owner",
                "reason": "study_specific_claim_not_workspace_memory",
            }
        ],
    )
    _stub_paused_status(cli=cli, monkeypatch=monkeypatch, study_root=study_root, study_id=study_id)

    exit_code, payload = _run_state_matrix(cli=cli, profile_path=profile_path, capsys=capsys)
    transition = payload["studies"][0]["domain_transition"]
    consumption = transition["completion_receipt_consumption"]

    assert exit_code == 0
    assert transition["decision_type"] == "memory_writeback_receipt_consumed"
    assert transition["route_target"] == "inspect"
    assert transition["controller_action"] == "none"
    assert transition["typed_blocker"]["blocker_id"] == "memory_writeback_receipt_observed"
    assert consumption["receipt_kind"] == "publication_route_memory_writeback_receipt"
    assert consumption["router_receipt_refs"] == [str(router_receipt_ref)]
    assert consumption["writeback_receipt_refs"] == [str(writeback_receipt_ref)]
    assert consumption["accepted_writeback_ref_count"] == 0
    assert consumption["rejected_writeback_ref_count"] == 1
    assert consumption["typed_blocker_count"] == 0
    assert consumption["rejected_reasons"] == ["study_specific_claim_not_workspace_memory"]
    assert consumption["next_action"] == "record_rejected_memory_writeback_receipt"
    assert transition["guard_boundary"]["opl_generic_runner_may_resume"] is False


def test_study_state_matrix_consumes_blocked_publication_route_memory_writeback_receipt(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path, workspace_root = _profile_workspace(tmp_path)
    study_id = "002-memory-blocked"
    study_root = _study_root(workspace_root, study_id)
    router_receipt_ref, writeback_receipt_ref = _write_memory_router_receipt(
        workspace_root=workspace_root,
        study_root=study_root,
        study_id=study_id,
        receipt_name="blocked-writeback",
        status="blocked",
        receipt_refs=None,
        typed_blockers=[
            {
                "blocker_id": "memory_writeback_owner_missing",
                "reason": "workspace_memory_owner_receipt_missing",
            }
        ],
    )
    _stub_paused_status(cli=cli, monkeypatch=monkeypatch, study_root=study_root, study_id=study_id)

    exit_code, payload = _run_state_matrix(cli=cli, profile_path=profile_path, capsys=capsys)
    transition = payload["studies"][0]["domain_transition"]
    consumption = transition["completion_receipt_consumption"]

    assert exit_code == 0
    assert transition["decision_type"] == "memory_writeback_receipt_consumed"
    assert transition["route_target"] == "inspect"
    assert consumption["router_receipt_refs"] == [str(router_receipt_ref)]
    assert consumption["writeback_receipt_refs"] == [str(writeback_receipt_ref)]
    assert consumption["receipt_statuses"] == ["blocked"]
    assert consumption["accepted_writeback_ref_count"] == 0
    assert consumption["rejected_writeback_ref_count"] == 0
    assert consumption["typed_blocker_count"] == 1
    assert consumption["typed_blocker_ids"] == ["memory_writeback_owner_missing"]
    assert consumption["typed_blocker_reasons"] == ["workspace_memory_owner_receipt_missing"]
    assert consumption["next_action"] == "record_blocked_memory_writeback_receipt"
    assert transition["guard_boundary"]["opl_generic_runner_may_resume"] is False


def test_study_state_matrix_memory_writeback_receipt_requires_publication_route_family(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path, workspace_root = _profile_workspace(tmp_path)
    study_id = "002-memory-wrong-family"
    study_root = _study_root(workspace_root, study_id)
    _write_memory_router_receipt(
        workspace_root=workspace_root,
        study_root=study_root,
        study_id=study_id,
        receipt_name="wrong-family",
        memory_family="literature_memory",
        accepted_writes=[
            {
                "write_id": "wrong-family-write",
                "destination": "workspace_research_memory_proposal",
            }
        ],
    )
    _stub_paused_status(cli=cli, monkeypatch=monkeypatch, study_root=study_root, study_id=study_id)

    exit_code, payload = _run_state_matrix(cli=cli, profile_path=profile_path, capsys=capsys)
    transition = payload["studies"][0]["domain_transition"]

    assert exit_code == 0
    assert transition["decision_type"] == "fail_closed"
    assert transition["typed_blocker"]["blocker_id"] == "domain_transition_unclassified"
    assert "completion_receipt_consumption" not in transition


def test_study_state_matrix_memory_writeback_receipt_requires_writeback_ref_chain(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path, workspace_root = _profile_workspace(tmp_path)
    study_id = "002-memory-no-ref-chain"
    study_root = _study_root(workspace_root, study_id)
    router_receipt_ref = Path("artifacts/stage_knowledge/memory_write_router_receipts/no-ref-chain.json")
    _write_json(
        study_root / router_receipt_ref,
        {
            "surface": "memory_write_router_receipt",
            "schema_version": 1,
            "study_id": study_id,
            "stage": "decision",
            "memory_family": "publication_route_memory",
            "idempotency_key": "no-ref-chain",
            "status": "applied",
            "apply": True,
            "receipt_refs": [str(study_root / router_receipt_ref)],
            "accepted_writes": [
                {
                    "write_id": "missing-writeback-ref",
                    "destination": "workspace_research_memory_proposal",
                }
            ],
            "rejected_writes": [],
            "typed_blockers": [],
        },
    )
    _stub_paused_status(cli=cli, monkeypatch=monkeypatch, study_root=study_root, study_id=study_id)

    exit_code, payload = _run_state_matrix(cli=cli, profile_path=profile_path, capsys=capsys)
    transition = payload["studies"][0]["domain_transition"]

    assert exit_code == 0
    assert transition["decision_type"] == "fail_closed"
    assert transition["typed_blocker"]["blocker_id"] == "domain_transition_unclassified"
    assert "completion_receipt_consumption" not in transition


def test_study_state_matrix_memory_writeback_receipt_requires_effective_payload(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path, workspace_root = _profile_workspace(tmp_path)
    study_id = "002-memory-empty"
    study_root = _study_root(workspace_root, study_id)
    _write_memory_router_receipt(
        workspace_root=workspace_root,
        study_root=study_root,
        study_id=study_id,
        receipt_name="empty-writeback",
    )
    _stub_paused_status(cli=cli, monkeypatch=monkeypatch, study_root=study_root, study_id=study_id)

    exit_code, payload = _run_state_matrix(cli=cli, profile_path=profile_path, capsys=capsys)
    transition = payload["studies"][0]["domain_transition"]

    assert exit_code == 0
    assert transition["decision_type"] == "fail_closed"
    assert transition["typed_blocker"]["blocker_id"] == "domain_transition_unclassified"
    assert "completion_receipt_consumption" not in transition


def test_study_state_matrix_memory_writeback_receipt_does_not_override_publication_gate_blocker(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path, workspace_root = _profile_workspace(tmp_path)
    study_id = "002-memory-gate-blocked"
    study_root = _study_root(workspace_root, study_id)
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "eval_id": "publication-eval::002-memory-gate-blocked",
            "study_id": study_id,
            "status": "blocked",
            "allow_write": False,
            "blockers": ["missing_external_validation"],
        },
    )
    router_receipt_ref, writeback_receipt_ref = _write_memory_router_receipt(
        workspace_root=workspace_root,
        study_root=study_root,
        study_id=study_id,
        receipt_name="blocked-by-gate",
        accepted_writes=[
            {
                "write_id": "accepted-but-gate-blocked",
                "destination": "workspace_research_memory_proposal",
            }
        ],
    )
    _stub_paused_status(cli=cli, monkeypatch=monkeypatch, study_root=study_root, study_id=study_id)

    exit_code, payload = _run_state_matrix(cli=cli, profile_path=profile_path, capsys=capsys)
    transition = payload["studies"][0]["domain_transition"]

    assert exit_code == 0
    assert transition["decision_type"] == "publication_gate_blocker"
    assert transition["typed_blocker"]["blocker_id"] == "publication_gate_blocked"
    assert transition["route_target"] == "review"
    assert "completion_receipt_consumption" not in transition
    assert str(router_receipt_ref) in transition["source_refs"]
    assert str(writeback_receipt_ref) in transition["source_refs"]


def test_study_state_matrix_memory_writeback_receipt_does_not_override_human_gate(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path, workspace_root = _profile_workspace(tmp_path)
    study_id = "002-memory-human-gate"
    study_root = _study_root(workspace_root, study_id)
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "decision-human-gate-memory",
            "study_id": study_id,
            "requires_human_confirmation": True,
            "family_human_gates": [{"gate_id": f"controller-human-confirmation-{study_id}"}],
            "controller_actions": [{"action_type": "ensure_study_runtime"}],
        },
    )
    _write_memory_router_receipt(
        workspace_root=workspace_root,
        study_root=study_root,
        study_id=study_id,
        receipt_name="human-gate-memory",
        accepted_writes=[
            {
                "write_id": "accepted-but-human-gated",
                "destination": "workspace_research_memory_proposal",
            }
        ],
    )
    _stub_paused_status(cli=cli, monkeypatch=monkeypatch, study_root=study_root, study_id=study_id)

    exit_code, payload = _run_state_matrix(cli=cli, profile_path=profile_path, capsys=capsys)
    transition = payload["studies"][0]["domain_transition"]

    assert exit_code == 0
    assert transition["decision_type"] == "human_gate"
    assert transition["route_target"] == "human_gate"
    assert transition["controller_action"] == "wait_for_human_gate"
    assert "completion_receipt_consumption" not in transition


def test_study_state_matrix_memory_writeback_receipt_does_not_override_stop_loss(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path, workspace_root = _profile_workspace(tmp_path)
    study_id = "002-memory-stop-loss"
    study_root = _study_root(workspace_root, study_id)
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "decision-stop-loss-memory",
            "study_id": study_id,
            "decision_type": "stop_loss",
            "route_decision": "stop_loss",
            "route_target": "stop",
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "stop_runtime"}],
        },
    )
    _write_memory_router_receipt(
        workspace_root=workspace_root,
        study_root=study_root,
        study_id=study_id,
        receipt_name="stop-loss-memory",
        accepted_writes=[
            {
                "write_id": "accepted-but-stopped",
                "destination": "workspace_research_memory_proposal",
            }
        ],
    )
    _stub_paused_status(cli=cli, monkeypatch=monkeypatch, study_root=study_root, study_id=study_id)

    exit_code, payload = _run_state_matrix(cli=cli, profile_path=profile_path, capsys=capsys)
    transition = payload["studies"][0]["domain_transition"]

    assert exit_code == 0
    assert transition["decision_type"] == "stop_loss"
    assert transition["route_target"] == "stop"
    assert transition["controller_action"] == "stop_runtime"
    assert transition["completion_receipt_consumption"]["receipt_kind"] == "mas_owner_stop_loss_receipt"
    assert transition["guard_boundary"]["opl_generic_runner_may_resume"] is False
