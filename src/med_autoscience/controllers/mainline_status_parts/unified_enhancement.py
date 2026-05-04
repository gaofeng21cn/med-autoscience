from __future__ import annotations

from typing import Any


def build_unified_enhancement_program_projection() -> dict[str, Any]:
    return {
        "surface_kind": "mas_mds_unified_enhancement_program_projection",
        "program_id": "mas_mds_unified_enhancement_program",
        "status": "active_integration_program",
        "owner": "MedAutoScience",
        "source_doc": "docs/program/mas_mds_unified_enhancement_program.md",
        "projection_only": True,
        "authority_boundary": (
            "This is a mainline projection for operator readability only. It does not become "
            "quality, submission, delivery, runtime, or controller authority."
        ),
        "authority_surfaces": [
            "StudyTruthKernel",
            "RuntimeHealthKernel",
            "publication_eval/latest.json",
            "controller_decisions/latest.json",
            "canonical artifact proof",
        ],
        "summary": (
            "把自动科研、文件管理和控制面增强建议收敛成 5 条 MAS-owned program lane，"
            "避免 frontdesk、cockpit、progress、delivery、observability 和 controller 各自重复解释下一步。"
        ),
        "lanes": [
            {
                "lane_id": "L1_real_workspace_longitudinal_soak",
                "owner": "MedAutoScience runtime + quality",
                "summary": "用真实 disease workspace 证明 pre-submission、revision、reopen、route change、final rebuild 和 recovery。",
                "authority_boundary": "proof/evidence only; publication readiness remains owned by quality truth surfaces.",
                "boundary_kind": "evidence_source",
            },
            {
                "lane_id": "L2_pi_action_projection",
                "owner": "MedAutoScience product entry",
                "summary": "把用户入口动作语言压缩成同一套 PI-readable next action payload。",
                "authority_boundary": "entry surfaces consume study-progress action projection; they do not calculate canonical next action.",
                "boundary_kind": "user_projection",
            },
            {
                "lane_id": "L3_outcome_calibration_and_provider_ops",
                "owner": "MedAutoScience Observability OS",
                "summary": "合并投稿结果反馈、AI reviewer calibration、provider freshness、citation drift 和 journal-family fixtures。",
                "authority_boundary": "observability and regression evidence only; no direct ready authorization.",
                "boundary_kind": "observability_projection",
            },
            {
                "lane_id": "L4_delivery_and_legacy_upgrade_visibility",
                "owner": "MedAutoScience artifact/delivery projection",
                "summary": "合并 legacy upgrade queue、doctor README、delivery traffic-light 和 backfill blockers。",
                "authority_boundary": "read model only; delivery truth writes require controller-authorized sync/apply.",
                "boundary_kind": "delivery_projection",
            },
            {
                "lane_id": "L5_natural_boundary_and_audit_compaction",
                "owner": "MedAutoScience maintainability",
                "summary": "合并 ownership audit、structure top targets、audit compaction pre-contract 和低风险拆分。",
                "authority_boundary": "maintainability only; it does not change study, publication, delivery, or runtime truth.",
                "boundary_kind": "maintainability_audit",
            },
        ],
        "recommendation_rollup": [
            {
                "recommendation_id": "auto_research_1",
                "lane_id": "L1_real_workspace_longitudinal_soak",
                "summary": "更多真实 disease workspace 长期 soak。",
            },
            {
                "recommendation_id": "auto_research_2",
                "lane_id": "L2_pi_action_projection",
                "summary": "用户入口动作语言压缩成 PI 判断。",
            },
            {
                "recommendation_id": "auto_research_3",
                "lane_id": "L3_outcome_calibration_and_provider_ops",
                "summary": "投稿结果反馈 calibration regression。",
            },
            {
                "recommendation_id": "auto_research_4",
                "lane_id": "L3_outcome_calibration_and_provider_ops",
                "summary": "provider freshness、partial outage、citation drift。",
            },
            {
                "recommendation_id": "auto_research_5",
                "lane_id": "L2_pi_action_projection",
                "secondary_lane_id": "L3_outcome_calibration_and_provider_ops",
                "summary": "journal-family writing pack。",
            },
            {
                "recommendation_id": "auto_research_6",
                "lane_id": "L1_real_workspace_longitudinal_soak",
                "summary": "first full draft authorization 到 submission package rebuild 闭环时延。",
            },
            {
                "recommendation_id": "file_management_1",
                "lane_id": "L4_delivery_and_legacy_upgrade_visibility",
                "summary": "legacy upgrade queue。",
            },
            {
                "recommendation_id": "file_management_2",
                "lane_id": "L4_delivery_and_legacy_upgrade_visibility",
                "summary": "医生友好 current_package README。",
            },
            {
                "recommendation_id": "file_management_3",
                "lane_id": "L5_natural_boundary_and_audit_compaction",
                "summary": "大文件结构瘦身。",
            },
            {
                "recommendation_id": "file_management_4",
                "lane_id": "L3_outcome_calibration_and_provider_ops",
                "summary": "真实 journal profile fixture matrix。",
            },
            {
                "recommendation_id": "file_management_5",
                "lane_id": "L4_delivery_and_legacy_upgrade_visibility",
                "summary": "delivery status 红黄绿可视化。",
            },
            {
                "recommendation_id": "control_plane_1",
                "lane_id": "L4_delivery_and_legacy_upgrade_visibility",
                "summary": "真实 workspace backfill blockers。",
            },
            {
                "recommendation_id": "control_plane_2",
                "lane_id": "L5_natural_boundary_and_audit_compaction",
                "summary": "audit_log compaction policy。",
            },
            {
                "recommendation_id": "control_plane_3",
                "lane_id": "L5_natural_boundary_and_audit_compaction",
                "summary": "旧 worktree ownership audit。",
            },
            {
                "recommendation_id": "control_plane_4",
                "lane_id": "L5_natural_boundary_and_audit_compaction",
                "summary": "历史大文件/高复杂函数低风险拆分。",
            },
        ],
        "module_boundary_audit": {
            "surface_kind": "module_boundary_audit_projection",
            "projection_only": True,
            "summary": "模块边界 audit 只描述 owner 和 read-model 边界，不能写入 authority truth。",
            "boundaries": [
                {
                    "boundary_id": "study_truth",
                    "authority_owner": "StudyTruthKernel",
                    "projection_consumers": ["study-progress", "workspace-cockpit", "product-frontdesk"],
                },
                {
                    "boundary_id": "runtime_truth",
                    "authority_owner": "RuntimeHealthKernel",
                    "projection_consumers": ["study_runtime_status", "runtime_watch", "mainline-status"],
                },
                {
                    "boundary_id": "quality_truth",
                    "authority_owner": "publication_eval/latest.json + publication_gate",
                    "projection_consumers": ["mainline-status", "AI reviewer calibration reports"],
                },
                {
                    "boundary_id": "delivery_truth",
                    "authority_owner": "controller-authorized artifact sync/apply",
                    "projection_consumers": ["delivery inspection", "legacy upgrade visibility"],
                },
                {
                    "boundary_id": "maintainability_truth",
                    "authority_owner": "Sentrux structure lane + line budget + owner-boundary tests",
                    "projection_consumers": ["module boundary audit", "structure target list"],
                },
            ],
        },
    }
