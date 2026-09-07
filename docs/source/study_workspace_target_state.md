# Study 工作区职责

本文只解释当前 workspace/study 对象和目录职责；实际路径由 domain descriptor、study contracts 与当前 manifest 决定。目录存在本身不授予质量、来源或发表权限。

## Workspace 与 study

`workspace_index.json#/studies` 持有研究线清单；每条记录以 `study_id` 和 `canonical_study_root` 指向 `studies/<study_id>/`。OPL 通过 `contracts/domain_descriptor.json#/standard_agent_interface/inventory_projection` 只读投影该清单。业务状态由 MAS lifecycle/authority 生成，不能从 provider、Temporal 或缺失 telemetry 推断。

Workspace 的数据资产布局见 [数据资产模型](./medical_data_asset_target_operating_model.md)；共享文献与记忆见 [知识合同](../runtime/contracts/workspace_knowledge_and_literature_contract.md)。这些共享资源不能被某个 study 的派生结果静默覆盖。

## 单篇论文的职责分层

| 对象 | 职责 |
| --- | --- |
| `control/lifecycle.json` | MAS 业务生命周期与显式唤醒权限 |
| `manuscript/` | 当前可编辑稿件的 canonical source |
| `analysis/` | study 特有 cohort、分析代码、参数、结果与验证 |
| `artifacts/stage_outputs/` | consumed/produced refs、阶段产物、审阅、lineage 与诊断 |
| `artifacts/research_trajectory/snapshot.json` | MAS 科研轨迹 projection，供选中 study 的 typed view 读取 |
| `submission/` | 当前 owner 授权、同 generation 的完整交付投影 |
| 运行账本 | OPL 持有的 StageRun/Attempt、retry、provider、usage 与执行 evidence |

正文与交付的详细规则由 [修订与投稿合同](../policies/study-workflow/submission_revision_operating_contract.md) 持有；不把历史 `paper/` 路径恢复为新 workspace 默认入口。

Canonical Stage identity 来自 `agent/stages/manifest.json`；论文物理阶段与 artifact role 来自 `contracts/mas-paper-study-stage-pack.json` 和 artifact-kernel adoption。不要从手写编号目录推断 Stage identity 或新增另一张阶段图。

## Stage evidence 与产品视图

Stage evidence 记录输入、输出、作者/审阅角色、exact refs 与 lineage；产品视图提供当前可读 manuscript、分析结果与 submission。两者通过 manifest/ref 关联，不互相取代。

未形成 ready receipt 时，可保留部分、阴性或失败分析产物和质量债，供下一 Stage 继续推理；不得把文件夹或 manifest 存在解释为 owner acceptance。真正的权限、身份、来源、安全或 human gate 必须保持阻断，详见 [Stage handoff](../runtime/stage_route_handoff_standard.md)。

暂停、交付暂停、停止状态的 current stage 必须为空；恢复条件由 [生命周期](./study_lifecycle_control.md) 决定。旧 runtime residue 不能重新激活 study。

## 迁移

实际 workspace 迁移须有用户授权、当前 artifact/identity 清单、目标路径、保留来源、可回退方式和目标侧 readback。当前 manuscript、revision、独立 review 与 quality debt 必须完整迁移；旧目录仅保留有价值的 provenance。没有真实迁移操作时，本文不宣称任何 workspace 已完成目录整理。
