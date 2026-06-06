from __future__ import annotations

from typing import Any

from opl_harness_shared.product_entry_program_companions import (
    build_clearance_lane as _build_shared_clearance_lane,
    build_clearance_target as _build_shared_clearance_target,
    build_platform_target as _build_shared_platform_target,
    build_product_entry_program_step as _build_shared_product_entry_program_step,
    build_product_entry_program_surface as _build_shared_product_entry_program_surface,
    build_program_capability as _build_shared_program_capability,
    build_program_sequence_step as _build_shared_program_sequence_step,
    build_source_provenance_surface as _build_shared_source_provenance_surface,
)

from med_autoscience.opl_runtime_contract import OPL_HOSTED_STAGE_RUNTIME_ID, OPL_RUNTIME_OWNER


def build_backend_deconstruction_lane(
    *,
    deconstruction_map_ref: str,
    **kwargs: Any,
) -> dict[str, Any]:
    _build_shared_source_provenance_surface(
        summary=str(kwargs["summary"]),
        source_provenance_ref={
            "surface_kind": "source_provenance",
            "ref": deconstruction_map_ref,
        },
        historical_fixture_ref={
            "surface_kind": "historical_fixture_ref",
            "ref": "fixtures/med-deepscientist/parity/",
        },
        explicit_archive_import_ref={
            "surface_kind": "explicit_archive_import_ref",
            "command": "uv run python -m med_autoscience.cli backend-audit --mode archive-import",
        },
        parity_oracle_ref={
            "surface_kind": "parity_oracle_ref",
            "ref": "program:med_deepscientist_retained_capability_parity",
        },
        authority_boundary=[
            "opl_provider_runtime_is_default_generic_owner",
            "source_refs_do_not_define_runtime_dependency",
            "archive_import_is_explicit_one_way_provenance",
        ],
        capability_classification="source_provenance_only",
        recommended_audit_command="uv run python -m med_autoscience.cli backend-audit",
    )
    return {
        "surface_kind": "phase4_backend_deconstruction_lane",
        "summary": str(kwargs["summary"]),
        "substrate_targets": list(kwargs["substrate_targets"]),
        "backend_retained_now": list(kwargs["backend_retained_now"]),
        "current_backend_chain": list(kwargs["current_backend_chain"]),
        "optional_executor_proofs": list(kwargs["optional_executor_proofs"]),
        "promotion_rules": list(kwargs["promotion_rules"]),
        "deconstruction_map_ref": deconstruction_map_ref,
        "recommended_phase_command": str(kwargs["recommended_phase_command"]),
    }


