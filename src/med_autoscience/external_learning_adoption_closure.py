from __future__ import annotations

import json
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, Mapping

from med_autoscience.ars_learning_projection import build_ars_learning_projection
from med_autoscience.autosci_learning_projection import build_autosci_learning_projection
from med_autoscience.evo_scientist_learning_projection import (
    build_evo_scientist_learning_projection,
)
from med_autoscience.progress_first_external_learning_contract import (
    build_ark_progress_first_learning_contract,
)


SURFACE_KIND = "mas_external_learning_adoption_closure"
SIDECAR_SURFACE_KIND = "mas_external_learning_sidecar_result"
SIDECAR_ACTION_TYPE = "run_external_learning_sidecar"
SIDECAR_OWNER = "external_learning_sidecar"
SIDECAR_CALLABLE_SURFACE = "external_learning_sidecar.run_external_learning_sidecar"
REQUEST_RELATIVE_PATH = Path("artifacts/supervision/requests/external_learning_sidecar/latest.json")
SIDECAR_RESULT_RELATIVE_PATH = Path("artifacts/advisory/external_learning_sidecar/latest.json")
SCHEMA_VERSION = 1
FORBIDDEN_WRITES = (
    "artifacts/publication_eval/latest.json",
    "artifacts/controller_decisions/latest.json",
    "paper/**",
    "paper/submission_minimal/**",
    "manuscript/current_package/**",
    "submission_package/**",
    "current_package/**",
    "memory/**/body",
)
ALLOWED_WRITES = (
    REQUEST_RELATIVE_PATH.as_posix(),
    SIDECAR_RESULT_RELATIVE_PATH.as_posix(),
)
SIDECAR_WORKER_REGISTRY: Mapping[str, tuple[str, str]] = {
    "paperspine": (
        "med_autoscience.external_learning_authoring_advisory",
        "build_paperspine_manuscript_advisory",
    ),
    "paperorchestra": (
        "med_autoscience.external_learning_authoring_advisory",
        "build_paperorchestra_authoring_advisory",
    ),
    "academic_research_skills": (
        "med_autoscience.external_learning_review_advisory",
        "build_ars_claim_support_advisory",
    ),
    "aris": (
        "med_autoscience.external_learning_review_advisory",
        "build_aris_review_import_advisory",
    ),
    "ark_progress_first": (
        "med_autoscience.external_learning_progress_workers",
        "build_ark_progress_worker_advisory",
    ),
    "autosci_omegawiki": (
        "med_autoscience.external_learning_progress_workers",
        "build_autosci_source_experiment_advisory",
    ),
}


