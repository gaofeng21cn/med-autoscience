from __future__ import annotations

from collections.abc import Sequence
import json
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, Mapping

from med_autoscience.controllers.study_launch_projection import launch_study
from med_autoscience.controllers.study_task_submission import submit_study_task
from med_autoscience.controllers.study_progress.projection import read_study_progress
from med_autoscience.domain_entry_contract import SERVICE_SAFE_DOMAIN_COMMANDS
from med_autoscience.paper_mission_domain import build_paper_mission_readback
from med_autoscience.profiles import WorkspaceProfile, load_profile


DISPLAY_PACK_DOMAIN_COMMANDS = frozenset(
    {
        "display-pack-capability-discover",
        "display-pack-orchestrate",
        "display-pack-figure-plan",
        "display-pack-preflight",
        "display-pack-render",
    }
)
RESEARCH_INTEGRITY_DOMAIN_COMMANDS = frozenset(
    {
        "research-integrity-gate-input",
        "research-integrity-reference-verification",
        "research-integrity-review-publication-gate-stage-hook",
    }
)
RESEARCH_INTEGRITY_FORBIDDEN_AUTHORITY_FLAGS = (
    "can_write_mas_study_truth",
    "can_write_publication_eval_latest",
    "can_write_publication_eval",
    "can_write_controller_decisions",
    "can_mutate_current_package",
    "can_write_current_package",
    "can_sign_owner_receipt",
    "can_write_owner_receipt",
    "can_materialize_typed_blocker",
    "can_write_typed_blocker",
    "can_materialize_human_gate",
    "can_write_runtime_queue_or_provider_attempt",
    "can_authorize_publication_quality",
    "can_authorize_publication_readiness",
    "can_authorize_submission_readiness",
)
class MedAutoScienceDomainEntry:
    """给 OPL framework、direct MAS skill 和 CLI 复用的 service-safe structured entry。"""

    def __init__(
        self,
        *,
        profile_loader: Callable[[str | Path], WorkspaceProfile] | None = None,
    ) -> None:
        self._profile_loader = profile_loader or load_profile

    def dispatch(self, request: Mapping[str, Any]) -> dict[str, Any]:
        command = _require_command(request).replace("_", "-")
        if command == "paper-mission":
            _assert_required_fields(
                command=command,
                required_fields=("profile_ref", "study_id"),
                request=request,
            )
            profile_ref = Path(str(request["profile_ref"])).expanduser().resolve()
            profile = self._profile_loader(profile_ref)
            payload = build_paper_mission_readback(
                profile=profile,
                profile_ref=profile_ref,
                study_id=str(request["study_id"]),
                paper_mission_command=str(request.get("paper_mission_command") or "inspect"),
                objective=_optional_text(request.get("objective")),
                mission_id=_optional_text(request.get("mission_id")),
                candidate=_optional_text(request.get("candidate")),
                run_id=_optional_text(request.get("run_id")),
                output_root=_optional_text(request.get("output_root")),
                submit_opl_runtime=bool(request.get("submit_opl_runtime")),
                opl_bin=_optional_text(request.get("opl_bin")),
                dry_run=bool(request.get("dry_run")),
                source="domain-entry",
            )
            return _with_command(command, payload)
        spec = SERVICE_SAFE_DOMAIN_COMMANDS.get(command)
        if spec is None:
            raise ValueError(f"不支持的 domain entry command: {command}")

        _assert_required_fields(command=command, required_fields=spec.required_fields, request=request)

        if command in {"domain-handler-export", "domain-handler-dispatch"}:
            payload = _dispatch_domain_handler(command, request)
            return _with_command(command, payload)

        if command in DISPLAY_PACK_DOMAIN_COMMANDS:
            payload = _dispatch_display_pack_command(command, request)
            return _with_command(command, payload)

        if command in RESEARCH_INTEGRITY_DOMAIN_COMMANDS:
            payload = _dispatch_research_integrity_command(command, request)
            return _with_command(command, payload)

        if command in {
            "study-state-matrix",
            "export-inspection-package",
            "publication-aftercare-plan",
            "delivery-authority-backfill-apply",
            "external-learning-adoption-closure",
            "scientific-capability-registry",
            "mainline-status",
            "mainline-phase",
        }:
            payload = _dispatch_domain_capability(command, request)
            return _with_command(command, payload)

        profile_ref = Path(str(request["profile_ref"])).expanduser().resolve()
        profile = self._profile_loader(profile_ref)
        payload = _dispatch_profile_command(
            command=command,
            request=request,
            profile=profile,
            profile_ref=profile_ref,
        )

        return _with_command(command, payload)