def build_platform_target() -> dict[str, Any]:
    return _build_shared_platform_target(
        summary=(
            "Phase 5 已完成 MAS functional monolith closeout；后续平台工作只剩 optional hosted/stage-runtime "
            "frontend 与 future upstream intake，不再以 external MDS runtime core 为默认运行条件。"
        ),
        sequence_scope="monorepo_landing_readiness",
        current_step_id="functional_monolith_completion",
        current_readiness_summary=(
            "MAS 默认研究入口、进度、诊断、artifact/quality parity、workspace helpers 与 OPL handoff 都已切到 MAS-owned domain surfaces；"
            "external MDS 只保留 frozen archive / historical fixture / explicit archive import reference。"
        ),
        north_star_topology={
            "domain_agent": "Med Auto Science",
            "runtime_owner": OPL_RUNTIME_OWNER,
            "runtime_substrate": OPL_HOSTED_STAGE_RUNTIME_ID,
            "controlled_research_backend": (
                "MAS domain owner receipts / Artifact authority refs / Quality verdict refs; "
                "generic runtime lifecycle handoff to OPL"
            ),
            "monorepo_status": "functional_monolith_completion_landed",
        },
        target_internal_modules=[
            "controller_charter",
            "runtime",
            "eval_hygiene",
        ],
        landing_sequence=[
            _build_shared_program_sequence_step(
                step_id="freeze_stage_runtime_truth",
                title="Freeze stage-runtime truth",
                status="completed",
                phase_id="phase_1_mainline_established",
                summary="mainline topology、product-entry companions 与 post-gate platform wording 已冻结成 repo-tracked truth。",
            ),
            _build_shared_program_sequence_step(
                step_id="stabilize_user_product_loop",
                title="Stabilize user product loop",
                status="in_progress",
                phase_id="phase_2_user_product_loop",
                summary=(
                    "当前活跃步骤：用 autonomy / quality / single-project owner 三线继续收紧 MAS "
                    "owner truth，并把启动 / 下任务 / 看进度 / 看恢复建议收成稳定前台回路。"
                ),
            ),
            _build_shared_program_sequence_step(
                step_id="clear_multi_workspace_host_gate",
                title="Clear multi-workspace / host gate",
                status="pending",
                phase_id="phase_3_multi_workspace_host_clearance",
                summary="把 runtime/service/recovery proof 扩到更多 workspace / host 后，才具备更大 cutover 资格。",
            ),
            _build_shared_program_sequence_step(
                step_id="freeze_backend_deconstruction_boundary",
                title="Freeze backend deconstruction boundary",
                status="pending",
                phase_id="phase_4_backend_deconstruction",
                summary="先把 substrate 与 backend retained-now 的边界继续收紧，再谈 executor 迁移或 ingest。",
            ),
            _build_shared_program_sequence_step(
                step_id="mds_no_history_absorb",
                title="MDS no-history absorb",
                status="completed",
                phase_id="phase_5_stage_runtime_platform_maturation",
                summary="MDS retained capability 已通过 no-history provenance、author guard、parity harness 和 external dependency retirement 收口到 MAS。",
            ),
            _build_shared_program_sequence_step(
                step_id="runtime_core_ingest",
                title="Runtime core ingest",
                status="completed",
                phase_id="phase_5_stage_runtime_platform_maturation",
                summary=(
                    "默认 domain runtime receipts 已由 MAS 承接；external MDS daemon/runtime root "
                    "不再是默认运行或诊断依赖。"
                ),
            ),
            _build_shared_program_sequence_step(
                step_id="functional_monolith_completion",
                title="Functional monolith completion",
                status="completed",
                phase_id="phase_5_stage_runtime_platform_maturation",
                summary="MAS 默认 CLI/MCP/product-entry/workspace helper/Progress Portal/OPL handoff 都不要求外部 MDS repo、daemon 或 WebUI。",
            ),
            _build_shared_program_sequence_step(
                step_id="optional_hosted_frontend_packaging",
                title="Optional hosted frontend packaging",
                status="pending",
                phase_id="phase_5_stage_runtime_platform_maturation",
                summary="后续可把 MAS Progress Portal / OPL dashboard 打包成 hosted frontend，但不得重解释 MAS study truth。",
            ),
            _build_shared_program_sequence_step(
                step_id="future_upstream_source_intake_review",
                title="Future upstream source intake review",
                status="pending",
                phase_id="phase_5_stage_runtime_platform_maturation",
                summary="未来如需吸收 MDS/DeepScientist 新 snapshot，只能走 no-history provenance、author audit 和 MAS-owned capability proof。",
            ),
        ],
        completed_step_ids=[
            "freeze_stage_runtime_truth",
            "mds_no_history_absorb",
            "runtime_core_ingest",
            "functional_monolith_completion",
        ],
        remaining_step_ids=[
            "optional_hosted_frontend_packaging",
            "future_upstream_source_intake_review",
        ],
        promotion_gates=[
            "phase_1_mainline_established",
            "phase_2_user_product_loop",
            "phase_3_multi_workspace_host_clearance",
            "phase_4_backend_deconstruction",
        ],
        recommended_phase_command=(
            "uv run python -m med_autoscience.cli doctor mainline-phase --phase phase_5_stage_runtime_platform_maturation"
        ),
        land_now=[
            "repo-tracked product-entry shell and family orchestration companions",
            "controller-owned runtime/progress/recovery truth",
            "CLI/MCP/controller entry surfaces that already support real work",
            "MAS-owned Progress Portal and OPL handoff refs",
        ],
        not_yet=[
            "mature hosted standalone medical frontend",
            "future upstream source intake beyond historical fixture/provenance refs",
        ],
    )