def build_external_learning_adoption_closure() -> dict[str, Any]:
    ars = build_ars_learning_projection()
    autosci = build_autosci_learning_projection()
    evo = build_evo_scientist_learning_projection()
    ark = build_ark_progress_first_learning_contract()
    frameworks = [
        _framework(
            framework_id="co_scientist",
            source_project="Google / Nature Co-Scientist",
            source_refs=[
                "https://www.nature.com/articles/s41586-026-10644-y",
                "https://arxiv.org/abs/2502.18864",
                "docs/references/mainline/co_scientist_hypothesis_portfolio_intake.md",
                "docs/runtime/designs/coscientist_stage_route_restructure.md",
            ],
            absorbed_pattern_ids=[
                "hypothesis_portfolio",
                "evidence_pack",
                "advisory_ranking",
                "triggered_meta_review",
                "progress_first_enhancement_layer",
            ],
            local_execution_state="semantic_pack_and_route_contract_landed",
            closure_status="owner_surface_landed",
            owner_surface="stage_route_contract_and_hypothesis_portfolio_pack",
            worker_or_executor_landing="ordinary_owner_actions_consume_portfolio_refs; sidecar advisory refs available through run_external_learning_sidecar",
            missing_landing_work=[
                "scale real-study hypothesis portfolio receipts across all active stages",
                "materialize per-study portfolio candidate refs when a route owner requests them",
            ],
            next_landing_path="extend current owner action input refs, not a new Co-Scientist runtime",
        ),
        _framework(
            framework_id="nature_skills",
            source_project="Nature-skills style academic workflow packs",
            source_refs=[
                "docs/references/mainline/nature_skills_learning_intake.md",
                "med_autoscience.stage_quality_contract.build_stage_quality_pack_contract",
            ],
            absorbed_pattern_ids=[
                "reviewer_response_edge_case_contract",
                "restricted_access_fair_metadata_contract",
                "strict_citation_scope_and_export_contract",
                "figure_backend_export_qa_contract",
                "manuscript_argument_failure_mode",
                "paper_reader_source_map",
                "pptx_asset_manifest_package_qa",
            ],
            local_execution_state="stage_quality_pack_prompt_and_tests_landed",
            closure_status="owner_surface_landed",
            owner_surface="stage_quality_pack_contract_and_ai_reviewer_quality_gate",
            worker_or_executor_landing="AI reviewer and stage owner actions consume quality-pack refs; no external skill runner is required",
            missing_landing_work=[
                "continue live paper-line evidence tail with owner receipts and artifact refs",
            ],
            next_landing_path="add missing ref family to quality pack or owner request only when current route needs it",
        ),
        _framework_from_projection(
            framework_id="academic_research_skills",
            source_project="Imbad0202/academic-research-skills",
            projection=ars,
            closure_status="sidecar_or_worker_landed",
            owner_surface="medical_material_passport_and_ars_learning_projection_and_sidecar_advisory",
            worker_or_executor_landing=(
                "medical material passport and source adapter rejection log are landed; "
                "refs-only claim-support advisory worker is "
                "med_autoscience.external_learning_review_advisory."
                "build_ars_claim_support_advisory; full owner-receipted claim-support "
                "audit is still not a separate owner action"
            ),
            missing_landing_work=[
                "claim-citation support audit needs owner receipt before being counted as study progress",
                "data-access oversight metadata needs live owner receipts before it can be counted as study progress",
            ],
            next_landing_path="route through existing source/material passport owner refs or run_external_learning_sidecar advisory worker output",
        ),
        _framework_from_projection(
            framework_id="autosci_omegawiki",
            source_project="skyllwt/AutoSci / OmegaWiki",
            projection=autosci,
            closure_status="sidecar_or_worker_landed",
            owner_surface="stage_quality_pack_contract_autosci_learning_projection_and_sidecar_advisory",
            extra_source_refs=[
                "med_autoscience.external_learning_progress_workers."
                "build_autosci_source_experiment_advisory",
            ],
            worker_or_executor_landing=(
                "research lifecycle, source discovery, reviewer verdict, and artifact QA "
                "patterns are consumable as MAS refs and quality-pack contracts; refs-only "
                "source/experiment advisory worker is "
                "med_autoscience.external_learning_progress_workers."
                "build_autosci_source_experiment_advisory"
            ),
            missing_landing_work=[
                "real source discovery and experiment lifecycle attempts still need owner receipts per study",
            ],
            next_landing_path="bind source discovery or experiment lifecycle refs to current owner work units",
        ),
        _framework_from_projection(
            framework_id="evo_scientist_evoskills",
            source_project="EvoScientist / EvoSkills",
            projection=evo,
            closure_status="sidecar_execution_slot_landed",
            owner_surface="evo_scientist_progress_accelerator_contract_and_external_learning_sidecar",
            worker_or_executor_landing="nonblocking current-owner-following sidecar action is declared by run_external_learning_sidecar",
            missing_landing_work=[
                "scale richer tool-affordance, failed-path, and observation-memory candidate generation under the same sidecar contract",
            ],
            next_landing_path="implementation scaleout only; do not reopen learning-plan status",
        ),
        _framework(
            framework_id="ark_progress_first",
            source_project="kaust-ark/ARK",
            source_refs=[
                "med_autoscience.progress_first_external_learning_contract.build_ark_progress_first_learning_contract",
                "med_autoscience.external_learning_progress_workers.build_ark_progress_worker_advisory",
            ],
            absorbed_pattern_ids=list(_mapping(ark).get("outputs") or []),
            local_execution_state="refs_only_sidecar_worker_landed",
            closure_status="sidecar_or_worker_landed",
            owner_surface="progress_first_external_learning_contract_and_sidecar_advisory",
            worker_or_executor_landing=(
                "contracts exist for micro canary, hard human decision request, "
                "real-run closeout, visual QA, no-progress evidence, and citation "
                "lifecycle queue; refs-only advisory worker is "
                "med_autoscience.external_learning_progress_workers."
                "build_ark_progress_worker_advisory"
            ),
            missing_landing_work=[
                "owner-receipted micro-study canary evidence",
                "operator preview harness evidence",
                "executor real-run closeout materializer receipt",
                "citation lifecycle queue owner action receipt",
            ],
            next_landing_path="emit refs-only candidates through run_external_learning_sidecar; promote to owner receipt only when a current progress blocker requires it",
        ),
        _framework(
            framework_id="aris",
            source_project="wanshuiyin/Auto-claude-code-research-in-sleep",
            source_refs=[
                "docs/history/superpowers/specs/2026-03-29-aris-sidecar-design.md",
                "docs/runtime/control/controllers.md#publication-aftercare-plan",
                "med_autoscience.controllers.publication_aftercare.build_publication_aftercare_plan",
                "https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep",
            ],
            absorbed_pattern_ids=[
                "cross_model_review_loop",
                "research_pipeline",
                "experiment_queue",
                "claim_assurance_map",
                "research_wiki_memory",
            ],
            local_execution_state="history_aftercare_projection_and_sidecar_worker_landed",
            closure_status="sidecar_or_worker_landed",
            owner_surface="publication_aftercare_plan_refs_only_projection_and_sidecar_advisory",
            worker_or_executor_landing=(
                "publication aftercare can expose ARIS handoff refs; refs-only review "
                "import advisory worker is med_autoscience.external_learning_review_advisory."
                "build_aris_review_import_advisory; MAS has not landed an ARIS provider "
                "result import path"
            ),
            missing_landing_work=[
                "owner-receipted ARIS input contract action",
                "body-free ARIS result import owner receipt",
                "cross-model reviewer receipt projection backed by live reviewer invocation",
            ],
            next_landing_path="project advisory refs through run_external_learning_sidecar and import only refs with owner receipt or typed blocker",
        ),
        _framework(
            framework_id="paperspine",
            source_project="WUBING2023/PaperSpine",
            source_refs=[
                "https://github.com/WUBING2023/PaperSpine",
                "med_autoscience.external_learning_authoring_advisory.build_paperspine_manuscript_advisory",
            ],
            absorbed_pattern_ids=[
                "motivation_spine",
                "writing_rationale_matrix",
                "evidence_blueprint",
                "latex_safe_audit",
            ],
            local_execution_state="refs_only_sidecar_worker_landed",
            closure_status="sidecar_or_worker_landed",
            owner_surface="paperspine_manuscript_authoring_sidecar_advisory",
            worker_or_executor_landing=(
                "refs-only manuscript authoring advisory worker is "
                "med_autoscience.external_learning_authoring_advisory."
                "build_paperspine_manuscript_advisory; it does not write paper body, "
                "publication eval, package artifacts, or quality verdicts"
            ),
            missing_landing_work=[
                "owner-consumed motivation-spine refs in manuscript authoring work units",
                "writing-rationale matrix owner receipt or typed blocker",
                "LaTeX-safe audit owner action receipt for finalize/package stages",
            ],
            next_landing_path="keep as manuscript-authoring advisory refs, never as paper-writing authority or external runner",
        ),
        _framework(
            framework_id="paperorchestra",
            source_project="Ar9av/PaperOrchestra",
            source_refs=[
                "docs/history/program/paper_orchestra_learning_intake_2026_05_02.md",
                "docs/history/program/open_auto_research_learning_intake_2026_05_04.md",
                "med_autoscience.external_learning_authoring_advisory.build_paperorchestra_authoring_advisory",
            ],
            absorbed_pattern_ids=[
                "authoring_dag",
                "outline_plot_ref",
                "literature_section_ref",
                "autorater_ref",
            ],
            local_execution_state="refs_only_sidecar_worker_landed",
            closure_status="sidecar_or_worker_landed",
            owner_surface="paperorchestra_authoring_sidecar_advisory",
            worker_or_executor_landing=(
                "refs-only authoring advisory worker is "
                "med_autoscience.external_learning_authoring_advisory."
                "build_paperorchestra_authoring_advisory; it does not introduce a "
                "PaperOrchestra runtime, paper generator, publication owner, or autorater gate"
            ),
            missing_landing_work=[
                "owner-consumed authoring DAG refs in manuscript work units",
                "medical-quality-specific autorater calibration evidence",
                "live reviewer receipt before any quality claim",
            ],
            next_landing_path="keep as authoring DAG and evaluator advisory refs under run_external_learning_sidecar",
        ),
        _framework(
            framework_id="open_auto_research",
            source_project="PaperBench / PaperQA2 / STORM / Open Deep Research family intake",
            source_refs=[
                "docs/history/program/open_auto_research_learning_intake_2026_05_04.md",
                "med_autoscience.controllers.open_auto_research_projection.build_open_auto_research_projection",
            ],
            absorbed_pattern_ids=[
                "literature_evidence_graph",
                "evaluation_rubric_tree",
                "runtime_trajectory_proof",
                "candidate_path_graph",
            ],
            local_execution_state="read_model_and_soak_landed",
            closure_status="read_model_landed",
            owner_surface="open_auto_research_projection_and_open_auto_research_soak",
            worker_or_executor_landing="controller-authorized soak can materialize OAR source artifacts; read entrypoints remain non-materializing",
            missing_landing_work=[
                "do not count OAR soak as publication readiness without AI reviewer/publication gate",
            ],
            next_landing_path="keep as read-only readiness accelerator and controller-authorized soak",
        ),
    ]
    counts = _counts(frameworks)
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": "adoption_closure_active",
        "owner": "MedAutoScience",
        "purpose": (
            "Close the gap between external-framework learning records and actual MAS execution surfaces."
        ),
        "machine_boundary": (
            "This surface classifies adoption and sidecar execution slots. It cannot authorize study truth, "
            "publication quality, submission readiness, artifact mutation, memory accept/reject, or stage closure."
        ),
        "authority_boundary": _closure_authority_boundary(),
        "frameworks": frameworks,
        "counts": counts,
        "sidecar_execution_contract": _sidecar_execution_contract(),
        "progress_first_friction_guard": {
            "mainline_waits_for_sidecar": False,
            "sidecar_missing_blocks_dispatch": False,
            "sidecar_failure_blocks_current_owner_action": False,
            "sidecar_budget_exhaustion_blocks_owner_action": False,
            "owner_policy_wins": True,
            "advisory_refs_count_as_paper_progress": False,
        },
        "completion_definition": {
            "contract_only_is_not_landed": True,
            "landed_requires_execution_slot_or_owner_surface": True,
            "worker_or_executor_must_declare_allowed_writes": True,
            "worker_or_executor_must_preserve_forbidden_authority": True,
            "tests_must_cover_nonblocking_refs_only_behavior": True,
        },
    }