def _assert_required_fields(
    *,
    command: str,
    required_fields: tuple[str, ...],
    request: Mapping[str, Any],
) -> None:
    missing_fields = [
        field_name for field_name in required_fields if not _has_structured_value(request.get(field_name))
    ]
    if missing_fields:
        raise ValueError(f"domain entry `{command}` 缺少必填字段: {', '.join(missing_fields)}")


def _with_command(command: str, payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise TypeError(f"domain entry `{command}` 返回值必须是 mapping。")
    if "command" in payload:
        return payload
    return {"command": command, **payload}


def _dispatch_profile_command(
    *,
    command: str,
    request: Mapping[str, Any],
    profile: WorkspaceProfile,
    profile_ref: Path,
) -> dict[str, Any]:
    handlers = {
        "study-progress": lambda: read_study_progress(
            profile=profile,
            profile_ref=profile_ref,
            study_id=str(request["study_id"]),
            entry_mode=_optional_text(request.get("entry_mode")),
            sync_runtime_summary=False,
            materialize_read_model_artifacts=False,
        ),
        "launch-study": lambda: launch_study(
            profile=profile,
            profile_ref=profile_ref,
            study_id=str(request["study_id"]),
            entry_mode=_optional_text(request.get("entry_mode")),
            allow_stopped_relaunch=bool(request.get("allow_stopped_relaunch")),
            explicit_user_wakeup=bool(request.get("explicit_user_wakeup")),
            force=bool(request.get("force")),
        ),
        "submit-study-task": lambda: submit_study_task(
            profile=profile,
            profile_ref=profile_ref,
            study_id=str(request["study_id"]),
            task_intent=str(request["task_intent"]),
            task_intake_kind=_optional_text(request.get("task_intake_kind")),
            entry_mode=_optional_text(request.get("entry_mode")),
            journal_target=_optional_text(request.get("journal_target")),
            constraints=_sequence_value(request.get("constraints")),
            evidence_boundary=_sequence_value(request.get("evidence_boundary")),
            trusted_inputs=_sequence_value(request.get("trusted_inputs")),
            reference_papers=_sequence_value(request.get("reference_papers")),
            first_cycle_outputs=_sequence_value(request.get("first_cycle_outputs")),
        ),
    }
    try:
        return handlers[command]()
    except KeyError as exc:
        raise ValueError(f"不支持的 profile domain entry command: {command}") from exc


def _require_command(request: Mapping[str, Any]) -> str:
    if not isinstance(request, Mapping):
        raise ValueError("domain entry request 必须是 mapping。")
    command = request.get("command")
    if not isinstance(command, str) or not command.strip():
        raise ValueError("domain entry request 缺少 command。")
    return command.strip()


def _has_structured_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _sequence_value(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(value)
    return (value,)


def _bool_value(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
    return bool(value)


def _optional_int_value(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _optional_mapping_value(value: Any) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def _mapping_value(value: Any, *, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"display pack domain entry `{field_name}` 必须是 mapping。")
    return value


def _dispatch_display_pack_command(command: str, request: Mapping[str, Any]) -> dict[str, Any]:
    from med_autoscience import display_pack_agent

    repo_root = request.get("repo_root")
    paper_root = request.get("paper_root")
    if command == "display-pack-capability-discover":
        return display_pack_agent.display_pack_capability_discover(
            repo_root=repo_root if repo_root is not None else None,
            paper_root=paper_root if paper_root is not None else None,
            include_templates=_bool_value(request.get("include_templates")),
            opl_descriptor_output_dir=request.get("opl_descriptor_output_dir"),
        )
    if command == "display-pack-orchestrate":
        figure_request = request.get("figure_request")
        current_owner_delta = request.get("current_owner_delta")
        return display_pack_agent.display_pack_orchestrate(
            repo_root=repo_root if repo_root is not None else None,
            paper_root=paper_root if paper_root is not None else None,
            current_owner_delta=(
                _mapping_value(current_owner_delta, field_name="current_owner_delta")
                if current_owner_delta is not None
                else None
            ),
            claim_ref=str(request.get("claim_ref") or ""),
            data_ref=str(request.get("data_ref") or ""),
            paper_target=str(request.get("paper_target") or ""),
            intent=str(request.get("intent") or ""),
            figure_request=(
                _mapping_value(figure_request, field_name="figure_request")
                if figure_request is not None
                else None
            ),
            max_recommendations=_optional_int_value(request.get("max_recommendations")) or 5,
            check_runtime_dependencies=_bool_value(request.get("check_runtime_dependencies"), default=True),
        )
    if command == "display-pack-figure-plan":
        return display_pack_agent.display_pack_figure_plan(
            repo_root=repo_root if repo_root is not None else None,
            paper_root=paper_root if paper_root is not None else None,
            figure_request=_mapping_value(request.get("figure_request"), field_name="figure_request"),
            max_recommendations=_optional_int_value(request.get("max_recommendations")) or 5,
        )
    if command == "display-pack-preflight":
        figure_request = request.get("figure_request")
        return display_pack_agent.display_pack_preflight(
            repo_root=repo_root if repo_root is not None else None,
            paper_root=paper_root if paper_root is not None else None,
            template_id=_optional_text(request.get("template_id")),
            figure_request=(
                _mapping_value(figure_request, field_name="figure_request")
                if figure_request is not None
                else None
            ),
            check_runtime_dependencies=_bool_value(request.get("check_runtime_dependencies"), default=True),
        )
    if command == "display-pack-render":
        figure_request = request.get("figure_request")
        visual_audit_review = request.get("visual_audit_review")
        return display_pack_agent.display_pack_render(
            repo_root=repo_root if repo_root is not None else None,
            paper_root=Path(str(paper_root)).expanduser(),
            figure_request=(
                _mapping_value(figure_request, field_name="figure_request")
                if figure_request is not None
                else None
            ),
            visual_audit_review=(
                _mapping_value(visual_audit_review, field_name="visual_audit_review")
                if visual_audit_review is not None
                else None
            ),
        )
    raise ValueError(f"不支持的 display pack domain entry command: {command}")


def _dispatch_research_integrity_command(command: str, request: Mapping[str, Any]) -> dict[str, Any]:
    if command == "research-integrity-gate-input":
        gate_bundle = import_module("med_autoscience.research_integrity.gate_bundle")
        return gate_bundle.build_research_integrity_gate_input_bundle(
            **_research_integrity_gate_input_kwargs(request),
        )
    if command == "research-integrity-reference-verification":
        builder = _load_research_integrity_reference_verification_builder()
        payload = builder(payload=_research_integrity_reference_verification_payload(request))
        return _with_research_integrity_forbidden_authority_boundary(command, payload)
    if command == "research-integrity-review-publication-gate-stage-hook":
        stage_hooks = import_module("med_autoscience.research_integrity.stage_hooks")
        payload = stage_hooks.build_review_publication_gate_stage_hook_payload(
            payload=_research_integrity_reference_verification_payload(request),
        )
        return _with_research_integrity_forbidden_authority_boundary(command, payload)
    raise ValueError(f"不支持的 research integrity domain entry command: {command}")


def _load_research_integrity_reference_verification_builder() -> Callable[..., dict[str, Any]]:
    module = import_module("med_autoscience.research_integrity.reference_verification")
    builder = getattr(module, "build_reference_verification_payload")
    if not callable(builder):
        raise TypeError("research integrity reference verification builder 必须可调用。")
    return builder


def _research_integrity_reference_verification_payload(request: Mapping[str, Any]) -> dict[str, Any]:
    raw_payload = request.get("payload")
    if raw_payload is None:
        payload: dict[str, Any] = {}
    elif isinstance(raw_payload, Mapping):
        payload = dict(raw_payload)
    else:
        raise ValueError("research integrity reference verification `payload` 必须是 mapping。")
    for field_name, value in request.items():
        if field_name not in {"command", "payload"}:
            payload[field_name] = value
    return payload


def _with_research_integrity_forbidden_authority_boundary(
    command: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise TypeError(f"domain entry `{command}` 返回值必须是 mapping。")
    boundary = dict(payload.get("authority_boundary") or {})
    for flag in RESEARCH_INTEGRITY_FORBIDDEN_AUTHORITY_FLAGS:
        value = boundary.get(flag, False)
        if value is not False:
            raise ValueError(f"domain entry `{command}` cannot set authority flag `{flag}`.")
        boundary[flag] = False
    return {**payload, "authority_boundary": boundary}


def _research_integrity_gate_input_payload(request: Mapping[str, Any]) -> dict[str, Any]:
    raw_payload = request.get("payload")
    if raw_payload is None:
        payload: dict[str, Any] = {}
    elif isinstance(raw_payload, Mapping):
        payload = dict(raw_payload)
    else:
        raise ValueError("research integrity domain entry `payload` 必须是 mapping。")
    for field_name in (
        "reference_checks",
        "reference",
        "references",
        "claim_spans",
        "claim",
        "claims",
        "citation_refs",
        "evidence_refs",
        "reference_attestation_refs",
        "manuscript_sections",
        "manuscript",
        "numeric_facts",
        "display_facts",
        "provider_evidence",
        "reference_attestations",
        "display_to_claim_map",
        "reporting_guideline_expectations",
        "reporting_checklist_expectations",
    ):
        if field_name in request:
            payload[field_name] = request[field_name]
    return payload


def _research_integrity_gate_input_kwargs(request: Mapping[str, Any]) -> dict[str, Any]:
    payload = _research_integrity_gate_input_payload(request)
    manuscript = _optional_mapping_value(payload.get("manuscript"))
    return {
        "reference_checks": _research_integrity_reference_checks(payload),
        "claim_spans": _mapping_sequence(_first_present(payload, "claim_spans", "claims", "claim"), "claim_spans"),
        "citation_refs": _ref_sequence(payload.get("citation_refs"), "citation_refs"),
        "evidence_refs": _ref_sequence(payload.get("evidence_refs"), "evidence_refs"),
        "reference_attestation_refs": _ref_sequence(
            _first_present(payload, "reference_attestation_refs", "reference_attestations"),
            "reference_attestation_refs",
        ),
        "manuscript_sections": _research_integrity_manuscript_sections(payload),
        "numeric_facts": _first_present(payload, "numeric_facts", mapping=manuscript),
        "display_facts": _first_present(payload, "display_facts", "display_to_claim_map", mapping=manuscript),
        "reporting_checklist_expectations": _first_present(
            payload,
            "reporting_checklist_expectations",
            "reporting_guideline_expectations",
            mapping=manuscript,
        ),
    }


def _research_integrity_reference_checks(payload: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    if "reference_checks" in payload:
        return _mapping_sequence(payload.get("reference_checks"), "reference_checks")
    references = (
        _mapping_sequence(payload.get("references"), "references")
        + _mapping_sequence(payload.get("reference"), "reference")
    )
    if not references:
        return ()
    shared_evidence = _mapping_sequence(payload.get("provider_evidence"), "provider_evidence")
    checks: list[Mapping[str, Any]] = []
    for reference in references:
        reference_evidence = _first_present(reference, "provider_evidence", "evidence")
        evidence = _mapping_sequence(
            reference_evidence if reference_evidence is not None else shared_evidence,
            "provider_evidence",
        )
        checks.append({"reference": reference, "provider_evidence": list(evidence)})
    return tuple(checks)


def _research_integrity_manuscript_sections(payload: Mapping[str, Any]) -> Mapping[str, Any] | None:
    if "manuscript_sections" in payload:
        return _optional_research_integrity_mapping(payload.get("manuscript_sections"), "manuscript_sections")
    manuscript = _optional_mapping_value(payload.get("manuscript"))
    if manuscript is None:
        return None
    sections = manuscript.get("sections")
    if sections is not None:
        return _optional_research_integrity_mapping(sections, "manuscript.sections")
    return manuscript


def _first_present(
    payload: Mapping[str, Any],
    *field_names: str,
    mapping: Mapping[str, Any] | None = None,
) -> Any:
    for field_name in field_names:
        if field_name in payload:
            return payload[field_name]
    if mapping is not None:
        for field_name in field_names:
            if field_name in mapping:
                return mapping[field_name]
    return None


def _mapping_sequence(value: Any, field_name: str) -> tuple[Mapping[str, Any], ...]:
    if value is None:
        return ()
    if isinstance(value, Mapping):
        return (value,)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ValueError(f"research integrity domain entry `{field_name}` 必须是 mapping 或 mapping list。")
    items: list[Mapping[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError(f"research integrity domain entry `{field_name}` 只能包含 mapping。")
        items.append(item)
    return tuple(items)


def _ref_sequence(value: Any, field_name: str) -> tuple[Mapping[str, Any] | str, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, Mapping)):
        return (value,)
    if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray)):
        raise ValueError(f"research integrity domain entry `{field_name}` 必须是 ref、mapping 或 list。")
    items: list[Mapping[str, Any] | str] = []
    for item in value:
        if not isinstance(item, (str, Mapping)):
            raise ValueError(f"research integrity domain entry `{field_name}` 只能包含 ref 或 mapping。")
        items.append(item)
    return tuple(items)


def _optional_research_integrity_mapping(value: Any, field_name: str) -> Mapping[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError(f"research integrity domain entry `{field_name}` 必须是 mapping。")
    return value


def _dispatch_domain_handler(command: str, request: Mapping[str, Any]) -> dict[str, Any]:
    if command == "domain-handler-export":
        from med_autoscience.controllers.owner_route_handoff.domain_handler_export import (
            export_family_domain_handler,
        )

        profile_ref = Path(str(request["profile_ref"])).expanduser().resolve()
        return export_family_domain_handler(
            profile=load_profile(profile_ref),
            profile_ref=profile_ref,
            opl_production_proof_ref=_optional_text(request.get("opl_production_proof_ref")),
            study_ids=tuple(str(item) for item in _sequence_value(request.get("study_ids"))),
        )

    task_path = Path(str(request["task_ref"])).expanduser().resolve()
    task = json.loads(task_path.read_text(encoding="utf-8"))
    if not isinstance(task, Mapping):
        raise ValueError("domain handler task 必须是 JSON object。")
    from med_autoscience.paper_mission_domain import (
        DOMAIN_ROUTE_START_OR_RESUME_TASK_KIND,
        paper_mission_domain_handler_dispatch_receipt,
    )

    if task.get("task_kind") == DOMAIN_ROUTE_START_OR_RESUME_TASK_KIND:
        return paper_mission_domain_handler_dispatch_receipt(
            task=task,
            task_path=task_path,
            load_profile=load_profile,
        )

    from med_autoscience.controllers.owner_route_handoff.dispatch_orchestration import dispatch_family_domain_handler_task

    return dispatch_family_domain_handler_task(task_path=task_path)


def _dispatch_domain_capability(command: str, request: Mapping[str, Any]) -> dict[str, Any]:
    if command == "study-state-matrix":
        from med_autoscience.controllers import domain_status_projection, study_state_matrix

        profile_ref = Path(str(request["profile_ref"])).expanduser().resolve()
        return study_state_matrix.build_study_state_matrix(
            profile=load_profile(profile_ref),
            domain_status_projection=domain_status_projection,
            study_ids=tuple(str(item) for item in _sequence_value(request.get("study_ids"))),
            entry_mode=_optional_text(request.get("entry_mode")),
        )
    if command == "export-inspection-package":
        from med_autoscience.controllers.submission_inspection_export import export_inspection_package

        profile_ref = Path(str(request["profile_ref"])).expanduser().resolve()
        return export_inspection_package(
            profile=load_profile(profile_ref),
            profile_ref=profile_ref,
            study_id=str(request["study_id"]),
            publication_profile=_optional_text(request.get("publication_profile")),
            force_materialize=_bool_value(request.get("force_materialize")),
            source="domain-entry",
        )
    if command == "publication-aftercare-plan":
        from med_autoscience.controllers.publication_aftercare import build_publication_aftercare_plan

        return build_publication_aftercare_plan(
            study_root=Path(str(request["study_root"])),
            quest_root=(Path(str(request["quest_root"])) if request.get("quest_root") else None),
        )
    if command == "delivery-authority-backfill-apply":
        from med_autoscience.controllers.delivery_authority_backfill_apply import run_backfill_apply

        return run_backfill_apply(
            workspace_roots=tuple(
                Path(str(item)).expanduser().resolve()
                for item in _sequence_value(request.get("workspace_roots"))
            ),
            apply=_bool_value(request.get("apply")),
            authority_snapshot=_optional_mapping_value(request.get("authority_snapshot")),
        )
    if command == "external-learning-adoption-closure":
        from med_autoscience.external_learning_adoption_closure import build_external_learning_adoption_closure

        return build_external_learning_adoption_closure()
    if command == "scientific-capability-registry":
        return _dispatch_scientific_capability(request)
    from med_autoscience.controllers import mainline_status

    if command == "mainline-status":
        return mainline_status.read_mainline_status()
    return mainline_status.read_mainline_phase_status(
        _optional_text(request.get("selector")) or "current"
    )


def _dispatch_scientific_capability(request: Mapping[str, Any]) -> dict[str, Any]:
    from med_autoscience import scientific_capability_registry as registry

    mode = str(request["mode"])
    if mode == "summary":
        return registry.build_scientific_capability_registry_summary()
    if mode == "inventory":
        return registry.build_scientific_capability_registry_inventory()
    if mode == "index":
        return registry.build_scientific_capability_registry()
    current_owner_delta = _optional_mapping_value(request.get("current_owner_delta"))
    if mode == "resolve":
        return registry.resolve_scientific_capabilities(current_owner_delta=current_owner_delta)
    if mode != "invoke":
        raise ValueError(f"不支持的 scientific capability mode: {mode}")
    capability_id = _optional_text(request.get("capability_id"))
    if not capability_id:
        raise ValueError("scientific capability invoke 缺少 capability_id。")
    return registry.invoke_scientific_capability(
        capability_id=capability_id,
        current_owner_delta=current_owner_delta,
        study_root=_optional_text(request.get("study_root")),
        apply=_bool_value(request.get("apply")),
        payload=_optional_mapping_value(request.get("payload")),
    )