def build_phase2_user_product_loop_lane(
    *,
    entry_status_command: str,
    workspace_cockpit_command: str,
    submit_task_command: str,
    launch_study_command: str,
    study_progress_command: str,
    controller_decisions_ref: str,
) -> dict[str, Any]:
    return {
        "surface_kind": "phase2_user_product_loop_lane",
        "summary": "把启动 MAS、给 study 下任务、续跑、持续看进度、处理恢复建议和人工 gate 收成同一条用户回路。",
        "recommended_step_id": "open_product_entry",
        "recommended_command": entry_status_command,
        "single_path": [
            {
                "step_id": "open_product_entry",
                "title": "先打开 MAS 产品入口",
                "surface_kind": "product_entry_status",
                "command": entry_status_command,
            },
            {
                "step_id": "inspect_workspace_inbox",
                "title": "确认当前 workspace inbox / attention queue",
                "surface_kind": "workspace_cockpit",
                "command": workspace_cockpit_command,
            },
            {
                "step_id": "submit_task",
                "title": "给目标 study 写 durable task intake",
                "surface_kind": "study_task_intake",
                "command": submit_task_command,
            },
            {
                "step_id": "continue_study",
                "title": "启动或续跑当前 study",
                "surface_kind": "launch_study",
                "command": launch_study_command,
            },
            {
                "step_id": "inspect_progress",
                "title": "持续看进度、阻塞和恢复建议",
                "surface_kind": "study_progress",
                "command": study_progress_command,
            },
            {
                "step_id": "handle_human_gate",
                "title": "遇到人工 gate 时回到 progress / cockpit 做决策",
                "surface_kind": "study_progress",
                "command": study_progress_command,
            },
        ],
        "operator_questions": [
            {
                "question": "用户现在怎么启动 MAS？",
                "answer_surface_kind": "product_entry_status",
                "command": entry_status_command,
            },
            {
                "question": "用户怎么给 study 下任务？",
                "answer_surface_kind": "study_task_intake",
                "command": submit_task_command,
            },
            {
                "question": "用户怎么持续看进度和恢复建议？",
                "answer_surface_kind": "study_progress",
                "command": study_progress_command,
            },
        ],
        "proof_surfaces": [
            {
                "surface_kind": "product_entry_status",
                "command": entry_status_command,
            },
            {
                "surface_kind": "workspace_cockpit",
                "command": workspace_cockpit_command,
            },
            {
                "surface_kind": "study_progress.operator_verdict",
                "command": study_progress_command,
            },
            {
                "surface_kind": "study_progress.recovery_contract",
                "command": study_progress_command,
            },
            {
                "surface_kind": "controller_decisions",
                "ref": controller_decisions_ref,
            },
        ],
    }


def build_phase2_user_product_loop() -> dict[str, Any]:
    return build_phase2_user_product_loop_lane(
        entry_status_command="uv run python -m med_autoscience.cli product entry_status --profile <profile>",
        workspace_cockpit_command="uv run python -m med_autoscience.cli workspace cockpit --profile <profile>",
        submit_task_command=(
            "uv run python -m med_autoscience.cli study submit-task --profile <profile> "
            "--study-id <study_id> --task-intent '<task_intent>'"
        ),
        launch_study_command="uv run python -m med_autoscience.cli study launch --profile <profile> --study-id <study_id>",
        study_progress_command=(
            "uv run python -m med_autoscience.cli study progress --profile <profile> --study-id <study_id>"
        ),
        controller_decisions_ref="studies/<study_id>/artifacts/controller_decisions/latest.json",
    )


