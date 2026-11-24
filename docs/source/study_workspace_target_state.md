# Study 与 Workspace 职责及接入边界

Owner: `MedAutoScience + OPL Workspace`
Purpose: `workspace_owner_boundary_and_onboarding`
State: `active_current_truth`
Machine boundary: Workspace locator、quest/StageRun lifecycle、StateIndex、restore/retention、environment prepare 与 hosted workbench 的机器真相归 OPL；医学 study/source/artifact truth、domain handlers、owner receipts 与 typed blockers 归 MAS。

## Workspace 对象模型与目录分层

`workspace_index.json#/studies` 持有研究线清单；每条记录以 `study_id` 和 `canonical_study_root` 指向 `studies/<study_id>/`。OPL 通过 `contracts/domain_descriptor.json#/standard_agent_interface/inventory_projection` 只读投影该清单；业务状态由 MAS lifecycle/authority 生成，不能从 provider、Temporal、目录存在或缺失 telemetry 推断。

```text
<workspace>/
├── data/datasets/                  # 病种级医学数据资产 release（body plane）
├── memory/portfolio/data_assets/   # 可重建数据资产治理投影（非个人长期知识库）
├── shared/memory/                  # 无外部资料库时的默认 owner/topic 知识目录
├── studies/<study_id>/
│   ├── control/lifecycle.json      # MAS 业务生命周期与显式唤醒权限
│   ├── manuscript/                 # 当前可编辑稿件的 canonical editable source
│   ├── analysis/                   # study 特有 cohort、代码、参数、结果与验证
│   ├── memory/ / state/            # 无外部资料库时的默认项目知识与时点事实
│   ├── artifacts/stage_outputs/    # consumed/produced refs、审阅、lineage 与诊断
│   ├── artifacts/research_trajectory/snapshot.json  # MAS 科研轨迹只读投影
│   └── submission/                 # 当前 owner 授权、同 generation 的完整交付投影
├── refs/                           # 来源与参考材料
└── artifacts/                      # 共享领域产物
```

OPL state root（package locks/receipts、workspace/quest bindings、StageRun/Attempt ledgers、不可变知识快照、StateIndex/restore/retention refs 与 hosted workbench 投影）与 MAS workspace 各自独立，仅通过 explicit locator、content digest、lineage ref 与 receipt 连接。

- 知识正文不强制复制到工作区：已有 Obsidian 或其他 Markdown 资料库时，个人、团队和病种主题正文直接绑定原处；研究数据、文献、论文与接收决策属于业务资产，不随运行缓存清理（见 [知识与记忆政策](../policies/domain_memory_markdown_first_policy.md)）。
- 数据资产布局与四桶分账见 [数据资产目标模型](./medical_data_asset_target_operating_model.md)，正文与交付见 [修订与投稿合同](../policies/study-workflow/submission_revision_operating_contract.md)，生命周期四态与 CAS 唤醒见 [Study 生命周期控制](./study_lifecycle_control.md)。

## 身份与接入顺序

- `workspace_root`、`study_id`、`stage_run_id` / `attempt_id` 与 `artifact/source/package refs` 不可互替，不能通过目录名或 handoff 编号猜测身份。`profiles/workspace.profile.template.toml` 是 profile 结构参考，不是 workspace initializer（见 [Workspace Profile 模板](../../profiles/workspace.profile.template.toml) 与 [Bootstrap](../../bootstrap/README.md)）。
- MAS 已退役 repo-local workspace initializer、bootstrap shell 与私有 CLI/MCP 入口（详见 [约束](../invariants.md#退役与兼容)）。

接入与执行顺序：

1. 通过 OPL generated/hosted workspace lifecycle surface 创建或登记 workspace，绑定 `profile_ref` 与至少包含 `workspace_root`、`study_id`、`task_intent` 及 schema 要求的 refs。
2. 以 `workspace_root`、`study_id` 与当前 refs 调用 `contracts/action_catalog.json` 中的 V2 Stage action；Codex 在 Tool Affordance Boundary 内选择 source、analysis、writing、review 或 display 能力。
3. 未形成 ready receipt 时可保留部分、阴性或失败产物及质量债供下一 Stage 推理；真正的权限、身份、来源、安全或 human gate 必须阻断（见 [Stage / Route / Handoff](../runtime/stage_route_handoff_standard.md)）。暂停、交付暂停或停止状态的 current stage 必须为空。

## Git 边界、旧 Workspace 与迁移

- **No root Git / No quest Git**：新 workspace 默认不使用 root Git 或 quest Git；Git history/diff 与 worktree list 不是 current runtime truth。
- **旧 `.ds` 与 legacy intake**：旧 `.ds/`、workspace-local Git、LaunchAgent/cron、runtime SQLite 与 archived reports 只按 provenance、restore proof 或 cleanup 输入读取，物理清理与迁移必须交 OPL lifecycle owner 并要求 inventory、hash、authorization 与目标侧 readback。
- **Workspace 迁移**：实际目录迁移须有用户授权、artifact/identity 清单、保留来源、回退方式与目标侧 readback，完整迁移 `manuscript/`、revision、独立 review 与 quality debt；不把历史 `paper/` 恢复为默认入口。

结构校验使用 `scripts/verify.sh`，workspace 可运行与恢复证据需读取对应 fresh locator、receipt 与 owner evidence（见 [Runtime 边界](../runtime/runtime_boundary.md)）。
