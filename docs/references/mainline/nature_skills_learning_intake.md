# Nature-skills Learning Intake

Owner: `MedAutoScience`
Purpose: `nature_skills_pattern_provenance`
State: `support_reference`
Machine boundary: 本文只保留 clean-room 来源与 pattern 归属。当前机器面归 `contracts/capability_map.json`、MAS Stage quality policy、MAS ScholarSkills、OPL-hosted execution与 Review receipts。

## 来源

Fresh intake 基于 `Yuan1z0825/nature-skills` observed commit `1cb9070fdd94929d5f267ce6585ac87e2cba60b3`。可复用的不是外部 runner，而是薄入口、declarative manifest、always-load core、axis-specific fragments、on-demand references 与 explicit gates。

## 当前吸收

- 写作、review、figure、citation、reader与 response pattern 进入 MAS Stage prompts、knowledge/quality requirements与 MAS ScholarSkills professional Skills。
- Figure 相关专业能力由 `medical-figure-design` 编排，`medical-figure-style` 与 `medical-figure-composer` 提供子能力；OPL 只托管工具与 Attempt。
- Exact figure/manuscript quality由独立 reviewer/re-reviewer判断；MAS owner持有 publication/export/artifact authority。
- OPL Pack负责 Skill package、dependency closure、materialization、currentness与 lifecycle receipt。

## 不吸收

- 不复制 Nature-skills runner、manifest schema、renderer、gallery、HTML/export UI或 provider client。
- 不恢复 MAS-local display sidecar、template selector、figure router、quality validator或 workbench。
- 外部 checklist、render success、tool receipt或 focused test不等于 medical quality、publication ready或 owner acceptance。

## Current verification

Repo-level boundary由 `tests/test_stage_quality_cycle_policy.py`、`tests/test_standard_agent_boundary.py`、fast/meta与冻结 Framework admission保护。真实论文图件仍需 exact artifact、independent Review receipt与 MAS owner result。