def build_phase3_clearance_lane() -> dict[str, Any]:
    doctor_command = "uv run python -m med_autoscience.cli doctor report --profile <profile>"
    supervisor_service_command = "uv run python -m med_autoscience.cli study progress --profile <profile> --format json"
    refresh_supervision_command = (
        "uv run python -m med_autoscience.cli runtime domain-health-diagnostic --runtime-root <runtime_root> "
        "--profile <profile> --request-opl-stage-attempts --request-opl-owner-route-reconcile --apply"
    )
    launch_study_command = (
        "uv run python -m med_autoscience.cli study launch --profile <profile> --study-id <study_id>"
    )
    study_progress_command = (
        "uv run python -m med_autoscience.cli study progress --profile <profile> --study-id <study_id>"
    )
    return _build_shared_clearance_lane(
        surface_kind="phase3_host_clearance_lane",
        summary=(
            "Phase 3 只做可选 hosted runtime / 多宿主 proof；MAS 默认研究入口、owner receipt "
            "与 paper-progress SLO 由 MAS surface 承接，generic cadence/provider SLO 归 OPL runtime manager。"
        ),
        recommended_step_id="mas_domain_refs_boundary",
        recommended_command=doctor_command,
        clearance_targets=[
            _build_shared_clearance_target(
                target_id="mas_domain_refs_boundary",
                title="Check MAS domain refs and legacy runtime tombstone boundary",
                commands=[doctor_command],
            ),
            _build_shared_clearance_target(
                target_id="supervisor_service",
                title="Inspect OPL-owned supervision projection",
                commands=[
                    supervisor_service_command,
                    refresh_supervision_command,
                ],
            ),
            _build_shared_clearance_target(
                target_id="study_recovery_proof",
                title="Prove live study recovery and supervision",
                commands=[
                    launch_study_command,
                    study_progress_command,
                ],
            ),
        ],
        clearance_loop=[
            _build_shared_product_entry_program_step(
                step_id="mas_domain_refs_boundary",
                title="确认 MAS domain refs boundary ready，旧 hosted runtime 仅保留 tombstone/provenance",
                surface_kind="doctor_domain_refs_boundary",
                command=doctor_command,
            ),
            _build_shared_product_entry_program_step(
                step_id="supervisor_service",
                title="确认 OPL replacement 与 MAS domain projection 在线",
                surface_kind="workspace_supervisor_service",
                command=supervisor_service_command,
            ),
            _build_shared_product_entry_program_step(
                step_id="refresh_supervision",
                title="刷新 MAS domain refs projection",
                surface_kind="domain_health_diagnostic_refresh",
                command=refresh_supervision_command,
            ),
            _build_shared_product_entry_program_step(
                step_id="study_recovery_proof",
                title="证明 live study recovery / progress supervision 成立",
                surface_kind="launch_study",
                command=launch_study_command,
            ),
            _build_shared_product_entry_program_step(
                step_id="inspect_study_progress",
                title="读取 study-progress proof",
                surface_kind="study_progress",
                command=study_progress_command,
            ),
        ],
        proof_surfaces=[
            _build_shared_product_entry_program_surface(
                surface_kind="doctor.runtime_contract",
                command=doctor_command,
            ),
            _build_shared_product_entry_program_surface(
                surface_kind="progress_projection.autonomous_runtime_notice",
                command="uv run python -m med_autoscience.cli study progress --profile <profile> --study-id <study_id> --format json",
            ),
            _build_shared_product_entry_program_surface(
                surface_kind="domain_health_diagnostic",
                ref="studies/<study_id>/artifacts/domain_health_diagnostic/latest.json",
            ),
            _build_shared_product_entry_program_surface(
                surface_kind="opl_runtime_owner_handoff",
                ref="studies/<study_id>/artifacts/supervision/opl_runtime_owner_handoff/latest.json",
            ),
            _build_shared_product_entry_program_surface(
                surface_kind="controller_decisions",
                ref="studies/<study_id>/artifacts/controller_decisions/latest.json",
            ),
        ],
        recommended_phase_command=(
            "uv run python -m med_autoscience.cli doctor mainline-phase --phase phase_3_multi_workspace_host_clearance"
        ),
    )


def build_phase4_backend_deconstruction() -> dict[str, Any]:
    return build_backend_deconstruction_lane(
        summary="Phase 4 只保留 future upstream source intake / historical fixture governance；MDS 不再是 runtime substrate。",
        substrate_targets=[
            _build_shared_program_capability(
                capability_id="session_run_watch_recovery",
                owner="MAS domain runtime receipts",
                summary=(
                    "session / run / watch / recovery 的 domain owner receipt、paper-progress blocker "
                    "与 safe action refs 由 MAS surface 承接；generic scheduling / attempt lifecycle 迁往 OPL。"
                ),
            ),
            _build_shared_program_capability(
                capability_id="backend_generic_runtime_contract",
                owner="MedAutoScience controller boundary",
                summary="controller / transport / durable surface 只认 backend-generic contract 与 explicit runtime handle。",
            ),
        ],
        backend_retained_now=[
            "frozen MedDeepScientist source archive",
            "historical oracle fixtures",
            "explicit archive import / backend-audit reference",
        ],
        current_backend_chain=[
            "med_autoscience domain surfaces -> MAS owner receipts / artifact authority refs / quality verdict refs",
            "generic runtime/provider context -> OPL current_control_state refs-only handoff",
            "historical med_deepscientist fixture/provenance refs only",
        ],
        optional_executor_proofs=[
            {
                "executor_kind": "hermes_agent",
                "entrypoint": "optional hosted runtime adapter",
                "default_model": "inherit_local_hermes_default",
                "default_reasoning_effort": "inherit_local_hermes_default",
            }
        ],
        promotion_rules=[
            "no claim of platform runtime ingest without owner + contract + tests + proof",
            "executor replacement must be explicit and proof-backed",
            "do not restore external MDS as a default runtime dependency",
        ],
        deconstruction_map_ref="program:med_deepscientist_deconstruction_map",
        recommended_phase_command=(
            "uv run python -m med_autoscience.cli doctor mainline-phase --phase phase_4_backend_deconstruction"
        ),
    )
