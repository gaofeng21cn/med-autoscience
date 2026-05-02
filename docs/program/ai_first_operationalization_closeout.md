# AI-first Operationalization Closeout

本 note 是 `plan_completion_ledger` 的人工/AI 审阅附件。它记录近期 `MAS AI-first Research OS` 规划的落地状态，帮助后续吸收并行 worktree 时判断哪些已经是 repo-level contract/read model，哪些仍在 runtime lane 中落地，哪些必须等真实论文 soak 才能宣称闭环。

它不参与 `scripts/verify.sh`、`make test-meta`、publication gate、submission gate 或 runtime authority 判定。机械系统不得把本 note 的文字当作 ready、finalize-ready、submission-ready 或质量关闭证据。

## 范围

本轮计划收口的是 owner、contract、read model 与剩余证据缺口，不收口物理迁移、跨仓 runtime ingest、MDS 退场或真实论文全量 soak。

当前目标架构已经冻结为：

- `MAS` 持有 research、quality、publication、artifact 与 user-visible truth owner。
- `MDS` 保留为 replaceable backend、behavior oracle 与 upstream intake buffer。
- 机械系统只持有 evidence、status、completeness、blocker、projection 与 replay。
- AI reviewer artifact 持有科学质量、医学写作质量、publishability 与 submission-facing readiness。

## 已有 Repo-level Surface

以下能力已经有 repo-tracked contract 或 read model，可作为后续实现和审阅的稳定参照：

| 领域 | 当前 repo-level surface | Closeout 状态 |
| --- | --- | --- |
| Study truth | `StudyTruthKernel` contract; `study_runtime_status.study_truth_snapshot`; `study_progress.study_truth_snapshot` | `contract/read_model_present` |
| Runtime health | `RuntimeHealthKernel` contract; `study_runtime_status.runtime_health_snapshot`; `study_progress.runtime_health_snapshot`; `runtime_watch` projection | `contract/read_model_present` |
| AI-first quality boundary | `AI-first Quality Boundary Policy`; `assessment_provenance.owner=ai_reviewer`; `medical_publication_ai_reviewer_os_v1` trace requirement | `contract_present` |
| First-draft quality | `Medical Manuscript First-Draft Quality Policy`; `pre_draft_writing_readiness_contract`; manuscript-native prose contract | `contract_present` |
| Evidence/review governance | `Evidence Review Contract`; study charter expectation closure; durable evidence/review refs | `contract_present` |
| Artifact authority | `Canonical Artifact Contract`; `artifact_rebuild_integrity_contract`; derived package cannot become authority | `contract_present` |
| Artifact visibility | `Artifact Inventory Projection`; artifact inventory is projection, not authority | `read_model_present` |
| Operations observability | `ai_first_observability_summary`; `ai_first_operations_dashboard_summary` | `read_model_present` |

这些 surface 足以解释当前 AI-first operationalization lanes 的架构方向和审阅口径。它们本身不足以证明任一真实论文已经完成 soak。

## 当前并行落地 Lane

以下工作被刻意拆到并行 worktree。本 ledger 只记录 owner 与预期落地 surface；在对应 commit 和验证被吸收前，不声明这些 lane 已完成。

| Lane | 活跃 branch/worktree | 预期落地 surface | Ledger 解释 |
| --- | --- | --- | --- |
| Pre-draft runtime | `codex/predraft-quality-runtime` / `.worktrees/predraft-quality-runtime` | materialized `paper/pre_draft_writing_readiness.json`; fail-closed AI reviewer provenance; write route consumes readiness before first full draft | `parallel_lane_active` |
| AI reviewer workflow | `codex/ai-reviewer-workflow` / `.worktrees/ai-reviewer-workflow` | AI reviewer-backed `publication_eval/latest.json`; `medical_publication_critique_v1`; `medical_publication_ai_reviewer_os_v1` trace | `parallel_lane_active` |
| Artifact proof | `codex/artifact-runtime-proof` / `.worktrees/artifact-runtime-proof` | canonical artifact rebuild proof for manuscript, figures, tables and submission package; derived package remains read-only handoff | `parallel_lane_active` |
| Operations state | `codex/operations-runtime-state` / `.worktrees/operations-runtime-state` | operations dashboard projection across runtime, quality, artifact freshness, route-back and human-review signals | `parallel_lane_active` |

后续吸收这些 lane 的 closeout 必须回写真实 commit id、验证命令和剩余缺口。在此之前，它们的状态是 planned/active，不是 complete。

## 剩余证据缺口

诚实剩余缺口是真实论文 soak。

下一份 proof 必须来自至少一条 live manuscript line，并在同一 study 中证明：

- pre-draft readiness is generated from study charter, evidence ledger, review ledger, canonical blueprint and AI reviewer-backed eval;
- AI reviewer-backed publication eval holds quality authority with complete provenance and reviewer OS trace;
- canonical artifact rebuild proof links sources, fingerprints, quality decision and controller decision for derived manuscript/package outputs;
- operations-state projection reads existing runtime/progress/quality/artifact snapshots without becoming authority;
- `study-progress`, `workspace-cockpit` and `product-frontdesk` explain the same current stage, blocker, next action and human-review need.

在该 proof 出现前，正确状态是 `repo_contracts_ready_for_soak`，不是 `AI-first Research OS fully proven`。

## 审阅规则

本 note 可供人工或 AI reviewer 对比计划意图与实施状态。它不得被转换成机械质量 gate。未来如果需要机械 gate，必须由显式 schema、runtime surface、测试和 live-study evidence 支撑，并作为独立 contract 变更记录。