def run_external_learning_sidecar(
    *,
    study_root: Path,
    dispatch: Mapping[str, Any] | None = None,
    apply: bool = False,
) -> dict[str, Any]:
    root = Path(study_root).expanduser().resolve()
    payload = _sidecar_payload(study_root=root, dispatch=dispatch or {}, apply=apply)
    if apply:
        result_path = root / SIDECAR_RESULT_RELATIVE_PATH
        result_path.parent.mkdir(parents=True, exist_ok=True)
        payload["result_path"] = str(result_path)
        result_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return payload


def _sidecar_payload(*, study_root: Path, dispatch: Mapping[str, Any], apply: bool) -> dict[str, Any]:
    closure = build_external_learning_adoption_closure()
    action_type = _dispatch_text(dispatch, "action_type") or "unknown_action"
    candidates = _advisory_candidates(action_type=action_type, closure=closure)
    return {
        "surface_kind": SIDECAR_SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": "executed" if apply else "dry_run",
        "study_id": study_root.name,
        "study_root_ref": str(study_root),
        "result_path": None,
        "refs_only": True,
        "body_included": False,
        "advisory_only": True,
        "mainline_waits_for_sidecar": False,
        "can_block_current_owner_action": False,
        "current_owner_action": _current_owner_action(dispatch),
        "advisory_candidates": candidates,
        "advisory_worker_results": _advisory_worker_results(
            action_type=action_type,
            dispatch=dispatch,
            candidates=candidates,
        ),
        "closure_counts": closure["counts"],
        "closure_ref": (
            "med_autoscience.external_learning_adoption_closure."
            "build_external_learning_adoption_closure"
        ),
        "authority_boundary": _sidecar_authority_boundary(),
        "forbidden_writes": list(FORBIDDEN_WRITES),
        "allowed_writes": [SIDECAR_RESULT_RELATIVE_PATH.as_posix()],
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def _framework_from_projection(
    *,
    framework_id: str,
    source_project: str,
    projection: Mapping[str, Any],
    closure_status: str,
    owner_surface: str,
    worker_or_executor_landing: str,
    missing_landing_work: list[str],
    next_landing_path: str,
    extra_source_refs: list[str | None] | None = None,
) -> dict[str, Any]:
    source = _mapping(projection.get("source_snapshot"))
    return _framework(
        framework_id=framework_id,
        source_project=source_project,
        source_refs=[
            _text(source.get("repository")),
            _text(source.get("intake_doc_ref")),
            _text(projection.get("contract_ref")),
            _text(projection.get("progress_accelerator_contract_ref")),
            *(extra_source_refs or []),
        ],
        absorbed_pattern_ids=[
            _text(pattern.get("pattern_id"))
            for pattern in _list(projection.get("absorbed_patterns"))
            if isinstance(pattern, Mapping)
        ],
        local_execution_state=_text(projection.get("status")) or closure_status,
        closure_status=closure_status,
        owner_surface=owner_surface,
        worker_or_executor_landing=worker_or_executor_landing,
        missing_landing_work=missing_landing_work,
        next_landing_path=next_landing_path,
    )


def _framework(
    *,
    framework_id: str,
    source_project: str,
    source_refs: list[str | None],
    absorbed_pattern_ids: list[str | None],
    local_execution_state: str,
    closure_status: str,
    owner_surface: str,
    worker_or_executor_landing: str,
    missing_landing_work: list[str],
    next_landing_path: str,
) -> dict[str, Any]:
    return {
        "framework_id": framework_id,
        "source_project": source_project,
        "source_refs": [ref for ref in source_refs if ref],
        "dependency_introduced": False,
        "absorbed_pattern_ids": [item for item in absorbed_pattern_ids if item],
        "local_execution_state": local_execution_state,
        "closure_status": closure_status,
        "owner_surface": owner_surface,
        "worker_or_executor_landing": worker_or_executor_landing,
        "missing_landing_work": missing_landing_work,
        "next_landing_path": next_landing_path,
        "friction_policy": {
            "can_block_current_owner_action": False,
            "mainline_waits_for_framework": False,
            "external_runtime_dependency": False,
            "owner_policy_wins": True,
        },
        "authority_boundary": {
            "can_write_domain_truth": False,
            "can_write_publication_eval": False,
            "can_write_controller_decisions": False,
            "can_write_paper_or_package": False,
            "can_authorize_publication_quality": False,
            "can_authorize_submission_readiness": False,
            "can_authorize_artifact_authority": False,
            "can_close_stage": False,
        },
    }


def _sidecar_execution_contract() -> dict[str, Any]:
    return {
        "action_type": SIDECAR_ACTION_TYPE,
        "owner": SIDECAR_OWNER,
        "callable_surface": SIDECAR_CALLABLE_SURFACE,
        "execution_model": "nonblocking_current_owner_following_sidecar",
        "allowed_writes": list(ALLOWED_WRITES),
        "forbidden_writes": list(FORBIDDEN_WRITES),
        "required_inputs": [
            "current owner action dispatch or owner route",
            "external learning adoption closure",
        ],
        "required_outputs": [
            SIDECAR_RESULT_RELATIVE_PATH.as_posix(),
            "refs-only advisory candidates",
            "refs-only advisory worker results",
        ],
        "mainline_waits_for_sidecar": False,
        "missing_sidecar_blocks_dispatch": False,
        "failure_policy": "record diagnostic if possible and continue current owner action",
        "authority_boundary": _sidecar_authority_boundary(),
    }


def _closure_authority_boundary() -> dict[str, Any]:
    return {
        "source_project_role": "external_pattern_source_only",
        "opl_owner": "one-person-lab",
        "mas_domain_truth_owner": "MedAutoScience",
        "can_write_domain_truth": False,
        "can_write_publication_eval": False,
        "can_write_controller_decisions": False,
        "can_write_paper_or_package": False,
        "can_authorize_publication_quality": False,
        "can_authorize_submission_readiness": False,
        "can_authorize_artifact_authority": False,
        "can_close_stage": False,
    }


def _sidecar_authority_boundary() -> dict[str, Any]:
    return {
        "surface_role": "refs_only_advisory_progress_accelerator",
        "can_write_domain_truth": False,
        "can_write_publication_eval": False,
        "can_write_controller_decisions": False,
        "can_write_paper_or_package": False,
        "can_write_memory_body": False,
        "can_authorize_owner_action": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_quality": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_submission_readiness": False,
        "can_authorize_artifact_authority": False,
        "can_close_stage": False,
    }


def _current_owner_action(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    owner_route = _mapping(dispatch.get("owner_route")) or _mapping(
        _mapping(dispatch.get("prompt_contract")).get("owner_route")
    )
    refs = _mapping(dispatch.get("refs"))
    return {
        "action_type": _dispatch_text(dispatch, "action_type"),
        "action_id": _dispatch_text(dispatch, "action_id"),
        "owner": _text(owner_route.get("owner")) or _dispatch_text(dispatch, "owner"),
        "work_unit_id": _text(owner_route.get("work_unit_id")) or _text(owner_route.get("unit_id")),
        "work_unit_fingerprint": _text(owner_route.get("work_unit_fingerprint")),
        "dispatch_path": _text(refs.get("dispatch_path")),
    }


def _advisory_candidates(*, action_type: str, closure: Mapping[str, Any]) -> list[dict[str, Any]]:
    frameworks = {
        item["framework_id"]: item
        for item in _list(closure.get("frameworks"))
        if isinstance(item, Mapping) and _text(item.get("framework_id")) is not None
    }
    framework_ids = {
        "return_to_ai_reviewer_workflow": ["co_scientist", "nature_skills", "autosci_omegawiki", "aris"],
        "run_quality_repair_batch": [
            "nature_skills",
            "paperspine",
            "paperorchestra",
            "co_scientist",
            "academic_research_skills",
        ],
        "unit_harmonized_external_validation_rerun": ["aris", "ark_progress_first", "autosci_omegawiki"],
        "run_gate_clearing_batch": ["nature_skills", "ark_progress_first", "open_auto_research"],
    }.get(
        action_type,
        ["evo_scientist_evoskills", "co_scientist", "academic_research_skills"],
    )
    candidates: list[dict[str, Any]] = []
    for framework_id in framework_ids:
        framework = frameworks.get(framework_id)
        if framework is None:
            continue
        candidates.append(
            {
                "candidate_ref": f"external-learning:{framework_id}:{action_type}",
                "framework_id": framework_id,
                "role": _candidate_role(framework_id=framework_id, action_type=action_type),
                "closure_status": framework.get("closure_status"),
                "owner_surface": framework.get("owner_surface"),
                "next_landing_path": framework.get("next_landing_path"),
                "can_block_current_owner_action": False,
                "body_included": False,
            }
        )
    gap_candidates = [
        item
        for item in _list(closure.get("frameworks"))
        if isinstance(item, Mapping)
        and _text(item.get("closure_status"))
        in {"contract_only_gap", "history_only_gap", "not_landed_gap"}
    ]
    if gap_candidates:
        candidates.append(
            {
                "candidate_ref": f"external-learning:closure-gap:{action_type}",
                "role": "operator_gap_visibility",
                "gap_framework_ids": [item["framework_id"] for item in gap_candidates],
                "can_block_current_owner_action": False,
                "body_included": False,
            }
        )
    return candidates


def _advisory_worker_results(
    *,
    action_type: str,
    dispatch: Mapping[str, Any],
    candidates: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for candidate in candidates:
        framework_id = _text(candidate.get("framework_id"))
        if framework_id is None or framework_id in seen:
            continue
        seen.add(framework_id)
        if framework_id not in SIDECAR_WORKER_REGISTRY:
            continue
        results.append(
            _normalize_advisory_worker_result(
                framework_id=framework_id,
                action_type=action_type,
                result=_run_registered_advisory_worker(
                    framework_id=framework_id,
                    action_type=action_type,
                    dispatch=dispatch,
                ),
            )
        )
    return results


def _run_registered_advisory_worker(
    *,
    framework_id: str,
    action_type: str,
    dispatch: Mapping[str, Any],
) -> dict[str, Any]:
    module_name, builder_name = SIDECAR_WORKER_REGISTRY[framework_id]
    try:
        builder = _load_advisory_builder(module_name=module_name, builder_name=builder_name)
    except (AttributeError, ImportError, ModuleNotFoundError) as exc:
        return _worker_unavailable_result(
            framework_id=framework_id,
            action_type=action_type,
            reason=type(exc).__name__,
        )
    try:
        value = builder(dispatch)
    except Exception as exc:  # pragma: no cover - defensive fail-open boundary.
        return _worker_unavailable_result(
            framework_id=framework_id,
            action_type=action_type,
            reason=type(exc).__name__,
        )
    return _mapping(value)


def _load_advisory_builder(
    *, module_name: str, builder_name: str
) -> Callable[[Mapping[str, Any]], Any]:
    builder = getattr(import_module(module_name), builder_name)
    if not callable(builder):
        raise AttributeError(builder_name)
    return builder


def _worker_unavailable_result(
    *,
    framework_id: str,
    action_type: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "surface_kind": "mas_external_learning_advisory_worker_result",
        "framework_id": framework_id,
        "status": "generator_unavailable",
        "reason": reason,
        "candidate_ref": f"external-learning:{framework_id}:{action_type}:generator-unavailable",
        "refs_only": True,
        "body_included": False,
        "advisory_only": True,
        "can_block_current_owner_action": False,
        "allowed_writes": [],
        "forbidden_writes": list(FORBIDDEN_WRITES),
        "authority_boundary": _sidecar_authority_boundary(),
    }


def _normalize_advisory_worker_result(
    *,
    framework_id: str,
    action_type: str,
    result: Mapping[str, Any],
) -> dict[str, Any]:
    normalized = dict(result)
    normalized["surface_kind"] = (
        _text(normalized.get("surface_kind"))
        or "mas_external_learning_advisory_worker_result"
    )
    normalized["framework_id"] = _text(normalized.get("framework_id")) or framework_id
    normalized["candidate_ref"] = (
        _text(normalized.get("candidate_ref"))
        or f"external-learning:{framework_id}:{action_type}:advisory-worker"
    )
    normalized["refs_only"] = True
    normalized["body_included"] = False
    normalized["advisory_only"] = True
    normalized["can_block_current_owner_action"] = False
    normalized["allowed_writes"] = []
    normalized["forbidden_writes"] = list(FORBIDDEN_WRITES)
    normalized["authority_boundary"] = _sidecar_authority_boundary()
    return normalized


def _candidate_role(*, framework_id: str, action_type: str) -> str:
    if framework_id == "paperspine":
        return "motivation_spine_and_writing_rationale_hint"
    if framework_id == "paperorchestra":
        return "authoring_dag_outline_plot_and_autorater_hint"
    if framework_id == "aris":
        return "cross_model_review_or_experiment_queue_hint"
    if framework_id == "academic_research_skills":
        return "claim_citation_and_material_passport_hint"
    if framework_id == "nature_skills":
        return "quality_pack_ref_floor_hint"
    if framework_id == "co_scientist":
        return "hypothesis_portfolio_and_next_delta_hint"
    if framework_id == "ark_progress_first":
        return "real_run_closeout_or_citation_queue_hint"
    if framework_id == "open_auto_research":
        return "read_only_open_auto_research_projection_hint"
    return "progress_accelerator_hint"


def _counts(frameworks: list[Mapping[str, Any]]) -> dict[str, int]:
    counts = {
        "framework_count": len(frameworks),
        "owner_surface_landed_count": 0,
        "sidecar_execution_slot_count": 0,
        "contract_or_projection_only_gap_count": 0,
        "not_landed_gap_count": 0,
    }
    for framework in frameworks:
        status = _text(framework.get("closure_status"))
        if status in {
            "owner_surface_landed",
            "contract_projection_landed",
            "read_model_landed",
        }:
            counts["owner_surface_landed_count"] += 1
        if status in {"sidecar_execution_slot_landed", "sidecar_or_worker_landed"}:
            counts["sidecar_execution_slot_count"] += 1
        if status in {
            "thin_projection_landed_worker_scaleout_gap",
            "contract_only_gap",
            "history_only_gap",
        }:
            counts["contract_or_projection_only_gap_count"] += 1
        if status == "not_landed_gap":
            counts["not_landed_gap_count"] += 1
    return counts


def _dispatch_text(dispatch: Mapping[str, Any], key: str) -> str | None:
    return _text(dispatch.get(key)) or _text(_mapping(dispatch.get("source_action")).get(key))


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: object) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "ALLOWED_WRITES",
    "FORBIDDEN_WRITES",
    "REQUEST_RELATIVE_PATH",
    "SCHEMA_VERSION",
    "SIDECAR_ACTION_TYPE",
    "SIDECAR_CALLABLE_SURFACE",
    "SIDECAR_OWNER",
    "SIDECAR_RESULT_RELATIVE_PATH",
    "SIDECAR_SURFACE_KIND",
    "SIDECAR_WORKER_REGISTRY",
    "SURFACE_KIND",
    "build_external_learning_adoption_closure",
    "run_external_learning_sidecar",
]
